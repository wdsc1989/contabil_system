"""
MCP Tools para processamento de dados financeiros
Implementa tools estruturados para detecção, mapeamento, normalização e validação
"""
from typing import Dict, List, Any, Optional
import json
import re
from datetime import datetime

from services.mcp_schema_generator import MCPSchemaGenerator
from config.ai_config import AIConfigManager


class MCPTools:
    """
    Implementa MCP Tools para processamento de dados
    """
    
    DATA_TYPES = {
        'transactions': 'Transações Financeiras',
        'bank_statements': 'Extratos Bancários',
        'contracts': 'Contratos/Eventos',
        'accounts_payable': 'Contas a Pagar',
        'accounts_receivable': 'Contas a Receber',
        'financial_investments': 'Extratos de Aplicações Financeiras',
        'credit_card_invoices': 'Faturas de Cartão de Crédito',
        'card_machine_statements': 'Extratos de Máquina de Cartão',
        'inventory': 'Controle de Estoque'
    }
    
    def __init__(self, db_session=None):
        """
        Inicializa MCP Tools
        
        Args:
            db_session: Sessão do banco de dados (opcional, para validações futuras)
        """
        self.db = db_session
        self.schema_generator = MCPSchemaGenerator()
    
    def get_detect_data_type_tool_definition(self) -> Dict[str, Any]:
        """
        Retorna definição do tool para detecção de tipo de dado
        """
        return {
            "name": "detect_data_type",
            "description": "Detecta o tipo de dado financeiro baseado em colunas e amostras de dados",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de nomes de colunas do arquivo"
                    },
                    "data_sample": {
                        "type": "string",
                        "description": "Amostra dos dados (primeiras 20 linhas em JSON ou texto)"
                    }
                },
                "required": ["columns", "data_sample"]
            }
        }
    
    def get_map_columns_tool_definition(self) -> Dict[str, Any]:
        """
        Retorna definição do tool para mapeamento de colunas
        """
        return {
            "name": "map_columns",
            "description": "Mapeia colunas origem para colunas destino baseado no schema da tabela",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "import_type": {
                        "type": "string",
                        "enum": list(self.DATA_TYPES.keys()),
                        "description": "Tipo de dado a ser importado"
                    },
                    "source_columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de colunas origem"
                    },
                    "columns_analysis": {
                        "type": "string",
                        "description": "Análise das colunas origem (opcional)"
                    }
                },
                "required": ["import_type", "source_columns"]
            }
        }
    
    def get_normalize_data_tool_definition(self) -> Dict[str, Any]:
        """
        Retorna definição do tool para normalização de dados
        """
        return {
            "name": "normalize_data",
            "description": "Normaliza e formata dados conforme schema da tabela destino",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "import_type": {
                        "type": "string",
                        "enum": list(self.DATA_TYPES.keys()),
                        "description": "Tipo de dado a ser importado"
                    },
                    "mapping": {
                        "type": "object",
                        "description": "Mapeamento de colunas origem → destino"
                    },
                    "records": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Registros a serem normalizados"
                    }
                },
                "required": ["import_type", "mapping", "records"]
            }
        }
    
    def get_validate_data_tool_definition(self) -> Dict[str, Any]:
        """
        Retorna definição do tool para validação de dados
        """
        return {
            "name": "validate_data",
            "description": "Valida dados normalizados antes da inserção no banco",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "import_type": {
                        "type": "string",
                        "enum": list(self.DATA_TYPES.keys()),
                        "description": "Tipo de dado a ser validado"
                    },
                    "normalized_records": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Registros normalizados a serem validados"
                    }
                },
                "required": ["import_type", "normalized_records"]
            }
        }
    
    def get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Retorna todas as definições de tools
        """
        return [
            self.get_detect_data_type_tool_definition(),
            self.get_map_columns_tool_definition(),
            self.get_normalize_data_tool_definition(),
            self.get_validate_data_tool_definition()
        ]
    
    def _create_detect_type_prompt(self, columns: List[str], data_sample: str) -> str:
        """
        Cria prompt para detecção de tipo usando contexto estruturado
        Após detectar, informa a estrutura da tabela destino
        """
        data_types_list = "\n".join([
            f"{i+1}. {key} - {value}" 
            for i, (key, value) in enumerate(self.DATA_TYPES.items())
        ])
        
        # Adiciona informações sobre estrutura de cada tipo
        structures_info = "\n".join([
            f"- {key}: {self.schema_generator.get_table_structure_description(key)[:200]}..."
            for key in self.DATA_TYPES.keys()
        ])
        
        return f"""Você é um especialista em análise de dados financeiros. Identifique o tipo de dado e, após a detecção, a estrutura da tabela destino será informada para mapeamento preciso.

TIPOS DISPONÍVEIS:
{data_types_list}

