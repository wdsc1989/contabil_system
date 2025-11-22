# 📊 Sistema Contábil Streamlit

Sistema web completo de gestão contábil multi-cliente com importação inteligente de dados, controle de acesso robusto, dashboards analíticos e CRUD completo.

**Versão:** 1.0.0  
**Data:** Novembro 2025  
**Tecnologia:** Python 3.8+ | Streamlit | SQLite/PostgreSQL | SQLAlchemy

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Funcionalidades](#funcionalidades)
3. [Instalação](#instalação)
4. [Arquitetura](#arquitetura)
5. [Modelos de Dados](#modelos-de-dados)
6. [Serviços](#serviços)
7. [Páginas](#páginas)
8. [Utilitários](#utilitários)
9. [Testes](#testes)
10. [Manutenção](#manutenção)
11. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

Sistema web desenvolvido em Streamlit para gestão contábil completa, permitindo:
- Gestão de múltiplos clientes com tipos de empresa
- Importação de dados de múltiplas fontes (CSV, Excel, PDF, OFX)
- Mapeamento inteligente de colunas com templates reutilizáveis
- CRUD completo em todos os módulos
- Dashboards analíticos com drill-down detalhado
- Controle de acesso com 3 níveis de permissão
- Análises comparativas com 2+ anos de dados

---

## ✨ Funcionalidades

### Agente IA Conversacional 🤖
- **Administrador Contábil Inteligente:** Interface conversacional para consultas em linguagem natural
- **Saudação Proativa:** Análise automática do cliente ao iniciar conversa com sugestões baseadas em KPIs
- **Consultas Inteligentes:** Pergunte sobre receitas, despesas, DRE, DFC, contratos, contas e muito mais
- **Relatórios Dinâmicos:** Geração automática de relatórios baseados em perguntas
- **Visualizações Automáticas:** Gráficos e tabelas gerados dinamicamente conforme o contexto
- **Histórico de Conversas:** Mantém contexto da conversa para perguntas de follow-up
- **Exportação de Resultados:** Baixe resultados em Excel diretamente do chat
- **Análise de Intenção:** IA identifica automaticamente o tipo de consulta e parâmetros necessários

### Controle de Acesso 🔐
- **3 Perfis de Usuário:**
  - **Admin**: Acesso total ao sistema
  - **Manager**: Gerencia clientes específicos com permissões de edição
  - **Viewer**: Apenas visualização de clientes autorizados
- **Permissões Granulares:** view, edit, delete por cliente
- **Autenticação Segura:** Senhas hasheadas com bcrypt
- **Sessão Persistente:** Mantém login e contexto entre páginas

### Gestão Multi-Cliente 👥
- **CRUD Completo:** Criar, editar, desativar e excluir clientes
- **Tipos de Empresa:** Eventos, Consultoria, Comércio, Serviços, Indústria, Outro
- **Seletor com Pesquisa:** Digite para filtrar clientes
- **Contexto Global:** Cliente selecionado mantido em todas as páginas
- **Permissões por Usuário:** Atribua acesso específico a cada cliente

### Importação Inteligente 📥
- **4 Formatos Suportados:**
  - **CSV**: Detecção automática de delimitador e encoding
  - **Excel**: Suporte a múltiplas planilhas (leitura completa de todas as abas)
  - **PDF**: Extração completa de todas as páginas, texto e tabelas
  - **OFX**: Extratos bancários padrão brasileiro
- **IA para Processamento:**
  - **Detecção Automática de Tipo:** IA identifica automaticamente o tipo de dado (extrato bancário, transações, contratos, etc.)
  - **Mapeamento Inteligente:** IA analisa estrutura do arquivo e sugere mapeamento de colunas
  - **Processamento Completo:** Leitura e processamento de arquivos completos (sem limitações de linhas)
  - **Classificação Automática:** IA classifica cada linha por grupo e subgrupo baseado em descrição e contexto
  - **Extração de Informações:** Extração automática de nome do banco, datas precisas e outros metadados
- **Preview de Dados:**
  - Visualização completa ou limitada (opcional)
  - Remoção automática de linhas em branco
  - Scrollbar para navegação em arquivos grandes
  - Edição direta dos dados antes da importação
- **Classificação Contábil:**
  - **PRIMÁRIO:** Grupos e Subgrupos (Plano de Contas) - Obrigatório para relatórios DRE/DFC
  - **SECUNDÁRIO:** Categoria (opcional) - Usada apenas como fallback quando não há grupo/subgrupo
  - **IA Inteligente:** Classificação automática por grupo/subgrupo durante importação
  - **Feedback em Tempo Real:** Status de processamento visível durante análise pela IA

### CRUD Completo ✏️
- **Transações:** Criar, editar, excluir (manual ou importadas)
- **Contratos:** Gestão completa de contratos e eventos
- **Contas a Pagar:** CRUD + registro de pagamento
- **Contas a Receber:** CRUD + registro de recebimento
- **Clientes:** CRUD com tipos de empresa
- **Usuários:** CRUD com alteração de senha e perfil
- **Grupos/Subgrupos:** Criar e excluir classificações

### Dashboards Analíticos 📊

#### **DRE (Demonstração do Resultado)**
- KPIs: Receitas, Despesas, Resultado, Margem
- Gráficos: Barras, Pizza, Categorias
- **Detalhamento Completo:**
  - Drill-down por categoria (3 níveis)
  - Transações individuais (até 10 por categoria)
  - Comparativo com período anterior
  - Insights automáticos
  - Recomendações baseadas em margem

#### **DFC (Fluxo de Caixa)**
- KPIs: Total Entradas, Saídas, Saldo, Média
- Gráficos: Fluxo mensal, Saldo acumulado, Tendências
- **Detalhamento Completo:**
  - Drill-down mês a mês (4 níveis)
  - Entradas/Saídas por categoria
  - Transações individuais (até 5 por categoria)
  - Estatísticas (médias, melhor/pior mês)
  - Projeção do próximo mês
  - Alertas automáticos

#### **Sazonalidade**
- Média de receitas por mês
- Heatmap por ano e mês
- Comparação ano a ano
- Identificação de meses fortes/fracos
- Crescimento ano a ano
- Recomendações comerciais

### Relatórios e Exportação 📑
- **Tipos:** DRE, DFC, DFC Projeção, Transações, Contratos, Contas, Completo
- **DFC Projeção:** Projeção de fluxo de caixa futuro com base em contas a pagar/receber
- **Formato:** Excel com múltiplas abas
- **Filtros:** Período personalizável
- **Dados:** Formatados e organizados
- **Geração via IA:** Relatórios personalizados gerados através do Agente IA

### Grupos e Subgrupos 🏷️
- **Classificação Hierárquica:** Grupo → Subgrupo
- **Por Cliente:** Cada cliente tem seus grupos
- **Aplicável a:** Transações e importações
- **Gestão:** Criar e excluir via interface

### Relatórios Especializados 📈

#### **Diário de Gastos**
- Visualização diária de despesas
- Heatmap de gastos por dia
- KPIs de gastos diários
- Filtros por período e categoria
- Tabela detalhada de transações

#### **Fluxo de Caixa Gerencial**
- Análise gerencial de fluxo de caixa
- Projeções e tendências
- Alertas de saldo negativo
- Comparações mensais

#### **Despesas CPF vs CNPJ**
- Separação de despesas pessoais e empresariais
- Análise comparativa
- Gráficos de distribuição
- Relatórios detalhados

#### **Dashboard de Contas**
- Visão consolidada de contas a pagar e receber
- Status de pagamentos
- Alertas de vencimento
- Análise de inadimplência

#### **Performance de Vendedores**
- Análise de vendas por vendedor
- Métricas de performance
- Comparações entre vendedores
- Relatórios de comissões

#### **Relatório de Eventos**
- Calendário de eventos
- Análise de contratos
- Performance de eventos
- Receitas por evento

#### **Painel de Controle Unificado**
- Visão geral consolidada
- KPIs principais
- Alertas e notificações
- Acesso rápido a todas as funcionalidades

### Configuração de Relatórios ⚙️
- **Seleção de Tipos de Dados:** Configure quais tipos de dados aparecem em cada relatório
- **Tipos Disponíveis:**
  - Transações Financeiras
  - Extratos Bancários
  - Contratos/Eventos
  - Contas a Pagar
  - Contas a Receber
  - Aplicações Financeiras
  - Faturas de Cartão
  - Extratos de Máquina de Cartão
  - Controle de Estoque
- **Mapa Visual de Dados:** Visualize o fluxo de dados e como cada tipo se conecta aos relatórios
- **Configuração por Cliente:** Cada cliente pode ter sua própria configuração de relatórios

---

## 🤖 Prompts de IA Utilizados

O sistema utiliza Inteligência Artificial para processamento e classificação automática de dados. Todos os prompts são otimizados para garantir precisão e consistência.

### Prompts de Processamento de Dados

#### 1. **Processamento de Transações Financeiras**

**Objetivo:** Processar e classificar transações financeiras de arquivos CSV, Excel ou PDF.

**Características:**
- Extração de data, descrição, valor e tipo (entrada/saída)
- Classificação automática por grupo e subgrupo
- Normalização de valores monetários
- Identificação de categoria
- Cálculo de `classification_confidence` (0.0 a 1.0)

**Regras Críticas:**
- Datas devem ser convertidas para YYYY-MM-DD
- Valores normalizados (remover símbolos, pontos de milhar)
- Tipo identificado automaticamente (entrada/saída)
- Classificação por grupo/subgrupo é OBRIGATÓRIA
- Alertas quando confiança < 70%

**Estrutura de Resposta:**
```json
{
  "processed_data": [
    {
      "date": "2024-01-15",
      "description": "Pagamento fornecedor",
      "value": 1500.00,
      "type": "saida",
      "category": "fornecedor",
      "group_id": 1,
      "subgroup_id": 3,
      "classification_confidence": 0.95
    }
  ],
  "summary": {
    "total_rows": 100,
    "processed": 98,
    "entradas": 45,
    "saidas": 53
  },
  "issues": []
}
```

#### 2. **Processamento de Extratos Bancários**

**Objetivo:** Processar extratos bancários e extrair informações completas.

**Características:**
- Extração automática do nome do banco (cabeçalhos, rodapés, descrições)
- Processamento de saldos
- Identificação de número de conta
- Classificação automática por grupo/subgrupo
- Suporte a PDFs com texto não estruturado

**Regras Críticas:**
- Nome do banco extraído automaticamente
- Valores mantêm sinal original (negativo = débito, positivo = crédito)
- Datas preservadas exatamente como no arquivo
- Classificação obrigatória por grupo/subgrupo

#### 3. **Processamento de Contas a Pagar**

**Objetivo:** Processar planilhas de contas a pagar.

**Estrutura Esperada:**
- `account_name`: Nome do credor/fornecedor
- `due_date`: Data de vencimento
- `value`: Valor a pagar
- `cpf_cnpj`: CPF/CNPJ (opcional)
- `month_ref`: Mês de referência (opcional)
- `paid`: Status de pagamento (opcional)
- `group_id` e `subgroup_id`: Classificação contábil

**Características:**
- Classificação automática por grupo/subgrupo
- Identificação de CPF vs CNPJ
- Cálculo de `classification_confidence`

#### 4. **Processamento de Contas a Receber**

**Objetivo:** Processar planilhas de contas a receber.

**Estrutura Esperada:**
- `account_name`: Nome do devedor/cliente
- `due_date`: Data de vencimento
- `value`: Valor a receber
- `cpf_cnpj`: CPF/CNPJ (opcional)
- `month_ref`: Mês de referência (opcional)
- `received`: Status de recebimento (opcional)
- `group_id` e `subgroup_id`: Classificação contábil

**Características:**
- Classificação automática por grupo/subgrupo
- Identificação de CPF vs CNPJ
- Vinculação com contratos (quando aplicável)

#### 5. **Processamento de Contratos/Eventos**

**Objetivo:** Processar contratos e eventos de arquivos estruturados ou PDFs.

**Estrutura Esperada:**
- `contract_start`: Data de início do contrato
- `event_date`: Data do evento
- `service_value`: Valor do serviço
- `displacement_value`: Valor do deslocamento
- `event_type`: Tipo de evento
- `service_sold`: Serviço vendido
- `guests_count`: Número de convidados
- `contractor_name`: Nome do contratante
- `seller_name`: Nome do vendedor (expandido)
- `event_location`: Local do evento (expandido)
- `service_hours`: Horas de serviço (expandido)
- `invoice_number`: Número da nota fiscal (expandido)
- `group_id` e `subgroup_id`: Classificação contábil

**Características:**
- Suporte a PDFs com texto não estruturado
- Extração de campos expandidos
- Classificação automática

#### 6. **Processamento de Aplicações Financeiras**

**Objetivo:** Processar extratos de aplicações financeiras.

**Estrutura Esperada:**
- `date`: Data da operação
- `investment_type`: Tipo (CDB, LCI, LCA, Tesouro, etc)
- `institution`: Instituição financeira
- `operation_type`: aplicado ou resgatado
- `applied_value`: Valor aplicado
- `redeemed_value`: Valor resgatado
- `yield_value`: Rendimento
- `balance`: Saldo atual

#### 7. **Processamento de Faturas de Cartão**

**Objetivo:** Processar faturas de cartão de crédito.

**Estrutura Esperada:**
- `transaction_date`: Data da transação
- `description`: Descrição
- `value`: Valor
- `category`: Categoria
- `establishment`: Estabelecimento
- `installment_number`: Número da parcela
- `total_installments`: Total de parcelas
- `card_brand`: Bandeira do cartão

#### 8. **Processamento de Extratos de Máquina de Cartão**

**Objetivo:** Processar extratos de máquinas de cartão.

**Estrutura Esperada:**
- `date`: Data da transação
- `gross_value`: Valor bruto
- `fee`: Taxa cobrada
- `net_value`: Valor líquido
- `card_brand`: Bandeira (Visa, Mastercard, Elo, etc)
- `transaction_type`: débito ou crédito
- `description`: Descrição

#### 9. **Processamento de Controle de Estoque**

**Objetivo:** Processar movimentações de estoque.

**Estrutura Esperada:**
- `product_name`: Nome do produto
- `quantity`: Quantidade (pode ser decimal)
- `unit_value`: Valor unitário
- `movement_date`: Data do movimento
- `movement_type`: entrada ou saida
- `description`: Descrição

### Bloco de Classificação Genérico

Todos os prompts incluem um bloco de classificação que lista os grupos e subgrupos disponíveis para o cliente:

```
**Classificação Contábil - Grupos e Subgrupos Disponíveis:**

[Grupo 1: Receitas]
  - Subgrupo 1.1: Vendas
  - Subgrupo 1.2: Serviços
  ...

[Grupo 2: Despesas]
  - Subgrupo 2.1: Fornecedores
  - Subgrupo 2.2: Pessoal
  ...

**Instruções de Classificação:**
- Analise CADA linha e classifique por grupo e subgrupo
- Use palavras-chave na descrição para identificar a categoria
- Retorne group_id e subgroup_id (IDs numéricos)
- Informe classification_confidence (0.0 a 1.0)
- Se confiança < 0.70, registre em issues
```

### Detecção Automática de Tipo de Dado

O sistema também utiliza IA para detectar automaticamente o tipo de dado do arquivo:

**Prompt de Detecção:**
- Analisa estrutura do arquivo
- Identifica padrões de colunas
- Compara com estruturas conhecidas
- Retorna tipo mais provável: `transactions`, `bank_statements`, `contracts`, `accounts_payable`, `accounts_receivable`, `financial_investments`, `credit_card_invoices`, `card_machine_statements`, `inventory`

### Provedores de IA Suportados

- **OpenAI** (GPT-3.5, GPT-4)
- **Google Gemini**
- **Groq** (Llama models)
- **Ollama** (modelos locais)

### Configuração de Confiança

- **Threshold Padrão:** 0.70 (70%)
- **Alertas:** Linhas com confiança < 70% são destacadas
- **Revisão Manual:** Usuário pode revisar e corrigir classificações de baixa confiança

---

## 🚀 Instalação

### Instalação Automática (Recomendado)

**Windows:**
```bash
# 1. Clique duas vezes em: install.bat
# 2. Aguarde 2-5 minutos
# 3. Pronto!
```

### Instalação Manual

#### Pré-requisitos:
- Python 3.8 ou superior
- pip (gerenciador de pacotes)

#### Passo a Passo:

```bash
# 1. Navegue até o diretório
cd contabil_system

# 2. Crie ambiente virtual
python -m venv venv

# 3. Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instale dependências
pip install -r requirements.txt

# 5. Inicialize banco de dados
python init_db.py

# 6. Carregue dados de teste (2 anos)
python tests/seed_data.py --reset

# 7. Execute o sistema
streamlit run app.py
```

### Execução Rápida

**Windows:**
```bash
# Clique duas vezes em: run.bat
```

**Manual:**
```bash
streamlit run app.py
```

**Acesse:** http://localhost:8501

---

## 🏗️ Arquitetura

### Stack Tecnológico

| Camada | Tecnologia | Versão | Propósito |
|--------|-----------|--------|-----------|
| **Frontend** | Streamlit | 1.29+ | Interface web |
| **Backend** | Python | 3.8+ | Lógica de negócio |
| **Banco de Dados** | SQLite/PostgreSQL | 3.x/16 | Armazenamento (SQLite dev, PostgreSQL prod) |
| **ORM** | SQLAlchemy | 2.0+ | Mapeamento objeto-relacional |
| **Visualização** | Plotly | 5.18+ | Gráficos interativos |
| **Processamento** | Pandas | 2.0+ | Manipulação de dados |
| **Segurança** | bcrypt | 4.1+ | Hash de senhas |

### Estrutura de Diretórios

```
contabil_system/
│
├── app.py                          # 🏠 Aplicação principal e página inicial
├── init_db.py                      # 🗄️ Script de inicialização do banco
│
├── install.bat                     # 📦 Instalador automático (Windows)
├── run.bat                         # ▶️ Executar sistema (Windows)
├── reset_data.bat                  # 🔄 Resetar dados de teste
├── build_exe.bat                   # 🔨 Criar executável
│
├── requirements.txt                # 📋 Dependências Python
├── .gitignore                      # 🚫 Arquivos ignorados pelo Git
│
├── config/                         # ⚙️ Configurações
│   ├── __init__.py
│   └── database.py                 # Configuração SQLite + SQLAlchemy
│
├── models/                         # 🗃️ Modelos de dados (SQLAlchemy)
│   ├── __init__.py
│   ├── user.py                     # Usuários e permissões
│   ├── client.py                   # Clientes
│   ├── group.py                    # Grupos e subgrupos
│   ├── transaction.py              # Transações e extratos
│   ├── contract.py                 # Contratos e eventos
│   └── account.py                  # Contas a pagar/receber + mapeamentos
│
├── services/                       # 🔧 Serviços e lógica de negócio
│   ├── __init__.py
│   ├── auth_service.py             # Autenticação e permissões
│   ├── parser_service.py           # Parse de arquivos (CSV, Excel, PDF, OFX)
│   ├── import_service.py           # Importação com mapeamento
│   ├── report_service.py           # Geração de relatórios e análises
│   ├── ai_service.py               # Serviço de IA (OpenAI, Gemini, Groq, Ollama)
│   └── ai_agent_service.py         # Agente conversacional de IA
│
├── pages/                          # 📄 Páginas do Streamlit
│   ├── __init__.py
│   ├── 1_Gestao_Clientes.py        # 👥 CRUD de clientes + permissões
│   ├── 2_Importacao_Dados.py       # 📥 Importação inteligente com IA
│   ├── 2_Transacoes.py             # 💳 CRUD de transações
│   ├── 3_Extratos_Bancarios.py     # 🏦 Gestão de extratos bancários
│   ├── 4_Contratos.py              # 📝 CRUD de contratos
│   ├── 5_Contas.py                 # 💰 CRUD de contas
│   ├── 6_DRE.py                    # 📊 Dashboard DRE
│   ├── 7_DFC.py                    # 💵 Dashboard DFC
│   ├── 8_Sazonalidade.py           # 📈 Dashboard Sazonalidade
│   ├── 9_Relatorios.py             # 📑 Exportação de relatórios
│   ├── 10_Admin.py                 # ⚙️ Administração do sistema + Configuração de IA
│   └── 11_Agente_IA.py             # 🤖 Agente conversacional de IA
│
├── utils/                          # 🛠️ Utilitários
│   ├── __init__.py
│   ├── validators.py               # Validações (CPF, CNPJ, datas, moeda)
│   ├── formatters.py               # Formatadores (CPF, CNPJ, moeda, datas)
│   ├── column_mapper.py            # Mapeamento inteligente de colunas
│   ├── ui_components.py            # Componentes visuais reutilizáveis
│   └── top_navigation.py           # Menu de navegação superior
│
├── tests/                          # 🧪 Testes e dados
│   ├── __init__.py
│   ├── seed_data.py                # Script de seed (2 anos de dados)
│   ├── TESTING_GUIDE.md            # Guia de testes
│   └── sample_files/               # Arquivos de exemplo (criados dinamicamente)
│
├── scripts/                        # 🔧 Scripts auxiliares
│   ├── build_exe_spec.py           # Especificação para build
│   ├── SistemaContabil.spec        # Configuração PyInstaller
│   └── auxiliares/                 # Scripts de desenvolvimento
│       ├── capture_screenshots.py  # Captura de screenshots
│       └── generate_pdf_tutorial*.py # Geração de PDFs
│
├── data/                           # 💾 Banco de dados (criado automaticamente)
│   └── contabil.db                 # SQLite database
│
├── build/                          # 🔨 Arquivos de build (gerados)
├── dist/                           # 📦 Distribuição (executável gerado)
│
└── docs/                           # 📚 Documentação organizada
    ├── README.md                   # Índice da documentação
    ├── tutoriais/                  # Tutoriais do sistema
    ├── guias/                      # Guias de instalação e uso
    │   ├── QUICKSTART.md
    │   ├── INSTALL.md
    │   ├── INSTALACAO_FACIL.md
    │   ├── INSTALACAO_COMPLETA.md
    │   └── GUIA_INSTALACAO_VISUAL.md
    ├── desenvolvimento/            # Documentação técnica
    │   ├── PROJECT_STATUS.md
    │   ├── IMPLEMENTATION_SUMMARY.md
    │   ├── CRUD_FEATURES.md
    │   ├── DETAILED_REPORTS.md
    │   ├── UI_IMPROVEMENTS.md
    │   └── LATEST_UPDATES.md
    ├── distribuicao/               # Documentação de distribuição
    │   ├── DISTRIBUICAO.md
    │   └── README_EXECUTAVEL.txt
    └── screenshots/                # Screenshots do sistema
```

---

## 🗃️ Modelos de Dados

### Diagrama de Relacionamentos

```
User (Usuários)
  ├─ UserClientPermission (Permissões)
  │    └─ Client (Clientes)
  │         ├─ Group (Grupos)
  │         │    └─ Subgroup (Subgrupos)
  │         │         └─ Transaction (Transações)
  │         ├─ Transaction (Transações)
  │         ├─ BankStatement (Extratos)
  │         ├─ Contract (Contratos)
  │         ├─ AccountPayable (Contas a Pagar)
  │         ├─ AccountReceivable (Contas a Receber)
  │         └─ ImportMapping (Mapeamentos)
```

### Tabelas Detalhadas

#### **users** (Usuários)
```python
id: Integer (PK)
username: String(50) UNIQUE NOT NULL
password_hash: String(255) NOT NULL  # bcrypt
email: String(100) UNIQUE NOT NULL
role: String(20) NOT NULL  # admin, manager, viewer
active: Boolean DEFAULT True
created_at: DateTime DEFAULT now()

Relacionamentos:
- permissions → UserClientPermission (1:N)
```

#### **clients** (Clientes)
```python
id: Integer (PK)
name: String(200) NOT NULL
cpf_cnpj: String(18) UNIQUE NOT NULL
tipo_empresa: String(100)  # Eventos, Consultoria, etc
active: Boolean DEFAULT True
created_at: DateTime DEFAULT now()

Relacionamentos:
- permissions → UserClientPermission (1:N)
- groups → Group (1:N)
- transactions → Transaction (1:N)
- contracts → Contract (1:N)
- accounts_payable → AccountPayable (1:N)
- accounts_receivable → AccountReceivable (1:N)
- bank_statements → BankStatement (1:N)
- import_mappings → ImportMapping (1:N)
```

#### **user_client_permissions** (Permissões)
```python
id: Integer (PK)
user_id: Integer (FK → users.id)
client_id: Integer (FK → clients.id)
can_view: Boolean DEFAULT True
can_edit: Boolean DEFAULT False
can_delete: Boolean DEFAULT False

Relacionamentos:
- user → User (N:1)
- client → Client (N:1)
```

#### **groups** (Grupos)
```python
id: Integer (PK)
client_id: Integer (FK → clients.id)
name: String(100) NOT NULL
description: Text

Relacionamentos:
- client → Client (N:1)
- subgroups → Subgroup (1:N)
- transactions → Transaction (1:N)
```

#### **subgroups** (Subgrupos)
```python
id: Integer (PK)
group_id: Integer (FK → groups.id)
name: String(100) NOT NULL
description: Text

Relacionamentos:
- group → Group (N:1)
- transactions → Transaction (1:N)
```

#### **transactions** (Transações)
```python
id: Integer (PK)
client_id: Integer (FK → clients.id)
date: Date NOT NULL
description: Text NOT NULL
value: Float NOT NULL
type: String(20) NOT NULL  # entrada, saida
category: String(100)  # Classificação secundária/opcional
group_id: Integer (FK → groups.id)  # Classificação PRINCIPAL - Plano de Contas
subgroup_id: Integer (FK → subgroups.id)  # Classificação PRINCIPAL - Plano de Contas
account: String(100)
document_type: String(50)  # manual, extrato_bancario, etc
imported_from: String(255)  # nome do arquivo ou 'manual'
created_at: DateTime DEFAULT now()

Relacionamentos:
- client → Client (N:1)
- group → Group (N:1)
- subgroup → Subgroup (N:1)

Índices:
- date (para queries por período)
```

**📌 Classificação Contábil:**
- **PRIMÁRIO (Obrigatório para DRE/DFC):** `group_id` e `subgroup_id` - Representam o Plano de Contas formal
- **SECUNDÁRIO (Opcional):** `category` - Classificação adicional/descritiva, usada apenas como fallback quando não há grupo/subgrupo
- **Prioridade nos Relatórios:** DRE e DFC priorizam agrupamento por grupo/subgrupo; categoria é usada apenas para transações sem classificação formal

#### **bank_statements** (Extratos Bancários)
```python
id: Integer (PK)
client_id: Integer (FK → clients.id)
bank_name: String(100)
account: String(50)
date: Date NOT NULL
description: Text NOT NULL
value: Float NOT NULL
balance: Float
imported_at: DateTime DEFAULT now()

Relacionamentos:
- client → Client (N:1)

Índices:
- date
```

#### **contracts** (Contratos)
```python
id: Integer (PK)
client_id: Integer (FK → clients.id)
contract_start: Date NOT NULL
event_date: Date NOT NULL
service_value: Float NOT NULL
displacement_value: Float DEFAULT 0
event_type: String(100)
service_sold: String(200)
guests_count: Integer
contractor_name: String(200) NOT NULL
payment_terms: Text
status: String(50) DEFAULT 'pendente'  # pendente, em_andamento, concluido, cancelado
created_at: DateTime DEFAULT now()

Relacionamentos:
- client → Client (N:1)

Índices:
- event_date
```

#### **accounts_payable** (Contas a Pagar)
```python
id: Integer (PK)
client_id: Integer (FK → clients.id)
account_name: String(200) NOT NULL
cpf_cnpj: String(18)
due_date: Date NOT NULL
value: Float NOT NULL
month_ref: String(7)  # YYYY-MM
paid: Boolean DEFAULT False
payment_date: Date
created_at: DateTime DEFAULT now()

Relacionamentos:
- client → Client (N:1)

Índices:
- due_date
```

#### **accounts_receivable** (Contas a Receber)
```python
id: Integer (PK)
client_id: Integer (FK → clients.id)
account_name: String(200) NOT NULL
cpf_cnpj: String(18)
due_date: Date NOT NULL
value: Float NOT NULL
month_ref: String(7)  # YYYY-MM
received: Boolean DEFAULT False
receipt_date: Date
created_at: DateTime DEFAULT now()

Relacionamentos:
- client → Client (N:1)

Índices:
- due_date
```

#### **import_mappings** (Mapeamentos de Importação)
```python
id: Integer (PK)
client_id: Integer (FK → clients.id)
import_type: String(50) NOT NULL  # transactions, contracts, etc
source_column: String(100) NOT NULL  # Coluna do arquivo
target_column: String(100) NOT NULL  # Campo do sistema
transformation_rule: Text  # Regras de transformação (JSON)

Relacionamentos:
- client → Client (N:1)

Uso:
- Salva templates de mapeamento
- Reutilizável por tipo e cliente
```

---

## 🔧 Serviços

### AuthService (services/auth_service.py)

**Responsabilidade:** Autenticação e controle de acesso

**Métodos Principais:**
```python
hash_password(password: str) -> str
    # Gera hash bcrypt da senha

verify_password(password: str, hashed: str) -> bool
    # Verifica senha contra hash

authenticate(db: Session, username: str, password: str) -> Optional[User]
    # Autentica usuário

create_user(db: Session, username, password, email, role) -> User
    # Cria novo usuário

get_user_clients(db: Session, user_id: int) -> List[Client]
    # Retorna clientes que o usuário pode acessar
    # Admin vê todos, outros veem apenas com permissão

check_permission(db: Session, user_id, client_id, permission_type) -> bool
    # Verifica permissão específica (view, edit, delete)

grant_permission(db: Session, user_id, client_id, can_view, can_edit, can_delete)
    # Concede ou atualiza permissão

# Métodos de Sessão (Streamlit):
init_session_state()  # Inicializa session state
login(user)           # Realiza login
logout()              # Realiza logout
is_authenticated()    # Verifica autenticação
get_current_user()    # Retorna usuário atual
require_auth()        # Exige autenticação (decorator)
require_role(roles)   # Exige role específica
```

**Uso:**
```python
from services.auth_service import AuthService

# Autenticar
user = AuthService.authenticate(db, username, password)
if user:
    AuthService.login(user)

# Verificar permissão
if AuthService.check_permission(db, user_id, client_id, 'edit'):
    # Permite edição
```

---

### ParserService (services/parser_service.py)

**Responsabilidade:** Parse de arquivos de diferentes formatos

**Métodos Principais:**
```python
parse_csv(file_content: bytes, encoding='utf-8', delimiter=',') -> pd.DataFrame
    # Faz parse de CSV
    # Tenta múltiplos encodings automaticamente
    # Retorna DataFrame

parse_excel(file_content: bytes, sheet_name=None) -> pd.DataFrame
    # Faz parse de Excel
    # Suporta múltiplas planilhas

get_excel_sheets(file_content: bytes) -> List[str]
    # Retorna lista de planilhas do Excel

parse_pdf(file_content: bytes) -> Dict[str, Any]
    # Extrai texto e tabelas de PDF
    # Retorna: {'text': str, 'tables': list, 'num_pages': int}

parse_pdf_to_dataframe(file_content: bytes) -> Optional[pd.DataFrame]
    # Tenta extrair primeira tabela do PDF como DataFrame

parse_ofx(file_content: bytes) -> Dict[str, Any]
    # Faz parse de arquivo OFX (extratos bancários)
    # Retorna: {'bank_id', 'account_id', 'transactions', 'balance'}

ofx_to_dataframe(file_content: bytes) -> pd.DataFrame
    # Converte OFX diretamente para DataFrame

detect_delimiter(file_content: bytes, sample_size=1024) -> str
    # Detecta delimitador de CSV (,;|\t)

clean_column_names(df: pd.DataFrame) -> pd.DataFrame
    # Limpa nomes de colunas (remove espaços, caracteres especiais)

infer_column_types(df: pd.DataFrame) -> Dict[str, str]
    # Infere tipos: date, currency, numeric, text
```

**Uso:**
```python
from services.parser_service import ParserService

# Parse CSV
df = ParserService.parse_csv(file_content, encoding='utf-8', delimiter=';')

# Parse Excel
sheets = ParserService.get_excel_sheets(file_content)
df = ParserService.parse_excel(file_content, sheets[0])

# Parse OFX
df = ParserService.ofx_to_dataframe(file_content)
```

---

### ImportService (services/import_service.py)

**Responsabilidade:** Importação de dados com mapeamento de colunas

**Métodos Principais:**
```python
save_mapping(db: Session, client_id, import_type, mapping: Dict)
    # Salva template de mapeamento para reutilização

load_mapping(db: Session, client_id, import_type) -> Dict
    # Carrega template salvo

apply_mapping(df: pd.DataFrame, mapping: Dict) -> pd.DataFrame
    # Aplica mapeamento ao DataFrame

import_transactions(db, client_id, df, document_type, filename, group_id, subgroup_id) -> int
    # Importa transações
    # Retorna número de registros importados

import_bank_statements(db, client_id, df, bank_name, filename) -> int
    # Importa extratos bancários

import_contracts(db, client_id, df) -> int
    # Importa contratos

import_accounts_payable(db, client_id, df) -> int
    # Importa contas a pagar

import_accounts_receivable(db, client_id, df) -> int
    # Importa contas a receber

get_target_columns(import_type: str) -> List[str]
    # Retorna colunas alvo para cada tipo de importação
```

**Tipos de Importação:**
- `transactions` - Transações financeiras
- `bank_statements` - Extratos bancários
- `contracts` - Contratos/eventos
- `accounts_payable` - Contas a pagar
- `accounts_receivable` - Contas a receber

**Uso:**
```python
from services.import_service import ImportService

# Aplicar mapeamento
mapped_df = ImportService.apply_mapping(df, mapping)

# Importar
count = ImportService.import_transactions(
    db, client_id, mapped_df, 'extrato', 'arquivo.csv', group_id, subgroup_id
)

# Salvar template
ImportService.save_mapping(db, client_id, 'transactions', mapping)
```

---

### ReportService (services/report_service.py)

**Responsabilidade:** Geração de relatórios e análises financeiras

**Métodos Principais:**
```python
get_dre_data(db: Session, client_id, start_date, end_date) -> Dict
    # Gera dados para DRE
    # Retorna: {
    #   'receitas': float,
    #   'despesas': float,
    #   'resultado': float,
    #   'margem': float,
    #   'receitas_por_grupo': list,  # Agrupado por grupo/subgrupo (prioritário)
    #   'despesas_por_grupo': list,
    #   'receitas_por_categoria': list,  # Fallback para sem grupo/subgrupo
    #   'despesas_por_categoria': list
    # }

get_dfc_data(db: Session, client_id, start_date, end_date, group_id=None) -> Dict
    # Gera dados para DFC
    # Retorna: {
    #   'fluxo_mensal': list,  # [{mes, entradas, saidas, saldo_mes, saldo_acumulado}]
    #   'saldo_final': float,
    #   'fluxo_por_grupo': dict  # Detalhamento por grupo (se group_id fornecido)
    # }

get_dfc_projection(db: Session, client_id, months_ahead=3) -> Dict
    # Gera projeção de fluxo de caixa futuro
    # Baseado em contas a pagar/receber pendentes
    # Retorna: {
    #   'projection': list,  # [{mes, entradas_previstas, saidas_previstas, saldo_projetado}]
    #   'alerts': list  # Alertas de déficit projetado
    # }

get_seasonality_data(db: Session, client_id) -> Dict
    # Analisa sazonalidade
    # Retorna: {
    #   'por_ano': dict,  # {ano: {mes: valor}}
    #   'media_mensal': list  # [{mes, media}]
    # }

get_kpis(db: Session, client_id, start_date, end_date) -> Dict
    # Calcula KPIs principais
    # Retorna: {
    #   'receitas', 'despesas', 'resultado', 'margem',
    #   'contas_pagar', 'contas_receber',
    #   'contratos_ativos', 'valor_contratos'
    # }

export_to_excel(data: Dict[str, pd.DataFrame], filename) -> bytes
    # Exporta múltiplas abas para Excel
    # data = {'Aba1': df1, 'Aba2': df2, ...}
```

---

### AIService (services/ai_service.py)

**Responsabilidade:** Integração com serviços de IA (OpenAI, Gemini, Groq, Ollama)

**Métodos Principais:**
```python
is_available() -> bool
    # Verifica se IA está configurada e disponível

process_and_structure_data(
    df: pd.DataFrame,
    import_type: str,
    groups_subgroups: List[Dict],
    pdf_full_data: Optional[Dict] = None,
    status_callback: Optional[Callable] = None
) -> Dict
    # Processa dados com IA para mapeamento e classificação
    # Retorna: {
    #   'success': bool,
    #   'processed_data': list,  # Dados processados e classificados
    #   'summary': dict,  # Resumo (bank_name, total_lines, etc)
    #   'issues': list  # Problemas encontrados
    # }

detect_data_type(df: pd.DataFrame, pdf_full_data: Optional[Dict] = None) -> str
    # Detecta automaticamente o tipo de dado usando IA
    # Retorna: 'bank_statements', 'transactions', 'contracts', etc.
```

**Provedores Suportados:**
- OpenAI (GPT-3.5, GPT-4)
- Google Gemini
- Groq (Llama models)
- Ollama (modelos locais)

---

### AIAgentService (services/ai_agent_service.py)

**Responsabilidade:** Agente conversacional para consultas em linguagem natural

**Métodos Principais:**
```python
pre_analyze_client(client_id: int) -> Dict
    # Faz pré-análise do cliente para gerar sugestões
    # Retorna KPIs, alertas, oportunidades e sugestões

generate_greeting_with_suggestions(client_id: int, client_name: str) -> str
    # Gera saudação proativa com sugestões baseadas em dados

analyze_query(query: str, client_id: int) -> Dict
    # Analisa pergunta e identifica intenção e parâmetros
    # Retorna: {
    #   'intent': str,  # relatorio, consulta, analise, etc
    #   'data_type': str,  # transacoes, dre, dfc, etc
    #   'period': dict,  # {start, end, type}
    #   'filters': dict,  # {group, subgroup, category, type}
    #   'output_format': str  # tabela, grafico, resumo, completo
    # }

execute_query(db: Session, client_id: int, query_analysis: Dict) -> Dict
    # Executa consulta ao banco de dados baseada na análise
    # Retorna dados formatados para visualização

format_response(query_result: Dict, query_analysis: Dict, original_query: str) -> str
    # Formata resposta em markdown com insights profissionais
```

**Uso:**
```python
from services.report_service import ReportService

# DRE
dre = ReportService.get_dre_data(db, client_id, start_date, end_date)
print(f"Receitas: {dre['receitas']}")
print(f"Margem: {dre['margem']}%")

# DFC
dfc = ReportService.get_dfc_data(db, client_id, start_date, end_date)
for mes in dfc['fluxo_mensal']:
    print(f"{mes['mes']}: {mes['saldo_mes']}")

# Exportar
excel_bytes = ReportService.export_to_excel({
    'DRE': dre_df,
    'DFC': dfc_df
}, 'relatorio.xlsx')
```

---

## 🛠️ Utilitários

### validators.py

**Funções de Validação:**
```python
validate_cpf(cpf: str) -> bool
    # Valida CPF brasileiro (dígitos verificadores)

validate_cnpj(cnpj: str) -> bool
    # Valida CNPJ brasileiro (dígitos verificadores)

validate_cpf_cnpj(value: str) -> bool
    # Valida CPF ou CNPJ automaticamente

parse_date(date_str: str) -> Optional[datetime]
    # Tenta parse em múltiplos formatos:
    # dd/mm/yyyy, dd-mm-yyyy, yyyy-mm-dd, etc

parse_currency(value: str) -> Optional[float]
    # Converte string de moeda para float
    # Suporta: R$ 1.234,56 ou 1,234.56
```

### formatters.py

**Funções de Formatação:**
```python
format_cpf(cpf: str) -> str
    # Formata: 000.000.000-00

format_cnpj(cnpj: str) -> str
    # Formata: 00.000.000/0000-00

format_cpf_cnpj(value: str) -> str
    # Formata automaticamente

format_currency(value: float, symbol='R$') -> str
    # Formata: R$ 1.234,56

format_date(date: datetime, format_str='%d/%m/%Y') -> str
    # Formata data

format_month_year(date: datetime) -> str
    # Formata: MM/YYYY
```

### column_mapper.py

**Classe ColumnMapper:**
```python
normalize_column_name(col_name: str) -> str
    # Normaliza: lowercase, sem acentos, sem espaços

suggest_mapping(source_columns, target_columns) -> Dict
    # Sugere mapeamento automático
    # Usa sinônimos e similaridade de strings
    # Score > 0.6 para aceitar match

validate_mapping(mapping, required_fields) -> tuple[bool, List]
    # Valida se campos obrigatórios estão mapeados
    # Retorna: (is_valid, missing_fields)

get_required_fields(import_type: str) -> List[str]
    # Retorna campos obrigatórios por tipo

SYNONYMS: Dict
    # Dicionário de sinônimos para cada campo
    # Ex: 'date': ['data', 'dt', 'date', 'fecha', ...]
```

### ui_components.py

**Componentes Visuais:**
```python
show_client_header(client_id, compact=True)
    # Exibe header visual do cliente
    # compact=True: versão horizontal
    # compact=False: versão completa com gradiente

show_client_selector() -> Optional[int]
    # Exibe seletor de cliente com pesquisa
    # Retorna client_id selecionado
    # Mantém em session_state

show_sidebar_navigation()
    # Exibe sidebar padrão com logout

show_metric_card(label, value, icon, delta, help_text)
    # Card de métrica estilizado

show_info_box(title, content, box_type)
    # Caixa de informação colorida
    # Tipos: info, success, warning, error

show_stat_cards(stats: list)
    # Múltiplos cards em colunas
```

### top_navigation.py

**Menu de Navegação Superior:**
```python
show_top_navigation()
    # Exibe menu de navegação na parte superior da tela
    # Inclui:
    # - Header com logo e informações do usuário
    # - Seleção de cliente
    # - Agente IA em destaque
    # - Menu organizado em tabs (Início, Dados, Relatórios, Admin)
    # - Botão de logout
```

---

## 📄 Páginas

O sistema possui **24 páginas** organizadas por funcionalidade:

### app.py (Página Principal)

**Funcionalidades:**
- Login/logout (sem credenciais de teste exibidas - produção ready)
- Menu de navegação superior (top navigation) com tabs organizadas
- Agente IA em destaque no menu principal
- Seleção de cliente visível no header
- Dashboard inicial com cards informativos
- Guia rápido de uso

**Session State:**
```python
st.session_state.authenticated: bool
st.session_state.user: dict  # {id, username, email, role}
st.session_state.selected_client_id: int
```

---

### 1_Gestao_Clientes.py

**Funcionalidades:**
- Lista de clientes com busca
- Criar novo cliente (nome, CPF/CNPJ, tipo)
- Editar cliente (todos os campos)
- Excluir cliente (admin apenas)
- Ativar/desativar cliente
- Gerenciar permissões de usuários por cliente
- **Configuração de Relatórios:** Selecionar quais tipos de dados aparecem em cada relatório
- **Mapa Visual de Dados:** Visualização do fluxo de dados e conexões com relatórios

**Permissões:** Admin, Manager

**CRUD Completo:** ✅

---

### 2_Importacao_Dados.py

**Funcionalidades:**
- Upload de arquivos (CSV, Excel, PDF, OFX) - detecção automática de tipo
- **Processamento com IA:**
  - Detecção automática do tipo de dado pelo conteúdo
  - Análise completa da estrutura do arquivo
  - Mapeamento inteligente de colunas
  - Classificação automática por grupo/subgrupo
  - Extração de informações (nome do banco, datas precisas)
  - Feedback em tempo real do status de processamento
  - Alertas de baixa confiança (< 70%)
- Preview de dados:
  - Opção para visualização completa ou limitada
  - Remoção automática de linhas em branco
  - Edição direta dos dados antes da importação
- Seleção de linhas para importação
- Validação e correção de dados

**Tipos de Importação:**
- Transações financeiras
- Extratos bancários
- Contratos/eventos
- Contas a pagar
- Contas a receber
- Aplicações financeiras
- Faturas de cartão de crédito
- Extratos de maquininha
- Controle de estoque

**Fluxo:**
```
Upload → Parse Completo → IA Analisa → IA Mapeia → Preview Editável → Importar
```

---

### 2_Transacoes.py

**Funcionalidades:**
- Lista com filtros (tipo, período, busca)
- Estatísticas (entradas, saídas, saldo)
- Criar transação manual
- Editar transação (importada ou manual)
- Excluir transação
- Classificar por grupo/subgrupo

**Filtros:**
- Tipo (entrada/saída)
- Data (de/até)
- Busca por descrição

**CRUD Completo:** ✅

**Campos:**
- Data, Descrição, Valor, Tipo
- Categoria, Grupo, Subgrupo, Conta

---

### 3_Extratos_Bancarios.py

**Funcionalidades:**
- Visualização de extratos bancários importados
- Filtros por banco, período, conta
- Estatísticas por banco
- Conversão automática para transações

---

### 4_Contratos.py

**Funcionalidades:**
- Lista com filtros (status, período)
- Estatísticas (total, valor, pendentes, concluídos)
- Criar contrato (com campos expandidos: vendedor, local, horas, NF, etc.)
- Editar contrato completo
- Excluir contrato
- Alterar status
- Vinculação com contas a receber

**Status:**
- pendente
- em_andamento
- concluido
- cancelado

**CRUD Completo:** ✅

**Campos:**
- Contratante, Datas, Valores
- Tipo de evento, Serviço, Convidados
- Vendedor, Local do evento, Horas de serviço
- Número da nota fiscal, Colaboradores, Observações
- Forma de pagamento, Status

---

### 5_Contas.py

**Funcionalidades:**

#### Contas a Pagar:
- Lista com filtros
- Alertas de vencimento (vencidas, vence em 7 dias)
- Criar conta (com campos expandidos: expense_type, expense_category)
- Editar conta
- Excluir conta
- Marcar como paga
- Estatísticas

#### Contas a Receber:
- Lista com filtros
- Alertas de atraso
- Criar conta (com vinculação a contratos)
- Editar conta
- Excluir conta
- Marcar como recebida
- Estatísticas

**CRUD Completo:** ✅

---

### 6_DRE.py

**Funcionalidades:**
- Seleção de período (mês, 3m, 6m, ano, personalizado)
- KPIs: Receitas, Despesas, Resultado, Margem
- Gráfico de barras (Receitas vs Despesas)
- Gráfico de pizza (Distribuição)
- Receitas por categoria (gráfico de barras)
- Despesas por categoria (gráfico de barras)
- **Detalhamento Completo (3 níveis):**
  - Por categoria (expandível)
  - Transações por categoria (até 10)
  - Comparativo com período anterior
  - Insights e recomendações
- **Origem dos Dados:** Exibe de onde vieram os dados (extrato bancário, fatura, etc.)
- **Respeita Configuração:** Apenas exibe dados dos tipos habilitados na configuração

**Análises:**
- Margem líquida
- Despesas/Receitas
- Maior categoria
- Variação vs período anterior
- Situação (positiva/crítica)

---

### 7_DFC.py

**Funcionalidades:**
- Seleção de período (6m, ano, 2 anos, personalizado)
- KPIs: Total Entradas, Saídas, Saldo, Média
- Gráfico de fluxo mensal (barras + linha)
- Gráfico de saldo acumulado
- Análise de tendência (crescimento/queda)
- Insights (melhor mês, maior gasto, superávit/déficit)
- **Detalhamento Completo (4 níveis):**
  - Mês a mês (expandível)
  - Entradas/Saídas do mês
  - Por categoria dentro do mês
  - Transações individuais (até 5)
  - Resumo consolidado
  - Estatísticas
  - Projeção próximo mês
- **Origem dos Dados:** Exibe de onde vieram os dados
- **Respeita Configuração:** Apenas exibe dados dos tipos habilitados

**Análises:**
- Tendência (últimos 3 meses)
- Melhor/pior mês
- Médias mensais
- Projeção baseada em histórico
- Alertas de saldo negativo

---

### 8_Sazonalidade.py

**Funcionalidades:**
- Média de receitas por mês (todos os anos)
- Heatmap de receitas (ano x mês)
- Comparação ano a ano (gráfico de linhas)
- Identificação de meses fortes/fracos
- Crescimento ano a ano (métricas)
- Recomendações comerciais
- Dados detalhados (tabela)
- **Análise por Grupo/Subgrupo:** Sazonalidade por classificação contábil
- **Distribuição por Fonte:** Breakdown por tipo de dado
- **Sazonalidade de Eventos:** Análise específica de eventos
- **Respeita Configuração:** Apenas exibe dados dos tipos habilitados

**Análises:**
- Padrões sazonais
- Variação sazonal (%)
- Meses acima/abaixo da média
- Crescimento entre anos

---

### 9_Relatorios.py

**Funcionalidades:**
- Seleção de tipo de relatório
- Seleção de período
- Geração de relatórios:
  - DRE
  - DFC
  - DFC Projeção
  - Transações
  - Extratos Bancários
  - Contratos
  - Contas a Pagar
  - Contas a Receber
  - Relatório Completo (todas as abas)
- Exportação para Excel
- Download do arquivo

**Formato Excel:**
- Múltiplas abas
- Dados formatados
- Pronto para análise

---

### 10_Admin.py

**Funcionalidades:**

#### Gestão de Usuários:
- Lista de usuários
- Criar usuário
- Editar usuário (username, email, role)
- Alterar senha
- Ativar/desativar
- Excluir usuário

#### Gestão de Grupos/Subgrupos:
- Lista hierárquica
- Criar grupo
- Criar subgrupo
- Excluir grupo/subgrupo

#### Configuração de IA:
- Seleção de provedor (OpenAI, Google Gemini, Groq, Ollama)
- Configuração de chaves de API
- Seleção de modelo (com opção de entrada manual)
- Teste de conexão com IA
- Configuração de parâmetros (temperature, max_tokens)

#### Estatísticas:
- Total de usuários/clientes
- Total de transações/contratos
- Distribuição de usuários por perfil (gráfico)
- Informações do sistema

**Permissões:** Admin apenas

---

### 11_Agente_IA.py

**Funcionalidades:**
- Interface de chat conversacional
- Seleção de cliente para análise
- **Saudação Proativa:**
  - Análise automática do cliente ao iniciar
  - Sugestões baseadas em KPIs e dados do último mês
  - Alertas e oportunidades identificadas automaticamente
- **Processamento de Perguntas:**
  - Análise de intenção usando IA
  - Identificação automática de tipo de consulta
  - Extração de parâmetros (período, filtros, formato)
- **Consultas Suportadas:**
  - Transações e extratos
  - DRE e DFC
  - Contratos e contas
  - KPIs e estatísticas
  - Análises comparativas
  - Relatórios personalizados
- **Visualizações Automáticas:**
  - Gráficos gerados dinamicamente (Plotly)
  - Tabelas interativas
  - KPIs destacados
- **Exportação:**
  - Download de resultados em Excel
  - Histórico de conversas
- **Histórico Persistente:**
  - Mantém contexto da conversa
  - Permite perguntas de follow-up

**Exemplos de Perguntas:**
- "Quais são as receitas do último mês?"
- "Gere um DRE do último trimestre"
- "Compare as receitas deste ano com o ano passado"
- "Qual é o saldo atual e quantas contas estão pendentes?"
- "Mostre o fluxo de caixa dos últimos 6 meses"

---

### 12_Faturas_Cartao.py

**Funcionalidades:**
- Visualização de faturas de cartão importadas
- Filtros por período, bandeira, estabelecimento
- Estatísticas de gastos por categoria
- Análise de parcelas

---

### 13_Aplicacoes_Financeiras.py

**Funcionalidades:**
- Visualização de aplicações financeiras
- Filtros por tipo, instituição, período
- Análise de rendimentos
- Saldo atual por aplicação

---

### 14_Maquina_Cartao.py

**Funcionalidades:**
- Visualização de extratos de máquina de cartão
- Filtros por período, bandeira, tipo
- Análise de taxas e valores líquidos
- Comparação de bandeiras

---

### 15_Estoque.py

**Funcionalidades:**
- Visualização de movimentações de estoque
- Filtros por produto, tipo de movimento, período
- Análise de entradas e saídas
- Saldo atual por produto

---

### 16_Diario_Gastos.py

**Funcionalidades:**
- **KPIs:** Total de gastos, média diária, maior gasto, dias com gastos
- **Heatmap:** Visualização de gastos por dia do mês
- **Gráficos:**
  - Gastos diários (linha)
  - Distribuição por dia da semana
  - Top categorias
  - Comparação mensal
- **Filtros:** Período, categoria, grupo/subgrupo, tipo
- **Tabela Detalhada:** Todas as transações com informações completas
- **Origem dos Dados:** Exibe de onde vieram os dados

---

### 17_Relatorio_Eventos.py

**Funcionalidades:**
- **Calendário de Eventos:** Visualização mensal
- **Estatísticas:** Total de eventos, valor total, eventos por status
- **Análise de Performance:**
  - Receitas por evento
  - Eventos por tipo
  - Performance por vendedor
  - Eventos por local
- **Filtros:** Período, tipo, status, vendedor
- **Tabela Detalhada:** Todos os eventos com informações completas

---

### 18_Fluxo_Caixa_Gerencial.py

**Funcionalidades:**
- **Análise Gerencial:** Visão executiva do fluxo de caixa
- **Projeções:** Análise de tendências futuras
- **Alertas:** Identificação de possíveis problemas
- **Comparações:** Análise comparativa entre períodos
- **Respeita Configuração:** Apenas exibe dados dos tipos habilitados

---

### 19_Despesas_PF_PJ.py

**Funcionalidades:**
- **Separação CPF/CNPJ:** Análise de despesas pessoais vs empresariais
- **Gráficos:**
  - Distribuição PF vs PJ
  - Evolução temporal
  - Top despesas por tipo
- **Filtros:** Período, tipo (PF/PJ), categoria
- **Tabela Detalhada:** Todas as despesas classificadas
- **Respeita Configuração:** Apenas exibe dados dos tipos habilitados

---

### 20_Contas_Dashboard.py

**Funcionalidades:**
- **Visão Consolidada:** Contas a pagar e receber em um único dashboard
- **KPIs:** Total a pagar, total a receber, saldo, vencidas, a vencer
- **Alertas:** Contas vencidas, vencendo em breve
- **Gráficos:**
  - Distribuição por status
  - Vencimentos por mês
  - Comparação pagar vs receber
- **Filtros:** Período, status, tipo
- **Tabelas Detalhadas:** Lista completa de contas

---

### 21_Performance_Vendedores.py

**Funcionalidades:**
- **Análise por Vendedor:** Performance individual
- **Métricas:**
  - Total de vendas
  - Número de contratos
  - Ticket médio
  - Taxa de conversão
- **Gráficos:**
  - Ranking de vendedores
  - Evolução temporal
  - Distribuição por tipo de evento
- **Filtros:** Período, vendedor
- **Tabela Detalhada:** Todos os contratos por vendedor

---

### 22_Painel_Controle.py

**Funcionalidades:**
- **Visão Unificada:** Dashboard consolidado com todos os KPIs principais
- **Seções:**
  - Resumo Financeiro
  - Contas (Pagar/Receber)
  - Contratos e Eventos
  - Alertas e Notificações
- **Acesso Rápido:** Links para todas as funcionalidades
- **Respeita Configuração:** Apenas exibe dados dos tipos habilitados

---

## 🧪 Testes

### Script de Seed (tests/seed_data.py)

**Funcionalidades:**
```python
clear_database()
    # Limpa todas as tabelas

create_users(db) -> List[User]
    # Cria 3 usuários (admin, gerente, viewer)

create_clients(db) -> List[Client]
    # Cria 5 clientes com tipos diferentes

create_permissions(db, users, clients)
    # Configura permissões

create_groups_and_subgroups(db, clients)
    # Cria estrutura de classificação

generate_transactions(db, client, start_date, end_date)
    # Gera transações com sazonalidade realista
    # Alta temporada: nov-fev (15-25 transações/mês)
    # Baixa temporada: jun-ago (5-12 transações/mês)
    # Normal: outros meses (10-18 transações/mês)

generate_contracts(db, client, start_date, end_date)
    # Gera contratos distribuídos (2-8 por mês)

generate_accounts(db, client, start_date, end_date)
    # Gera contas a pagar (5-12 por mês)
    # Gera contas a receber (3-10 por mês)
```

**Execução:**
```bash
# Resetar e popular
python tests/seed_data.py --reset

# Adicionar mais dados
python tests/seed_data.py
```

**Dados Gerados:**
- 3 usuários
- 5 clientes (tipos variados)
- ~5.200 transações (2 anos)
- ~620 contratos
- ~1.000 contas a pagar
- ~850 contas a receber
- Grupos e subgrupos para cada cliente

---

## 🔧 Manutenção

### Adicionar Nova Página

1. **Crie o arquivo:**
```python
# pages/11_Nova_Pagina.py
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService
from utils.ui_components import show_client_selector, show_sidebar_navigation

st.set_page_config(page_title="Nova Página", page_icon="🆕", layout="wide")

AuthService.init_session_state()
AuthService.require_auth()

show_sidebar_navigation()

st.title("🆕 Nova Página")

client_id = show_client_selector()
if not client_id:
    st.stop()

# Seu código aqui
```

2. **Adicione ao menu (app.py):**
```python
st.page_link("pages/11_Nova_Pagina.py", label="Nova Página", icon="🆕")
```

---

### Adicionar Novo Modelo

1. **Crie o arquivo:**
```python
# models/novo_modelo.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from config.database import Base

class NovoModelo(Base):
    __tablename__ = 'novo_modelo'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    nome = Column(String(100))
    
    client = relationship('Client', back_populates='novo_modelo')
```

2. **Atualize client.py:**
```python
# Em Client, adicione:
novo_modelo = relationship('NovoModelo', back_populates='client')
```

3. **Atualize models/__init__.py:**
```python
from models.novo_modelo import NovoModelo
__all__ = [..., 'NovoModelo']
```

4. **Recrie o banco:**
```bash
python init_db.py
```

---

### Adicionar Novo Tipo de Importação

1. **Adicione ao ImportService:**
```python
# services/import_service.py

@staticmethod
def import_novo_tipo(db: Session, client_id: int, df: pd.DataFrame) -> int:
    imported_count = 0
    for _, row in df.iterrows():
        # Parse e validação
        # Criar objeto
        # db.add(objeto)
        imported_count += 1
    db.commit()
    return imported_count

@staticmethod
def get_target_columns(import_type: str) -> List[str]:
    columns_map = {
        # ... existentes ...
        'novo_tipo': ['campo1', 'campo2', 'campo3']
    }
    return columns_map.get(import_type, [])
```

2. **Adicione à página de importação:**
```python
# pages/2_Importacao_Dados.py
import_type = st.selectbox(
    "Tipo de dado:",
    options=[..., 'novo_tipo'],
    format_func=lambda x: {
        ...,
        'novo_tipo': '🆕 Novo Tipo'
    }[x]
)
```

---

### Adicionar Nova Análise ao DRE/DFC

1. **Adicione ao ReportService:**
```python
# services/report_service.py

@staticmethod
def get_nova_analise(db: Session, client_id: int, start_date, end_date) -> Dict:
    # Query de dados
    # Processamento
    # Retorna dicionário com resultados
    return {'dados': ...}
```

2. **Use na página:**
```python
# pages/6_DRE.py ou 7_DFC.py
analise = ReportService.get_nova_analise(db, client_id, start_date, end_date)
st.metric("Nova Métrica", analise['dados'])
```

---

### Alterar Tipos de Empresa

**Arquivo:** `pages/1_Gestao_Clientes.py`

**Localizar:**
```python
tipo_empresa = st.selectbox(
    "Tipo de Empresa",
    options=['', 'Eventos', 'Consultoria', 'Comércio', 'Serviços', 'Indústria', 'Outro']
)
```

**Adicionar novos tipos:**
```python
options=['', 'Eventos', 'Consultoria', 'Comércio', 'Serviços', 'Indústria', 'Tecnologia', 'Saúde', 'Outro']
```

---

### Alterar Credenciais Padrão

**Arquivo:** `tests/seed_data.py`

**Localizar:**
```python
users = [
    ('admin', 'admin123', 'admin@sistema.com', 'admin'),
    ('gerente1', 'gerente123', 'gerente1@sistema.com', 'manager'),
    ('viewer1', 'viewer123', 'viewer1@sistema.com', 'viewer'),
]
```

**Modificar:**
```python
users = [
    ('seu_admin', 'sua_senha_forte', 'seu@email.com', 'admin'),
    # ...
]
```

---

### Personalizar Grupos/Subgrupos Padrão

**Arquivo:** `tests/seed_data.py`

**Localizar:**
```python
groups_data = {
    'Receitas': ['Vendas', 'Serviços', 'Eventos', 'Consultorias'],
    'Despesas Operacionais': ['Salários', 'Aluguel', 'Energia', 'Internet', 'Material'],
    # ...
}
```

**Modificar conforme necessário**

---

### Alterar Sazonalidade dos Dados de Teste

**Arquivo:** `tests/seed_data.py`

**Função:** `generate_transactions()`

**Localizar:**
```python
# Meses de alta temporada
if month in [11, 12, 1, 2]:
    num_receitas = random.randint(15, 25)
# Meses de baixa temporada
elif month in [6, 7, 8]:
    num_receitas = random.randint(5, 12)
```

**Ajustar valores conforme padrão desejado**

---

## 🔍 Troubleshooting

### Erro: ModuleNotFoundError

**Causa:** Dependência não instalada

**Solução:**
```bash
pip install -r requirements.txt
```

---

### Erro: No module named 'config'

**Causa:** Path não configurado

**Solução:** Adicione no início do arquivo:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

---

### Erro: Table doesn't exist

**Causa:** Banco não inicializado

**Solução:**
```bash
python init_db.py
```

---

### Erro: No such column

**Causa:** Modelo alterado mas banco não atualizado

**Solução:**
```bash
# Opção 1: Resetar banco (perde dados)
python tests/seed_data.py --reset

# Opção 2: Usar Alembic (preserva dados)
alembic revision --autogenerate -m "descrição"
alembic upgrade head
```

---

### Performance Lenta

**Causas e Soluções:**

1. **Muitos dados:**
   - Adicione paginação nas queries
   - Use `limit()` nas queries
   - Adicione índices nas colunas filtradas

2. **Queries não otimizadas:**
   - Use `joinedload()` para relacionamentos
   - Evite N+1 queries
   - Use `func.count()` ao invés de `len()`

3. **Gráficos pesados:**
   - Limite dados exibidos
   - Use amostragem para grandes volumes

---

### Backup e Restauração

**Backup:**
```bash
# Copie a pasta data/
copy data\contabil.db backup\contabil_backup_20251111.db
```

**Restauração:**
```bash
# Substitua o arquivo
copy backup\contabil_backup_20251111.db data\contabil.db
```

**Backup Automático (Opcional):**
Crie script agendado no Windows:
```batch
@echo off
set data=%date:~-4%%date:~3,2%%date:~0,2%
copy data\contabil.db backups\contabil_%data%.db
```

---

## 📚 Documentação

### Tutoriais Principais

- **[📚 Tutorial Completo](docs/TUTORIAL_COMPLETO.md)** - Guia completo de todas as funcionalidades e como utilizar o sistema
- **[🚀 Tutorial de Deploy e Produção](docs/TUTORIAL_DEPLOY_PRODUCAO.md)** - Guia completo de deploy, manutenção e atualização em produção

### Documentação de Deploy

- **[🔐 Conexão SSH](docs/deploy/SSH_CONNECTION.md)** - Como conectar ao servidor via SSH
- **[📖 Deploy Hostinger VPS](docs/deploy/HOSTINGER_DEPLOY.md)** - Guia completo de deploy na Hostinger
- **[💾 Backup e Restauração](docs/deploy/BACKUP_GUIDE.md)** - Guia de backup e restauração
- **[🔄 Deploy Contínuo](docs/deploy/CONTINUOUS_DEPLOY.md)** - Configuração de deploy automatizado
- **[📊 Monitoramento PostgreSQL](docs/deploy/POSTGRESQL_MONITORING.md)** - Monitoramento do banco de dados
- **[⚡ Quick Start](docs/deploy/QUICK_START.md)** - Início rápido para deploy

---

## 🔐 Segurança

### Senhas:
- ✅ Hash bcrypt (salt automático)
- ✅ Nunca armazenadas em texto plano
- ✅ Validação no login

### SQL Injection:
- ✅ SQLAlchemy ORM (parametrizado)
- ✅ Sem queries raw
- ✅ Proteção automática

### Permissões:
- ✅ Verificação em todas as operações
- ✅ Isolamento de dados por cliente
- ✅ Logs de acesso (session state)

### Recomendações para Produção:
1. Altere senhas padrão
2. Use HTTPS (reverse proxy)
3. Configure firewall
4. Backups automáticos
5. Migre para PostgreSQL (se >100 usuários)

---

## 🚀 Deploy em Produção (VPS)

### Deploy na Hostinger VPS

O sistema agora suporta deploy em produção com PostgreSQL e configuração completa de servidor.

**Documentação completa:**
- 🔐 [Como Conectar na VPS via SSH](docs/deploy/SSH_CONNECTION.md) - **Comece aqui!**
- 📖 [Guia de Deploy - Hostinger VPS](docs/deploy/HOSTINGER_DEPLOY.md)
- 💾 [Guia de Backup e Restauração](docs/deploy/BACKUP_GUIDE.md)
- 🔄 [Guia de Deploy Contínuo](docs/deploy/CONTINUOUS_DEPLOY.md)

**Recursos incluídos:**
- ✅ Scripts de setup automatizado da VPS
- ✅ Migração automática SQLite → PostgreSQL
- ✅ Sistema de backup automático (diário, semanal, mensal)
- ✅ Configuração Nginx com SSL (Let's Encrypt)
- ✅ Serviço systemd para gerenciamento
- ✅ Scripts de deploy automatizado

**Quick Start:**
```bash
# 1. Setup inicial da VPS
sudo bash deploy/setup_vps_hostinger.sh

# 2. Configure variáveis de ambiente
cp env.example.txt .env
nano .env

# 3. Migre dados (se necessário)
python scripts/migrate_sqlite_to_postgres.py data/contabil.db postgresql://...

# 4. Deploy
sudo bash deploy/deploy.sh
```

**Sistema de Backup:**
- Backups automáticos diários, semanais e mensais
- Retenção configurável (7 dias, 4 semanas, 12 meses)
- Scripts de restauração incluídos
- Verificação de integridade automática

Para mais detalhes, consulte a [documentação completa de deploy](docs/deploy/HOSTINGER_DEPLOY.md).

---

## 🚀 Distribuição

### Método 1: Scripts .bat (Recomendado)

**Para distribuir:**
1. Compacte a pasta `contabil_system`
2. Envie para usuário
3. Usuário executa `install.bat`
4. Depois usa `run.bat`

**Tamanho:** ~50-100MB (compactado)

### Método 2: Executável .exe

**Para criar:**
```bash
# Clique em: build_exe.bat
# Aguarde 5-10 minutos
# Resultado: dist/SistemaContabil.exe
```

**Para distribuir:**
1. Copie `SistemaContabil.exe`
2. Copie `README_EXECUTAVEL.txt`
3. Envie para usuário
4. Usuário clica no .exe

**Tamanho:** ~200-300MB

---

## 📊 Estatísticas do Projeto

### Código:
- **Arquivos Python:** 35+
- **Linhas de Código:** ~8.000+
- **Modelos:** 10
- **Serviços:** 6 (incluindo IA)
- **Páginas:** 11 (incluindo Agente IA)
- **Utilitários:** 5

### Funcionalidades:
- **Páginas com CRUD:** 7
- **Dashboards:** 3
- **Agente IA Conversacional:** 1
- **Formatos de Importação:** 4
- **Tipos de Relatório:** 8 (incluindo DFC Projeção)
- **Perfis de Usuário:** 3
- **Provedores de IA:** 4 (OpenAI, Gemini, Groq, Ollama)

### Dados de Teste:
- **Clientes:** 5
- **Transações:** ~5.200
- **Contratos:** ~620
- **Contas:** ~1.900
- **Período:** 2 anos

---

## 🛠️ Dependências

### Core:
- `streamlit>=1.29.0` - Framework web
- `sqlalchemy>=2.0.0` - ORM
- `pandas>=2.0.0` - Processamento de dados
- `bcrypt>=4.1.0` - Hash de senhas

### Parsing:
- `openpyxl>=3.1.0` - Excel
- `PyPDF2>=3.0.0` - PDF
- `pdfplumber>=0.10.0` - PDF (tabelas)
- `ofxparse>=0.21` - OFX

### Visualização:
- `plotly>=5.18.0` - Gráficos interativos
- `altair>=5.2.0` - Gráficos declarativos

### IA e Processamento:
- `openai>=1.0.0` - OpenAI API (opcional)
- `google-generativeai>=0.3.0` - Google Gemini API (opcional)
- `groq>=0.4.0` - Groq API (opcional)
- `ollama>=0.1.0` - Ollama local models (opcional)

### Utilitários:
- `python-dateutil>=2.8.0` - Manipulação de datas
- `validators>=0.22.0` - Validações
- `pyyaml>=6.0.0` - Configurações

### Desenvolvimento:
- `pytest>=7.4.0` - Testes
- `faker>=21.0.0` - Dados fake

---

## 💡 Boas Práticas

### Ao Desenvolver:

1. **Sempre use o ORM:**
   ```python
   # ✅ Correto
   db.query(Transaction).filter(Transaction.client_id == client_id).all()
   
   # ❌ Evite
   db.execute("SELECT * FROM transactions WHERE client_id = ?", client_id)
   ```

2. **Feche sessões:**
   ```python
   db = SessionLocal()
   try:
       # operações
   finally:
       db.close()
   ```

3. **Verifique permissões:**
   ```python
   AuthService.require_auth()
   if not AuthService.check_permission(db, user_id, client_id, 'edit'):
       st.error("Sem permissão")
       st.stop()
   ```

4. **Use componentes reutilizáveis:**
   ```python
   from utils.ui_components import show_client_selector
   client_id = show_client_selector()
   ```

5. **Valide dados:**
   ```python
   from utils.validators import validate_cpf_cnpj, parse_currency
   if not validate_cpf_cnpj(cpf):
       st.error("CPF/CNPJ inválido")
   ```

---

## 📞 Suporte

### Problemas Comuns:

**Sistema não inicia:**
- Verifique Python instalado: `python --version`
- Execute `install.bat` novamente
- Veja logs no terminal

**Dados não aparecem:**
- Execute `reset_data.bat`
- Verifique cliente selecionado
- Verifique permissões do usuário

**Erro ao importar:**
- Verifique formato do arquivo
- Mapeie campos obrigatórios
- Veja mensagem de erro detalhada

**Performance lenta:**
- Muitos dados? Adicione filtros
- Use período menor nos dashboards
- Considere migrar para PostgreSQL

---

## 🎓 Recursos de Aprendizado

### Para Entender o Código:

1. **Comece por:**
   - `app.py` - Estrutura principal
   - `models/` - Entenda os dados
   - `services/auth_service.py` - Autenticação

2. **Depois veja:**
   - `pages/2_Transacoes.py` - CRUD exemplo
   - `services/import_service.py` - Importação
   - `services/report_service.py` - Relatórios

3. **Explore:**
   - `utils/column_mapper.py` - Mapeamento inteligente
   - `pages/6_DRE.py` - Dashboard complexo
   - `tests/seed_data.py` - Geração de dados

### Conceitos Importantes:

- **Session State:** Mantém dados entre páginas
- **Expanders:** Seções expandíveis/recolhíveis
- **Metrics:** Cards de métricas
- **Plotly:** Gráficos interativos
- **SQLAlchemy:** ORM e relacionamentos

---

## 🎉 Conclusão

**Sistema completo e profissional para gestão contábil!**

### ✅ Características:
- 📊 11 páginas funcionais (incluindo Agente IA)
- 🗃️ 10 modelos de dados
- 🔧 6 serviços principais (incluindo IA)
- 🤖 Agente IA conversacional com análise inteligente
- 📥 4 formatos de importação com processamento completo por IA
- 📈 3 dashboards analíticos + DFC Projeção
- 🔐 3 níveis de acesso
- 📋 Drill-down completo
- ✏️ CRUD em todos os módulos
- 🎨 Interface moderna com menu superior
- 📚 Documentação completa
- 🧠 Classificação automática por IA (grupos/subgrupos)

### 🚀 Pronto para:
- ✅ Uso imediato
- ✅ Distribuição
- ✅ Customização
- ✅ Manutenção
- ✅ Expansão

---

## 📄 Licença

Proprietary - Todos os direitos reservados

---

## 📧 Contato

Para dúvidas, sugestões ou suporte:
- Consulte a documentação em `docs/`
- Veja o guia de testes em `tests/TESTING_GUIDE.md`
- Execute `install.bat` para reinstalar

---

**Sistema Contábil v1.0** | Desenvolvido com ❤️ usando Streamlit





