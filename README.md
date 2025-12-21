# SDRAG Chainlit Frontend

Frontend determinista para arquitectura RAG híbrida con capa semántica.

## 🏗️ Arquitectura

```
Usuario → Chainlit → n8n (router) → Cube Core/OpenSearch → DuckDB → Ollama → Chainlit
```

## 🎯 Características

- ✅ **Trazabilidad completa**: Cada paso visible con `cl.Step()`
- ✅ **Ejecución determinista**: Cálculos verificados vía Cube Core
- ✅ **Visualización FP&A**: DataFrames, SQL, gráficos Plotly
- ✅ **Sin alucinaciones aritméticas**: LLM solo explica, no calcula

## 🚀 Despliegue

### Local (desarrollo)

```bash
pip install -r requirements.txt
chainlit run app.py
```

Abre: http://localhost:8001

### Coolify (producción)

1. Conectar repositorio GitHub en Coolify
2. Coolify detecta `Dockerfile` automáticamente
3. Configurar dominio: `chainlit.sdrag.com`
4. Agregar variables de entorno:
   - `N8N_WEBHOOK_URL`
   - `OLLAMA_BASE_URL`
   - `CUBE_API_URL` (cuando esté listo)
5. Deploy

## 📊 Variables de Entorno

```bash
N8N_WEBHOOK_URL=http://100.105.68.15:5678/webhook/sdrag-query
OLLAMA_BASE_URL=http://100.116.107.52:11434
CUBE_API_URL=http://100.116.107.52:4000
OPENSEARCH_URL=http://100.110.109.43:9200
```

## 📝 Roadmap

- [x] Estructura básica con `cl.Step()` para trazabilidad
- [ ] Integración n8n para clasificación de consultas
- [ ] Integración Cube Core para SQL determinista
- [ ] Visualización de DataFrames con pandas
- [ ] Gráficos Plotly para métricas FP&A
- [ ] Integración Ollama para explicaciones
- [ ] Exportar audit trail a JSON
- [ ] Métricas de latency/accuracy

## 🎓 Proyecto de Tesis

**Arquitectura RAG Híbrida con Capa Semántica Determinista (SDRAG)**  
Maestría en Ciencia de los Datos  
Universidad de Guadalajara

Investigador: Héctor Gabriel Sánchez Pérez  
Diciembre 2025
