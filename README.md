# FinSight AI

Production-style fintech demo: **FastAPI backend** + **React (Vite) frontend**, with an optional legacy **Streamlit** UI.

## Architecture

```
FinSightAI/
├── backend/
│   ├── app.py           # Run API: python app.py (uses PORT, optional UVICORN_RELOAD=1)
│   ├── main.py          # FastAPI app
│   └── requirements.txt
├── frontend/            # React + Vite (plain CSS + Framer Motion + Recharts)
├── data/
│   └── users_data.json  # Shared JSON store (API + legacy Streamlit)
├── run.sh               # macOS/Linux: API + Vite + open browser
├── docker-compose.yml   # Optional: API only + data volume
├── render.yaml          # Optional: Render.com Blueprint
└── app.py               # Legacy Streamlit (optional)
```

## Quick start (one command)

From `FinSightAI/`:

```bash
chmod +x run.sh
./run.sh
```

This starts the API on **port 8000** (with reload), the Vite dev server on **5173**, and opens **http://localhost:5173** on macOS.

Prerequisites: **Node 18+**, **Python 3.11+**, and backend deps (`cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`).

## Backend API (FastAPI)

**Run** (from `FinSightAI/backend`):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Same as `uvicorn main:app --host 0.0.0.0 --port 8000` — use `UVICORN_RELOAD=1 python app.py` for reload without `run.sh`.

**Health:** `GET http://localhost:8000/health`

**Endpoints**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/analyze-expenses` | Dashboard analytics (JSON) |
| GET | `/get-transactions` | List transactions for `user_id` |
| POST | `/predict-spending` | Spending forecast |
| POST | `/chat-insights` | AI reply (OpenAI if `OPENAI_API_KEY`, else rules) |
| POST | `/transactions` | Add expense |
| POST | `/budget` | Set monthly budget |
| POST | `/import-bank` | Simulate bank import |

**CORS:** Defaults include `http://localhost:5173`. For production, set **`ALLOWED_ORIGINS`** to a comma-separated list (e.g. your Vercel URL). See `.env.example`.

## Frontend

**Requires Node.js 18+** (`npm`).

```bash
cd FinSightAI/frontend
npm install
npm run dev
```

Dev server proxies **`/api` → `http://localhost:8000`** (path strip: `/api` prefix removed before hitting the API).

**Production API URL:** set in Vite env (see below).

## Environment variables

Copy **`.env.example`** to `.env` and adjust. Do not commit secrets.

| Variable | Where | Purpose |
|----------|--------|---------|
| `OPENAI_API_KEY` | Backend / Render / Docker | Optional GPT for `/chat-insights` |
| `PORT` | Backend | Listen port (default `8000`; set automatically on Render) |
| `ALLOWED_ORIGINS` | Backend | CORS allowlist for deployed frontends |
| `VITE_API_BASE_URL` | **frontend** `.env.production` / Vercel | Full API origin, e.g. `https://finsight-api.onrender.com` (no trailing slash). Leave **empty** locally so the app uses `/api` + Vite proxy. |

**Vercel:** Project root = **frontend** (or set “Root Directory” to `frontend`). Add environment variable **`VITE_API_BASE_URL`** = your deployed API URL. Build: `npm run build`, output `dist`.

**Render / Railway:** Deploy the **`backend`** folder (or repo with start command `cd backend && python app.py`). Set **`ALLOWED_ORIGINS`** to your Vercel URL. Optional **`OPENAI_API_KEY`**.

## Docker (optional)

From `FinSightAI/` (repository root):

```bash
docker compose up --build
```

API: **http://localhost:8000**. Run the frontend separately with `cd frontend && npm run dev` so `/api` proxies to the container, or point `VITE_API_BASE_URL` at `http://localhost:8000` for static builds.

## Legacy Streamlit (optional)

```bash
cd FinSightAI
source .venv/bin/activate
pip install streamlit pandas plotly scikit-learn fpdf2
streamlit run app.py
```

## Data

- Primary store for API + legacy app: `data/users_data.json`

## Demo mode

The React app falls back to **offline demo data** if the API is unreachable; use the **Offline demo** toggle in the UI for a fully local demo.
