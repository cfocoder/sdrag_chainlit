# Fase 3.5: Capa de Explicación (Dify)

**Objetivo**: Integrar Dify como servicio de explicación post-cálculo, reemplazando OpenRouter.

**Prioridad**: CRÍTICA - Componente central de la arquitectura SDRAG.

---

## Prerrequisitos

### Fases previas requeridas

- [x] Fase 0: Infraestructura verificada
- [x] Fase 3: RAG Documental (para `hybrid_search()` usado en flujo completo)

### Servicios que deben estar operativos

Ejecutar antes de comenzar:

```bash
# Verificar Dify
curl -s http://100.110.109.43:80/health
# o
curl -I http://100.110.109.43:80
```

- [ ] Dify: `http://100.110.109.43:80` - Capa de explicación
- [ ] OpenRouter API Key configurada (fallback)

### Estructura de directorios

```bash
# Ya debería existir de Fase 3
ls services/  # Debe existir
```

---

## Principios Fundamentales

**Dify en SDRAG:**

- ❌ NO clasifica consultas (responsabilidad de n8n)
- ❌ NO genera SQL (responsabilidad de Cube Core)
- ❌ NO modifica datos numéricos (inmutables)
- ✅ SÍ genera explicaciones en lenguaje natural
- ✅ SÍ permite versionado de prompts
- ✅ SÍ habilita métricas de consistencia

**Flujo:**

```
Chainlit → n8n → Clasificación (3 rutas)
    ↓
    ├─ Cube Core (datos numéricos - ruta semántica)
    ├─ Weaviate (chunks documentales - ruta documental)
    └─ Cube Core + Weaviate (ruta híbrida)
    ↓
    [DATOS VALIDADOS + CONTEXTO DOCUMENTAL]
    ↓
    Dify API (explicación post-cálculo)
    ↓
    Explicación en español con trazabilidad
    ↓
    Chainlit
```

---

## Prerrequisitos

### Verificar Dify en Mac Mini

```bash
# SSH a macmini
ssh macmini

# Verificar contenedor Dify
docker ps | grep dify

# Verificar API disponible
curl http://localhost:80/v1/health
```

### Crear Aplicación en Dify

1. Acceder a Dify UI: `http://100.110.109.43:80`
2. Crear nueva aplicación tipo "Chat"
3. Nombre: `SDRAG FP&A Explainer`
4. Configurar prompt del sistema (ver Tarea 3.5.2)
5. Obtener API Key de la aplicación

---

## Tarea 3.5.1: Verificar Dify Operativo

### Descripción

Confirmar que Dify está corriendo y accesible desde Chainlit.

### Verificación desde cfocoder3 (donde corre Chainlit)

```bash
ssh cfocoder3

# Test de conectividad
curl http://100.110.109.43:80/v1/health

# Debe retornar algo como:
# {"status": "ok"}
```

### ✅ Criterios de Completitud

**Testing desde cfocoder3:**
```bash
ssh cfocoder3
curl -v http://100.110.109.43:80/v1/health
# Debe retornar HTTP 200 + {"status": "ok"}
```

**Verificación:**
- [ ] Respuesta en <500ms
- [ ] Sin errores de timeout
- [ ] Mac Mini alcanzable vía Tailscale

---

## Tarea 3.5.2: Crear Aplicación en Dify

### Descripción

Configurar la aplicación Dify con el prompt especializado para FP&A.

### Prompt del Sistema (System Prompt)

```
Eres un analista financiero experto explicando resultados de consultas FP&A.

REGLAS CRÍTICAS:
1. NUNCA inventes números. Solo usa los datos proporcionados en el contexto.
2. NUNCA modifiques los valores numéricos.
3. Explica en español de forma clara y profesional.
4. Si hay tablas, describe las tendencias y variaciones importantes.
5. Menciona el período fiscal cuando sea relevante.

FORMATO DE RESPUESTA:
- Respuesta concisa (2-4 oraciones para preguntas simples)
- Para análisis de tendencias, usa bullets
- Siempre menciona la fuente de los datos si está disponible

DATOS PROPORCIONADOS:
{{context}}

PREGUNTA DEL USUARIO:
{{query}}
```

### Variables de Entrada (Input Variables)

En la configuración de Dify:

- `query`: string - La pregunta del usuario
- `context`: string - Datos validados + SQL + metadata
- `data`: object - Datos numéricos en JSON

### Obtener API Key

1. En Dify UI → Aplicación → Settings → API Access
2. Copiar el API Key (formato: `app-xxxxxxxxxxxx`)
3. Guardar en variable de entorno `DIFY_API_KEY`

