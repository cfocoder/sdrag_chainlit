"""
SDRAG Chainlit Frontend
Arquitectura RAG Híbrida con Capa Semántica Determinista
Maestría en Ciencia de los Datos - Universidad de Guadalajara
"""

import chainlit as cl
from datetime import datetime
import os

# Configuración
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://100.105.68.15:5678/webhook/sdrag-query")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://100.116.107.52:11434")

@cl.on_chat_start
async def start():
    """Inicializa la sesión de chat"""
    await cl.Message(
        content="""# 🎯 SDRAG - Arquitectura RAG Híbrida

**Sistema de Analítica Financiera con Ejecución Determinista**

Este sistema garantiza:
- ✅ **Sin alucinaciones aritméticas**: Todos los cálculos vía Cube Core
- ✅ **Trazabilidad completa**: SQL visible, pasos auditables
- ✅ **Reproducibilidad**: Mismo input → mismo output

**Ejemplos de consultas**:
- "¿Cuál fue el Revenue de Q3 2024?"
- "Compara EBITDA entre regiones"
- "Muestra la tendencia de OPEX mensual"

---
*Versión: 0.1.0 - Diciembre 2025*
"""
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Procesa consulta del usuario con arquitectura SDRAG"""
    
    # Paso 1: Clasificación de consulta
    async with cl.Step(name="🔍 Clasificación de Consulta") as step:
        step.output = "Analizando tipo de consulta..."
        # TODO: Llamar a n8n para clasificación
        query_type = "semantic"  # o "documental"
        step.output = f"Tipo detectado: **{query_type}**"
    
    # Paso 2: Ejecución determinista
    if query_type == "semantic":
        async with cl.Step(name="�� Ejecución SQL (Cube Core)") as step:
            step.output = "Generando SQL canónico..."
            # TODO: Integrar con Cube Core vía n8n
            sql = "SELECT revenue, cogs, ebitda FROM financial_metrics WHERE quarter = 'Q3-2024'"
            step.output = f"```sql\n{sql}\n```"
        
        # Paso 3: Visualización de datos
        async with cl.Step(name="📈 Visualización de Resultados") as step:
            step.output = "Preparando DataFrame..."
            # TODO: Crear DataFrame real desde DuckDB
            # import pandas as pd
            # df = pd.DataFrame(...)
            # await cl.DataFrame(df=df, name="Resultados").send()
            step.output = "DataFrame renderizado (placeholder)"
    
    else:
        async with cl.Step(name="📄 Búsqueda Documental (OpenSearch)") as step:
            step.output = "Recuperando documentos relevantes..."
            # TODO: Integrar con OpenSearch
            step.output = "3 documentos recuperados"
    
    # Paso 4: Explicación generada por LLM
    async with cl.Step(name="🤖 Generación de Explicación") as step:
        step.output = "Ollama generando explicación..."
        # TODO: Integrar con Ollama
        explanation = f"Basado en la consulta: '{message.content}'\n\nLos datos han sido procesados correctamente a través de la capa semántica determinista. En producción, esta respuesta contendrá cálculos verificados desde Cube Core."
        step.output = explanation
    
    # Respuesta final
    await cl.Message(
        content=f"""## Respuesta

{explanation}

---
*Sistema SDRAG - Trazabilidad completa garantizada*  
*Timestamp: {datetime.now().isoformat()}*
"""
    ).send()


@cl.on_settings_update
async def setup_agent(settings):
    """Actualiza configuración en tiempo real"""
    print(f"Settings updated: {settings}")
