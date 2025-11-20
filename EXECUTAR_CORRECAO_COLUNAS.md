# 🔧 Executar Correção de Colunas Faltantes

## Problema

Erro: `column contracts.seller_name does not exist` (e outras colunas)

Isso acontece porque as colunas novas foram adicionadas aos modelos Python, mas não foram criadas no banco de dados PostgreSQL em produção.

## Solução Rápida

Execute no servidor:

```bash
cd /opt/contabil
source venv/bin/activate
python3 scripts/adicionar_colunas_faltantes.py
```

Este script irá:
- ✅ Detectar automaticamente se está usando PostgreSQL ou SQLite
- ✅ Verificar quais colunas já existem
- ✅ Adicionar apenas as colunas faltantes
- ✅ Adicionar foreign keys quando apropriado (PostgreSQL)

## Colunas que serão adicionadas

### Tabela `contracts`:
- `seller_name` (VARCHAR(200)) - Vendedor responsável
- `event_location` (TEXT) - Local do evento
- `service_hours` (FLOAT) - Horas de serviço
- `collaborators` (TEXT) - Colaboradores envolvidos
- `invoice_number` (VARCHAR(50)) - Número da NF
- `notes` (TEXT) - Observações gerais

### Tabela `accounts_payable`:
- `expense_type` (VARCHAR(20)) - Tipo CPF ou CNPJ
- `expense_category` (VARCHAR(50)) - Categoria de despesa
- `description` (TEXT) - Descrição detalhada

### Tabela `accounts_receivable`:
- `contract_id` (INTEGER) - Vínculo com contrato (com foreign key)

## Após executar

```bash
# Reiniciar o serviço
sudo systemctl restart contabil

# Verificar status
sudo systemctl status contabil

# Ver logs
sudo journalctl -u contabil -n 50 -f
```

## Alternativa: Usar script de migrações completo

```bash
cd /opt/contabil
source venv/bin/activate
bash scripts/run_migrations.sh
```

Este script executa todas as migrações, incluindo a correção de colunas.

## Verificar se funcionou

```bash
# Verificar configuração e conexão
python3 scripts/verificar_env.py
```

---

## ⚠️ Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'dotenv'"
```bash
pip install python-dotenv
```

### Erro: "connection refused" ou "authentication failed"
- Verifique se o PostgreSQL está rodando: `sudo systemctl status postgresql`
- Verifique se o `.env` está configurado corretamente: `python3 scripts/verificar_env.py`

### Ainda aparece erro após executar
1. Verifique se o serviço foi reiniciado: `sudo systemctl restart contabil`
2. Verifique os logs: `sudo journalctl -u contabil -n 100`
3. Execute o script novamente: `python3 scripts/adicionar_colunas_faltantes.py`

