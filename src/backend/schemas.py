from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# -------- AUTH --------

class LoginRequest(BaseModel):
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# -------- PRODUCTS --------

class ProductCreate(BaseModel):
    name: Optional[str]
    url: Optional[str]
    category: Optional[str]


class ProductResponse(BaseModel):
    id: int
    name: Optional[str]
    url: Optional[str]
    category: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


# -------- PRICES --------

class PriceResponse(BaseModel):
    id: int
    price: float
    checked_at: datetime

    class Config:
        orm_mode = True
