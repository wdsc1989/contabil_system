# 💾 Guia Completo de Backup e Restauração

Este guia detalha como fazer backup e restaurar o banco de dados PostgreSQL do Sistema Contábil.

## 📋 Índice

1. [Sistema de Backup Automático](#sistema-de-backup-automático)
2. [Backup Manual](#backup-manual)
3. [Restauração de Backup](#restauração-de-backup)
4. [Estratégia de Retenção](#estratégia-de-retenção)
5. [Verificação de Integridade](#verificação-de-integridade)
6. [Troubleshooting](#troubleshooting)

---

## 🔄 Sistema de Backup Automático

### Configuração

Os backups automáticos são executados via cron jobs configurados para:

- **Backup Diário**: Todos os dias às 2:00 AM
- **Backup Semanal**: Todo domingo às 1:00 AM
- **Backup Mensal**: Dia 1 de cada mês às 00:00

### Localização dos Backups

```
/var/backups/contabil/postgresql/
├── daily/          # Backups diários (retenção: 7 dias)
├── weekly/         # Backups semanais (retenção: 4 semanas)
└── monthly/        # Backups mensais (retenção: 12 meses)
```

### Verificar Status dos Backups

```bash
# Lista backups diários
ls -lh /var/backups/contabil/postgresql/daily/

# Lista backups semanais
ls -lh /var/backups/contabil/postgresql/weekly/

# Lista backups mensais
ls -lh /var/backups/contabil/postgresql/monthly/

# Verifica logs de backup
tail -f /var/log/contabil/backup.log
```

### Configurar Cron Jobs

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

---

## 📦 Backup Manual

### Backup Diário

```bash
cd /opt/contabil/contabil_system
sudo -u contabil bash scripts/backup_postgres.sh daily
```

### Backup Semanal

```bash
cd /opt/contabil/contabil_system
sudo -u contabil bash scripts/backup_postgres.sh weekly
```

### Backup Mensal

```bash
cd /opt/contabil/contabil_system
sudo -u contabil bash scripts/backup_postgres.sh monthly
```

### Backup Antes de Operações Críticas

**SEMPRE faça backup antes de:**
- Atualizações do sistema
- Migrações de banco de dados
- Alterações em produção
- Deploy de novas versões

```bash
# Backup antes de operação crítica
cd /opt/contabil/contabil_system
sudo -u contabil bash scripts/backup_postgres.sh daily

# Ou crie um backup com nome específico
BACKUP_FILE="/var/backups/contabil/postgresql/daily/backup_pre_deploy_$(date +%Y%m%d_%H%M%S).sql.gz"
sudo -u contabil PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h localhost -U contabil_user -d contabil_db | gzip > "$BACKUP_FILE"
```

---

## 🔄 Restauração de Backup

### ⚠️ ATENÇÃO

**A restauração irá SOBRESCREVER o banco de dados atual!**

Sempre faça um backup de segurança antes de restaurar.

### Passo 1: Backup de Segurança

```bash
# Cria backup do estado atual
cd /opt/contabil/contabil_system
sudo -u contabil bash scripts/backup_postgres.sh daily
```

### Passo 2: Listar Backups Disponíveis

```bash
# Lista backups diários
ls -lh /var/backups/contabil/postgresql/daily/

# Lista backups semanais
ls -lh /var/backups/contabil/postgresql/weekly/

# Lista backups mensais
ls -lh /var/backups/contabil/postgresql/monthly/
```

### Passo 3: Verificar Integridade do Backup

```bash
# Verifica se o arquivo não está corrompido
gzip -t /var/backups/contabil/postgresql/daily/backup_daily_2024-01-15_02-00-00.sql.gz

# Verifica hash MD5 (se existir)
cat /var/backups/contabil/postgresql/daily/backup_daily_2024-01-15_02-00-00.sql.gz.md5
md5sum /var/backups/contabil/postgresql/daily/backup_daily_2024-01-15_02-00-00.sql.gz
```

### Passo 4: Parar Aplicação

```bash
# Para a aplicação para evitar conflitos
sudo systemctl stop contabil.service
```

### Passo 5: Restaurar Backup

```bash
cd /opt/contabil/contabil_system

# Restaura backup (substitua pelo caminho do seu backup)
sudo -u contabil bash scripts/restore_postgres.sh \
    /var/backups/contabil/postgresql/daily/backup_daily_2024-01-15_02-00-00.sql.gz \
    --confirm
```

### Passo 6: Validar Restauração

```bash
# Conecta ao banco e verifica dados
sudo -u postgres psql -d contabil_db

# Verifica contagem de registros
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM clients;
SELECT COUNT(*) FROM transactions;
SELECT COUNT(*) FROM contracts;

# Verifica data do último registro
SELECT MAX(created_at) FROM transactions;

# Sai
\q
```

### Passo 7: Reiniciar Aplicação

```bash
# Reinicia a aplicação
sudo systemctl start contabil.service

# Verifica status
sudo systemctl status contabil.service

# Verifica logs
sudo journalctl -u contabil.service -f
```

---

## 📊 Estratégia de Retenção

### Retenção Configurada

| Tipo | Frequência | Retenção | Localização |
|------|-----------|----------|-------------|
| Diário | Diário às 2:00 AM | 7 dias | `/var/backups/contabil/postgresql/daily/` |
| Semanal | Domingo às 1:00 AM | 4 semanas | `/var/backups/contabil/postgresql/weekly/` |
| Mensal | Dia 1 às 00:00 | 12 meses | `/var/backups/contabil/postgresql/monthly/` |

### Limpeza Automática

Os backups antigos são automaticamente removidos pelos scripts de backup baseado na retenção configurada.

### Limpeza Manual

```bash
# Remove backups diários com mais de 7 dias
find /var/backups/contabil/postgresql/daily/ -name "*.sql.gz" -mtime +7 -delete

# Remove backups semanais com mais de 28 dias
find /var/backups/contabil/postgresql/weekly/ -name "*.sql.gz" -mtime +28 -delete

# Remove backups mensais com mais de 365 dias
find /var/backups/contabil/postgresql/monthly/ -name "*.sql.gz" -mtime +365 -delete
```

---

## ✅ Verificação de Integridade

### Verificar Backup

```bash
# Testa se o arquivo está íntegro
gzip -t /var/backups/contabil/postgresql/daily/backup_daily_2024-01-15_02-00-00.sql.gz

# Verifica hash MD5
if [ -f backup.sql.gz.md5 ]; then
    EXPECTED=$(cat backup.sql.gz.md5)
    ACTUAL=$(md5sum backup.sql.gz | cut -d' ' -f1)
    if [ "$EXPECTED" = "$ACTUAL" ]; then
        echo "✅ Hash MD5 confere"
    else
        echo "❌ Hash MD5 não confere - arquivo pode estar corrompido"
    fi
fi
```

### Verificar Banco de Dados

```bash
# Conecta ao banco
sudo -u postgres psql -d contabil_db

# Verifica integridade das tabelas
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Verifica contagem de registros por tabela
SELECT 
    'users' as tabela, COUNT(*) as registros FROM users
UNION ALL
SELECT 'clients', COUNT(*) FROM clients
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'contracts', COUNT(*) FROM contracts;

# Sai
\q
```

---

## 🔧 Troubleshooting

### Backup Falha

```bash
# Verifica logs
tail -f /var/log/contabil/backup.log

# Verifica variáveis de ambiente
sudo -u contabil env | grep POSTGRES

# Testa conexão manual
sudo -u contabil PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U contabil_user -d contabil_db -c "SELECT 1;"

# Testa pg_dump manual
sudo -u contabil PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h localhost -U contabil_user -d contabil_db > /tmp/test.sql
```

### Restauração Falha

```bash
# Verifica se o arquivo existe e não está corrompido
ls -lh /var/backups/contabil/postgresql/daily/backup_*.sql.gz
gzip -t /var/backups/contabil/postgresql/daily/backup_*.sql.gz

# Verifica permissões
sudo -u contabil ls -l /var/backups/contabil/postgresql/daily/

# Verifica espaço em disco
df -h /var/backups

# Tenta restaurar manualmente
gunzip -c /var/backups/contabil/postgresql/daily/backup_*.sql.gz | \
    sudo -u postgres psql -d contabil_db
```

### Sem Espaço em Disco

```bash
# Verifica uso de disco
df -h

# Lista tamanho dos backups
du -sh /var/backups/contabil/postgresql/*

# Remove backups antigos manualmente
find /var/backups/contabil/postgresql/ -name "*.sql.gz" -mtime +30 -ls
find /var/backups/contabil/postgresql/ -name "*.sql.gz" -mtime +30 -delete
```

### Backup Não Executa Automaticamente

```bash
# Verifica se o cron está rodando
sudo systemctl status cron

# Verifica crontab do usuário
sudo -u contabil crontab -l

# Verifica logs do cron
sudo grep CRON /var/log/syslog | tail -20

# Testa script manualmente
sudo -u contabil bash /opt/contabil/contabil_system/scripts/backup_postgres.sh daily
```

---

## 📤 Backup Remoto (Opcional)

### Upload para Google Drive

```bash
# Instala rclone (ferramenta para sincronização)
curl https://rclone.org/install.sh | sudo bash

# Configura rclone
rclone config

# Script para upload de backup
#!/bin/bash
BACKUP_FILE="/var/backups/contabil/postgresql/daily/backup_daily_$(date +%Y-%m-%d).sql.gz"
rclone copy "$BACKUP_FILE" gdrive:backups/contabil/
```

### Upload para S3

```bash
# Instala AWS CLI
sudo apt install awscli

# Configura credenciais
aws configure

# Script para upload
#!/bin/bash
BACKUP_FILE="/var/backups/contabil/postgresql/daily/backup_daily_$(date +%Y-%m-%d).sql.gz"
aws s3 cp "$BACKUP_FILE" s3://seu-bucket/backups/contabil/
```

---

## 📋 Checklist de Backup

### Antes de Operações Críticas

- [ ] Backup completo do banco atual
- [ ] Verificação de integridade do backup
- [ ] Teste de restauração em ambiente de teste
- [ ] Documentação do ponto de restauração

### Após Operações Críticas

- [ ] Backup imediato do novo estado
- [ ] Validação de contagem de registros
- [ ] Teste de queries críticas
- [ ] Backup de confirmação

### Manutenção Regular

- [ ] Verificar logs de backup semanalmente
- [ ] Verificar espaço em disco mensalmente
- [ ] Testar restauração trimestralmente
- [ ] Revisar estratégia de retenção anualmente

---

## 🔐 Segurança dos Backups

### Criptografia (Opcional)

```bash
# Cria backup criptografado
pg_dump -h localhost -U contabil_user -d contabil_db | \
    gzip | \
    openssl enc -aes-256-cbc -salt -out backup_encrypted.sql.gz.enc

# Restaura backup criptografado
openssl enc -d -aes-256-cbc -in backup_encrypted.sql.gz.enc | \
    gunzip | \
    psql -h localhost -U contabil_user -d contabil_db
```

### Permissões

```bash
# Ajusta permissões dos backups
sudo chmod 600 /var/backups/contabil/postgresql/**/*.sql.gz
sudo chown -R contabil:contabil /var/backups/contabil
```

---

**✅ Sistema de backup configurado e funcionando!**









