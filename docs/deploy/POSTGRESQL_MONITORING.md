# 📊 Guia de Monitoramento do PostgreSQL

Este guia fornece comandos e scripts para monitorar o banco de dados PostgreSQL do Sistema Contábil.

## 🔍 Monitoramento Básico

### 1. Verificar Status do PostgreSQL

```bash
# Status do serviço
systemctl status postgresql

# Verifica se está rodando
pg_isready -h localhost -p 5432

# Versão do PostgreSQL
psql -h localhost -U postgres -c "SELECT version();"
```

### 2. Conectar ao Banco

```bash
# Como usuário postgres
sudo -u postgres psql -d contabil_db

# Como usuário contabil_user
psql -h localhost -U contabil_user -d contabil_db
```

---

## 📈 Queries de Monitoramento

### Tamanho do Banco de Dados

```sql
-- Tamanho total do banco
SELECT pg_size_pretty(pg_database_size('contabil_db')) AS tamanho_total;

-- Tamanho por tabela
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS tamanho,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS tabela,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indices
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Contagem de Registros

```sql
-- Contagem por tabela
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
UNION ALL
SELECT 'bank_statements', COUNT(*) FROM bank_statements
UNION ALL
SELECT 'groups', COUNT(*) FROM groups
UNION ALL
SELECT 'subgroups', COUNT(*) FROM subgroups
ORDER BY registros DESC;
```

### Conexões Ativas

```sql
-- Conexões ativas
SELECT 
    datname,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    state_change
FROM pg_stat_activity
WHERE datname = 'contabil_db'
ORDER BY query_start;

-- Total de conexões
SELECT count(*) as total_conexoes FROM pg_stat_activity WHERE datname = 'contabil_db';

-- Conexões por estado
SELECT state, count(*) 
FROM pg_stat_activity 
WHERE datname = 'contabil_db'
GROUP BY state;
```

### Queries Lentas

```sql
-- Queries em execução há mais de 1 minuto
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duracao,
    query,
    state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '1 minute'
  AND datname = 'contabil_db'
ORDER BY duracao DESC;
```

### Estatísticas de Tabelas

```sql
-- Estatísticas de tabelas (última atualização, número de linhas)
SELECT 
    schemaname,
    tablename,
    n_live_tup as linhas_vivas,
    n_dead_tup as linhas_mortas,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
```

### Índices Não Utilizados

```sql
-- Índices que nunca foram usados
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as vezes_usado
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Espaço em Disco

```sql
-- Espaço usado pelo banco
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS tamanho
FROM pg_database
ORDER BY pg_database_size(pg_database.datname) DESC;

-- Espaço total usado
SELECT pg_size_pretty(sum(pg_database_size(datname))) AS tamanho_total
FROM pg_database;
```

---

## 🔧 Scripts de Monitoramento

### Script: Verificação Rápida

Crie o arquivo `/opt/contabil/contabil_system/scripts/monitor_postgres.sh`:

```bash
#!/bin/bash
# Script de monitoramento rápido do PostgreSQL

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   MONITORAMENTO POSTGRESQL - Sistema Contábil            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Carrega variáveis de ambiente
source /opt/contabil/contabil_system/.env 2>/dev/null || true

DB_NAME="${POSTGRES_DB:-contabil_db}"
DB_USER="${POSTGRES_USER:-contabil_user}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

export PGPASSWORD="${POSTGRES_PASSWORD}"

echo -e "${YELLOW}📊 Status do PostgreSQL${NC}"
systemctl is-active postgresql && echo -e "${GREEN}✅ PostgreSQL está rodando${NC}" || echo "❌ PostgreSQL não está rodando"

echo ""
echo -e "${YELLOW}💾 Tamanho do Banco${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT pg_size_pretty(pg_database_size('$DB_NAME')) AS tamanho;
" | xargs

echo ""
echo -e "${YELLOW}🔌 Conexões Ativas${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT count(*) as total FROM pg_stat_activity WHERE datname = '$DB_NAME';
" | xargs

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
"

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
"

echo ""
echo -e "${YELLOW}⏱️  Queries Lentas (> 1 minuto)${NC}"
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
"

echo ""
echo -e "${YELLOW}💿 Espaço em Disco${NC}"
df -h /var/lib/postgresql | tail -1 | awk '{print "Usado: " $3 " / " $2 " (" $5 ")"}'

echo ""
echo "✅ Monitoramento concluído!"
```