### ✅ Criterios de Completitud

**Configuración verificada:**
- [ ] Aplicación "SDRAG FP&A Explainer" visible en Dify UI
- [ ] Prompt del sistema contiene "NUNCA inventes números"
- [ ] Variables: `query`, `context`, `data` definidas
- [ ] API Key formato: `app-xxxxxxxxxxxx`

**Test del prompt:**
```bash
# Probar en Dify UI con datos mock
query: "¿Cuál fue el revenue de Q4 2024?"
data: {"revenue": 1234567, "period": "Q4 2024"}
# Respuesta debe citar el número exacto: 1,234,567
```

**Almacenar API Key:**
```bash
export DIFY_API_KEY="app-xxxxxxxxxxxx"
# Agregar a .env y Coolify
```

---

## Tarea 3.5.3: Cliente HTTP para Dify API

### Descripción

Implementar función async para llamar a Dify, similar a `call_openrouter()`.

### Archivo a modificar

`app.py` - Agregar después de la función `call_openrouter()`

### Código de referencia

```python
import httpx
import os
import time
import logging

logger = logging.getLogger(__name__)

DIFY_API_URL = os.getenv("DIFY_API_URL", "http://100.110.109.43:80/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")

async def call_dify(
    query: str,
    data: dict,
    sql: str = "",
    context: str = ""
) -> dict:
    """
    Envía datos validados a Dify para generar explicación.

    Args:
        query: Pregunta original del usuario
        data: Datos numéricos validados (de Cube Core o mock)
        sql: SQL generado (para trazabilidad)
        context: Contexto adicional (chunks de Weaviate)

    Returns:
        dict con 'explanation' y 'latency_ms'
    """
    if not DIFY_API_KEY:
        logger.warning("DIFY_API_KEY no configurada, usando fallback")
        return await _fallback_to_openrouter(query, data)

    start_time = time.time()

    # Construir contexto completo
    full_context = f"""
DATOS VALIDADOS:
{_format_data_for_prompt(data)}

SQL EJECUTADO:
{sql if sql else "N/A"}

CONTEXTO DOCUMENTAL (Weaviate):
{context if context else "N/A"}
"""

    payload = {
        "inputs": {
            "query": query,
            "context": full_context
        },
        "response_mode": "blocking",
        "user": "chainlit-sdrag"
    }

    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{DIFY_API_URL}/chat-messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            result = response.json()
            latency_ms = (time.time() - start_time) * 1000

            return {
                "explanation": result.get("answer", "Sin respuesta de Dify"),
                "latency_ms": latency_ms,
                "source": "dify"
            }

    except httpx.HTTPError as e:
        logger.error(f"Error llamando Dify: {e}")
        return await _fallback_to_openrouter(query, data)

    except Exception as e:
        logger.error(f"Error inesperado con Dify: {e}")
        return await _fallback_to_openrouter(query, data)


def _format_data_for_prompt(data: dict) -> str:
    """Formatea datos para incluir en el prompt"""
    if not data:
        return "No hay datos disponibles"

    lines = []
    for key, value in data.items():
        if isinstance(value, (int, float)):
            # Formatear números con separadores
            formatted = f"${value:,.2f}" if "revenue" in key.lower() or "income" in key.lower() else f"{value:,.2f}"
            lines.append(f"- {key}: {formatted}")
        else:
            lines.append(f"- {key}: {value}")

    return "\n".join(lines)


async def _fallback_to_openrouter(query: str, data: dict) -> dict:
    """Fallback a OpenRouter si Dify falla"""
    logger.info("Usando fallback a OpenRouter")
    start_time = time.time()

    # Usar la función existente call_openrouter
    prompt = f"""
Explica los siguientes datos financieros en español:

Datos: {data}

Pregunta: {query}

Responde de forma concisa (2-3 oraciones).
"""
    explanation = await call_openrouter(prompt)
    latency_ms = (time.time() - start_time) * 1000

    return {
        "explanation": explanation,
        "latency_ms": latency_ms,
        "source": "openrouter_fallback"
    }
```

### Variables de entorno

```bash
DIFY_API_URL=http://100.110.109.43:80/v1
DIFY_API_KEY=app-xxxxxxxxxxxx
```

### ✅ Criterios de Completitud

**Testing:**
```bash
pytest tests/test_dify_client.py::test_call_dify -v
pytest tests/test_dify_client.py::test_dify_fallback -v
```

**Tests específicos:**
- [ ] Dify retorna explicación válida
- [ ] Timeout después de 30s
- [ ] Fallback activa si Dify falla
- [ ] Latency_ms registrada correctamente

