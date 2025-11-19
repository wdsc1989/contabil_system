# 🚀 Guia Completo de Deploy - Hostinger VPS

Este guia fornece instruções passo a passo para fazer deploy do Sistema Contábil em uma VPS Hostinger com Ubuntu 24.04 LTS.

## 📋 Pré-requisitos

- VPS Hostinger com Ubuntu 24.04 LTS
- Acesso SSH com privilégios de root
- Domínio configurado apontando para o IP da VPS (opcional, mas recomendado)
- Repositório GitHub do projeto

## 🎯 Visão Geral do Processo

1. **Preparação Local** - Backup do SQLite e preparação do código
2. **Setup da VPS** - Configuração inicial do servidor
3. **Instalação do PostgreSQL** - Configuração do banco de dados
4. **Migração de Dados** - Transferência do SQLite para PostgreSQL
5. **Deploy da Aplicação** - Instalação e configuração
6. **Configuração de Produção** - Nginx, SSL, systemd
7. **Sistema de Backup** - Configuração de backups automáticos

---

## 📦 FASE 1: Preparação Local

### 1.1 Backup do SQLite Local

**IMPORTANTE: Faça backup ANTES de qualquer coisa!**

```bash
# No seu computador local
cd Contabil/contabil_system

# Executa o script de backup
bash scripts/backup_sqlite.sh

# O backup será salvo em: backups/sqlite/backup_YYYY-MM-DD_HH-MM-SS.db.gz
```

### 1.2 Verificar Código no GitHub

```bash
# Certifique-se de que todo o código está commitado e pushado
git status
git add .
git commit -m "Preparação para deploy em produção"
git push origin main
```

### 1.3 Preparar Credenciais

Anote as seguintes informações (você precisará delas):
- URL do repositório GitHub
- Domínio (se tiver)
- Email para certificado SSL

---

## 🖥️ FASE 2: Setup Inicial da VPS

### 2.1 Conectar na VPS

```bash
# Conecte via SSH (substitua pelo IP da sua VPS)
ssh root@SEU_IP_VPS

# Ou se usar chave SSH
ssh -i ~/.ssh/sua_chave root@SEU_IP_VPS
```

### 2.2 Executar Script de Setup

```bash
# Clone o repositório temporariamente para obter os scripts
cd /tmp
git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git temp_setup
cd temp_setup/contabil_system

# Torna o script executável
chmod +x deploy/setup_vps_hostinger.sh

# Execute o script (como root)
sudo bash deploy/setup_vps_hostinger.sh
```

