# 📁 Arquivos de Exemplo para Importação

## 🎯 Propósito

Estes arquivos servem para testar a funcionalidade de importação do sistema.

---

## 📊 Arquivos Disponíveis

### CSV (Comma-Separated Values)

#### 1. **extrato_bancario_exemplo.csv**
- **Linhas:** 18 transações
- **Período:** Novembro 2025
- **Delimitador:** Vírgula (,)
- **Colunas:** Data, Descrição, Valor, Saldo
- **Formato Valor:** 2500.00 (ponto decimal)
- **Uso:** Testar importação de extratos bancários

#### 2. **transacoes_exemplo.csv**
- **Linhas:** 15 transações
- **Delimitador:** Ponto e vírgula (;)
- **Colunas:** data, descricao, valor, tipo, categoria
- **Formato Valor:** 2500,00 (vírgula decimal - brasileiro)
- **Uso:** Testar importação com formato brasileiro

#### 3. **contratos_exemplo.csv**
- **Linhas:** 7 contratos
- **Colunas:** Data Inicio, Data Evento, Contratante, Tipo Evento, etc
- **Status:** Variados (pendente, em_andamento, concluido)
- **Uso:** Testar importação de contratos

#### 4. **contas_pagar_exemplo.csv**
- **Linhas:** 10 contas
- **Colunas:** Fornecedor, CNPJ, Vencimento, Valor, Categoria
- **Vencimentos:** Dezembro 2025 e Janeiro 2026
- **Uso:** Testar importação de contas a pagar

#### 5. **contas_receber_exemplo.csv**
- **Linhas:** 8 contas
- **Colunas:** Cliente, CPF/CNPJ, Vencimento, Valor, Forma Recebimento
- **Uso:** Testar importação de contas a receber

#### 6. **extrato_formato2_exemplo.csv**
- **Linhas:** 5 transações
- **Delimitador:** Ponto e vírgula (;)
- **Colunas:** dt_movimento, historico, vlr_movimento, saldo_final
- **Uso:** Testar mapeamento com nomes diferentes

---

### Excel (XLSX)

#### 7. **fatura_cartao_exemplo.xlsx**
- **Linhas:** 14 lançamentos
- **Colunas:** Data, Estabelecimento, Valor, Categoria
- **Uso:** Testar importação de fatura de cartão

#### 8. **contratos_completo_exemplo.xlsx**
- **Abas:** 2 (Contratos + Resumo)
- **Linhas:** 5 contratos + resumo
- **Uso:** Testar importação com múltiplas planilhas

#### 9. **diario_gastos_exemplo.xlsx**
- **Linhas:** 30 dias de gastos
- **Colunas:** Data, Descrição, Valor, Categoria, Forma Pagamento
- **Uso:** Testar controle diário de gastos

---

## 🎯 Como Usar

### Passo a Passo:

1. **Acesse o sistema**
   - http://localhost:8501
   - Login: admin / admin123

2. **Vá para Importação**
   - Clique em 📥 Importação

3. **Selecione tipo de importação**
   - Ex: Extratos Bancários

4. **Escolha formato**
   - CSV, Excel, PDF ou OFX

5. **Faça upload**
   - Selecione um dos arquivos desta pasta

6. **Mapeie colunas**
   - Sistema sugere automaticamente
   - Ajuste se necessário

7. **Importe**
   - Clique em "Importar Dados"

8. **Verifique**
   - Vá para página específica (Transações, Contratos, etc)
   - Veja dados importados

---

## 📋 Mapeamento Esperado

### Extrato Bancário:
```
Data        → date
Descrição   → description
Valor       → value
Saldo       → balance
```

### Transações:
```
data        → date
descricao   → description
valor       → value
tipo        → type
categoria   → category
```

### Contratos:
```
Data Inicio           → contract_start
Data Evento           → event_date
Contratante           → contractor_name
Tipo Evento           → event_type
Valor Serviço         → service_value
Valor Deslocamento    → displacement_value
Numero Convidados     → guests_count
Forma Pagamento       → payment_terms
Status                → status
```

### Contas a Pagar:
```
Fornecedor  → account_name
CNPJ        → cpf_cnpj
Vencimento  → due_date
Valor       → value
```

### Contas a Receber:
```
Cliente     → account_name
CPF/CNPJ    → cpf_cnpj
Vencimento  → due_date
Valor       → value
```

---

## 🧪 Testes Sugeridos

### Teste 1: Diferentes Delimitadores
- Use `extrato_bancario_exemplo.csv` (vírgula)
- Use `transacoes_exemplo.csv` (ponto e vírgula)
- Sistema deve detectar automaticamente

### Teste 2: Diferentes Formatos de Valor
- CSV 1: 2500.00 (ponto decimal)
- CSV 2: 2500,00 (vírgula decimal)
- Sistema deve converter ambos

### Teste 3: Nomes de Colunas Diferentes
- Use `extrato_formato2_exemplo.csv`
- Colunas: dt_movimento, historico, vlr_movimento
- Teste mapeamento manual

### Teste 4: Múltiplas Planilhas
- Use `contratos_completo_exemplo.xlsx`
- Selecione aba "Contratos"
- Importe

### Teste 5: Salvamento de Template
- Importe um arquivo
- Mapeie colunas
- Clique "Salvar Mapeamento"
- Importe outro arquivo do mesmo tipo
- Mapeamento deve ser reutilizado

---

## 💡 Dicas

### Para Criar Seus Próprios Arquivos:

**CSV:**
- Use vírgula ou ponto e vírgula como delimitador
- Primeira linha = nomes das colunas
- Formato de data: dd/mm/yyyy
- Formato de valor: 1234.56 ou 1234,56

**Excel:**
- Primeira linha = cabeçalhos
- Uma linha por registro
- Sem formatação complexa
- Sem fórmulas (apenas valores)

### Formatos Aceitos:

**Datas:**
- dd/mm/yyyy (01/11/2025)
- dd-mm-yyyy (01-11-2025)
- yyyy-mm-dd (2025-11-01)

**Valores:**
- 1234.56 (americano)
- 1234,56 (brasileiro)
- R$ 1.234,56 (com símbolo)
- 1.234,56 (com separador de milhar)

**CPF/CNPJ:**
- Com ou sem formatação
- 123.456.789-00 ou 12345678900
- 12.345.678/0001-90 ou 12345678000190

---

## 🎉 Resultado

**9 arquivos de exemplo prontos para uso!**

- ✅ Diferentes formatos (CSV, Excel)
- ✅ Diferentes delimitadores
- ✅ Diferentes formatos de valor
- ✅ Dados realistas
- ✅ Todos os tipos de importação cobertos

**Use para aprender e testar o sistema!** 🚀

---

## 📞 Suporte

Se tiver problemas ao importar:
1. Verifique o formato do arquivo
2. Veja mensagens de erro
3. Ajuste mapeamento
4. Consulte TUTORIAL_COMPLETO.md
5. Veja exemplos nesta pasta

**Bons testes!** 🎓














