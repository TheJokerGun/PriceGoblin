from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Literal, Optional


# -------- AUTH --------

class LoginRequest(BaseModel):
    email: str
    password: str
    locale: str | None = None


class RegisterRequest(BaseModel):
    email: str
    password: str
    locale: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# -------- PRODUCTS --------

class ProductCreate(BaseModel):
    name: Optional[str]
    url: Optional[str]
    category: Optional[str]
    image_url: Optional[str] = None
    source: Optional[str] = None
    target_price: Optional[float] = None


class ProductResponse(BaseModel):
    id: int
    name: Optional[str]
    url: Optional[str]
    category: Optional[str]
    image_url: str | None = None
    tracking_id: int | None = None
    is_active: bool | None = None
    source: str | None = None
    target_price: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductSelectionItem(BaseModel):
    name: str | None = None
    url: str | None = None
    category: str | None = None
    price: str | float | None = None
    image_url: str | None = None
    source: str | None = None
    target_price: float | None = None


class ProductCategorySelectionCreate(BaseModel):
    items: list[ProductSelectionItem]


class ProductCategorySelectionResult(BaseModel):
    product_id: int
    tracking_id: int
    name: str | None = None
    url: str | None = None
    category: str | None = None
    image_url: str | None = None
    source: str | None = None
    target_price: float | None = None
    is_active: bool
    created_product: bool
    created_tracking: bool
    seeded_price: float | None = None


class ProductCategorySelectionResponse(BaseModel):
    count: int
    data: list[ProductCategorySelectionResult]


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
    source: str | None = None
    target_price: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrackingActiveUpdate(BaseModel):
    is_active: bool | None = None


class TrackingTargetPriceUpdate(BaseModel):
    target_price: float | None = None

# -------- SCRAPER --------

class ScrapeRequest(BaseModel):
    name: str | None = None
    url: str | None = None
    category: str | None = None
    target_price: float | None = None


class ScrapeUrlRequest(BaseModel):
    url: str
    target_price: float | None = None


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
    image_url: str | None = None


class ScrapeCategoryItem(BaseModel):
    name: str
    price: str | float | None = None
    image_url: str | None = None
    source: str | None = None
    url: str | None = None


class ScrapeCategoryResponse(BaseModel):
    type: Literal["category"] = "category"
    category: str
    count: int
    data: list[ScrapeCategoryItem]


ScrapeResponse = ScrapeProductResponse | ScrapeCategoryResponse
