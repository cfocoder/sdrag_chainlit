# SDRAG Chainlit - Interfaz de Chat para Ejecución Determinista

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Chainlit](https://img.shields.io/badge/chainlit-1.0+-green.svg)](https://docs.chainlit.io)
[![Status](https://img.shields.io/badge/status-active%20development-yellow.svg)]()

**Proyecto de soporte para el proyecto de tesis: Arquitectura RAG Híbrida con Capa Semántica Determinista (SDRAG)**

Este repositorio contiene el desarrollo del frontend de chat usando **Chainlit** como parte del proyecto de tesis de la Maestría en Ciencia de Datos de la Universidad de Guadalajara. El proyecto principal de investigación SDRAG se desarrolla en otro repositorio; este proyecto se enfoca exclusivamente en la implementación, configuración y experimentación con Chainlit.

**📖 Documentación para LLMs**: Ver [roadmap/README.md](roadmap/README.md) para detalles de implementación de cada fase.

## 📚 Contexto de Investigación

**Hipótesis:** Una arquitectura de ejecución determinista con explicación asistida por lenguaje (SDRAG) reduce significativamente las alucinaciones aritméticas en sistemas de IA generativa financiera, comparada con enfoques Text-to-SQL directos y RAG tradicionales.

**Principio arquitectónico:** Los LLMs explican resultados pero no calculan. Los números provienen de Cube Core (capa semántica determinista).

## 🏗️ Arquitectura del Ecosistema SDRAG

```
Usuario → Chainlit → n8n (clasificación determinista)
    ↓
    ├─ Semántica (métricas/agregaciones) → Cube Core → DuckDB → JSON
    ├─ Documental (contexto textual) → Weaviate → Chunks
    └─ Híbrida (datos + contexto) → Cube Core + Weaviate → Combinación
    ↓
    Dify (explicación post-cálculo) → Chainlit (visualización con cl.Step)
```

**Weaviate como única base vectorial:** Simplificación arquitectónica deliberada para recursos académicos. GraphRAG ligero mediante cross-references (1-2 saltos máximo).

**Nodos del cluster distribuido (Tailscale):**
- **cfocoder3** (100.105.68.15) - Oracle Cloud: Chainlit, n8n, Coolify, Dask Scheduler
- **macmini** (100.110.109.43) - On-premise: Weaviate, MinIO, Dify, Dask Worker
- **vostro** (100.116.107.52) - Local: Cube Core, Ollama, DuckDB, Docling, Dask Worker

## 🎯 Características de Chainlit

- ✅ **Trazabilidad completa**: Cada paso visible con `cl.Step()`
- ✅ **Ejecución determinista**: Cálculos verificados vía Cube Core
- ✅ **Visualización FP&A**: DataFrames, SQL, gráficos Plotly
- ✅ **Sin alucinaciones aritméticas**: LLM (Dify/Ollama) solo explica, no calcula
- ✅ **Clasificación explícita**: n8n con reglas determinísticas para enrutamiento auditable (3 rutas)
- ✅ **Búsqueda híbrida**: Weaviate (vectorial + BM25) con GraphRAG ligero (cross-references)

## 🚀 Instalación y Despliegue

### Requisitos Previos

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Gestor de paquetes Python
- Acceso a cluster Tailscale (para servicios externos)

### Instalación de uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# O con pip
pip install uv
```

### Setup Local

```bash
# Clonar repositorio
git clone <repo-url>
cd sdrag_chainlit

# Crear entorno virtual e instalar dependencias
uv sync

# Configurar variables de entorno (opcional para desarrollo)
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar Chainlit
source .venv/bin/activate
chainlit run app.py
```

Abre: http://localhost:8001

### Producción (Oracle Cloud vía Coolify)

Desplegado automáticamente en el nodo **cfocoder3** (100.105.68.15):

1. Coolify detecta `Dockerfile` y hace pull desde GitHub
2. Configuración de dominio: `chainlit.sdrag.com`
3. Variables de entorno configuradas en Coolify
4. Deploy automático en push a main

## 📊 Variables de Entorno

Configuradas en Coolify para el nodo **cfocoder3**:

```bash
# Autenticación Chainlit
CHAINLIT_AUTH_SECRET=<clave-secreta>
CHAINLIT_USER=hector
CHAINLIT_PASSWORD=sdrag2025

# Dify - Capa de Explicación (primario)
DIFY_API_URL=http://100.110.109.43:80/v1          # macmini
DIFY_API_KEY=app-xxx

# OpenRouter (fallback/desarrollo)
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=mistralai/devstral-2512:free

# Servicios del cluster SDRAG
N8N_WEBHOOK_URL=http://100.105.68.15:5678/webhook/sdrag-query
CUBE_API_URL=http://100.116.107.52:4000          # vostro
WEAVIATE_URL=http://100.110.109.43:8080          # macmini - Única base vectorial
OLLAMA_BASE_URL=http://100.116.107.52:11434       # vostro
DASK_SCHEDULER_URL=tcp://100.105.68.15:8786       # cfocoder3
```

## 📂 Estructura del Proyecto

```
app.py                  # Aplicación Chainlit principal (338 líneas)
main.py                 # Entry point placeholder
pyproject.toml          # Gestión de dependencias con uv
Dockerfile              # Imagen para despliegue en producción
README.md               # Este archivo
ROADMAP.md              # Roadmap completo del proyecto
.chainlit/config.toml   # Configuración UI de Chainlit
public/                 # Assets web (logos, theme.json)
chainlit.md             # Mensaje de bienvenida (inglés)
chainlit_es-ES.md       # Mensaje de bienvenida (español)
roadmap/                # Documentación detallada por fase
  ├── README.md                    # Índice para agentes LLM
  ├── fase-0-infraestructura.md    # Verificación de servicios
  ├── fase-3-rag-documental.md     # Weaviate + Docling
  ├── fase-3.5-dify.md             # Capa de explicación
  ├── fase-4-n8n-router.md         # Router determinista
  ├── fase-5-cube-core.md          # Capa semántica
  ├── fase-8-benchmarks.md         # Evaluación académica
  └── comercializacion.md          # Roadmap post-tesis
scripts/                # Scripts de utilidad
  ├── convert_spider_to_parquet.py # Conversión benchmarks
  ├── evaluate_execution_accuracy.py # Evaluador de EX
  ├── compare_systems.py           # Comparación de sistemas
  └── generate_report.py           # Reporte de resultados
services/               # Clientes de servicios externos
  ├── weaviate_client.py           # Cliente Weaviate
  ├── dify_client.py               # Cliente Dify
  └── cube_client.py               # Cliente Cube Core
tests/                  # Tests unitarios
  ├── conftest.py                  # Fixtures compartidos
  ├── test_classification.py       # Tests de clasificación
  ├── test_dify_client.py          # Tests de Dify
  └── test_weaviate.py             # Tests de Weaviate
documentos_de_referencia_tesis/  # Contexto de investigación
  ├── ARQUITECTURA.md              # Arquitectura completa del cluster
  ├── Protocolo_MCD_2025_Hector_Sanchez_v7_Weaviate.md # Protocolo v7
  └── tailscale-computers-info.md  # Inventario de nodos
```

## 📝 Roadmap de Desarrollo Chainlit

**Estado actual:** Fase 1-2 completadas, próximas: Fase 3 (RAG Documental) + Fase 3.5 (Dify)

### ✅ Fase 1-2: Foundation + Trazabilidad (Completadas)
- [x] Estructura básica con `cl.Step()` para trazabilidad (4 pasos visibles)
- [x] Clasificación de consultas (semántica vs documental)
- [x] Mock data FP&A para testing
- [x] Autenticación y tema personalizado
- [x] Despliegue en Coolify/Oracle Cloud

### 🚧 Fase 3: RAG Documental con Weaviate (Próxima)
- [ ] Upload de documentos PDF/Excel
- [ ] Integración Docling para extracción estructural
- [ ] Chunking semántico (HybridChunker θ=0.8, tablas indivisibles)
- [ ] Schema de Weaviate (Document, Chunk, MetricDefinition, BusinessRule)
- [ ] Búsqueda híbrida (vectorial + BM25) en Weaviate
- [ ] GraphRAG ligero con cross-references (1-2 saltos)

📖 **Detalles**: [roadmap/fase-3-rag-documental.md](roadmap/fase-3-rag-documental.md)

### 🚧 Fase 3.5: Capa de Explicación Dify (Crítica)
- [ ] Integración Dify como capa de explicación post-cálculo
- [ ] Dify recibe datos validados + contexto documental, genera explicaciones
- [ ] Fallback a OpenRouter si Dify falla
- [ ] Métricas de Explanation Consistency (BLEU/ROUGE)

📖 **Detalles**: [roadmap/fase-3.5-dify.md](roadmap/fase-3.5-dify.md)

### 📝 Fase 4: Router Determinista (n8n) - Documentada
- [ ] Webhook para recibir consultas de Chainlit
- [ ] Classification Node con JavaScript (3 rutas)
- [ ] Switch Node para enrutamiento
- [ ] Integración con Cube Core, Weaviate, Dify
- [ ] Métricas de Query Routing Accuracy

📖 **Detalles**: [roadmap/fase-4-n8n-router.md](roadmap/fase-4-n8n-router.md)

### 📝 Fase 5: Capa Semántica (Cube Core) - Documentada
- [ ] Modelo Facts.js con 14 métricas FP&A
- [ ] Pre-aggregations (quarterly, monthly, yearly)
- [ ] Configuración con DuckDB + Redis
- [ ] API REST para n8n/Chainlit
- [ ] Latencia P50 < 300ms

📖 **Detalles**: [roadmap/fase-5-cube-core.md](roadmap/fase-5-cube-core.md)

### 📅 Fase 6-7: Visualización + Audit Trail
- [ ] Gráficos Plotly (líneas, barras)
- [ ] DataFrames con paginación
- [ ] Exportación de sesiones (JSON, PDF)
- [ ] Dashboard de métricas de uso

### 📝 Fase 8: Evaluación con Benchmarks - Documentada
- [ ] Conversión Spider, BIRD, FinQA a Parquet
- [ ] Pipeline de evaluación (BenchmarkEvaluator)
- [ ] Comparación Baseline vs RAG vs SDRAG
- [ ] Métricas: Execution Accuracy, Latency
- [ ] Reporte automático en Markdown

📖 **Detalles**: [roadmap/fase-8-benchmarks.md](roadmap/fase-8-benchmarks.md)

---

📋 **Ver roadmap completo**: [ROADMAP.md](ROADMAP.md)  
🤖 **Documentación para implementación LLM**: [roadmap/README.md](roadmap/README.md)

## 🧪 Testing & Evaluación

### Tests Unitarios

```bash
# Ejecutar todos los tests
pytest

# Tests específicos
pytest tests/test_dify_client.py
pytest tests/test_weaviate.py

# Con coverage
pytest --cov=. --cov-report=html
```

### Benchmarks Académicos

```bash
# Convertir Spider a Parquet
python3 scripts/convert_spider_to_parquet.py

# Ejecutar evaluación
python3 scripts/evaluate_execution_accuracy.py

# Comparar sistemas
python3 scripts/compare_systems.py

# Generar reporte
python3 scripts/generate_report.py
```

**Métricas evaluadas**:
- Execution Accuracy (EX): Objetivo >95%
- Numerical Hallucination Rate: Objetivo <5%
- Query Routing Accuracy: Objetivo >98%
- Latency P50/P95/P99

Ver [roadmap/fase-8-benchmarks.md](roadmap/fase-8-benchmarks.md) para detalles completos.

---

## 🎓 Información de Investigación

**Proyecto de Tesis:**  
Arquitectura RAG Híbrida con Capa Semántica Determinista para Reducir Alucinaciones Aritméticas en Sistemas de IA Generativa aplicados a Analítica Financiera (FP&A)

**Programa:**  
Maestría en Ciencia de los Datos  
Centro Universitario de Ciencias Económico Administrativas  
Universidad de Guadalajara

**Investigador:**  
Héctor Gabriel Sánchez Pérez  
hector@sanchezmx.com  
[www.cfocoder.com](https://www.cfocoder.com)

**Período:** 2025-2027

## 📖 Referencias

### Documentos de Tesis
- **Protocolo de Investigación (v7):** [documentos_de_referencia_tesis/Protocolo_MCD_2025_Hector_Sanchez_v7_Weaviate.md](documentos_de_referencia_tesis/Protocolo_MCD_2025_Hector_Sanchez_v7_Weaviate.md)
- **Arquitectura Completa:** [documentos_de_referencia_tesis/ARQUITECTURA.md](documentos_de_referencia_tesis/ARQUITECTURA.md)
- **Cluster Tailscale:** [documentos_de_referencia_tesis/tailscale-computers-info.md](documentos_de_referencia_tesis/tailscale-computers-info.md)

### Roadmap de Implementación
- **Roadmap Principal:** [ROADMAP.md](ROADMAP.md)
- **Documentación para LLMs:** [roadmap/README.md](roadmap/README.md)
- **Análisis de Alineación:** [ANALISIS_ALINEACION_ROADMAP.md](ANALISIS_ALINEACION_ROADMAP.md)

### Tecnologías Clave
- [Chainlit Documentation](https://docs.chainlit.io)
- [Cube Core](https://cube.dev/docs)
- [Weaviate](https://weaviate.io/developers/weaviate)
- [Dify](https://docs.dify.ai)
- [n8n](https://docs.n8n.io)

---

**Nota:** Este repositorio se enfoca únicamente en el desarrollo de Chainlit como interfaz de usuario. El proyecto completo de investigación SDRAG incluye componentes adicionales (Cube Core, n8n, Dify, Weaviate) que se desarrollan en otros repositorios y nodos del cluster.
