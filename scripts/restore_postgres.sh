#!/bin/bash
# Script de restauração de backup do PostgreSQL
# Uso: ./restore_postgres.sh [arquivo_backup] [--confirm]
# ATENÇÃO: Este script irá SOBRESCREVER o banco de dados atual!

set -e  # Para na primeira erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verifica se o arquivo foi fornecido
if [ -z "$1" ]; then
    echo -e "${RED}❌ Erro: Arquivo de backup não especificado${NC}"
    echo "Uso: $0 [arquivo_backup] [--confirm]"
    echo ""
    echo "Exemplo:"
    echo "  $0 /var/backups/contabil/postgresql/daily/backup_daily_2024-01-15_02-00-00.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"
CONFIRM="$2"

# Verifica se o arquivo existe
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Erro: Arquivo de backup não encontrado: $BACKUP_FILE${NC}"
    exit 1
fi

# Configurações do banco
DB_NAME="${POSTGRES_DB:-contabil_db}"
DB_USER="${POSTGRES_USER:-contabil_user}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

echo -e "${RED}⚠️  ATENÇÃO: Esta operação irá SOBRESCREVER o banco de dados atual!${NC}"
echo ""
echo "Banco de destino: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "Arquivo de backup: $BACKUP_FILE"
echo ""

# Verifica confirmação
if [ "$CONFIRM" != "--confirm" ]; then
    echo -e "${YELLOW}Para confirmar a restauração, execute:${NC}"
    echo "$0 $BACKUP_FILE --confirm"
    exit 1
fi

# Verifica integridade do arquivo
echo -e "${YELLOW}🔍 Verificando integridade do backup...${NC}"
if [[ "$BACKUP_FILE" == *.gz ]]; then
    if ! gzip -t "$BACKUP_FILE" 2>/dev/null; then
        echo -e "${RED}❌ Erro: Arquivo de backup corrompido${NC}"
        exit 1
    fi
    
    # Verifica MD5 se existir
    if [ -f "${BACKUP_FILE}.md5" ]; then
        EXPECTED_MD5=$(cat "${BACKUP_FILE}.md5")
        ACTUAL_MD5=$(md5sum "$BACKUP_FILE" | cut -d' ' -f1)
        
        if [ "$EXPECTED_MD5" != "$ACTUAL_MD5" ]; then
            echo -e "${RED}❌ Erro: Hash MD5 não confere. Arquivo pode estar corrompido.${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ Hash MD5 verificado${NC}"
    fi
fi

# Solicita senha
export PGPASSWORD="${POSTGRES_PASSWORD}"

# Verifica se psql está disponível
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ Erro: psql não encontrado. Instale o PostgreSQL client.${NC}"
    exit 1
fi

# Cria backup do banco atual ANTES de restaurar
echo -e "${YELLOW}📦 Criando backup de segurança do banco atual...${NC}"
SAFETY_BACKUP="/tmp/contabil_safety_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" | gzip > "$SAFETY_BACKUP"; then
    echo -e "${GREEN}✅ Backup de segurança criado: $SAFETY_BACKUP${NC}"
else
    echo -e "${YELLOW}⚠️  Aviso: Não foi possível criar backup de segurança${NC}"
fi

# Descompacta o backup se necessário
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo -e "${YELLOW}🗜️  Descompactando backup...${NC}"
    TEMP_FILE="/tmp/contabil_restore_$(date +%Y%m%d_%H%M%S).sql"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    RESTORE_FILE="$TEMP_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Desconecta todas as conexões ativas (exceto a nossa)
echo -e "${YELLOW}🔌 Desconectando conexões ativas...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$DB_NAME'
  AND pid <> pg_backend_pid();
" 2>/dev/null || true

# Restaura o backup
echo -e "${YELLOW}🔄 Restaurando banco de dados...${NC}"
echo "Isso pode levar alguns minutos dependendo do tamanho do backup..."

if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$RESTORE_FILE" 2>&1; then
    echo -e "${GREEN}✅ Banco de dados restaurado com sucesso!${NC}"
    
    # Verifica se a restauração foi bem-sucedida
    echo -e "${YELLOW}🔍 Verificando integridade...${NC}"
    TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
    echo "Tabelas encontradas: $TABLE_COUNT"
    
    if [ "$TABLE_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ Restauração validada com sucesso!${NC}"
    else
        echo -e "${RED}⚠️  Aviso: Nenhuma tabela encontrada após restauração${NC}"
    fi
    
    # Limpa arquivo temporário
    if [ -f "$TEMP_FILE" ]; then
        rm -f "$TEMP_FILE"
    fi
    
    echo -e "\n${GREEN}✅ Processo de restauração concluído!${NC}"
    echo -e "${YELLOW}💡 Dica: Backup de segurança salvo em: $SAFETY_BACKUP${NC}"
    exit 0
else
    echo -e "${RED}❌ Erro ao restaurar banco de dados${NC}"
    echo -e "${YELLOW}💡 Você pode restaurar o backup de segurança:${NC}"
    echo "  $0 $SAFETY_BACKUP --confirm"
    
    # Limpa arquivo temporário
    if [ -f "$TEMP_FILE" ]; then
        rm -f "$TEMP_FILE"
    fi
    
    exit 1
fi







