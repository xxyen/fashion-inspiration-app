# Fashion Inspiration App

Initial project scaffold for a fashion inspiration image library. The app currently supports image upload, a searchable gallery backed by SQLite, AI classification, and designer annotations.

The planned stack is:

- Frontend: React, Vite, TypeScript, Tailwind CSS
- Backend: Python, FastAPI
- Database: SQLite

## Structure

```text
app/                    Application source
app/backend/            FastAPI app
app/backend/app/        Backend package, schema, classifier, and API routes
app/backend/uploads/    Local upload storage
app/frontend/           React + Tailwind app
app/frontend/e2e/       Playwright end-to-end tests
eval/                   Evaluation script and labeled test set
tests/backend/          Backend unit and integration tests
```

## Local Setup

Backend:

```bash
cd app/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The API starts at `http://localhost:8000`. On startup, the backend initializes the SQLite schema in `app/backend/app/schema.sql`.

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

Uploaded images are classified through `app/backend/app/classifier.py` with the configured multimodal model. If no API key is configured, the classifier returns deterministic placeholder metadata so the upload and gallery workflow remains testable.

Frontend:

```bash
cd app/frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The frontend can upload an image with optional designer and location context, render a searchable image grid, filter by dynamically generated garment, consumer, location, time, and designer metadata options, and review AI metadata plus human designer notes in a selected-image detail panel.

Backend tests:

```bash
./app/backend/.venv/bin/python -m pytest
```

Frontend build:

```bash
cd app/frontend
npm run build
```

End-to-end test:

```bash
cd app/frontend
npm run test:e2e
```

The E2E test starts its own backend and frontend servers on `127.0.0.1:8010` and `127.0.0.1:5174`, uses a temporary SQLite database under `/tmp`, clears `OPENAI_API_KEY` so classification is deterministic, and runs with the locally installed Google Chrome browser. The Playwright spec lives under `app/frontend/e2e` because it runs through the frontend package and its local Playwright dependency.

## Deliverables

| Area | Status | Notes |
| --- | --- | --- |
| Image upload and storage | [x] Done | Uploads local images and stores metadata in SQLite. |
| AI classification | [x] Done | Uses a multimodal model to return a description and structured attributes. |
| Search and filters | [x] Done | Supports text search and dynamic filters from stored metadata. |
| Designer annotations | [x] Done | Designers can add tags and notes separate from AI output. |
| Model evaluation | [x] Done | Uses 70 manually reviewed Pexels images and reports per-field accuracy. |
| Testing | [x] Done | Includes parser tests, filter integration tests, and one upload/classify/filter E2E test. |
| README and architecture notes | [x] Done | Documents setup, trade-offs, evaluation, and next steps. |

## Evaluation

Use 70 Pexels fashion images under `eval/images`, with manual labels in `eval/labels.json`. Start from `eval/labels.example.json`.

Prepare downloaded images with consistent names:

```bash
./app/backend/.venv/bin/python eval/prepare_images.py /path/to/raw/pexels-downloads --max-size 1024 --quality 85
```

This resizes each image to a maximum side length of 1024px, converts it to optimized JPEG, saves it under `eval/images` as `001.jpg`, `002.jpg`, and so on, and writes `eval/image_manifest.json`. Fill in `source_url` and `photographer` in that manifest where available.

Generate AI-assisted draft labels:

```bash
./app/backend/.venv/bin/python eval/draft_labels.py --images eval/images --manifest eval/image_manifest.json
```

This writes `eval/labels.draft.json`. Review and correct the draft labels manually, then save the final version as `eval/labels.json`. The draft is only a labeling aid; `eval/labels.json` should represent manually reviewed expected attributes.

Run:

```bash
./app/backend/.venv/bin/python eval/run_eval.py --labels eval/labels.json --images eval/images
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
| pattern | 0.926 | Good for obvious solid, striped, embroidered, and graphic patterns. |
| occasion | 0.971 | Strong on broad use cases such as casual, formal, and workwear. |
| season | 0.897 | Scored with light normalization such as autumn to fall. |
| material | 0.837 | Evaluated only when manually labeled as visually apparent; 27 ambiguous cases were skipped. |
| location_scene | 0.571 | Scored against a small controlled taxonomy rather than raw exact string matching. |

Scene-level location is normalized before scoring because raw scene labels are open-ended. For example, street, city street, sidewalk, and urban street are normalized to urban street. This is more meaningful than exact string matching, but still imperfect because some scenes are genuinely ambiguous, such as outdoor versus urban street. The model performs best on visually grounded attributes such as garment type, color palette, pattern, and broad occasion. Trend notes and natural-language descriptions are reviewed qualitatively because they are open-ended inspiration aids rather than strict classification fields.

## Model and Labeling Notes

The app uses `gpt-4.1-mini` by default because it gives a practical balance between visual reasoning quality, speed, and cost for a small proof of concept. A larger vision model could improve subtle fields like material, style, or scene context, but would likely be slower and more expensive. A smaller model could be faster, but may return weaker fashion attributes. The model is configurable through `OPENAI_MODEL`, so the classifier can be swapped without changing the app flow.

The ground-truth labels in `eval/labels.json` were manually reviewed from 70 Pexels fashion images. Labels focus on visible evidence: garment type, color, pattern, broad occasion, season, and scene. Subjective fields such as style and consumer profile allow multiple valid labels when reasonable. Very open-ended fields such as description and trend notes are used for qualitative review rather than exact accuracy.

