# Fase 0: Verificación de Infraestructura

**Objetivo**: Confirmar que todos los servicios del cluster están operativos antes de iniciar cualquier fase de desarrollo.

**Prioridad**: CRÍTICA - Ejecutar antes de cualquier otra fase.

---

## Contexto

El proyecto SDRAG depende de múltiples servicios distribuidos en el cluster Tailscale. Esta fase asegura que todos los servicios estén disponibles y correctamente configurados.

**Arquitectura simplificada (Protocolo v7):**
- **Weaviate** es la única base de datos vectorial
- **3 rutas de clasificación**: Semántica, Documental, Híbrida
- **Sin Neo4j/OpenSearch/Qdrant** - simplificación deliberada

**Cluster Tailscale:**

| Servicio | Host | IP Tailscale | Puerto | Rol |
|----------|------|--------------|--------|-----|
| Chainlit | cfocoder3 | 100.105.68.15 | 8001 | Frontend UI |
| n8n | cfocoder3 | 100.105.68.15 | 5678 | Router determinista |
| Dify | macmini | 100.110.109.43 | 80 | Capa de explicación |
| **Weaviate** | macmini | 100.110.109.43 | 8080 | **Única base vectorial** |
| MinIO | macmini | 100.110.109.43 | 9000 | Object storage (DuckLake) |
| Cube Core | vostro | 100.116.107.52 | 4000 | Capa semántica SQL |
| Ollama | vostro | 100.116.107.52 | 11434 | Embeddings e inferencia |

---

## Tarea 0.1: Verificar Conectividad Tailscale

### Descripción
Confirmar que todas las máquinas del cluster son accesibles.

### Verificación
```bash
# Desde tu máquina local (vostro)
ping -c 1 100.105.68.15  # cfocoder3
ping -c 1 100.110.109.43  # macmini

# O usar SSH directo
ssh cfocoder3 'echo "cfocoder3 OK"'
ssh macmini 'echo "macmini OK"'
```

### Criterios de aceptación
- [ ] cfocoder3 (100.105.68.15) responde
- [ ] macmini (100.110.109.43) responde
- [ ] vostro (100.116.107.52) responde

---

## Tarea 0.2: Verificar Weaviate

### Descripción
Confirmar que Weaviate está corriendo como única base de datos vectorial.

### Verificación
```bash
# Readiness check
curl -s http://100.110.109.43:8080/v1/.well-known/ready | jq .

# Respuesta esperada:
# {}  (vacío significa ready)

# Listar colecciones (puede estar vacío inicialmente)
curl -s http://100.110.109.43:8080/v1/schema | jq '.classes[].class'

# Verificar versión
curl -s http://100.110.109.43:8080/v1/meta | jq '.version'
```

### Si Weaviate no está corriendo
```bash
ssh macmini
docker ps | grep weaviate

# Si no está, iniciar:
docker start weaviate  # o el nombre del contenedor

# O si usas docker-compose:
cd /path/to/weaviate
docker compose up -d
```

### Criterios de aceptación
- [ ] Weaviate responde en puerto 8080
- [ ] Endpoint /v1/.well-known/ready retorna OK
- [ ] API de schema accesible

---

## Tarea 0.3: Verificar Dify

### Descripción
Confirmar que Dify está corriendo como capa de explicación.

### Verificación
```bash
# Health check
curl -I http://100.110.109.43:80

# Verificar contenedores Dify (son varios)
ssh macmini
docker ps | grep dify
```

### Si Dify no está corriendo
```bash
ssh macmini
cd /path/to/dify  # Ubicación de docker-compose
docker compose up -d
```

### Criterios de aceptación
- [ ] Dify responde en puerto 80
- [ ] UI accesible en http://100.110.109.43:80
- [ ] API /v1 disponible

---

## Tarea 0.4: Verificar Ollama

### Descripción
Confirmar que Ollama está corriendo con el modelo de embeddings.

