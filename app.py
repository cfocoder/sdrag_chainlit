"""
SDRAG Chainlit Frontend
Arquitectura RAG Híbrida con Capa Semántica Determinista
Maestría en Ciencia de los Datos - Universidad de Guadalajara
"""

import chainlit as cl
import os
import httpx
import time
import re
import pandas as pd

# Configuración
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://100.105.68.15:5678/webhook/sdrag-query")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "e6368ea404601fb6ebbb3f6c8d074e7081b8efacac4d9694")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "gemini-flash")
API_BASE_URL = os.getenv("API_BASE_URL", "http://100.110.109.43:18789/v1")

# Usuarios autorizados
AUTHORIZED_USERS = {
    os.getenv("CHAINLIT_USER", "hector"): os.getenv("CHAINLIT_PASSWORD", "sdrag2025")
}

# =============================================================================
# DATOS MOCK - Métricas FP&A de ejemplo
# =============================================================================
MOCK_METRICS = {
    "revenue": {
        "Q1_2024": 980_000, "Q2_2024": 1_050_000, 
        "Q3_2024": 1_100_000, "Q4_2024": 1_234_567,
        "2024": 4_364_567, "2023": 3_890_000
    },
    "cogs": {
        "Q1_2024": 380_000, "Q2_2024": 400_000,
        "Q3_2024": 420_000, "Q4_2024": 450_000,
        "2024": 1_650_000, "2023": 1_520_000
    },
    "gross_margin": {
        "Q1_2024": 0.612, "Q2_2024": 0.619,
        "Q3_2024": 0.618, "Q4_2024": 0.635,
        "2024": 0.622, "2023": 0.609
    },
    "opex": {
        "Q1_2024": 280_000, "Q2_2024": 290_000,
        "Q3_2024": 295_000, "Q4_2024": 310_000,
        "2024": 1_175_000, "2023": 1_100_000
    },
    "ebitda": {
        "Q1_2024": 320_000, "Q2_2024": 360_000,
        "Q3_2024": 385_000, "Q4_2024": 474_567,
        "2024": 1_539_567, "2023": 1_270_000
    },
    "net_income": {
        "Q1_2024": 210_000, "Q2_2024": 245_000,
        "Q3_2024": 265_000, "Q4_2024": 320_000,
        "2024": 1_040_000, "2023": 870_000
    }
}

# Keywords para clasificación
SEMANTIC_KEYWORDS = {
    "revenue": ["revenue", "ventas", "ingresos", "sales", "facturación"],
    "cogs": ["cogs", "costo", "cost of goods", "costo de ventas"],
    "gross_margin": ["margen bruto", "gross margin", "margen"],
    "opex": ["opex", "gastos operativos", "operating expenses", "gastos"],
    "ebitda": ["ebitda", "utilidad operativa"],
    "net_income": ["net income", "utilidad neta", "ganancia", "profit"]
}

PERIOD_PATTERNS = {
    "Q1_2024": [r"q1.?2024", r"primer.?trimestre.?2024"],
    "Q2_2024": [r"q2.?2024", r"segundo.?trimestre.?2024"],
    "Q3_2024": [r"q3.?2024", r"tercer.?trimestre.?2024"],
    "Q4_2024": [r"q4.?2024", r"cuarto.?trimestre.?2024"],
    "2024": [r"\b2024\b"],
    "2023": [r"\b2023\b"]
}


def classify_query(query: str) -> dict:
    """Clasifica la consulta y extrae métrica y período"""
    query_lower = query.lower()
    
    detected_metric = None
    for metric, keywords in SEMANTIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                detected_metric = metric
                break
        if detected_metric:
            break
    
    # Detectar período (trimestres primero, luego año)
    detected_period = None
    
    # Primero buscar trimestres específicos
    for period in ["Q1_2024", "Q2_2024", "Q3_2024", "Q4_2024"]:
        for pattern in PERIOD_PATTERNS[period]:
            if re.search(pattern, query_lower):
                detected_period = period
                break
        if detected_period:
            break
    
    # Si no hay trimestre, buscar año
    if not detected_period:
        for period in ["2024", "2023"]:
            for pattern in PERIOD_PATTERNS[period]:
                if re.search(pattern, query_lower):
                    detected_period = period
                    break
            if detected_period:
                break
    
    # Default a 2024 si no se detectó período
    if not detected_period:
        detected_period = "2024"
    
    if detected_metric:
        route = "semantic"
        route_target = "Cube Core"
    else:
        route = "documental"
        route_target = "Weaviate"
    
    return {
        "route": route,
        "route_target": route_target,
        "metric": detected_metric,
        "period": detected_period,
        "is_financial": detected_metric is not None
    }


def generate_mock_sql(metric: str, period: str) -> str:
    """Genera SQL mock basado en la métrica y período"""
    metric_column = {
        "revenue": "SUM(revenue_amount)",
        "cogs": "SUM(cogs_amount)",
        "gross_margin": "AVG(gross_margin_pct)",
        "opex": "SUM(opex_amount)",
        "ebitda": "SUM(ebitda_amount)",
        "net_income": "SUM(net_income_amount)"
    }
    
    if "Q" in period:
        quarter = period.split("_")[0]
        year = period.split("_")[1]
        where_clause = f"WHERE fiscal_quarter = '{quarter}' AND fiscal_year = {year}"
    else:
        where_clause = f"WHERE fiscal_year = {period}"
    
    return f"""SELECT {metric_column.get(metric, 'value')} as {metric}
FROM financial_metrics
{where_clause}"""


