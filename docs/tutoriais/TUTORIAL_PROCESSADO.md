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

<!-- Imagem não encontrada: screenshots/01_cmd_iniciando.png -->


**O navegador abrirá automaticamente em:**
```
http://localhost:8501
```

---

## 🔐 Passo 2: Login

### Tela de Login

![Tela de Login](screenshots/02_tela_login.png)


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


**Clique na lista suspensa:**

![Lista de Clientes](screenshots/05_lista_clientes.png)


**Você verá:**
- Empresa de Eventos Ltda [Eventos]
- Consultoria XYZ [Consultoria]
- Prestador de Serviços [Serviços]
- Comércio ABC [Comércio]
- Indústria Tech [Indústria]

**Para pesquisar:**

<!-- Imagem não encontrada: screenshots/06_pesquisa_cliente.png -->


**Digite:** "eventos"
**Resultado:** Lista filtra mostrando apenas clientes com "eventos"

---

## 📥 Passo 5: Importação de Dados

### Página de Importação

**Clique em:** 📥 Importação

![Página Importação](screenshots/07_pagina_importacao.png)


### Selecionar Tipo

![Tipo de Importação](screenshots/08_tipo_importacao.png)


**Selecione:** 🏦 Extratos Bancários

### Escolher Formato

<!-- Imagem não encontrada: screenshots/09_formato_arquivo.png -->


**Selecione:** CSV

### Upload de Arquivo

<!-- Imagem não encontrada: screenshots/10_upload_arquivo.png -->


**Clique em:** "Browse files"
**Selecione:** `tests/sample_files/extrato_bancario_exemplo.csv`

### Preview dos Dados

<!-- Imagem não encontrada: screenshots/11_preview_dados.png -->


**Você verá:**
- Tabela com as primeiras 10 linhas
- Total de linhas: 18
- Colunas: Data, Descrição, Valor, Saldo

### Mapeamento de Colunas

<!-- Imagem não encontrada: screenshots/12_mapeamento_colunas.png -->


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

<!-- Imagem não encontrada: screenshots/13_botao_importar.png -->


**Clique em:** 📥 Importar Dados

### Sucesso

<!-- Imagem não encontrada: screenshots/14_importacao_sucesso.png -->


**Mensagem:**
✅ 18 registro(s) importado(s) com sucesso!
🎈 [Animação de balões]

---

## 💳 Passo 6: Gestão de Transações

### Página de Transações

**Clique em:** 💳 Transações

<!-- Imagem não encontrada: screenshots/15_pagina_transacoes.png -->


**Elementos:**
- Seletor de cliente no topo
- Filtros (Tipo, Data, Busca)
- Cards de estatísticas (3)
- Tabela de transações

### Filtros

<!-- Imagem não encontrada: screenshots/16_filtros_transacoes.png -->


**Filtros disponíveis:**
- Tipo: Entrada/Saída (multiselect)
- Data de/até
- Busca por descrição

### Estatísticas

<!-- Imagem não encontrada: screenshots/17_estatisticas_transacoes.png -->


### Tabela de Transações

<!-- Imagem não encontrada: screenshots/18_tabela_transacoes.png -->


**Colunas:**
- ID, Data, Tipo, Descrição, Valor, Categoria, Origem

### Nova Transação

**Clique em:** Tab "➕ Nova Transação"

<!-- Imagem não encontrada: screenshots/19_nova_transacao.png -->


**Formulário:**
- Campos em 2 colunas
- Data, Descrição, Valor, Tipo
- Categoria, Grupo, Subgrupo, Conta

### Editar Transação

<!-- Imagem não encontrada: screenshots/20_editar_transacao.png -->


**Elementos:**
- Dropdown de seleção
- Formulário preenchido
- Botões Salvar e Excluir

---

## 📝 Passo 7: Gestão de Contratos

### Página de Contratos

**Clique em:** 📝 Contratos

![Página Contratos](screenshots/21_pagina_contratos.png)


### Filtros e Estatísticas

<!-- Imagem não encontrada: screenshots/22_filtros_contratos.png -->


### Tabela de Contratos

<!-- Imagem não encontrada: screenshots/23_tabela_contratos.png -->


**Colunas:**
- ID, Contratante, Data Evento, Valor Serviço, Valor Total, Status, Tipo, Convidados

### Novo Contrato

<!-- Imagem não encontrada: screenshots/24_novo_contrato.png -->


---

## 💰 Passo 8: Contas a Pagar e Receber

### Contas a Pagar

**Clique em:** 💰 Contas → Tab "💸 Contas a Pagar"

![Contas a Pagar](screenshots/25_contas_pagar.png)


**Alertas:**

<!-- Imagem não encontrada: screenshots/26_alertas_vencimento.png -->


### Registrar Pagamento

<!-- Imagem não encontrada: screenshots/27_registrar_pagamento.png -->


### Editar Conta

<!-- Imagem não encontrada: screenshots/28_editar_conta_pagar.png -->


### Contas a Receber

<!-- Imagem não encontrada: screenshots/29_contas_receber.png -->


---

## 📊 Passo 9: Dashboard DRE

### Página DRE

**Clique em:** 📊 DRE

![Dashboard DRE](screenshots/30_dashboard_dre.png)


### Seleção de Período

<!-- Imagem não encontrada: screenshots/31_periodo_dre.png -->


### KPIs Principais

![KPIs DRE](screenshots/32_kpis_dre.png)


**Métricas:**
- 💰 Receitas
- 💸 Despesas
- 📊 Resultado
- 📉 Margem

### Gráficos

![Gráfico Receitas vs Despesas](screenshots/33_grafico_receitas_despesas.png)


<!-- Imagem não encontrada: screenshots/34_grafico_pizza_dre.png -->