INDICADORES POR TIPO:
- transactions: data, descrição, valor (sem saldo, sem bandeira/cartão)
- bank_statements: data, descrição, valor, saldo (OBRIGATÓRIO - diferencia de transactions)
- credit_card_invoices: data, estabelecimento, valor, bandeira (Visa/Mastercard), parcela
- contracts: contract_start, event_date, contractor_name, service_value
- accounts_payable: account_name/fornecedor, due_date, value
- accounts_receivable: account_name/cliente, due_date, value
- financial_investments: date, investment_type, applied_value/redeemed_value
- card_machine_statements: date, gross_value, fee, net_value
- inventory: product_name, quantity, unit_value, movement_type

ESTRUTURAS DAS TABELAS DESTINO (para referência):
{structures_info}

COLUNAS DO ARQUIVO: {', '.join(columns)}
AMOSTRA DE DADOS:
{data_sample}

Analise os dados e retorne JSON com:
{{
    "suggested_type": "tipo_identificado",
    "confidence": 0.0-1.0,
    "reasoning": "explicação curta",
    "key_indicators": ["indicador1", "indicador2"]
}}

IMPORTANTE: Após identificar o tipo, o sistema usará a estrutura exata da tabela destino para mapear apenas as colunas necessárias."""
    
    def _create_map_columns_prompt(
        self, 
        import_type: str, 
        source_columns: List[str],
        columns_analysis: Optional[str] = None
    ) -> str:
        """
        Cria prompt para mapeamento de colunas usando schema
        Foca apenas nas colunas necessárias para a tabela destino
        """
        schema = self.schema_generator.get_schema_for_data_type(import_type)
        target_columns = self.schema_generator.get_target_columns(import_type)
        column_specs = self.schema_generator.get_column_specifications(import_type)
        table_structure = self.schema_generator.get_table_structure_description(import_type)
        
        # Separa colunas obrigatórias e opcionais
        required_columns = [col for col, spec in column_specs.items() if spec.get('required', False)]
        optional_columns = [col for col, spec in column_specs.items() if not spec.get('required', False)]
        
        # Cria lista detalhada de colunas destino com exemplos e sinônimos
        required_specs = "\n".join([
            f"  * {col}: {spec['type']} (OBRIGATÓRIO) - {spec.get('description', '')}"
            for col, spec in column_specs.items() 
            if spec.get('required', False)
        ])
        
        optional_specs = "\n".join([
            f"  - {col}: {spec['type']} (opcional) - {spec.get('description', '')}"
            for col, spec in column_specs.items() 
            if not spec.get('required', False)
        ])
        
        analysis_text = f"\n**ANÁLISE DAS COLUNAS ORIGEM:**\n{columns_analysis}" if columns_analysis else ""
        
        return f"""Você é um especialista em mapeamento de dados financeiros. Sua tarefa é mapear APENAS as colunas origem que correspondem às colunas destino necessárias para a tabela {import_type}.

**TIPO DE DADOS DETECTADO:** {import_type}
**ESTRUTURA DA TABELA DESTINO:**
{table_structure}

**COLUNAS DESTINO OBRIGATÓRIAS (devem ser mapeadas):**
{required_specs}

**COLUNAS DESTINO OPCIONAIS (mapear se houver correspondência):**
{optional_specs}

**COLUNAS ORIGEM DISPONÍVEIS:**
{', '.join(source_columns)}
{analysis_text}

**REGRAS DE MAPEAMENTO:**
1. PRIORIZE mapear as colunas OBRIGATÓRIAS primeiro
2. Mapeie apenas colunas origem que realmente correspondem às colunas destino
3. IGNORE colunas origem que não têm correspondência na tabela destino
4. Use correspondência por:
   - Nome similar (ex: "Data" → "date", "Valor" → "value")
   - Conteúdo similar (ex: coluna com datas → "date")
   - Contexto (ex: coluna com descrições → "description")
5. Se uma coluna origem não mapeia para nenhuma destino, NÃO inclua no mapeamento

**IMPORTANTE:**
- Foque APENAS nas colunas que existem na estrutura da tabela destino acima
- Não invente colunas destino que não existem
- Se não houver correspondência clara, deixe a coluna origem sem mapeamento

Retorne APENAS JSON (sem markdown, sem texto adicional):
{{
    "mapping": {{
        "coluna_origem": "coluna_destino"
    }},
    "unmapped_destinations": ["colunas destino obrigatórias sem mapeamento"],
    "unmapped_sources": ["colunas origem que não mapeiam para nenhuma destino"],
    "inferred_mappings": {{
        "coluna_destino": "como será inferida (se aplicável)"
    }}
}}"""
    
    def _create_normalize_data_prompt(
        self,
        import_type: str,
        mapping: Dict[str, str],
        records: List[Dict[str, Any]]
    ) -> str:
        """
        Cria prompt para normalização de dados usando schema
        Foca apenas nas colunas mapeadas e necessárias para a tabela destino
        """
        schema = self.schema_generator.get_schema_for_data_type(import_type)
        target_columns = self.schema_generator.get_target_columns(import_type)
        column_specs = self.schema_generator.get_column_specifications(import_type)
        table_structure = self.schema_generator.get_table_structure_description(import_type)
        
        records_json = json.dumps(records[:10], indent=2, default=str, ensure_ascii=False)
        
        # Lista apenas colunas que estão no mapeamento ou são obrigatórias
        mapped_target_columns = set(mapping.values())
        required_columns = {col for col, spec in column_specs.items() if spec.get('required', False)}
        relevant_columns = mapped_target_columns.union(required_columns)
        
        specs_text = "\n".join([
            f"  - {col}: {spec['type']} ({spec.get('format', '')}) {'[OBRIGATÓRIO]' if spec.get('required', False) else '[OPCIONAL]'}"
            for col, spec in column_specs.items()
            if col in relevant_columns
        ])
        
        return f"""Você é um especialista em normalização de dados financeiros. Normalize os registros APENAS para as colunas da tabela destino {import_type}.