### Verificación
```bash
# Listar modelos disponibles
curl -s http://100.116.107.52:11434/api/tags | jq '.models[].name'

# Verificar nomic-embed-text específicamente
curl -s http://100.116.107.52:11434/api/tags | jq '.models[] | select(.name | contains("nomic"))'

# Test de embedding (debe retornar 768 dimensiones)
curl -X POST http://100.116.107.52:11434/api/embeddings \
  -d '{"model": "nomic-embed-text", "prompt": "test"}' | jq '.embedding | length'
```

### Si nomic-embed-text no está instalado
```bash
ssh vostro
ollama pull nomic-embed-text
```

### Criterios de aceptación
- [ ] Ollama responde en puerto 11434
- [ ] Modelo nomic-embed-text disponible
- [ ] Embeddings de 768 dimensiones

---

## Tarea 0.5: Verificar Cube Core

### Descripción
Confirmar que Cube Core está corriendo como capa semántica (CRÍTICO para Fase 5).

### Verificación
```bash
# Health check
curl -s http://100.116.107.52:4000/readyz
# Esperado: {"health":"ok"}

# Verificar acceso desde cfocoder3 (donde corre Chainlit)
ssh cfocoder3
curl -s http://100.116.107.52:4000/readyz

# Verificar meta API (métricas disponibles)
curl -s http://100.116.107.52:4000/cubejs-api/v1/meta | jq '.cubes[].name'
# Esperado: Lista de cubos definidos (puede estar vacío inicialmente)
```

### Si Cube Core no está corriendo
```bash
ssh vostro

# Verificar si existe contenedor
docker ps -a | grep cube

# Si existe pero está detenido
docker start cube

# Si no existe, ver roadmap/fase-5-cube-core.md para instalación
```

### Criterios de aceptación
- [ ] Cube Core responde en puerto 4000
- [ ] Endpoint /readyz retorna OK
- [ ] Meta API accesible
- [ ] Accesible desde cfocoder3 (Chainlit) vía Tailscale

---

## Tarea 0.6: Verificar n8n

### Descripción
Confirmar que n8n está corriendo como router determinista (CRÍTICO para Fase 4).

### Verificación
```bash
# UI de n8n accesible
curl -I http://100.105.68.15:5678
# Esperado: HTTP/1.1 200 OK

# Verificar desde vostro (donde corre Chainlit)
# n8n debe ser accesible para recibir llamadas
curl -I http://100.105.68.15:5678

# Listar workflows activos (si tienes credenciales)
# curl -u user:password http://100.105.68.15:5678/rest/workflows
```

### Si n8n no está corriendo
```bash
ssh cfocoder3

# Verificar contenedor
docker ps | grep n8n

# Si está detenido
docker start n8n

# Ver logs
docker logs n8n --tail 50
```

### Criterios de aceptación
- [ ] n8n UI accesible en puerto 5678
- [ ] Accesible desde otros nodos vía Tailscale
- [ ] Sin errores en logs
- [ ] Listo para crear webhooks (Fase 4)

---

## Tarea 0.7: Crear Estructura de Directorios

### Descripción
Crear carpetas necesarias para el proyecto si no existen.

### Verificación y Creación
```bash
# Desde el directorio del proyecto
cd /home/hectorsa/Documents/sdrag_chainlit

# Crear estructura
mkdir -p services scripts tests
touch services/__init__.py

# Verificar
ls -la services/ scripts/ tests/
```

### Estructura esperada
```
sdrag_chainlit/
├── app.py
├── services/           # Clientes de servicios externos
│   ├── __init__.py
│   ├── docling_extractor.py
│   ├── chunker.py
│   ├── embeddings.py
│   ├── weaviate_client.py
│   └── dify_client.py
├── scripts/            # Scripts de utilidad
│   └── ingest_document.py
├── tests/              # Tests automatizados
│   ├── conftest.py
│   └── test_*.py
└── roadmap/            # Documentación de fases
```

### Criterios de aceptación
- [ ] Directorio `services/` existe
- [ ] Directorio `scripts/` existe
- [ ] Directorio `tests/` existe

---