**Verificación manual:**
```python
# En chainlit, ejecutar:
result = await call_dify(
    query="¿Cuál fue el revenue?",
    data={"revenue": 1200000},
    sql="SELECT SUM(revenue) FROM facts"
)
assert "revenue" in result["explanation"].lower()
assert result["latency_ms"] > 0
assert result["source"] in ["dify", "openrouter_fallback"]
```

**Benchmark:**
- [ ] Latencia Dify P50 <1s
- [ ] Latencia Dify P95 <3s

---

## Tarea 3.5.4: Enviar Datos Deterministas a Dify

### Descripción

Integrar `call_dify()` en el flujo existente de `main()`.

### Archivo a modificar

`app.py` - Dentro del handler `@cl.on_message`

### Código de referencia

````python
@cl.on_message
async def main(message: cl.Message):
    query = message.content
    start_time = time.time()

    # Paso 1: Clasificación
    async with cl.Step(name="Clasificación", type="tool") as step:
        step.input = query
        classification = classify_query(query)
        step.output = f"Ruta: {classification['route']}, Métrica: {classification.get('metric', 'N/A')}"

    # Paso 2: Generación SQL (o búsqueda documental)
    async with cl.Step(name="SQL", type="tool") as step:
        if classification["route"] == "semantic":
            sql = generate_mock_sql(classification["metric"], classification["period"])
            step.output = f"```sql\n{sql}\n```"
        else:
            sql = "-- Consulta documental, sin SQL"
            step.output = "Ruta documental - búsqueda en Weaviate"

    # Paso 3: Obtención de datos
    async with cl.Step(name="Datos", type="tool") as step:
        if classification["route"] == "semantic":
            data = get_mock_data(classification["metric"], classification["period"])
            step.output = f"```json\n{data}\n```"
        else:
            # TODO: Integrar con búsqueda Weaviate (Fase 3)
            data = {"context": "Datos de documentos"}

    # Paso 4: Explicación con Dify
    async with cl.Step(name="Explicación (Dify)", type="llm") as step:
        step.input = f"Query: {query}\nDatos: {data}"

        # Llamar a Dify en lugar de OpenRouter
        result = await call_dify(
            query=query,
            data=data,
            sql=sql,
            context=""  # Agregar chunks de Weaviate si es documental
        )

        explanation = result["explanation"]
        latency = result["latency_ms"]
        source = result["source"]

        step.output = f"[{source}, {latency:.0f}ms]\n\n{explanation}"

    # Respuesta final
    total_time = (time.time() - start_time) * 1000
    await cl.Message(
        content=f"{explanation}\n\n---\n*Tiempo total: {total_time:.0f}ms*"
    ).send()
````

### ✅ Criterios de Completitud

**Testing end-to-end:**
```bash
chainlit run app.py
# Consulta: "¿Cuál fue el revenue de Q4 2024?"
```

**Verificar en UI:**
- [ ] cl.Step "Explicación (Dify)" visible
- [ ] Latencia mostrada en output
- [ ] Fuente (dify/openrouter_fallback) visible
- [ ] Tiempo total calculado correctamente

**Validación de datos:**
- [ ] Datos numéricos pasan correctamente a Dify
- [ ] SQL incluido en contexto
- [ ] Explicación coherente con los datos

**Benchmark:**
- [ ] Flujo completo <3s (P50)
- [ ] No hay errores en logs

---

## Tarea 3.5.5: Recibir Explicación

### Descripción

Parsear respuesta de Dify y manejar casos de error.

### Ya incluido en Tarea 3.5.3

La función `call_dify()` ya maneja:

- Parsing de `response.json()["answer"]`
- Errores HTTP
- Timeout
- Fallback

### Criterios de aceptación

- [ ] Explicación extraída correctamente
- [ ] Errores manejados con fallback
- [ ] No hay crashes por respuestas inesperadas

---

## Tarea 3.5.6: Renderizar en cl.Step

### Descripción

Mostrar explicación de Dify con formato apropiado en la UI.

### Ya incluido en Tarea 3.5.4

El cl.Step "Explicación (Dify)" muestra:

- Fuente (dify o fallback)
- Latencia en ms
- Texto de explicación

### Formato adicional (opcional)

```python
# Si la explicación incluye bullets, formatear como lista
if "•" in explanation or "-" in explanation:
    # Ya está formateado
    formatted = explanation
else:
    # Agregar formato si es texto plano largo
    formatted = explanation

step.output = f"""
**Fuente:** {source}
**Latencia:** {latency:.0f}ms

{formatted}
"""
```

### Criterios de aceptación

