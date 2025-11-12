# 🎓 Tutorial com Imagens - Sistema Contábil

## Guia Visual Completo com Screenshots

---

## 📸 Como Usar Este Tutorial

Este tutorial usa imagens reais do sistema. Para melhor experiência:
1. Abra o sistema em uma aba do navegador
2. Siga este tutorial em outra aba
3. Compare as telas
4. Pratique cada passo

---

## 🚀 Passo 1: Iniciar o Sistema

### Executar o Sistema

**Clique duas vezes no arquivo:**
```
run.bat
```

**Você verá esta janela:**

![CMD Iniciando](screenshots/01_cmd_iniciando.png)
> **📸 Capturar:** Janela CMD com mensagem "Iniciando Sistema Contábil..."

**O navegador abrirá automaticamente em:**
```
http://localhost:8501
```

---

## 🔐 Passo 2: Login

### Tela de Login

![Tela de Login](screenshots/02_tela_login.png)
> **📸 Capturar:** Tela inicial com formulário de login

**O que você vê:**
- Título: "🔐 Sistema Contábil"
- Campo "Usuário"
- Campo "Senha"
- Botão "Entrar"
- Credenciais de teste exibidas

**Digite:**
- **Usuário:** `admin`
- **Senha:** `admin123`

**Clique em:** Entrar

---

## 🏠 Passo 3: Tela Inicial

### Página Principal

![Tela Inicial](screenshots/03_tela_inicial.png)
> **📸 Capturar:** Página inicial completa com sidebar e conteúdo

**Elementos da tela:**

**Sidebar (Esquerda):**
- Informações do usuário
- Seletor de cliente
- Menu de navegação

**Conteúdo Principal:**
- Título "Bem-vindo"
- Card do cliente selecionado
- Cards informativos (4 colunas)
- Guia rápido (expandível)

---

## 🏢 Passo 4: Seleção de Cliente

### Seletor de Cliente na Sidebar

![Seletor de Cliente](screenshots/04_seletor_cliente.png)
> **📸 Capturar:** Sidebar com foco no seletor de cliente

**Clique na lista suspensa:**

![Lista de Clientes](screenshots/05_lista_clientes.png)
> **📸 Capturar:** Lista suspensa aberta mostrando os 5 clientes

**Você verá:**
- Empresa de Eventos Ltda [Eventos]
- Consultoria XYZ [Consultoria]
- Prestador de Serviços [Serviços]
- Comércio ABC [Comércio]
- Indústria Tech [Indústria]

**Para pesquisar:**

![Pesquisa de Cliente](screenshots/06_pesquisa_cliente.png)
> **📸 Capturar:** Digite "eventos" na lista e mostre filtro funcionando

**Digite:** "eventos"
**Resultado:** Lista filtra mostrando apenas clientes com "eventos"

---

## 📥 Passo 5: Importação de Dados

### Página de Importação

**Clique em:** 📥 Importação

![Página Importação](screenshots/07_pagina_importacao.png)
> **📸 Capturar:** Página de importação completa

### Selecionar Tipo

![Tipo de Importação](screenshots/08_tipo_importacao.png)
> **📸 Capturar:** Dropdown "Tipo de dado" aberto

**Selecione:** 🏦 Extratos Bancários

### Escolher Formato

![Formato Arquivo](screenshots/09_formato_arquivo.png)
> **📸 Capturar:** Radio buttons de formato

**Selecione:** CSV

### Upload de Arquivo

![Upload Arquivo](screenshots/10_upload_arquivo.png)
> **📸 Capturar:** Área de upload de arquivo

**Clique em:** "Browse files"
**Selecione:** `tests/sample_files/extrato_bancario_exemplo.csv`

### Preview dos Dados

![Preview Dados](screenshots/11_preview_dados.png)
> **📸 Capturar:** Tabela de preview com dados do CSV

**Você verá:**
- Tabela com as primeiras 10 linhas
- Total de linhas: 18
- Colunas: Data, Descrição, Valor, Saldo

### Mapeamento de Colunas

![Mapeamento Colunas](screenshots/12_mapeamento_colunas.png)
> **📸 Capturar:** Interface de mapeamento completa

**Mapeamento sugerido:**
```
Data        → date
Descrição   → description
Valor       → value
Saldo       → balance
```

