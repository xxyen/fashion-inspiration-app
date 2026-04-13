import json
import re
from pathlib import Path
from .schemas import ClassificationResult, GarmentAttributes


def parse_model_output(raw: str) -> ClassificationResult:
    text = raw.strip()
    fenced_json = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced_json:
        text = fenced_json.group(1).strip()

    payload = json.loads(text)
    return ClassificationResult.model_validate(payload)


async def classify_image(image_path: Path) -> ClassificationResult:
    # Deterministic placeholder so upload flow works before the real model is connected.
    return ClassificationResult(
        description="A fashion inspiration image pending AI classification.",
        attributes=GarmentAttributes(
            garment_type=["unknown"],
            style=["inspiration"],
            trend_notes=["classification placeholder"],
        ),
    )

