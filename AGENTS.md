# AGENTS.md

Instructions for AI coding agents working in this repository.

## Project Overview

SDRAG Chainlit is a Python chat frontend for a hybrid RAG architecture with a deterministic semantic layer. Part of a Master's thesis exploring how to reduce arithmetic hallucinations in LLM-powered FP&A systems.

**Core principle:** LLMs explain results but don't calculate. Numbers come from Cube Core (deterministic semantic layer).

## Commands

### Package Management
```bash
# Always use uv, never pip
uv sync                     # Install dependencies
uv add <package>           # Add new dependency
```

### Development
```bash
chainlit run app.py         # Run locally (http://localhost:8001)
```

### Linting
```bash
ruff check .                # Check all files
ruff check app.py           # Check single file
ruff check . --fix          # Auto-fix issues
```

### Testing
```bash
pytest                      # Run all tests
pytest tests/test_file.py   # Run single test file
pytest -k "test_name"       # Run test by name pattern
pytest -x                   # Stop on first failure
```

### Docker/Production
```bash
docker build -t sdrag-chainlit .
docker run -p 8001:8001 -e OPENROUTER_API_KEY="..." sdrag-chainlit
```

## Code Style

### Formatting
- Line length: **100 characters** (configured in pyproject.toml)
- Target Python: **3.11+**
- Use `ruff` for linting

### Imports
Order imports following this pattern (as seen in app.py):
```python
import chainlit as cl       # Third-party (alphabetical)
import os
import httpx
import time
import re
import pandas as pd
```

### Type Hints
Use type hints for function signatures:
```python
def classify_query(query: str) -> dict:
def get_mock_data(metric: str, period: str) -> dict:
async def call_openrouter(prompt: str) -> str:
```

### Naming Conventions
- **Constants:** UPPER_SNAKE_CASE (`MOCK_METRICS`, `SEMANTIC_KEYWORDS`)
- **Functions:** snake_case (`classify_query`, `generate_mock_sql`)
- **Variables:** snake_case (`detected_metric`, `query_lower`)
- **Chainlit decorators:** Use async functions with descriptive names

### Error Handling
Use try/except with specific error messages:
```python
try:
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
except Exception as e:
    return f"Error: {str(e)}"
```

### Docstrings
Keep minimal and functional:
```python
def classify_query(query: str) -> dict:
    """Clasifica la consulta y extrae metrica y periodo"""
```

### Chainlit Patterns
Use `cl.Step` for traceability:
```python
async with cl.Step(name="Step Name", type="tool") as step:
    step.input = "Input description"
    step.output = "Output result"
```

### Async HTTP Calls
Use httpx with context manager:
```python
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(url, headers=headers, json=payload)
```

## Architecture

```
User -> Chainlit (app.py) -> Classification -> Route Decision
                                                |
                         +----------------------+----------------------+
                         |                                             |
                   Semantic (FP&A)                              Documental
                   -> Cube Core                                 -> OpenSearch
                   -> DuckDB
                         |                                             |
                         +----------------------+----------------------+
                                                |
                         LLM (OpenRouter) generates explanation
                                                |
                         Response with cl.Step traceability
```

### Key Components
- **app.py**: Main application with query classification, mock data, OpenRouter integration
- **classify_query()**: Routes queries (semantic vs documental) at line 80
- **cl.Step**: Shows 4 visible steps (Classification -> SQL -> Data -> Explanation)
- **call_openrouter()**: Async LLM calls for explanations (not calculations)

## Environment Variables

```bash
OPENROUTER_API_KEY=...                           # Required for LLM
OPENROUTER_MODEL=mistralai/devstral-2512:free
N8N_WEBHOOK_URL=http://100.105.68.15:5678/webhook/sdrag-query
CHAINLIT_USER=hector
CHAINLIT_PASSWORD=sdrag2025
```

## Project Structure

```
app.py                  # Main Chainlit application (338 lines)
main.py                 # Placeholder entry point
pyproject.toml          # Dependencies and ruff config
Dockerfile              # Production container (port 8001)
.chainlit/config.toml   # Chainlit UI configuration
public/                 # Web assets (logos, theme.json)
chainlit.md             # Welcome message (English)
chainlit_es-ES.md       # Welcome message (Spanish)
```

## Guidelines from Copilot Instructions

From `.github/copilot-instructions.md`:
- Write minimum necessary code to deliver results
- Minimal comments, prefer simple and elegant code
- Don't overuse print statements or decorative lines
- Use Vega-Altair for charts in Python scripts
- Execute Python scripts with `python3`
- Limited emoji usage; only when adding value

## Tailscale Network

SSH access available without password:
```bash
ssh cfocoder3    # Chainlit host (100.105.68.15)
ssh macmini      # OpenSearch/MinIO (100.110.109.43)
ssh vostro       # Cube Core/Ollama (100.116.107.52)
ssh inspiron13
ssh inspiron15
```

## Anti-patterns to Avoid

1. **Never use pip** - always use `uv`
2. **Don't invent numbers** - LLMs explain, Cube Core calculates
3. **Avoid verbose comments** - keep code self-documenting
4. **Don't create unnecessary files** - prefer editing existing ones
5. **Avoid excessive print statements** - makes code noisy
