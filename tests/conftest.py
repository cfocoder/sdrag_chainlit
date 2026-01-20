"""
Fixtures compartidos para tests de SDRAG Chainlit.

Proporciona mocks para servicios externos (Dify, Weaviate, OpenRouter, Ollama)
para permitir tests unitarios sin dependencias de red.

Protocolo v7: Weaviate como única base de datos vectorial.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Generator, Any


# =============================================================================
# Fixtures: Mock Data FP&A
# =============================================================================

@pytest.fixture
def sample_fpa_query() -> str:
    """Query típica de FP&A para testing."""
    return "¿Cuál fue el revenue de Q4 2024?"


@pytest.fixture
def sample_documental_query() -> str:
    """Query documental para testing."""
    return "¿Cuál es la política de viáticos de la empresa?"


@pytest.fixture
def sample_fpa_data() -> dict:
    """Datos mock de respuesta FP&A."""
    return {
        "revenue": 1200000.50,
        "period": "Q4 2024",
        "currency": "USD",
        "variance_vs_budget": 0.05
    }


@pytest.fixture
def sample_sql() -> str:
    """SQL mock generado por Cube Core."""
    return "SELECT SUM(revenue) FROM facts WHERE quarter = 'Q4' AND year = 2024"


# =============================================================================
# Fixtures: Mock de Servicios Externos
# =============================================================================

@pytest.fixture
def mock_dify_response() -> dict:
    """Respuesta mock de Dify API."""
    return {
        "answer": "El revenue de Q4 2024 fue de $1,200,000.50 USD, lo que representa un 5% por encima del presupuesto.",
        "conversation_id": "test-conv-123",
        "message_id": "test-msg-456"
    }


@pytest.fixture
def mock_openrouter_response() -> str:
    """Respuesta mock de OpenRouter API."""
    return "El revenue del cuarto trimestre de 2024 fue de $1.2 millones USD."


@pytest.fixture
def mock_weaviate_chunks() -> list[dict]:
    """Chunks mock de Weaviate (búsqueda híbrida)."""
    return [
        {
            "content": "La política de viáticos establece un límite de $500 USD por día...",
            "chunk_type": "text",
            "section": "Políticas de Gastos",
            "page_number": 3,
            "score": 0.92,
            "document": {"title": "politicas/viaticos.pdf", "uuid": "doc-001"}
        },
        {
            "content": "Los gastos de alimentación no deben exceder $100 USD por comida...",
            "chunk_type": "text",
            "section": "Límites de Gastos",
            "page_number": 4,
            "score": 0.87,
            "document": {"title": "politicas/viaticos.pdf", "uuid": "doc-001"}
        }
    ]


@pytest.fixture
def mock_embedding_768() -> list[float]:
    """Embedding mock de 768 dimensiones (nomic-embed-text)."""
    return [0.01] * 768


# =============================================================================
# Fixtures: Patches para Servicios
# =============================================================================

@pytest.fixture
def mock_httpx_client():
    """Mock de httpx.AsyncClient para llamadas HTTP."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_dify_api(mock_httpx_client, mock_dify_response):
    """Configura mock para llamadas a Dify API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_dify_response
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.post.return_value = mock_response
    return mock_httpx_client


@pytest.fixture
def mock_weaviate_client():
    """Mock del cliente Weaviate."""
    with patch("weaviate.connect_to_custom") as mock_connect:
        mock_client = MagicMock()
        mock_connect.return_value = mock_client

        # Mock de colecciones
        mock_collection = MagicMock()
        mock_client.collections.get.return_value = mock_collection
        mock_client.collections.exists.return_value = True

        # Mock de data operations
        mock_collection.data.insert.return_value = "test-uuid-12345678"

        # Mock de query operations
        mock_query_result = MagicMock()
        mock_query_result.objects = []
        mock_collection.query.hybrid.return_value = mock_query_result

        yield mock_client


@pytest.fixture
def mock_ollama_embeddings(mock_embedding_768):
    """Mock para generación de embeddings con Ollama (768 dims)."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"embedding": mock_embedding_768}
        mock_response.raise_for_status = MagicMock()
        mock_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_instance
        yield mock_instance


