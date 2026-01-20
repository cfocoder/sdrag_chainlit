# Fase 4: Router Determinista (n8n)

**Objetivo**: Implementar clasificación determinista de consultas en 3 rutas (Semántica, Documental, Híbrida) usando n8n.

**Prioridad**: CRÍTICA - Componente central de la arquitectura SDRAG.

---

## Prerrequisitos

### Fases previas requeridas
- [x] Fase 0: Infraestructura verificada
- [x] Fase 3: RAG Documental (para ruta documental)
- [x] Fase 3.5: Dify (para explicaciones)

### Servicios que deben estar operativos

Ejecutar antes de comenzar:
```bash
# Verificar n8n
curl -I http://100.105.68.15:5678
# Debe retornar: HTTP/1.1 200 OK

# Verificar Cube Core (para ruta semántica)
curl -s http://100.116.107.52:4000/readyz

# Verificar Weaviate (para ruta documental)
curl -s http://100.110.109.43:8080/v1/.well-known/ready

# Verificar Dify (para explicaciones)
curl -I http://100.110.109.43:80
```

- [ ] n8n: `http://100.105.68.15:5678` - Orquestador de flujos
- [ ] Cube Core: `http://100.116.107.52:4000` - Capa semántica
- [ ] Weaviate: `http://100.110.109.43:8080` - Base vectorial
- [ ] Dify: `http://100.110.109.43:80` - Capa de explicación

---

## Contexto

### ¿Por qué n8n para Clasificación?

n8n permite implementar un **router determinista** con ventajas sobre clasificación mediante LLM:

| Criterio | Clasificación con LLM | n8n Determinista |
|----------|----------------------|------------------|
| **Reproducibilidad** | Baja (estocástico) | Alta (reglas fijas) |
| **Trazabilidad** | Opaca (prompt → output) | Explícita (logs de nodos) |
| **Latencia** | Alta (~500-1000ms) | Baja (~50-100ms) |
| **Costo** | Por token | Gratis (self-hosted) |
| **Auditabilidad** | Difícil | Completa |
| **Debugging** | Complejo | Visual (UI de n8n) |

### Rol de n8n en SDRAG

n8n **SÍ es responsable de**:
- Clasificar consultas en 3 rutas (Semántica, Documental, Híbrida)
- Orquestar llamadas a Cube Core, Weaviate, Dify
- Combinar resultados en flujo híbrido
- Registrar métricas de routing (latencia, ruta elegida)

n8n **NO participa en**:
- Generación de SQL (responsabilidad de Cube Core)
- Generación de embeddings (responsabilidad de Ollama)
- Generación de explicaciones (responsabilidad de Dify)

---

## Arquitectura del Router

```
Chainlit → Webhook n8n
              ↓
     [Classification Node]
      (JavaScript + Reglas)
              ↓
          [Switch Node]
         /      |      \
        /       |       \
   Semántica  Documental  Híbrida
       ↓         ↓          ↓
   Cube Core  Weaviate   Cube Core + Weaviate
       ↓         ↓          ↓
       +------- Dify -------+
              ↓
       [Respond to Webhook]
              ↓
          Chainlit
```

---

## Tarea 4.1: Crear Webhook de Entrada

### Descripción
Configurar webhook que reciba consultas de Chainlit.

### Pasos en n8n UI

1. Crear nuevo workflow: `SDRAG Router`
2. Agregar nodo **Webhook**
3. Configurar:
   - **Method**: POST
   - **Path**: `sdrag-query`
   - **Response Mode**: When Last Node Finishes
   - **Response Data**: All Entries

4. Test payload:
```json
{
  "query": "¿Cuál fue el revenue de Q1 2024?",
  "user_id": "test_user",
  "session_id": "test_session"
}
```

### URL resultante
```
http://100.105.68.15:5678/webhook/sdrag-query
```

### Criterios de aceptación
- [ ] Webhook creado y activo
- [ ] POST request exitoso retorna 200
- [ ] Payload JSON correctamente parseado

---

## Tarea 4.2: Implementar Classification Node

### Descripción
Clasificar consulta en 3 rutas usando reglas determinísticas.

### Agregar nodo "Function" en n8n

