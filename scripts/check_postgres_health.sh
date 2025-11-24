#!/bin/bash
# Script de verificação de saúde do PostgreSQL

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Carrega variáveis de ambiente
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

DB_NAME="${POSTGRES_DB:-contabil_db}"
DB_USER="${POSTGRES_USER:-contabil_user}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

export PGPASSWORD="${POSTGRES_PASSWORD}"

ALERTAS=0

echo "🔍 Verificando saúde do PostgreSQL..."
echo ""

# Verifica se PostgreSQL está rodando
if ! systemctl is-active --quiet postgresql; then
    echo -e "${RED}❌ ALERTA: PostgreSQL não está rodando!${NC}"
    ALERTAS=$((ALERTAS + 1))
else
    echo -e "${GREEN}✅ PostgreSQL está rodando${NC}"
fi

# Verifica conexões
CONEXOES=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname = '$DB_NAME';" 2>/dev/null | xargs)
MAX_CONEXOES=100

if [ -n "$CONEXOES" ]; then
    if [ "$CONEXOES" -gt "$MAX_CONEXOES" ]; then
        echo -e "${YELLOW}⚠️  ALERTA: Muitas conexões ($CONEXOES/$MAX_CONEXOES)${NC}"
        ALERTAS=$((ALERTAS + 1))
    else
        echo -e "${GREEN}✅ Conexões OK ($CONEXOES)${NC}"
    fi
fi

# Verifica espaço em disco
if [ -d "/var/lib/postgresql" ]; then
    DISCO_USADO=$(df /var/lib/postgresql 2>/dev/null | tail -1 | awk '{print $5}' | sed 's/%//')
else
    DISCO_USADO=$(df / 2>/dev/null | tail -1 | awk '{print $5}' | sed 's/%//')
fi

if [ -n "$DISCO_USADO" ]; then
    if [ "$DISCO_USADO" -gt 80 ]; then
        echo -e "${YELLOW}⚠️  ALERTA: Disco quase cheio ($DISCO_USADO%)${NC}"
        ALERTAS=$((ALERTAS + 1))
    elif [ "$DISCO_USADO" -gt 90 ]; then
        echo -e "${RED}❌ ALERTA CRÍTICO: Disco muito cheio ($DISCO_USADO%)${NC}"
        ALERTAS=$((ALERTAS + 1))
    else
        echo -e "${GREEN}✅ Espaço em disco OK ($DISCO_USADO%)${NC}"
    fi
fi

# Verifica tamanho do banco
TAMANHO_GB=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_database_size('$DB_NAME') / 1024.0 / 1024.0 / 1024.0;" 2>/dev/null | xargs)

if [ -n "$TAMANHO_GB" ]; then
    # Usa awk para comparação de float
    TAMANHO_CHECK=$(echo "$TAMANHO_GB" | awk '{if ($1 > 10) print "ALERTA"; else print "OK"}')
    if [ "$TAMANHO_CHECK" = "ALERTA" ]; then
        echo -e "${YELLOW}⚠️  ALERTA: Banco muito grande (${TAMANHO_GB}GB)${NC}"
        ALERTAS=$((ALERTAS + 1))
    else
        echo -e "${GREEN}✅ Tamanho do banco OK (${TAMANHO_GB}GB)${NC}"
    fi
fi

# Verifica queries lentas
QUERIES_LENTAS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT count(*) FROM pg_stat_activity 
WHERE (now() - query_start) > interval '5 minutes' 
  AND datname = '$DB_NAME';
" 2>/dev/null | xargs)

if [ -n "$QUERIES_LENTAS" ] && [ "$QUERIES_LENTAS" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  ALERTA: $QUERIES_LENTAS query(s) lenta(s) detectada(s)${NC}"
    ALERTAS=$((ALERTAS + 1))
else
    echo -e "${GREEN}✅ Nenhuma query lenta${NC}"
fi

echo ""
if [ "$ALERTAS" -eq 0 ]; then
    echo -e "${GREEN}✅ Tudo OK! Nenhum alerta.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Total de alertas: $ALERTAS${NC}"
    exit 1
fi