O script irá:
- ✅ Atualizar o sistema
- ✅ Instalar Python 3.12
- ✅ Instalar PostgreSQL 16
- ✅ Instalar Nginx
- ✅ Instalar Certbot (Let's Encrypt)
- ✅ Configurar firewall (UFW)
- ✅ Criar usuário da aplicação
- ✅ Criar diretórios necessários
- ✅ Configurar PostgreSQL com banco e usuário

**⚠️ IMPORTANTE: Anote as credenciais do banco de dados que serão exibidas!**

### 2.3 Verificar Instalações

```bash
# Verifica Python
python3.12 --version

# Verifica PostgreSQL
sudo systemctl status postgresql

# Verifica Nginx
sudo systemctl status nginx

# Verifica firewall
sudo ufw status
```

---

## 🗄️ FASE 3: Configuração do PostgreSQL

### 3.1 Credenciais do Banco

O script de setup já criou o banco. Use as credenciais exibidas:

```
Database: contabil_db
User: contabil_user
Password: [senha gerada]
```

### 3.2 Testar Conexão

```bash
# Conecta ao PostgreSQL
sudo -u postgres psql -d contabil_db -U contabil_user

# Testa uma query simples
SELECT version();

# Sai do psql
\q
```

---

## 📤 FASE 4: Migração de Dados

### 4.1 Preparar Arquivo de Backup Local

No seu computador local, certifique-se de ter o backup do SQLite:

```bash
# Lista os backups disponíveis
ls -lh backups/sqlite/
```

### 4.2 Transferir Backup para VPS

```bash
# No seu computador local, transfere o backup
scp backups/sqlite/backup_*.db.gz root@SEU_IP_VPS:/tmp/
```

### 4.3 Clonar Repositório na VPS

```bash
# Na VPS, clone o repositório
cd /opt
sudo git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git contabil
cd contabil/contabil_system

# Ajusta permissões
sudo chown -R contabil:contabil /opt/contabil
```

### 4.4 Configurar Variáveis de Ambiente

```bash
# Cria arquivo .env
sudo -u contabil cp env.example.txt .env
sudo -u contabil nano .env
```

Configure as seguintes variáveis:

```env
ENVIRONMENT=production
DEBUG=False

# Use as credenciais geradas pelo setup
DATABASE_URL=postgresql://contabil_user:SUA_SENHA@localhost:5432/contabil_db

# Gere uma chave secreta aleatória
SECRET_KEY=$(openssl rand -hex 32)

STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=127.0.0.1
STREAMLIT_SERVER_HEADLESS=true

# Para scripts de backup
POSTGRES_DB=contabil_db
POSTGRES_USER=contabil_user
POSTGRES_PASSWORD=SUA_SENHA
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 4.5 Executar Migração

```bash
# Ativa ambiente virtual
cd /opt/contabil/contabil_system
sudo -u contabil python3.12 -m venv venv
sudo -u contabil source venv/bin/activate

# Instala dependências
sudo -u contabil pip install -r requirements.txt

# Descompacta backup do SQLite (se necessário)
cd /tmp
gunzip backup_*.db.gz
SQLITE_BACKUP=/tmp/backup_*.db

# Executa migração
cd /opt/contabil/contabil_system
sudo -u contabil python scripts/migrate_sqlite_to_postgres.py \
    "$SQLITE_BACKUP" \
    "postgresql://contabil_user:SUA_SENHA@localhost:5432/contabil_db"
```

### 4.6 Validar Migração

```bash
# Conecta ao PostgreSQL e verifica dados
sudo -u postgres psql -d contabil_db

# Conta registros em algumas tabelas
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM clients;
SELECT COUNT(*) FROM transactions;

# Sai
\q
```

### 4.7 Backup Imediato Após Migração

```bash
# Cria backup imediato do PostgreSQL
cd /opt/contabil/contabil_system
sudo -u contabil bash scripts/backup_postgres.sh daily
```

---

## 🚀 FASE 5: Deploy da Aplicação

### 5.1 Configurar Serviço Systemd

```bash
# Copia arquivo de serviço
sudo cp /opt/contabil/contabil_system/deploy/systemd/contabil.service /etc/systemd/system/

# Recarrega systemd
sudo systemctl daemon-reload

# Habilita serviço para iniciar no boot
sudo systemctl enable contabil.service

# Inicia serviço
sudo systemctl start contabil.service

# Verifica status
sudo systemctl status contabil.service
```

### 5.2 Verificar Logs

```bash
# Ver logs em tempo real
sudo journalctl -u contabil.service -f

# Ver últimas 50 linhas
sudo journalctl -u contabil.service -n 50
```

### 5.3 Testar Aplicação

```bash
# Testa se está respondendo
curl http://localhost:8501

# Ou acesse via navegador (se tiver acesso)
# http://SEU_IP_VPS:8501
```

---

## 🌐 FASE 6: Configuração Nginx e SSL

### 6.1 Configurar Nginx

```bash
# Copia configuração do Nginx
sudo cp /opt/contabil/contabil_system/deploy/nginx/contabil.conf /etc/nginx/sites-available/contabil

# Edita e configura o domínio
sudo nano /etc/nginx/sites-available/contabil

# Substitua "server_name _;" pelo seu domínio
# server_name seudominio.com www.seudominio.com;

# Cria link simbólico
sudo ln -s /etc/nginx/sites-available/contabil /etc/nginx/sites-enabled/

# Remove configuração padrão (opcional)
sudo rm /etc/nginx/sites-enabled/default

# Testa configuração
sudo nginx -t

# Recarrega Nginx
sudo systemctl reload nginx
```

### 6.2 Configurar SSL com Let's Encrypt

```bash
# Instala certificado SSL (substitua pelo seu domínio e email)
sudo certbot --nginx -d seudominio.com -d www.seudominio.com --email seuemail@exemplo.com --agree-tos --non-interactive

# Testa renovação automática
sudo certbot renew --dry-run
```

### 6.3 Verificar Acesso

Acesse no navegador:
- `https://seudominio.com` (ou `https://SEU_IP_VPS`)

---

## 💾 FASE 7: Sistema de Backup Automático

### 7.1 Configurar Backups Diários

```bash
# Edita crontab do usuário contabil
sudo -u contabil crontab -e

# Adiciona as seguintes linhas:

# Backup diário às 2:00 AM
0 2 * * * /opt/contabil/contabil_system/scripts/backup_postgres.sh daily >> /var/log/contabil/backup.log 2>&1

# Backup semanal aos domingos às 1:00 AM
0 1 * * 0 /opt/contabil/contabil_system/scripts/backup_postgres.sh weekly >> /var/log/contabil/backup.log 2>&1

# Backup mensal no dia 1 às 00:00
0 0 1 * * /opt/contabil/contabil_system/scripts/backup_postgres.sh monthly >> /var/log/contabil/backup.log 2>&1
```

### 7.2 Testar Backup Manual

```bash
# Testa backup manual
cd /opt/contabil/contabil_system
sudo -u contabil bash scripts/backup_postgres.sh daily

# Verifica se foi criado
ls -lh /var/backups/contabil/postgresql/daily/
```

### 7.3 Verificar Logs de Backup

```bash
# Ver logs de backup
tail -f /var/log/contabil/backup.log
```

---

## 🔄 Comandos Úteis

### Gerenciar Aplicação

```bash
# Status do serviço
sudo systemctl status contabil.service

# Reiniciar aplicação
sudo systemctl restart contabil.service

# Parar aplicação
sudo systemctl stop contabil.service

# Iniciar aplicação
sudo systemctl start contabil.service

# Ver logs
sudo journalctl -u contabil.service -f
```

### Gerenciar Banco de Dados

```bash
# Conectar ao PostgreSQL
sudo -u postgres psql -d contabil_db

# Backup manual
cd /opt/contabil/contabil_system
sudo -u contabil bash scripts/backup_postgres.sh daily

# Restaurar backup
sudo -u contabil bash scripts/restore_postgres.sh /caminho/do/backup.sql.gz --confirm
```

### Atualizar Aplicação

```bash
# Usa o script de deploy
cd /opt/contabil/contabil_system
sudo -u contabil bash deploy/deploy.sh main

# Ou manualmente:
cd /opt/contabil/contabil_system
sudo -u contabil git pull origin main
sudo -u contabil source venv/bin/activate
sudo -u contabil pip install -r requirements.txt
sudo systemctl restart contabil.service
```

---

## 🛠️ Troubleshooting

### Aplicação não inicia

```bash
# Verifica logs
sudo journalctl -u contabil.service -n 100

# Verifica se o arquivo .env existe e está correto
sudo -u contabil cat /opt/contabil/contabil_system/.env

# Testa conexão com banco
sudo -u contabil psql -h localhost -U contabil_user -d contabil_db
```

### Erro de permissões

```bash
# Ajusta permissões
sudo chown -R contabil:contabil /opt/contabil
sudo chown -R contabil:contabil /var/log/contabil
sudo chown -R contabil:contabil /var/backups/contabil
```

### Nginx não funciona

```bash
# Testa configuração
sudo nginx -t

# Verifica logs
sudo tail -f /var/log/nginx/contabil_error.log

# Verifica se Streamlit está rodando
curl http://localhost:8501
```

### Backup não funciona

```bash
# Verifica variáveis de ambiente
sudo -u contabil env | grep POSTGRES

# Testa conexão manual
sudo -u contabil PGPASSWORD=senha pg_dump -h localhost -U contabil_user -d contabil_db > /tmp/test.sql
```

---

## 📚 Próximos Passos

1. **Monitoramento** - Configure alertas e monitoramento
2. **Domínio** - Configure DNS apontando para a VPS
3. **Email** - Configure notificações por email
4. **CDN** - Configure CDN para assets estáticos (opcional)
5. **CI/CD** - Configure GitHub Actions para deploy automático (opcional)

---

## 🔒 Segurança

- ✅ Firewall configurado (UFW)
- ✅ SSL/HTTPS obrigatório
- ✅ Fail2ban ativo
- ✅ Atualizações automáticas de segurança
- ✅ Usuário não-root para aplicação
- ✅ Senhas fortes
- ✅ Backups automáticos

---

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs: `journalctl -u contabil.service -f`
2. Verifique a documentação: `docs/deploy/BACKUP_GUIDE.md`
3. Consulte os logs do Nginx: `/var/log/nginx/contabil_error.log`

---

**✅ Deploy concluído com sucesso!**