**Mensagem:**
✅ Todos os campos obrigatórios foram mapeados!

### Importar Dados

![Botão Importar](screenshots/13_botao_importar.png)
> **📸 Capturar:** Botões "Salvar Mapeamento" e "Importar Dados"

**Clique em:** 📥 Importar Dados

### Sucesso

![Importação Sucesso](screenshots/14_importacao_sucesso.png)
> **📸 Capturar:** Mensagem de sucesso com balões

**Mensagem:**
✅ 18 registro(s) importado(s) com sucesso!
🎈 [Animação de balões]

---

## 💳 Passo 6: Gestão de Transações

### Página de Transações

**Clique em:** 💳 Transações

![Página Transações](screenshots/15_pagina_transacoes.png)
> **📸 Capturar:** Página completa de transações

**Elementos:**
- Seletor de cliente no topo
- Filtros (Tipo, Data, Busca)
- Cards de estatísticas (3)
- Tabela de transações

### Filtros

![Filtros Transações](screenshots/16_filtros_transacoes.png)
> **📸 Capturar:** Linha de filtros em uso

**Filtros disponíveis:**
- Tipo: Entrada/Saída (multiselect)
- Data de/até
- Busca por descrição

### Estatísticas

![Estatísticas](screenshots/17_estatisticas_transacoes.png)
> **📸 Capturar:** Cards de métricas (Entradas, Saídas, Saldo)

### Tabela de Transações

![Tabela Transações](screenshots/18_tabela_transacoes.png)
> **📸 Capturar:** Tabela completa com dados

**Colunas:**
- ID, Data, Tipo, Descrição, Valor, Categoria, Origem

### Nova Transação

**Clique em:** Tab "➕ Nova Transação"

![Nova Transação](screenshots/19_nova_transacao.png)
> **📸 Capturar:** Formulário de nova transação

**Formulário:**
- Campos em 2 colunas
- Data, Descrição, Valor, Tipo
- Categoria, Grupo, Subgrupo, Conta

### Editar Transação

![Editar Transação](screenshots/20_editar_transacao.png)
> **📸 Capturar:** Seção de edição com dropdown e formulário

**Elementos:**
- Dropdown de seleção
- Formulário preenchido
- Botões Salvar e Excluir

---

## 📝 Passo 7: Gestão de Contratos

### Página de Contratos

**Clique em:** 📝 Contratos

![Página Contratos](screenshots/21_pagina_contratos.png)
> **📸 Capturar:** Página completa de contratos

### Filtros e Estatísticas

![Filtros Contratos](screenshots/22_filtros_contratos.png)
> **📸 Capturar:** Filtros de status e período + cards de estatísticas

### Tabela de Contratos

![Tabela Contratos](screenshots/23_tabela_contratos.png)
> **📸 Capturar:** Tabela com contratos

**Colunas:**
- ID, Contratante, Data Evento, Valor Serviço, Valor Total, Status, Tipo, Convidados

### Novo Contrato

![Novo Contrato](screenshots/24_novo_contrato.png)
> **📸 Capturar:** Formulário de novo contrato (2 colunas)

---

## 💰 Passo 8: Contas a Pagar e Receber

### Contas a Pagar

**Clique em:** 💰 Contas → Tab "💸 Contas a Pagar"

![Contas a Pagar](screenshots/25_contas_pagar.png)
> **📸 Capturar:** Página completa com alertas

**Alertas:**

![Alertas Vencimento](screenshots/26_alertas_vencimento.png)
> **📸 Capturar:** Alertas de contas vencidas e a vencer

### Registrar Pagamento

![Registrar Pagamento](screenshots/27_registrar_pagamento.png)
> **📸 Capturar:** Seção de registro de pagamento

### Editar Conta

![Editar Conta Pagar](screenshots/28_editar_conta_pagar.png)
> **📸 Capturar:** Formulário de edição de conta

### Contas a Receber

![Contas a Receber](screenshots/29_contas_receber.png)
> **📸 Capturar:** Tab de contas a receber

---

## 📊 Passo 9: Dashboard DRE

### Página DRE

**Clique em:** 📊 DRE

![Dashboard DRE](screenshots/30_dashboard_dre.png)
> **📸 Capturar:** Dashboard completo (scroll para mostrar tudo)

### Seleção de Período

