# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SDRAG Chainlit is a Python chat frontend for a hybrid RAG architecture with a deterministic semantic layer. Part of a Master's thesis at Universidad de Guadalajara exploring how to reduce arithmetic hallucinations in LLM-powered FP&A systems.

**Core principle:** LLMs explain results but don't calculate. Numbers come from Cube Core (deterministic semantic layer).

**Current Status:** Phase 1-2 complete (authentication, theming, traceability, mock data). Next: Phase 3 (Weaviate RAG) + Phase 3.5 (Dify integration).

## Commands

### Package Management
```bash
uv sync                     # Install dependencies
uv sync --all-extras        # Install with dev dependencies
uv add <package>            # Add new dependency
uv add --dev <package>      # Add dev dependency
uv remove <package>         # Remove dependency
```

### Development
```bash
chainlit run app.py         # Run locally (http://localhost:8001)
```

### Linting
```bash
ruff check .                # Check all files
ruff check . --fix          # Auto-fix issues
ruff format .               # Format code
```

### Testing
```bash
pytest                                            # Run all tests
pytest tests/test_file.py                         # Run single file
pytest tests/test_file.py::TestClass::test_method # Run specific test
pytest -k "test_classify"                         # Run by name pattern
pytest -x                                         # Stop on first failure
pytest -v --tb=short                              # Verbose, short traceback
```

### Docker
```bash
docker build -t sdrag-chainlit .
docker run -p 8001:8001 -e OPENROUTER_API_KEY="..." sdrag-chainlit
```

## Architecture

```
User → Chainlit (app.py) → n8n (classification) → Route Decision (3 routes)
                                                        ↓
                              ┌──────────────────────────────────────────────┐
                              │  Semantic (FP&A)   │  Documental │  Hybrid   │
                              │  → Cube Core       │  → Weaviate │  → Both   │
                              │  → DuckDB          │             │           │
                              └──────────────────────────────────────────────┘
                                                        ↓
                              Dify (explanation layer - post-calculation)
                                                        ↓
                              Response with cl.Step traceability
```

**Key principle**: Dify receives **already-calculated data** from Cube Core/Weaviate and only generates natural language explanations. It does NOT participate in query classification, SQL generation, or numerical calculations.

**Weaviate as only vector database**: Architectural simplification. GraphRAG limited to 1-2 hops via cross-references.

### Classification Routes

1. **Semantic** (metrics, aggregations) → Cube Core → DuckDB
2. **Documental** (textual context, definitions) → Weaviate
3. **Hybrid** (data + context) → Cube Core first, Weaviate to enrich

### Key Functions (app.py)

| Function | Line | Purpose |
|----------|------|---------|
| `classify_query()` | 80 | Routes queries by keyword detection (SEMANTIC_KEYWORDS, PERIOD_PATTERNS) |
| `generate_mock_sql()` | 135 | Generates SQL based on metric/period |
| `get_mock_data()` | 158 | Returns mock FP&A data from MOCK_METRICS dict |
| `call_openrouter()` | 182 | Async LLM calls for explanations (fallback for Dify) |
| `auth_callback()` | 171 | Password authentication handler using AUTHORIZED_USERS |
| `start()` | 218 | `@cl.on_chat_start` - sends welcome message |
| `main()` | 234 | `@cl.on_message` - Main message handler with 4 cl.Step stages |

**Message Flow in `main()`:**
1. Classification → determines route (semantic/documental) and extracts metric+period
2. SQL Generation → mock SQL for financial queries
3. Data Retrieval → fetch from MOCK_METRICS
4. Explanation → call OpenRouter (will be replaced by Dify in Phase 3.5)

### Mock Data Structure

**MOCK_METRICS** (app.py:27-58): Dictionary of FP&A metrics by period
- Metrics: `revenue`, `cogs`, `gross_margin`, `opex`, `ebitda`, `net_income`
- Periods: `Q1_2024`, `Q2_2024`, `Q3_2024`, `Q4_2024`, `2024`, `2023`
- Example: `MOCK_METRICS["revenue"]["Q4_2024"]` = 1_234_567

