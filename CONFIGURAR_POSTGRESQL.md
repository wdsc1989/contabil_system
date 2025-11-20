# 🐘 Configurar PostgreSQL em Produção

Guia para configurar PostgreSQL no servidor e atualizar o `.env`.

---

## 📋 Pré-requisitos

- PostgreSQL instalado no servidor
- Usuário e banco de dados criados
- Credenciais de acesso

---

## 🔧 Passo 1: Verificar/Criar Banco PostgreSQL

### Conectar ao PostgreSQL

```bash
# Como usuário postgres
sudo -u postgres psql

# Ou se tiver acesso direto
psql -U postgres
```

### Criar Banco e Usuário

```sql
-- Criar banco de dados
CREATE DATABASE contabil_db;

-- Criar usuário
CREATE USER contabil_user WITH PASSWORD 'SUA_SENHA_SEGURA_AQUI';

-- Dar permissões
GRANT ALL PRIVILEGES ON DATABASE contabil_db TO contabil_user;

-- Conectar ao banco e dar permissões no schema
\c contabil_db
GRANT ALL ON SCHEMA public TO contabil_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO contabil_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO contabil_user;

-- Sair
\q
```

---

## 📝 Passo 2: Configurar .env

### Editar arquivo .env

```bash
cd /opt/contabil
nano .env
```

### Configuração Completa

```bash
# Ambiente
ENVIRONMENT=production
DEBUG=False

# Banco de Dados PostgreSQL
# Formato: postgresql://usuario:senha@host:porta/database
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

# Domínio (opcional)
DOMAIN=seudominio.com
ALLOWED_HOSTS=seudominio.com,www.seudominio.com
```

### Gerar SECRET_KEY

```bash
# Gerar chave secreta aleatória
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🔄 Passo 3: Migrar Dados (se houver dados em SQLite)

Se você já tem dados em SQLite e quer migrar para PostgreSQL:

```bash
cd /opt/contabil
source venv/bin/activate

# Executar migração
python3 scripts/migrate_sqlite_to_postgres.py data/contabil.db postgresql://contabil_user:senha@localhost:5432/contabil_db
```

---

## 🆕 Passo 4: Inicializar Banco PostgreSQL

Se for começar do zero:

```bash
cd /opt/contabil
source venv/bin/activate

# Inicializar banco
python3 init_db.py

# Criar usuário admin
python3 -c "
from config.database import SessionLocal
from services.auth_service import AuthService
db = SessionLocal()
AuthService.create_user(
    db=db,
    username='admin',
    password='SUA_SENHA_ADMIN_SEGURA',
    email='admin@exemplo.com',
    role='admin'
)
db.commit()
db.close()
print('✅ Usuário admin criado')
"
```

---

## ✅ Passo 5: Verificar Configuração

```bash
# Testar conexão
cd /opt/contabil
source venv/bin/activate
python3 << 'EOF'
from config.database import engine, DATABASE_URL
from sqlalchemy import text

print(f"Banco configurado: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✅ Conexão OK!")
        print(f"PostgreSQL: {version[:50]}...")
except Exception as e:
    print(f"❌ Erro de conexão: {e}")
EOF
```

---

## 🔄 Passo 6: Reiniciar Serviço

```bash
sudo systemctl restart contabil
sudo systemctl status contabil
```

---

## 📊 Verificar Funcionamento

```bash
# Ver logs
sudo journalctl -u contabil.service -f

# Testar aplicação
curl http://localhost:8501
```

---

## 🔐 Segurança

### Alterar Senha do PostgreSQL

```sql
ALTER USER contabil_user WITH PASSWORD 'NOVA_SENHA_SEGURA';
```

### Atualizar .env

```bash
nano .env
# Atualizar POSTGRES_PASSWORD e DATABASE_URL
```

---

## 🐛 Troubleshooting

### Erro: "password authentication failed"

Verifique:
1. Senha no `.env` está correta
2. Usuário existe no PostgreSQL
3. Permissões foram concedidas

### Erro: "database does not exist"

```sql
CREATE DATABASE contabil_db;
GRANT ALL PRIVILEGES ON DATABASE contabil_db TO contabil_user;
```

### Erro: "permission denied"

```sql
\c contabil_db
GRANT ALL ON SCHEMA public TO contabil_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO contabil_user;
```

---

## 📝 Checklist

- [ ] PostgreSQL instalado
- [ ] Banco `contabil_db` criado
- [ ] Usuário `contabil_user` criado
- [ ] Permissões concedidas
- [ ] `.env` configurado com `DATABASE_URL` PostgreSQL
- [ ] `SECRET_KEY` gerada
- [ ] Conexão testada
- [ ] Serviço reiniciado
- [ ] Aplicação funcionando

---

**Pronto! Sistema configurado com PostgreSQL! 🎉**

