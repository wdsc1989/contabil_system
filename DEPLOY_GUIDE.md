# 🚀 Guia Rápido de Deploy para Produção

## 📋 Checklist Pré-Deploy

Antes de começar, certifique-se de que:

- [ ] Código commitado e enviado para o GitHub
- [ ] Servidor VPS configurado e acessível via SSH
- [ ] PostgreSQL instalado e configurado no servidor
- [ ] Credenciais de acesso ao servidor (IP, usuário, senha)

---

## 🆕 Primeiro Deploy (Setup Inicial)

### Passo 1: Conectar ao Servidor

```bash
ssh root@SEU_IP_SERVIDOR
# Exemplo: ssh root@72.61.56.204
```

### Passo 2: Executar Script de Setup

```bash
# 1. Clonar repositório
cd /opt
git clone git@github.com:wdsc1989/contabil_system.git contabil
cd contabil

# 2. Executar script de setup
sudo bash deploy/setup_vps_hostinger.sh
```

O script irá:
- Instalar dependências do sistema
- Configurar PostgreSQL
- Configurar Nginx
- Configurar systemd service
- Criar usuário do sistema

### Passo 3: Configurar Variáveis de Ambiente

```bash
# 1. Copiar arquivo de exemplo
cp env.example.txt .env

# 2. Editar variáveis
nano .env
```

**Configurações importantes:**
- `DATABASE_URL`: URL de conexão com PostgreSQL
- `SECRET_KEY`: Chave secreta aleatória
- `POSTGRES_PASSWORD`: Senha do banco de dados

### Passo 4: Inicializar Banco de Dados

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate

# 2. Inicializar banco
python init_db.py

# 3. Criar usuário admin
python -c "
from config.database import SessionLocal
from services.auth_service import AuthService
db = SessionLocal()
AuthService.create_user(
    db=db,
    username='admin',
    password='SUA_SENHA_SEGURA',
    email='admin@exemplo.com',
    role='admin'
)
db.commit()
db.close()
"
```

### Passo 5: Iniciar Serviço

```bash
# 1. Recarregar systemd
sudo systemctl daemon-reload

# 2. Iniciar serviço
sudo systemctl start contabil

# 3. Habilitar no boot
sudo systemctl enable contabil

# 4. Verificar status
sudo systemctl status contabil
```

### Passo 6: Verificar Funcionamento

```bash
# Ver logs
sudo journalctl -u contabil -f

# Testar acesso
curl http://localhost:8501
```

**Acesse no navegador:** `http://SEU_IP:8501`

---

## 🔄 Deploy de Atualização (Código Já no Servidor)

### Opção 1: Deploy Automatizado (Recomendado)

```bash
# Conectar ao servidor
ssh root@SEU_IP_SERVIDOR

# Ir para diretório da aplicação
cd /opt/contabil

# Executar script de deploy
bash deploy/deploy.sh
```

O script irá:
- Fazer backup do banco
- Atualizar código (git pull)
- Atualizar dependências
- Reiniciar serviço
- Verificar status

### Opção 2: Deploy Manual

```bash
# 1. Conectar ao servidor
ssh root@SEU_IP_SERVIDOR

# 2. Ir para diretório
cd /opt/contabil

# 3. Fazer backup (recomendado)
bash scripts/backup_postgres.sh

# 4. Atualizar código
git pull origin main

# 5. Ativar ambiente virtual
source venv/bin/activate

# 6. Atualizar dependências
pip install -r requirements.txt

# 7. Executar migrações (se houver)
# python scripts/migrate_xxx.py

# 8. Reiniciar serviço
sudo systemctl restart contabil

# 9. Verificar logs
sudo journalctl -u contabil -f
```

### Opção 3: Deploy via Script Windows (Local)

Execute no Windows:

```bash
deploy_production_interactive.bat
```

O script irá:
- Conectar ao servidor via SSH
- Executar o deploy automaticamente
- Mostrar status e logs

---

## 🔍 Verificação Pós-Deploy

### 1. Verificar Status do Serviço

```bash
sudo systemctl status contabil
```

**Deve mostrar:** `Active: active (running)`

### 2. Verificar Logs

```bash
sudo journalctl -u contabil -n 50
```

**Procurar por:**
- ✅ "You can now view your Streamlit app"
- ❌ Erros de conexão com banco
- ❌ Erros de importação

### 3. Testar Aplicação

```bash
# Via curl
curl http://localhost:8501

# Ou acesse no navegador
# http://SEU_IP:8501
```

### 4. Verificar Banco de Dados

```bash
# Conectar ao PostgreSQL
psql -U contabil_user -d contabil_db

# Verificar tabelas
\dt

# Sair
\q
```

---

## 🐛 Troubleshooting

### Serviço Não Inicia

```bash
# Ver logs de erro
sudo journalctl -u contabil -n 100

# Verificar se porta está em uso
sudo netstat -tulpn | grep 8501

# Verificar permissões
ls -la /opt/contabil
```

### Erro de Conexão com Banco

```bash
# Testar conexão
psql -U contabil_user -d contabil_db -h localhost

# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar .env
cat /opt/contabil/.env | grep DATABASE_URL
```

### Erro 502 Bad Gateway (Nginx)

```bash
# Ver logs do Nginx
sudo tail -f /var/log/nginx/error.log

# Verificar se serviço está rodando
sudo systemctl status contabil

# Testar configuração
sudo nginx -t
```

---

## 📞 Comandos Úteis

### Gerenciar Serviço

```bash
# Iniciar
sudo systemctl start contabil

# Parar
sudo systemctl stop contabil

# Reiniciar
sudo systemctl restart contabil

# Status
sudo systemctl status contabil

# Logs em tempo real
sudo journalctl -u contabil -f
```

### Backup

```bash
# Backup manual
bash scripts/backup_postgres.sh

# Restaurar backup
bash scripts/restore_postgres.sh backup_file.dump
```

### Atualizar Código

```bash
cd /opt/contabil
git pull origin main
bash deploy/deploy.sh
```

---

## ✅ Checklist Pós-Deploy

- [ ] Serviço está rodando
- [ ] Aplicação responde no navegador
- [ ] Login funciona
- [ ] Banco de dados conectado
- [ ] Logs sem erros críticos
- [ ] Backup configurado

---

**Pronto! Sistema em produção! 🎉**

Para mais detalhes, consulte: `docs/TUTORIAL_DEPLOY_PRODUCAO.md`

