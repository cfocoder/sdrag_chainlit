# 🗺️ SDRAG Chainlit - Roadmap de Implementación

**Proyecto:** Arquitectura RAG Híbrida con Capa Semántica Determinista  
**Componente:** Frontend Chainlit  
**Última actualización:** 21 de Diciembre, 2025  
**Estado general:** ✅ Fase 2 completada - Próxima: Fase 3 (RAG Documental)

---

## 📋 Resumen Ejecutivo

Este documento define el roadmap de implementación del frontend **Chainlit** para el proyecto SDRAG (Structured Data Retrieval Augmented Generation). Chainlit actúa como la **consola analítica determinista** del sistema, proporcionando:

- Interfaz conversacional para usuarios FP&A
- Visualización de resultados con trazabilidad completa (`cl.Step`)
- Renderizado de DataFrames, SQL visible y gráficos Plotly
- Integración con el router n8n para clasificación de consultas

---

## 🎯 Objetivo del Componente Chainlit

Chainlit es el **punto de entrada del usuario** en la arquitectura SDRAG:

```
Usuario → Chainlit → n8n (router) → Cube Core/OpenSearch → DuckDB → LLM → Chainlit
```

**Responsabilidades:**
1. Recibir consultas en lenguaje natural
2. Enviar consultas al router n8n para clasificación
3. Renderizar resultados de forma determinista (SQL + datos + explicación)
4. Proveer trazabilidad completa de cada paso con `cl.Step`
5. Mostrar visualizaciones FP&A (DataFrames, gráficos Plotly)

---

## 📊 Fases de Implementación

### ✅ Fase 1: Infraestructura Base (COMPLETADA)

| ID | Tarea | Estado | Fecha |
|----|-------|--------|-------|
| 1.1 | Crear proyecto con `uv` y `pyproject.toml` | ✅ Completado | Dic 2025 |
| 1.2 | Configurar Dockerfile para despliegue en Coolify | ✅ Completado | Dic 2025 |
| 1.3 | Integrar OpenRouter como proveedor de LLM | ✅ Completado | Dic 2025 |
| 1.4 | Desplegar en `https://chainlit.sdrag.com` | ✅ Completado | Dic 2025 |
| 1.5 | Implementar autenticación con password | ✅ Completado | Dic 2025 |
| 1.6 | Personalizar tema (colores azules del logo) | ✅ Completado | Dic 2025 |
| 1.7 | Configurar logos y branding SDRAG | ✅ Completado | Dic 2025 |

**Entregables Fase 1:**
- Chat funcional conectado a OpenRouter
- Autenticación por usuario/password
- Tema personalizado azul
- Despliegue automático vía GitHub → Coolify

---

### ✅ Fase 2: Trazabilidad con `cl.Step` (COMPLETADA)

**Objetivo:** Implementar visualización de pasos de ejecución para auditoría completa.

| ID | Tarea | Estado | Prioridad |
|----|-------|--------|-----------|
| 2.1 | Implementar estructura base de `cl.Step` | ✅ Completado | Alta |
| 2.2 | Mostrar paso de "Clasificación de consulta" | ✅ Completado | Alta |
| 2.3 | Mostrar paso de "Generación de SQL" (mock) | ✅ Completado | Alta |
| 2.4 | Mostrar paso de "Ejecución de datos" (mock) | ✅ Completado | Alta |
| 2.5 | Mostrar paso de "Generación de explicación" | ✅ Completado | Alta |
| 2.6 | Agregar timestamps y duración por paso | ✅ Completado | Media |

**Entregables Fase 2:**
- 4 pasos de trazabilidad visibles (Clasificación → SQL → Datos → Explicación)
- Tiempos de ejecución por paso
- Datos mock FP&A funcionando
- Clasificación por keywords

---

### 🚧 Fase 3: RAG Documental (OpenSearch + Docling) - PRÓXIMA

**Objetivo:** Permitir subir documentos PDF/Excel y consultarlos mediante búsqueda híbrida.

**¿Por qué esta fase ahora?** 
- OpenSearch ya está en Mac Mini (100.110.109.43:9200)
- Embeddings via OpenRouter (ya tienes API key)
- No depende de n8n ni Cube Core
- Funcionalidad real para la tesis

| ID | Tarea | Estado | Prioridad |
|----|-------|--------|-----------|
| 3.1 | Implementar upload de archivos en Chainlit | ⬜ Pendiente | Alta |
| 3.2 | Integrar Docling para extracción estructural de PDFs | ⬜ Pendiente | Alta |
| 3.3 | Implementar chunking semántico (HybridChunker θ=0.8) | ⬜ Pendiente | Alta |
| 3.4 | Generar embeddings con OpenRouter/Ollama | ⬜ Pendiente | Alta |
| 3.5 | Conectar con OpenSearch para indexación | ⬜ Pendiente | Alta |
| 3.6 | Implementar búsqueda híbrida (vectorial + BM25) | ⬜ Pendiente | Alta |
| 3.7 | Mostrar fuentes citadas con metadata | ⬜ Pendiente | Media |
| 3.8 | Preservación de tablas como unidades indivisibles | ⬜ Pendiente | Media |

**Arquitectura del flujo documental:**
```
Usuario sube PDF → Docling (extracción) → HybridChunker (chunking)
    → Embeddings (OpenRouter) → OpenSearch (indexación)

Usuario consulta → Clasificación → OpenSearch (búsqueda híbrida)
    → Chunks relevantes + metadata → LLM (explicación) → Respuesta
```

**Metadata por chunk:**
```json
{
  "text": "Revenue for Q4 2024 was $1.2M...",
  "metadata": {
    "source_document": "financial_report_2024.pdf",
    "fiscal_year": "2024",
    "document_type": "P&L Statement",
    "section": "Revenue Recognition",
    "page_number": 12
  }
}
```