# =============================================================================
# Fixtures: Environment Variables
# =============================================================================

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Configura variables de entorno para testing."""
    env_vars = {
        "DIFY_API_URL": "http://test-dify:80/v1",
        "DIFY_API_KEY": "app-test-key-12345",
        "OPENROUTER_API_KEY": "sk-test-openrouter",
        "OPENROUTER_MODEL": "test-model",
        "WEAVIATE_URL": "http://test-weaviate:8080",
        "OLLAMA_BASE_URL": "http://test-ollama:11434",
        "EMBEDDING_MODEL": "nomic-embed-text",
        "N8N_WEBHOOK_URL": "http://test-n8n:5678/webhook/test"
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


# =============================================================================
# Fixtures: Chainlit Mocks
# =============================================================================

@pytest.fixture
def mock_cl_message():
    """Mock de cl.Message para tests sin Chainlit server."""
    with patch("chainlit.Message") as mock_msg:
        mock_instance = MagicMock()
        mock_instance.send = AsyncMock()
        mock_msg.return_value = mock_instance
        yield mock_msg


@pytest.fixture
def mock_cl_step():
    """Mock de cl.Step para tests de trazabilidad."""
    with patch("chainlit.Step") as mock_step:
        mock_instance = MagicMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock()
        mock_step.return_value = mock_instance
        yield mock_step


# =============================================================================
# Fixtures: Weaviate Schema (Fase 3)
# =============================================================================

@pytest.fixture
def sample_weaviate_document() -> dict:
    """Documento mock para indexar en Weaviate."""
    return {
        "title": "Annual Report 2024",
        "source_path": "/documents/annual_report_2024.pdf",
        "document_type": "PDF",
        "fiscal_year": "2024"
    }


@pytest.fixture
def sample_weaviate_chunk() -> dict:
    """Chunk mock para indexar en Weaviate."""
    return {
        "content": "Revenue for Q4 2024 was $1.2M, representing a 15% increase YoY.",
        "chunk_type": "text",
        "section": "Financial Summary",
        "page_number": 5
    }


@pytest.fixture
def sample_hybrid_search_results(mock_weaviate_chunks) -> list[dict]:
    """Resultados mock de búsqueda híbrida."""
    return mock_weaviate_chunks

# =============================================================================
# Fixtures: Cube Core (Fase 5)
# =============================================================================

@pytest.fixture
def mock_cube_core_response() -> dict:
    """Respuesta mock de Cube Core API."""
    return {
        "data": [
            {"quarter": "Q1_2024", "revenue": 980000, "cogs": 380000, "gross_margin": 0.612},
            {"quarter": "Q2_2024", "revenue": 1050000, "cogs": 400000, "gross_margin": 0.619},
            {"quarter": "Q3_2024", "revenue": 1100000, "cogs": 420000, "gross_margin": 0.618},
            {"quarter": "Q4_2024", "revenue": 1234567, "cogs": 450000, "gross_margin": 0.635}
        ],
        "sql": "SELECT fiscal_quarter, SUM(revenue), SUM(cogs), AVG(gross_margin) FROM facts WHERE fiscal_year = 2024 GROUP BY fiscal_quarter",
        "execution_time_ms": 145
    }


@pytest.fixture
def mock_cube_core_api(mock_httpx_client, mock_cube_core_response):
    """Configura mock para llamadas a Cube Core API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_cube_core_response
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.post.return_value = mock_response
    return mock_httpx_client


# =============================================================================
# Fixtures: Docling (Fase 3)
# =============================================================================

@pytest.fixture
def mock_docling_extracted_doc() -> dict:
    """Documento extraído mock de Docling."""
    return {
        "file_name": "annual_report_2024.pdf",
        "file_type": "PDF",
        "text_content": "This is the annual report for fiscal year 2024. Revenue increased by 15% YoY...",
        "tables": [
            {
                "table_id": "table_1",
                "caption": "Quarterly Revenue Summary",
                "data": [
                    ["Quarter", "Revenue", "COGS", "Gross Margin"],
                    ["Q1 2024", "$980,000", "$380,000", "61.2%"],
                    ["Q2 2024", "$1,050,000", "$400,000", "61.9%"]
                ],
                "page_number": 7
            }
        ],
        "metadata": {
            "title": "Annual Report 2024",
            "author": "Finance Department",
            "pages": 45,
            "creation_date": "2025-01-15"
        }
    }


@pytest.fixture
def mock_docling_extractor():
    """Mock del extractor Docling."""
    with patch("services.docling_extractor.extract_document") as mock_extract:
        mock_extract.return_value = {
            "file_name": "test.pdf",
            "file_type": "PDF",
            "text_content": "Sample text...",
            "tables": [],
            "metadata": {"pages": 10}
        }
        yield mock_extract


# =============================================================================
# Fixtures: n8n Router (Fase 4)
# =============================================================================

@pytest.fixture
def mock_n8n_classification() -> dict:
    """Clasificación mock de n8n router."""
    return {
        "route": "semantic",
        "metric": "revenue",
        "period": "Q4_2024",
        "confidence": 0.95,
        "reasoning": "Query contains metric 'revenue' and period 'Q4 2024'"
    }


