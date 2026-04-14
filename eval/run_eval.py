import argparse
import asyncio
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend"))

from app.classifier import classify_image


LIST_FIELDS = [
    "garment_type",
    "style",
    "material",
    "color_palette",
    "pattern",
    "occasion",
    "consumer_profile",
]

SCALAR_FIELDS = ["season"]


def normalize(value) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(item).strip().lower() for item in value if str(item).strip()}
    return {str(value).strip().lower()}


def matches(predicted, expected) -> bool:
    predicted_values = normalize(predicted)
    expected_values = normalize(expected)
    return bool(predicted_values and expected_values and predicted_values.intersection(expected_values))


def model_dump(model) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


async def evaluate(labels_path: Path, images_dir: Path) -> dict:
    labels = json.loads(labels_path.read_text())
    totals: dict[str, int] = {}
    correct: dict[str, int] = {}
    details = []

    async def evaluate_field(name: str, predicted, expected, row: dict) -> None:
        if not normalize(expected):
            row["matches"][name] = "skipped"
            return
        totals[name] = totals.get(name, 0) + 1
        is_match = matches(predicted, expected)
        correct[name] = correct.get(name, 0) + int(is_match)
        row["matches"][name] = is_match

    for item in labels:
        image_path = images_dir / item["image"]
        expected = item["expected"]
        result = await classify_image(image_path)
        predicted = model_dump(result.attributes)
        row = {
            "image": item["image"],
            "description": result.description,
            "matches": {},
        }

        for field in LIST_FIELDS:
            await evaluate_field(field, predicted.get(field), expected.get(field), row)

        for field in SCALAR_FIELDS:
            await evaluate_field(field, predicted.get(field), expected.get(field), row)

        await evaluate_field(
            "location_scene",
            predicted.get("location_context", {}).get("scene"),
            expected.get("location_context", {}).get("scene"),
            row,
        )
        details.append(row)

    summary = {
        field: round(correct.get(field, 0) / total, 3)
        for field, total in totals.items()
        if total
    }
    return {"summary": summary, "details": details}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", default="eval/labels.json")
    parser.add_argument("--images", default="eval/images")
    parser.add_argument("--output", default="eval/results.json")
    args = parser.parse_args()

    results = await evaluate(Path(args.labels), Path(args.images))
    output_path = Path(args.output)
    output_path.write_text(json.dumps(results, indent=2))
    print(json.dumps(results["summary"], indent=2))


if __name__ == "__main__":
    asyncio.run(main())