- [ ] Explicación legible en UI
- [ ] Metadata visible (fuente, latencia)
- [ ] Formato markdown correcto

---

## Tarea 3.5.7: Fallback a OpenRouter

### Descripción

Si Dify no está disponible, usar OpenRouter automáticamente.

### Ya incluido en Tarea 3.5.3

La función `_fallback_to_openrouter()` se activa cuando:

- `DIFY_API_KEY` no está configurada
- Error HTTP al llamar Dify
- Timeout de Dify

### Logging

```python
# En _fallback_to_openrouter:
logger.warning(f"Dify no disponible, usando OpenRouter fallback")
```

### Criterios de aceptación

- [ ] Fallback automático sin intervención
- [ ] Log indica que se usó fallback
- [ ] Response incluye `source: "openrouter_fallback"`
- [ ] Usuario no nota diferencia (solo en logs)

---

## Tarea 3.5.8: Medir Latencia Dify vs OpenRouter

### Descripción

Registrar latencias para comparar performance.

### Implementación

```python
import logging

# Crear logger específico para métricas
metrics_logger = logging.getLogger("sdrag.metrics")
metrics_logger.setLevel(logging.INFO)

# En call_dify(), después de obtener resultado:
metrics_logger.info(f"LLM_CALL|source={source}|latency_ms={latency_ms:.0f}|query_len={len(query)}")
```

### Análisis posterior

```bash
# Grep de métricas en logs
grep "LLM_CALL" /var/log/chainlit.log | \
  awk -F'|' '{print $2, $3}' | \
  sort | uniq -c
```

### Métricas a recolectar

| Métrica                 | Objetivo | Cómo medir                        |
| ----------------------- | -------- | --------------------------------- |
| Latencia p50 Dify       | <1500ms  | Percentil 50 de `latency_ms`      |
| Latencia p95 Dify       | <3000ms  | Percentil 95                      |
| Tasa de fallback        | <5%      | % de `source=openrouter_fallback` |
| Explanation Consistency | -        | BLEU entre respuestas repetidas   |

### Criterios de aceptación

- [ ] Latencias registradas en logs
- [ ] Fuente identificable en cada llamada
- [ ] Datos suficientes para análisis de tesis

---

## Integración Final

### Flujo completo con Dify (3 rutas)

```python
# En app.py - main()

@cl.on_message
async def main(message: cl.Message):
    query = message.content

    # 1. Clasificación (3 rutas)
    classification = classify_query(query)

    # 2. Obtener datos según ruta
    sql = ""
    data = {}
    context = ""

    if classification["route"] == "semantic":
        # Ruta semántica: Cube Core → DuckDB
        sql = generate_mock_sql(...)  # Futuro: Cube Core
        data = get_mock_data(...)      # Futuro: DuckDB

    elif classification["route"] == "documental":
        # Ruta documental: Weaviate → Chunks
        embedding = await generate_embedding(query)
        chunks = await hybrid_search(query, embedding)
        data = {"chunks": len(chunks)}
        context = "\n\n".join([c["content"] for c in chunks])

    elif classification["route"] == "hybrid":
        # Ruta híbrida: Cube Core + Weaviate
        sql = generate_mock_sql(...)
        data = get_mock_data(...)
        embedding = await generate_embedding(query)
        chunks = await hybrid_search(query, embedding)
        context = "\n\n".join([c["content"] for c in chunks])

    # 3. Explicación con Dify
    result = await call_dify(query, data, sql, context)

    # 4. Respuesta
    await cl.Message(content=result["explanation"]).send()
```

---

## Tarea 3.5.9: Tests de Fase 3.5

### Descripción

Implementar tests para validar el cliente Dify y el mecanismo de fallback.

### Archivo de test

`tests/test_dify_client.py`

### Tests requeridos