![Período DRE](screenshots/31_periodo_dre.png)
> **📸 Capturar:** Dropdown de seleção de período

### KPIs Principais

![KPIs DRE](screenshots/32_kpis_dre.png)
> **📸 Capturar:** 4 cards de métricas principais

**Métricas:**
- 💰 Receitas
- 💸 Despesas
- 📊 Resultado
- 📉 Margem

### Gráficos

![Gráfico Receitas vs Despesas](screenshots/33_grafico_receitas_despesas.png)
> **📸 Capturar:** Gráfico de barras (Receitas vs Despesas)

![Gráfico Pizza](screenshots/34_grafico_pizza_dre.png)
> **📸 Capturar:** Gráfico de pizza do resultado

![Receitas por Categoria](screenshots/35_receitas_categoria.png)
> **📸 Capturar:** Gráfico de barras de receitas por categoria

![Despesas por Categoria](screenshots/36_despesas_categoria.png)
> **📸 Capturar:** Gráfico de barras de despesas por categoria

### Detalhamento Completo

![Detalhamento DRE Fechado](screenshots/37_detalhamento_fechado.png)
> **📸 Capturar:** Expander "Detalhamento Completo" fechado

**Clique para expandir:**

![Detalhamento DRE Aberto](screenshots/38_detalhamento_aberto.png)
> **📸 Capturar:** Detalhamento expandido mostrando estrutura

### Drill-down por Categoria

![Categoria Expandida](screenshots/39_categoria_expandida.png)
> **📸 Capturar:** Uma categoria de receita expandida mostrando transações

**Mostra:**
- Total de transações
- Valor médio
- Tabela com transações individuais

### Comparativo e Insights

![Comparativo Período](screenshots/40_comparativo_periodo.png)
> **📸 Capturar:** Seção de comparativo com período anterior

![Insights DRE](screenshots/41_insights_dre.png)
> **📸 Capturar:** Seção de insights e recomendações

---

## 💵 Passo 10: Dashboard DFC

### Página DFC

**Clique em:** 💵 DFC

![Dashboard DFC](screenshots/42_dashboard_dfc.png)
> **📸 Capturar:** Dashboard DFC completo

### KPIs DFC

![KPIs DFC](screenshots/43_kpis_dfc.png)
> **📸 Capturar:** 4 cards de métricas do fluxo de caixa

### Gráfico de Fluxo Mensal

![Fluxo Mensal](screenshots/44_fluxo_mensal.png)
> **📸 Capturar:** Gráfico com barras (entradas/saídas) e linha (saldo)

### Gráfico Saldo Acumulado

![Saldo Acumulado](screenshots/45_saldo_acumulado.png)
> **📸 Capturar:** Gráfico de área do saldo acumulado

### Análise de Tendência

![Tendência](screenshots/46_analise_tendencia.png)
> **📸 Capturar:** Cards de análise de tendência e insights

### Detalhamento DFC

![Detalhamento DFC](screenshots/47_detalhamento_dfc.png)
> **📸 Capturar:** Expander do detalhamento expandido

### Drill-down Mensal

![Mês Expandido](screenshots/48_mes_expandido.png)
> **📸 Capturar:** Um mês expandido mostrando entradas e saídas

### Categoria Expandida

![Categoria DFC](screenshots/49_categoria_dfc_expandida.png)
> **📸 Capturar:** Categoria dentro do mês expandida com transações

### Estatísticas e Projeção

![Estatísticas DFC](screenshots/50_estatisticas_dfc.png)
> **📸 Capturar:** Seção de estatísticas do período

![Projeção](screenshots/51_projecao_dfc.png)
> **📸 Capturar:** Seção de projeção do próximo mês

---

## 📈 Passo 11: Sazonalidade

### Página Sazonalidade

**Clique em:** 📈 Sazonalidade

![Dashboard Sazonalidade](screenshots/52_dashboard_sazonalidade.png)
> **📸 Capturar:** Dashboard completo de sazonalidade

### Média Mensal

![Média Mensal](screenshots/53_media_mensal.png)
> **📸 Capturar:** Gráfico de barras com média por mês

### Heatmap

![Heatmap](screenshots/54_heatmap.png)
> **📸 Capturar:** Heatmap de receitas por ano e mês

### Comparação Ano a Ano

