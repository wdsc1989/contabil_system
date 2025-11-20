#!/bin/bash
# Script para configurar PostgreSQL e criar banco/usuário
# Uso: sudo bash scripts/configurar_postgres.sh

set -e

echo "=" * 70
echo "🐘 CONFIGURAÇÃO DO POSTGRESQL"
echo "=" * 70
echo ""

# Solicitar informações
read -p "Nome do banco de dados [contabil_db]: " DB_NAME
DB_NAME=${DB_NAME:-contabil_db}

read -p "Nome do usuário [contabil_user]: " DB_USER
DB_USER=${DB_USER:-contabil_user}

read -sp "Senha do usuário: " DB_PASSWORD
echo ""

read -p "Host [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Porta [5432]: " DB_PORT
DB_PORT=${DB_PORT:-5432}

echo ""
echo "Criando banco de dados e usuário..."

# Criar banco e usuário
sudo -u postgres psql << EOF
-- Criar banco
CREATE DATABASE ${DB_NAME};

-- Criar usuário
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';

-- Permissões
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};

-- Conectar e dar permissões no schema
\c ${DB_NAME}
GRANT ALL ON SCHEMA public TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${DB_USER};
EOF

echo ""
echo "✅ Banco e usuário criados!"
echo ""
echo "📝 Adicione ao .env:"
echo "DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo "POSTGRES_DB=${DB_NAME}"
echo "POSTGRES_USER=${DB_USER}"
echo "POSTGRES_PASSWORD=${DB_PASSWORD}"
echo "POSTGRES_HOST=${DB_HOST}"
echo "POSTGRES_PORT=${DB_PORT}"
echo ""