```python
# tests/test_dify_client.py

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestCallDify:
    """Tests de la función call_dify()."""

    @pytest.mark.asyncio
    async def test_successful_dify_call(
        self,
        mock_env_vars,
        mock_dify_api,
        sample_fpa_query,
        sample_fpa_data,
        sample_sql
    ):
        """Llamada exitosa a Dify retorna explicación."""
        from app import call_dify  # Ajustar import según estructura

        result = await call_dify(
            query=sample_fpa_query,
            data=sample_fpa_data,
            sql=sample_sql
        )

        assert "explanation" in result
        assert "latency_ms" in result
        assert result["source"] == "dify"
        assert result["latency_ms"] > 0

    @pytest.mark.asyncio
    async def test_dify_timeout_triggers_fallback(self, mock_env_vars):
        """Timeout de Dify activa fallback a OpenRouter."""
        import httpx

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = httpx.TimeoutException("timeout")
            mock_client.return_value.__aenter__.return_value = mock_instance

            from app import call_dify
            result = await call_dify(query="test", data={})

            assert result["source"] == "openrouter_fallback"

    @pytest.mark.asyncio
    async def test_missing_api_key_uses_fallback(self, monkeypatch):
        """Sin DIFY_API_KEY usa fallback automáticamente."""
        monkeypatch.delenv("DIFY_API_KEY", raising=False)
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        # Mock OpenRouter response
        with patch("app.call_openrouter", new_callable=AsyncMock) as mock_or:
            mock_or.return_value = "Respuesta de fallback"

            from app import call_dify
            result = await call_dify(query="test", data={})

            assert result["source"] == "openrouter_fallback"

    @pytest.mark.asyncio
    async def test_latency_is_measured(
        self,
        mock_env_vars,
        mock_dify_api
    ):
        """Latencia se mide correctamente."""
        from app import call_dify

        result = await call_dify(query="test", data={"revenue": 1000})

        assert "latency_ms" in result
        assert isinstance(result["latency_ms"], (int, float))
        assert result["latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_dify_receives_correct_payload(
        self,
        mock_env_vars,
        mock_dify_api,
        sample_fpa_query,
        sample_fpa_data
    ):
        """Dify recibe payload con query y datos."""
        from app import call_dify

        await call_dify(
            query=sample_fpa_query,
            data=sample_fpa_data,
            sql="SELECT * FROM test"
        )

        # Verificar que se llamó con el payload correcto
        call_args = mock_dify_api.post.call_args
        payload = call_args.kwargs.get("json", call_args[1].get("json"))

        assert "inputs" in payload
        assert payload["inputs"]["query"] == sample_fpa_query


class TestFormatDataForPrompt:
    """Tests de formateo de datos para Dify."""

    def test_formats_currency_values(self):
        """Valores de revenue se formatean con $."""
        from app import _format_data_for_prompt

        data = {"revenue": 1200000.50, "period": "Q4 2024"}
        formatted = _format_data_for_prompt(data)

        assert "$" in formatted
        assert "1,200,000" in formatted

    def test_handles_empty_data(self):
        """Datos vacíos retornan mensaje apropiado."""
        from app import _format_data_for_prompt

        formatted = _format_data_for_prompt({})
        assert "No hay datos" in formatted or formatted == ""

    def test_handles_nested_structures(self):
        """Estructuras anidadas se manejan sin error."""
        from app import _format_data_for_prompt

        data = {"metrics": {"revenue": 100}, "period": "Q4"}
        formatted = _format_data_for_prompt(data)

        assert formatted is not None
```

### Ejecutar tests de Fase 3.5

```bash
# Tests del cliente Dify
pytest tests/test_dify_client.py -v

# Con coverage
pytest tests/test_dify_client.py --cov=app --cov-report=term-missing
```

### Criterios de aceptación

- [ ] `test_successful_dify_call` pasa
- [ ] `test_dify_timeout_triggers_fallback` pasa
- [ ] `test_missing_api_key_uses_fallback` pasa
- [ ] `test_latency_is_measured` pasa
- [ ] Coverage >80% en `call_dify()` y `_format_data_for_prompt()`

---

## Checklist Final Fase 3.5

- [ ] 3.5.1 Dify operativo y accesible desde cfocoder3
- [ ] 3.5.2 Aplicación "SDRAG FP&A Explainer" configurada
- [ ] 3.5.3 `call_dify()` implementada con timeout y logging
- [ ] 3.5.4 Datos enviados correctamente a Dify
- [ ] 3.5.5 Explicación parseada sin errores
- [ ] 3.5.6 cl.Step muestra explicación formateada
- [ ] 3.5.7 Fallback a OpenRouter funciona
- [ ] 3.5.8 Latencias registradas para análisis
- [ ] 3.5.9 Tests automatizados pasan (>80% coverage)
- [ ] Variable `DIFY_API_KEY` configurada en Coolify

---

## Métricas de Éxito (Tesis)

| Métrica                     | Objetivo                            | Medición                      |
| --------------------------- | ----------------------------------- | ----------------------------- |
| **Explanation Consistency** | Alta                                | BLEU/ROUGE entre ejecuciones  |
| **Latency Overhead**        | <500ms vs OpenRouter                | Comparar p50                  |
| **Determinism**             | Mismo input → mismo output numérico | 100% (Dify no modifica datos) |

---

## Siguiente Fase

Continuar con [Fase 4: n8n Router](fase-4-n8n-router.md).
