#!/bin/bash

# Script de limpieza del proyecto SDRAG Chainlit
# Elimina archivos duplicados, zombies y reorganiza assets

set -e  # Salir en caso de error

PROJECT_ROOT="/home/hectorsa/Documents/sdrag_chainlit"
cd "$PROJECT_ROOT"

echo "🧹 Iniciando limpieza del proyecto SDRAG Chainlit..."
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Contador de acciones
actions_taken=0

# Función para confirmar acción
confirm() {
    read -p "$1 (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# 1. Eliminar ARQUITECTURA.md obsoleto en raíz
echo "📄 Verificando ARQUITECTURA.md..."
if [ -f "ARQUITECTURA.md" ]; then
    echo -e "${YELLOW}Encontrado ARQUITECTURA.md obsoleto en raíz${NC}"
    if confirm "¿Eliminar ARQUITECTURA.md de raíz? (la versión correcta está en documentos_de_referencia_tesis/)"; then
        rm ARQUITECTURA.md
        echo -e "${GREEN}✅ ARQUITECTURA.md eliminado de raíz${NC}"
        ((actions_taken++))
    else
        echo "⏭️  Saltado"
    fi
else
    echo -e "${GREEN}✅ ARQUITECTURA.md ya no existe en raíz${NC}"
fi
echo ""

# 2. Eliminar main.py zombie
echo "🐍 Verificando main.py..."
if [ -f "main.py" ]; then
    echo -e "${YELLOW}Encontrado main.py (archivo zombie)${NC}"
    if confirm "¿Eliminar main.py? (no se usa, entry point es app.py)"; then
        rm main.py
        echo -e "${GREEN}✅ main.py eliminado${NC}"
        ((actions_taken++))
    else
        echo "⏭️  Saltado"
    fi
else
    echo -e "${GREEN}✅ main.py ya no existe${NC}"
fi
echo ""

# 3. Logos en raíz
echo "🎨 Verificando logos en raíz..."
logos_found=0

if [ -f "sdrag_log_no_bg.svg" ]; then
    ((logos_found++))
fi
if [ -f "sdrag_logo_no_bg.png" ]; then
    ((logos_found++))
fi
if [ -f "sdrag_logo.svg" ]; then
    ((logos_found++))
fi

if [ $logos_found -gt 0 ]; then
    echo -e "${YELLOW}Encontrados $logos_found logos en raíz:${NC}"
    ls -lh sdrag_log*.svg sdrag_logo*.png sdrag_logo.svg 2>/dev/null | awk '{print "  - " $9 " (" $5 ")"}'
    echo ""
    echo "Opciones:"
    echo "  1) Mover a public/"
    echo "  2) Eliminar (si son duplicados)"
    echo "  3) Mantener en raíz"
    read -p "Elige opción (1/2/3): " -n 1 -r
    echo ""

    case $REPLY in
        1)
            mv sdrag_log_no_bg.svg public/ 2>/dev/null && echo -e "${GREEN}✅ sdrag_log_no_bg.svg movido${NC}" && ((actions_taken++))
            mv sdrag_logo_no_bg.png public/ 2>/dev/null && echo -e "${GREEN}✅ sdrag_logo_no_bg.png movido${NC}" && ((actions_taken++))
            mv sdrag_logo.svg public/ 2>/dev/null && echo -e "${GREEN}✅ sdrag_logo.svg movido${NC}" && ((actions_taken++))
            ;;
        2)
            rm sdrag_log_no_bg.svg 2>/dev/null && echo -e "${GREEN}✅ sdrag_log_no_bg.svg eliminado${NC}" && ((actions_taken++))
            rm sdrag_logo_no_bg.png 2>/dev/null && echo -e "${GREEN}✅ sdrag_logo_no_bg.png eliminado${NC}" && ((actions_taken++))
            rm sdrag_logo.svg 2>/dev/null && echo -e "${GREEN}✅ sdrag_logo.svg eliminado${NC}" && ((actions_taken++))
            ;;
        3)
            echo "⏭️  Manteniendo logos en raíz"
            ;;
        *)
            echo "⏭️  Opción inválida, saltando"
            ;;
    esac
else
    echo -e "${GREEN}✅ No hay logos en raíz${NC}"
fi
echo ""

# 4. Verificar que documentos de referencia estén intactos
echo "📚 Verificando documentos de referencia de maestría..."
if [ -f "documentos_de_referencia_tesis/ARQUITECTURA.md" ]; then
    echo -e "${GREEN}✅ documentos_de_referencia_tesis/ARQUITECTURA.md intacto${NC}"
else
    echo -e "${RED}⚠️  ADVERTENCIA: documentos_de_referencia_tesis/ARQUITECTURA.md NO ENCONTRADO${NC}"
fi

if [ -f "documentos_de_referencia_tesis/Protocolo_MCD_2025_Hector_Sanchez_v7_Weaviate.md" ]; then
    echo -e "${GREEN}✅ Protocolo v7 intacto${NC}"
else
    echo -e "${RED}⚠️  ADVERTENCIA: Protocolo v7 NO ENCONTRADO${NC}"
fi
echo ""

# 5. Resumen
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Resumen de limpieza:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Acciones completadas: $actions_taken${NC}"
echo ""

if [ $actions_taken -gt 0 ]; then
    echo "🎯 Cambios realizados. Considera hacer commit:"
    echo ""
    echo "  git add -A"
    echo "  git commit -m \"chore: limpieza de archivos duplicados y zombies\""
    echo ""
fi

echo "✨ Limpieza completada. El proyecto está listo para Fase 3."
echo ""

# 6. Verificación final (opcional)
if confirm "¿Ejecutar verificación final?"; then
    echo ""
    echo "🔍 Verificación final de estructura del proyecto:"
    echo ""

    # Archivos que NO deben existir
    echo "Archivos que NO deben existir en raíz:"
    for file in "ARQUITECTURA.md" "main.py"; do
        if [ -f "$file" ]; then
            echo -e "  ${RED}❌ $file (aún existe)${NC}"
        else
            echo -e "  ${GREEN}✅ $file (eliminado correctamente)${NC}"
        fi
    done

    echo ""
    echo "Archivos que DEBEN existir:"
    for file in "app.py" "README.md" "ROADMAP.md" "documentos_de_referencia_tesis/ARQUITECTURA.md"; do
        if [ -f "$file" ]; then
            echo -e "  ${GREEN}✅ $file${NC}"
        else
            echo -e "  ${RED}❌ $file (no encontrado)${NC}"
        fi
    done

    echo ""
    echo "Directorios críticos:"
    for dir in "roadmap" "tests" "scripts" "documentos_de_referencia_tesis" "public"; do
        if [ -d "$dir" ]; then
            count=$(find "$dir" -type f | wc -l)
            echo -e "  ${GREEN}✅ $dir/ ($count archivos)${NC}"
        else
            echo -e "  ${RED}❌ $dir/ (no encontrado)${NC}"
        fi
    done
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Script de limpieza finalizado"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
