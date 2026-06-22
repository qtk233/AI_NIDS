# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NIDS (Network Intrusion Detection System) — deep learning-based network intrusion detection using a multi-modal Transformer. Classifies network traffic into known attack types and detects unknown attacks via OpenMax.

## Repository Layout

The `nids/` directory is the monorepo root. Everything (backend, frontend, data, checkpoints) lives under it. The top-level `.env`, `reasonix.toml`, and `headroom_ai-*.whl` are not part of the application.

```
nids/
├── backend/           # FastAPI + PyTorch backend
│   ├── main.py        # FastAPI app entry point (CORS, routers, exception handlers)
│   ├── core/          # config (pydantic-settings), database (async SQLAlchemy), exceptions
│   ├── models/        # PyTorch nn.Module components (see model architecture below)
│   ├── engine/        # Detection pipeline: preprocessor, feature extractor, detector
│   ├── api/           # REST routers: system, detect, alerts, model, ws (WebSocket)
│   ├── db/            # SQLAlchemy ORM models + CRUD (detection_logs, model_versions, experiments)
│   ├── schemas/       # Pydantic request/response schemas
│   ├── training/      # Dataset, Trainer, metrics
│   └── tests/         # unit/ and integration/ (pytest)
├── frontend/          # React 18 + TypeScript + Tailwind CSS 4 + Vite
│   └── src/
│       ├── pages/     # 6 page components
│       ├── components/# Layout, StatCard, FlowTable
│       ├── hooks/     # useApi, useWebSocket
│       └── lib/       # api client, types (ApiResponse<T>, DetectionResult, etc.)
├── data/              # Raw training datasets
├── processed/         # Preprocessed .pt tensor files
├── checkpoints/       # Saved model weights (best.pt)
├── train.py           # Training entry point (argparse + MLflow)
└── init_db.sql        # MySQL schema (detection_logs, model_versions, experiments)
```

## Model Architecture

**Multi-modal Transformer with late fusion + OpenMax for open-set recognition:**

- `StatEncoder` — Transformer encoder over 80-dim statistical flow features
- `PayloadEncoder` — Transformer encoder over byte-level payload sequences (vocab 256, max_len 2560)
- `LateFusionClassifier` — concatenates both encoders' [CLS] embeddings → MLP → class logits
- `OpenMax` — recalibrates logits using Weibull distribution on class-wise mean activation vectors; rejects samples below a distance threshold as "unknown"

Wrapper: `NIDSModel` composes StatEncoder + PayloadEncoder + fusion into a single `nn.Module`.

## Common Commands

### Backend (Python/FastAPI)

```bash
cd nids
source venv/Scripts/activate    # Windows
# source venv/bin/activate      # Linux/Mac

# Start API server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Run all tests
pytest backend/tests/ -v

# Run tests with coverage
pytest backend/tests/ -v --cov=backend --cov-report=term-missing

# Run a single test file
pytest backend/tests/unit/test_openmax.py -v

# Train a model
python train.py --stat processed/train_stat.pt --payload processed/train_payload.pt \
                --labels processed/train_labels.pt \
                --val-stat processed/val_stat.pt --val-payload processed/val_payload.pt \
                --val-labels processed/val_labels.pt --epochs 100 --batch-size 64
```

### Frontend (React/TypeScript)

```bash
cd nids/frontend

# Install dependencies
npm install

# Dev server (http://localhost:5173)
npm run dev

# Type-check + build
npm run build

# Lint
npm run lint

# Run Playwright E2E tests
npx playwright test

# Run a single E2E spec
npx playwright test test_navigation.spec.ts
```

### Database

```bash
# Initialize MySQL schema
mysql -u root -p < nids/init_db.sql
```

## Environment Configuration

Copy `nids/.env.example` to `nids/backend/.env` (pydantic-settings reads `.env` from the working directory):

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `mysql+aiomysql://root@localhost:3306/nids` | Async MySQL via aiomysql |
| `MODEL_CHECKPOINT` | `checkpoints/best.pt` | Path to trained model weights |
| `HOST` | `127.0.0.1` | API bind address |
| `PORT` | `8000` | API port |
| `BATCH_SIZE` | `64` | Inference batch size |
| `WS_CACHE_SIZE` | `200` | WebSocket history buffer |

## API Design

All endpoints follow a uniform envelope: `{success: boolean, data: T | null, error: string | null, meta?: {...}}`.

| Router | Endpoints | Purpose |
|---|---|---|
| `system` | `/api/system/stats`, `/api/system/health` | System stats, health check |
| `detect` | `/api/detect/pcap` (POST multipart) | Upload PCAP for detection |
| `alerts` | `/api/alerts`, `/api/alerts/{id}` | Paginated alert CRUD |
| `model` | `/api/model/info`, `/api/model/metrics` | Model version & evaluation metrics |
| `ws` | `/ws/detections` | Real-time detection push via WebSocket |

## Frontend Routing

| Route | Page | Key Features |
|---|---|---|
| `/dashboard` | Dashboard | StatCard stats, trend charts (Recharts), attack distribution |
| `/live` | LiveDetection | WebSocket real-time detection feed |
| `/traffic/:id` | TrafficDetail | Metadata, SHAP explanation, attention heatmap |
| `/bigscreen` | BigScreen | Full-screen D3.js topology graph + attack timeline |
| `/history` | History | Alert search/filter/pagination/export |
| `/model` | ModelManagement | Model version info, confusion matrix, ROC curve |

## Testing

- **Backend unit tests:** `nids/backend/tests/unit/` — model layers, config, dataset, metrics, preprocessing
- **Backend integration tests:** `nids/backend/tests/integration/` — API endpoints via httpx, WebSocket, full pipeline
- **Frontend E2E tests:** `nids/frontend/e2e/` — Playwright tests for dashboard, navigation, live detection
- Fixtures in `conftest.py` provide a small `NIDSModel` and `Detector` instance for tests

## Key Patterns

- **Backend imports use the `backend.` prefix** (e.g., `from backend.models.nids_model import NIDSModel`) — Python path is set from the `nids/` directory
- **Async SQLAlchemy** throughout — all DB operations use `AsyncSession` with `async_sessionmaker`
- **Frontend API client** (`lib/api.ts`) wraps fetch with a generic `request<T>()` helper; all responses are typed as `ApiResponse<T>`
- **Tailwind CSS 4** with the Vite plugin (not PostCSS config)
- **React Router v7** with `<Layout>` as a wrapper component providing sidebar navigation