**ESTRUTURA DA TABELA DESTINO:**
{table_structure}

**MAPEAMENTO ORIGEM → DESTINO (use apenas este mapeamento):**
{json.dumps(mapping, indent=2, ensure_ascii=False)}

**COLUNAS DESTINO RELEVANTES (apenas as que serão usadas):**
{specs_text}

**REGISTROS ORIGEM (amostra):**
{records_json}

**REGRAS CRÍTICAS DE NORMALIZAÇÃO:**
1. **USE APENAS O MAPEAMENTO:** Para cada coluna destino, busque o valor na coluna origem mapeada
2. **Datas:** Converter para YYYY-MM-DD (ex: "15/01/2024" → "2024-01-15")
3. **Valores monetários:** Converter para float (ex: "R$ 200,00" → 200.0)
4. **Textos:** Manter original, limpar apenas ruídos (datas/valores misturados)
5. **Booleanos:** Converter para true/false quando houver indicação clara, senão null
6. **NUNCA INVENTE DADOS:** Se não houver valor na coluna origem mapeada, use null
7. **APENAS COLUNAS DESTINO:** Retorne APENAS as colunas que existem na estrutura da tabela destino acima

**EXEMPLO:**
- Mapeamento: {{"Data": "date", "Descrição": "description", "Valor": "value"}}
- Registro origem: {{"Data": "15/01/2024", "Descrição": "Pix enviado", "Valor": "R$ 100,00"}}
- Resultado: {{"date": "2024-01-15", "description": "Pix enviado", "value": 100.0}}

Retorne APENAS JSON (sem markdown, sem texto adicional):
{{
    "normalized_records": [
        {{
            "coluna_destino": "valor_normalizado"
        }}
    ]
}}"""
    
    def _create_validate_data_prompt(
        self,
        import_type: str,
        normalized_records: List[Dict[str, Any]]
    ) -> str:
        """
        Cria prompt para validação de dados usando schema
        """
        schema = self.schema_generator.get_schema_for_data_type(import_type)
        target_columns = self.schema_generator.get_target_columns(import_type)
        column_specs = self.schema_generator.get_column_specifications(import_type)
        
        sample_json = json.dumps(normalized_records[:5], indent=2, default=str, ensure_ascii=False)
        
        return f"""Você é um especialista em validação de dados. Use o tool validate_data para validar registros.

TIPO DE IMPORTAÇÃO: {import_type}
COLUNAS ESPERADAS: {', '.join(target_columns)}

AMOSTRA DE DADOS NORMALIZADOS:
{sample_json}

SCHEMA DA TABELA:
{json.dumps(schema, indent=2, ensure_ascii=False)}

Valide se:
1. Todos os registros têm todas as colunas esperadas
2. Tipos de dados estão corretos (datas como YYYY-MM-DD, valores como números)
3. Campos obrigatórios não estão null
4. Não há inconsistências

Retorne JSON:
{{
    "is_valid": true/false,
    "issues": ["problema1", "problema2"],
    "records_with_issues": [0, 2, 5],
    "missing_columns": ["coluna1"],
    "type_errors": ["coluna1 deve ser date mas recebeu string"]
}}"""
    
    def get_tool_prompt(self, tool_name: str, **kwargs) -> str:
        """
        Obtém prompt para um tool específico
        
        Args:
            tool_name: Nome do tool
            **kwargs: Argumentos específicos do tool
        
        Returns:
            String com prompt formatado
        """
        if tool_name == "detect_data_type":
            return self._create_detect_type_prompt(
                kwargs.get("columns", []),
                kwargs.get("data_sample", "")
            )
        elif tool_name == "map_columns":
            return self._create_map_columns_prompt(
                kwargs.get("import_type", ""),
                kwargs.get("source_columns", []),
                kwargs.get("columns_analysis")
            )
        elif tool_name == "normalize_data":
            return self._create_normalize_data_prompt(
                kwargs.get("import_type", ""),
                kwargs.get("mapping", {}),
                kwargs.get("records", [])
            )
        elif tool_name == "validate_data":
            return self._create_validate_data_prompt(
                kwargs.get("import_type", ""),
                kwargs.get("normalized_records", [])
            )
        else:
            raise ValueError(f"Tool desconhecido: {tool_name}")

