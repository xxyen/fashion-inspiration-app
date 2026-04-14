# Fashion Inspiration App

Initial project scaffold for a fashion inspiration image library. The app currently supports image upload, a searchable gallery backed by SQLite, AI classification, and designer annotations.

The planned stack is:

- Frontend: React, Vite, TypeScript, Tailwind CSS
- Backend: Python, FastAPI
- Database: SQLite

## Structure

```text
frontend/          React + Tailwind app
backend/           FastAPI app
backend/app/schema.sql SQLite image metadata schema
backend/uploads/   Future local upload storage
eval/              Future evaluation dataset and scripts
tests/             Future backend and e2e tests
```

## Local Setup

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API starts at `http://localhost:8000`. On startup, the backend initializes the SQLite schema in `backend/app/schema.sql`.

Current endpoints:

```text
GET /api/health
POST /api/images
GET /api/images
GET /api/filters
PATCH /api/images/{image_id}/annotations
DELETE /api/images/{image_id}
```

`POST /api/images` accepts multipart form data with an `image` file and optional context fields: `designer`, `continent`, `country`, `city`, and `captured_at`.
`GET /api/images` supports search and filters through query params such as `query`, `garment_type`, `style`, `material`, `color_palette`, `pattern`, `season`, `occasion`, `consumer_profile`, `country`, `city`, and `designer`.
`GET /api/filters` dynamically returns available filter values from stored image metadata.
`PATCH /api/images/{image_id}/annotations` updates human-entered designer tags and notes.
`DELETE /api/images/{image_id}` removes the database record and the uploaded local image file.

Uploaded images are classified through `backend/app/classifier.py`. The classifier currently returns placeholder metadata so the workflow is stable before connecting a real multimodal model.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The frontend can upload an image with optional designer and location context, render a searchable image grid, filter by dynamically generated garment, consumer, location, time, and designer metadata options, and review AI metadata plus human designer notes in a selected-image detail panel.

Backend tests:

```bash
./backend/.venv/bin/pytest
```

## Evaluation

Use 50-80 Pexels fashion or street-fashion images under `eval/images`, with manual labels in `eval/labels.json`. Start from `eval/labels.example.json`.

Prepare downloaded images with consistent names:

```bash
./backend/.venv/bin/python eval/prepare_images.py /path/to/raw/pexels-downloads --max-size 1024 --quality 85
```

This resizes each image to a maximum side length of 1024px, converts it to optimized JPEG, saves it under `eval/images` as `001.jpg`, `002.jpg`, and so on, and writes `eval/image_manifest.json`. Fill in `source_url` and `photographer` in that manifest where available.

Generate AI-assisted draft labels:

```bash
./backend/.venv/bin/python eval/draft_labels.py --images eval/images --manifest eval/image_manifest.json
```

This writes `eval/labels.draft.json`. Review and correct the draft labels manually, then save the final version as `eval/labels.json`. The draft is only a labeling aid; `eval/labels.json` should represent manually reviewed expected attributes.

Run:

```bash
./backend/.venv/bin/python eval/run_eval.py --labels eval/labels.json --images eval/images
```

The script writes `eval/results.json` and prints per-attribute accuracy. Empty expected values are skipped for that field, so visually ambiguous material or consumer labels do not unfairly count as errors.

Primary accuracy fields:

```text
garment_type
color_palette
pattern
season
occasion
location_scene
```

Secondary, more subjective fields:

```text
style
material
consumer_profile
```

Qualitative review only:

```text
description
trend_notes
```

Exact city and country are treated as user-provided context, not visually reliable model targets for Pexels images.

Current evaluation summary on 70 manually reviewed Pexels images:

| Field | Accuracy | Notes |
| --- | ---: | --- |
| garment_type | 0.971 | Strong on visible garment categories. |
| consumer_profile | 0.971 | Directionally useful, but still a subjective merchandising label. |
| style | 0.943 | Good when expected labels allow multiple valid styles. |
| color_palette | 0.943 | Strong on dominant visible colors. |
| pattern | 0.912 | Good for obvious solid, striped, embroidered, and graphic patterns. |
| season | 0.897 | Scored with light normalization such as autumn to fall. |
| material | 0.837 | Evaluated only when manually labeled as visually apparent; 27 ambiguous cases were skipped. |
| location_scene | 0.557 | Scored against a small controlled taxonomy rather than raw exact string matching. |

Scene-level location is normalized before scoring because raw scene labels are open-ended. For example, street, city street, sidewalk, and urban street are normalized to urban street. This is more meaningful than exact string matching, but still imperfect because some scenes are genuinely ambiguous, such as outdoor versus urban street. The model performs best on visually grounded attributes such as garment type, color palette, pattern, and broad occasion. Trend notes and natural-language descriptions are reviewed qualitatively because they are open-ended inspiration aids rather than strict classification fields.

## Environment Variables

Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY` when the real multimodal classifier is connected.

```text
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
DATABASE_PATH=backend/fashion.db
UPLOAD_DIR=backend/uploads
VITE_API_BASE_URL=http://localhost:8000
```

If `OPENAI_API_KEY` is not set, the backend falls back to deterministic placeholder metadata so upload and gallery flows still work locally.

## Next Steps

1. Add the labeled Pexels test set.
2. Add end-to-end tests.
