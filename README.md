# Bonsai 2.0 — Synthetic youth social post generator

Minimal research tool that generates **one** synthetic Snapchat / Instagram / TikTok-style post per request for studies involving users aged **10–16**.

No accounts, database, or post library. Nothing is persisted server-side.

## Stack

| Layer | Tech |
| --- | --- |
| Frontend | Next.js (App Router) + React + Tailwind — `frontend/` |
| Backend | FastAPI + OpenAI Python SDK + httpx — `backend/` |

## Features

- Inputs: platform, format (`text` / `image` / `video`), topic, tone, context, values, optional constraints
- Generation: GPT caption + platform styling; OpenAI Images for photos; fal.ai text-to-video for short vertical clips
- Output: in-browser preview + download (`.txt`, `.png`, `.mp4`, or `.zip` when caption + media)

## Required API access

| Capability | Provider | Env var | Notes |
| --- | --- | --- | --- |
| Captions / planning | OpenAI GPT | `OPENAI_API_KEY` | Default model `gpt-4o-mini` |
| Images | OpenAI Images | `OPENAI_API_KEY` | Default model `gpt-image-1.5` (vertical `1024x1536`) |
| Video (~10s) | fal.ai | `FAL_KEY` | **Required for video.** OpenAI Sora / Videos API was shut down (2026-09-24). Default model `fal-ai/minimax/video-01` |

Copy `backend/.env.example` → `backend/.env` and fill in keys.

## Setup

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# ensure .env has OPENAI_API_KEY (and FAL_KEY if using video)
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000/generate](http://localhost:3000/generate).

API: `POST http://127.0.0.1:8000/api/generate`

## Limitations

- **One post per request** — no batching or history
- **No storage** — response includes base64 preview + download payload only
- **Video length** is approximate (~5–10s depending on fal model); not guaranteed exact 10 seconds
- **Video needs `FAL_KEY`**; text/image work with OpenAI alone
- Image/video APIs may refuse prompts that trip safety filters
- Content is **synthetic and fictional** — never copies real creators or identities
- Mildly concerning themes (FOMO, exclusion, etc.) are allowed for research but kept non-graphic; sexual / exploitative content involving minors is blocked in the system prompt
- Large video responses are embedded as base64 (fine for a prototype; not for production scale)

## Safety intent

This tool is for **research stimuli** about youth social media. Prompts instruct the model to invent anonymous fictional teens, match platform vernacular, and avoid sexual content, grooming, self-harm instructions, and illegal how-tos.
