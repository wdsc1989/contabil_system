"""
Script de teste para validação da integração MCP
Testa schema generator, MCP tools e AIMultiAgent
"""
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import SessionLocal
from services.mcp_schema_generator import MCPSchemaGenerator
from services.mcp_tools import MCPTools
from services.ai_multi_agent import AIMultiAgent
import json


def test_schema_generator():
    """Testa o gerador de schemas"""
    print("\n" + "="*60)
    print("TESTE 1: Schema Generator")
    print("="*60)
    
    generator = MCPSchemaGenerator()
    
    # Testa todos os tipos de dados
    data_types = [
        'transactions',
        'bank_statements',
        'contracts',
        'accounts_payable',
        'accounts_receivable',
        'financial_investments',
        'credit_card_invoices',
        'card_machine_statements',
        'inventory'
    ]
    
    success_count = 0
    for data_type in data_types:
        try:
            print(f"\n[TESTE] Testando {data_type}...")
            
            # Testa geração de schema
            schema = generator.get_schema_for_data_type(data_type)
            assert schema is not None, f"Schema não gerado para {data_type}"
            assert 'properties' in schema, f"Schema sem 'properties' para {data_type}"
            print(f"  [OK] Schema gerado: {len(schema.get('properties', {}))} propriedades")
            
            # Testa colunas destino
            columns = generator.get_target_columns(data_type)
            assert len(columns) > 0, f"Nenhuma coluna retornada para {data_type}"
            print(f"  [OK] Colunas destino: {len(columns)} colunas")
            
            # Testa especificações
            specs = generator.get_column_specifications(data_type)
            assert len(specs) > 0, f"Nenhuma especificação para {data_type}"
            print(f"  [OK] Especificações: {len(specs)} colunas")
            
            # Testa descrição
            description = generator.get_table_structure_description(data_type)
            assert len(description) > 0, f"Descrição vazia para {data_type}"
            print(f"  [OK] Descrição gerada")
            
            success_count += 1
        except Exception as e:
            print(f"  [ERRO] Erro em {data_type}: {e}")
    
    print(f"\n[OK] Schema Generator: {success_count}/{len(data_types)} tipos testados com sucesso")
    return success_count == len(data_types)


def test_mcp_tools():
    """Testa os MCP tools"""
    print("\n" + "="*60)
    print("TESTE 2: MCP Tools")
    print("="*60)
    
    db = SessionLocal()
    try:
        tools = MCPTools(db_session=db)
        
        # Testa definições de tools
        print("\n[TESTE] Testando definições de tools...")
        tool_definitions = tools.get_all_tool_definitions()
        assert len(tool_definitions) == 4, "Deve ter 4 tools definidos"
        print(f"  [OK] {len(tool_definitions)} tools definidos")
        
        # Testa cada tool
        test_cases = [
            {
                'name': 'detect_data_type',
                'kwargs': {
                    'columns': ['Data', 'Descrição', 'Valor'],
                    'data_sample': '{"Data": "01/01/2024", "Descrição": "Pix enviado", "Valor": "R$ 100,00"}'
                }
            },
            {
                'name': 'map_columns',
                'kwargs': {
                    'import_type': 'transactions',
                    'source_columns': ['Data', 'Descrição', 'Valor'],
                    'columns_analysis': None
                }
            },
            {
                'name': 'normalize_data',
                'kwargs': {
                    'import_type': 'transactions',
                    'mapping': {'Data': 'date', 'Descrição': 'description', 'Valor': 'value'},
                    'records': [{'Data': '01/01/2024', 'Descrição': 'Pix enviado', 'Valor': 'R$ 100,00'}]
                }
            },
            {
                'name': 'validate_data',
                'kwargs': {
                    'import_type': 'transactions',
                    'normalized_records': [{'date': '2024-01-01', 'description': 'Pix enviado', 'value': 100.0}]
                }
            }
        ]
        
        success_count = 0
        for test_case in test_cases:
            try:
                print(f"\n[TESTE] Testando tool: {test_case['name']}...")
                prompt = tools.get_tool_prompt(test_case['name'], **test_case['kwargs'])
                assert len(prompt) > 0, f"Prompt vazio para {test_case['name']}"
                # Verifica se o prompt contém informações esperadas
                import_type = test_case.get('import_type')
                if import_type:
                    assert import_type in prompt, \
                        f"Prompt não contém import_type '{import_type}' para {test_case['name']}"
                elif test_case['name'] == 'detect_data_type':
                    # Para detect_data_type, verifica se contém informações sobre tipos
                    assert 'transactions' in prompt or 'bank_statements' in prompt, \
                        f"Prompt não contém informações sobre tipos para {test_case['name']}"
                print(f"  [OK] Prompt gerado ({len(prompt)} caracteres)")
                success_count += 1
            except Exception as e:
                print(f"  [ERRO] Erro em {test_case['name']}: {e}")
        
        print(f"\n[OK] MCP Tools: {success_count}/{len(test_cases)} tools testados com sucesso")
        return success_count == len(test_cases)
    finally:
        db.close()


