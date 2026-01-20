#!/bin/bash
# Script de verificación de infraestructura SDRAG
# Ejecutar antes de cualquier fase de desarrollo
# Protocolo v7: Weaviate como única base de datos vectorial

echo "=== Verificación de Infraestructura SDRAG (Protocolo v7) ==="
echo ""
echo "Arquitectura simplificada: Weaviate como única base vectorial"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

check_service() {
    local name=$1
    local url=$2
    if curl -s --connect-timeout 5 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        return 0
    else
        echo -e "${RED}✗${NC} $name - No responde en $url"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

echo "Verificando conectividad Tailscale..."
echo ""

check_service "cfocoder3 (100.105.68.15)" "http://100.105.68.15:8001" || true
check_service "macmini (100.110.109.43)" "http://100.110.109.43:8080/v1/.well-known/ready" || true
check_service "vostro (100.116.107.52)" "http://100.116.107.52:11434/api/tags" || true

echo ""
echo "Verificando servicios principales..."
echo ""

check_service "Weaviate (8080)" "http://100.110.109.43:8080/v1/.well-known/ready"
check_service "Dify (80)" "http://100.110.109.43:80"
check_service "Ollama (11434)" "http://100.116.107.52:11434/api/tags"
check_service "n8n (5678)" "http://100.105.68.15:5678" || true

echo ""
echo "Verificando modelo de embeddings..."
if curl -s http://100.116.107.52:11434/api/tags 2>/dev/null | grep -q "nomic-embed-text"; then
    echo -e "${GREEN}✓${NC} nomic-embed-text disponible en Ollama"
else
    echo -e "${RED}✗${NC} nomic-embed-text NO encontrado"
    echo -e "${YELLOW}  Ejecutar: ssh vostro 'ollama pull nomic-embed-text'${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "Verificando Weaviate schema..."
WEAVIATE_CLASSES=$(curl -s http://100.110.109.43:8080/v1/schema 2>/dev/null | grep -o '"class"' | wc -l)
if [ "$WEAVIATE_CLASSES" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Weaviate tiene $WEAVIATE_CLASSES clase(s) configurada(s)"
else
    echo -e "${YELLOW}!${NC} Weaviate sin clases configuradas (se crearán en Fase 3)"
fi

echo ""
echo "Verificando estructura de directorios..."
for dir in services scripts tests; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir/"
    else
        echo -e "${YELLOW}!${NC} $dir/ no existe - ejecutar: mkdir -p $dir"
    fi
done

echo ""
echo "Verificando archivo .env..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env existe"

    # Verificar variables críticas
    source .env 2>/dev/null
    if [ -n "$DIFY_API_KEY" ] && [ "$DIFY_API_KEY" != "app-xxx" ]; then
        echo -e "${GREEN}✓${NC} DIFY_API_KEY configurada"
    else
        echo -e "${YELLOW}!${NC} DIFY_API_KEY no configurada o es placeholder"
    fi

    if [ -n "$WEAVIATE_URL" ]; then
        echo -e "${GREEN}✓${NC} WEAVIATE_URL configurada: $WEAVIATE_URL"
    else
        echo -e "${YELLOW}!${NC} WEAVIATE_URL no configurada"
    fi
else
    echo -e "${YELLOW}!${NC} .env no existe - ver fase-0-infraestructura.md para crear"
fi

echo ""
echo "=== Resumen ==="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}Todos los servicios operativos. Listo para desarrollo.${NC}"
else
    echo -e "${RED}$ERRORS servicio(s) con problemas. Revisar antes de continuar.${NC}"
fi
echo ""