**SEMANTIC_KEYWORDS** (app.py:61-68): Keyword mapping for classification
- Maps metrics to Spanish/English keywords
- Example: `"revenue"` → `["revenue", "ventas", "ingresos", "sales", "facturación"]`

**PERIOD_PATTERNS** (app.py:70-77): Regex patterns for period detection
- Detects quarters: `r"q1.?2024"`, `r"primer.?trimestre.?2024"`
- Detects years: `r"\b2024\b"`, `r"\b2023\b"`
- Classification tries quarters first, falls back to years

**Classification Logic:**
1. Check for metric keywords (semantic) vs no match (documental)
2. Extract period using regex patterns (quarters preferred over years)
3. Default to "2024" if no period detected
4. Return `{"route": "semantic"|"documental", "metric": str|None, "period": str, "is_financial": bool}`

### cl.Step Traceability

Financial queries show 4 visible steps: Classification → SQL → Data → Explanation

```python
async with cl.Step(name="Classification", type="tool") as step:
    step.input = query
    classification = classify_query(query)
    step.output = f"Route: {classification['route']}"
```

Step types: `"tool"`, `"llm"`, `"embedding"`, `"retrieval"`

## Backend Services (Tailscale Cluster)

The system runs on a distributed cluster of 3 nodes connected via Tailscale. All services are accessible by hostname without passwords.

| Service | Host | URL/Access | Purpose |
|---------|------|------------|---------|
| Chainlit | cfocoder3 (100.105.68.15) | http://localhost:8001 | Chat UI (this app) |
| Coolify | cfocoder3 | - | Auto-deployment from GitHub |
| n8n | cfocoder3 | :5678/webhook/sdrag-query | Deterministic query router |
| Dask Scheduler | cfocoder3 | tcp://100.105.68.15:8786 | Distributed task coordination |
| Cube Core | vostro (100.116.107.52) | http://100.116.107.52:4000 | Semantic SQL layer |
| DuckDB | vostro | - | Analytical database for Cube |
| Ollama | vostro | http://100.116.107.52:11434 | Embeddings (nomic-embed-text, 768 dims) |
| Docling | vostro | - | PDF extraction (32GB RAM) |
| Dask Worker | vostro | - | Distributed processing |
| Dify | macmini (100.110.109.43) | http://100.110.109.43:80/v1 | Explanation layer (primary) |
| **Weaviate** | macmini | http://100.110.109.43:8080 | **Only vector database** |
| MinIO | macmini | - | S3-compatible storage |
| Dask Worker | macmini | - | Distributed processing |

**SSH Access:** `ssh cfocoder3`, `ssh macmini`, `ssh vostro` (passwordless via Tailscale)

**Deployment Flow:**
1. Push to GitHub main branch
2. Coolify (cfocoder3) auto-detects Dockerfile
3. Builds and deploys to `chainlit.sdrag.com`
4. Environment variables configured in Coolify UI

## Environment Variables

```bash
# Authentication
CHAINLIT_AUTH_SECRET=<secret-key>
CHAINLIT_USER=hector
CHAINLIT_PASSWORD=sdrag2025

# Dify (explanation layer - primary)
DIFY_API_URL=http://100.110.109.43:80/v1
DIFY_API_KEY=app-xxx

# OpenRouter (fallback/development)
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=mistralai/devstral-2512:free

# Weaviate
WEAVIATE_URL=http://100.110.109.43:8080

# Embeddings (Ollama)
OLLAMA_BASE_URL=http://100.116.107.52:11434
EMBEDDING_MODEL=nomic-embed-text

# Integrations
N8N_WEBHOOK_URL=http://100.105.68.15:5678/webhook/sdrag-query
CUBE_API_URL=http://100.116.107.52:4000
```

