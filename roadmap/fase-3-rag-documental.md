# Fase 3: RAG Documental (Weaviate + Docling)

**Objetivo**: Implementar indexación y búsqueda híbrida de documentos no estructurados usando Weaviate como única base de datos vectorial.

**Prioridad**: Alta - Habilita consultas documentales y contexto para explicaciones.

---

## Prerrequisitos

### Fases previas requeridas
- [x] Fase 0: Infraestructura verificada (Weaviate, Ollama operativos)
- [x] Fase 1-2: Chainlit con cl.Step funcionando

### Servicios que deben estar operativos

Ejecutar antes de comenzar:
```bash
# Verificar Weaviate
curl -s http://100.110.109.43:8080/v1/.well-known/ready | jq .

# Verificar Ollama con nomic-embed-text
curl -s http://100.116.107.52:11434/api/tags | jq '.models[] | select(.name | contains("nomic"))'

# Test de embedding (debe retornar 768 dimensiones)
curl -X POST http://100.116.107.52:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "test"}' | jq '.embedding | length'
```

- [ ] Weaviate: `http://100.110.109.43:8080` - Base de datos vectorial única
- [ ] Ollama: `http://100.116.107.52:11434` - Modelo nomic-embed-text para embeddings

### Estructura de directorios

```bash
# Crear si no existe
mkdir -p services scripts tests
touch services/__init__.py
```

---

## Contexto

### ¿Por qué Weaviate como Única Base Vectorial?

La decisión de utilizar Weaviate como única base de datos vectorial responde a principios de **simplicidad verificable** alineados con los objetivos de la tesis:

| Criterio | Múltiples Vector DBs | Weaviate Única |
|----------|---------------------|----------------|
| **Complejidad arquitectónica** | Alta (routing, sincronización) | Baja |
| **Trazabilidad** | Dispersa entre sistemas | Centralizada |
| **Mantenimiento** | Múltiples backups, updates | Un solo sistema |
| **Consistencia de índices** | Riesgo de desincronización | Garantizada |
| **Recursos requeridos** | Alto (RAM, storage) | Optimizado |
| **Debugging** | Complejo | Simple |

### Rol de Weaviate en SDRAG

Weaviate **SÍ es responsable de**:
- Almacenar y recuperar embeddings de documentos no estructurados
- Proveer búsqueda híbrida (vectorial + BM25)
- Almacenar definiciones de métricas y reglas de negocio
- Soportar relaciones mediante cross-references (GraphRAG ligero)

Weaviate **NO participa en**:
- Generación de valores numéricos (responsabilidad de Cube Core)
- Cálculos aritméticos o agregaciones
- Ejecución de SQL o consultas analíticas
- Toma de decisiones de enrutamiento (responsabilidad de n8n)

**Principio Crítico**: Los valores numéricos **nunca provienen de Weaviate**. Los números son exclusivamente provistos por Cube Core.

### GraphRAG Implícito en Weaviate

Weaviate permite modelar relaciones mediante cross-references entre clases, habilitando un **GraphRAG ligero** sin necesidad de una base de datos de grafos dedicada.

**Limitación deliberada**: El GraphRAG en Weaviate se limita a **1-2 saltos** de profundidad. Consultas de razonamiento multi-hop complejo quedan fuera del alcance.

---

## Tarea 3.1: Upload de Archivos en Chainlit

### Descripción
Habilitar que los usuarios suban documentos PDF/Excel para indexación.

### Código de referencia para `app.py`

```python
import chainlit as cl
from pathlib import Path

@cl.on_message
async def main(message: cl.Message):
    # Procesar archivos adjuntos
    if message.elements:
        for element in message.elements:
            if isinstance(element, cl.File):
                file_path = element.path
                file_name = element.name

                async with cl.Step(name="Procesando documento", type="tool") as step:
                    step.input = f"Archivo: {file_name}"

                    # Validar tipo de archivo
                    suffix = Path(file_name).suffix.lower()
                    if suffix not in ['.pdf', '.xlsx', '.md', '.txt']:
                        step.output = f"Tipo de archivo no soportado: {suffix}"
                        return

                    # Procesar documento
                    result = await process_document(file_path, file_name)
                    step.output = f"Documento indexado: {result['chunks_count']} chunks"

                await cl.Message(
                    content=f"Documento '{file_name}' indexado correctamente con {result['chunks_count']} chunks."
                ).send()
                return

    # Continuar con flujo normal de consulta...
```

