# ⚡ EXECUTAR MIGRAÇÕES AGORA - Correção dos Erros

## 🚨 Problema

O banco de dados em produção está faltando colunas que foram adicionadas aos modelos. Isso causa erros ao acessar as páginas.

## ✅ Solução Rápida

Execute os seguintes comandos no servidor:

### Passo 1: Conectar ao Servidor

```bash
ssh root@SEU_IP_SERVIDOR
```

### Passo 2: Executar Migrações

```bash
cd /opt/contabil
source venv/bin/activate
bash scripts/run_migrations.sh
```

### Passo 3: Reiniciar Serviço

```bash
sudo systemctl restart contabil
```

### Passo 4: Verificar

```bash
sudo journalctl -u contabil.service -f
```

## 📋 Comandos Completos (Copiar e Colar)

```bash
# Conectar ao servidor (substitua SEU_IP_SERVIDOR)
ssh root@SEU_IP_SERVIDOR

# Executar migrações
cd /opt/contabil && source venv/bin/activate && bash scripts/run_migrations.sh

# Reiniciar serviço
sudo systemctl restart contabil

# Verificar status
sudo systemctl status contabil
```

## ✅ O que o Script Faz

1. Cria backup do banco de dados
2. Adiciona colunas faltantes em `contracts`:
   - seller_name
   - event_location
   - service_hours
   - collaborators
   - invoice_number
   - notes
3. Adiciona colunas faltantes em `accounts_payable`:
   - expense_type
   - expense_category
   - description
4. Adiciona coluna faltante em `accounts_receivable`:
   - contract_id

## 🔍 Verificar se Funcionou

Após executar, acesse a aplicação no navegador. Os erros devem ter desaparecido.

Se ainda houver erros, verifique os logs:
```bash
sudo journalctl -u contabil.service -n 100
```