![Comparação Anos](screenshots/55_comparacao_anos.png)
> **📸 Capturar:** Gráfico de linhas comparando anos

### Insights de Sazonalidade

![Insights Sazonalidade](screenshots/56_insights_sazonalidade.png)
> **📸 Capturar:** Cards com insights (melhor/pior mês, variação)

![Recomendações](screenshots/57_recomendacoes_sazonalidade.png)
> **📸 Capturar:** Seção de recomendações

---

## 📑 Passo 12: Geração de Relatórios

### Página de Relatórios

**Clique em:** 📑 Relatórios

![Página Relatórios](screenshots/58_pagina_relatorios.png)
> **📸 Capturar:** Página de relatórios

### Seleção de Tipo

![Tipo Relatório](screenshots/59_tipo_relatorio.png)
> **📸 Capturar:** Dropdown de tipo de relatório aberto

### Seleção de Período

![Período Relatório](screenshots/60_periodo_relatorio.png)
> **📸 Capturar:** Campos de data inicial e final

### Relatório Gerado

![Relatório Gerado](screenshots/61_relatorio_gerado.png)
> **📸 Capturar:** Preview do relatório gerado

### Botão de Download

![Download Excel](screenshots/62_download_excel.png)
> **📸 Capturar:** Botão de download do Excel

### Arquivo Excel Aberto

![Excel Aberto](screenshots/63_excel_aberto.png)
> **📸 Capturar:** Arquivo Excel aberto mostrando múltiplas abas

---

## 👥 Passo 13: Gestão de Clientes

### Página Gestão de Clientes

**Clique em:** 👥 Gestão de Clientes

![Gestão Clientes](screenshots/64_gestao_clientes.png)
> **📸 Capturar:** Página completa com tabs

### Lista de Clientes

![Lista Clientes](screenshots/65_lista_clientes.png)
> **📸 Capturar:** Tabela com todos os clientes

**Colunas:**
- ID, Nome, Tipo, CPF/CNPJ, Status, Cadastro

### Busca de Cliente

![Busca Cliente](screenshots/66_busca_cliente.png)
> **📸 Capturar:** Campo de busca em uso

### Editar Cliente

![Editar Cliente](screenshots/67_editar_cliente.png)
> **📸 Capturar:** Formulário de edição de cliente

**Campos:**
- Nome
- CPF/CNPJ
- Tipo de Empresa (dropdown)
- Ativo (checkbox)

### Novo Cliente

![Novo Cliente](screenshots/68_novo_cliente.png)
> **📸 Capturar:** Tab "Novo Cliente" com formulário

### Permissões

![Permissões](screenshots/69_permissoes.png)
> **📸 Capturar:** Tab de permissões

![Configurar Permissões](screenshots/70_configurar_permissoes.png)
> **📸 Capturar:** Formulário de permissões por cliente

---

## ⚙️ Passo 14: Administração

### Página Admin

**Clique em:** ⚙️ Administração

![Página Admin](screenshots/71_pagina_admin.png)
> **📸 Capturar:** Página de administração com tabs

### Gestão de Usuários

![Lista Usuários](screenshots/72_lista_usuarios.png)
> **📸 Capturar:** Tabela de usuários

### Novo Usuário

![Novo Usuário](screenshots/73_novo_usuario.png)
> **📸 Capturar:** Formulário de novo usuário

### Editar Usuário

![Editar Usuário](screenshots/74_editar_usuario.png)
> **📸 Capturar:** Formulário de edição com campos preenchidos

### Grupos e Subgrupos

![Grupos](screenshots/75_grupos.png)
> **📸 Capturar:** Tab de grupos e subgrupos

![Novo Grupo](screenshots/76_novo_grupo.png)
> **📸 Capturar:** Formulário de novo grupo

### Estatísticas do Sistema

![Estatísticas Sistema](screenshots/77_estatisticas_sistema.png)
> **📸 Capturar:** Cards de estatísticas gerais

![Gráfico Distribuição](screenshots/78_grafico_distribuicao.png)
> **📸 Capturar:** Gráfico de pizza de distribuição de usuários

---

## 📱 Passo 15: Responsividade

### Visualização Mobile

![Mobile Login](screenshots/79_mobile_login.png)
> **📸 Capturar:** Tela de login em dispositivo móvel