**Código JavaScript**:
```javascript
// Classification Logic para SDRAG Router
const query = $input.item.json.query.toLowerCase();
const timestamp = new Date().toISOString();

// Keywords por ruta
const SEMANTIC_KEYWORDS = [
  'revenue', 'cogs', 'ebitda', 'margen', 'utilidad', 'ganancia',
  'gasto', 'opex', 'capex', 'ingresos', 'ventas', 'costos',
  'total', 'suma', 'promedio', 'comparar', 'varianza',
  'q1', 'q2', 'q3', 'q4', 'trimestre', 'año', 'mes',
  'cuánto', 'cuál fue', 'mostrar', 'calcular'
];

const DOCUMENTAL_KEYWORDS = [
  'define', 'qué es', 'explica', 'cómo se calcula', 'cómo se determina',
  'metodología', 'política', 'regla', 'criterio', 'definición',
  'según el reporte', 'menciona', 'dice', 'referencia',
  'documento', 'sección', 'página'
];

// Clasificación
let route = 'semantic';  // default
let confidence = 0;
let matched_keywords = [];

// Contar matches
const semantic_matches = SEMANTIC_KEYWORDS.filter(kw => query.includes(kw));
const documental_matches = DOCUMENTAL_KEYWORDS.filter(kw => query.includes(kw));

if (documental_matches.length > 0 && semantic_matches.length === 0) {
  // Solo keywords documentales → Ruta Documental
  route = 'documental';
  confidence = documental_matches.length / DOCUMENTAL_KEYWORDS.length;
  matched_keywords = documental_matches;
  
} else if (semantic_matches.length > 0 && documental_matches.length > 0) {
  // Ambos tipos → Ruta Híbrida
  route = 'hybrid';
  confidence = (semantic_matches.length + documental_matches.length) / 
               (SEMANTIC_KEYWORDS.length + DOCUMENTAL_KEYWORDS.length);
  matched_keywords = [...semantic_matches, ...documental_matches];
  
} else {
  // Solo semánticas o ninguna → Ruta Semántica (default)
  route = 'semantic';
  confidence = semantic_matches.length > 0 ? 
               semantic_matches.length / SEMANTIC_KEYWORDS.length : 0.5;
  matched_keywords = semantic_matches;
}

// Output
return {
  json: {
    query: $input.item.json.query,
    query_normalized: query,
    route: route,
    confidence: confidence,
    matched_keywords: matched_keywords,
    timestamp: timestamp,
    user_id: $input.item.json.user_id,
    session_id: $input.item.json.session_id
  }
};
```

### Criterios de aceptación
- [ ] Classification node retorna ruta correcta
- [ ] Test: "¿Cuál fue el revenue?" → `semantic`
- [ ] Test: "Define EBITDA" → `documental`
- [ ] Test: "¿Cuál fue el EBITDA y cómo se calcula?" → `hybrid`
- [ ] Confidence score > 0 para todas las rutas

---

## Tarea 4.3: Implementar Switch Node

### Descripción
Enrutar según clasificación a diferentes ramas de procesamiento.

### Configurar Switch Node

**Mode**: Rules

**Rules**:
1. **Rule 1 - Semántica**:
   - Output: 0
   - Condition: `{{ $json.route }}` equals `semantic`

2. **Rule 2 - Documental**:
   - Output: 1
   - Condition: `{{ $json.route }}` equals `documental`

3. **Rule 3 - Híbrida**:
   - Output: 2
   - Condition: `{{ $json.route }}` equals `hybrid`

4. **Fallback**:
   - Output: 0 (default a semántica)

### Criterios de aceptación
- [ ] Switch node conectado a Classification node
- [ ] 3 outputs configurados correctamente
- [ ] Fallback a ruta semántica funciona

---

## Tarea 4.4: Implementar Ruta Semántica (Cube Core)

### Descripción
Procesar consultas de métricas/agregaciones vía Cube Core.

### Nodo: HTTP Request (Cube Core API)

**Configuración**:
- **Method**: POST
- **URL**: `http://100.116.107.52:4000/cubejs-api/v1/load`
- **Authentication**: None (o API key si configurado)
- **Body**:
```json
{
  "query": {
    "measures": ["Facts.revenue"],
    "dimensions": ["Facts.fiscalQuarter"],
    "filters": [
      {
        "member": "Facts.fiscalQuarter",
        "operator": "equals",
        "values": ["Q1_2024"]
      }
    ]
  }
}
```

**Nota**: En producción, este query debe ser generado dinámicamente basado en la consulta del usuario. Para MVP, usar queries mock basados en keywords.

### Ejemplo de Query Builder Simplificado

Agregar nodo "Function" antes de HTTP Request:

