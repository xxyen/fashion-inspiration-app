CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    image_url TEXT NOT NULL,
    description TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    designer_tags_json TEXT NOT NULL DEFAULT '[]',
    designer_notes TEXT,
    designer TEXT,
    continent TEXT,
    country TEXT,
    city TEXT,
    captured_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_images_created_at ON images(created_at);
CREATE INDEX IF NOT EXISTS idx_images_designer ON images(designer);
CREATE INDEX IF NOT EXISTS idx_images_country ON images(country);

CREATE VIRTUAL TABLE IF NOT EXISTS image_search USING fts5(content);