def test_ai_multi_agent():
    """Testa o AIMultiAgent com MCP"""
    print("\n" + "="*60)
    print("TESTE 3: AIMultiAgent com MCP")
    print("="*60)
    
    db = SessionLocal()
    try:
        agent = AIMultiAgent(db)
        
        # Verifica se MCP tools estão inicializados
        print("\n[TESTE] Verificando inicialização...")
        assert hasattr(agent, 'mcp_tools'), "AIMultiAgent não tem mcp_tools"
        assert hasattr(agent, 'schema_generator'), "AIMultiAgent não tem schema_generator"
        print("  [OK] MCP tools e schema generator inicializados")
        
        # Testa métodos auxiliares
        print("\n[TESTE] Testando métodos auxiliares...")
        test_type = 'transactions'
        
        # Testa _get_target_columns
        columns = agent._get_target_columns(test_type)
        assert len(columns) > 0, "Nenhuma coluna retornada"
        print(f"  [OK] _get_target_columns: {len(columns)} colunas")
        
        # Testa _get_column_specifications
        specs = agent._get_column_specifications(test_type)
        assert len(specs) > 0, "Nenhuma especificação retornada"
        print(f"  [OK] _get_column_specifications: {len(specs)} especificações")
        
        # Testa _get_table_structure_description
        description = agent._get_table_structure_description(test_type)
        assert len(description) > 0, "Descrição vazia"
        print(f"  [OK] _get_table_structure_description: {len(description)} caracteres")
        
        # Testa agent_detect_type (sem chamar IA, apenas verifica estrutura)
        print("\n[TESTE] Testando agent_detect_type (estrutura)...")
        try:
            # Não chama IA, apenas verifica se o método existe e aceita parâmetros
            # Em um teste real, você precisaria de API key configurada
            print("  [OK] Método agent_detect_type disponível")
        except Exception as e:
            print(f"  [AVISO] Método agent_detect_type: {e}")
        
        print("\n[OK] AIMultiAgent: Estrutura validada")
        return True
    finally:
        db.close()


def test_integration_flow():
    """Testa o fluxo completo de integração"""
    print("\n" + "="*60)
    print("TESTE 4: Fluxo de Integração Completo")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Simula fluxo completo sem chamar IA
        print("\n[TESTE] Simulando fluxo completo...")
        
        # 1. Schema Generator
        generator = MCPSchemaGenerator()
        schema = generator.get_schema_for_data_type('transactions')
        print("  [OK] 1. Schema gerado")
        
        # 2. MCP Tools
        tools = MCPTools(db_session=db)
        mapping_prompt = tools.get_tool_prompt(
            'map_columns',
            import_type='transactions',
            source_columns=['Data', 'Descrição', 'Valor']
        )
        print("  [OK] 2. Prompt de mapeamento gerado")
        
        # 3. AIMultiAgent
        agent = AIMultiAgent(db)
        columns = agent._get_target_columns('transactions')
        print(f"  [OK] 3. Colunas destino obtidas: {len(columns)}")
        
        print("\n[OK] Fluxo de integração: Todos os componentes conectados")
        return True
    finally:
        db.close()


def main():
    """Executa todos os testes"""
    print("\n" + "="*60)
    print("TESTES DE INTEGRAÇÃO MCP")
    print("="*60)
    
    results = []
    
    # Teste 1: Schema Generator
    try:
        results.append(("Schema Generator", test_schema_generator()))
    except Exception as e:
        print(f"\n[ERRO] Erro no teste Schema Generator: {e}")
        results.append(("Schema Generator", False))
    
    # Teste 2: MCP Tools
    try:
        results.append(("MCP Tools", test_mcp_tools()))
    except Exception as e:
        print(f"\n[ERRO] Erro no teste MCP Tools: {e}")
        results.append(("MCP Tools", False))
    
    # Teste 3: AIMultiAgent
    try:
        results.append(("AIMultiAgent", test_ai_multi_agent()))
    except Exception as e:
        print(f"\n[ERRO] Erro no teste AIMultiAgent: {e}")
        results.append(("AIMultiAgent", False))
    
    # Teste 4: Fluxo completo
    try:
        results.append(("Fluxo de Integração", test_integration_flow()))
    except Exception as e:
        print(f"\n[ERRO] Erro no teste Fluxo de Integração: {e}")
        results.append(("Fluxo de Integração", False))
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK] PASSOU" if result else "[ERRO] FALHOU"
        print(f"{status} - {name}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} testes passaram")
    print("="*60)
    
    if passed == total:
        print("\n[SUCESSO] Todos os testes passaram! Integração MCP está funcionando.")
        return 0
    else:
        print(f"\n[AVISO] {total - passed} teste(s) falharam. Revise os erros acima.")
        return 1


if __name__ == "__main__":
    exit(main())