### ✅ Criterios de Completitud

**Testing:**
- [ ] Test: Subir PDF válido retorna success
- [ ] Test: Subir archivo .exe retorna error
- [ ] Test: cl.Step aparece en UI con nombre correcto

**Verificación manual:**
```bash
# Ejecutar Chainlit y subir un PDF
chainlit run app.py
# Arrastrar un archivo PDF en el chat
# Verificar mensaje: "Documento 'archivo.pdf' indexado correctamente..."
```

**Benchmark:**
- [ ] Upload de PDF <5MB debe completar en <2s
- [ ] Mensaje de error para tipos no soportados en <100ms

---

## Tarea 3.2: Extracción con Docling

### Descripción
Usar Docling para extraer texto estructurado de PDFs preservando tablas.

### Dependencias
```bash
uv add docling
```

### Archivo a crear
`services/docling_extractor.py`

### ✅ Criterios de Completitud

**Testing:**
- [ ] Test: Extracción de PDF retorna JSON estructurado
- [ ] Test: Tablas preservadas como unidades indivisibles
- [ ] Test: Metadata extraída correctamente (título, autor, páginas)

**Verificación en VOSTRO:**
```bash
ssh vostro
python3 -c "from docling.document_converter import DocumentConverter; print('✅ Docling instalado')"

# Test de extracción
cd /tmp
curl -o test.pdf https://arxiv.org/pdf/2301.00234.pdf
python3 services/docling_extractor.py test.pdf
# Verificar JSON con tablas preservadas
```

**Benchmark:**
- [ ] Extracción de PDF 50 páginas <10s
- [ ] PDF 200 páginas <45s

### Código de referencia
```python
"""Extractor de documentos usando Docling"""
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from pathlib import Path
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Configurar converter
converter = DocumentConverter()

def extract_document(file_path: str) -> Dict[str, Any]:
    """
    Extrae contenido estructurado de un documento.

    Args:
        file_path: Ruta al archivo (PDF, XLSX, MD, TXT)

    Returns:
        Dict con contenido extraído y metadata
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    # Determinar formato
    suffix = path.suffix.lower()
    format_map = {
        '.pdf': InputFormat.PDF,
        '.xlsx': InputFormat.XLSX,
        '.md': InputFormat.MD,
        '.txt': InputFormat.TXT,
    }

    if suffix not in format_map:
        raise ValueError(f"Formato no soportado: {suffix}")

    # Extraer documento
    result = converter.convert(file_path)
    doc = result.document

    # Extraer contenido
    extracted = {
        "file_name": path.name,
        "file_type": suffix,
        "text_content": doc.export_to_markdown(),
        "tables": [],
        "metadata": {
            "page_count": len(doc.pages) if hasattr(doc, 'pages') else 1,
        }
    }

    # Extraer tablas como unidades indivisibles
    if hasattr(doc, 'tables'):
        for i, table in enumerate(doc.tables):
            extracted["tables"].append({
                "table_id": f"tbl_{i}",
                "content": table.export_to_markdown(),
                "page": table.prov[0].page_no if table.prov else None
            })

    logger.info(f"Documento extraído: {path.name}, {len(extracted['tables'])} tablas")
    return extracted


def extract_text_only(file_path: str) -> str:
    """Extrae solo el texto de un documento (para embeddings)."""
    result = extract_document(file_path)
    return result["text_content"]
```

### Criterios de aceptación
- [ ] PDFs se extraen correctamente con Docling
- [ ] Tablas se preservan como unidades indivisibles
- [ ] Metadata incluye número de páginas
- [ ] Manejo de errores para archivos corruptos

---

