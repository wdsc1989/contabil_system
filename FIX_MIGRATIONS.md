# 🔧 Correção: Executar Migrações em Produção

Os erros indicam que as colunas não existem no banco de dados PostgreSQL. É necessário executar as migrações.

## 🚨 Erros Encontrados

1. `contracts.seller_name` não existe
2. `contracts.event_location` não existe
3. `contracts.service_hours` não existe
4. `contracts.collaborators` não existe
5. `contracts.invoice_number` não existe
6. `contracts.notes` não existe
7. `accounts_receivable.contract_id` não existe
8. `accounts_payable.expense_type` não existe
9. `accounts_payable.expense_category` não existe
10. `accounts_payable.description` não existe

## ✅ Solução: Executar Migrações

### Opção 1: Via SSH (Recomendado)

```bash
# 1. Conectar ao servidor
ssh root@SEU_IP_SERVIDOR

# 2. Ir para diretório da aplicação
cd /opt/contabil

# 3. Ativar ambiente virtual
source venv/bin/activate

# 4. Executar migrações
bash scripts/run_migrations.sh
```

### Opção 2: Executar Migrações Individualmente

```bash
# 1. Conectar ao servidor
ssh root@SEU_IP_SERVIDOR

# 2. Ir para diretório
cd /opt/contabil

# 3. Ativar ambiente virtual
source venv/bin/activate

# 4. Executar migração de contratos
python3 scripts/migrate_expand_contracts.py

# 5. Executar migração de contas
python3 scripts/migrate_expand_accounts.py
```

### Opção 3: Via Script Windows (Local)

Crie um arquivo `fix_migrations.bat`:

```batch
@echo off
echo Executando migracoes no servidor...
echo.
set /p SERVER_IP="Digite o IP do servidor: "
set /p SERVER_USER="Digite o usuario SSH (ex: root): "
set /p APP_DIR="Digite o diretorio da aplicacao (ex: /opt/contabil): "
if "%APP_DIR%"=="" set APP_DIR=/opt/contabil

echo.
echo Conectando e executando migracoes...
ssh %SERVER_USER%@%SERVER_IP% "cd %APP_DIR% && source venv/bin/activate && bash scripts/run_migrations.sh"

echo.
echo Migracoes concluidas!
pause
```

## 🔄 Após Executar as Migrações

### 1. Reiniciar o Serviço

```bash
sudo systemctl restart contabil
```

### 2. Verificar Logs

```bash
sudo journalctl -u contabil.service -f
```

### 3. Testar a Aplicação

Acesse no navegador e verifique se os erros foram resolvidos.

## 📋 Verificação

Para verificar se as colunas foram criadas:

```bash
# Conectar ao PostgreSQL
psql -U contabil_user -d contabil_db

# Verificar colunas da tabela contracts
\d contracts

# Verificar colunas da tabela accounts_payable
\d accounts_payable

# Verificar colunas da tabela accounts_receivable
\d accounts_receivable

# Sair
\q
```

## ⚠️ Importante

- **Backup:** O script de migração cria um backup automaticamente antes de executar
- **Downtime:** Pode haver um breve downtime durante a migração
- **Teste:** Teste a aplicação após as migrações

## 🐛 Se Ainda Houver Erros

1. Verifique os logs: `sudo journalctl -u contabil.service -n 100`
2. Verifique se as colunas foram criadas (comando acima)
3. Verifique se o serviço foi reiniciado
4. Verifique se o código está atualizado: `git pull origin main`

