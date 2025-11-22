# 🚀 Quick Start - Deploy Rápido

Guia resumido para deploy rápido na VPS Hostinger.

## ⚠️ IMPORTANTE: Onde Executar Cada Comando

- **Windows PowerShell:** Comandos para preparação local
- **VPS (SSH):** Comandos para execução no servidor

---

## 📋 Passo a Passo Rápido

### 1️⃣ Preparação no Windows

```powershell
# No Windows PowerShell
cd C:\Users\DELL\Documents\Projetos\Contabil\contabil_system

# 1. Faça commit e push do código
git add .
git commit -m "Preparação para deploy"
git push origin main

# 2. (Opcional) Faça backup do SQLite
# Se tiver Git Bash ou WSL:
# bash scripts/backup_sqlite.sh
# Ou copie manualmente: data\contabil.db
```

### 2️⃣ Conectar na VPS

```powershell
# No Windows PowerShell
ssh root@72.61.56.204
# Digite a senha quando solicitado
```

### 3️⃣ Setup Inicial da VPS

```bash
# Na VPS (após conectar via SSH)
cd /tmp
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git temp_setup
cd temp_setup/contabil_system
chmod +x deploy/setup_vps_hostinger.sh
bash deploy/setup_vps_hostinger.sh

# ⚠️ ANOTE AS CREDENCIAIS DO BANCO QUE SERÃO EXIBIDAS!
```

### 4️⃣ Clonar Repositório Definitivo

```bash
# Na VPS
cd /opt
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git contabil
cd contabil/contabil_system
chown -R contabil:contabil /opt/contabil
```

### 5️⃣ Configurar Variáveis de Ambiente

```bash
# Na VPS
cd /opt/contabil/contabil_system
cp env.example.txt .env
nano .env

# Configure:
# - DATABASE_URL com as credenciais anotadas no passo 3
# - SECRET_KEY (gere uma chave aleatória)
# - POSTGRES_PASSWORD com a senha anotada
```

### 6️⃣ (Opcional) Transferir Banco SQLite do Windows

```powershell
# No Windows PowerShell (em outra janela/terminal)
scp "C:/Users/DELL/Documents/Projetos/Contabil/contabil_system/data/contabil.db" root@72.61.56.204:/tmp/
```

### 7️⃣ Migrar Dados (se transferiu o banco)

```bash
# Na VPS
cd /opt/contabil/contabil_system
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Executa migração (use a senha anotada no passo 3)
python scripts/migrate_sqlite_to_postgres.py \
    /tmp/contabil.db \
    "postgresql://contabil_user:SUA_SENHA@localhost:5432/contabil_db"
```

### 8️⃣ Configurar Serviço Systemd

```bash
# Na VPS
cp /opt/contabil/contabil_system/deploy/systemd/contabil.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable contabil.service
systemctl start contabil.service
systemctl status contabil.service
```

### 9️⃣ Configurar Nginx

```bash
# Na VPS
cp /opt/contabil/contabil_system/deploy/nginx/contabil.conf /etc/nginx/sites-available/contabil
nano /etc/nginx/sites-available/contabil
# Altere "server_name _;" para seu domínio

ln -s /etc/nginx/sites-available/contabil /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

### 🔟 Configurar SSL

```bash
# Na VPS
certbot --nginx -d seudominio.com -d www.seudominio.com --email seuemail@exemplo.com --agree-tos --non-interactive
```

### 1️⃣1️⃣ Configurar Backups Automáticos

```bash
# Na VPS
crontab -e -u contabil

# Adicione:
0 2 * * * /opt/contabil/contabil_system/scripts/backup_postgres.sh daily >> /var/log/contabil/backup.log 2>&1
0 1 * * 0 /opt/contabil/contabil_system/scripts/backup_postgres.sh weekly >> /var/log/contabil/backup.log 2>&1
0 0 1 * * /opt/contabil/contabil_system/scripts/backup_postgres.sh monthly >> /var/log/contabil/backup.log 2>&1
```

---

## ✅ Verificação Final

```bash
# Na VPS
# Verifica se o serviço está rodando
systemctl status contabil.service

# Verifica logs
journalctl -u contabil.service -f

# Testa aplicação
curl http://localhost:8501

# Verifica Nginx
systemctl status nginx
```

---

## 🔧 Comandos Úteis

### Reiniciar Aplicação
```bash
systemctl restart contabil.service
```

### Ver Logs
```bash
journalctl -u contabil.service -f
```

### Atualizar Código
```bash
cd /opt/contabil/contabil_system
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart contabil.service
```

### Backup Manual
```bash
cd /opt/contabil/contabil_system
bash scripts/backup_postgres.sh daily
```

---

## 📚 Documentação Completa

Para mais detalhes, consulte:
- [Guia Completo de Deploy](HOSTINGER_DEPLOY.md)
- [Guia de Backup e Restauração](BACKUP_GUIDE.md)









