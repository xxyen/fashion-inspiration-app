import json


def test_list_images_filters_and_dynamic_filter_options(tmp_path, monkeypatch):
    database_path = tmp_path / "filters.db"

    import app.db as db
    from app.db import init_db, get_connection
    from app.main import get_filters, list_images

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
                country,
                city
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
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
                "France",
                "Paris",
            ),
        )

    assert len(list_images(query="artisan")) == 1
    assert len(list_images(garment_type="dress")) == 1
    assert len(list_images(country="France")) == 1
    assert len(list_images(style="streetwear")) == 0

    filters = get_filters()
    assert filters["garment_type"] == ["dress"]
    assert filters["style"] == ["bohemian"]
    assert filters["country"] == ["France"]
