# Guia de Testes - Sistema Contábil

## Credenciais de Acesso

Após executar o script de seed (`python tests/seed_data.py --reset`), use as seguintes credenciais:

- **Admin**: `admin` / `admin123` (acesso total)
- **Gerente**: `gerente1` / `gerente123` (acesso aos Clientes A e B)
- **Visualizador**: `viewer1` / `viewer123` (apenas visualização do Cliente A)

## Clientes de Teste

1. **Empresa de Eventos Ltda** (CNPJ: 12.345.678/0001-90)
2. **Consultoria XYZ** (CNPJ: 98.765.432/0001-10)
3. **Prestador de Serviços** (CPF: 123.456.789-00)

## Dados Gerados

O script de seed gera automaticamente:
- **2 anos de dados** (do dia atual retroativo)
- **Transações financeiras** com sazonalidade realista
- **Contratos e eventos** distribuídos ao longo do período
- **Contas a pagar e receber** com diferentes status
- **Grupos e subgrupos** para classificação

## Checklist de Testes

### 1. Autenticação e Controle de Acesso

- [ ] Login com admin
- [ ] Login com gerente
- [ ] Login com visualizador
- [ ] Logout
- [ ] Tentativa de acesso sem login (deve redirecionar)
- [ ] Tentativa de acesso a página admin com perfil não-admin (deve bloquear)

### 2. Gestão de Clientes (Admin/Gerente)

- [ ] Visualizar lista de clientes
- [ ] Criar novo cliente
- [ ] Editar cliente existente
- [ ] Desativar cliente
- [ ] Buscar cliente por nome ou CPF/CNPJ
- [ ] Atribuir permissões a usuários
- [ ] Verificar que gerente só vê clientes com permissão

### 3. Importação de Dados

#### Teste com CSV
- [ ] Upload de arquivo CSV
- [ ] Detecção automática de delimitador
- [ ] Preview dos dados
- [ ] Mapeamento automático de colunas
- [ ] Mapeamento manual de colunas
- [ ] Salvar template de mapeamento
- [ ] Reutilizar template salvo
- [ ] Importar transações
- [ ] Importar contas a pagar
- [ ] Importar contas a receber

#### Teste com Excel
- [ ] Upload de arquivo Excel
- [ ] Seleção de planilha (se múltiplas)
- [ ] Mapeamento e importação

#### Teste com OFX
- [ ] Upload de arquivo OFX
- [ ] Importação automática de extratos

### 4. Gestão de Contratos

- [ ] Visualizar lista de contratos
- [ ] Filtrar por status
- [ ] Filtrar por período
- [ ] Criar novo contrato
- [ ] Editar contrato existente
- [ ] Alterar status do contrato
- [ ] Visualizar estatísticas (total, valor, pendentes, concluídos)
- [ ] Excluir contrato

### 5. Contas a Pagar e Receber

#### Contas a Pagar
- [ ] Visualizar lista de contas
- [ ] Filtrar por status (pagas/pendentes)
- [ ] Filtrar por período
- [ ] Ver alertas de contas vencidas
- [ ] Ver alertas de contas a vencer
- [ ] Cadastrar nova conta
- [ ] Marcar conta como paga
- [ ] Visualizar estatísticas

#### Contas a Receber
- [ ] Visualizar lista de contas
- [ ] Filtrar por status (recebidas/pendentes)
- [ ] Filtrar por período
- [ ] Ver alertas de contas atrasadas
- [ ] Cadastrar nova conta
- [ ] Marcar conta como recebida
- [ ] Visualizar estatísticas

### 6. Dashboard DRE

- [ ] Selecionar diferentes períodos (mês, 3 meses, 6 meses, ano, personalizado)
- [ ] Visualizar KPIs (receitas, despesas, resultado, margem)
- [ ] Ver gráfico de receitas vs despesas
- [ ] Ver gráfico de pizza do resultado
- [ ] Ver receitas por categoria
- [ ] Ver despesas por categoria
- [ ] Expandir detalhamento DRE completo

### 7. Dashboard DFC

- [ ] Selecionar diferentes períodos
- [ ] Visualizar KPIs (total entradas, saídas, saldo, média)
- [ ] Ver gráfico de fluxo mensal (entradas, saídas, saldo)
- [ ] Ver gráfico de saldo acumulado
- [ ] Ver análise de tendência
- [ ] Ver insights (melhor mês, maior gasto, superávit/déficit)
- [ ] Expandir detalhamento mensal

### 8. Dashboard Sazonalidade

- [ ] Ver média de receitas por mês
- [ ] Ver heatmap de receitas por ano e mês
- [ ] Ver comparação ano a ano
- [ ] Ver insights (melhor/pior mês, variação sazonal)
- [ ] Ver recomendações (meses fortes/fracos)
- [ ] Ver crescimento ano a ano
- [ ] Expandir dados detalhados