@pytest.fixture
def mock_n8n_webhook(mock_httpx_client, mock_n8n_classification):
    """Mock para webhook de n8n."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_n8n_classification
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.post.return_value = mock_response
    return mock_httpx_client


# =============================================================================
# Fixtures: Audit Trail (Fase 7)
# =============================================================================

@pytest.fixture
def sample_session_trace() -> dict:
    """SessionTrace mock para audit trail."""
    return {
        "session_id": "test-session-12345678",
        "user_id": "test-user@example.com",
        "timestamp": "2026-01-20T10:30:00Z",
        "query": "¿Cuál fue el revenue de Q4 2024?",
        "steps": [
            {
                "step_name": "Clasificación",
                "step_type": "tool",
                "input": "¿Cuál fue el revenue de Q4 2024?",
                "output": "Ruta: semantic, Métrica: revenue",
                "duration_ms": 150,
                "timestamp": "2026-01-20T10:30:00.100Z"
            },
            {
                "step_name": "SQL",
                "step_type": "tool",
                "input": "Generar SQL para revenue Q4 2024",
                "output": "SELECT SUM(revenue) FROM facts WHERE quarter='Q4' AND year=2024",
                "duration_ms": 50,
                "timestamp": "2026-01-20T10:30:00.250Z"
            },
            {
                "step_name": "Datos",
                "step_type": "tool",
                "input": "Ejecutar SQL en Cube Core",
                "output": '{"revenue": 1234567, "period": "Q4_2024"}',
                "duration_ms": 320,
                "timestamp": "2026-01-20T10:30:00.300Z"
            },
            {
                "step_name": "Explicación",
                "step_type": "llm",
                "input": "Generar explicación con Dify",
                "output": "El revenue de Q4 2024 fue de $1,234,567...",
                "duration_ms": 1200,
                "timestamp": "2026-01-20T10:30:00.620Z"
            }
        ],
        "total_duration_ms": 1720,
        "result": {
            "answer": "El revenue de Q4 2024 fue de $1,234,567...",
            "data": {"revenue": 1234567, "period": "Q4_2024"},
            "sql": "SELECT SUM(revenue) FROM facts WHERE quarter='Q4' AND year=2024"
        },
        "classification": {"route": "semantic", "metric": "revenue", "period": "Q4_2024"}
    }


# =============================================================================
# Fixtures: Helpers
# =============================================================================

@pytest.fixture
def temp_test_dir(tmp_path) -> str:
    """Directorio temporal para tests con archivos."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    return str(test_dir)


@pytest.fixture
def sample_pdf_path(temp_test_dir) -> str:
    """Path a PDF mock para tests de upload."""
    pdf_path = f"{temp_test_dir}/test_report.pdf"
    # Crear archivo dummy
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n%mock pdf content')
    return pdf_path


# =============================================================================
# Notas de Uso
# =============================================================================
"""
USO DE FIXTURES:

1. Mock de Dify API:
   def test_dify_integration(mock_dify_api, mock_dify_response):
       result = await call_dify(query="test", data={})
       assert result["answer"] == mock_dify_response["answer"]

2. Mock de Weaviate:
   def test_weaviate_search(mock_weaviate_client, mock_weaviate_chunks):
       results = await hybrid_search(query="test")
       assert len(results) == len(mock_weaviate_chunks)

3. Mock de Ollama embeddings:
   @pytest.mark.asyncio
   async def test_embeddings(mock_ollama_embeddings, mock_embedding_768):
       embedding = await generate_embedding("test")
       assert len(embedding) == 768

4. Mock de Cube Core:
   @pytest.mark.asyncio
   async def test_cube_query(mock_cube_core_api, mock_cube_core_response):
       result = await call_cube_core(sql="SELECT...")
       assert len(result["data"]) == 4

5. Variables de entorno:
   def test_with_env(mock_env_vars):
       import os
       assert os.getenv("DIFY_API_KEY") == "app-test-key-12345"

6. Chainlit mocks:
   @pytest.mark.asyncio
   async def test_chainlit_message(mock_cl_message):
       await cl.Message(content="test").send()
       mock_cl_message.return_value.send.assert_called_once()

TIPS:
- Todos los mocks de servicios HTTP usan mock_httpx_client base
- Embeddings son siempre 768 dimensiones (nomic-embed-text)
- Weaviate única base vectorial (Protocolo v7)
- mock_env_vars configura todas las variables necesarias
- temp_test_dir proporciona directorio limpio por test
"""