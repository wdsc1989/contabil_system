#!/bin/bash
# Script para corrigir problemas comuns em produção
# Uso: bash deploy/fix_production.sh

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR="${APP_DIR:-/opt/contabil}"
VENV_DIR="${APP_DIR}/venv"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   CORREÇÃO DE PROBLEMAS - PRODUÇÃO                     ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

cd "$APP_DIR"

# 1. Corrige permissões dos scripts
echo -e "${YELLOW}🔧 Corrigindo permissões dos scripts...${NC}"
chmod +x deploy/deploy.sh
chmod +x deploy/setup_vps_hostinger.sh
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true
echo -e "${GREEN}✅ Permissões corrigidas${NC}"

# 2. Ativa venv e instala PyMuPDF
echo -e "${YELLOW}📦 Instalando PyMuPDF...${NC}"
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip
pip install PyMuPDF>=1.23.0
echo -e "${GREEN}✅ PyMuPDF instalado${NC}"

# 3. Verifica instalação
echo -e "${YELLOW}🔍 Verificando instalação...${NC}"
python -c "import fitz; print('✅ PyMuPDF OK:', fitz.__version__)" || {
    echo -e "${RED}❌ Erro ao importar PyMuPDF${NC}"
    exit 1
}

python -c "import openai; print('✅ OpenAI OK:', openai.__version__)" || {
    echo -e "${RED}❌ Erro ao importar OpenAI${NC}"
    exit 1
}

# 4. Instala todas as dependências do requirements.txt
echo -e "${YELLOW}📚 Instalando todas as dependências...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependências instaladas${NC}"

# 5. Verifica poppler (para pdf2image fallback)
echo -e "${YELLOW}🔍 Verificando poppler-utils...${NC}"
if ! command -v pdftoppm &> /dev/null; then
    echo -e "${YELLOW}⚠️  poppler-utils não encontrado. Instalando...${NC}"
    apt-get update && apt-get install -y poppler-utils || {
        echo -e "${YELLOW}⚠️  Não foi possível instalar poppler-utils (pode não ser necessário)${NC}"
    }
else
    echo -e "${GREEN}✅ poppler-utils já instalado${NC}"
fi

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   CORREÇÃO CONCLUÍDA!                                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ Tudo pronto! Agora você pode executar:${NC}"
echo "   ./deploy/deploy.sh"
echo ""