```javascript
// Simplified Query Builder para Cube Core
const query = $input.item.json.query_normalized;

// Detectar métrica
let measure = "Facts.revenue";  // default
if (query.includes('cogs') || query.includes('costos')) {
  measure = "Facts.cogs";
} else if (query.includes('ebitda')) {
  measure = "Facts.ebitda";
} else if (query.includes('margen')) {
  measure = "Facts.grossMargin";
}

// Detectar período
let period = null;
if (query.match(/q1.*2024/)) {
  period = "Q1_2024";
} else if (query.match(/q2.*2024/)) {
  period = "Q2_2024";
} else if (query.match(/2024/)) {
  period = "2024";
}

// Construir query Cube
const cubeQuery = {
  query: {
    measures: [measure],
    dimensions: ["Facts.fiscalQuarter"],
    filters: period ? [
      {
        member: "Facts.fiscalQuarter",
        operator: "equals",
        values: [period]
      }
    ] : []
  }
};

return {
  json: {
    ...($input.item.json),
    cube_query: cubeQuery,
    detected_metric: measure,
    detected_period: period
  }
};
```

### Criterios de aceptación
- [ ] HTTP Request a Cube Core exitoso
- [ ] Response contiene datos numéricos
- [ ] SQL visible en metadata
- [ ] Latencia < 500ms (p50)

---

## Tarea 4.5: Implementar Ruta Documental (Weaviate)

### Descripción
Procesar consultas explicativas vía Weaviate.

### Nodo: HTTP Request (Weaviate Hybrid Search)

**Configuración**:
- **Method**: POST
- **URL**: `http://100.110.109.43:8080/v1/graphql`
- **Headers**:
  - `Content-Type`: `application/json`
- **Body**:
```json
{
  "query": "{ Get { Chunk(hybrid: {query: \"{{ $json.query }}\", alpha: 0.5}, limit: 5) { content section page_number _additional { score } } } }"
}
```

### Nodo: Function (Parse Weaviate Response)

```javascript
// Parse Weaviate response
const weaviateData = $input.item.json.data.Get.Chunk;

// Extraer chunks relevantes
const chunks = weaviateData.map(chunk => ({
  content: chunk.content,
  section: chunk.section,
  page_number: chunk.page_number,
  score: chunk._additional.score
}));

// Ordenar por score descendente
chunks.sort((a, b) => b.score - a.score);

return {
  json: {
    ...($input.item.json),
    weaviate_chunks: chunks,
    context: chunks.map(c => c.content).join('\n\n')
  }
};
```

### Criterios de aceptación
- [ ] HTTP Request a Weaviate exitoso
- [ ] Response contiene chunks con scores
- [ ] Top 5 chunks extraídos
- [ ] Latencia < 300ms (p50)

---

## Tarea 4.6: Implementar Ruta Híbrida

### Descripción
Combinar resultados de Cube Core (datos) + Weaviate (contexto).

### Flujo Híbrido

1. **Parallelizar**: Ejecutar Cube Core y Weaviate simultáneamente
   - Usar nodo **Split In Batches** o ejecutar ambos en paralelo

2. **Merge**: Combinar resultados
   - Nodo: **Merge** (Mode: Merge By Position)

3. **Function**: Estructurar payload para Dify

```javascript
// Combinar datos de Cube Core + contexto de Weaviate
const cubeData = $input.item.json.cube_data;
const weaviateChunks = $input.item.json.weaviate_chunks;

return {
  json: {
    query: $input.item.json.query,
    route: 'hybrid',
    // Datos numéricos de Cube Core
    data: cubeData.data,
    sql: cubeData.sql,
    // Contexto documental de Weaviate
    context: weaviateChunks.map(c => c.content).join('\n\n'),
    sources: weaviateChunks.map(c => ({
      section: c.section,
      page: c.page_number,
      score: c.score
    }))
  }
};
```

### Criterios de aceptación
- [ ] Cube Core y Weaviate ejecutados en paralelo
- [ ] Resultados correctamente fusionados
- [ ] Payload híbrido completo
- [ ] Latencia < 800ms (p50)

---

## Tarea 4.7: Integrar Dify para Explicación

### Descripción
Enviar datos deterministas (de cualquier ruta) a Dify para generar explicación.

### Nodo: HTTP Request (Dify API)

**Configuración**:
- **Method**: POST
- **URL**: `http://100.110.109.43:80/v1/chat-messages`
- **Headers**:
  - `Content-Type`: `application/json`
  - `Authorization`: `Bearer {{ $env.DIFY_API_KEY }}`
- **Body**:
```json
{
  "inputs": {
    "query": "{{ $json.query }}",
    "data": "{{ $json.data }}",
    "sql": "{{ $json.sql }}",
    "context": "{{ $json.context }}"
  },
  "response_mode": "blocking",
  "user": "{{ $json.user_id }}"
}
```

### Nodo: Function (Parse Dify Response)