**Servicios requeridos:**
- OpenSearch: `http://100.110.109.43:9200` (Mac Mini)
- Embeddings: OpenRouter API (text-embedding-3-small) o Ollama local

---

### 📅 Fase 4: Integración con n8n Router

**Objetivo:** Conectar Chainlit con el router determinista n8n para clasificación real de consultas.

| ID | Tarea | Estado | Prioridad |
|----|-------|--------|-----------|
| 4.1 | Crear webhook handler para enviar consultas a n8n | ⬜ Pendiente | Alta |
| 4.2 | Implementar clasificación semántica vs. documental | ⬜ Pendiente | Alta |
| 4.3 | Manejar respuestas JSON estructuradas de n8n | ⬜ Pendiente | Alta |
| 4.4 | Implementar timeout y manejo de errores | ⬜ Pendiente | Media |

---

### 📅 Fase 5: Integración con Cube Core

**Objetivo:** Conectar directamente con la capa semántica para consultas SQL deterministas.

| ID | Tarea | Estado | Prioridad |
|----|-------|--------|-----------|
| 5.1 | Implementar cliente HTTP para Cube Core API | ⬜ Pendiente | Alta |
| 5.2 | Parsear respuestas de métricas Cube | ⬜ Pendiente | Alta |
| 5.3 | Mostrar SQL canónico generado por Cube | ⬜ Pendiente | Alta |
| 5.4 | Cachear resultados frecuentes (Redis) | ⬜ Pendiente | Baja |

**Métricas FP&A disponibles en Cube Core:**
- `Revenue`, `COGS`, `GrossMargin`, `OPEX`, `EBITDA`, `NetIncome`

---

### 📅 Fase 6: Visualización Avanzada

**Objetivo:** DataFrames interactivos y gráficos Plotly.

| ID | Tarea | Estado | Prioridad |
|----|-------|--------|-----------|
| 6.1 | Paginación para tablas grandes | ⬜ Pendiente | Media |
| 6.2 | Gráficos de línea (tendencias) | ⬜ Pendiente | Alta |
| 6.3 | Gráficos de barras (comparaciones) | ⬜ Pendiente | Alta |
| 6.4 | Auto-detectar tipo de gráfico | ⬜ Pendiente | Baja |

---

### 📅 Fase 7: Audit Trail y Exportación

**Objetivo:** Permitir exportar trazas de ejecución para auditoría.

| ID | Tarea | Estado | Prioridad |
|----|-------|--------|-----------|
| 7.1 | Exportar sesión a JSON | ⬜ Pendiente | Media |
| 7.2 | Exportar sesión a PDF | ⬜ Pendiente | Baja |
| 7.3 | Guardar historial en base de datos | ⬜ Pendiente | Baja |
| 7.4 | Dashboard de métricas de uso | ⬜ Pendiente | Baja |

---

### 📅 Fase 8: Evaluación de Benchmarks

**Objetivo:** Interfaz para ejecutar y visualizar resultados de benchmarks.

| ID | Tarea | Estado | Prioridad |
|----|-------|--------|-----------|
| 8.1 | Modo "benchmark" para ejecución masiva | ⬜ Pendiente | Alta |
| 8.2 | Mostrar métricas de Execution Accuracy | ⬜ Pendiente | Alta |
| 8.3 | Comparar resultados: LLM solo vs SDRAG | ⬜ Pendiente | Alta |
| 8.4 | Visualizar latencias (P50, P95, P99) | ⬜ Pendiente | Media |

---

## 📈 Métricas de Éxito del Componente

| Métrica | Objetivo | Estado Actual |
|---------|----------|---------------|
| **Traceability Completeness** | 100% de consultas con pasos visibles | ✅ 100% (Fase 2) |
| **Latencia UI** | < 2s para queries simples | ✅ ~1.5s |
| **Disponibilidad** | 99% uptime | ✅ Funcionando |
| **Autenticación** | 100% de accesos autenticados | ✅ Implementado |

---

## 🔧 Variables de Entorno Requeridas

```bash
# Autenticación
CHAINLIT_AUTH_SECRET=<clave-secreta-larga>
CHAINLIT_USER=<usuario>
CHAINLIT_PASSWORD=<password>

# LLM Provider
OPENROUTER_API_KEY=<api-key>
OPENROUTER_MODEL=mistralai/devstral-2512:free

# RAG Documental (Fase 3)
OPENSEARCH_URL=http://100.110.109.43:9200
OPENSEARCH_INDEX=sdrag_documents
EMBEDDING_MODEL=nomic-embed-text  # o text-embedding-3-small via OpenRouter

# Integraciones (Fase 4-5)
N8N_WEBHOOK_URL=http://100.105.68.15:5678/webhook/sdrag-query
CUBE_API_URL=http://100.116.107.52:4000
```

---

## 📚 Referencias

- [Protocolo de Investigación](Protocolo_MCD_2025_Hector_Sanchez_v4_Chainlit.md)
- [Arquitectura del Sistema](ARQUITECTURA.md)
- [README Tesis](README_TESIS.md)
- [Documentación Chainlit](https://docs.chainlit.io)

---

## 📝 Changelog

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2025-12-21 | 0.3.0 | Fase 2 trazabilidad + Reorganizar RAG a Fase 3 + traducciones es-ES |
| 2025-12-21 | 0.2.0 | Autenticación + Tema azul |
| 2025-12-21 | 0.1.0 | Chat básico con OpenRouter |

---

*Documento generado para tracking del proyecto SDRAG Chainlit*  
*Maestría en Ciencia de los Datos - Universidad de Guadalajara*