### 9. Relatórios e Exportação

- [ ] Gerar relatório DRE
- [ ] Gerar relatório DFC
- [ ] Gerar relatório de Transações
- [ ] Gerar relatório de Contratos
- [ ] Gerar relatório de Contas a Pagar
- [ ] Gerar relatório de Contas a Receber
- [ ] Gerar Relatório Completo (todas as abas)
- [ ] Exportar para Excel
- [ ] Abrir arquivo Excel exportado e verificar dados

### 10. Administração (Admin apenas)

#### Usuários
- [ ] Visualizar lista de usuários
- [ ] Criar novo usuário
- [ ] Editar usuário existente
- [ ] Alterar senha de usuário
- [ ] Desativar usuário
- [ ] Excluir usuário
- [ ] Verificar que não pode excluir próprio usuário

#### Grupos e Subgrupos
- [ ] Visualizar grupos existentes
- [ ] Criar novo grupo
- [ ] Excluir grupo
- [ ] Visualizar subgrupos
- [ ] Criar novo subgrupo
- [ ] Excluir subgrupo

#### Estatísticas
- [ ] Ver estatísticas do sistema
- [ ] Ver distribuição de usuários por perfil
- [ ] Ver informações do sistema

## Cenários de Teste Específicos

### Cenário 1: Fluxo Completo de Importação
1. Fazer login como admin
2. Selecionar Cliente A
3. Ir para Importação de Dados
4. Fazer upload de CSV com transações
5. Mapear colunas
6. Salvar mapeamento
7. Importar dados
8. Verificar no dashboard DRE que os dados aparecem

### Cenário 2: Análise Comparativa de 2 Anos
1. Fazer login como admin
2. Selecionar Cliente A
3. Ir para Dashboard de Sazonalidade
4. Verificar que há dados de 2 anos
5. Analisar heatmap e comparação ano a ano
6. Identificar padrões sazonais
7. Exportar relatório completo

### Cenário 3: Gestão de Permissões
1. Fazer login como admin
2. Criar novo usuário gerente
3. Atribuir permissão apenas para Cliente B
4. Fazer logout
5. Fazer login com novo gerente
6. Verificar que só vê Cliente B
7. Tentar acessar página de Admin (deve bloquear)

### Cenário 4: Controle Financeiro Completo
1. Fazer login como gerente
2. Selecionar Cliente A
3. Cadastrar novo contrato
4. Cadastrar contas a receber relacionadas
5. Cadastrar contas a pagar
6. Marcar algumas como pagas/recebidas
7. Ver alertas de vencimento
8. Verificar impacto no DRE e DFC

## Resultados Esperados

### Dados de Teste
- Aproximadamente **1.200-1.500 transações** por cliente (2 anos)
- Aproximadamente **150-200 contratos** por cliente
- Aproximadamente **200-300 contas a pagar** por cliente
- Aproximadamente **150-200 contas a receber** por cliente

### Sazonalidade
- Meses de **novembro, dezembro, janeiro e fevereiro** devem ter mais receitas (alta temporada)
- Meses de **junho, julho e agosto** devem ter menos receitas (baixa temporada)
- Outros meses com valores intermediários

### Dashboards
- **DRE**: Deve mostrar receitas > despesas (resultado positivo na maioria dos meses)
- **DFC**: Saldo acumulado deve ser crescente ao longo do tempo
- **Sazonalidade**: Deve mostrar padrões claros de alta e baixa temporada

## Problemas Conhecidos e Soluções

### Problema: Banco de dados não existe
**Solução**: Execute `python init_db.py` antes de rodar o seed

### Problema: Erro ao importar módulos
**Solução**: Certifique-se de estar no diretório correto e que o ambiente virtual está ativado

### Problema: Dados não aparecem nos dashboards
**Solução**: Verifique se o cliente correto está selecionado na sidebar

### Problema: Permissões não funcionam
**Solução**: Faça logout e login novamente após alterar permissões

## Comandos Úteis

```bash
# Inicializar banco de dados
python init_db.py

# Popular com dados de teste (limpa antes)
python tests/seed_data.py --reset

# Popular sem limpar (adiciona mais dados)
python tests/seed_data.py

# Executar aplicação
streamlit run app.py

# Instalar dependências
pip install -r requirements.txt
```

## Notas Importantes

1. Os dados de teste são **gerados aleatoriamente** mas seguem padrões realistas
2. A **sazonalidade é intencional** para permitir análises comparativas
3. Os **2 anos de dados** permitem comparações ano a ano
4. Grupos e subgrupos são criados automaticamente para cada cliente
5. As permissões de usuários são configuradas automaticamente no seed

## Suporte

Para problemas ou dúvidas:
1. Verifique este guia primeiro
2. Consulte o README.md
3. Verifique os logs do terminal
4. Execute o seed novamente com `--reset` se necessário


