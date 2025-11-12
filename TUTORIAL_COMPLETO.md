# 🎓 Tutorial Completo - Sistema Contábil

## Aprenda a Usar Todas as Funcionalidades

---

## 📋 Índice do Tutorial

1. [Primeiro Acesso](#primeiro-acesso)
2. [Seleção de Cliente](#seleção-de-cliente)
3. [Importação de Dados](#importação-de-dados)
4. [Gestão de Transações](#gestão-de-transações)
5. [Gestão de Contratos](#gestão-de-contratos)
6. [Contas a Pagar e Receber](#contas-a-pagar-e-receber)
7. [Dashboard DRE](#dashboard-dre)
8. [Dashboard DFC](#dashboard-dfc)
9. [Análise de Sazonalidade](#análise-de-sazonalidade)
10. [Geração de Relatórios](#geração-de-relatórios)
11. [Administração](#administração)

---

## 1️⃣ Primeiro Acesso

### Passo 1: Iniciar o Sistema

**Opção A - Com Scripts:**
```
1. Clique duas vezes em: run.bat
2. Aguarde a janela CMD abrir
3. O navegador abrirá automaticamente
```

**Opção B - Manual:**
```
1. Abra CMD na pasta do sistema
2. Digite: streamlit run app.py
3. Abra navegador em: http://localhost:8501
```

### Passo 2: Tela de Login

```
┌─────────────────────────────────┐
│   🔐 Sistema Contábil           │
├─────────────────────────────────┤
│                                 │
│   Usuário: [____________]       │
│   Senha:   [____________]       │
│                                 │
│   [      Entrar      ]          │
│                                 │
│   Credenciais de Teste:         │
│   Admin: admin / admin123       │
│   Gerente: gerente1 / gerente123│
│   Visualizador: viewer1 / ...   │
└─────────────────────────────────┘
```

**Digite:**
- Usuário: `admin`
- Senha: `admin123`
- Clique em **"Entrar"**

### Passo 3: Tela Inicial

Após login, você verá:

```
┌─────────────────────────────────────────────────────┐
│ Sidebar (Esquerda)          │ Conteúdo Principal    │
├─────────────────────────────┼───────────────────────┤
│ 📊 Sistema Contábil         │ 🏠 Bem-vindo ao       │
│ Usuário: admin              │    Sistema Contábil   │
│ Perfil: Admin               │                       │
│ ─────────────────────       │ [Card do Cliente]     │
│ 🏢 Cliente                  │                       │
│ [Empresa de Eventos... ▼]  │ 📊 Dashboards: 3      │
│ 📋 12.345.678/0001-90       │ 📥 Importação: 4...   │
│ ─────────────────────       │ 📝 Contratos: ...     │
│ Menu                        │ 💰 Contas: ...        │
│ 🏠 Início                   │                       │
│                             │ 📖 Guia Rápido        │
│ Dados                       │ [Expandir seções]     │
│ 📥 Importação              │                       │
│ 💳 Transações              │                       │
│ 📝 Contratos               │                       │
│ 💰 Contas                  │                       │
│                             │                       │
│ Dashboards                  │                       │
│ 📊 DRE                     │                       │
│ 💵 DFC                     │                       │
│ 📈 Sazonalidade            │                       │
│ 📑 Relatórios              │                       │
└─────────────────────────────┴───────────────────────┘
```

---

## 2️⃣ Seleção de Cliente

### Como Selecionar:

**Na Sidebar:**
```
🏢 Cliente
┌────────────────────────────────────┐
│ Empresa de Eventos Ltda [Eventos]▼│
└────────────────────────────────────┘
📋 12.345.678/0001-90
```

**Para Pesquisar:**
1. Clique na lista suspensa
2. **Digite** parte do nome (ex: "consultoria")
3. Lista filtra automaticamente
4. Selecione o cliente

**Clientes Disponíveis (dados de teste):**
- Empresa de Eventos Ltda [Eventos]
- Consultoria XYZ [Consultoria]
- Prestador de Serviços [Serviços]
- Comércio ABC [Comércio]
- Indústria Tech [Indústria]

**💡 Dica:** O cliente selecionado permanece ativo ao navegar entre páginas!

---

## 3️⃣ Importação de Dados

### Tutorial: Importar Extrato Bancário (CSV)

**Passo 1:** Clique em **📥 Importação** no menu

**Passo 2:** Selecione o tipo de importação
```
1️⃣ Selecione o Tipo de Importação
┌────────────────────────────────┐
│ 🏦 Extratos Bancários      ▼  │
└────────────────────────────────┘
```

**Passo 3:** Escolha o formato
```
Formato do arquivo:
( ) CSV  ( ) Excel  ( ) PDF  ( ) OFX
```
Selecione: **CSV**

**Passo 4:** Faça upload
```
📁 Selecione um arquivo CSV
[Arrastar arquivo ou clicar para selecionar]
```

**Use o arquivo:** `tests/sample_files/extrato_bancario_exemplo.csv`

**Passo 5:** Configure encoding e delimitador
```
Encoding: [utf-8 ▼]
Delimitador: [, ▼]
```

**Passo 6:** Preview dos dados
```
3️⃣ Preview dos Dados
┌──────────────┬────────────────────┬──────────┬──────────┐
│ Data         │ Descrição          │ Valor    │ Saldo    │
├──────────────┼────────────────────┼──────────┼──────────┤
│ 01/11/2025   │ Depósito - Cliente │ 2500.00  │ 15000.00 │
│ 02/11/2025   │ PIX Recebido       │ 1800.50  │ 16800.50 │
│ ...          │ ...                │ ...      │ ...      │
└──────────────┴────────────────────┴──────────┴──────────┘
Total de linhas: 18
```

**Passo 7:** Mapeamento de Colunas
```
4️⃣ Mapeamento de Colunas

Coluna do Arquivo    →    Campo do Sistema
─────────────────────────────────────────────
Data                 →    [date ▼]
Descrição            →    [description ▼]
Valor                →    [value ▼]
Saldo                →    [balance ▼]

✅ Todos os campos obrigatórios foram mapeados!
```

**💡 O sistema sugere automaticamente!**

**Passo 8:** Importar
```
[💾 Salvar Mapeamento]  [📥 Importar Dados]
```

Clique em **"📥 Importar Dados"**

**Resultado:**
```
✅ 18 registro(s) importado(s) com sucesso!
🎈 [Balões de comemoração]
```

---

### Tutorial: Importar Contratos (Excel)

**Passo 1:** Selecione tipo: **📝 Contratos/Eventos**

**Passo 2:** Formato: **Excel**

**Passo 3:** Upload: `tests/sample_files/contratos_exemplo.csv`

**Passo 4:** Mapeamento automático:
```
Data Inicio        → contract_start ✓
Data Evento        → event_date ✓
Contratante        → contractor_name ✓
Tipo Evento        → event_type ✓
Valor Serviço      → service_value ✓
Valor Deslocamento → displacement_value ✓
Numero Convidados  → guests_count ✓
Forma Pagamento    → payment_terms ✓
Status             → status ✓
```

**Passo 5:** Importar

**Resultado:**
```
✅ 7 registro(s) importado(s) com sucesso!
```

---

### Tutorial: Importar com Formato Diferente

**Arquivo:** `extrato_formato2_exemplo.csv`

**Características:**
- Delimitador: `;` (ponto e vírgula)
- Nomes de colunas diferentes
- Formato de valor: `1.234,56` (brasileiro)

**Mapeamento:**
```
dt_movimento  → date
historico     → description
vlr_movimento → value
saldo_final   → balance
```

**💡 O sistema detecta automaticamente:**
- Delimitador (`;`)
- Formato de moeda (vírgula decimal)
- Formato de data (dd/mm/yyyy)

---

## 4️⃣ Gestão de Transações

### Ver Transações

**Passo 1:** Clique em **💳 Transações**

**Passo 2:** Use os filtros
```
Tipo: [☑ 💰 Entrada] [☑ 💸 Saída]
Data de: [01/11/2025]
Data até: [30/11/2025]
🔍 Buscar: [Digite aqui...]
```

**Passo 3:** Veja estatísticas
```
┌─────────────────┬─────────────────┬─────────────────┐
│ 💰 Total Entradas│ 💸 Total Saídas │ 📊 Saldo        │
│ R$ 45.000,00    │ R$ 18.000,00    │ R$ 27.000,00    │
└─────────────────┴─────────────────┴─────────────────┘
```

**Passo 4:** Tabela de transações
```
┌────┬────────────┬──────┬─────────────┬────────────┬──────────┐
│ ID │ Data       │ Tipo │ Descrição   │ Valor      │ Origem   │
├────┼────────────┼──────┼─────────────┼────────────┼──────────┤
│ 1  │ 01/11/2025 │ 💰   │ Depósito... │ R$ 2.500   │ CSV      │
│ 2  │ 02/11/2025 │ 💰   │ PIX Rec...  │ R$ 1.800   │ CSV      │
└────┴────────────┴──────┴─────────────┴────────────┴──────────┘
```

### Criar Transação Manual

**Passo 1:** Tab **"➕ Nova Transação"**

**Passo 2:** Preencha o formulário
```
Data *: [11/11/2025]
Descrição *: [Venda de serviço de consultoria]
Valor *: [3500.00]
Tipo *: [entrada ▼]

Categoria: [Serviços]
Grupo: [Receitas ▼]
Subgrupo: [Consultorias ▼]
Conta: [Banco Itaú]
```

**Passo 3:** Clique em **"➕ Cadastrar Transação"**

**Resultado:**
```
✅ Transação cadastrada com sucesso!
```

### Editar Transação

**Passo 1:** Na lista, role até **"✏️ Editar/Excluir Transação"**

**Passo 2:** Selecione a transação
```
Selecione uma transação:
┌────────────────────────────────────────────────┐
│ 01/11/2025 - Depósito - Cliente... - R$ 2.500 ▼│
└────────────────────────────────────────────────┘
```

**Passo 3:** Altere os campos desejados

**Passo 4:** Clique em **"💾 Salvar"** ou **"🗑️ Excluir"**

---

## 5️⃣ Gestão de Contratos

### Ver Contratos

**Passo 1:** Clique em **📝 Contratos**

**Passo 2:** Use filtros
```
Status: [☑ ⏳ Pendente] [☑ ▶️ Em Andamento]
Data do evento de: [01/11/2025]
Data do evento até: [31/12/2025]
```

**Passo 3:** Veja estatísticas
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Total        │ Valor Total  │ Pendentes    │ Concluídos   │
│ 7            │ R$ 62.500    │ 3            │ 2            │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

### Criar Contrato

**Passo 1:** Tab **"➕ Novo Contrato"**

**Passo 2:** Preencha
```
Contratante *: [José da Silva]
Início do Contrato *: [11/11/2025]
Data do Evento *: [15/12/2025]
Tipo de Evento: [Casamento]
Serviço Vendido: [Buffet Completo + Decoração]

Valor do Serviço *: [15000.00]
Valor Deslocamento: [500.00]
Número de Convidados: [180]
Status: [pendente ▼]
Forma de Pagamento: [50% entrada, 50% no evento]
```

**Passo 3:** Clique em **"➕ Cadastrar Contrato"**

### Editar Contrato

**Passo 1:** Role até **"✏️ Editar Contrato"**

**Passo 2:** Selecione o contrato

**Passo 3:** Altere status, valores, etc

**Passo 4:** **"💾 Salvar"** ou **"🗑️ Excluir"**

---

## 6️⃣ Contas a Pagar e Receber

### Contas a Pagar

**Passo 1:** Clique em **💰 Contas**

**Passo 2:** Tab **"💸 Contas a Pagar"**

**Passo 3:** Veja alertas
```
⚠️ 2 conta(s) vencida(s)!
⏰ 3 conta(s) vencem nos próximos 7 dias!
```

**Passo 4:** Veja lista
```
┌────┬─────────────┬──────────────┬────────────┬──────────┬────────┐
│ ID │ Conta       │ CPF/CNPJ     │ Vencimento │ Valor    │ Status │
├────┼─────────────┼──────────────┼────────────┼──────────┼────────┤
│ 1  │ Fornecedor A│ 12.345...    │ 05/12/2025 │ R$ 2.500 │ ⏳ Pend│
│ 2  │ Energia     │ 23.456...    │ 10/12/2025 │ R$ 850   │ ⏳ Pend│
└────┴─────────────┴──────────────┴────────────┴──────────┴────────┘
```

**Passo 5:** Marcar como paga
```
💳 Registrar Pagamento

Selecione a conta:
[Fornecedor Alpha - R$ 2.500 (Venc: 05/12/2025) ▼]

Data do pagamento: [11/11/2025]

[✅ Marcar como Paga]
```

**Passo 6:** Editar ou Excluir
```
✏️ Editar/Excluir Conta

[Selecione a conta ▼]

Nome da Conta *: [Fornecedor Alpha Ltda]
CPF/CNPJ: [12.345.678/0001-90]
Vencimento *: [05/12/2025]
Valor *: [2500.00]

[💾 Salvar]  [🗑️ Excluir]
```

### Contas a Receber

**Similar às contas a pagar, mas:**
- Tab **"💰 Contas a Receber"**
- Botão: **"✅ Marcar como Recebida"**
- Alertas de contas atrasadas

---

## 7️⃣ Dashboard DRE

### Visualizar DRE

**Passo 1:** Clique em **📊 DRE**

**Passo 2:** Selecione período
```
📅 Período de Análise

Tipo de período: [Últimos 6 meses ▼]
```

**Opções:**
- Mês Atual
- Últimos 3 meses
- Últimos 6 meses
- Último ano
- Personalizado (escolha datas)

**Passo 3:** Veja KPIs
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ 💰 Receitas  │ 💸 Despesas  │ 📊 Resultado │ 📉 Margem    │
│ R$ 250.000   │ R$ 180.000   │ R$ 70.000    │ 28.0%        │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**Passo 4:** Veja gráficos
- **Receitas vs Despesas** (barras)
- **Resultado** (pizza)
- **Receitas por Categoria** (barras)
- **Despesas por Categoria** (barras)

**Passo 5:** Expanda detalhamento
```
📋 Detalhamento Completo da DRE [Clique para expandir]
```

**Dentro do detalhamento:**

**Nível 1 - Categorias:**
```
(+) RECEITAS OPERACIONAIS

💰 Vendas - R$ 150.000 (60%) [Expandir]
💰 Serviços - R$ 80.000 (32%) [Expandir]
💰 Eventos - R$ 20.000 (8%) [Expandir]
```

**Nível 2 - Transações:**
Clique em uma categoria para ver:
```
💰 Vendas - R$ 150.000 (60%)
├─ Total de transações: 45
├─ Valor médio: R$ 3.333,33
└─ Transações:
   ┌────────────┬────────────────────┬────────────┐
   │ Data       │ Descrição          │ Valor      │
   ├────────────┼────────────────────┼────────────┤
   │ 01/11/2025 │ Venda produto A    │ R$ 5.000   │
   │ 05/11/2025 │ Venda produto B    │ R$ 3.500   │
   │ ...        │ ...                │ ...        │
   └────────────┴────────────────────┴────────────┘
   Mostrando 10 de 45 transações
```

**Análises Automáticas:**
- Margem Líquida
- Despesas/Receitas
- Comparativo com período anterior
- Insights (situação positiva/crítica)
- Recomendações

---

## 8️⃣ Dashboard DFC

### Visualizar Fluxo de Caixa

**Passo 1:** Clique em **💵 DFC**

**Passo 2:** Selecione período
```
[Últimos 6 meses ▼]
```

**Passo 3:** Veja KPIs
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ 💰 Entradas  │ 💸 Saídas    │ 📊 Saldo     │ 📉 Média     │
│ R$ 300.000   │ R$ 220.000   │ R$ 80.000    │ R$ 13.333/mês│
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**Passo 4:** Veja gráficos
- **Fluxo Mensal** (entradas, saídas, saldo)
- **Saldo Acumulado** (linha com área)

**Passo 5:** Análise de Tendência
```
📈 Análise de Tendência
✅ Tendência de crescimento no saldo!
Variação (últimos 3 meses): +15.2%
```

**Passo 6:** Expanda detalhamento
```
📋 Detalhamento Completo do DFC [Clique para expandir]
```

**Nível 1 - Meses:**
```
📅 2024-11 - Saldo: 🟢 R$ 5.000 [Expandir]
📅 2024-12 - Saldo: 🟢 R$ 8.000 [Expandir]
📅 2025-01 - Saldo: 🔴 R$ -2.000 [Expandir]
```

**Nível 2 - Entradas/Saídas:**
Clique em um mês:
```
📅 2024-11 - Saldo: 🟢 R$ 5.000

┌──────────────┬──────────────┬──────────────┐
│ 💰 Entradas  │ 💸 Saídas    │ 📊 Acumulado │
│ R$ 50.000    │ R$ 45.000    │ R$ 80.000    │
└──────────────┴──────────────┴──────────────┘

💰 Entradas do Mês
📂 Vendas - R$ 30.000 (10 transações) [Expandir]
📂 Serviços - R$ 20.000 (8 transações) [Expandir]

💸 Saídas do Mês
📂 Salários - R$ 25.000 (5 transações) [Expandir]
📂 Despesas - R$ 20.000 (15 transações) [Expandir]
```

**Nível 3 - Transações:**
Clique em uma categoria para ver transações individuais

**Análises:**
- Resumo consolidado
- Estatísticas (médias, melhor/pior mês)
- Projeção do próximo mês
- Alertas automáticos

---

## 9️⃣ Análise de Sazonalidade

**Passo 1:** Clique em **📈 Sazonalidade**

**Passo 2:** Veja média mensal
```
Gráfico de barras mostrando receita média por mês:
- Janeiro: R$ 45.000
- Fevereiro: R$ 42.000
- ...
- Dezembro: R$ 50.000 (pico)

Linha vermelha: Média geral (R$ 38.000)
```

**Passo 3:** Heatmap
```
        Jan    Fev    Mar    Abr    Mai    Jun
2023   45K    42K    38K    35K    32K    28K
2024   48K    45K    40K    37K    34K    30K
2025   52K    48K    43K    39K    36K    32K

Cores: Verde (alto) → Amarelo → Vermelho (baixo)
```

**Passo 4:** Comparação Ano a Ano
```
Gráfico de linhas:
- 2023 (linha azul)
- 2024 (linha verde)
- 2025 (linha roxa)

Identifique padrões e crescimento
```

**Passo 5:** Insights
```
💡 Insights de Sazonalidade

✅ Melhor mês (média): Dezembro
   Receita média: R$ 50.000

❌ Pior mês (média): Junho
   Receita média: R$ 28.000

ℹ️ Variação sazonal: 78.6%

Meses fortes: Nov, Dez, Jan, Fev
Meses fracos: Jun, Jul, Ago
```

---

## 🔟 Geração de Relatórios

### Gerar Relatório Completo

**Passo 1:** Clique em **📑 Relatórios**

**Passo 2:** Selecione tipo
```
Tipo de relatório:
[Relatório Completo ▼]
```

**Opções:**
- DRE
- DFC
- Transações
- Contratos
- Contas a Pagar
- Contas a Receber
- **Relatório Completo** (todas as abas)

**Passo 3:** Selecione período
```
Data inicial: [01/10/2025]
Data final: [30/11/2025]
```

**Passo 4:** Clique em **"📊 Gerar Relatório"**

**Passo 5:** Veja preview
```
📄 Relatório Completo
Período: 01/10/2025 a 30/11/2025
Cliente: Empresa de Eventos Ltda

### 📊 DRE
Receitas: R$ 85.000
Despesas: R$ 62.000
Resultado: R$ 23.000

### 💵 DFC
[Tabela com fluxo mensal]

### 💳 Transações
[Lista de transações]

...
```

**Passo 6:** Download
```
[📥 Download Excel]
```

**Resultado:**
- Arquivo Excel com múltiplas abas
- Dados formatados
- Pronto para análise

---

## 1️⃣1️⃣ Administração

### Criar Novo Usuário

**Passo 1:** Clique em **⚙️ Administração** (Admin apenas)

**Passo 2:** Tab **"👥 Usuários"** → **"➕ Novo Usuário"**

**Passo 3:** Preencha
```
Usuário *: [joao.silva]
Email *: [joao@empresa.com]
Perfil *: [manager ▼]
Senha *: [senha123]
```

**Passo 4:** **"➕ Cadastrar"**

### Atribuir Permissões

**Passo 1:** Tab **"🔐 Permissões"** (na página Gestão de Clientes)

**Passo 2:** Selecione usuário
```
[joao.silva (manager) ▼]
```

**Passo 3:** Configure permissões por cliente
```
Empresa de Eventos Ltda (12.345.678/0001-90)
[☑] 👁️ Visualizar  [☑] ✏️ Editar  [ ] 🗑️ Excluir

Consultoria XYZ (98.765.432/0001-10)
[☑] 👁️ Visualizar  [ ] ✏️ Editar  [ ] 🗑️ Excluir
```

**Passo 4:** **"💾 Salvar Permissões"**

### Criar Grupos e Subgrupos

**Passo 1:** Tab **"🏷️ Grupos e Subgrupos"**

**Passo 2:** Criar Grupo
```
Novo Grupo
Nome *: [Investimentos]
Descrição: [Gastos com investimentos]
[➕ Criar]
```

**Passo 3:** Criar Subgrupo
```
Novo Subgrupo
Grupo *: [Investimentos ▼]
Nome *: [Equipamentos]
Descrição: [Compra de equipamentos]
[➕ Criar]
```

**Uso:** Agora pode classificar transações com este grupo!

---

## 📚 Casos de Uso Práticos

### Caso 1: Fluxo Completo de Trabalho Mensal

```
1. Início do mês:
   → Importar extrato bancário do mês anterior
   → Importar faturas de cartão
   → Cadastrar contas a pagar do mês

2. Durante o mês:
   → Adicionar transações manuais (dinheiro, PIX)
   → Cadastrar novos contratos
   → Marcar contas pagas/recebidas

3. Fim do mês:
   → Gerar DRE do mês
   → Gerar DFC
   → Exportar relatório completo
   → Enviar para contador/cliente

4. Análise:
   → Comparar com mês anterior
   → Verificar sazonalidade
   → Identificar oportunidades
```

### Caso 2: Correção de Dados Importados

```
Problema: Importou 100 transações, 5 estão com categoria errada

Solução:
1. Vá para 💳 Transações
2. Use filtro de busca: "fornecedor X"
3. Selecione cada transação
4. Edite a categoria
5. Salve
6. Pronto! Sem reimportar tudo
```

### Caso 3: Análise Comparativa de Clientes

```
Objetivo: Comparar performance de 2 clientes

Passos:
1. Selecione Cliente A (Eventos)
2. Vá para 📊 DRE
3. Anote: Receitas, Margem
4. Selecione Cliente B (Consultoria)
5. Veja DRE do Cliente B
6. Compare resultados
7. Identifique padrões por tipo de empresa
```

---

## 🎯 Exercícios Práticos

### Exercício 1: Importação Básica

**Objetivo:** Importar extrato bancário

**Passos:**
1. Vá para 📥 Importação
2. Tipo: Extratos Bancários
3. Upload: `extrato_bancario_exemplo.csv`
4. Mapeie colunas (automático)
5. Importe
6. Vá para 💳 Transações
7. Verifique dados importados

**Resultado Esperado:** 18 transações importadas

---

### Exercício 2: Cadastro Manual

**Objetivo:** Criar transação, contrato e conta

**Passos:**
1. **Transação:**
   - 💳 Transações → Nova Transação
   - Preencha dados
   - Cadastre

2. **Contrato:**
   - 📝 Contratos → Novo Contrato
   - Preencha dados
   - Cadastre

3. **Conta a Pagar:**
   - 💰 Contas → Nova Conta
   - Preencha dados
   - Cadastre

**Resultado:** 3 registros criados manualmente

---

### Exercício 3: Análise Completa

**Objetivo:** Gerar análise completa de um cliente

**Passos:**
1. Selecione cliente
2. Vá para 📊 DRE
3. Selecione "Último ano"
4. Expanda detalhamento completo
5. Explore cada categoria
6. Vá para 💵 DFC
7. Expanda detalhamento
8. Explore mês a mês
9. Vá para 📈 Sazonalidade
10. Identifique padrões
11. Vá para 📑 Relatórios
12. Gere relatório completo
13. Download Excel

**Resultado:** Análise completa exportada

---

## 📁 Arquivos de Exemplo Incluídos

### Localização:
```
tests/sample_files/
```

### Arquivos CSV:

1. **extrato_bancario_exemplo.csv**
   - 18 transações
   - Formato: Data, Descrição, Valor, Saldo
   - Delimitador: vírgula

2. **transacoes_exemplo.csv**
   - 15 transações
   - Formato brasileiro (vírgula decimal)
   - Delimitador: ponto e vírgula

3. **contratos_exemplo.csv**
   - 7 contratos
   - Todos os campos
   - Status variados

4. **contas_pagar_exemplo.csv**
   - 10 contas
   - Fornecedores diversos
   - Vencimentos futuros

5. **contas_receber_exemplo.csv**
   - 8 contas
   - Clientes diversos
   - Formas de recebimento variadas

6. **extrato_formato2_exemplo.csv**
   - Formato alternativo
   - Nomes de colunas diferentes
   - Para testar mapeamento

### Arquivos Excel:

7. **fatura_cartao_exemplo.xlsx**
   - 14 lançamentos
   - Estabelecimentos diversos
   - Categorias

8. **contratos_completo_exemplo.xlsx**
   - 2 abas (Contratos + Resumo)
   - Para testar múltiplas planilhas

9. **diario_gastos_exemplo.xlsx**
   - 30 dias de gastos
   - Controle diário
   - Categorias e formas de pagamento

---

## 💡 Dicas e Truques

### Dica 1: Atalhos de Teclado
- **Ctrl + R** - Recarregar página
- **Ctrl + Shift + R** - Limpar cache e recarregar
- **Ctrl + K** - Busca rápida (alguns navegadores)

### Dica 2: Múltiplas Abas
- Abra o sistema em várias abas do navegador
- Cada aba mantém seu próprio estado
- Útil para comparar clientes

### Dica 3: Exportar Gráficos
- Passe o mouse sobre gráficos Plotly
- Clique no ícone de câmera
- Download como PNG

### Dica 4: Filtros Rápidos
- Use filtros para encontrar dados específicos
- Combine múltiplos filtros
- Filtros são mantidos ao navegar

### Dica 5: Mapeamento Reutilizável
- Salve mapeamento na primeira importação
- Próximas importações usam automaticamente
- Economize tempo!

---

## 🎓 Conclusão do Tutorial

**Parabéns! Você aprendeu:**

- ✅ Fazer login e navegar
- ✅ Selecionar e pesquisar clientes
- ✅ Importar dados (CSV, Excel)
- ✅ Criar dados manualmente
- ✅ Editar e excluir dados
- ✅ Visualizar dashboards
- ✅ Expandir detalhamentos
- ✅ Gerar e exportar relatórios
- ✅ Administrar usuários e permissões
- ✅ Criar grupos e subgrupos

**Próximos Passos:**

1. ✅ Pratique com os arquivos de exemplo
2. ✅ Importe seus dados reais
3. ✅ Crie seus próprios clientes
4. ✅ Configure permissões
5. ✅ Explore análises avançadas
6. ✅ Gere relatórios mensais

**Sistema completo à sua disposição!** 🎉

---

## 📞 Precisa de Ajuda?

- **Instalação:** INSTALACAO_FACIL.md
- **Funcionalidades:** CRUD_FEATURES.md
- **Técnico:** MANUTENCAO_TECNICA.md
- **Testes:** tests/TESTING_GUIDE.md

**Bom uso do sistema!** 🚀