```javascript
// Extraer explicación de Dify
const explanation = $input.item.json.answer;

return {
  json: {
    query: $input.item.json.query,
    route: $input.item.json.route,
    data: $input.item.json.data,
    sql: $input.item.json.sql,
    context: $input.item.json.context || null,
    explanation: explanation,
    timestamp: new Date().toISOString()
  }
};
```

### Criterios de aceptación
- [ ] Dify recibe payload correctamente estructurado
- [ ] Explicación generada en español
- [ ] Valores numéricos preservados exactamente
- [ ] Latencia de Dify < 1500ms (p50)

---

## Tarea 4.8: Implementar Response Node

### Descripción
Retornar resultado estructurado a Chainlit.

### Nodo: Respond to Webhook

**Response**:
```json
{
  "success": true,
  "query": "{{ $json.query }}",
  "route": "{{ $json.route }}",
  "data": "{{ $json.data }}",
  "sql": "{{ $json.sql }}",
  "context": "{{ $json.context }}",
  "explanation": "{{ $json.explanation }}",
  "timestamp": "{{ $json.timestamp }}",
  "latency_ms": "{{ $json.latency_ms }}"
}
```

### Criterios de aceptación
- [ ] Response 200 OK
- [ ] JSON válido
- [ ] Todos los campos presentes
- [ ] Chainlit puede parsear respuesta

---

## Tarea 4.9: Integración con Chainlit

### Descripción
Modificar `app.py` para llamar al webhook n8n en lugar de mock data.

### Código de referencia

```python
# app.py - Modificar función existente

import httpx

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://100.105.68.15:5678/webhook/sdrag-query")

async def call_n8n_router(query: str, user_id: str = "default") -> dict:
    """
    Envía consulta al router n8n y retorna resultado estructurado.
    
    Args:
        query: Consulta del usuario
        user_id: ID del usuario (para tracking)
    
    Returns:
        Resultado con route, data, sql, explanation
    """
    async with cl.Step(name="Router n8n", type="tool") as step:
        step.input = query
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    N8N_WEBHOOK_URL,
                    json={
                        "query": query,
                        "user_id": user_id,
                        "session_id": cl.user_session.get("id")
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                step.output = f"Route: {result['route']}"
                return result
                
        except httpx.HTTPError as e:
            step.output = f"Error: {str(e)}"
            # Fallback a mock data
            return {"error": str(e), "route": "error"}

@cl.on_message
async def main(message: cl.Message):
    query = message.content
    
    # Llamar al router n8n
    result = await call_n8n_router(query)
    
    if result.get("error"):
        await cl.Message(content=f"Error en router: {result['error']}").send()
        return
    
    # Mostrar resultados con cl.Step
    async with cl.Step(name="Clasificación", type="tool") as step:
        step.output = f"Ruta: {result['route']}"
    
    async with cl.Step(name="SQL Generado", type="tool") as step:
        step.input = result.get('sql', 'N/A')
        step.output = "SQL ejecutado exitosamente"
    
    async with cl.Step(name="Datos Obtenidos", type="tool") as step:
        step.output = str(result.get('data', {}))
    
    async with cl.Step(name="Explicación", type="llm") as step:
        step.output = result['explanation']
    
    # Enviar respuesta final
    await cl.Message(content=result['explanation']).send()
```

### Criterios de aceptación
- [ ] `app.py` llama correctamente a n8n webhook
- [ ] Timeout configurado (30s)
- [ ] Manejo de errores con fallback
- [ ] cl.Step muestra trazabilidad completa

---

## Tarea 4.10: Métricas de Routing

### Descripción
Registrar métricas para evaluar Query Routing Accuracy.

### Nodo: Function (Log Metrics)

Agregar después del Classification Node:

```javascript
// Log routing metrics
const metrics = {
  timestamp: new Date().toISOString(),
  query: $input.item.json.query,
  route: $input.item.json.route,
  confidence: $input.item.json.confidence,
  matched_keywords: $input.item.json.matched_keywords,
  user_id: $input.item.json.user_id
};

// En producción, enviar a sistema de métricas (InfluxDB, Prometheus, etc.)
console.log('ROUTING_METRIC:', JSON.stringify(metrics));

return { json: $input.item.json };
```

### Análisis Manual

Para evaluar Query Routing Accuracy:

```bash
# Extraer logs de n8n
docker logs n8n 2>&1 | grep "ROUTING_METRIC" > routing_metrics.jsonl

# Analizar con Python
import pandas as pd

df = pd.read_json('routing_metrics.jsonl', lines=True)
print(f"Total queries: {len(df)}")
print(df['route'].value_counts())
print(f"Average confidence: {df['confidence'].mean():.2f}")
```