## Tarea 0.7: Verificar Variables de Entorno

### Descripción
Confirmar que las variables de entorno están configuradas.

### Variables Requeridas

```bash
# Crear archivo .env si no existe
cat > .env << 'EOF'
# Autenticación Chainlit
CHAINLIT_AUTH_SECRET=tu-clave-secreta-larga
CHAINLIT_USER=hector
CHAINLIT_PASSWORD=sdrag2025

# Dify (Fase 3.5)
DIFY_API_URL=http://100.110.109.43:80/v1
DIFY_API_KEY=app-xxx

# OpenRouter (Fallback)
OPENROUTER_API_KEY=tu-api-key
OPENROUTER_MODEL=mistralai/devstral-2512:free

# Weaviate (Fase 3) - Única base vectorial
WEAVIATE_URL=http://100.110.109.43:8080

# Ollama (Fase 3)
OLLAMA_BASE_URL=http://100.116.107.52:11434
EMBEDDING_MODEL=nomic-embed-text

# n8n (Fase 4)
N8N_WEBHOOK_URL=http://100.105.68.15:5678/webhook/sdrag-query

# Cube Core (Fase 5)
CUBE_API_URL=http://100.116.107.52:4000
EOF
```

### Verificación
```bash
# Cargar y verificar
source .env
echo "DIFY: $DIFY_API_URL"
echo "Weaviate: $WEAVIATE_URL"
echo "Ollama: $OLLAMA_BASE_URL"
```

### Criterios de aceptación
- [ ] Archivo .env existe
- [ ] Variables de entorno cargables
- [ ] API keys configuradas (obtener de cada servicio)

---

## Script de Verificación Completa

Ejecutar este script para verificar todo de una vez:

```bash
#!/bin/bash
# scripts/verify_infrastructure.sh

echo "=== Verificación de Infraestructura SDRAG (Protocolo v7) ==="
echo ""
echo "Arquitectura simplificada: Weaviate como única base vectorial"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

check_service() {
    local name=$1
    local url=$2
    if curl -s --connect-timeout 5 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        return 0
    else
        echo -e "${RED}✗${NC} $name - No responde en $url"
        return 1
    fi
}

echo "Verificando servicios..."
echo ""

check_service "Weaviate" "http://100.110.109.43:8080/v1/.well-known/ready"
check_service "Dify" "http://100.110.109.43:80"
check_service "Ollama" "http://100.116.107.52:11434/api/tags"
check_service "n8n" "http://100.105.68.15:5678"

echo ""
echo "Verificando modelo de embeddings..."
if curl -s http://100.116.107.52:11434/api/tags | grep -q "nomic-embed-text"; then
    echo -e "${GREEN}✓${NC} nomic-embed-text disponible"
else
    echo -e "${RED}✗${NC} nomic-embed-text NO encontrado - ejecutar: ollama pull nomic-embed-text"
fi

echo ""
echo "Verificando estructura de directorios..."
for dir in services scripts tests; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir/"
    else
        echo -e "${RED}✗${NC} $dir/ - ejecutar: mkdir -p $dir"
    fi
done

echo ""
echo "=== Verificación completada ==="
```

### Ejecutar
```bash
chmod +x scripts/verify_infrastructure.sh
./scripts/verify_infrastructure.sh
```

---

## Checklist Final Fase 0

- [ ] 0.1 Conectividad Tailscale OK
- [ ] 0.2 Weaviate operativo (8080)
- [ ] 0.3 Dify operativo (80)
- [ ] 0.4 Ollama + nomic-embed-text (11434)
- [ ] 0.5 n8n operativo (5678) - opcional para Fases 3-3.5
- [ ] 0.6 Estructura de directorios creada
- [ ] 0.7 Variables de entorno configuradas

---

## Siguiente Fase

Una vez completada la Fase 0, continuar con [Fase 3: RAG Documental](fase-3-rag-documental.md).

**Nota**: Las Fases 1 y 2 ya están completadas (infraestructura base y trazabilidad cl.Step).
