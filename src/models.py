"""product_data.json 입력 스키마 (Pydantic v2)."""
from pydantic import BaseModel, Field


class Brand(BaseModel):
    name: str
    tagline: str = ""
    color_primary: str = "#FF6B35"
    color_secondary: str = "#1A1A2E"


class Transformation(BaseModel):
    before: str = ""
    after: str = ""


class Product(BaseModel):
    name: str
    category: str = ""
    price: int = Field(ge=0)
    original_price: int = Field(ge=0)
    key_benefits: list[str] = []
    ingredients_or_specs: list[str] = []
    usage_steps: list[str] = []
    target_customer: str = ""
    pain_points: list[str] = []
    transformation: Transformation = Transformation()


class Testimonial(BaseModel):
    model_config = {"extra": "allow"}

    name: str
    result: str = ""
    comment: str = ""
    rating: float = Field(default=5.0, ge=1.0, le=5.0)


class SocialProof(BaseModel):
    review_count: int = 0
    avg_rating: float = Field(default=5.0, ge=1.0, le=5.0)
    testimonials: list[Testimonial] = []


class Authority(BaseModel):
    expert_name: str = ""
    credentials: list[str] = []
    story: str = ""


class BonusItem(BaseModel):
    name: str
    value: int = Field(ge=0)


class Offer(BaseModel):
    deadline: str = ""
    bonus_items: list[BonusItem] = []
    guarantee_days: int = Field(default=30, ge=0)


class ProductData(BaseModel):
    brand: Brand
    product: Product
    social_proof: SocialProof = SocialProof()
    authority: Authority = Authority()
    offer: Offer = Offer()
    section_overrides: dict = {}
