import base64
import json
import logging
import mimetypes
import re
from pathlib import Path
from .config import OPENAI_API_KEY, OPENAI_MODEL
from .schemas import ClassificationResult, GarmentAttributes


logger = logging.getLogger(__name__)


CLASSIFICATION_PROMPT = """
Analyze this fashion inspiration image for a design team.

Return only valid JSON with this exact top-level shape:
{
  "description": "A rich natural-language description of the visible outfit or garment.",
  "attributes": {
    "garment_type": ["dress"],
    "style": ["streetwear"],
    "material": ["denim"],
    "color_palette": ["blue", "black"],
    "pattern": ["solid"],
    "season": "fall",
    "occasion": ["casual"],
    "consumer_profile": ["young adult"],
    "trend_notes": ["oversized silhouette"],
    "location_context": {
      "continent": null,
      "country": null,
      "city": null,
      "scene": "urban street"
    }
  }
}

Use null when the image does not provide enough evidence. Do not guess exact city,
country, or continent from visual appearance alone.
"""


def fallback_classification() -> ClassificationResult:
    return ClassificationResult(
        description="A fashion inspiration image pending AI classification.",
        attributes=GarmentAttributes(
            garment_type=["unknown"],
            style=["inspiration"],
            trend_notes=["classification placeholder"],
        ),
    )


LIST_ATTRIBUTE_FIELDS = [
    "garment_type",
    "style",
    "material",
    "color_palette",
    "pattern",
    "occasion",
    "consumer_profile",
    "trend_notes",
]


def normalize_attribute_payload(payload: dict) -> dict:
    attributes = payload.setdefault("attributes", {})
    for field in LIST_ATTRIBUTE_FIELDS:
        value = attributes.get(field, [])
        if value is None:
            attributes[field] = []
        elif isinstance(value, list):
            attributes[field] = [str(item) for item in value if item not in (None, "")]
        else:
            attributes[field] = [str(value)]

    location_context = attributes.get("location_context")
    if not isinstance(location_context, dict):
        attributes["location_context"] = {}

    return payload


def parse_model_output(raw: str) -> ClassificationResult:
    text = raw.strip()
    fenced_json = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced_json:
        text = fenced_json.group(1).strip()

    payload = normalize_attribute_payload(json.loads(text))
    if hasattr(ClassificationResult, "model_validate"):
        return ClassificationResult.model_validate(payload)
    return ClassificationResult.parse_obj(payload)


def image_to_data_url(image_path: Path) -> str:
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


async def classify_image(image_path: Path) -> ClassificationResult:
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY is not set; using fallback classification.")
        return fallback_classification()

    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": CLASSIFICATION_PROMPT},
                        {"type": "input_image", "image_url": image_to_data_url(image_path)},
                    ],
                }
            ],
            temperature=0,
        )
        raw_output = response.output_text
        return parse_model_output(raw_output)
    except Exception:
        logger.warning("OpenAI classification failed; using fallback classification.", exc_info=True)
        return fallback_classification()
