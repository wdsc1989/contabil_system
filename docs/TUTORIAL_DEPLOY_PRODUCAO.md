# 🚀 Tutorial de Deploy e Manutenção em Produção

Guia completo para deploy, manutenção e atualização do sistema em ambiente de produção.

---

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Configuração Inicial do Repositório](#configuração-inicial-do-repositório)
3. [Deploy Inicial](#deploy-inicial)
4. [Workflow de Atualização](#workflow-de-atualização)
5. [Backup e Restauração](#backup-e-restauração)
6. [Monitoramento](#monitoramento)
7. [Troubleshooting](#troubleshooting)
8. [Manutenção Regular](#manutenção-regular)

---

## 1️⃣ Pré-requisitos

### 1.1 Servidor VPS

- **Sistema Operacional:** Ubuntu 20.04+ ou Debian 11+
- **Recursos Mínimos:**
  - 2 CPU cores
  - 4GB RAM
  - 20GB SSD
- **Acesso:** SSH com chave pública

### 1.2 Conta GitHub

- Repositório criado
- Acesso SSH configurado
- Permissões de push/pull

### 1.3 Banco de Dados

- **PostgreSQL 14+** instalado e configurado
- Usuário e banco de dados criados
- Credenciais de acesso

### 1.4 Domínio (Opcional)

- Domínio configurado
- DNS apontando para o servidor
- Certificado SSL (Let's Encrypt)

---

## 2️⃣ Configuração Inicial do Repositório

### 2.1 Estrutura do Repositório

O repositório deve conter:

```
contabil_system/
├── app.py
├── requirements.txt
├── .gitignore
├── config/
├── models/
├── pages/
├── services/
├── utils/
├── scripts/
│   ├── migrate_sqlite_to_postgres.py
│   ├── backup_postgres.sh
│   ├── restore_postgres.sh
│   └── seed_example_client.py
├── deploy/
│   ├── deploy.sh
│   ├── setup_vps_hostinger.sh
│   ├── nginx/
│   └── systemd/
└── docs/
```

### 2.2 Arquivos Essenciais no .gitignore

Certifique-se de que o `.gitignore` contém:

```gitignore
# Python
__pycache__/
*.py[cod]
venv/
env/

# Database
*.db
*.sqlite
*.sqlite3

# Config
config/auth_config.yaml
.streamlit/secrets.toml

# Backups
backups/
*.bak

# SSH Keys
*.pem
*.key
ssh_*
*_rsa

# Build artifacts
*.spec
build/
dist/
*.exe

# Environment
.env
.env.local
```

### 2.3 Arquivo .env.example

Crie um arquivo `.env.example` com as variáveis necessárias:

```bash
# Database
DATABASE_URL=postgresql://usuario:senha@localhost:5432/contabil_db

# Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# AI Configuration (opcional)
OPENAI_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
OLLAMA_BASE_URL=

# Security
SECRET_KEY=your-secret-key-here
```

### 2.4 Primeiro Push para GitHub

```bash
# 1. Inicializar repositório (se ainda não foi feito)
cd contabil_system
git init

# 2. Adicionar arquivos
git add .

# 3. Commit inicial
git commit -m "Initial commit - Sistema Contábil v1.0"

# 4. Adicionar remote
git remote add origin git@github.com:seu-usuario/contabil-system.git

# 5. Push para GitHub
git branch -M main
git push -u origin main
```

---

## 3️⃣ Deploy Inicial

### 3.1 Conectar ao Servidor

```bash
# Conectar via SSH
ssh usuario@seu-servidor.com

# Ou usando chave específica
ssh -i ~/.ssh/sua-chave usuario@seu-servidor.com
```

### 3.2 Executar Script de Setup

```bash
# 1. Clonar repositório
cd /opt
sudo git clone git@github.com:seu-usuario/contabil-system.git
cd contabil-system

# 2. Executar script de setup
sudo bash deploy/setup_vps_hostinger.sh
```

O script de setup irá:

- Instalar dependências do sistema (Python, PostgreSQL, Nginx)
- Criar usuário do sistema
- Configurar ambiente virtual
- Instalar dependências Python
- Configurar PostgreSQL
- Configurar Nginx
- Configurar systemd service
- Configurar SSL (se domínio configurado)

### 3.3 Configurar Variáveis de Ambiente

```bash
# 1. Copiar arquivo de exemplo
cp .env.example .env

# 2. Editar variáveis
nano .env

# 3. Configurar DATABASE_URL
# Exemplo: postgresql://contabil_user:senha_segura@localhost:5432/contabil_db
```

### 3.4 Inicializar Banco de Dados

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate

# 2. Inicializar banco de dados
python init_db.py

# 3. Criar usuário admin (se necessário)
python -c "
from config.database import SessionLocal
from services.auth_service import AuthService
db = SessionLocal()
AuthService.create_user(
    db=db,
    username='admin',
    password='senha_segura_aqui',
    email='admin@exemplo.com',
    role='admin'
)
db.commit()
db.close()
"
```

### 3.5 Iniciar Serviço

```bash
# 1. Recarregar systemd
sudo systemctl daemon-reload

# 2. Iniciar serviço
sudo systemctl start contabil

# 3. Habilitar para iniciar automaticamente
sudo systemctl enable contabil

# 4. Verificar status
sudo systemctl status contabil
```

### 3.6 Verificar Funcionamento

```bash
# Verificar logs
sudo journalctl -u contabil -f

# Testar acesso
curl http://localhost:8501

# Ou acessar via navegador
# http://seu-servidor.com ou http://seu-ip:8501
```

---

## 4️⃣ Workflow de Atualização

### 4.1 Fluxo de Atualização

```
Desenvolvimento Local → Commit → Push GitHub → Pull no Servidor → Restart Serviço
```

### 4.2 Passo a Passo

#### 4.2.1 Desenvolvimento Local

```bash
# 1. Fazer alterações no código
# 2. Testar localmente
streamlit run app.py

# 3. Verificar que tudo funciona
```

#### 4.2.2 Commit e Push

```bash
# 1. Verificar mudanças
git status

# 2. Adicionar arquivos
git add .

# 3. Commit com mensagem descritiva
git commit -m "Descrição das alterações"

# 4. Push para GitHub
git push origin main
```

**Boas Práticas:**
- Commits descritivos e atômicos
- Nunca commitar arquivos sensíveis (.env, chaves, etc.)
- Testar antes de fazer push
- Usar branches para features grandes

#### 4.2.3 Deploy no Servidor

```bash
# 1. Conectar ao servidor
ssh usuario@seu-servidor.com

# 2. Ir para diretório do projeto
cd /opt/contabil-system

# 3. Fazer backup do banco (recomendado)
bash scripts/backup_postgres.sh

# 4. Pull das alterações
git pull origin main

# 5. Ativar ambiente virtual
source venv/bin/activate

# 6. Atualizar dependências (se necessário)
pip install -r requirements.txt

# 7. Executar migrações (se houver)
# Exemplo: python scripts/migrate_expand_contracts.py

# 8. Reiniciar serviço
sudo systemctl restart contabil

# 9. Verificar logs
sudo journalctl -u contabil -f
```

### 4.3 Script de Deploy Automatizado

Crie um script `deploy.sh` para automatizar:

```bash
#!/bin/bash
set -e

echo "🚀 Iniciando deploy..."

# Backup
echo "📦 Fazendo backup..."
bash scripts/backup_postgres.sh

# Pull
echo "⬇️ Atualizando código..."
git pull origin main

# Dependências
echo "📥 Atualizando dependências..."
source venv/bin/activate
pip install -r requirements.txt

# Migrações (se necessário)
# echo "🔄 Executando migrações..."
# python scripts/migrate_xxx.py

# Restart
echo "🔄 Reiniciando serviço..."
sudo systemctl restart contabil

# Verificar
echo "✅ Verificando status..."
sleep 3
sudo systemctl status contabil --no-pager

echo "✅ Deploy concluído!"
```

Tornar executável:

```bash
chmod +x deploy.sh
```

Usar:

```bash
./deploy.sh
```

### 4.4 Deploy com GitHub Actions (Opcional)

Crie `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/contabil-system
            bash deploy.sh
```

Configure secrets no GitHub:
- `SERVER_HOST`: IP ou domínio do servidor
- `SERVER_USER`: Usuário SSH
- `SSH_PRIVATE_KEY`: Chave SSH privada

---

## 5️⃣ Backup e Restauração

### 5.1 Backup do Banco de Dados

#### Backup Manual

```bash
# Backup PostgreSQL
pg_dump -U contabil_user -d contabil_db -F c -f backup_$(date +%Y%m%d_%H%M%S).dump

# Com compressão
pg_dump -U contabil_user -d contabil_db -F c | gzip > backup_$(date +%Y%m%d_%H%M%S).dump.gz
```

#### Backup Automatizado

O script `scripts/backup_postgres.sh` já está configurado:

```bash
# Executar manualmente
bash scripts/backup_postgres.sh

# Ou configurar cron para backups diários
crontab -e

# Adicionar linha (backup diário às 2h da manhã)
0 2 * * * /opt/contabil-system/scripts/backup_postgres.sh
```

### 5.2 Backup de Arquivos

```bash
# Backup do diretório do projeto
tar -czf backup_files_$(date +%Y%m%d).tar.gz /opt/contabil-system

# Excluir arquivos desnecessários
tar -czf backup_files_$(date +%Y%m%d).tar.gz \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  /opt/contabil-system
```

### 5.3 Restauração

#### Restaurar Banco de Dados

```bash
# 1. Parar serviço
sudo systemctl stop contabil

# 2. Restaurar backup
pg_restore -U contabil_user -d contabil_db -c backup_20251119_020000.dump

# Ou com arquivo comprimido
gunzip -c backup_20251119_020000.dump.gz | pg_restore -U contabil_user -d contabil_db -c

# 3. Reiniciar serviço
sudo systemctl start contabil
```

#### Restaurar Arquivos

```bash
# Extrair backup
tar -xzf backup_files_20251119.tar.gz -C /tmp

# Copiar arquivos necessários
cp -r /tmp/opt/contabil-system/* /opt/contabil-system/
```

### 5.4 Estratégia de Backup

**Recomendado:**
- **Backups Diários:** Banco de dados (manter 7 dias)
- **Backups Semanais:** Banco de dados completo (manter 4 semanas)
- **Backups Mensais:** Banco de dados + arquivos (manter 12 meses)
- **Backups Antes de Deploy:** Sempre fazer backup antes de atualizações

---

## 6️⃣ Monitoramento

### 6.1 Logs do Sistema

```bash
# Ver logs em tempo real
sudo journalctl -u contabil -f

# Ver últimas 100 linhas
sudo journalctl -u contabil -n 100

# Ver logs de hoje
sudo journalctl -u contabil --since today

# Ver logs de erro
sudo journalctl -u contabil -p err
```

### 6.2 Status do Serviço

```bash
# Verificar status
sudo systemctl status contabil

# Verificar se está rodando
sudo systemctl is-active contabil

# Verificar se está habilitado
sudo systemctl is-enabled contabil
```

### 6.3 Monitoramento de Recursos

```bash
# CPU e Memória
htop

# Espaço em disco
df -h

# Uso de memória
free -h

# Processos do Python
ps aux | grep python
```

### 6.4 Monitoramento do Banco de Dados

```bash
# Conectar ao PostgreSQL
psql -U contabil_user -d contabil_db

# Ver tamanho do banco
SELECT pg_size_pretty(pg_database_size('contabil_db'));

# Ver conexões ativas
SELECT count(*) FROM pg_stat_activity;

# Ver tabelas e tamanhos
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 6.5 Alertas

Configure alertas para:

- **Serviço parado:** `systemctl status contabil`
- **Disco cheio:** `df -h` (alertar se > 80%)
- **Memória alta:** `free -h` (alertar se > 90%)
- **Erros nos logs:** `journalctl -u contabil -p err`

---

## 7️⃣ Troubleshooting

### 7.1 Serviço Não Inicia

```bash
# Verificar logs de erro
sudo journalctl -u contabil -n 50

# Verificar se porta está em uso
sudo netstat -tulpn | grep 8501

# Verificar permissões
ls -la /opt/contabil-system

# Verificar variáveis de ambiente
cat /opt/contabil-system/.env
```

### 7.2 Erro de Conexão com Banco

```bash
# Testar conexão
psql -U contabil_user -d contabil_db -h localhost

# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar configuração
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

### 7.3 Erro 502 Bad Gateway (Nginx)

```bash
# Verificar logs do Nginx
sudo tail -f /var/log/nginx/error.log

# Verificar se serviço está rodando
sudo systemctl status contabil

# Verificar configuração do Nginx
sudo nginx -t
```

### 7.4 Performance Lenta

```bash
# Verificar uso de recursos
htop

# Verificar conexões do banco
psql -U contabil_user -d contabil_db -c "SELECT count(*) FROM pg_stat_activity;"

# Verificar queries lentas
psql -U contabil_user -d contabil_db -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
"
```

### 7.5 Problemas de Permissão

```bash
# Corrigir permissões do diretório
sudo chown -R contabil:contabil /opt/contabil-system
sudo chmod -R 755 /opt/contabil-system

# Corrigir permissões do venv
sudo chown -R contabil:contabil /opt/contabil-system/venv
```

---

## 8️⃣ Manutenção Regular

### 8.1 Tarefas Diárias

- [ ] Verificar logs de erro
- [ ] Verificar status do serviço
- [ ] Verificar espaço em disco
- [ ] Verificar backups

### 8.2 Tarefas Semanais

- [ ] Revisar logs da semana
- [ ] Verificar performance
- [ ] Verificar backups semanais
- [ ] Atualizar dependências (se necessário)

### 8.3 Tarefas Mensais

- [ ] Revisar uso de recursos
- [ ] Otimizar banco de dados
- [ ] Verificar backups mensais
- [ ] Atualizar sistema operacional
- [ ] Revisar segurança

### 8.4 Otimização do Banco de Dados

```bash
# Analisar tabelas
psql -U contabil_user -d contabil_db -c "ANALYZE;"

# Vacuum (limpeza)
psql -U contabil_user -d contabil_db -c "VACUUM ANALYZE;"

# Vacuum completo (quando necessário)
psql -U contabil_user -d contabil_db -c "VACUUM FULL ANALYZE;"
```

### 8.5 Atualização de Dependências

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate

# 2. Atualizar pip
pip install --upgrade pip

# 3. Verificar dependências desatualizadas
pip list --outdated

# 4. Atualizar requirements.txt (testar localmente primeiro)
pip freeze > requirements.txt

# 5. Testar
streamlit run app.py

# 6. Commit e deploy
git add requirements.txt
git commit -m "Atualizar dependências"
git push origin main
# Depois fazer deploy no servidor
```

---

## 9️⃣ Checklist de Deploy

### Antes de Fazer Deploy

- [ ] Código testado localmente
- [ ] Commits descritivos
- [ ] Backup do banco de dados
- [ ] Verificar .gitignore (não commitar arquivos sensíveis)
- [ ] Verificar variáveis de ambiente

### Durante o Deploy

- [ ] Fazer pull do código
- [ ] Atualizar dependências
- [ ] Executar migrações (se necessário)
- [ ] Reiniciar serviço
- [ ] Verificar logs

### Após o Deploy

- [ ] Testar funcionalidades principais
- [ ] Verificar logs de erro
- [ ] Verificar performance
- [ ] Notificar usuários (se houver mudanças significativas)

---

## 🔟 Comandos Úteis

### Serviço

```bash
# Iniciar
sudo systemctl start contabil

# Parar
sudo systemctl stop contabil

# Reiniciar
sudo systemctl restart contabil

# Recarregar (sem parar)
sudo systemctl reload contabil

# Status
sudo systemctl status contabil

# Habilitar no boot
sudo systemctl enable contabil

# Desabilitar no boot
sudo systemctl disable contabil
```

### Logs

```bash
# Seguir logs
sudo journalctl -u contabil -f

# Últimas 100 linhas
sudo journalctl -u contabil -n 100

# Desde hoje
sudo journalctl -u contabil --since today

# Apenas erros
sudo journalctl -u contabil -p err
```

### Banco de Dados

```bash
# Backup
pg_dump -U contabil_user -d contabil_db -F c -f backup.dump

# Restore
pg_restore -U contabil_user -d contabil_db -c backup.dump

# Conectar
psql -U contabil_user -d contabil_db

# Tamanho
psql -U contabil_user -d contabil_db -c "SELECT pg_size_pretty(pg_database_size('contabil_db'));"
```

### Git

```bash
# Pull
git pull origin main

# Status
git status

# Log
git log --oneline -10

# Verificar mudanças
git diff
```

---

## 📞 Suporte

Para problemas ou dúvidas:

1. Consulte os logs: `sudo journalctl -u contabil -f`
2. Verifique este tutorial
3. Consulte a documentação do Streamlit
4. Entre em contato com a equipe de desenvolvimento

---

**Sistema Contábil v1.0** | Tutorial de Deploy e Manutenção | Última atualização: Novembro 2025

