from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas import LoginRequest, TokenResponse
from services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.login_user(db, request.email)
    token = auth_service.create_access_token(user)
    return {"access_token": token}

#TODO: Look into token type bearer and how the jwt token works