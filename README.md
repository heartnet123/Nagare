# Nagare (流)

> **AI Agents OS** — An open-source platform for building, evaluating, monitoring, and operating RAG pipelines and AI agent systems from a unified workspace.

## Overview

Nagare (流, meaning "flow") is a full-stack AI Operating System that provides a comprehensive workspace for managing AI agent workflows. It combines a **FastAPI** backend with a **Nuxt 4 + Nuxt UI** frontend to deliver a modern interface for interacting with RAG pipelines, evaluating agent performance, managing datasets, monitoring system health, and handling MCP (Model Context Protocol) server configurations.

## Features

| Feature | Description |
|---------|-------------|
| **Agent Management** | Create, configure, and manage AI agents with skill/tool integration |
| **Chat Interface** | Conversational UI for interacting with agents |
| **RAG Pipeline Evaluation** | Evaluate and benchmark retrieval-augmented generation pipelines |
| **Dataset Management** | Upload, version, and manage evaluation datasets |
| **System Monitoring** | Real-time metrics, logs, and system health tracking |
| **Knowledge Base** | Vector-powered memory and knowledge management (ChromaDB) |
| **MCP Server Management** | Configure and manage Model Context Protocol servers |
| **Analytics & Benchmarking** | Performance analysis and model comparison tools |

## Tech Stack

### Backend (`backend/`)

| Technology | Purpose |
|------------|---------|
| **Python 3** | Core language |
| **FastAPI 0.115** | REST API framework |
| **Uvicorn 0.32** | ASGI server |
| **Pydantic 2.9** | Data validation |
| **ChromaDB** | Vector database for memory/knowledge |
| **httpx** | Async HTTP client |

### Frontend (`frontend/`)

| Technology | Purpose |
|------------|---------|
| **Vue.js** | UI framework |
| **Nuxt 4** | Full-stack framework |
| **Nuxt UI 4** | Component library |
| **Tailwind CSS 4** | Utility-first styling |
| **Lucide Icons** | Icon system |
| **TypeScript 6** | Type safety |
| **pnpm** | Package manager |

## Project Structure

```
nagare/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── requirements.txt     # Python dependencies
│   ├── models/              # Pydantic domain models
│   ├── routers/             # API route handlers
│   │   ├── agents.py
│   │   ├── chat.py
│   │   ├── datasets.py
│   │   ├── evaluations.py
│   │   ├── logs.py
│   │   ├── mcp.py
│   │   ├── memory.py
│   │   └── monitoring.py
│   ├── services/            # Business logic layer
│   │   ├── agent/           # Agent core, LLM, tools, skills
│   │   ├── memory/          # Vector memory & knowledge
│   │   ├── data.py
│   │   └── knowledge.py
│   ├── middleware/          # Error handling middleware
│   ├── data/                # Runtime data storage
│   └── tests/               # Backend tests
├── frontend/
│   ├── app/
│   │   ├── app.vue          # Root Vue component
│   │   ├── pages/           # Route pages (14 routes)
│   │   ├── components/      # Reusable UI components
│   │   ├── composables/     # Vue composables (useApi)
│   │   ├── layouts/         # Layout components
│   │   └── utils/           # Utility functions
│   ├── nuxt.config.ts       # Nuxt configuration
│   ├── package.json
│   └── tsconfig.json
├── docs/                    # Documentation
├── LICENSE                  # AGPL-3.0
└── README.md
```

## Prerequisites

- **Python 3.10+** and `venv` (or `uv`)
- **Node.js 20+** and **pnpm** (install via `npm install -g pnpm`)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/nagare.git
cd nagare
```

### 2. Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Run the API server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Docs at `http://localhost:8000/docs` (Swagger UI).

### 3. Frontend setup

```bash
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

The frontend will be available at `http://localhost:3000`.

### 4. Environment configuration

The frontend connects to the backend API at `http://localhost:8000` by default.  
To override, create a `.env` file in the `frontend/` directory:

```bash
NUXT_PUBLIC_API_BASE=http://localhost:8000
```

## Scripts

### Backend

| Command | Description |
|---------|-------------|
| `uvicorn main:app --reload` | Start dev server with hot reload |
| `pytest` | Run test suite |

### Frontend

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start dev server (`localhost:3000`) |
| `pnpm build` | Build for production |
| `pnpm preview` | Preview production build |
| `pnpm lint` | Run ESLint |
| `pnpm typecheck` | Run TypeScript type checking |

## API Endpoints

The backend exposes the following route groups under `/api`:

| Prefix | Description |
|--------|-------------|
| `/api/evaluations` | RAG pipeline evaluation runs |
| `/api/agents` | AI agent CRUD |
| `/api/datasets` | Dataset management |
| `/api/monitoring` | System metrics |
| `/api/logs` | Log retrieval |
| `/api/chat` | Chat/completion endpoints |
| `/api/mcp/servers` | MCP server configuration |
| `/api/memory` | Knowledge/memory operations |

## License

[AGPL-3.0](./LICENSE)