## Tarea 3.3: Chunking Semántico

### Descripción
Implementar chunking semántico usando HybridChunker con umbral θ=0.8.

### Dependencias
```bash
uv add llama-index
```

### Archivo a crear
`services/chunker.py`

### Código de referencia
```python
"""Chunking semántico para documentos financieros"""
from typing import List, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)

# Parámetros de chunking (del protocolo de tesis)
SIMILARITY_THRESHOLD = 0.8  # θ=0.8
MAX_CHUNK_SIZE = 500  # caracteres
PRESERVE_TABLES = True


def simple_chunk(text: str, max_size: int = MAX_CHUNK_SIZE) -> List[str]:
    """
    Divide texto en chunks por párrafos respetando tamaño máximo.
    """
    # Dividir por párrafos dobles
    paragraphs = re.split(r'\n\s*\n', text)

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 2 <= max_size:
            current_chunk += "\n\n" + para if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def chunk_document(
    text_content: str,
    tables: List[Dict] = None,
    metadata: Dict = None
) -> List[Dict[str, Any]]:
    """
    Divide un documento en chunks semánticos.

    Args:
        text_content: Texto extraído del documento
        tables: Lista de tablas extraídas (se mantienen como unidades)
        metadata: Metadata del documento fuente

    Returns:
        Lista de chunks con contenido y metadata
    """
    chunks = []
    metadata = metadata or {}

    # Chunking del texto
    text_chunks = simple_chunk(text_content, MAX_CHUNK_SIZE)

    for i, chunk_text in enumerate(text_chunks):
        chunks.append({
            "chunk_id": f"chunk_{i}",
            "content": chunk_text,
            "chunk_type": "text",
            "metadata": {
                **metadata,
                "chunk_index": i,
            }
        })

    # Agregar tablas como chunks indivisibles
    if tables and PRESERVE_TABLES:
        for table in tables:
            chunks.append({
                "chunk_id": table.get("table_id", f"table_{len(chunks)}"),
                "content": table["content"],
                "chunk_type": "table",
                "metadata": {
                    **metadata,
                    "page_number": table.get("page"),
                    "table_id": table.get("table_id"),
                }
            })

    logger.info(f"Documento dividido en {len(chunks)} chunks ({len(text_chunks)} texto + {len(tables or [])} tablas)")
    return chunks


def chunk_for_indexing(extracted_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Wrapper para chunking de documento ya extraído.

    Args:
        extracted_doc: Output de docling_extractor.extract_document()

    Returns:
        Lista de chunks listos para indexación
    """
    return chunk_document(
        text_content=extracted_doc["text_content"],
        tables=extracted_doc.get("tables", []),
        metadata={
            "source_document": extracted_doc["file_name"],
            "file_type": extracted_doc["file_type"],
        }
    )
```

### ✅ Criterios de Completitud

**Testing:**
- [ ] Test: Chunking respeta límite de 500 caracteres
- [ ] Test: Tabla extraída permanece indivisible
- [ ] Test: Metadata propagada a todos los chunks

**Verificación:**
```bash
pytest tests/test_embeddings.py::test_chunk_document -v
pytest tests/test_embeddings.py::test_preserve_tables -v
```

**Benchmark:**
- [ ] Chunking de 10,000 palabras <1s
- [ ] No más de 100 chunks por documento promedio

---

## Tarea 3.4: Generación de Embeddings con Ollama

### Descripción
Generar embeddings de 768 dimensiones usando nomic-embed-text via Ollama.

### Dependencias
```bash
uv add httpx
```

### Archivo a crear
`services/embeddings.py`

