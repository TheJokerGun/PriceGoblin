from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import LoginRequest, RegisterRequest, TokenResponse
from ..services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = auth_service.register_user(db, request.email, request.password)
    token = auth_service.create_access_token({"sub": user.email, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = auth_service.authenticate_user(db, request.email, request.password)
    token = auth_service.create_access_token({"sub": user.email, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def read_current_user(current_user=Depends(auth_service.get_current_user)) -> dict[str, str | int]:
    return {"id": current_user.id, "email": current_user.email}
