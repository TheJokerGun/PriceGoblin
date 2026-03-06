from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Literal, Optional


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


# -------- TRACKING --------

class TrackingResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrackingActiveUpdate(BaseModel):
    is_active: bool | None = None

# -------- SCRAPER --------

class ScrapeRequest(BaseModel):
    name: str | None = None
    url: str | None = None
    category: str | None = None


class ScrapeUrlRequest(BaseModel):
    url: str


class ScrapeCategoryRequest(BaseModel):
    category: str
    name: str | None = None
    limit: int = 10


class ScrapeProductResponse(BaseModel):
    type: Literal["product"] = "product"
    id: int = 1
    name: str
    url: str
    category: str | None = None
    created_at: datetime
    price: float | None = None


class ScrapeCategoryItem(BaseModel):
    name: str
    price: str | float | None = None
    source: str | None = None
    url: str | None = None


class ScrapeCategoryResponse(BaseModel):
    type: Literal["category"] = "category"
    category: str
    count: int
    data: list[ScrapeCategoryItem]


ScrapeResponse = ScrapeProductResponse | ScrapeCategoryResponse
