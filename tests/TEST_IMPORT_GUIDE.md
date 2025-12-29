# Guia de Testes de Importação

Este documento descreve como testar o sistema de importação de dados com a arquitetura MCP.

## Arquivos de Teste

Os arquivos de teste estão localizados em `tests/sample_files/`:

- `transactions.csv` - Transações financeiras
- `bank_statements.csv` - Extratos bancários
- `credit_card_invoices.csv` - Faturas de cartão de crédito
- `contracts.xlsx` - Contratos/Eventos
- `accounts_payable.csv` - Contas a pagar
- `accounts_receivable.csv` - Contas a receber
- `financial_investments.csv` - Extratos de aplicações financeiras
- `card_machine_statements.csv` - Extratos de máquina de cartão
- `inventory.csv` - Controle de estoque

## Scripts de Teste

### 1. Teste Completo (`test_full_import_flow.py`)

Testa o fluxo completo de importação para todos os tipos de arquivo:

```bash
python scripts/test_full_import_flow.py
```

**O que testa:**
- Carregamento de arquivo
- Detecção de tipo de dado
- Análise de estrutura
- Mapeamento de colunas
- Normalização de dados
- Validação de dados
- Verificação de dados na tabela de revisão

**Saída:**
- Relatório detalhado por tipo
- Resumo de sucessos/falhas
- Estatísticas de cada etapa

### 2. Teste Interativo (`test_import_interactive.py`)

Permite testar importação de arquivo específico e ver cada etapa:

```bash
python scripts/test_import_interactive.py
```

**Funcionalidades:**
- Menu interativo para escolher tipo de arquivo
- Visualização de cada etapa do processo
- Exibição de dados em cada etapa
- Útil para debug e validação manual

## Fluxo de Teste

```
1. Carregar Arquivo
   ↓
2. Detecção de Tipo (MCP Tool: detect_data_type)
   ↓
3. Análise de Estrutura
   ↓
4. Mapeamento de Colunas (MCP Tool: map_columns)
   ↓
5. Normalização de Dados (MCP Tool: normalize_data)
   ↓
6. Validação (MCP Tool: validate_data)
   ↓
7. Verificação na Tabela de Revisão
```

## Validações

Para cada tipo de arquivo, verificar:

- ✅ Detecção de tipo funciona corretamente
- ✅ Mapeamento cria correspondências corretas
- ✅ Normalização formata dados corretamente
- ✅ Validação identifica problemas
- ✅ Dados aparecem na tabela de revisão
- ✅ Colunas destino estão preenchidas
- ✅ Valores estão no formato correto

## Problemas Comuns

### Mapeamento vazio
- **Causa**: IA não conseguiu mapear colunas
- **Solução**: Sistema usa fallback automático (ColumnMapper.suggest_mapping)

### Normalização retorna vazio
- **Causa**: Erro no processamento de dados
- **Solução**: Sistema aplica mapeamento direto aos dados originais

### Dados não aparecem na tabela de revisão
- **Causa**: Colunas destino não foram preenchidas
- **Solução**: Verificar mapeamento e normalização, garantir que todas as colunas destino existem

### Validação encontra problemas
- **Causa**: Dados não estão no formato esperado
- **Solução**: Verificar formato dos dados de entrada e ajustar normalização

## Executando Testes

### Ambiente
Certifique-se de que:
- Banco de dados está configurado
- Variáveis de ambiente estão definidas (`.env`)
- IA está disponível (API key configurada)

### Executar todos os testes
```bash
cd Contabil/contabil_system
python scripts/test_full_import_flow.py
```

### Executar teste interativo
```bash
cd Contabil/contabil_system
python scripts/test_import_interactive.py
```

## Interpretando Resultados

### Sucesso
- Todas as etapas completadas sem erros
- Dados aparecem corretamente na tabela de revisão
- Validação passa sem problemas críticos

### Avisos
- Tipo detectado diferente do esperado (mas ainda funcional)
- Validação encontrou problemas menores
- Mapeamento parcial (algumas colunas não mapeadas)

### Falhas
- Erro em alguma etapa crítica
- Dados não aparecem na tabela de revisão
- Mapeamento completamente falhou

## Próximos Passos

Após executar os testes:
1. Revisar relatório de resultados
2. Corrigir problemas identificados
3. Re-executar testes para validar correções
4. Documentar problemas encontrados e soluções