Torne executável:

```bash
chmod +x /opt/contabil/contabil_system/scripts/monitor_postgres.sh
```

Uso:

```bash
# Executa monitoramento
/opt/contabil/contabil_system/scripts/monitor_postgres.sh
```

---

## 📊 Monitoramento de Recursos do Sistema

### Uso de CPU e Memória

```bash
# Uso de recursos do PostgreSQL
top -p $(pgrep -d',' -f postgres)

# Ou use htop
htop -p $(pgrep -d',' -f postgres)

# Memória usada pelo PostgreSQL
ps aux | grep postgres | awk '{sum+=$6} END {print "Memória total: " sum/1024 " MB"}'
```

### Espaço em Disco

```bash
# Espaço usado pelo PostgreSQL
du -sh /var/lib/postgresql

# Espaço por banco
sudo -u postgres du -sh /var/lib/postgresql/16/main/base/*

# Espaço total do sistema
df -h
```

### Logs do PostgreSQL

```bash
# Ver logs recentes
sudo tail -f /var/log/postgresql/postgresql-16-main.log

# Ver erros
sudo grep ERROR /var/log/postgresql/postgresql-16-main.log | tail -20

# Ver warnings
sudo grep WARNING /var/log/postgresql/postgresql-16-main.log | tail -20
```

---

## 🚨 Alertas e Verificações

### Script de Verificação de Saúde

Crie `/opt/contabil/contabil_system/scripts/check_postgres_health.sh`:

```bash
#!/bin/bash
# Script de verificação de saúde do PostgreSQL

source /opt/contabil/contabil_system/.env 2>/dev/null || true

DB_NAME="${POSTGRES_DB:-contabil_db}"
DB_USER="${POSTGRES_USER:-contabil_user}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

export PGPASSWORD="${POSTGRES_PASSWORD}"

ALERTAS=0

# Verifica se PostgreSQL está rodando
if ! systemctl is-active --quiet postgresql; then
    echo "❌ ALERTA: PostgreSQL não está rodando!"
    ALERTAS=$((ALERTAS + 1))
fi

# Verifica conexões
CONEXOES=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname = '$DB_NAME';" | xargs)
MAX_CONEXOES=100

if [ "$CONEXOES" -gt "$MAX_CONEXOES" ]; then
    echo "⚠️  ALERTA: Muitas conexões ($CONEXOES/$MAX_CONEXOES)"
    ALERTA=$((ALERTAS + 1))
fi

# Verifica espaço em disco
DISCO_USADO=$(df /var/lib/postgresql | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISCO_USADO" -gt 80 ]; then
    echo "⚠️  ALERTA: Disco quase cheio ($DISCO_USADO%)"
    ALERTAS=$((ALERTAS + 1))
fi

# Verifica tamanho do banco
TAMANHO_GB=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_database_size('$DB_NAME') / 1024 / 1024 / 1024;" | xargs)
if (( $(echo "$TAMANHO_GB > 10" | bc -l) )); then
    echo "⚠️  ALERTA: Banco muito grande (${TAMANHO_GB}GB)"
    ALERTAS=$((ALERTAS + 1))
fi

# Verifica queries lentas
QUERIES_LENTAS=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT count(*) FROM pg_stat_activity 
WHERE (now() - query_start) > interval '5 minutes' 
  AND datname = '$DB_NAME';
" | xargs)

if [ "$QUERIES_LENTAS" -gt 0 ]; then
    echo "⚠️  ALERTA: $QUERIES_LENTAS query(s) lenta(s) detectada(s)"
    ALERTAS=$((ALERTAS + 1))
fi

if [ "$ALERTAS" -eq 0 ]; then
    echo "✅ Tudo OK! Nenhum alerta."
    exit 0
else
    echo "⚠️  Total de alertas: $ALERTAS"
    exit 1
fi
```

Torne executável:

