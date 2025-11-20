# 🔄 Guia de Deploy Contínuo

Este guia explica como fazer novos deploys e atualizações do sistema após o deploy inicial.

## 📋 Visão Geral

Após o primeiro deploy, você pode atualizar o sistema de duas formas:

1. **Deploy Automatizado** - Usando o script `deploy.sh` (recomendado)
2. **Deploy Manual** - Passo a passo manual

---

## 🚀 Método 1: Deploy Automatizado (Recomendado)

### Processo Completo

```bash
# Na VPS, execute:
cd /opt/contabil/contabil_system
bash deploy/deploy.sh main
```

O script `deploy.sh` faz automaticamente:
- ✅ Puxa código atualizado do GitHub
- ✅ Instala/atualiza dependências Python
- ✅ Executa migrações do banco (se necessário)
- ✅ Cria backup antes de atualizar
- ✅ Reinicia o serviço
- ✅ Verifica se está funcionando

### Passo a Passo Detalhado

#### 1. Preparar Código no GitHub

**No Windows (seu computador local):**

```powershell
cd C:\Users\DELL\Documents\Projetos\Contabil\contabil_system

# Faz suas alterações no código...

# Commit e push
git add .
git commit -m "Descrição das alterações"
git push origin main
```

#### 2. Executar Deploy na VPS

**Na VPS (via SSH):**

```bash
# Conecta na VPS
ssh root@72.61.56.204

# Executa deploy
cd /opt/contabil/contabil_system
bash deploy/deploy.sh main
```

#### 3. Verificar Deploy

```bash
# Verifica status do serviço
systemctl status contabil.service

# Verifica logs
journalctl -u contabil.service -n 50

# Testa aplicação
curl http://localhost:8501
```

---

## 🔧 Método 2: Deploy Manual

Se preferir fazer manualmente ou se o script automático falhar:

### Passo 1: Backup Antes de Atualizar

```bash
# Na VPS
cd /opt/contabil/contabil_system

# Cria backup do banco ANTES de atualizar
bash scripts/backup_postgres.sh daily
```

### Passo 2: Atualizar Código

```bash
# Na VPS
cd /opt/contabil/contabil_system

# Puxa código atualizado
git fetch origin
git checkout main
git pull origin main

# Verifica qual commit foi atualizado
git log -1 --oneline
```

### Passo 3: Atualizar Dependências

```bash
# Ativa ambiente virtual
source venv/bin/activate

# Atualiza pip
pip install --upgrade pip

# Instala/atualiza dependências
pip install -r requirements.txt
```

### Passo 4: Executar Migrações (se necessário)

```bash
# Se houver mudanças no banco de dados
python init_db.py

# Ou se usar Alembic (migrations)
# alembic upgrade head
```

### Passo 5: Reiniciar Serviço

```bash
# Reinicia aplicação
systemctl restart contabil.service

# Verifica status
systemctl status contabil.service

# Verifica logs
journalctl -u contabil.service -f
```

### Passo 6: Verificar Funcionamento

```bash
# Testa localmente
curl http://localhost:8501

# Verifica logs de erro
journalctl -u contabil.service --since "5 minutes ago" | grep -i error
```

---

## 🔄 Fluxo Completo de Deploy

