# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SDRAG Chainlit is a Python-based chat frontend for a hybrid RAG (Retrieval-Augmented Generation) architecture with a deterministic semantic layer. Part of a Master's thesis at Universidad de Guadalajara exploring how to reduce arithmetic hallucinations in LLM-powered Financial Planning & Analysis (FP&A) systems.

**Core principle:** LLMs explain results but don't calculate. Numbers come from Cube Core (deterministic semantic layer).

## Common Commands

```bash
# Install dependencies (always use uv, never pip)
uv sync

# Run locally (development)
chainlit run app.py
# Opens: http://localhost:8001

# Lint code
ruff check .

# Run tests
pytest
```

### Docker/Production

```bash
# Build
docker build -t sdrag-chainlit .

# Run
docker run -p 8001:8001 \
  -e OPENROUTER_API_KEY="..." \
  sdrag-chainlit
```

## Architecture

```
User → Chainlit (app.py) → Classification → Route Decision
                                              ↓
                        ┌───────────────────────────────────────┐
                        │  Semantic (FP&A)     │  Documental    │
                        │  → Cube Core         │  → OpenSearch  │
                        │  → DuckDB            │                │
                        └───────────────────────────────────────┘
                                              ↓
                        LLM (OpenRouter) generates explanation
                                              ↓
                        Response with cl.Step traceability
```

### Key Components

- **app.py**: Main application with query classification, mock data, and OpenRouter LLM integration
- **classify_query()**: Routes queries based on keyword detection (semantic vs documental)
- **cl.Step**: Chainlit traceability - shows 4 visible steps (Classification → SQL → Data → Explanation)
- **call_openrouter()**: Async LLM calls for explanations (not calculations)

### Backend Services (Distributed Cluster via Tailscale)

| Service | Host | Purpose |
|---------|------|---------|
| Chainlit | cfocoder3 (100.105.68.15) | Chat UI |
| n8n | cfocoder3 | Query router (future) |
| Cube Core | vostro (100.116.107.52) | Semantic SQL layer |
| Ollama | vostro | Local LLM inference |
| OpenSearch | macmini (100.110.109.43) | Vector database |
| MinIO | macmini | S3-compatible storage |

## Environment Variables

```bash
OPENROUTER_API_KEY=...              # Required for LLM explanations
OPENROUTER_MODEL=mistralai/devstral-2512:free
N8N_WEBHOOK_URL=http://100.105.68.15:5678/webhook/sdrag-query
CHAINLIT_USER=hector
CHAINLIT_PASSWORD=sdrag2025
```

## Code Style

- Line length: 100 characters (configured in pyproject.toml)
- Target Python: 3.11+
- Use `uv` for package management, never `pip`
- Minimal comments, simple code
- Use Vega-Altair for charts in Python scripts

## Project Structure

```
app.py                 # Main Chainlit application
pyproject.toml         # Dependencies and project config
Dockerfile             # Production container (port 8001)
.chainlit/config.toml  # Chainlit UI configuration
public/                # Web assets (logos, theme.json)
chainlit.md            # Welcome message shown to users
```

## Current Implementation Status

- **Phase 1-2 Complete**: Authentication, theming, cl.Step traceability, mock FP&A data
- **Phase 3 Next**: Document upload with Docling, OpenSearch integration
- **Future**: n8n router, Cube Core integration, Plotly visualizations

## Query Flow (app.py:234)

1. User sends message
2. `classify_query()` detects metric (revenue, COGS, etc.) and period (Q1-Q4 2024)
3. If financial query → generate SQL, get mock data, call LLM for explanation
4. If general query → call LLM directly
5. Response rendered with full traceability via `cl.Step`
