#!/bin/bash
# Script para executar todas as migrações necessárias no banco de dados
# Uso: bash scripts/run_migrations.sh

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   EXECUTANDO MIGRAÇÕES DO BANCO DE DADOS                ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verifica se está no diretório correto
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ Erro: Execute este script de dentro do diretório da aplicação${NC}"
    exit 1
fi

# Ativa ambiente virtual se existir
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Ambiente virtual ativado${NC}"
fi

# Backup antes de migrar
echo -e "${YELLOW}📦 Criando backup antes das migrações...${NC}"
if [ -f "scripts/backup_postgres.sh" ]; then
    bash scripts/backup_postgres.sh pre_migration || echo -e "${YELLOW}⚠️  Aviso: Erro ao criar backup (continuando...)${NC}"
else
    echo -e "${YELLOW}⚠️  Script de backup não encontrado (continuando...)${NC}"
fi
echo ""

# Migração 1: Adicionar colunas faltantes (script robusto que funciona com SQLite e PostgreSQL)
echo -e "${YELLOW}[1/3] Executando migração: Adicionar Colunas Faltantes...${NC}"
if [ -f "scripts/adicionar_colunas_faltantes.py" ]; then
    python3 scripts/adicionar_colunas_faltantes.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Migração de colunas concluída${NC}"
    else
        echo -e "${RED}❌ Erro na migração de colunas${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Script adicionar_colunas_faltantes.py não encontrado${NC}"
    # Fallback para scripts antigos
    if [ -f "scripts/migrate_expand_contracts.py" ]; then
        echo -e "${YELLOW}   Tentando migrate_expand_contracts.py...${NC}"
        python3 scripts/migrate_expand_contracts.py || true
    fi
    if [ -f "scripts/migrate_expand_accounts.py" ]; then
        echo -e "${YELLOW}   Tentando migrate_expand_accounts.py...${NC}"
        python3 scripts/migrate_expand_accounts.py || true
    fi
fi
echo ""

# Migração 2: Expandir contratos (legacy - mantido para compatibilidade)
echo -e "${YELLOW}[2/3] Executando migração: Expandir Contratos (legacy)...${NC}"
if [ -f "scripts/migrate_expand_contracts.py" ]; then
    python3 scripts/migrate_expand_contracts.py || echo -e "${YELLOW}⚠️  Aviso: Erro na migração de contratos (pode ser que já esteja aplicada)${NC}"
else
    echo -e "${YELLOW}⚠️  Script migrate_expand_contracts.py não encontrado${NC}"
fi
echo ""

# Migração 3: Expandir contas (legacy - mantido para compatibilidade)
echo -e "${YELLOW}[3/3] Executando migração: Expandir Contas (legacy)...${NC}"
if [ -f "scripts/migrate_expand_accounts.py" ]; then
    python3 scripts/migrate_expand_accounts.py || echo -e "${YELLOW}⚠️  Aviso: Erro na migração de contas (pode ser que já esteja aplicada)${NC}"
else
    echo -e "${YELLOW}⚠️  Script migrate_expand_accounts.py não encontrado${NC}"
fi
echo ""

# Resumo
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   MIGRAÇÕES CONCLUÍDAS!                                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ Todas as migrações foram executadas com sucesso!${NC}"
echo ""
echo -e "${YELLOW}📋 Próximos passos:${NC}"
echo "   1. Reiniciar o serviço: sudo systemctl restart contabil"
echo "   2. Verificar logs: sudo journalctl -u contabil.service -f"
echo "   3. Testar a aplicação no navegador"
echo ""

