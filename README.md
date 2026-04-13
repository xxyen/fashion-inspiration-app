# Fashion Inspiration App

Initial project scaffold for a fashion inspiration image library.

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

The only endpoint for now is:

```text
GET /api/health
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Environment Variables

Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY` when the real multimodal classifier is connected.

```text
OPENAI_API_KEY=
DATABASE_PATH=backend/fashion.db
UPLOAD_DIR=backend/uploads
VITE_API_BASE_URL=http://localhost:8000
```

## Next Steps

1. Add image upload storage and the first `/api/images` endpoint.
2. Build the gallery UI around stored image records.
3. Add the AI classification service boundary.
4. Add search, filters, designer annotations, evaluation, and tests.
