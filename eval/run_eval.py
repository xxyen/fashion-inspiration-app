import argparse
import asyncio
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "app/backend"))

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

SEASON_ALIASES = {
    "fall": {"fall", "autumn"},
    "winter": {"winter", "cold weather"},
    "summer": {"summer", "warm weather"},
    "spring": {"spring"},
    "transitional": {"transitional", "spring/fall", "fall/spring", "spring or fall", "fall or spring"},
}

SCENE_ALIASES = {
    "street": {
        "street",
        "urban street",
        "city street",
        "sidewalk",
        "urban",
        "street scene",
        "outdoor street",
        "city sidewalk",
    },
    "studio": {
        "studio",
        "photo studio",
        "indoor studio",
        "plain background",
        "studio portrait",
    },
    "runway": {"runway", "catwalk", "fashion show"},
    "market": {"market", "artisan market", "bazaar", "street market"},
    "store": {"store", "shop", "retail", "boutique"},
    "beach": {"beach", "coast", "seaside", "shore"},
    "outdoor": {
        "outdoor",
        "outside",
        "park",
        "garden",
        "nature",
        "field",
        "outdoor stairs",
        "outdoor setting",
    },
    "event": {"event", "party", "festival", "concert"},
    "travel": {"travel", "airport", "train station", "station"},
    "indoor": {"indoor", "interior", "room", "hallway"},
}


def normalize(value) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(item).strip().lower() for item in value if str(item).strip()}
    return {str(value).strip().lower()}


def canonicalize(value, aliases: dict[str, set[str]]):
    values = normalize(value)
    canonical_values = set()
    for item in values:
        matched = False
        for canonical, alias_values in aliases.items():
            if item == canonical or item in alias_values:
                canonical_values.add(canonical)
                matched = True
                break
        if not matched:
            canonical_values.add(item)
    return canonical_values


def matches(predicted, expected) -> bool:
    predicted_values = normalize(predicted)
    expected_values = normalize(expected)
    return bool(predicted_values and expected_values and predicted_values.intersection(expected_values))


def multilabel_counts(predicted, expected) -> dict[str, int]:
    predicted_values = normalize(predicted)
    expected_values = normalize(expected)
    return {
        "tp": len(predicted_values.intersection(expected_values)),
        "fp": len(predicted_values - expected_values),
        "fn": len(expected_values - predicted_values),
    }


def precision_recall_f1(counts: dict[str, int]) -> dict[str, float]:
    tp = counts["tp"]
    fp = counts["fp"]
    fn = counts["fn"]
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
    }


def canonical_matches(predicted, expected, aliases: dict[str, set[str]]) -> bool:
    predicted_values = canonicalize(predicted, aliases)
    expected_values = canonicalize(expected, aliases)
    return bool(predicted_values and expected_values and predicted_values.intersection(expected_values))


def model_dump(model) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


async def evaluate(labels_path: Path, images_dir: Path) -> dict:
    labels = json.loads(labels_path.read_text())
    totals: dict[str, int] = {}
    correct: dict[str, int] = {}
    multilabel_totals = {
        field: {"tp": 0, "fp": 0, "fn": 0}
        for field in LIST_FIELDS
    }
    details = []

    async def evaluate_field(name: str, predicted, expected, row: dict, aliases: dict[str, set[str]] | None = None) -> None:
        row["expected"][name] = expected
        row["predicted"][name] = predicted
        if not normalize(expected):
            row["matches"][name] = "skipped"
            return
        totals[name] = totals.get(name, 0) + 1
        if aliases:
            row["expected"][f"{name}_normalized"] = sorted(canonicalize(expected, aliases))
            row["predicted"][f"{name}_normalized"] = sorted(canonicalize(predicted, aliases))
            is_match = canonical_matches(predicted, expected, aliases)
        else:
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
            "expected": {},
            "predicted": {},
            "matches": {},
        }

        for field in LIST_FIELDS:
            await evaluate_field(field, predicted.get(field), expected.get(field), row)
            if normalize(expected.get(field)):
                counts = multilabel_counts(predicted.get(field), expected.get(field))
                row["matches"][f"{field}_counts"] = counts
                for key, value in counts.items():
                    multilabel_totals[field][key] += value

        for field in SCALAR_FIELDS:
            await evaluate_field(field, predicted.get(field), expected.get(field), row, SEASON_ALIASES)

        await evaluate_field(
            "location_scene",
            predicted.get("location_context", {}).get("scene"),
            expected.get("location_context", {}).get("scene"),
            row,
            SCENE_ALIASES,
        )
        details.append(row)

    summary = {
        field: round(correct.get(field, 0) / total, 3)
        for field, total in totals.items()
        if total
    }
    multilabel_summary = {
        field: precision_recall_f1(counts)
        for field, counts in multilabel_totals.items()
    }
    return {
        "summary": summary,
        "multilabel_summary": multilabel_summary,
        "details": details,
    }


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
    print(json.dumps(results["multilabel_summary"], indent=2))


if __name__ == "__main__":
    asyncio.run(main())
