import logging
from time import perf_counter
from typing import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import (
    http_exception_handler as fastapi_http_exception_handler,
)
from fastapi.exception_handlers import (
    request_validation_exception_handler as fastapi_request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from src.backend.logging_utils import (
    configure_logging,
    extract_validation_expectations,
    get_request_headers,
    get_request_id,
    get_sanitized_request_body,
    log_event,
    should_log_request_completed,
    should_log_request_received,
)
from src.backend.routes.scraper import router as scrape_router
from src.backend.routes.auth import router as auth_router
from src.backend.routes.products import router as products_router
from src.backend.routes.tracking import router as tracking_router

logger = configure_logging()
app = FastAPI()


def _infer_expected_from_http_exception(exc: HTTPException) -> list[str] | None:
    if exc.status_code == 401:
        return ["Authorization header: Bearer <token>"]
    if exc.status_code == 404:
        return ["Valid resource id owned by current user"]
    if exc.status_code != 400 or not isinstance(exc.detail, str):
        return None

    details_to_expected: dict[str, list[str]] = {
        "At least one of name, url, or category must be provided": [
            "Body includes one of: name, url, category",
        ],
        "Provide either url OR category": [
            "Body includes exactly one of: url or category",
        ],
        "Invalid email domain": [
            "Email ending with @my.dbb-lippe.de",
        ],
    }
    return details_to_expected.get(exc.detail)


# Development CORS: allow same-network access and preflight requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape_router)
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(tracking_router)


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
):
    request.state.request_id = uuid4().hex
    start = perf_counter()
    if should_log_request_received(request):
        body = await get_sanitized_request_body(request)
        log_event(
            logger,
            logging.INFO,
            "request.received",
            request_id=get_request_id(request),
            method=request.method,
            path=request.url.path,
            query=request.url.query or None,
            headers=get_request_headers(request),
            body=body,
        )

    response = await call_next(request)
    duration_ms = round((perf_counter() - start) * 1000, 2)

    status_code = response.status_code
    if should_log_request_completed(request, status_code):
        level = (
            logging.ERROR
            if status_code >= 500
            else logging.WARNING if status_code >= 400 else logging.INFO
        )
        log_event(
            logger,
            level,
            "request.completed",
            request_id=get_request_id(request),
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration_ms,
            failure_reason=getattr(request.state, "failure_reason", None),
            expected=getattr(request.state, "expected", None),
        )

    response.headers["X-Request-ID"] = get_request_id(request)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    expected = extract_validation_expectations(errors)
    request.state.failure_reason = "Request validation failed"
    request.state.expected = expected

    log_event(
        logger,
        logging.WARNING,
        "request.validation_failed",
        request_id=get_request_id(request),
        method=request.method,
        path=request.url.path,
        expected=expected,
        errors=errors,
    )
    return await fastapi_request_validation_exception_handler(request, exc)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request.state.failure_reason = exc.detail

    inferred_expected = _infer_expected_from_http_exception(exc)
    if inferred_expected:
        request.state.expected = inferred_expected

    level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    log_event(
        logger,
        level,
        "request.http_exception",
        request_id=get_request_id(request),
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
        detail=exc.detail,
        expected=getattr(request.state, "expected", None),
    )

    return await fastapi_http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request.state.failure_reason = str(exc) or exc.__class__.__name__

    log_event(
        logger,
        logging.ERROR,
        "request.unhandled_exception",
        request_id=get_request_id(request),
        method=request.method,
        path=request.url.path,
        error_type=type(exc).__name__,
        detail=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": get_request_id(request),
        },
    )
