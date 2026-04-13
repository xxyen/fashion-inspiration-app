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
def list_images() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM images ORDER BY created_at DESC, id DESC"
        ).fetchall()
    return [serialize_image(row) for row in rows]


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
