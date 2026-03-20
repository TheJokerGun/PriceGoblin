from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..locale_utils import normalize_locale
from ..schemas import LoginRequest, RegisterRequest, TokenResponse
from ..services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    locale = normalize_locale(request.locale)
    user = auth_service.register_user(db, request.email, request.password, locale=locale)
    payload = {"sub": user.email, "user_id": user.id}
    token_locale = locale or user.locale
    if token_locale:
        payload["locale"] = token_locale
    token = auth_service.create_access_token(payload)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = auth_service.authenticate_user(db, request.email, request.password)
    locale = normalize_locale(request.locale)
    if locale and user.locale != locale:
        user.locale = locale
        db.add(user)
        db.commit()
        db.refresh(user)
    payload = {"sub": user.email, "user_id": user.id}
    token_locale = locale or user.locale
    if token_locale:
        payload["locale"] = token_locale
    token = auth_service.create_access_token(payload)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def read_current_user(current_user=Depends(auth_service.get_current_user)) -> dict[str, str | int]:
    return {"id": current_user.id, "email": current_user.email, "locale": getattr(current_user, "locale", None)}
