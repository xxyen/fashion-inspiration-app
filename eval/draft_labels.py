import argparse
import asyncio
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "app/backend"))

from app.classifier import classify_image


def model_dump(model) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def load_manifest(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    rows = json.loads(path.read_text())
    return {row["image"]: row for row in rows}


def load_existing_labels(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def image_paths(images_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in images_dir.iterdir()
        if path.is_file() and not path.name.startswith(".")
    )


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", default="eval/images")
    parser.add_argument("--manifest", default="eval/image_manifest.json")
    parser.add_argument("--output", default="eval/labels.draft.json")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--restart", action="store_true")
    args = parser.parse_args()

    images_dir = Path(args.images)
    manifest = load_manifest(Path(args.manifest))
    output_path = Path(args.output)
    labels = [] if args.restart else load_existing_labels(output_path)
    completed = {item["image"] for item in labels}
    pending = [path for path in image_paths(images_dir) if path.name not in completed]
    if args.limit:
        pending = pending[: args.limit]

    total = len(completed) + len(pending)
    for offset, image_path in enumerate(pending, start=len(completed) + 1):
        print(f"[{offset}/{total}] Drafting labels for {image_path.name}", flush=True)
        result = await classify_image(image_path)
        attributes = model_dump(result.attributes)
        source = manifest.get(image_path.name, {})
        labels.append(
            {
                "image": image_path.name,
                "source": "pexels",
                "source_url": source.get("source_url", ""),
                "photographer": source.get("photographer", ""),
                "draft_description": result.description,
                "expected": {
                    "garment_type": attributes.get("garment_type", []),
                    "style": attributes.get("style", []),
                    "material": attributes.get("material", []),
                    "color_palette": attributes.get("color_palette", []),
                    "pattern": attributes.get("pattern", []),
                    "season": attributes.get("season"),
                    "occasion": attributes.get("occasion", []),
                    "consumer_profile": attributes.get("consumer_profile", []),
                    "location_context": {
                        "scene": attributes.get("location_context", {}).get("scene")
                    },
                },
            }
        )
        output_path.write_text(json.dumps(labels, indent=2))

    print(f"Wrote {args.output}. Review and save as eval/labels.json before running eval.", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