```bash
chmod +x /opt/contabil/contabil_system/scripts/check_postgres_health.sh
```

### Agendar Verificação Diária

```bash
# Adiciona ao crontab
crontab -e

# Adiciona linha (verifica às 8h da manhã):
0 8 * * * /opt/contabil/contabil_system/scripts/check_postgres_health.sh >> /var/log/contabil/postgres_health.log 2>&1
```

---

## 🛠️ Ferramentas de Monitoramento

### pgAdmin (Interface Gráfica)

Instalação:

```bash
# Instala pgAdmin 4
curl -fsS https://www.pgadmin.org/static/packages_pgadmin_org.pub | sudo gpg --dearmor -o /usr/share/keyrings/packages-pgadmin-org.gpg
sudo sh -c 'echo "deb [signed-by=/usr/share/keyrings/packages-pgadmin-org.gpg] https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/$(lsb_release -cs) pgadmin4 main" > /etc/apt/sources.list.d/pgadmin4.list'
sudo apt update
sudo apt install pgadmin4-web

# Configura
sudo /usr/pgadmin4/bin/setup-web.sh
```

Acesso: `http://SEU_IP/pgadmin4`

### pg_stat_statements (Análise de Queries)

Habilita extensão para análise de queries:

```sql
-- Conecta como postgres
sudo -u postgres psql -d contabil_db

-- Habilita extensão
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Ver queries mais executadas
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

---

## 📋 Relatório Diário

### Script de Relatório

Crie `/opt/contabil/contabil_system/scripts/postgres_daily_report.sh`:

```bash
#!/bin/bash
# Relatório diário do PostgreSQL

source /opt/contabil/contabil_system/.env 2>/dev/null || true

DB_NAME="${POSTGRES_DB:-contabil_db}"
DB_USER="${POSTGRES_USER:-contabil_user}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

export PGPASSWORD="${POSTGRES_PASSWORD}"

REPORT_FILE="/var/log/contabil/postgres_report_$(date +%Y%m%d).txt"

{
    echo "═══════════════════════════════════════════════════════════"
    echo "  RELATÓRIO DIÁRIO - PostgreSQL"
    echo "  Data: $(date)"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    echo "📊 TAMANHO DO BANCO"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT pg_size_pretty(pg_database_size('$DB_NAME')) AS tamanho_total;
    "
    
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
    "
    
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
    "
    
    echo ""
    echo "🔌 CONEXÕES"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
    SELECT state, count(*) 
    FROM pg_stat_activity 
    WHERE datname = '$DB_NAME'
    GROUP BY state;
    "
    
    echo ""
    echo "💿 ESPAÇO EM DISCO"
    df -h /var/lib/postgresql
    
} > "$REPORT_FILE"

echo "Relatório salvo em: $REPORT_FILE"
cat "$REPORT_FILE"
```

Agende execução diária:

```bash
chmod +x /opt/contabil/contabil_system/scripts/postgres_daily_report.sh

# Adiciona ao crontab (executa às 6h da manhã)
crontab -e
# Adiciona:
0 6 * * * /opt/contabil/contabil_system/scripts/postgres_daily_report.sh
```

---

## 🔍 Comandos Rápidos de Referência

```bash
# Status
systemctl status postgresql

# Tamanho do banco
sudo -u postgres psql -d contabil_db -c "SELECT pg_size_pretty(pg_database_size('contabil_db'));"

# Conexões ativas
sudo -u postgres psql -d contabil_db -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'contabil_db';"

# Últimas queries
sudo -u postgres psql -d contabil_db -c "SELECT query, state, query_start FROM pg_stat_activity WHERE datname = 'contabil_db' ORDER BY query_start DESC LIMIT 5;"

# Logs
sudo tail -f /var/log/postgresql/postgresql-16-main.log

# Reiniciar PostgreSQL
sudo systemctl restart postgresql
```

---

## 📚 Recursos Adicionais

- [Documentação Oficial PostgreSQL](https://www.postgresql.org/docs/)
- [pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html)
- [Monitoramento PostgreSQL](https://www.postgresql.org/docs/current/monitoring.html)

---

**✅ Sistema de monitoramento configurado!**







