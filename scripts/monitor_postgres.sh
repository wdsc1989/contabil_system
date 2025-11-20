#!/bin/bash
# Script de monitoramento rápido do PostgreSQL

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   MONITORAMENTO POSTGRESQL - Sistema Contábil            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

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

echo -e "${YELLOW}📊 Status do PostgreSQL${NC}"
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✅ PostgreSQL está rodando${NC}"
else
    echo -e "${RED}❌ PostgreSQL não está rodando${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}💾 Tamanho do Banco${NC}"
TAMANHO=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | xargs)
if [ -n "$TAMANHO" ]; then
    echo "   $TAMANHO"
else
    echo -e "${RED}   Erro ao obter tamanho${NC}"
fi

echo ""
echo -e "${YELLOW}🔌 Conexões Ativas${NC}"
CONEXOES=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname = '$DB_NAME';" 2>/dev/null | xargs)
if [ -n "$CONEXOES" ]; then
    echo "   Total: $CONEXOES conexão(ões)"
else
    echo -e "${RED}   Erro ao obter conexões${NC}"
fi

echo ""
echo -e "${YELLOW}📈 Top 5 Tabelas por Tamanho${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS tamanho
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size('public.'||tablename) DESC
LIMIT 5;
" 2>/dev/null || echo -e "${RED}   Erro ao obter tabelas${NC}"

echo ""
echo -e "${YELLOW}📊 Contagem de Registros${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT 
    'users' as tabela, COUNT(*) as registros FROM users
UNION ALL
SELECT 'clients', COUNT(*) FROM clients
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'contracts', COUNT(*) FROM contracts
ORDER BY registros DESC;
" 2>/dev/null || echo -e "${RED}   Erro ao obter contagens${NC}"

echo ""
echo -e "${YELLOW}⏱️  Queries Lentas (> 1 minuto)${NC}"
QUERIES_LENTAS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT count(*) FROM pg_stat_activity
WHERE (now() - query_start) > interval '1 minute'
  AND datname = '$DB_NAME';
" 2>/dev/null | xargs)

if [ -n "$QUERIES_LENTAS" ] && [ "$QUERIES_LENTAS" -gt 0 ]; then
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT 
        pid,
        now() - query_start AS duracao,
        LEFT(query, 50) as query_inicio,
        state
    FROM pg_stat_activity
    WHERE (now() - query_start) > interval '1 minute'
      AND datname = '$DB_NAME'
    ORDER BY duracao DESC;
    " 2>/dev/null
else
    echo "   Nenhuma query lenta detectada"
fi

echo ""
echo -e "${YELLOW}💿 Espaço em Disco${NC}"
if [ -d "/var/lib/postgresql" ]; then
    df -h /var/lib/postgresql | tail -1 | awk '{print "   Usado: " $3 " / " $2 " (" $5 ")"}'
else
    df -h / | tail -1 | awk '{print "   Usado: " $3 " / " $2 " (" $5 ")"}'
fi

echo ""
echo "✅ Monitoramento concluído!"

