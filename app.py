"""
SDRAG Chainlit Frontend
Arquitectura RAG Híbrida con Capa Semántica Determinista
Maestría en Ciencia de los Datos - Universidad de Guadalajara
"""

import chainlit as cl
from datetime import datetime
import os
import httpx

# Configuración
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://100.105.68.15:5678/webhook/sdrag-query")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/devstral-2512:free")

async def call_openrouter(prompt: str) -> str:
    """Llama a OpenRouter API para generar explicaciones"""
    if not OPENROUTER_API_KEY:
        return "⚠️ OpenRouter API Key no configurada"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://chainlit.sdrag.com",
                    "X-Title": "SDRAG Chainlit Frontend",
                },
                json={
                    "model": OPENROUTER_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Eres un asistente financiero experto en analítica FP&A. Tu objetivo es explicar resultados de datos de manera clara y concisa, sin inventar números. Solo explica los datos proporcionados."
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
    # No enviamos mensaje aquí, chainlit.md se muestra automáticamente
    pass


@cl.on_message
async def main(message: cl.Message):
    """Procesa mensajes del usuario con OpenRouter"""
    
    # Mostrar indicador de procesamiento
    msg = cl.Message(content="")
    await msg.send()
    
    # Llamar a OpenRouter
    prompt = f"""Eres un asistente útil y amigable. Responde de manera clara y concisa.

Usuario: {message.content}"""
    
    response = await call_openrouter(prompt)
    
    # Actualizar mensaje con respuesta
    msg.content = response
    await msg.update()


@cl.on_settings_update
async def setup_agent(settings):
    """Actualiza configuración en tiempo real"""
    print(f"Settings updated: {settings}")