### Código de referencia
```python
"""Generación de embeddings con Ollama"""
import httpx
import os
import logging
from typing import List

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://100.116.107.52:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_DIM = 768  # Dimensiones de nomic-embed-text


async def generate_embedding(text: str) -> List[float]:
    """
    Genera embedding para un texto usando Ollama.

    Args:
        text: Texto a vectorizar

    Returns:
        Lista de floats (768 dimensiones)
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": text
            }
        )
        response.raise_for_status()
        data = response.json()

        embedding = data.get("embedding", [])

        if len(embedding) != EMBEDDING_DIM:
            logger.warning(f"Embedding con dimensiones inesperadas: {len(embedding)}")

        return embedding


async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Genera embeddings para múltiples textos.

    Args:
        texts: Lista de textos a vectorizar

    Returns:
        Lista de embeddings
    """
    embeddings = []
    for text in texts:
        embedding = await generate_embedding(text)
        embeddings.append(embedding)
    return embeddings
```

### Verificación
```bash
# Test de embedding desde Python
python3 -c "
import asyncio
from services.embeddings import generate_embedding

async def test():
    emb = await generate_embedding('Revenue for Q4 2024')
    print(f'Dimensiones: {len(emb)}')
    print(f'Primeros 5 valores: {emb[:5]}')

asyncio.run(test())
"
```

### ✅ Criterios de Completitud

**Testing:**
- [ ] Test: Embedding retorna vector de 768 dimensiones
- [ ] Test: Timeout después de 30s lanza excepción
- [ ] Test: Batch de 10 embeddings funciona

**Verificación en VOSTRO:**
```bash
ssh vostro
curl -X POST http://localhost:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "test"}' | jq '.embedding | length'
# Debe retornar: 768
```

**Benchmark:**
- [ ] 1 embedding <200ms (P50)
- [ ] Batch de 100 embeddings <10s

---

## Tarea 3.5: Configurar Schema de Weaviate

### Descripción
Crear las clases en Weaviate para almacenar documentos, chunks, métricas y reglas.

### Dependencias
```bash
uv add weaviate-client
```

### Archivo a crear
`services/weaviate_client.py`

