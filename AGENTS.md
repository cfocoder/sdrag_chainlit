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
uv add <package>            # Add new dependency
uv add --dev <package>      # Add dev dependency
uv remove <package>         # Remove dependency
```

### Development
```bash
chainlit run app.py         # Run locally (http://localhost:8001)
python3 app.py              # Alternative entry point
```

### Linting
```bash
ruff check .                # Check all files
ruff check app.py           # Check single file
ruff check . --fix          # Auto-fix issues
ruff format .               # Format code
```

### Testing
```bash
# Run all tests
pytest

# Run single test file
pytest tests/test_classification.py
pytest tests/test_dify_client.py

# Run specific test method in a class
pytest tests/test_classification.py::TestClassifyQuery::test_semantic_revenue_query

# Run by name pattern (substring match - most flexible)
pytest -k "test_classify"        # Runs all tests with "classify" in name
pytest -k "semantic"             # Runs all tests with "semantic" in name
pytest -k "revenue"              # Runs all tests with "revenue" in name

# Useful flags
pytest -x                        # Stop on first failure
pytest -v                        # Verbose output
pytest -vv                       # Extra verbose (show full diff)
pytest --tb=short                # Shorter traceback format
pytest --tb=no                   # No traceback (just pass/fail)
pytest -s                        # Show print statements (disable capture)

# With coverage
pytest --cov=. --cov-report=html
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
- Use `ruff` for linting and formatting
- Follow PEP 8 guidelines

### Imports
Order imports following this pattern (as seen in app.py:7-12):
```python
import chainlit as cl       # Third-party first (alphabetical)
import os                   # Then standard library (alphabetical)
import httpx
import time
import re
import pandas as pd
```

**Import rules:**
- One import per line (except `from x import a, b`)
- Group: third-party → standard library → local
- Alphabetically within each group
- **Note:** This codebase uses third-party first, then standard library

### Type Hints
Always use type hints for function signatures (app.py:80, 135, 161):
```python
def classify_query(query: str) -> dict:
def generate_mock_sql(metric: str, period: str) -> str:
async def call_openrouter(prompt: str) -> str:
```

### Naming Conventions
- **Constants:** UPPER_SNAKE_CASE (`MOCK_METRICS`, `SEMANTIC_KEYWORDS`, `N8N_WEBHOOK_URL`)
- **Functions:** snake_case (`classify_query`, `generate_mock_sql`, `get_mock_data`)
- **Variables:** snake_case (`detected_metric`, `query_lower`, `fiscal_quarter`)
- **Chainlit decorators:** Use async functions with descriptive names (`@cl.on_message`)
- **Private functions:** Prefix with underscore if internal

### Dictionary and Data Structures
Use clear, multi-line formatting for complex structures (app.py:27-58):
```python
MOCK_METRICS = {
    "revenue": {
        "Q1_2024": 980_000, "Q2_2024": 1_050_000,
        "2024": 4_364_567, "2023": 3_890_000
    },
    "cogs": {
        "Q1_2024": 380_000, "Q2_2024": 400_000,
    }
}
```

**Use underscores for large numbers:** `1_234_567` instead of `1234567`

### Error Handling
Use try/except with specific, informative error messages:
```python
try:
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
except httpx.HTTPError as e:
    return f"HTTP Error: {str(e)}"
except Exception as e:
    return f"Error: {str(e)}"
```

**Prefer specific exceptions** (HTTPError, KeyError) over generic Exception when possible.

### Docstrings
Keep minimal and functional (app.py:81, 136):
```python
def classify_query(query: str) -> dict:
    """Clasifica la consulta y extrae métrica y período"""
    
def generate_mock_sql(metric: str, period: str) -> str:
    """Genera SQL mock basado en la métrica y período"""
```

**Spanish or English is fine** - this codebase uses Spanish docstrings.

### Chainlit Patterns
Use `cl.Step` for traceability in user-facing workflows:
```python
async with cl.Step(name="Classification", type="tool") as step:
    step.input = query
    classification = classify_query(query)
    step.output = f"Route: {classification['route']}"
```

**Step types:** `"tool"`, `"llm"`, `"embedding"`, `"retrieval"`

### Async HTTP Calls
Always use httpx with context manager and timeout:
```python
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(url, headers=headers, json=payload)
```

### Regular Expressions
Use raw strings for regex patterns (app.py:70-77):
```python
PERIOD_PATTERNS = {
    "Q1_2024": [r"q1.?2024", r"primer.?trimestre.?2024"],
    "2024": [r"\b2024\b"]
}
```

## Architecture

```
User -> Chainlit (app.py) -> n8n (classification) -> Route Decision (3 routes)
                                                          |
                           +---------------+---------------+---------------+
                           |               |               |               |
                     Semantic (FP&A)    Documental         Hybrid
                     -> Cube Core       -> Weaviate        -> Cube + Weaviate
                     -> DuckDB
                           |               |               |
                           +---------------+---------------+---------------+
                                                          |
                           Dify (explanation layer - post-calculation)
                                                          |
                           Response with cl.Step traceability
```

**Weaviate as only vector database**: Architectural simplification for academic resources.
**3 classification routes**: Semantic, Documental, Hybrid.

**Key principle**: Dify receives **already-calculated data** and only generates natural language explanations. It does NOT participate in query classification, SQL generation, or numerical calculations.

### Key Components
- **app.py**: Main application with query classification, mock data, LLM integration
- **classify_query()**: Routes queries (semantic vs documental) at line 80
- **cl.Step**: Shows 4 visible steps (Classification → SQL → Data → Explanation)
- **Dify**: Explanation layer (post-calculation) - receives validated data, generates explanations

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

# Weaviate (only vector database)
WEAVIATE_URL=http://100.110.109.43:8080

# Embeddings (Ollama)
OLLAMA_BASE_URL=http://100.116.107.52:11434
EMBEDDING_MODEL=nomic-embed-text

# Integrations
N8N_WEBHOOK_URL=http://100.105.68.15:5678/webhook/sdrag-query
CUBE_API_URL=http://100.116.107.52:4000
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
- Execute Python scripts with `python3`
- Limited emoji usage; only when adding value
- **Use MCP tools**: Feel free to use Context7 or other MCP tools for documentation lookup

## Tailscale Network

SSH access available without password:
```bash
ssh cfocoder3    # Chainlit, n8n (100.105.68.15)
ssh macmini      # Dify, Weaviate, MinIO (100.110.109.43)
ssh vostro       # Cube Core, Ollama, Docling (100.116.107.52)
ssh inspiron13
ssh inspiron15
```

## Anti-patterns to Avoid

1. **Never use pip** - always use `uv`
2. **Don't invent numbers** - LLMs explain, Cube Core calculates
3. **Avoid verbose comments** - keep code self-documenting
4. **Don't create unnecessary files** - prefer editing existing ones
5. **Avoid excessive print statements** - makes code noisy