<!-- Imagem não encontrada: screenshots/35_receitas_categoria.png -->


<!-- Imagem não encontrada: screenshots/36_despesas_categoria.png -->


### Detalhamento Completo

<!-- Imagem não encontrada: screenshots/37_detalhamento_fechado.png -->


**Clique para expandir:**

![Detalhamento DRE Aberto](screenshots/38_detalhamento_aberto.png)


### Drill-down por Categoria

<!-- Imagem não encontrada: screenshots/39_categoria_expandida.png -->


**Mostra:**
- Total de transações
- Valor médio
- Tabela com transações individuais

### Comparativo e Insights

<!-- Imagem não encontrada: screenshots/40_comparativo_periodo.png -->


<!-- Imagem não encontrada: screenshots/41_insights_dre.png -->


---

## 💵 Passo 10: Dashboard DFC

### Página DFC

**Clique em:** 💵 DFC

![Dashboard DFC](screenshots/42_dashboard_dfc.png)


### KPIs DFC

![KPIs DFC](screenshots/43_kpis_dfc.png)


### Gráfico de Fluxo Mensal

![Fluxo Mensal](screenshots/44_fluxo_mensal.png)


### Gráfico Saldo Acumulado

<!-- Imagem não encontrada: screenshots/45_saldo_acumulado.png -->


### Análise de Tendência

<!-- Imagem não encontrada: screenshots/46_analise_tendencia.png -->


### Detalhamento DFC

<!-- Imagem não encontrada: screenshots/47_detalhamento_dfc.png -->


### Drill-down Mensal

<!-- Imagem não encontrada: screenshots/48_mes_expandido.png -->


### Categoria Expandida

<!-- Imagem não encontrada: screenshots/49_categoria_dfc_expandida.png -->


### Estatísticas e Projeção

<!-- Imagem não encontrada: screenshots/50_estatisticas_dfc.png -->


<!-- Imagem não encontrada: screenshots/51_projecao_dfc.png -->


---

## 📈 Passo 11: Sazonalidade

### Página Sazonalidade

**Clique em:** 📈 Sazonalidade

![Dashboard Sazonalidade](screenshots/52_dashboard_sazonalidade.png)


### Média Mensal

![Média Mensal](screenshots/53_media_mensal.png)


### Heatmap

![Heatmap](screenshots/54_heatmap.png)


### Comparação Ano a Ano

<!-- Imagem não encontrada: screenshots/55_comparacao_anos.png -->


### Insights de Sazonalidade

<!-- Imagem não encontrada: screenshots/56_insights_sazonalidade.png -->


<!-- Imagem não encontrada: screenshots/57_recomendacoes_sazonalidade.png -->


---

## 📑 Passo 12: Geração de Relatórios

### Página de Relatórios

**Clique em:** 📑 Relatórios

<!-- Imagem não encontrada: screenshots/58_pagina_relatorios.png -->


### Seleção de Tipo

<!-- Imagem não encontrada: screenshots/59_tipo_relatorio.png -->


### Seleção de Período

<!-- Imagem não encontrada: screenshots/60_periodo_relatorio.png -->


### Relatório Gerado

<!-- Imagem não encontrada: screenshots/61_relatorio_gerado.png -->


### Botão de Download

<!-- Imagem não encontrada: screenshots/62_download_excel.png -->


### Arquivo Excel Aberto

<!-- Imagem não encontrada: screenshots/63_excel_aberto.png -->


---

## 👥 Passo 13: Gestão de Clientes

### Página Gestão de Clientes

**Clique em:** 👥 Gestão de Clientes

<!-- Imagem não encontrada: screenshots/64_gestao_clientes.png -->


### Lista de Clientes

<!-- Imagem não encontrada: screenshots/65_lista_clientes.png -->


**Colunas:**
- ID, Nome, Tipo, CPF/CNPJ, Status, Cadastro

### Busca de Cliente

<!-- Imagem não encontrada: screenshots/66_busca_cliente.png -->


### Editar Cliente

<!-- Imagem não encontrada: screenshots/67_editar_cliente.png -->


**Campos:**
- Nome
- CPF/CNPJ
- Tipo de Empresa (dropdown)
- Ativo (checkbox)

### Novo Cliente

<!-- Imagem não encontrada: screenshots/68_novo_cliente.png -->


### Permissões

<!-- Imagem não encontrada: screenshots/69_permissoes.png -->


<!-- Imagem não encontrada: screenshots/70_configurar_permissoes.png -->


---

## ⚙️ Passo 14: Administração

### Página Admin

**Clique em:** ⚙️ Administração

<!-- Imagem não encontrada: screenshots/71_pagina_admin.png -->


### Gestão de Usuários

<!-- Imagem não encontrada: screenshots/72_lista_usuarios.png -->


### Novo Usuário

<!-- Imagem não encontrada: screenshots/73_novo_usuario.png -->


### Editar Usuário

<!-- Imagem não encontrada: screenshots/74_editar_usuario.png -->


### Grupos e Subgrupos

<!-- Imagem não encontrada: screenshots/75_grupos.png -->


<!-- Imagem não encontrada: screenshots/76_novo_grupo.png -->


### Estatísticas do Sistema

<!-- Imagem não encontrada: screenshots/77_estatisticas_sistema.png -->


<!-- Imagem não encontrada: screenshots/78_grafico_distribuicao.png -->


---

## 📱 Passo 15: Responsividade

### Visualização Mobile

<!-- Imagem não encontrada: screenshots/79_mobile_login.png -->


<!-- Imagem não encontrada: screenshots/80_mobile_dashboard.png -->


<!-- Imagem não encontrada: screenshots/81_mobile_menu.png -->


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

