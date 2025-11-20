# 🚀 Atualizar .env no Servidor - Guia Rápido

## Passo 1: Instalar python-dotenv

```bash
cd /opt/contabil
source venv/bin/activate
pip install python-dotenv
```

## Passo 2: Atualizar .env

Execute o script interativo:

```bash
python3 scripts/atualizar_env_postgres.py
```

O script irá:
- ✅ Verificar se o arquivo `.env` existe
- ✅ Solicitar informações do PostgreSQL (usuário, senha, banco, host, porta)
- ✅ Atualizar o `DATABASE_URL` e outras variáveis
- ✅ Gerar uma `SECRET_KEY` se necessário

**OU** edite manualmente:

```bash
nano .env
```

Altere a linha:
```bash
DATABASE_URL=sqlite:////opt/contabil/data/contabil.db
```

Para:
```bash
DATABASE_URL=postgresql://contabil_user:SUA_SENHA@localhost:5432/contabil_db
```

## Passo 3: Verificar Configuração

```bash
python3 scripts/verificar_env.py
```

Este script irá:
- ✅ Verificar se o `.env` está correto
- ✅ Testar a conexão com o banco
- ✅ Listar as tabelas existentes

## Passo 4: Reiniciar o Serviço

```bash
sudo systemctl restart contabil
sudo systemctl status contabil
```

## Passo 5: Verificar Logs

```bash
sudo journalctl -u contabil -f
```

---

## ⚠️ Se o PostgreSQL ainda não estiver configurado:

### Criar Banco e Usuário PostgreSQL

```bash
sudo -u postgres psql
```

No psql, execute:

```sql
-- Criar banco de dados
CREATE DATABASE contabil_db;

-- Criar usuário
CREATE USER contabil_user WITH PASSWORD 'SUA_SENHA_SEGURA_AQUI';

-- Dar permissões
GRANT ALL PRIVILEGES ON DATABASE contabil_db TO contabil_user;

-- Conectar ao banco
\c contabil_db

-- Dar permissões no schema
GRANT ALL ON SCHEMA public TO contabil_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO contabil_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO contabil_user;

-- Sair
\q
```

---

## 🔍 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'dotenv'"
```bash
source venv/bin/activate
pip install python-dotenv
```

### Erro: "connection refused" ou "authentication failed"
- Verifique se o PostgreSQL está rodando: `sudo systemctl status postgresql`
- Verifique se o usuário e senha estão corretos
- Verifique se o banco de dados existe

### Ainda está usando SQLite após atualizar .env
- Verifique se o arquivo `.env` está no diretório correto: `/opt/contabil/.env`
- Reinicie o serviço: `sudo systemctl restart contabil`
- Verifique os logs: `sudo journalctl -u contabil -n 50`

