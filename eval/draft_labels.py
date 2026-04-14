import argparse
import asyncio
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend"))

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


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", default="eval/images")
    parser.add_argument("--manifest", default="eval/image_manifest.json")
    parser.add_argument("--output", default="eval/labels.draft.json")
    args = parser.parse_args()

    images_dir = Path(args.images)
    manifest = load_manifest(Path(args.manifest))
    labels = []

    for image_path in sorted(images_dir.iterdir()):
        if not image_path.is_file() or image_path.name.startswith("."):
            continue
        print(f"Drafting labels for {image_path.name}")
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

    Path(args.output).write_text(json.dumps(labels, indent=2))
    print(f"Wrote {args.output}. Review and save as eval/labels.json before running eval.")


if __name__ == "__main__":
    asyncio.run(main())