### Código de referencia
```python
"""Cliente Weaviate para SDRAG"""
import weaviate
from weaviate.classes.config import Configure, Property, DataType, ReferenceProperty
from weaviate.classes.query import Filter
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://100.110.109.43:8080")

# Cliente singleton
_client = None


def get_client() -> weaviate.WeaviateClient:
    """Obtiene cliente Weaviate (singleton)."""
    global _client
    if _client is None:
        host = WEAVIATE_URL.replace("http://", "").replace("https://", "").split(":")[0]
        port = int(WEAVIATE_URL.split(":")[-1]) if ":" in WEAVIATE_URL else 8080
        _client = weaviate.connect_to_custom(
            http_host=host,
            http_port=port,
            http_secure=False,
        )
    return _client


def close_client():
    """Cierra conexión al cliente."""
    global _client
    if _client:
        _client.close()
        _client = None


def create_schema():
    """
    Crea el schema de Weaviate para SDRAG.

    Clases:
    - Document: Documentos fuente
    - Chunk: Fragmentos semánticos
    - MetricDefinition: Definiciones de métricas
    - BusinessRule: Reglas de negocio
    """
    client = get_client()

    # Clase Document
    if not client.collections.exists("Document"):
        client.collections.create(
            name="Document",
            description="Documentos fuente (PDFs, reportes, papers)",
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(name="title", data_type=DataType.TEXT),
                Property(name="source_path", data_type=DataType.TEXT),
                Property(name="document_type", data_type=DataType.TEXT),
                Property(name="fiscal_year", data_type=DataType.TEXT),
            ]
        )
        logger.info("Clase 'Document' creada")

    # Clase Chunk
    if not client.collections.exists("Chunk"):
        client.collections.create(
            name="Chunk",
            description="Fragmentos semánticos de documentos",
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(name="content", data_type=DataType.TEXT),
                Property(name="chunk_type", data_type=DataType.TEXT),
                Property(name="section", data_type=DataType.TEXT),
                Property(name="page_number", data_type=DataType.INT),
            ],
            references=[
                ReferenceProperty(name="belongsTo", target_collection="Document"),
            ]
        )
        logger.info("Clase 'Chunk' creada")

    # Clase MetricDefinition
    if not client.collections.exists("MetricDefinition"):
        client.collections.create(
            name="MetricDefinition",
            description="Definiciones de métricas de Cube Core",
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(name="metric_name", data_type=DataType.TEXT),
                Property(name="definition", data_type=DataType.TEXT),
                Property(name="formula", data_type=DataType.TEXT),
            ],
            references=[
                ReferenceProperty(name="referencedIn", target_collection="Document"),
            ]
        )
        logger.info("Clase 'MetricDefinition' creada")

    # Clase BusinessRule
    if not client.collections.exists("BusinessRule"):
        client.collections.create(
            name="BusinessRule",
            description="Reglas de negocio y políticas de cálculo",
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(name="rule_name", data_type=DataType.TEXT),
                Property(name="description", data_type=DataType.TEXT),
            ],
            references=[
                ReferenceProperty(name="appliesTo", target_collection="MetricDefinition"),
            ]
        )
        logger.info("Clase 'BusinessRule' creada")

    logger.info("Schema de Weaviate configurado correctamente")


async def index_document(
    title: str,
    source_path: str,
    document_type: str,
    fiscal_year: str = None,
) -> str:
    """
    Indexa un documento en Weaviate.

    Returns:
        UUID del documento creado
    """
    client = get_client()
    collection = client.collections.get("Document")

    uuid = collection.data.insert(
        properties={
            "title": title,
            "source_path": source_path,
            "document_type": document_type,
            "fiscal_year": fiscal_year or "",
        }
    )

    logger.info(f"Documento indexado: {title} -> {uuid}")
    return str(uuid)


async def index_chunk(
    content: str,
    chunk_type: str,
    vector: List[float],
    document_uuid: str,
    section: str = None,
    page_number: int = None,
) -> str:
    """
    Indexa un chunk con su embedding y referencia al documento.

    Returns:
        UUID del chunk creado
    """
    client = get_client()
    collection = client.collections.get("Chunk")

    uuid = collection.data.insert(
        properties={
            "content": content,
            "chunk_type": chunk_type,
            "section": section or "",
            "page_number": page_number or 0,
        },
        vector=vector,
        references={"belongsTo": document_uuid}
    )

    logger.info(f"Chunk indexado: {content[:50]}... -> {uuid}")
    return str(uuid)


async def hybrid_search(
    query: str,
    query_vector: List[float],
    limit: int = 5,
    alpha: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Búsqueda híbrida (vectorial + BM25) en Weaviate.

    Args:
        query: Texto de búsqueda (para BM25)
        query_vector: Embedding de la query (para vectorial)
        limit: Número máximo de resultados
        alpha: Balance entre vectorial (1.0) y BM25 (0.0)

    Returns:
        Lista de chunks con score y metadata
    """
    client = get_client()
    collection = client.collections.get("Chunk")

    response = collection.query.hybrid(
        query=query,
        vector=query_vector,
        alpha=alpha,
        limit=limit,
        return_metadata=["score"],
        return_references=["belongsTo"]
    )

    results = []
    for obj in response.objects:
        result = {
            "chunk_id": str(obj.uuid),
            "content": obj.properties.get("content", ""),
            "chunk_type": obj.properties.get("chunk_type", ""),
            "section": obj.properties.get("section", ""),
            "page_number": obj.properties.get("page_number", 0),
            "score": obj.metadata.score if obj.metadata else 0,
        }

        # Obtener documento padre
        if obj.references and "belongsTo" in obj.references:
            doc_ref = obj.references["belongsTo"]
            if doc_ref.objects:
                result["document"] = {
                    "uuid": str(doc_ref.objects[0].uuid),
                    "title": doc_ref.objects[0].properties.get("title", ""),
                }

        results.append(result)

    logger.info(f"Búsqueda híbrida: {len(results)} resultados para '{query[:50]}...'")
    return results


def format_search_results(results: List[Dict[str, Any]]) -> str:
    """
    Formatea resultados de búsqueda para incluir en contexto de Dify.
    """
    if not results:
        return "No se encontraron documentos relevantes."

    lines = []
    for i, result in enumerate(results, 1):
        doc_title = result.get("document", {}).get("title", "Desconocido")
        lines.append(f"[{i}] {doc_title} (pág. {result.get('page_number', '?')})")
        lines.append(f"    {result['content'][:200]}...")
        lines.append("")

    return "\n".join(lines)
```

