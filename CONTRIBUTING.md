# Contributing

Thanks for contributing to Grab YT Comments.

## Ground Rules

- Keep module responsibilities separated:
  - `backend/scraper.py`: YouTube API and scraping logic only
  - `backend/classifier.py`: classification logic only
  - `backend/api.py`: HTTP API orchestration only
  - `backend/app.py`: Gradio UI only
- Do not hardcode secrets.
- Prefer small, readable functions with minimal, useful type hints.
- Preserve existing behavior unless the change request explicitly requires a behavior change.

## Development Setup

1. Install backend dependencies:

```bash
cd backend
uv sync
```

2. Create `backend/.env`:

```env
YOUTUBE_API_KEY=your_youtube_api_key_here
```

Optional local LLM settings:

```env
LOCAL_LLM_URL=http://127.0.0.1:8080/v1/chat/completions
LOCAL_LLM_MODEL=LiquidAI/LFM2.5-350M-GGUF:Q4_K_M
CLASSIFICATION_REQUEST_TIMEOUT=30
```

3. Install frontend dependencies:

```bash
cd frontend
npm install
```

## Run Locally

- Backend API:

```bash
cd backend
uv run python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

- Frontend:

```bash
cd frontend
npm run dev
```

- Gradio app (optional):

```bash
cd backend
uv run python app.py
```

## Making Changes

1. Create a branch from `main`.
2. Make focused, minimal changes.
3. Keep API contracts stable where possible.
4. Update docs when behavior or setup changes.

## Validation Checklist

### Backend
From the `backend/` directory (or repo root with uv):

```bash
python -m py_compile app.py api.py scraper.py classifier.py
uv run pytest tests/ -q
```

### Frontend
```bash
cd frontend
npm run typecheck
npm run lint
npm run test:run
npm run build
```

These checks (plus more) run automatically via GitHub Actions on every push and pull request.

## Pull Request Guidelines

- Use a clear title and summary.
- Explain:
  - what changed
  - why it changed
  - how it was validated
- Include screenshots/GIFs for UI changes.
- Note any required environment variable or migration changes.

## Security and Secrets

- Never commit `.env` files or API keys.
- Never print secrets in logs.
- Sanitize user-controlled strings before logging or storing if needed.

## Reporting Bugs

Please include:

- steps to reproduce
- expected behavior
- actual behavior
- relevant logs/errors (with secrets removed)
- environment details (OS, Python version, Node version)
