#!/bin/bash
# Relatório diário do PostgreSQL

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

LOG_DIR="/var/log/contabil"
mkdir -p "$LOG_DIR"

REPORT_FILE="$LOG_DIR/postgres_report_$(date +%Y%m%d).txt"

{
    echo "═══════════════════════════════════════════════════════════"
    echo "  RELATÓRIO DIÁRIO - PostgreSQL"
    echo "  Data: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    echo "📊 TAMANHO DO BANCO"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT pg_size_pretty(pg_database_size('$DB_NAME')) AS tamanho_total;
    " 2>/dev/null || echo "Erro ao obter tamanho"
    
    echo ""
    echo "📈 CONTAGEM DE REGISTROS"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT 
        'users' as tabela, COUNT(*) as registros FROM users
    UNION ALL
    SELECT 'clients', COUNT(*) FROM clients
    UNION ALL
    SELECT 'transactions', COUNT(*) FROM transactions
    UNION ALL
    SELECT 'contracts', COUNT(*) FROM contracts
    UNION ALL
    SELECT 'accounts_payable', COUNT(*) FROM accounts_payable
    UNION ALL
    SELECT 'accounts_receivable', COUNT(*) FROM accounts_receivable
    ORDER BY registros DESC;
    " 2>/dev/null || echo "Erro ao obter contagens"
    
    echo ""
    echo "💾 TOP 10 TABELAS POR TAMANHO"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT 
        tablename,
        pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS tamanho
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY pg_total_relation_size('public.'||tablename) DESC
    LIMIT 10;
    " 2>/dev/null || echo "Erro ao obter tabelas"
    
    echo ""
    echo "🔌 CONEXÕES"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT state, count(*) 
    FROM pg_stat_activity 
    WHERE datname = '$DB_NAME'
    GROUP BY state;
    " 2>/dev/null || echo "Erro ao obter conexões"
    
    echo ""
    echo "💿 ESPAÇO EM DISCO"
    if [ -d "/var/lib/postgresql" ]; then
        df -h /var/lib/postgresql
    else
        df -h /
    fi
    
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  Fim do Relatório"
    echo "═══════════════════════════════════════════════════════════"
    
} > "$REPORT_FILE" 2>&1

echo "Relatório salvo em: $REPORT_FILE"
echo ""
cat "$REPORT_FILE"

