### Verificación
```bash
# Verificar schema creado
python3 -c "
from services.weaviate_client import get_client, create_schema, close_client

create_schema()
client = get_client()
print('Colecciones:', list(client.collections.list_all().keys()))
close_client()
"
```

### ✅ Criterios de Completitud

**Testing:**
- [ ] Test: Schema creado sin errores
- [ ] Test: Cross-references verificadas con query
- [ ] Test: Vectorizer "none" confirmado

**Verificación en Mac Mini:**
```bash
ssh macmini
curl -s http://localhost:8080/v1/schema | jq '.classes[] | .class'
# Debe listar: Document, Chunk, MetricDefinition, BusinessRule

# Verificar cross-reference
curl -s http://localhost:8080/v1/schema/Chunk | jq '.properties[] | select(.name=="belongsTo")'
```

**Benchmark:**
- [ ] Creación de schema <5s
- [ ] Query con cross-reference <100ms

---

## Tarea 3.6: Implementar Búsqueda Híbrida

### Descripción
La búsqueda híbrida ya está implementada en `weaviate_client.py` (función `hybrid_search`).

Esta tarea es integrar la búsqueda en el flujo de clasificación de consultas.

### Archivo a modificar
`app.py`

### Código de referencia
```python
from services.weaviate_client import hybrid_search, format_search_results
from services.embeddings import generate_embedding

async def handle_documental_query(query: str) -> Dict[str, Any]:
    """
    Maneja consultas documentales usando Weaviate.
    """
    # Generar embedding de la query
    query_vector = await generate_embedding(query)

    # Búsqueda híbrida
    results = await hybrid_search(
        query=query,
        query_vector=query_vector,
        limit=5,
        alpha=0.5  # Balance vectorial/BM25
    )

    # Formatear para contexto
    context = format_search_results(results)

    return {
        "results": results,
        "context": context,
        "chunks_found": len(results)
    }
```

### Criterios de aceptación
- [ ] Búsqueda híbrida con alpha=0.5 por defecto
- [ ] Resultados incluyen metadata del documento padre
- [ ] Contexto formateado para Dify

---

## Tarea 3.7: Mostrar Fuentes Citadas

### Descripción
Mostrar en Chainlit las fuentes de los chunks recuperados.

### Código de referencia para `app.py`
```python
async def show_sources(results: List[Dict], step: cl.Step):
    """
    Muestra fuentes citadas en cl.Step.
    """
    if not results:
        step.output = "No se encontraron fuentes relevantes."
        return

    sources_text = "**Fuentes consultadas:**\n\n"

    for i, result in enumerate(results, 1):
        doc = result.get("document", {})
        title = doc.get("title", "Documento sin título")
        page = result.get("page_number", "?")
        score = result.get("score", 0)

        sources_text += f"{i}. **{title}** (pág. {page}) - Relevancia: {score:.2f}\n"
        sources_text += f"   > {result['content'][:150]}...\n\n"

    step.output = sources_text
```

### ✅ Criterios de Completitud

**Testing:**
- [ ] Test: Formato incluye título, página, score, preview
- [ ] Test: Links renderizados en Markdown

**Verificación manual:**
```bash
chainlit run app.py
# Consulta documental: "¿Cuál es la política de viáticos?"
# Verificar output incluye:
# **Fuentes consultadas:**
# 1. [Política de Viáticos](path.pdf) - Pág. 5 (Score: 0.89)
#    Preview: "Los viáticos se aprueban según..."
```

**UX:**
- [ ] Fuentes al final de respuesta
- [ ] Formato legible y profesional

---

## Tarea 3.8: Preservación de Tablas

### Descripción
Asegurar que las tablas financieras se indexan como unidades indivisibles.

Ya implementado en:
- `services/docling_extractor.py`: Extrae tablas como unidades
- `services/chunker.py`: `chunk_type="table"` para tablas

