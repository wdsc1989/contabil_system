#!/bin/bash
# Script de backup automático do PostgreSQL
# Configurado para ser executado via cron diariamente
# Uso: ./backup_postgres.sh [tipo] onde tipo = daily|weekly|monthly

set -e  # Para na primeira erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configurações
BACKUP_TYPE="${1:-daily}"  # daily, weekly, monthly
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
DATE_ONLY=$(date +"%Y-%m-%d")

# Diretórios de backup
BASE_BACKUP_DIR="/var/backups/contabil/postgresql"
DAILY_DIR="${BASE_BACKUP_DIR}/daily"
WEEKLY_DIR="${BASE_BACKUP_DIR}/weekly"
MONTHLY_DIR="${BASE_BACKUP_DIR}/monthly"

# Configurações do banco (via variáveis de ambiente ou padrão)
DB_NAME="${POSTGRES_DB:-contabil_db}"
DB_USER="${POSTGRES_USER:-contabil_user}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

# Define diretório baseado no tipo
case $BACKUP_TYPE in
    daily)
        BACKUP_DIR="$DAILY_DIR"
        RETENTION_DAYS=7
        ;;
    weekly)
        BACKUP_DIR="$WEEKLY_DIR"
        RETENTION_DAYS=28  # 4 semanas
        ;;
    monthly)
        BACKUP_DIR="$MONTHLY_DIR"
        RETENTION_DAYS=365  # 12 meses
        ;;
    *)
        echo -e "${RED}❌ Tipo de backup inválido: $BACKUP_TYPE${NC}"
        echo "Use: daily, weekly ou monthly"
        exit 1
        ;;
esac

# Cria diretórios se não existirem
mkdir -p "$BACKUP_DIR"
mkdir -p "$DAILY_DIR" "$WEEKLY_DIR" "$MONTHLY_DIR"

# Nome do arquivo de backup
BACKUP_FILE="${BACKUP_DIR}/backup_${BACKUP_TYPE}_${TIMESTAMP}.sql"
BACKUP_FILE_GZ="${BACKUP_FILE}.gz"

echo -e "${YELLOW}📦 Iniciando backup $BACKUP_TYPE do PostgreSQL...${NC}"
echo "Banco: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "Destino: $BACKUP_FILE_GZ"
echo "Data: $(date)"

# Verifica se pg_dump está disponível
if ! command -v pg_dump &> /dev/null; then
    echo -e "${RED}❌ Erro: pg_dump não encontrado. Instale o PostgreSQL client.${NC}"
    exit 1
fi

# Solicita senha via variável de ambiente ou arquivo .pgpass
export PGPASSWORD="${POSTGRES_PASSWORD}"

# Cria backup
echo -e "${YELLOW}🔄 Criando dump do banco de dados...${NC}"
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --verbose \
    --format=plain \
    --no-owner \
    --no-acl \
    --file="$BACKUP_FILE" 2>&1; then
    
    # Verifica se o arquivo foi criado e tem conteúdo
    if [ ! -s "$BACKUP_FILE" ]; then
        echo -e "${RED}❌ Erro: Arquivo de backup está vazio${NC}"
        rm -f "$BACKUP_FILE"
        exit 1
    fi
    
    # Compacta o backup
    echo -e "${YELLOW}🗜️  Compactando backup...${NC}"
    gzip -f "$BACKUP_FILE"
    
    # Verifica integridade do arquivo compactado
    if ! gzip -t "$BACKUP_FILE_GZ" 2>/dev/null; then
        echo -e "${RED}❌ Erro: Arquivo de backup corrompido${NC}"
        rm -f "$BACKUP_FILE_GZ"
        exit 1
    fi
    
    # Obtém tamanho do arquivo
    SIZE=$(du -h "$BACKUP_FILE_GZ" | cut -f1)
    
    # Calcula hash MD5 para verificação de integridade
    MD5_HASH=$(md5sum "$BACKUP_FILE_GZ" | cut -d' ' -f1)
    echo "$MD5_HASH" > "${BACKUP_FILE_GZ}.md5"
    
    echo -e "${GREEN}✅ Backup criado com sucesso!${NC}"
    echo "Arquivo: $BACKUP_FILE_GZ"
    echo "Tamanho: $SIZE"
    echo "MD5: $MD5_HASH"
    echo "Data: $(date)"
    
    # Limpa backups antigos
    echo -e "\n${YELLOW}🧹 Limpando backups antigos (mantendo últimos $RETENTION_DAYS dias)...${NC}"
    find "$BACKUP_DIR" -name "backup_${BACKUP_TYPE}_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "backup_${BACKUP_TYPE}_*.sql.gz.md5" -type f -mtime +$RETENTION_DAYS -delete
    
    # Lista backups recentes
    echo -e "\n${YELLOW}📋 Últimos 5 backups $BACKUP_TYPE:${NC}"
    ls -lh "$BACKUP_DIR"/backup_${BACKUP_TYPE}_*.sql.gz 2>/dev/null | tail -5 | awk '{print $9, "(" $5 ")"}'
    
    # Estatísticas
    TOTAL_BACKUPS=$(ls -1 "$BACKUP_DIR"/backup_${BACKUP_TYPE}_*.sql.gz 2>/dev/null | wc -l)
    TOTAL_SIZE=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
    echo -e "\n${GREEN}📊 Estatísticas:${NC}"
    echo "Total de backups $BACKUP_TYPE: $TOTAL_BACKUPS"
    echo "Tamanho total: $TOTAL_SIZE"
    
    echo -e "\n${GREEN}✅ Processo de backup concluído!${NC}"
    exit 0
else
    echo -e "${RED}❌ Erro ao criar backup${NC}"
    rm -f "$BACKUP_FILE"
    exit 1
fi















