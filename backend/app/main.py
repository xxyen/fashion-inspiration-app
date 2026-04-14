import json
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .classifier import classify_image
from .config import UPLOAD_DIR
from .db import get_connection, init_db
from .schemas import GarmentAttributes
from pydantic import BaseModel, Field


app = FastAPI(title="Fashion Inspiration API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


class AnnotationUpdate(BaseModel):
    designer_tags: list[str] = Field(default_factory=list)
    designer_notes: str | None = None


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def serialize_image(row) -> dict:
    metadata = GarmentAttributes.model_validate(json.loads(row["metadata_json"] or "{}"))
    return {
        "id": row["id"],
        "filename": row["filename"],
        "image_url": row["image_url"],
        "description": row["description"],
        "metadata": metadata.model_dump(),
        "designer_tags": json.loads(row["designer_tags_json"] or "[]"),
        "designer_notes": row["designer_notes"],
        "designer": row["designer"],
        "continent": row["continent"],
        "country": row["country"],
        "city": row["city"],
        "captured_at": row["captured_at"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def list_matches(values: list[str], expected: str | None) -> bool:
    if not expected:
        return True
    expected_value = normalize(expected)
    return expected_value in {normalize(value) for value in values}


def value_matches(value: str | None, expected: str | None) -> bool:
    return not expected or normalize(value) == normalize(expected)


def searchable_text(record: dict) -> str:
    metadata = record["metadata"]
    pieces = [
        record["description"],
        record["designer_notes"],
        record["designer"],
        record["continent"],
        record["country"],
        record["city"],
        metadata.get("season"),
        metadata.get("location_context", {}).get("scene"),
        " ".join(record["designer_tags"]),
        " ".join(metadata.get("garment_type", [])),
        " ".join(metadata.get("style", [])),
        " ".join(metadata.get("material", [])),
        " ".join(metadata.get("color_palette", [])),
        " ".join(metadata.get("pattern", [])),
        " ".join(metadata.get("occasion", [])),
        " ".join(metadata.get("consumer_profile", [])),
        " ".join(metadata.get("trend_notes", [])),
    ]
    return " ".join(piece for piece in pieces if piece).lower()


def record_matches(
    record: dict,
    query: str | None,
    garment_type: str | None,
    style: str | None,
    material: str | None,
    color_palette: str | None,
    pattern: str | None,
    season: str | None,
    occasion: str | None,
    consumer_profile: str | None,
    country: str | None,
    city: str | None,
    designer: str | None,
) -> bool:
    metadata = record["metadata"]
    return (
        (not query or normalize(query) in searchable_text(record))
        and list_matches(metadata.get("garment_type", []), garment_type)
        and list_matches(metadata.get("style", []), style)
        and list_matches(metadata.get("material", []), material)
        and list_matches(metadata.get("color_palette", []), color_palette)
        and list_matches(metadata.get("pattern", []), pattern)
        and value_matches(metadata.get("season"), season)
        and list_matches(metadata.get("occasion", []), occasion)
        and list_matches(metadata.get("consumer_profile", []), consumer_profile)
        and value_matches(record["country"], country)
        and value_matches(record["city"], city)
        and value_matches(record["designer"], designer)
    )


def add_values(bucket: set[str], values: list[str]) -> None:
    for value in values:
        cleaned = value.strip()
        if cleaned:
            bucket.add(cleaned)


@app.post("/api/images")
async def upload_image(
    image: UploadFile = File(...),
    designer: str | None = Form(None),
    continent: str | None = Form(None),
    country: str | None = Form(None),
    city: str | None = Form(None),
    captured_at: str | None = Form(None),
) -> dict:
    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    suffix = Path(image.filename or "").suffix.lower() or ".jpg"
    filename = f"{uuid4().hex}{suffix}"
    image_path = UPLOAD_DIR / filename
    image_path.write_bytes(await image.read())

    classification = await classify_image(image_path)
    metadata = classification.attributes
    metadata.location_context.continent = metadata.location_context.continent or continent
    metadata.location_context.country = metadata.location_context.country or country
    metadata.location_context.city = metadata.location_context.city or city

    metadata_json = metadata.model_dump_json()
    image_url = f"/uploads/{filename}"
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO images (
                filename,
                image_url,
                description,
                metadata_json,
                designer,
                continent,
                country,
                city,
                captured_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                image_url,
                classification.description,
                metadata_json,
                designer,
                continent,
                country,
                city,
                captured_at,
            ),
        )
        row = connection.execute(
            "SELECT * FROM images WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    return serialize_image(row)


@app.get("/api/images")
def list_images(
    query: str | None = None,
    garment_type: str | None = None,
    style: str | None = None,
    material: str | None = None,
    color_palette: str | None = None,
    pattern: str | None = None,
    season: str | None = None,
    occasion: str | None = None,
    consumer_profile: str | None = None,
    country: str | None = None,
    city: str | None = None,
    designer: str | None = None,
) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM images ORDER BY created_at DESC, id DESC"
        ).fetchall()
    records = [serialize_image(row) for row in rows]
    return [
        record
        for record in records
        if record_matches(
            record,
            query,
            garment_type,
            style,
            material,
            color_palette,
            pattern,
            season,
            occasion,
            consumer_profile,
            country,
            city,
            designer,
        )
    ]


@app.get("/api/filters")
def get_filters() -> dict[str, list[str]]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM images").fetchall()

    buckets: dict[str, set[str]] = {
        "garment_type": set(),
        "style": set(),
        "material": set(),
        "color_palette": set(),
        "pattern": set(),
        "season": set(),
        "occasion": set(),
        "consumer_profile": set(),
        "country": set(),
        "city": set(),
        "designer": set(),
    }

    for row in rows:
        record = serialize_image(row)
        metadata = record["metadata"]
        add_values(buckets["garment_type"], metadata.get("garment_type", []))
        add_values(buckets["style"], metadata.get("style", []))
        add_values(buckets["material"], metadata.get("material", []))
        add_values(buckets["color_palette"], metadata.get("color_palette", []))
        add_values(buckets["pattern"], metadata.get("pattern", []))
        add_values(buckets["occasion"], metadata.get("occasion", []))
        add_values(buckets["consumer_profile"], metadata.get("consumer_profile", []))
        add_values(buckets["season"], [metadata["season"]] if metadata.get("season") else [])
        add_values(buckets["country"], [record["country"]] if record.get("country") else [])
        add_values(buckets["city"], [record["city"]] if record.get("city") else [])
        add_values(buckets["designer"], [record["designer"]] if record.get("designer") else [])

    return {key: sorted(values) for key, values in buckets.items()}


@app.patch("/api/images/{image_id}/annotations")
def update_annotations(image_id: int, payload: AnnotationUpdate) -> dict:
    tags = [tag.strip() for tag in payload.designer_tags if tag.strip()]
    notes = payload.designer_notes.strip() if payload.designer_notes else None
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM images WHERE id = ?",
            (image_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Image not found")

        connection.execute(
            """
            UPDATE images
            SET designer_tags_json = ?,
                designer_notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (json.dumps(tags), notes, image_id),
        )
        updated = connection.execute(
            "SELECT * FROM images WHERE id = ?",
            (image_id,),
        ).fetchone()
    return serialize_image(updated)


@app.delete("/api/images/{image_id}")
def delete_image(image_id: int) -> dict[str, int | str]:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM images WHERE id = ?",
            (image_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Image not found")

        connection.execute("DELETE FROM images WHERE id = ?", (image_id,))

    image_path = UPLOAD_DIR / row["filename"]
    if image_path.exists() and image_path.is_file():
        image_path.unlink()

    return {"status": "deleted", "id": image_id}