### Verificación
```python
# Test de extracción de tablas
from services.docling_extractor import extract_document

doc = extract_document("path/to/financial_report.pdf")
print(f"Tablas extraídas: {len(doc['tables'])}")
for table in doc['tables']:
    print(f"  - {table['table_id']}: {len(table['content'])} caracteres")
```

### Criterios de aceptación
- [ ] Tablas se extraen completas con Docling
- [ ] Tablas se indexan con `chunk_type="table"`
- [ ] Tablas no se dividen en chunking

### ✅ Criterios de Completitud

**Testing:**
- [ ] Test: Tabla de 20+ filas en un solo chunk
- [ ] Test: Encabezados incluidos
- [ ] Test: Búsqueda retorna tabla completa

**Verificación con PDF real:**
```bash
# Subir PDF con tabla financiera
# Consultar: "muéstrame resultados Q4"
# Verificar tabla completa, no fragmentada
```

**Calidad:**
- [ ] 100% tablas preservadas
- [ ] Formato Markdown legible

---

## Tarea 3.9: Tests de RAG Documental

### Descripción
Implementar tests para validar el flujo completo de RAG.

### Archivo de test
`tests/test_weaviate.py`

### Tests requeridos
```python
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

class TestWeaviateClient:
    """Tests del cliente Weaviate."""

    @pytest.mark.asyncio
    async def test_index_document(self, mock_weaviate_client):
        """Documento se indexa correctamente."""
        from services.weaviate_client import index_document

        uuid = await index_document(
            title="Test Report",
            source_path="/test/report.pdf",
            document_type="PDF",
            fiscal_year="2024"
        )

        assert uuid is not None

    @pytest.mark.asyncio
    async def test_hybrid_search_returns_results(self, mock_weaviate_client):
        """Búsqueda híbrida retorna resultados."""
        from services.weaviate_client import hybrid_search

        results = await hybrid_search(
            query="revenue Q4 2024",
            query_vector=[0.1] * 768,
            limit=5
        )

        assert isinstance(results, list)

    def test_format_search_results_empty(self):
        """Resultados vacíos retornan mensaje apropiado."""
        from services.weaviate_client import format_search_results

        formatted = format_search_results([])
        assert "No se encontraron" in formatted

    def test_format_search_results_with_data(self):
        """Resultados se formatean correctamente."""
        from services.weaviate_client import format_search_results

        results = [
            {
                "content": "Revenue was $1.2M in Q4...",
                "page_number": 12,
                "score": 0.85,
                "document": {"title": "Annual Report 2024"}
            }
        ]

        formatted = format_search_results(results)
        assert "Annual Report 2024" in formatted
        assert "pág. 12" in formatted


class TestEmbeddings:
    """Tests de generación de embeddings."""

    @pytest.mark.asyncio
    async def test_generate_embedding_dimension(self, mock_ollama):
        """Embedding tiene 768 dimensiones."""
        from services.embeddings import generate_embedding

        embedding = await generate_embedding("test text")
        assert len(embedding) == 768

    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, mock_ollama):
        """Batch de embeddings funciona."""
        from services.embeddings import generate_embeddings_batch

        texts = ["text 1", "text 2", "text 3"]
        embeddings = await generate_embeddings_batch(texts)

        assert len(embeddings) == 3
        assert all(len(e) == 768 for e in embeddings)


# Fixtures
@pytest.fixture
def mock_weaviate_client():
    with patch("services.weaviate_client.weaviate") as mock:
        client = MagicMock()
        mock.connect_to_custom.return_value = client

        collection = MagicMock()
        collection.data.insert.return_value = "test-uuid-12345678"
        collection.query.hybrid.return_value = MagicMock(objects=[])

        client.collections.get.return_value = collection
        client.collections.exists.return_value = False

        yield client


@pytest.fixture
def mock_ollama():
    with patch("services.embeddings.httpx.AsyncClient") as mock:
        client = AsyncMock()
        response = MagicMock()
        response.json.return_value = {"embedding": [0.1] * 768}
        client.post.return_value = response
        mock.return_value.__aenter__.return_value = client
        yield mock
```

