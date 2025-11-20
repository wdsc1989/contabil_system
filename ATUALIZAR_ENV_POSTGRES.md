# 🔧 Atualizar .env para PostgreSQL

Guia rápido para configurar PostgreSQL e atualizar o `.env` no servidor.

---

## 📋 Passo 1: Criar Banco e Usuário PostgreSQL

Execute no servidor:

```bash
# Conectar ao PostgreSQL
sudo -u postgres psql
```

Depois execute no psql:

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

## 📝 Passo 2: Atualizar .env

### Editar arquivo .env

```bash
cd /opt/contabil
nano .env
```

### Substituir DATABASE_URL

**ANTES (SQLite):**
```bash
DATABASE_URL=sqlite:////opt/contabil/data/contabil.db
```

**DEPOIS (PostgreSQL):**
```bash
DATABASE_URL=postgresql://contabil_user:SUA_SENHA_AQUI@localhost:5432/contabil_db
```

### Configuração Completa do .env

```bash
# Ambiente
ENVIRONMENT=production
DEBUG=False

# Banco de Dados PostgreSQL
DATABASE_URL=postgresql://contabil_user:SUA_SENHA_AQUI@localhost:5432/contabil_db

# Segurança
SECRET_KEY=GERE_UMA_CHAVE_SECRETA_ALEATORIA_AQUI_32_CARACTERES

# Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=127.0.0.1
STREAMLIT_SERVER_HEADLESS=true

# Logging
LOG_LEVEL=INFO
LOG_DIR=/var/log/contabil

# Backup
BACKUP_DIR=/var/backups/contabil/postgresql
BACKUP_RETENTION_DAYS=7

# PostgreSQL (para scripts de backup)
POSTGRES_DB=contabil_db
POSTGRES_USER=contabil_user
POSTGRES_PASSWORD=SUA_SENHA_AQUI
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### Gerar SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copie o resultado e cole no `.env` como `SECRET_KEY=...`

---

## ✅ Passo 3: Testar Conexão

```bash
cd /opt/contabil
source venv/bin/activate

python3 << 'EOF'
from config.database import engine, DATABASE_URL
from sqlalchemy import text

print(f"Banco: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✅ Conexão OK!")
        print(f"PostgreSQL: {version[:60]}...")
except Exception as e:
    print(f"❌ Erro: {e}")
EOF
```

---

## 🔄 Passo 4: Inicializar Banco

```bash
cd /opt/contabil
source venv/bin/activate

# Inicializar banco (cria todas as tabelas)
python3 init_db.py

# Criar usuário admin
python3 -c "
from config.database import SessionLocal
from services.auth_service import AuthService
db = SessionLocal()
try:
    AuthService.create_user(
        db=db,
        username='admin',
        password='SUA_SENHA_ADMIN',
        email='admin@exemplo.com',
        role='admin'
    )
    db.commit()
    print('✅ Usuário admin criado')
except Exception as e:
    print(f'⚠️  {e}')
finally:
    db.close()
"
```

---

## 🚀 Passo 5: Reiniciar Serviço

```bash
sudo systemctl restart contabil
sudo systemctl status contabil
```

---

## 📊 Verificar

```bash
# Ver logs
sudo journalctl -u contabil.service -f

# Testar aplicação
curl http://localhost:8501
```

---

## 🔐 Importante

- **Altere a senha do admin** após o primeiro login
- **Use senhas fortes** para PostgreSQL e admin
- **Mantenha o .env seguro** (não commitar no Git)

---

**Pronto! Sistema configurado com PostgreSQL! 🎉**