```
┌─────────────────────────────────────────────────────────┐
│  1. Desenvolvimento Local (Windows)                     │
│     - Faz alterações no código                          │
│     - Testa localmente                                  │
│     - Commit e push para GitHub                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  2. Na VPS - Backup de Segurança                        │
│     - Cria backup do banco de dados                     │
│     - Verifica espaço em disco                          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  3. Na VPS - Atualizar Código                           │
│     - Git pull do repositório                           │
│     - Verifica mudanças                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  4. Na VPS - Atualizar Dependências                     │
│     - Atualiza pip                                      │
│     - Instala novas dependências                        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  5. Na VPS - Migrações (se necessário)                  │
│     - Executa init_db.py                                │
│     - Ou Alembic migrations                             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  6. Na VPS - Reiniciar Serviço                          │
│     - Restart do systemd                                │
│     - Verifica status                                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  7. Na VPS - Verificação                                │
│     - Testa aplicação                                   │
│     - Verifica logs                                     │
│     - Testa funcionalidades                             │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 Checklist de Deploy

Antes de cada deploy:

- [ ] Código testado localmente
- [ ] Commit e push feito no GitHub
- [ ] Backup do banco criado na VPS
- [ ] Verificado espaço em disco disponível
- [ ] Notificado usuários (se necessário)

Durante o deploy:

- [ ] Código atualizado (git pull)
- [ ] Dependências atualizadas
- [ ] Migrações executadas (se necessário)
- [ ] Serviço reiniciado
- [ ] Aplicação testada

Após o deploy:

- [ ] Verificado logs de erro
- [ ] Testado acesso via navegador
- [ ] Verificado funcionalidades principais
- [ ] Backup de confirmação criado

---

## 🚨 Rollback (Reverter Deploy)

Se algo der errado, você pode reverter:

### Opção 1: Reverter Código

```bash
# Na VPS
cd /opt/contabil/contabil_system

# Vê histórico de commits
git log --oneline -10

# Reverte para commit anterior
git reset --hard COMMIT_ANTERIOR

# Ou volta para versão anterior do branch
git reset --hard origin/main~1

# Reinicia serviço
systemctl restart contabil.service
```

### Opção 2: Restaurar Backup do Banco

```bash
# Lista backups disponíveis
ls -lh /var/backups/contabil/postgresql/daily/

# Restaura backup
cd /opt/contabil/contabil_system
bash scripts/restore_postgres.sh \
    /var/backups/contabil/postgresql/daily/backup_daily_YYYY-MM-DD_HH-MM-SS.sql.gz \
    --confirm
```

---

## 🔍 Verificação Pós-Deploy

### Comandos de Verificação

```bash
# 1. Status do serviço
systemctl status contabil.service

# 2. Logs recentes
journalctl -u contabil.service -n 100

# 3. Erros nos logs
journalctl -u contabil.service --since "10 minutes ago" | grep -i error

# 4. Teste de conectividade
curl -I http://localhost:8501

# 5. Verifica versão/código
cd /opt/contabil/contabil_system
git log -1 --oneline

# 6. Verifica dependências
source venv/bin/activate
pip list | grep streamlit
```

### Testes Funcionais

Após deploy, teste:

1. ✅ Login no sistema
2. ✅ Acesso às páginas principais
3. ✅ Importação de dados (se aplicável)
4. ✅ Geração de relatórios
5. ✅ Funcionalidades críticas

---

## 📊 Monitoramento Durante Deploy

### Acompanhar Logs em Tempo Real

```bash
# Em um terminal, acompanhe os logs
journalctl -u contabil.service -f

# Em outro terminal, execute o deploy
bash deploy/deploy.sh main
```

### Verificar Recursos do Sistema

```bash
# CPU e memória
htop

# Espaço em disco
df -h

# Conexões de rede
netstat -tlnp | grep -E '8501|80|443'
```

---

## 🔄 Deploy Automatizado com CI/CD (Opcional)

### GitHub Actions

Crie `.github/workflows/deploy.yml`:

```yaml
name: Deploy to VPS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/contabil/contabil_system
            bash deploy/deploy.sh main
```

**Configuração no GitHub:**
1. Vá em Settings → Secrets → Actions
2. Adicione:
   - `VPS_HOST`: IP da VPS
   - `VPS_USER`: root
   - `VPS_SSH_KEY`: Chave SSH privada

---

## 🛠️ Script de Deploy Melhorado

O script `deploy.sh` já inclui:

- ✅ Backup automático antes de atualizar
- ✅ Validação de código
- ✅ Verificação de dependências
- ✅ Teste de saúde após deploy
- ✅ Logs detalhados

### Personalizar Script

Você pode editar `deploy/deploy.sh` para adicionar:

- Notificações por email
- Testes automatizados
- Validações customizadas
- Rollback automático em caso de erro

---

## 📅 Agendamento de Deploys

### Deploy Automatizado Diário

```bash
# Adiciona ao crontab
crontab -e

