# Imagulator (MRI + Flywheel MVP)

## What is this?
Clinician-friendly MRI app: fetch from Flywheel, register (Greedy), segment (SynthSeg / WMH-SynthSeg), write BIDS derivatives, view overlays, draft LLM summaries.

## Quickstart
### API (Python)
python3 -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt
uvicorn app.main:app --reload --port 8000 --app-dir api
# http://localhost:8000/healthz

### UI (React/Vite)
cd ui
npm install
npm run dev -- --host
# http://localhost:5173

## Env Vars
Copy `.env.example` → `.env`, fill values (not committed).
- FW_API_KEY=
- API_PORT=8000
- UI_PORT=5173

## Repo Layout
api/    # FastAPI app
ui/     # React app
engine/ # image pipelines
agents/ # LLM + tool calling (later)
configs/ tests/ docs/

## Common Commands
pytest -q api
npm run build --prefix ui

## Troubleshooting
- CORS: ensure API allows http://localhost:5173
- Node version: nvm use (see .nvmrc)