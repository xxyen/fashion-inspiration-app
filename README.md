# Fashion Inspiration App

Initial project scaffold for a fashion inspiration image library. The app currently supports image upload, a basic gallery backed by SQLite, and an AI classification boundary with deterministic placeholder metadata.

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
DELETE /api/images/{image_id}
```

`POST /api/images` accepts multipart form data with an `image` file and optional context fields: `designer`, `continent`, `country`, `city`, and `captured_at`.
`GET /api/images` supports search and filters through query params such as `query`, `garment_type`, `style`, `material`, `color_palette`, `pattern`, `season`, `occasion`, `consumer_profile`, `country`, `city`, and `designer`.
`GET /api/filters` dynamically returns available filter values from stored image metadata.
`DELETE /api/images/{image_id}` removes the database record and the uploaded local image file.

Uploaded images are classified through `backend/app/classifier.py`. The classifier currently returns placeholder metadata so the workflow is stable before connecting a real multimodal model.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The frontend can upload an image with optional designer and location context, then renders the stored image records and AI metadata returned by `GET /api/images`.

Backend tests:

```bash
./backend/.venv/bin/pytest
```

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

1. Add frontend search and filter controls.
2. Add designer annotations, evaluation, and end-to-end tests.