# Deploy automático às 3h da manhã (horário de baixo uso)
0 3 * * * cd /opt/contabil/contabil_system && bash deploy/deploy.sh main >> /var/log/contabil/auto_deploy.log 2>&1
```

### Deploy Manual com Notificação

```bash
# Script com notificação
#!/bin/bash
cd /opt/contabil/contabil_system
bash deploy/deploy.sh main

# Envia email (se configurado)
if [ $? -eq 0 ]; then
    echo "Deploy realizado com sucesso" | mail -s "Deploy OK" seuemail@exemplo.com
else
    echo "Erro no deploy" | mail -s "Deploy FALHOU" seuemail@exemplo.com
fi
```

---

## 🔐 Segurança em Deploys

### Boas Práticas

1. **Sempre faça backup antes:**
   ```bash
   bash scripts/backup_postgres.sh daily
   ```

2. **Teste em ambiente de desenvolvimento primeiro**

3. **Use branches para features grandes:**
   ```bash
   git checkout -b feature/nova-funcionalidade
   # Desenvolve...
   git push origin feature/nova-funcionalidade
   # Merge no main depois de testado
   ```

4. **Mantenha logs de deploy:**
   ```bash
   bash deploy/deploy.sh main 2>&1 | tee /var/log/contabil/deploy_$(date +%Y%m%d_%H%M%S).log
   ```

---

## 📚 Comandos Úteis

### Ver Último Deploy

```bash
cd /opt/contabil/contabil_system
git log -1 --pretty=format:"%h - %an, %ar : %s"
```

### Ver Diferenças

```bash
# Ver o que mudou desde último deploy
cd /opt/contabil/contabil_system
git fetch origin
git diff HEAD origin/main
```

### Forçar Atualização

```bash
# Se precisar forçar atualização (cuidado!)
cd /opt/contabil/contabil_system
git fetch origin
git reset --hard origin/main
systemctl restart contabil.service
```

---

## 🆘 Troubleshooting

### Erro: "fatal: detected dubious ownership in repository"

**Causa:** O repositório foi clonado com um usuário diferente do atual.

**Solução:**
```bash
# Adiciona o diretório à lista de diretórios seguros do Git
git config --global --add safe.directory /opt/contabil

# Ou execute o deploy novamente (o script já corrige isso automaticamente)
bash deploy/deploy.sh main
```

### Deploy Falha

```bash
# Ver logs detalhados
journalctl -u contabil.service -n 200

# Verificar erros específicos
journalctl -u contabil.service --since "10 minutes ago" | grep -i error

# Verificar dependências
source venv/bin/activate
pip check
```

### Serviço Não Inicia

```bash
# Testa manualmente
cd /opt/contabil/contabil_system
source venv/bin/activate
streamlit run app.py --server.port=8501

# Verifica variáveis de ambiente
cat .env | grep -v PASSWORD
```

### Banco de Dados com Problemas

```bash
# Verifica conexão
psql -h localhost -U contabil_user -d contabil_db -c "SELECT 1;"

# Verifica logs do PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-16-main.log
```

---

## ✅ Resumo

**Deploy Rápido:**
```bash
cd /opt/contabil/contabil_system
bash deploy/deploy.sh main
```

**Deploy com Backup:**
```bash
cd /opt/contabil/contabil_system
bash scripts/backup_postgres.sh daily
bash deploy/deploy.sh main
```

**Verificar Deploy:**
```bash
systemctl status contabil.service
journalctl -u contabil.service -n 50
curl http://localhost:8501
```

---

**✅ Sistema de deploy contínuo configurado!**

