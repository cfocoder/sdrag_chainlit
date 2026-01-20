# 📁 Roadmap - Guía para Agentes LLM

Este directorio contiene los detalles de implementación de cada fase del proyecto SDRAG Chainlit.

**Documento raíz**: Ver [../ROADMAP.md](../ROADMAP.md) para el índice de alto nivel.

---

## 🎯 Propósito

Cada archivo en este directorio está diseñado para ser consumido por agentes LLM (Claude, GPT-4, etc.) que implementan las fases del proyecto. Los documentos incluyen:

- **Prerrequisitos** verificables antes de comenzar
- **Tareas** con criterios de aceptación claros
- **Código de referencia** listo para adaptar
- **Comandos de verificación** para confirmar completitud

---

## 📂 Archivos de Fase

| Archivo | Fase | Estado | Descripción |
|---------|------|--------|-------------|
| [fase-0-infraestructura.md](fase-0-infraestructura.md) | 0 | 🔧 Verificación | Verificar servicios del cluster (Weaviate, Dify, Ollama, Cube Core, n8n) |
| [fase-3-rag-documental.md](fase-3-rag-documental.md) | 3 | 🚧 Próxima | RAG Documental con Weaviate + Docling |
| [fase-3.5-dify.md](fase-3.5-dify.md) | 3.5 | 🚧 Crítica | Integración de Dify como capa de explicación |
| [fase-4-n8n-router.md](fase-4-n8n-router.md) | 4 | 📝 Listo | Router determinista (3 rutas: Semántica, Documental, Híbrida) |
| [fase-5-cube-core.md](fase-5-cube-core.md) | 5 | 📝 Listo | Capa semántica (métricas FP&A, pre-aggregations) |
| [fase-8-benchmarks.md](fase-8-benchmarks.md) | 8 | 📝 Listo | Evaluación con benchmarks (Spider, BIRD, FinQA) |
| [comercializacion.md](comercializacion.md) | Post-tesis | 📅 Futuro | Roadmap de comercialización (SaaS) |

> **IMPORTANTE**: Ejecutar Fase 0 antes de cualquier otra fase para verificar que los servicios estén operativos.

---

## 🏗️ Arquitectura Simplificada (Protocolo v7)

El proyecto utiliza una arquitectura simplificada con **Weaviate como única base de datos vectorial**:

```
Usuario → Chainlit → n8n (clasificación determinista)
    ↓
    ├─ Semántica (métricas/agregaciones): Cube Core → DuckDB → JSON
    ├─ Documental (contexto textual): Weaviate → Chunks
    └─ Híbrida (datos + contexto): Cube Core → Weaviate → Combinación
    ↓
    Dify (explicación post-cálculo)
    ↓
    Chainlit (cl.Step + DataFrame + SQL + Gráfico)
```

**Principios clave:**
- **3 rutas de clasificación**: Semántica, Documental, Híbrida
- **Weaviate única**: Simplificación deliberada para recursos académicos
- **GraphRAG ligero**: Cross-references en Weaviate (1-2 saltos máximo)
- **Dify solo explica**: Nunca clasifica, genera SQL ni calcula

---

## 🖥️ Servicios del Cluster

| Servicio | Host | IP Tailscale | Puerto | Rol |
|----------|------|--------------|--------|-----|
| Chainlit | cfocoder3 | 100.105.68.15 | 8001 | Frontend UI |
| n8n | cfocoder3 | 100.105.68.15 | 5678 | Router determinista |
| Dask Scheduler | cfocoder3 | 100.105.68.15 | 8786, 8787 | Coordinador ETL |
| Dify | macmini | 100.110.109.43 | 80 | Capa de explicación |
| **Weaviate** | macmini | 100.110.109.43 | 8080 | **Única base vectorial** |
| MinIO | macmini | 100.110.109.43 | 9000 | Object storage (DuckLake) |
| Cube Core | vostro | 100.116.107.52 | 4000 | Capa semántica SQL |
| Ollama | vostro | 100.116.107.52 | 11434 | Embeddings e inferencia |
| Docling | vostro | 100.116.107.52 | - | Extracción de PDFs |

---

## 🔄 Orden de Implementación