![Mobile Dashboard](screenshots/80_mobile_dashboard.png)
> **📸 Capturar:** Dashboard em mobile

![Mobile Menu](screenshots/81_mobile_menu.png)
> **📸 Capturar:** Menu hamburger aberto

---

## 🎯 Guia de Captura de Screenshots

### Como Capturar as Telas:

**Windows:**
1. **Tela inteira:** Pressione `Print Screen`
2. **Janela ativa:** Pressione `Alt + Print Screen`
3. **Área selecionada:** Pressione `Windows + Shift + S`

**Salvar:**
1. Abra Paint ou editor de imagem
2. Cole (`Ctrl + V`)
3. Recorte área desejada
4. Salve como PNG
5. Nomeie conforme número acima (ex: `01_cmd_iniciando.png`)

### Organização:

Crie pasta:
```
contabil_system/
└── screenshots/
    ├── 01_cmd_iniciando.png
    ├── 02_tela_login.png
    ├── 03_tela_inicial.png
    ├── ...
    └── 81_mobile_menu.png
```

### Checklist de Capturas:

**Essenciais (mínimo):**
- [ ] 02 - Tela de login
- [ ] 03 - Tela inicial
- [ ] 05 - Lista de clientes
- [ ] 11 - Preview de dados
- [ ] 12 - Mapeamento de colunas
- [ ] 14 - Importação sucesso
- [ ] 15 - Página transações
- [ ] 30 - Dashboard DRE
- [ ] 42 - Dashboard DFC
- [ ] 52 - Dashboard Sazonalidade

**Completas (todas 81):**
- [ ] Todas as telas listadas acima

---

## 🔄 Atualizar Tutorial com Imagens

### Após Capturar:

1. **Salve imagens** em `screenshots/`
2. **Nomeie corretamente** (01_xxx.png, 02_xxx.png, etc)
3. **Imagens aparecem** automaticamente no tutorial
4. **Compartilhe** tutorial + pasta screenshots

### Formato das Imagens:

- **Formato:** PNG (melhor qualidade)
- **Resolução:** 1920x1080 ou similar
- **Tamanho:** Comprima se > 500KB
- **Nome:** Número + descrição (ex: 02_tela_login.png)

---

## 📦 Distribuir Tutorial com Imagens

### Opção 1: Pasta Completa
```
Compartilhe:
- TUTORIAL_COM_IMAGENS.md
- screenshots/ (pasta com todas as imagens)
```

### Opção 2: PDF
```
1. Abra TUTORIAL_COM_IMAGENS.md
2. Converta para PDF (com imagens)
3. Distribua PDF único
```

### Opção 3: Vídeo
```
1. Grave tela seguindo o tutorial
2. Adicione narração
3. Exporte como MP4
4. Compartilhe vídeo
```

---

## ✅ Próximos Passos

### Para Completar Este Tutorial:

1. **Execute o sistema:**
   ```
   run.bat
   ```

2. **Capture as telas:**
   - Use Windows + Shift + S
   - Siga a ordem numérica
   - Salve em screenshots/

3. **Verifique:**
   - Todas as 81 imagens capturadas
   - Nomes corretos
   - Qualidade boa

4. **Teste:**
   - Abra o tutorial
   - Verifique se imagens aparecem
   - Ajuste se necessário

5. **Distribua:**
   - Tutorial + screenshots
   - Ou converta para PDF

---

## 🎉 Resultado

**Tutorial visual completo estruturado!**

- ✅ **81 pontos** de captura identificados
- ✅ **Todas as funcionalidades** cobertas
- ✅ **Ordem lógica** de aprendizado
- ✅ **Descrições** de cada tela
- ✅ **Guia de captura** incluído
- ✅ **Pronto** para adicionar imagens

**Capture as telas e terá um tutorial visual completo!** 📸

---

## 💡 Alternativa: Tutorial em Vídeo

Se preferir, pode criar um vídeo tutorial:

1. **Grave a tela** (Windows + G para Game Bar)
2. **Siga este tutorial** como roteiro
3. **Narre** cada passo
4. **Edite** o vídeo
5. **Publique** (YouTube, Vimeo, etc)

**Vantagem:** Mais dinâmico e fácil de seguir!

---

**Tutorial estruturado e pronto para screenshots!** 🎬


