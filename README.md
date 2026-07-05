# Grab YT Comments

This helps you read YouTube comments without drowning in the noise.
It extracts comments from any video URL and classifies them locally with **LFM2.5-350M**, giving you a clear dashboard of what people are asking, praising, criticizing, joking about, or pushing back on.

![Demo GIF](media/animation.gif)

## Project Structure

```text
grab-yt-comments/
|-- backend/
|   |-- api.py              # FastAPI API for the React frontend
|   |-- app.py              # Existing Gradio UI entrypoint
|   |-- scraper.py          # YouTube Data API comment scraping
|   |-- classifier.py       # LLM classification and SQLite persistence
|   |-- pyproject.toml      # Backend dependencies for uv
|   |-- requirements.txt    # Backend dependencies for pip-style deploys
|   |-- uv.lock
|   `-- .gitignore
|-- frontend/
|   |-- App.tsx
|   |-- services/
|   |-- components/
|   |-- package.json
|   `-- .gitignore
|-- .gitignore
|-- LICENSE
`-- README.md
```

## Prerequisite:

Desktop usage is Windows-first.

Scraping requires a YouTube API key.
Classification is optional and only works when a local OpenAI-compatible model server is already running.

<details>
<summary><strong>Optional local LLM for classification</strong></summary>

If you want AI labels in the desktop app, install and start **LFM2.5-350M** with `llama.cpp`.

1. Install `llama.cpp`:

```bash
winget install llama.cpp
```

2. Start the model server:

```bash
llama-server -hf LiquidAI/LFM2.5-350M-GGUF:Q4_K_M
```

Once started, the server is available at `http://localhost:8080`.

</details>

## Desktop Setup

Set your YouTube API key in your Windows user environment before launching the installed desktop app:

```powershell
[Environment]::SetEnvironmentVariable("YOUTUBE_API_KEY", "your_youtube_api_key_here", "User")
```

Optional classification settings:

```powershell
[Environment]::SetEnvironmentVariable("LOCAL_LLM_URL", "http://127.0.0.1:8080/v1/chat/completions", "User")
[Environment]::SetEnvironmentVariable("LOCAL_LLM_MODEL", "LiquidAI/LFM2.5-350M-GGUF:Q4_K_M", "User")
[Environment]::SetEnvironmentVariable("CLASSIFICATION_REQUEST_TIMEOUT", "30", "User")
```

Restart the desktop app after changing environment variables so the packaged backend picks them up.

If you are running the desktop app from source instead of the installer:

```bash
cd backend
uv sync
cd ../frontend
npm install
```

For source-based desktop development, you can still use `backend/.env`:

```text
YOUTUBE_API_KEY=your_youtube_api_key_here
LOCAL_LLM_URL=http://127.0.0.1:8080/v1/chat/completions
LOCAL_LLM_MODEL=LiquidAI/LFM2.5-350M-GGUF:Q4_K_M
CLASSIFICATION_REQUEST_TIMEOUT=30
```

## Run The App

For the packaged desktop app:

1. Build the Windows installer:

```bash
cd frontend
npm run dist:win
```

2. Install `frontend/release-desktop/GrabComments-Setup-0.0.0.exe`.
3. Launch **GrabComments**. Electron opens the desktop window and starts the bundled FastAPI backend sidecar automatically.

For desktop development from source:

1. Start the React renderer:

```bash
cd frontend
npm run dev
```

2. In a second terminal, launch Electron:

```bash
cd frontend
npm run desktop:dev
```

The desktop shell connects to its backend automatically. In development it starts FastAPI from `backend/` on `http://127.0.0.1:8000` unless you override the desktop backend environment variables.

## Existing Gradio App

The original Gradio workflow is still available and remains separate from the desktop boot path:

```bash
cd backend
uv run python app.py
```

## Classification Labels

When classification is enabled, comments are classified with the local OpenAI-compatible LLM endpoint into:

- `appreciation`
- `humor`
- `questions`
- `criticism`
- `personal experience`
- `feedback`
- `spam`

The backend stores scraped comments first, classifies each saved comment, writes labels back to SQLite, and returns the final result from the database.