Images are normalized before evaluation with `eval/prepare_images.py`: they are renamed consistently, resized to a maximum side length, converted to JPEG, and EXIF orientation is applied. This keeps the test set small and consistent while preserving enough visual detail for classification.

Model output is normalized before storage and scoring. The parser removes optional fenced JSON, validates the response with Pydantic schemas, converts scalar values into lists for list-based fields, and uses aliases during evaluation for fields like season and location scene. This reduces failures from small wording differences such as `autumn` versus `fall`.

The prompt asks the model to return only JSON with a fixed schema and to avoid guessing exact city, country, or continent from visual appearance. This improves parsing reliability and reduces false precision. The trade-off is that the output is less free-form, but it is easier to store, filter, and evaluate.

## POC Trade-offs

The main goal for the one-day proof of concept was to make the core workflow work end to end: upload image, classify it, store it, search it, filter it, annotate it, and evaluate the model. I chose simple, local components first so the app is easy to run and review.

| Decision | Why | Trade-off |
| --- | --- | --- |
| SQLite instead of a hosted database | Fast local setup and enough for a small image library. | Not designed for large multi-user production traffic. |
| Synchronous classification | Simpler flow and easier to test in a short timebox. | Slow model calls block the upload response. |
| Dynamic filters from stored records | Avoids hardcoded fashion taxonomies and reflects the actual library. | Filter quality depends on model output quality. |
| Manual reviewed labels for eval | Gives a realistic small test set for model quality. | Labels are still subjective, especially style and consumer profile. |
| Pexels images | Easy to collect open fashion images quickly. | Not a perfect match for private field research images. |

## Designer Notes Usage

Designer notes are not just comments. In the current app, designer tags and notes are stored separately from AI metadata and are included in search, so human context can help users find images later.

With clear user consent, these notes could improve the system over time:

| Use | Benefit | Guardrail |
| --- | --- | --- |
| Better search ranking | Match designer language, not only AI labels. | Keep notes separate from AI-generated fields. |
| Label guideline improvement | Find common words designers use for style, mood, and trend. | Review patterns manually before changing labels. |
| Model evaluation | Compare AI output with trusted human notes. | Use reviewed notes, not every raw note. |
| Future model tuning | Build better prompts or examples from real designer language. | Use only opted-in data and avoid private context. |

The trade-off is trust. Designer notes may be more useful than generic AI labels, but they can include subjective or sensitive context. For a production system, notes should only be used for learning after opt-in, with clear data boundaries.

## Tech Choices

| Choice | Reason |
| --- | --- |
| React + Vite | Good fit for a small interactive gallery. Faster and simpler than a full Next.js app for this scope. |
| Tailwind CSS | Quick to build consistent layout and states without adding a UI framework. |
| Python + FastAPI | Simple API layer, strong validation with Pydantic, and easy integration with image/model scripts. |
| SQLite | Minimal setup and easy local review. |
| OpenAI multimodal model | Good enough visual reasoning for a POC and easy to swap through `OPENAI_MODEL`. |
| Playwright | Covers the real browser flow from upload to filter. |

I did not use Next.js because server-side rendering and routing were not needed for this workflow. I did not use Node or Java on the backend because Python kept the model, image processing, evaluation, and API code in one language. The hardest part was making model output reliable enough for filtering and evaluation. I handled that with a strict JSON prompt, Pydantic validation, parser tests, and normalization for fields such as season and scene.

## Future Priorities

If I had more time, I would improve in this order:

| Priority | Work | Good standard |
| --- | --- | --- |
| 1 | Improve labels and evaluation | Clear labeling rules, more images, and a second reviewer for subjective fields. |
| 2 | Improve classifier workflow | Async `processing` / `ready` / `failed` states, retry action, and no blocking upload. |
| 3 | Improve model quality | Compare models and prompts on the same test set, then choose based on accuracy, latency, and cost. |
| 4 | Improve image scale | Thumbnails, pagination, and better lazy loading for larger libraries. |
| 5 | Use designer notes with consent | Improve search and model prompts from reviewed human language. |
| 6 | Improve product polish | Better empty states, bulk upload, and clearer annotation workflows. |

The standard is not perfect accuracy. For this product, a good result means objective fields such as garment type, color, pattern, and occasion are reliable enough for search, while subjective fields are clearly presented as AI suggestions that designers can refine.

## Environment Variables

Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY` when the real multimodal classifier is connected.

```text
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
DATABASE_PATH=app/backend/fashion.db
UPLOAD_DIR=app/backend/uploads
VITE_API_BASE_URL=http://localhost:8000
```

If `OPENAI_API_KEY` is not set, the backend falls back to deterministic placeholder metadata so upload and gallery flows still work locally.

## UX and Scalability Notes

The current proof of concept keeps the upload flow synchronous: the backend saves the image, runs classification, stores the metadata, and then returns the completed record. The frontend reflects this with an `Analyzing image...` upload state so users know the image is being processed rather than only transferred.

For larger libraries, gallery images use lazy browser loading so off-screen images do not block the initial view. A production version would also add paginated image APIs and generated thumbnails so the grid does not fetch or render the full library at once.

For slower classifiers, the next architectural step would be asynchronous classification: create the image record immediately with a `processing` status, show the image in the gallery right away, run multimodal classification in the background, then update the record to `ready` or `failed`. The UI could show processing badges, skeleton metadata, and a retry action for failed classifications.

## Next Steps

1. Polish the assignment.
