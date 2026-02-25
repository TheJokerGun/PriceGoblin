from pydantic import BaseModel
from pydantic import ConfigDict
from datetime import datetime
from typing import Optional


# -------- AUTH --------

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


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

    model_config = ConfigDict(from_attributes=True)


# -------- PRICES --------

class PriceResponse(BaseModel):
    id: int
    price: float
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)

# -------- SCRAPER --------

class ScrapeRequest(BaseModel):
    name: str | None = None
    url: str | None = None
    category: str | None = None
