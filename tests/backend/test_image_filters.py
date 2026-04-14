import json


def test_list_images_filters_and_dynamic_filter_options(tmp_path, monkeypatch):
    database_path = tmp_path / "filters.db"

    import app.db as db
    from app.db import init_db, get_connection
    from app.main import get_filters, list_images, rebuild_search_index

    monkeypatch.setattr(db, "DATABASE_PATH", database_path)
    init_db()
    with get_connection() as connection:
        connection.execute(
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
                "one.jpg",
                "/uploads/one.jpg",
                "Embroidered neckline at an artisan market.",
                json.dumps(
                    {
                        "garment_type": ["dress"],
                        "style": ["bohemian"],
                        "material": ["cotton"],
                        "color_palette": ["white", "blue"],
                        "pattern": ["embroidered"],
                        "season": "summer",
                        "occasion": ["vacation"],
                        "consumer_profile": ["young adult"],
                        "trend_notes": ["artisan detail"],
                        "location_context": {"scene": "market"},
                    }
                ),
                "Avery",
                "Europe",
                "France",
                "Paris",
                "2026-04-14",
            ),
        )
    rebuild_search_index()

    assert len(list_images(query="artisan")) == 1
    assert len(list_images(query="embroider")) == 1
    assert len(list_images(query="!!!")) == 0
    assert len(list_images(garment_type="dress")) == 1
    assert len(list_images(continent="Europe")) == 1
    assert len(list_images(country="France")) == 1
    assert len(list_images(year="2026")) == 1
    assert len(list_images(month="04")) == 1
    assert len(list_images(month="05")) == 0
    assert len(list_images(style="streetwear")) == 0

    filters = get_filters()
    assert filters["garment_type"] == ["dress"]
    assert filters["style"] == ["bohemian"]
    assert filters["continent"] == ["Europe"]
    assert filters["country"] == ["France"]
    assert filters["year"] == ["2026"]
    assert filters["month"] == ["04"]


def test_update_annotations_and_searches_human_notes(tmp_path, monkeypatch):
    database_path = tmp_path / "annotations.db"

    import app.db as db
    from app.db import init_db, get_connection
    from app.main import AnnotationUpdate, list_images, rebuild_search_index, update_annotations

    monkeypatch.setattr(db, "DATABASE_PATH", database_path)
    init_db()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO images (
                filename,
                image_url,
                description,
                metadata_json
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                "one.jpg",
                "/uploads/one.jpg",
                "A neutral outfit.",
                json.dumps({"garment_type": ["jacket"]}),
            ),
        )
        image_id = cursor.lastrowid
    rebuild_search_index()

    updated = update_annotations(
        image_id,
        AnnotationUpdate(
            designer_tags=["artisan", "market"],
            designer_notes="Use this for embroidered neckline references.",
        ),
    )

    assert updated["designer_tags"] == ["artisan", "market"]
    assert updated["designer_notes"] == "Use this for embroidered neckline references."
    assert len(list_images(query="embroidered neckline")) == 1
    assert len(list_images(query="artisan")) == 1
