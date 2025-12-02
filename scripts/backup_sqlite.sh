#!/bin/bash
# Script de backup do banco de dados SQLite local
# Uso: ./backup_sqlite.sh [caminho_do_banco] [diretorio_destino]

set -e  # Para na primeira erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configurações padrão
DB_PATH="${1:-data/contabil.db}"
BACKUP_DIR="${2:-backups/sqlite}"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.db"

# Verifica se o banco existe
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}❌ Erro: Banco de dados não encontrado em $DB_PATH${NC}"
    exit 1
fi

# Cria diretório de backup se não existir
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}📦 Iniciando backup do SQLite...${NC}"
echo "Banco de origem: $DB_PATH"
echo "Destino: $BACKUP_FILE"

# Faz backup usando sqlite3
if command -v sqlite3 &> /dev/null; then
    # Usa .backup do sqlite3 (método recomendado)
    sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"
    
    if [ $? -eq 0 ]; then
        # Compacta o backup
        echo -e "${YELLOW}🗜️  Compactando backup...${NC}"
        gzip -f "$BACKUP_FILE"
        BACKUP_FILE="${BACKUP_FILE}.gz"
        
        # Obtém tamanho do arquivo
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        
        echo -e "${GREEN}✅ Backup criado com sucesso!${NC}"
        echo "Arquivo: $BACKUP_FILE"
        echo "Tamanho: $SIZE"
        echo "Data: $(date)"
        
        # Lista os últimos 5 backups
        echo -e "\n${YELLOW}📋 Últimos 5 backups:${NC}"
        ls -lh "$BACKUP_DIR"/*.db.gz 2>/dev/null | tail -5 | awk '{print $9, "(" $5 ")"}'
    else
        echo -e "${RED}❌ Erro ao criar backup${NC}"
        exit 1
    fi
else
    # Fallback: copia o arquivo diretamente
    echo -e "${YELLOW}⚠️  sqlite3 não encontrado, usando cópia direta...${NC}"
    cp "$DB_PATH" "$BACKUP_FILE"
    gzip -f "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ Backup criado com sucesso!${NC}"
    echo "Arquivo: $BACKUP_FILE"
    echo "Tamanho: $SIZE"
fi

# Limpa backups antigos (mantém últimos 10)
echo -e "\n${YELLOW}🧹 Limpando backups antigos (mantendo últimos 10)...${NC}"
ls -t "$BACKUP_DIR"/*.db.gz 2>/dev/null | tail -n +11 | xargs -r rm -f

echo -e "${GREEN}✅ Processo de backup concluído!${NC}"















