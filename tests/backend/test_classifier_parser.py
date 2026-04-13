import json
import pytest
from pydantic import ValidationError
from app.classifier import parse_model_output


def test_parse_model_output_accepts_plain_json():
    raw = json.dumps(
        {
            "description": "A denim jacket styled for casual streetwear.",
            "attributes": {
                "garment_type": ["jacket"],
                "style": ["streetwear"],
                "material": ["denim"],
                "color_palette": ["blue"],
                "pattern": ["solid"],
                "season": "fall",
                "occasion": ["casual"],
                "consumer_profile": ["young adult"],
                "trend_notes": ["oversized silhouette"],
                "location_context": {"scene": "urban street"},
            },
        }
    )

    result = parse_model_output(raw)

    assert result.description == "A denim jacket styled for casual streetwear."
    assert result.attributes.garment_type == ["jacket"]
    assert result.attributes.location_context.scene == "urban street"


def test_parse_model_output_accepts_fenced_json():
    raw = """
    ```json
    {
      "description": "A floral summer dress.",
      "attributes": {
        "garment_type": ["dress"],
        "style": ["romantic"],
        "color_palette": ["pink", "green"]
      }
    }
    ```
    """

    result = parse_model_output(raw)

    assert result.attributes.garment_type == ["dress"]
    assert result.attributes.style == ["romantic"]
    assert result.attributes.material == []
    assert result.attributes.season is None


def test_parse_model_output_fills_optional_attribute_defaults():
    raw = json.dumps(
        {
            "description": "A minimally labeled garment image.",
            "attributes": {},
        }
    )

    result = parse_model_output(raw)

    assert result.attributes.garment_type == []
    assert result.attributes.trend_notes == []
    assert result.attributes.location_context.country is None


def test_parse_model_output_rejects_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        parse_model_output("not json")


def test_parse_model_output_rejects_missing_required_description():
    with pytest.raises(ValidationError):
        parse_model_output(json.dumps({"attributes": {}}))

