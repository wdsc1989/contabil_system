# 🧪 Guia de Testes - Integração MCP

Este guia explica como testar a nova implementação MCP para processamento de dados.

## 📋 Pré-requisitos

1. **Banco de dados configurado**: SQLite ou PostgreSQL
2. **Python 3.8+** instalado
3. **Dependências instaladas**: `pip install -r requirements.txt`
4. **API Key de IA configurada** (opcional, para testes completos com IA)

## 🚀 Testes Automatizados

### Teste Rápido (Sem IA)

Execute o script de teste que valida a estrutura sem chamar APIs de IA:

```bash
cd Contabil/contabil_system
python scripts/test_mcp_integration.py
```

Este teste verifica:
- ✅ Geração de schemas para todos os 9 tipos de dados
- ✅ Definições de MCP tools
- ✅ Geração de prompts estruturados
- ✅ Integração entre componentes
- ✅ Métodos auxiliares do AIMultiAgent

### Resultado Esperado

```
============================================================
TESTES DE INTEGRAÇÃO MCP
============================================================

============================================================
TESTE 1: Schema Generator
============================================================

📊 Testando transactions...
  ✅ Schema gerado: 8 propriedades
  ✅ Colunas destino: 8 colunas
  ✅ Especificações: 8 colunas
  ✅ Descrição gerada
...

✅ Schema Generator: 9/9 tipos testados com sucesso

============================================================
TESTE 2: MCP Tools
============================================================

📋 Testando definições de tools...
  ✅ 4 tools definidos

🔧 Testando tool: detect_data_type...
  ✅ Prompt gerado (1234 caracteres)
...

✅ MCP Tools: 4/4 tools testados com sucesso

============================================================
RESUMO DOS TESTES
============================================================
✅ PASSOU - Schema Generator
✅ PASSOU - MCP Tools
✅ PASSOU - AIMultiAgent
✅ PASSOU - Fluxo de Integração

============================================================
Total: 4/4 testes passaram
============================================================

🎉 Todos os testes passaram! Integração MCP está funcionando.
```

## 🧪 Testes Manuais via Interface

### 1. Teste de Detecção de Tipo

1. Acesse a página **"Importação de Dados"** no sistema
2. Faça upload de um arquivo CSV/Excel com dados financeiros
3. Selecione **"Usar IA para detectar tipo"**
4. Verifique se o tipo é detectado corretamente

**Arquivo de teste (transactions.csv)**:
```csv
Data,Descrição,Valor
01/01/2024,Pix enviado,100.00
02/01/2024,Transferência recebida,500.00
```

**Resultado esperado**: Tipo detectado como `transactions`

### 2. Teste de Mapeamento de Colunas

1. Após detectar o tipo, o sistema deve mapear automaticamente as colunas
2. Verifique se o mapeamento está correto:
   - `Data` → `date`
   - `Descrição` → `description`
   - `Valor` → `value`

### 3. Teste de Normalização

1. Após o mapeamento, os dados devem ser normalizados
2. Verifique se:
   - Datas estão no formato `YYYY-MM-DD`
   - Valores monetários são números (float)
   - Textos estão limpos

**Exemplo de normalização**:
```json
{
  "date": "2024-01-01",
  "description": "Pix enviado",
  "value": 100.0
}
```

### 4. Teste de Validação

1. Antes da inserção, os dados devem ser validados
2. Verifique se:
   - Todos os campos obrigatórios estão presentes
   - Tipos de dados estão corretos
   - Não há valores inválidos

## 🔍 Testes por Tipo de Dado

### Transactions
```csv
Data,Descrição,Valor,Tipo
01/01/2024,Compra no mercado,150.00,saida
02/01/2024,Salário recebido,3000.00,entrada
```

### Bank Statements
```csv
Data,Descrição,Valor,Saldo
01/01/2024,Pix enviado,100.00,5000.00
02/01/2024,Depósito,500.00,5500.00
```

### Credit Card Invoices
```csv
Data,Estabelecimento,Valor,Bandeira,Parcela
01/01/2024,Supermercado ABC,200.00,Mastercard,1/3
```

### Contracts
```csv
Data Início,Data Evento,Contratante,Valor Serviço
01/01/2024,15/01/2024,João Silva,5000.00
```

## 🐛 Troubleshooting

### Erro: "Schema não gerado"
- Verifique se os modelos SQLAlchemy estão importados corretamente
- Execute: `python -c "from services.mcp_schema_generator import MCPSchemaGenerator; print('OK')"`

### Erro: "MCP tools não encontrados"
- Verifique se o arquivo `services/mcp_tools.py` existe
- Execute: `python -c "from services.mcp_tools import MCPTools; print('OK')"`

### Erro: "AIMultiAgent não tem mcp_tools"
- Verifique se o `__init__` do AIMultiAgent inicializa `self.mcp_tools`
- Execute o script de teste para verificar

### Erro na detecção de tipo
- Verifique se a API key de IA está configurada
- Verifique os logs para ver o prompt gerado
- Teste com diferentes formatos de arquivo

## 📊 Verificação de Schemas

Para verificar os schemas gerados para um tipo específico:

```python
from services.mcp_schema_generator import MCPSchemaGenerator
import json

generator = MCPSchemaGenerator()

# Ver schema completo
schema = generator.get_schema_for_data_type('transactions')
print(json.dumps(schema, indent=2, ensure_ascii=False))

# Ver colunas destino
columns = generator.get_target_columns('transactions')
print(f"Colunas: {columns}")

# Ver especificações
specs = generator.get_column_specifications('transactions')
print(json.dumps(specs, indent=2, ensure_ascii=False))
```

## ✅ Checklist de Testes

- [ ] Schema Generator gera schemas para todos os 9 tipos
- [ ] MCP Tools geram prompts estruturados
- [ ] AIMultiAgent usa MCP tools corretamente
- [ ] Detecção de tipo funciona na interface
- [ ] Mapeamento de colunas funciona
- [ ] Normalização de dados funciona
- [ ] Validação de dados funciona
- [ ] Inserção no banco funciona após validação

## 🎯 Testes de Performance

Para testar performance com arquivos grandes:

```python
import pandas as pd
from services.ai_multi_agent import AIMultiAgent
from config.database import SessionLocal

# Cria DataFrame grande
df = pd.DataFrame({
    'Data': ['01/01/2024'] * 1000,
    'Descrição': ['Teste'] * 1000,
    'Valor': [100.0] * 1000
})

db = SessionLocal()
agent = AIMultiAgent(db)

# Testa processamento em lote
import time
start = time.time()
normalized = agent.agent_extract_and_format(
    df.to_dict('records'),
    'transactions',
    {'Data': 'date', 'Descrição': 'description', 'Valor': 'value'}
)
end = time.time()

print(f"Processados {len(normalized)} registros em {end-start:.2f}s")
```

## 📝 Logs e Debug

Para ver os prompts gerados pelos MCP tools:

```python
from services.mcp_tools import MCPTools
from config.database import SessionLocal

db = SessionLocal()
tools = MCPTools(db_session=db)

prompt = tools.get_tool_prompt(
    'detect_data_type',
    columns=['Data', 'Descrição', 'Valor'],
    data_sample='{"Data": "01/01/2024", "Descrição": "Pix", "Valor": "100"}'
)

print(prompt)
```

## 🎉 Conclusão

Após executar todos os testes e verificar que estão passando, a integração MCP está funcionando corretamente e pronta para uso em produção!