## Code Style

- Line length: 100 characters (configured in pyproject.toml)
- Python 3.11+
- Always use `uv`, never `pip`
- Use type hints for function signatures
- Minimal docstrings (Spanish or English)
- Use underscores for large numbers: `1_234_567`

### Async HTTP Calls
```python
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(url, headers=headers, json=payload)
```

## Project Structure & Important Files

```
app.py                  # Main Chainlit application (338 lines)
pyproject.toml          # Dependencies managed with uv
Dockerfile              # Production deployment configuration
.env.example            # Template for environment variables
ROADMAP.md              # High-level roadmap
roadmap/                # Detailed phase-by-phase implementation docs
  ├── README.md                      # Index for LLM agents
  ├── fase-0-infraestructura.md      # Infrastructure verification
  ├── fase-3-rag-documental.md       # Weaviate + Docling integration
  ├── fase-3.5-dify.md               # Dify explanation layer
  ├── fase-4-n8n-router.md           # Deterministic router
  ├── fase-5-cube-core.md            # Semantic layer integration
  ├── fase-8-benchmarks.md           # Academic evaluation
  └── comercializacion.md            # Post-thesis commercialization
services/               # Client modules for external services (empty, ready for Phase 3+)
tests/                  # Comprehensive test suite
  ├── conftest.py                    # Shared fixtures for all phases
  ├── test_classification.py         # Query classification tests
  ├── test_dify_client.py            # Dify integration tests
  └── test_*.py                      # Additional test modules
documentos_de_referencia_tesis/      # Research context and architecture docs
```

**Reading Roadmap Documentation:**
1. Start with `ROADMAP.md` for overview
2. Check `roadmap/README.md` for implementation guidance
3. Read specific phase files before implementing (e.g., `roadmap/fase-3-rag-documental.md`)
4. Each phase doc includes prerequisites, tasks with dependencies, and verification steps

## Current Status

**Phase 1-2 Complete:** Authentication, theming, cl.Step traceability, mock FP&A data, Coolify deployment

**Phase 3 (Next):** RAG Documental (Weaviate + Docling) - ~24h estimated

**Phase 3.5 (Critical):** Dify integration as explanation layer - ~11h estimated

**Phase 4-5:** n8n router + Cube Core integration - ~20h combined

**Phase 0 (Prerequisite):** Before starting Phase 3+, run verification in `roadmap/fase-0-infraestructura.md`

## Testing Strategy

**Test Files:** All fixtures in `tests/conftest.py` with comprehensive mocks for external services

**Key Fixtures:**
- `mock_dify_api` - Mock Dify responses
- `mock_weaviate_client` - Mock Weaviate operations
- `mock_ollama_embeddings` - Mock embeddings (768 dims)
- `mock_cube_core_api` - Mock Cube Core responses
- `mock_env_vars` - Set all environment variables for tests

**Test Organization:**
- One test file per phase (e.g., `test_dify_client.py` for Phase 3.5)
- Use async fixtures for async operations
- Mock all external HTTP calls (no real API calls in tests)
- Target 80% coverage for critical functions

**Running Tests:**
```bash
pytest                              # All tests
pytest tests/test_dify_client.py    # Specific phase
pytest -k "test_classify"           # By pattern
pytest --cov=. --cov-report=html    # With coverage
```

## Anti-patterns to Avoid

1. **Never use pip** - always use `uv` for package management
2. **Don't invent numbers** - LLMs explain, Cube Core calculates (core principle)
3. **Avoid verbose comments** - keep code self-documenting
4. **Don't create unnecessary files** - prefer editing existing ones
5. **Avoid excessive print statements** - makes code noisy
6. **Never mock in production code** - mocks belong in `tests/conftest.py` only
7. **Don't skip Phase 0 verification** - always verify infrastructure before implementing new phases
