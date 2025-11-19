#!/bin/bash
# Script de deploy da aplicação
# Uso: ./deploy.sh [branch]
# Executa: git pull, instala dependências, migra banco, reinicia serviços

set -e  # Para na primeira erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
APP_DIR="${APP_DIR:-/opt/contabil}"
BRANCH="${1:-main}"
APP_USER="${APP_USER:-contabil}"
VENV_DIR="${APP_DIR}/venv"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DEPLOY - Sistema Contábil                             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verifica se está no diretório correto
if [ ! -f "${APP_DIR}/app.py" ]; then
    echo -e "${RED}❌ Erro: Diretório da aplicação não encontrado: $APP_DIR${NC}"
    echo "   Execute este script de dentro do diretório da aplicação"
    exit 1
fi

cd "$APP_DIR"

# Verifica se .env existe
if [ ! -f "${APP_DIR}/.env" ]; then
    echo -e "${RED}❌ Erro: Arquivo .env não encontrado${NC}"
    echo "   Copie env.example.txt para .env e configure as variáveis"
    exit 1
fi

# Carrega variáveis de ambiente
set -a
source "${APP_DIR}/.env"
set +a

echo -e "${YELLOW}📦 Atualizando código do repositório...${NC}"
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

COMMIT_HASH=$(git rev-parse --short HEAD)
echo -e "${GREEN}✅ Código atualizado (commit: $COMMIT_HASH)${NC}"

# Cria/atualiza ambiente virtual
echo -e "${YELLOW}🐍 Configurando ambiente virtual...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    python3.12 -m venv "$VENV_DIR"
    echo -e "${GREEN}✅ Ambiente virtual criado${NC}"
else
    echo -e "${YELLOW}⚠️  Ambiente virtual já existe${NC}"
fi

# Ativa ambiente virtual e instala/atualiza dependências
echo -e "${YELLOW}📚 Instalando dependências...${NC}"
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✅ Dependências instaladas${NC}"

# Executa migrações do banco (se necessário)
echo -e "${YELLOW}🗄️  Verificando migrações do banco...${NC}"
python3 "${APP_DIR}/init_db.py" || echo -e "${YELLOW}⚠️  Aviso: Erro ao executar init_db.py (pode ser normal se já estiver atualizado)${NC}"

# Cria backup antes de atualizar (se aplicável)
if [ -f "${APP_DIR}/scripts/backup_postgres.sh" ]; then
    echo -e "${YELLOW}📦 Criando backup antes do deploy...${NC}"
    bash "${APP_DIR}/scripts/backup_postgres.sh" daily || echo -e "${YELLOW}⚠️  Aviso: Erro ao criar backup${NC}"
fi

# Reinicia serviço systemd
echo -e "${YELLOW}🔄 Reiniciando serviço...${NC}"
if systemctl is-active --quiet contabil.service; then
    systemctl restart contabil.service
    echo -e "${GREEN}✅ Serviço reiniciado${NC}"
else
    echo -e "${YELLOW}⚠️  Serviço não está rodando. Inicie com: systemctl start contabil.service${NC}"
fi

# Verifica status do serviço
sleep 2
if systemctl is-active --quiet contabil.service; then
    echo -e "${GREEN}✅ Serviço está rodando${NC}"
    
    # Verifica se a aplicação está respondendo
    sleep 3
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 | grep -q "200\|302"; then
        echo -e "${GREEN}✅ Aplicação está respondendo${NC}"
    else
        echo -e "${YELLOW}⚠️  Aplicação pode não estar respondendo corretamente${NC}"
    fi
else
    echo -e "${RED}❌ Erro: Serviço não está rodando${NC}"
    echo "   Verifique os logs: journalctl -u contabil.service -n 50"
    exit 1
fi

# Testa Nginx (se configurado)
if systemctl is-active --quiet nginx; then
    echo -e "${YELLOW}🌐 Testando configuração do Nginx...${NC}"
    nginx -t && systemctl reload nginx
    echo -e "${GREEN}✅ Nginx atualizado${NC}"
fi

# Resumo
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DEPLOY CONCLUÍDO!                                     ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ Deploy realizado com sucesso!${NC}"
echo "   Commit: $COMMIT_HASH"
echo "   Branch: $BRANCH"
echo ""
echo -e "${YELLOW}📋 Comandos úteis:${NC}"
echo "   Ver logs: journalctl -u contabil.service -f"
echo "   Status: systemctl status contabil.service"
echo "   Reiniciar: systemctl restart contabil.service"
echo ""

