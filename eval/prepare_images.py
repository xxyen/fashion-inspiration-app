import argparse
import json
from pathlib import Path
from PIL import Image, ImageOps


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def image_files(source_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def resize_and_save(source_path: Path, target_path: Path, max_size: int, quality: int) -> None:
    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image)
        image.thumbnail((max_size, max_size))
        image.convert("RGB").save(
            target_path,
            "JPEG",
            quality=quality,
            optimize=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", help="Directory containing raw downloaded images.")
    parser.add_argument("--output-dir", default="eval/images")
    parser.add_argument("--manifest", default="eval/image_manifest.json")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--max-size", type=int, default=1024)
    parser.add_argument("--quality", type=int, default=85)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)
    manifest_path = Path(args.manifest)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for index, source_path in enumerate(image_files(source_dir), start=args.start):
        target_name = f"{index:03d}.jpg"
        target_path = output_dir / target_name
        manifest.append(
            {
                "image": target_name,
                "original_filename": source_path.name,
                "source_url": "",
                "photographer": "",
            }
        )
        print(f"{source_path} -> {target_path} ({args.max_size}px max, quality {args.quality})")
        if not args.dry_run:
            resize_and_save(source_path, target_path, args.max_size, args.quality)

    if not args.dry_run:
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
