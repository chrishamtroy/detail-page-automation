import pytest
from pydantic import ValidationError
from src.models import ProductData

_VALID = {
    "brand": {"name": "TestBrand"},
    "product": {"name": "TestProduct", "price": 50000, "original_price": 100000},
}


def test_valid_minimal_data():
    pd = ProductData.model_validate(_VALID)
    assert pd.product.name == "TestProduct"
    assert pd.product.price == 50000


def test_defaults_applied():
    pd = ProductData.model_validate(_VALID)
    assert pd.brand.color_primary == "#FF6B35"
    assert pd.brand.color_secondary == "#1A1A2E"
    assert pd.offer.guarantee_days == 30
    assert pd.social_proof.review_count == 0


def test_missing_product_raises():
    with pytest.raises(ValidationError):
        ProductData.model_validate({"brand": {"name": "x"}})


def test_missing_brand_raises():
    with pytest.raises(ValidationError):
        ProductData.model_validate({"product": {"name": "x", "price": 0, "original_price": 0}})


def test_negative_price_raises():
    data = {
        "brand": {"name": "x"},
        "product": {"name": "x", "price": -1, "original_price": 100},
    }
    with pytest.raises(ValidationError):
        ProductData.model_validate(data)


def test_bonus_item_validation():
    data = {
        **_VALID,
        "offer": {"bonus_items": [{"name": "Gift", "value": 10000}]},
    }
    pd = ProductData.model_validate(data)
    assert pd.offer.bonus_items[0].name == "Gift"


def test_testimonial_extra_fields_allowed():
    data = {
        **_VALID,
        "social_proof": {
            "testimonials": [{"name": "김철수", "comment": "좋아요", "age": 30}]
        },
    }
    pd = ProductData.model_validate(data)
    assert pd.social_proof.testimonials[0].name == "김철수"