### Criterios de aceptación
- [ ] Métricas registradas en logs
- [ ] Formato JSON válido
- [ ] Campos necesarios presentes (query, route, confidence)
- [ ] Query Routing Accuracy medible manualmente

---

## Testing

### Test 1: Ruta Semántica

```bash
curl -X POST http://100.105.68.15:5678/webhook/sdrag-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Cuál fue el revenue de Q1 2024?",
    "user_id": "test"
  }' | jq .
```

**Esperado**:
```json
{
  "success": true,
  "route": "semantic",
  "data": {"revenue": 980000, "period": "Q1_2024"},
  "sql": "SELECT SUM(amount) FROM facts WHERE quarter='Q1' AND year=2024",
  "explanation": "El revenue de Q1 2024 fue de $980,000..."
}
```

### Test 2: Ruta Documental

```bash
curl -X POST http://100.105.68.15:5678/webhook/sdrag-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Cómo se calcula el EBITDA?",
    "user_id": "test"
  }' | jq .
```

**Esperado**:
```json
{
  "success": true,
  "route": "documental",
  "context": "EBITDA se calcula como Revenue - COGS - OPEX...",
  "explanation": "Según la documentación, EBITDA..."
}
```

### Test 3: Ruta Híbrida

```bash
curl -X POST http://100.105.68.15:5678/webhook/sdrag-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "¿Cuál fue el EBITDA de 2024 y cómo se calcula?",
    "user_id": "test"
  }' | jq .
```

**Esperado**:
```json
{
  "success": true,
  "route": "hybrid",
  "data": {"ebitda": 1234567, "period": "2024"},
  "context": "EBITDA se calcula como...",
  "explanation": "El EBITDA de 2024 fue $1,234,567. Esta métrica se calcula..."
}
```

### Tests Unitarios

```python
# tests/test_n8n_router.py
import pytest
import httpx
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_call_n8n_router_semantic(mock_httpx_client):
    """Test ruta semántica."""
    mock_response = {
        "route": "semantic",
        "data": {"revenue": 980000},
        "explanation": "El revenue fue..."
    }
    mock_httpx_client.post.return_value.json.return_value = mock_response
    
    result = await call_n8n_router("¿Cuál fue el revenue?")
    
    assert result["route"] == "semantic"
    assert "revenue" in result["data"]

@pytest.mark.asyncio
async def test_call_n8n_router_documental(mock_httpx_client):
    """Test ruta documental."""
    mock_response = {
        "route": "documental",
        "context": "EBITDA se calcula...",
        "explanation": "Según la documentación..."
    }
    mock_httpx_client.post.return_value.json.return_value = mock_response
    
    result = await call_n8n_router("¿Cómo se calcula EBITDA?")
    
    assert result["route"] == "documental"
    assert "context" in result

@pytest.mark.asyncio
async def test_call_n8n_router_timeout():
    """Test manejo de timeout."""
    with pytest.raises(httpx.TimeoutException):
        async with httpx.AsyncClient(timeout=0.001) as client:
            await client.post("http://100.105.68.15:5678/webhook/sdrag-query")
```

---

## Métricas de Éxito

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| **Query Routing Accuracy** | >98% | Manual validation sobre 100 consultas |
| **Latencia End-to-End** | <2s (p50) | Logs de n8n |
| **Disponibilidad** | >99% | Uptime monitoring |
| **Error Rate** | <1% | Logs de errores |

---

## Troubleshooting

### Problema: Webhook no responde

```bash
# Verificar n8n está corriendo
ssh cfocoder3
docker ps | grep n8n

# Revisar logs
docker logs n8n --tail 50
```

### Problema: Clasificación incorrecta

- Revisar keywords en Classification Node
- Ajustar regex patterns
- Agregar más ejemplos a SEMANTIC_KEYWORDS/DOCUMENTAL_KEYWORDS

### Problema: Timeout en Cube Core

```bash
# Verificar Cube Core
ssh vostro
curl http://localhost:4000/readyz

# Revisar logs
docker logs cube --tail 50
```

---

## Próximos Pasos

Después de completar esta fase:
1. ✅ Router determinista operativo
2. → Fase 5: Implementar modelo semántico completo en Cube Core
3. → Fase 6: Visualizaciones avanzadas (DataFrames, Plotly)
4. → Fase 8: Ejecutar benchmarks para medir Query Routing Accuracy

---

*Documento creado para implementación LLM - Fase 4 crítica del roadmap SDRAG*