1. **Fase 0**: Verificar infraestructura (SIEMPRE ejecutar primero)
2. **Fase 3**: RAG Documental (Weaviate + Docling + embeddings)
3. **Fase 3.5**: Dify (capa de explicación)
4. **Fase 4+**: n8n Router, Cube Core, Visualización (pendientes de documentar)

---

## 📋 Instrucciones para Agentes LLM

### Antes de Implementar Cualquier Fase

1. **Leer el archivo de fase** completo antes de escribir código
2. **Ejecutar Fase 0** si no se ha verificado la infraestructura
3. **Verificar prerrequisitos** listados en cada archivo
4. **Seguir el orden de tareas** - las dependencias están documentadas

### Estructura de Cada Archivo de Fase

```markdown
# Fase X: Nombre

## Prerrequisitos
- [ ] Fases previas requeridas
- [ ] Servicios que deben estar operativos
- [ ] Comandos de verificación

## Tarea X.1: Nombre de la Tarea
### Descripción
### Código de referencia
### Criterios de aceptación
### Verificación

## Checklist Final Fase X
```

### Al Completar una Tarea

1. Verificar criterios de aceptación
2. Ejecutar comandos de verificación
3. Marcar checkbox en el checklist
4. Continuar con siguiente tarea

---

## 🧰 Código Base Actual

Antes de implementar, revisar:
- `app.py`: Aplicación principal (~338 líneas)
- `app.py:80` - `classify_query()`: Clasificación actual por keywords
- `app.py:182` - `call_openrouter()`: Patrón para llamadas HTTP async
- `app.py:234` - `main()`: Handler de mensajes con cl.Step

## 📐 Convenciones de Código

- Python 3.11+
- Usar `uv` para dependencias, nunca `pip`
- Type hints en funciones
- Docstrings en español
- httpx para llamadas HTTP async
- Timeout de 30s para APIs externas

---

## 🧪 Testing

Cada fase incluye una tarea de tests. Ver [ROADMAP.md#política-de-testing](../ROADMAP.md#-política-de-testing) para la política completa.

### Estructura de Tests

```
tests/
├── conftest.py              # Fixtures compartidos (mocks)
├── test_classification.py   # classify_query()
├── test_dify_client.py      # call_dify() + fallback
├── test_weaviate.py         # Indexación y búsqueda híbrida
├── test_embeddings.py       # Generación de embeddings
└── test_integration.py      # Flujos end-to-end
```

### Comandos Rápidos

```bash
# Ejecutar todos los tests
pytest

# Tests de una fase específica
pytest tests/test_dify_client.py      # Fase 3.5
pytest tests/test_weaviate.py         # Fase 3

# Con coverage
pytest --cov=. --cov-report=html

# Tests en paralelo (si tienes pytest-xdist)
pytest -n auto
```

### Principios de Testing

1. **Mocks para servicios externos** - Nunca llamar a Dify, Weaviate, Ollama reales
2. **Fixtures en conftest.py** - Datos mock reutilizables
3. **Coverage >80%** - En funciones críticas
4. **Tests por fase** - Cada `fase-X.md` incluye tarea de tests específica

### Tests por Fase

| Fase | Tests Requeridos | Tarea |
|------|------------------|-------|
| 3 | `test_weaviate.py`, `test_embeddings.py` | 3.9 |
| 3.5 | `test_dify_client.py` | 3.5.9 |
| 4 | `test_n8n_router.py` | Pendiente |
| 5 | `test_cube_client.py` | Pendiente |

---

## 📚 Referencias

- **Protocolo de Investigación**: [../documentos_de_referencia_tesis/Protocolo_MCD_2025_Hector_Sanchez_v7_Weaviate.md](../documentos_de_referencia_tesis/Protocolo_MCD_2025_Hector_Sanchez_v7_Weaviate.md)
- **Arquitectura del Sistema**: [../documentos_de_referencia_tesis/ARQUITECTURA.md](../documentos_de_referencia_tesis/ARQUITECTURA.md)
- **Información de Infraestructura**: [../documentos_de_referencia_tesis/tailscale-computers-info.md](../documentos_de_referencia_tesis/tailscale-computers-info.md)

---

*Última actualización: 19 de Enero, 2026*
