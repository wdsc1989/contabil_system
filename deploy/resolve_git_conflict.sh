#!/bin/bash
# Script para resolver conflitos de git na VPS
# Uso: bash deploy/resolve_git_conflict.sh

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR="${APP_DIR:-/opt/contabil}"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   RESOLVENDO CONFLITOS GIT                             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

cd "$APP_DIR"

# Verifica status
echo -e "${YELLOW}📊 Verificando status do Git...${NC}"
git status --short

# Opção 1: Fazer stash das mudanças locais
echo -e "${YELLOW}💾 Fazendo stash das mudanças locais...${NC}"
git stash push -m "Mudanças locais antes do pull $(date +%Y-%m-%d)"

# Atualiza código
echo -e "${YELLOW}📦 Atualizando código do repositório...${NC}"
git fetch origin
git checkout main
git pull origin main

echo -e "${GREEN}✅ Código atualizado com sucesso!${NC}"
echo ""
echo -e "${YELLOW}💡 Nota: Seus arquivos locais foram salvos no stash.${NC}"
echo -e "${YELLOW}   Para ver: git stash list${NC}"
echo -e "${YELLOW}   Para restaurar: git stash pop${NC}"
echo ""