def get_mock_data(metric: str, period: str) -> dict:
    """Obtiene datos mock para la métrica y período"""
    if metric and metric in MOCK_METRICS:
        value = MOCK_METRICS[metric].get(period, 0)
        return {
            "metric": metric,
            "period": period,
            "value": value,
            "formatted": f"${value:,.2f}" if metric != "gross_margin" else f"{value*100:.1f}%"
        }
    return None


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """Valida credenciales de usuario"""
    if username in AUTHORIZED_USERS and AUTHORIZED_USERS[username] == password:
        return cl.User(
            identifier=username,
            metadata={"role": "admin", "provider": "credentials"}
        )
    return None


async def call_openrouter(prompt: str) -> str:
    """Llama a OpenRouter API para generar explicaciones"""
    if not OPENROUTER_API_KEY:
        return "⚠️ OpenRouter API Key no configurada"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://chainlit.sdrag.com",
                    "X-Title": "SDRAG Chainlit Frontend (Powered by Frankie)",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Eres un asistente financiero experto en analítica FP&A. Explica los datos proporcionados de manera clara y concisa. NO inventes números, solo usa los datos que te proporcionan."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"❌ Error llamando a OpenRouter: {str(e)}"


@cl.on_chat_start
async def start():
    """Inicializa la sesión de chat"""
    user = cl.user_session.get("user")
    if user:
        await cl.Message(
            content=f"👋 ¡Hola **{user.identifier}**! Bienvenido a SDRAG Chat.\n\n"
                    f"Puedo ayudarte con consultas financieras FP&A. Prueba preguntas como:\n"
                    f"- *¿Cuál fue el revenue del Q4 2024?*\n"
                    f"- *¿Cuál es el EBITDA del 2024?*\n"
                    f"- *¿Cómo está el margen bruto del Q3 2024?*\n\n"
                    f"📊 *Modelo: {OPENROUTER_MODEL}*"
        ).send()


@cl.on_message
async def main(message: cl.Message):
    """Procesa mensajes con trazabilidad completa usando cl.Step"""
    
    query = message.content
    start_time = time.time()
    
    # PASO 1: Clasificación de consulta
    async with cl.Step(name="🔍 Clasificación", type="tool") as step_classify:
        step_classify.input = query
        classify_start = time.time()
        
        classification = classify_query(query)
        
        classify_time = time.time() - classify_start
        
        if classification["is_financial"]:
            step_classify.output = (
                f"**Tipo:** Consulta Semántica\n"
                f"**Ruta:** {classification['route_target']}\n"
                f"**Métrica detectada:** `{classification['metric']}`\n"
                f"**Período:** `{classification['period']}`\n"
                f"⏱️ *{classify_time*1000:.0f}ms*"
            )
        else:
            step_classify.output = (
                f"**Tipo:** Consulta General\n"
                f"**Ruta:** Chat directo (OpenRouter)\n"
                f"⏱️ *{classify_time*1000:.0f}ms*"
            )
    
    if classification["is_financial"]:
        metric = classification["metric"]
        period = classification["period"]
        
        # PASO 2: Generación de SQL
        async with cl.Step(name="📝 SQL Generado", type="tool") as step_sql:
            sql_start = time.time()
            sql = generate_mock_sql(metric, period)
            sql_time = time.time() - sql_start
            step_sql.input = f"Métrica: {metric}, Período: {period}"
            step_sql.output = f"```sql\n{sql}\n```\n⏱️ *{sql_time*1000:.0f}ms*"
        
        # PASO 3: Ejecución y recuperación de datos
        async with cl.Step(name="📊 Datos Recuperados", type="tool") as step_data:
            data_start = time.time()
            data = get_mock_data(metric, period)
            
            if data:
                df = pd.DataFrame([{
                    "Métrica": metric.replace("_", " ").title(),
                    "Período": period.replace("_", " "),
                    "Valor": data["formatted"]
                }])
                data_time = time.time() - data_start
                step_data.input = "Ejecutando query en DuckDB..."
                step_data.output = f"**Resultado:**\n\n{df.to_markdown(index=False)}\n\n⏱️ *{data_time*1000:.0f}ms*"
            else:
                step_data.output = "❌ No se encontraron datos"
        
        # PASO 4: Generación de explicación
        async with cl.Step(name="💬 Generando Explicación", type="llm") as step_explain:
            explain_start = time.time()
            
            prompt = f"""Basándote ÚNICAMENTE en estos datos, genera una explicación breve:

Consulta: {query}
Métrica: {metric.replace('_', ' ').title()}
Período: {period.replace('_', ' ')}
Valor: {data['formatted'] if data else 'N/A'}

Responde como analista FP&A. NO inventes datos adicionales."""
            
            step_explain.input = prompt
            explanation = await call_openrouter(prompt)
            explain_time = time.time() - explain_start
            step_explain.output = f"{explanation}\n\n⏱️ *{explain_time*1000:.0f}ms*"
        
        # Respuesta final
        total_time = time.time() - start_time
        final_response = f"""## 📊 Resultado

**{metric.replace('_', ' ').title()}** ({period.replace('_', ' ')}): **{data['formatted'] if data else 'N/A'}**

---

{explanation}

---
*⏱️ Tiempo total: {total_time:.2f}s | Ruta: {classification['route_target']}*"""
        
        await cl.Message(content=final_response).send()
    
    else:
        # Consulta general - Chat directo
        async with cl.Step(name="💬 Generando Respuesta", type="llm") as step_chat:
            chat_start = time.time()
            prompt = f"Responde de manera clara y concisa:\n\n{query}"
            step_chat.input = query
            response = await call_openrouter(prompt)
            chat_time = time.time() - chat_start
            step_chat.output = f"{response}\n\n⏱️ *{chat_time*1000:.0f}ms*"
        
        total_time = time.time() - start_time
        await cl.Message(content=f"{response}\n\n---\n*⏱️ Tiempo: {total_time:.2f}s*").send()