### Ejecutar tests
```bash
pytest tests/test_weaviate.py -v
```

### Criterios de aceptación
- [ ] Tests de indexación pasan
- [ ] Tests de búsqueda híbrida pasan
- [ ] Tests de embeddings pasan
- [ ] Coverage >80% en services/weaviate_client.py

---

## Pipeline Completo de Ingesta

### Script de Ingesta
`scripts/ingest_document.py`

```python
"""Script para ingestar documentos en Weaviate"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.docling_extractor import extract_document
from services.chunker import chunk_for_indexing
from services.embeddings import generate_embedding
from services.weaviate_client import (
    create_schema,
    index_document,
    index_chunk,
    close_client
)


async def ingest_file(file_path: str) -> dict:
    """
    Ingesta un archivo completo en Weaviate.

    Pipeline:
    1. Extraer con Docling
    2. Chunk con chunker semántico
    3. Generar embeddings con Ollama
    4. Indexar en Weaviate
    """
    path = Path(file_path)
    print(f"Procesando: {path.name}")

    # 1. Extraer documento
    print("  -> Extrayendo contenido...")
    extracted = extract_document(file_path)

    # 2. Chunk documento
    print("  -> Dividiendo en chunks...")
    chunks = chunk_for_indexing(extracted)
    print(f"    {len(chunks)} chunks generados")

    # 3. Crear documento en Weaviate
    print("  -> Indexando documento...")
    doc_uuid = await index_document(
        title=path.name,
        source_path=str(path.absolute()),
        document_type=path.suffix.upper().replace(".", ""),
        fiscal_year=extracted.get("metadata", {}).get("fiscal_year", "")
    )

    # 4. Indexar chunks con embeddings
    print("  -> Generando embeddings e indexando chunks...")
    indexed_count = 0
    for chunk in chunks:
        vector = await generate_embedding(chunk["content"])
        await index_chunk(
            content=chunk["content"],
            chunk_type=chunk["chunk_type"],
            vector=vector,
            document_uuid=doc_uuid,
            section=chunk.get("metadata", {}).get("section"),
            page_number=chunk.get("metadata", {}).get("page_number")
        )
        indexed_count += 1

    print(f"  OK: {indexed_count} chunks indexados")

    return {
        "document_uuid": doc_uuid,
        "chunks_count": indexed_count,
        "file_name": path.name
    }


async def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/ingest_document.py <archivo>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not Path(file_path).exists():
        print(f"Error: Archivo no encontrado: {file_path}")
        sys.exit(1)

    create_schema()

    try:
        result = await ingest_file(file_path)
        print(f"\nResultado: {result}")
    finally:
        close_client()


if __name__ == "__main__":
    asyncio.run(main())
```

### Ejecutar ingesta
```bash
python scripts/ingest_document.py /path/to/document.pdf
```

---

## Checklist Final Fase 3

- [ ] 3.1 Upload de archivos funciona en Chainlit
- [ ] 3.2 Docling extrae PDFs correctamente
- [ ] 3.3 Chunking semántico con 500 chars máximo
- [ ] 3.4 Embeddings de 768 dims con Ollama
- [ ] 3.5 Schema de Weaviate creado (4 clases)
- [ ] 3.6 Búsqueda híbrida funciona
- [ ] 3.7 Fuentes citadas se muestran en UI
- [ ] 3.8 Tablas preservadas como unidades
- [ ] 3.9 Tests pasan (>80% coverage)
- [ ] Variables de entorno configuradas en Coolify

---

## Variables de Entorno

```bash
# Weaviate
WEAVIATE_URL=http://100.110.109.43:8080

# Embeddings (Ollama en VOSTRO)
OLLAMA_BASE_URL=http://100.116.107.52:11434
EMBEDDING_MODEL=nomic-embed-text
```

---

## Siguiente Fase

Una vez completada la Fase 3, continuar con [Fase 3.5: Dify](fase-3.5-dify.md) para integrar la capa de explicación.
