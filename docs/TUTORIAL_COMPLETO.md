# 📚 Tutorial Completo - Sistema Contábil

Guia completo de todas as funcionalidades e como utilizar o sistema.

---

## 📋 Índice

1. [Primeiro Acesso](#primeiro-acesso)
2. [Gestão de Clientes](#gestão-de-clientes)
3. [Importação de Dados](#importação-de-dados)
4. [Gestão de Transações](#gestão-de-transações)
5. [Gestão de Contratos](#gestão-de-contratos)
6. [Contas a Pagar e Receber](#contas-a-pagar-e-receber)
7. [Dashboards e Relatórios](#dashboards-e-relatórios)
8. [Agente IA](#agente-ia)
9. [Administração](#administração)

---

## 1️⃣ Primeiro Acesso

### 1.1 Login

1. Acesse o sistema através do navegador
2. Na tela de login, digite suas credenciais:
   - **Usuário:** Seu nome de usuário
   - **Senha:** Sua senha
3. Clique em **"Entrar"**

### 1.2 Seleção de Cliente

Após o login:

1. Na barra lateral ou no topo da página, você verá o seletor de cliente
2. Selecione o cliente que deseja trabalhar
3. O cliente selecionado será mantido em todas as páginas

### 1.3 Navegação

O sistema possui um menu superior organizado em abas:

- **🏠 Início:** Página inicial com visão geral
- **📥 Dados:** Importação e visualização de dados
- **📊 Relatórios:** Dashboards e análises
- **⚙️ Admin:** Configurações (apenas para administradores)

---

## 2️⃣ Gestão de Clientes

### 2.1 Acessar Gestão de Clientes

1. Clique em **"👥 Gestão de Clientes"** no menu
2. Ou acesse através da aba **"Admin"** → **"Gestão de Clientes"**

### 2.2 Criar Novo Cliente

1. Na aba **"➕ Novo Cliente"**
2. Preencha os campos:
   - **Nome:** Nome completo da empresa/cliente
   - **CPF/CNPJ:** Documento (será validado automaticamente)
   - **Tipo de Empresa:** Selecione o tipo (Eventos, Consultoria, etc.)
3. Clique em **"Criar Cliente"**

### 2.3 Editar Cliente

1. Na aba **"📋 Lista de Clientes"**
2. Clique no botão **"✏️ Editar"** do cliente desejado
3. Modifique os campos necessários
4. Clique em **"Salvar Alterações"**

### 2.4 Configurar Relatórios

1. Na aba **"⚙️ Configuração de Relatórios"**
2. Selecione quais tipos de dados devem aparecer em cada relatório:
   - ✅ Transações Financeiras
   - ✅ Extratos Bancários
   - ✅ Contratos/Eventos
   - ✅ Contas a Pagar
   - ✅ Contas a Receber
   - ✅ Aplicações Financeiras
   - ✅ Faturas de Cartão
   - ✅ Extratos de Máquina de Cartão
   - ✅ Controle de Estoque
3. Clique em **"Salvar Configuração"**

**Importante:** Apenas os tipos de dados selecionados aparecerão nos relatórios (DRE, DFC, Sazonalidade, etc.)

### 2.5 Mapa Visual de Dados

1. Na aba **"🗺️ Mapa Visual de Dados"**
2. Visualize o fluxo de dados e como cada tipo se conecta aos relatórios
3. Veja quais tipos estão habilitados e desabilitados

---

## 3️⃣ Importação de Dados

### 3.1 Acessar Importação

1. Clique em **"📤 Importar Dados"** no menu
2. Ou acesse através da aba **"Dados"** → **"Importar Dados"**

### 3.2 Tipos de Arquivos Suportados

- **CSV:** Arquivos separados por vírgula ou ponto e vírgula
- **Excel:** Arquivos .xlsx ou .xls
- **PDF:** Extratos bancários e documentos em PDF
- **OFX:** Extratos bancários no formato OFX

### 3.3 Processo de Importação

#### Passo 1: Upload do Arquivo

1. Clique em **"Escolher arquivo"**
2. Selecione o arquivo que deseja importar
3. Aguarde o upload

#### Passo 2: Processamento com IA

O sistema automaticamente:

1. **Detecta o tipo de dado** (extrato bancário, transações, contratos, etc.)
2. **Analisa a estrutura** do arquivo
3. **Mapeia as colunas** para os campos do sistema
4. **Classifica automaticamente** por grupo e subgrupo
5. **Extrai informações** (nome do banco, datas, etc.)

**Status de Processamento:**
- Você verá mensagens em tempo real do progresso
- Linhas com baixa confiança (< 70%) serão destacadas

#### Passo 3: Revisar Dados

1. Visualize os dados processados na tabela
2. **Edite diretamente** se necessário:
   - Clique em uma célula para editar
   - Pressione Enter para salvar
3. **Selecione linhas** para importar:
   - Use as checkboxes à esquerda
   - Ou selecione todas com o checkbox do cabeçalho

#### Passo 4: Importar

1. Revise os dados uma última vez
2. Clique em **"Importar Dados Selecionados"**
3. Aguarde a confirmação

### 3.4 Tipos de Dados que Podem ser Importados

1. **Transações Financeiras**
   - Campos: Data, Descrição, Valor, Tipo (entrada/saída)
   - Classificação automática por grupo/subgrupo

2. **Extratos Bancários**
   - Extração automática do nome do banco
   - Conversão automática para transações
   - Preservação de saldos

3. **Contratos/Eventos**
   - Campos: Datas, Valores, Tipo de evento, Cliente, etc.
   - Campos expandidos: Vendedor, Local, Horas, NF, etc.

4. **Contas a Pagar**
   - Campos: Credor, Data de vencimento, Valor, CPF/CNPJ
   - Classificação automática

5. **Contas a Receber**
   - Campos: Devedor, Data de vencimento, Valor, CPF/CNPJ
   - Vinculação com contratos

6. **Aplicações Financeiras**
   - Campos: Tipo, Instituição, Valores, Rendimentos

7. **Faturas de Cartão**
   - Campos: Data, Descrição, Valor, Categoria, Parcelas

8. **Extratos de Máquina de Cartão**
   - Campos: Data, Valor bruto/líquido, Taxa, Bandeira

9. **Controle de Estoque**
   - Campos: Produto, Quantidade, Valor, Tipo de movimento

### 3.5 Dicas de Importação

- **PDFs:** O sistema extrai texto completo, incluindo cabeçalhos e rodapés
- **Excel:** Suporta múltiplas planilhas - todas serão processadas
- **CSV:** Detecção automática de delimitador e encoding
- **Classificação:** A IA classifica automaticamente, mas você pode revisar e corrigir
- **Confiança:** Linhas com confiança < 70% devem ser revisadas manualmente

---

## 4️⃣ Gestão de Transações

### 4.1 Acessar Transações

1. Clique em **"💳 Transações Financeiras"** no menu
2. Ou acesse através da aba **"Dados"** → **"Transações"**

### 4.2 Visualizar Transações

- **Filtros disponíveis:**
  - Tipo: Entrada ou Saída
  - Período: Data inicial e final
  - Busca: Por descrição
- **Estatísticas:** Total de entradas, saídas e saldo

### 4.3 Criar Transação Manual

1. Clique em **"➕ Nova Transação"**
2. Preencha os campos:
   - **Data:** Data da transação
   - **Descrição:** Descrição detalhada
   - **Valor:** Valor (use ponto como separador decimal)
   - **Tipo:** Entrada ou Saída
   - **Categoria:** (Opcional)
   - **Grupo/Subgrupo:** Selecione a classificação contábil
   - **Conta:** (Opcional) Banco ou conta relacionada
3. Clique em **"Salvar"**

### 4.4 Editar Transação

1. Na lista de transações, clique em **"✏️ Editar"**
2. Modifique os campos necessários
3. Clique em **"Salvar Alterações"**

### 4.5 Excluir Transação

1. Na lista de transações, clique em **"🗑️ Excluir"**
2. Confirme a exclusão

---

## 5️⃣ Gestão de Contratos

### 5.1 Acessar Contratos

1. Clique em **"📝 Contratos e Eventos"** no menu
2. Ou acesse através da aba **"Dados"** → **"Contratos"**

### 5.2 Visualizar Contratos

- **Filtros disponíveis:**
  - Status: Pendente, Em Andamento, Concluído, Cancelado
  - Período: Data inicial e final
- **Estatísticas:** Total de contratos, valor total, pendentes, concluídos

### 5.3 Criar Contrato

1. Clique em **"➕ Novo Contrato"**
2. Preencha os campos:
   - **Contratante:** Nome do cliente
   - **Data de Início:** Data de início do contrato
   - **Data do Evento:** Data do evento
   - **Valor do Serviço:** Valor principal
   - **Valor de Deslocamento:** (Opcional)
   - **Tipo de Evento:** Casamento, Aniversário, etc.
   - **Serviço Vendido:** Descrição do serviço
   - **Número de Convidados:** (Opcional)
   - **Vendedor:** Nome do vendedor
   - **Local do Evento:** (Opcional)
   - **Horas de Serviço:** (Opcional)
   - **Número da NF:** (Opcional)
   - **Colaboradores:** (Opcional)
   - **Observações:** (Opcional)
   - **Forma de Pagamento:** (Opcional)
3. Clique em **"Salvar"**

### 5.4 Alterar Status do Contrato

1. Na lista de contratos, clique em **"✏️ Editar"**
2. Altere o campo **"Status"**
3. Clique em **"Salvar Alterações"**

**Status disponíveis:**
- **Pendente:** Contrato criado, aguardando execução
- **Em Andamento:** Evento em execução
- **Concluído:** Evento finalizado
- **Cancelado:** Contrato cancelado

---

## 6️⃣ Contas a Pagar e Receber

### 6.1 Acessar Contas

1. Clique em **"💰 Contas a Pagar/Receber"** no menu
2. Ou acesse através da aba **"Dados"** → **"Contas"**

### 6.2 Contas a Pagar

#### Visualizar

- **Filtros:** Período, Status (Paga/Pendente)
- **Alertas:**
  - 🔴 Contas vencidas
  - 🟡 Contas vencendo em 7 dias
- **Estatísticas:** Total a pagar, pagas, pendentes

#### Criar Conta a Pagar

1. Na aba **"Contas a Pagar"**, clique em **"➕ Nova Conta"**
2. Preencha:
   - **Credor:** Nome do fornecedor
   - **CPF/CNPJ:** (Opcional)
   - **Data de Vencimento:** Data de vencimento
   - **Valor:** Valor a pagar
   - **Mês de Referência:** (Opcional) YYYY-MM
   - **Tipo de Despesa:** (Opcional)
   - **Categoria de Despesa:** (Opcional)
   - **Descrição:** (Opcional)
3. Clique em **"Salvar"**

#### Marcar como Paga

1. Na lista, clique em **"✅ Marcar como Paga"**
2. Informe a data de pagamento
3. Clique em **"Confirmar"**

### 6.3 Contas a Receber

#### Visualizar

- **Filtros:** Período, Status (Recebida/Pendente)
- **Alertas:** Contas em atraso
- **Estatísticas:** Total a receber, recebidas, pendentes

#### Criar Conta a Receber

1. Na aba **"Contas a Receber"**, clique em **"➕ Nova Conta"**
2. Preencha:
   - **Devedor:** Nome do cliente
   - **CPF/CNPJ:** (Opcional)
   - **Data de Vencimento:** Data de vencimento
   - **Valor:** Valor a receber
   - **Mês de Referência:** (Opcional) YYYY-MM
   - **Contrato:** (Opcional) Vincular a um contrato
3. Clique em **"Salvar"**

#### Marcar como Recebida

1. Na lista, clique em **"✅ Marcar como Recebida"**
2. Informe a data de recebimento
3. Clique em **"Confirmar"**

---

## 7️⃣ Dashboards e Relatórios

### 7.1 DRE (Demonstração do Resultado)

#### Acessar

1. Clique em **"📊 DRE"** no menu
2. Ou acesse através da aba **"Relatórios"** → **"DRE"**

#### Funcionalidades

- **KPIs Principais:**
  - Total de Receitas
  - Total de Despesas
  - Resultado (Receitas - Despesas)
  - Margem (%)

- **Gráficos:**
  - Receitas vs Despesas (Barras)
  - Distribuição (Pizza)
  - Receitas por Categoria
  - Despesas por Categoria

- **Detalhamento:**
  - Clique em uma categoria para expandir
  - Veja transações individuais
  - Compare com período anterior
  - Receba insights automáticos

- **Filtros:**
  - Período: Mês atual, 3 meses, 6 meses, 1 ano, Personalizado

#### Interpretação

- **Margem Positiva:** Receitas > Despesas (Lucro)
- **Margem Negativa:** Despesas > Receitas (Prejuízo)
- **Margem Ideal:** > 20% para a maioria dos negócios

### 7.2 DFC (Fluxo de Caixa)

#### Acessar

1. Clique em **"💵 DFC"** no menu
2. Ou acesse através da aba **"Relatórios"** → **"DFC"**

#### Funcionalidades

- **KPIs:**
  - Total de Entradas
  - Total de Saídas
  - Saldo Final
  - Média Mensal

- **Gráficos:**
  - Fluxo Mensal (Barras + Linha)
  - Saldo Acumulado
  - Tendência

- **Detalhamento:**
  - Clique em um mês para expandir
  - Veja entradas e saídas do mês
  - Veja transações por categoria
  - Veja transações individuais
  - Projeção do próximo mês

- **Alertas:**
  - Saldo negativo
  - Tendência de queda
  - Recomendações

### 7.3 Sazonalidade

#### Acessar

1. Clique em **"📈 Sazonalidade"** no menu
2. Ou acesse através da aba **"Relatórios"** → **"Sazonalidade"**

#### Funcionalidades

- **Análises:**
  - Média de receitas por mês
  - Heatmap (Ano x Mês)
  - Comparação ano a ano
  - Crescimento ano a ano

- **Identificação:**
  - Meses fortes (acima da média)
  - Meses fracos (abaixo da média)
  - Padrões sazonais

- **Recomendações:**
  - Sugestões comerciais baseadas em padrões
  - Estratégias para meses fracos

- **Análises Adicionais:**
  - Por Grupo/Subgrupo
  - Por Fonte de Dados
  - Sazonalidade de Eventos

### 7.4 Diário de Gastos

#### Acessar

1. Clique em **"📅 Diário de Gastos"** no menu
2. Ou acesse através da aba **"Relatórios"** → **"Diário de Gastos"**

#### Funcionalidades

- **KPIs:**
  - Total de Gastos
  - Média Diária
  - Maior Gasto
  - Dias com Gastos

- **Visualizações:**
  - Heatmap de gastos por dia
  - Gráfico de gastos diários
  - Distribuição por dia da semana
  - Top categorias
  - Comparação mensal

- **Filtros:**
  - Período
  - Categoria
  - Grupo/Subgrupo
  - Tipo

### 7.5 Outros Relatórios

#### Fluxo de Caixa Gerencial

- Visão executiva do fluxo de caixa
- Projeções e tendências
- Alertas gerenciais

#### Despesas CPF vs CNPJ

- Separação de despesas pessoais e empresariais
- Análise comparativa
- Gráficos de distribuição

#### Dashboard de Contas

- Visão consolidada de contas a pagar e receber
- Status de pagamentos
- Alertas de vencimento

#### Performance de Vendedores

- Análise de vendas por vendedor
- Métricas de performance
- Ranking de vendedores

#### Relatório de Eventos

- Calendário de eventos
- Análise de contratos
- Performance de eventos

#### Painel de Controle Unificado

- Visão geral consolidada
- KPIs principais
- Acesso rápido a todas as funcionalidades

### 7.6 Exportação de Relatórios

1. Acesse **"📑 Relatórios e Exportação"**
2. Selecione o tipo de relatório
3. Selecione o período
4. Clique em **"Gerar Relatório"**
5. Clique em **"📥 Download Excel"**

**Tipos de Relatórios Exportáveis:**
- DRE
- DFC
- DFC Projeção
- Transações
- Contratos
- Contas a Pagar
- Contas a Receber
- Relatório Completo (todas as abas)

---

## 8️⃣ Agente IA

### 8.1 Acessar Agente IA

1. Clique em **"🤖 Agente IA"** no menu (destaque especial)
2. Ou acesse através da aba **"Início"** → **"Agente IA"**

### 8.2 Funcionalidades

#### Saudação Proativa

Ao iniciar uma conversa, o Agente IA:

1. **Analisa automaticamente** o cliente selecionado
2. **Identifica KPIs** principais
3. **Gera sugestões** baseadas nos dados
4. **Apresenta alertas** e oportunidades

#### Fazer Perguntas

Você pode fazer perguntas em linguagem natural:

**Exemplos:**
- "Quais são as receitas do último mês?"
- "Gere um DRE do último trimestre"
- "Compare as receitas deste ano com o ano passado"
- "Qual é o saldo atual e quantas contas estão pendentes?"
- "Mostre o fluxo de caixa dos últimos 6 meses"
- "Quais são os principais gastos deste mês?"
- "Quantos contratos estão pendentes?"

#### Visualizações Automáticas

O Agente IA gera automaticamente:

- **Gráficos interativos** (Plotly)
- **Tabelas detalhadas**
- **KPIs destacados**
- **Insights e recomendações**

#### Exportar Resultados

1. Após receber uma resposta, clique em **"📥 Exportar para Excel"**
2. O arquivo será baixado com os dados formatados

#### Histórico de Conversas

- O sistema mantém o contexto da conversa
- Você pode fazer perguntas de follow-up
- O histórico é preservado durante a sessão

### 8.3 Dicas de Uso

- **Seja específico:** Quanto mais detalhes, melhor a resposta
- **Mencione períodos:** "último mês", "este ano", "últimos 3 meses"
- **Peça comparações:** "compare X com Y"
- **Solicite visualizações:** "mostre um gráfico de..."
- **Peça análises:** "analise as despesas de..."

---

## 9️⃣ Administração

### 9.1 Acessar Administração

1. Clique em **"⚙️ Administração"** no menu
2. **Apenas administradores** têm acesso

### 9.2 Gestão de Usuários

#### Criar Usuário

1. Na aba **"👥 Usuários"**
2. Clique em **"➕ Novo Usuário"**
3. Preencha:
   - **Usuário:** Nome de usuário
   - **Email:** Email válido
   - **Senha:** Senha forte
   - **Perfil:** Admin, Manager ou Viewer
4. Clique em **"Criar Usuário"**

#### Editar Usuário

1. Na lista, clique em **"✏️ Editar"**
2. Modifique os campos
3. Clique em **"Salvar Alterações"**

#### Alterar Senha

1. Na lista, clique em **"🔑 Alterar Senha"**
2. Digite a nova senha
3. Confirme a senha
4. Clique em **"Alterar"**

#### Ativar/Desativar Usuário

1. Na lista, clique em **"✅ Ativar"** ou **"❌ Desativar"**

### 9.3 Gestão de Grupos e Subgrupos

#### Criar Grupo

1. Na aba **"🏷️ Grupos e Subgrupos"**
2. Selecione o cliente
3. Clique em **"➕ Novo Grupo"**
4. Preencha:
   - **Nome:** Nome do grupo (ex: "Receitas", "Despesas")
   - **Descrição:** (Opcional)
5. Clique em **"Criar"**

#### Criar Subgrupo

1. Selecione um grupo existente
2. Clique em **"➕ Novo Subgrupo"**
3. Preencha:
   - **Nome:** Nome do subgrupo (ex: "Vendas", "Fornecedores")
   - **Descrição:** (Opcional)
4. Clique em **"Criar"**

#### Excluir Grupo/Subgrupo

1. Clique em **"🗑️ Excluir"**
2. Confirme a exclusão

**Atenção:** Ao excluir um grupo, todos os subgrupos também serão excluídos.

### 9.4 Configuração de IA

#### Configurar Provedor

1. Na aba **"🤖 Configuração de IA"**
2. Selecione o provedor:
   - **OpenAI:** GPT-3.5 ou GPT-4
   - **Google Gemini:** Gemini Pro
   - **Groq:** Llama models
   - **Ollama:** Modelos locais
3. Configure a chave de API
4. Selecione o modelo
5. Clique em **"Salvar Configuração"**

#### Testar Conexão

1. Clique em **"🧪 Testar Conexão"**
2. Aguarde a confirmação

#### Parâmetros Avançados

- **Temperature:** Controla a criatividade (0.0 a 1.0)
- **Max Tokens:** Limite de tokens por resposta

### 9.5 Estatísticas do Sistema

Na aba **"📊 Estatísticas"**, visualize:

- Total de usuários
- Total de clientes
- Total de transações
- Total de contratos
- Distribuição de usuários por perfil

---

## 🔟 Dicas e Boas Práticas

### 10.1 Importação de Dados

- **Revise sempre** as classificações automáticas
- **Corrija** linhas com baixa confiança
- **Importe em lotes** pequenos para melhor controle
- **Mantenha backups** antes de importações grandes

### 10.2 Classificação Contábil

- **Use grupos/subgrupos** consistentemente
- **Crie grupos** antes de importar dados
- **Revise periodicamente** as classificações
- **Padronize** nomes de categorias

### 10.3 Relatórios

- **Configure** quais tipos de dados aparecem em cada relatório
- **Use períodos** consistentes para comparações
- **Exporte regularmente** para backup
- **Analise tendências** ao longo do tempo

### 10.4 Segurança

- **Altere senhas** regularmente
- **Use senhas fortes**
- **Não compartilhe** credenciais
- **Revise permissões** periodicamente

### 10.5 Manutenção

- **Faça backups** regularmente
- **Monitore** o uso do sistema
- **Atualize** quando houver novas versões
- **Reporte problemas** ao administrador

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Consulte este tutorial
2. Verifique a documentação de deploy
3. Entre em contato com o administrador do sistema

---

**Sistema Contábil v1.0** | Tutorial Completo | Última atualização: Novembro 2025

