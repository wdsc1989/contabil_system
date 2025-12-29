"""
Script de teste interativo para importação
Permite testar importação de arquivo específico e ver cada etapa
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sqlalchemy.orm import Session
from config.database import SessionLocal
from services.ai_multi_agent import AIMultiAgent
from utils.column_mapper import ColumnMapper

# Mapeamento de tipos para arquivos de teste
TEST_FILES = {
    'transactions': 'tests/sample_files/transactions.csv',
    'bank_statements': 'tests/sample_files/bank_statements.csv',
    'credit_card_invoices': 'tests/sample_files/credit_card_invoices.csv',
    'contracts': 'tests/sample_files/contracts.xlsx',
    'accounts_payable': 'tests/sample_files/accounts_payable.csv',
    'accounts_receivable': 'tests/sample_files/accounts_receivable.csv',
    'financial_investments': 'tests/sample_files/financial_investments.csv',
    'card_machine_statements': 'tests/sample_files/card_machine_statements.csv',
    'inventory': 'tests/sample_files/inventory.csv'
}

def show_step(step_num: int, total: int, name: str):
    """Mostra cabeçalho de etapa"""
    print(f"\n{'='*60}")
    print(f"[{step_num}/{total}] {name}")
    print(f"{'='*60}")

def show_dataframe(df: pd.DataFrame, max_rows: int = 5):
    """Mostra DataFrame formatado"""
    print(f"\nShape: {df.shape[0]} linhas x {df.shape[1]} colunas")
    print(f"\nColunas: {', '.join(df.columns)}")
    print(f"\nPrimeiras {min(max_rows, len(df))} linhas:")
    print(df.head(max_rows).to_string())

def show_mapping(mapping: dict):
    """Mostra mapeamento de colunas"""
    print(f"\nMapeamento ({len(mapping)} colunas):")
    for src, tgt in mapping.items():
        print(f"  {src} → {tgt}")

def show_records(records: list, max_records: int = 3):
    """Mostra registros normalizados"""
    print(f"\nTotal de registros: {len(records)}")
    if records:
        print(f"\nPrimeiros {min(max_records, len(records))} registros:")
        for i, record in enumerate(records[:max_records], 1):
            print(f"\n  Registro {i}:")
            for key, value in list(record.items())[:10]:  # Primeiras 10 colunas
                print(f"    {key}: {value}")

def test_file_interactive(file_path: str, import_type: str = None):
    """Testa importação de arquivo específico de forma interativa"""
    print("\n" + "="*60)
    print("TESTE INTERATIVO DE IMPORTAÇÃO")
    print("="*60)
    
    # 1. Carregar arquivo
    show_step(1, 6, "Carregando Arquivo")
    try:
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path, encoding='utf-8')
        show_dataframe(df)
    except Exception as e:
        print(f"Erro ao carregar arquivo: {e}")
        return
    
    # 2. Detecção de tipo
    show_step(2, 6, "Detecção de Tipo")
    db = SessionLocal()
    try:
        multi_agent = AIMultiAgent(db)
        
        if not multi_agent.is_available():
            print("IA não disponível")
            return
        
        columns = list(df.columns)
        sample_data = df.head(5).to_dict('records')
        sample_json = str(sample_data)
        
        print("Enviando para IA...")
        detection = multi_agent.agent_detect_type(columns, sample_json)
        
        if detection.get('success'):
            detected_type = detection.get('suggested_type', 'unknown')
            confidence = detection.get('confidence', 0)
            print(f"Tipo detectado: {detected_type} (confiança: {confidence})")
            
            if import_type and detected_type != import_type:
                print(f"[AVISO] Tipo esperado era {import_type}")
            
            if not import_type:
                import_type = detected_type
        else:
            print(f"Erro na detecção: {detection.get('error')}")
            if not import_type:
                print("Por favor, informe o tipo manualmente")
                return
    finally:
        pass  # Mantém db aberto para próximos passos
    
    # 3. Análise de estrutura
    show_step(3, 6, "Análise de Estrutura")
    structure_analysis = multi_agent.agent_analyze_structure(df, import_type)
    
    if structure_analysis.get('success'):
        print("[OK] Estrutura analisada com sucesso")
        if 'target_structure' in structure_analysis:
            target = structure_analysis['target_structure']
            print(f"Colunas destino: {len(target.get('target_columns', []))}")
            print(f"Colunas obrigatórias: {len(target.get('required_columns', []))}")
    else:
        print("[ERRO] Falha na analise de estrutura")
        return
    
    # 4. Mapeamento
    show_step(4, 6, "Mapeamento de Colunas")
    mapping = multi_agent.agent_map_columns(structure_analysis, import_type)
    
    if not mapping:
        print("Mapeamento vazio, tentando fallback...")
        target_columns = multi_agent._get_target_columns(import_type)
        mapping = ColumnMapper.suggest_mapping(
            list(df.columns), target_columns, df=df, db=db, import_type=import_type
        )
        mapping = {k: v for k, v in mapping.items() if v and v != 'ignore'}
    
    if mapping:
        show_mapping(mapping)
    else:
        print("[ERRO] Nao foi possivel criar mapeamento")
        return
    
    # 5. Normalização
    show_step(5, 6, "Normalização de Dados")
    processed_data = df.to_dict('records')
    for record in processed_data:
        record['group_id'] = None
        record['subgroup_id'] = None
    
    normalized_records = multi_agent.agent_extract_and_format(processed_data, import_type, mapping)
    
    if not normalized_records:
        print("Normalização retornou vazio, aplicando mapeamento direto...")
        normalized_records = []
        for record in processed_data:
            new_record = {}
            for src_col, tgt_col in mapping.items():
                if src_col in record:
                    new_record[tgt_col] = record[src_col]
            normalized_records.append(new_record)
    
    if normalized_records:
        target_columns = multi_agent._get_target_columns(import_type)
        sample = normalized_records[0]
        cols_present = [col for col in target_columns if col in sample and sample.get(col) is not None]
        print(f"[OK] {len(normalized_records)} registros normalizados")
        print(f"  Colunas preenchidas: {len(cols_present)}/{len(target_columns)}")
        show_records(normalized_records)
    else:
        print("[ERRO] Falha na normalizacao")
        return
    
    # 6. Validação
    show_step(6, 6, "Validação de Dados")
    validation = multi_agent.agent_validate(normalized_records, import_type)
    
    if validation.get('success'):
        issues = validation.get('issues', [])
        if issues:
            print(f"[AVISO] Encontrados {len(issues)} problema(s):")
            for issue in issues[:5]:
                print(f"  - {issue}")
        else:
            print("[OK] Validacao passou sem problemas")
    else:
        print(f"[ERRO] Validacao falhou: {validation.get('error')}")
    
    # Resumo final
    print("\n" + "="*60)
    print("RESUMO")
    print("="*60)
    print(f"Tipo: {import_type}")
    print(f"Registros processados: {len(normalized_records)}")
    if normalized_records:
        target_columns = multi_agent._get_target_columns(import_type)
        sample = normalized_records[0]
        cols_present = [col for col in target_columns if col in sample and sample.get(col) is not None]
        print(f"Colunas preenchidas: {len(cols_present)}/{len(target_columns)}")
    
    db.close()

def main():
    """Menu interativo"""
    print("\n" + "="*60)
    print("TESTE INTERATIVO DE IMPORTAÇÃO")
    print("="*60)
    print("\nTipos disponíveis:")
    for i, (key, path) in enumerate(TEST_FILES.items(), 1):
        print(f"  {i}. {key}")
    
    print("\nOpções:")
    print("  1. Testar arquivo específico")
    print("  2. Testar todos os arquivos")
    print("  0. Sair")
    
    choice = input("\nEscolha uma opção: ").strip()
    
    if choice == '1':
        print("\nTipos disponíveis:")
        types_list = list(TEST_FILES.keys())
        for i, key in enumerate(types_list, 1):
            print(f"  {i}. {key}")
        
        type_choice = input("\nEscolha o tipo (número): ").strip()
        try:
            idx = int(type_choice) - 1
            if 0 <= idx < len(types_list):
                import_type = types_list[idx]
                file_path = TEST_FILES[import_type]
                full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_path)
                test_file_interactive(full_path, import_type)
            else:
                print("Opção inválida")
        except ValueError:
            print("Opção inválida")
    
    elif choice == '2':
        for import_type, file_path in TEST_FILES.items():
            full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_path)
            if os.path.exists(full_path):
                test_file_interactive(full_path, import_type)
                input("\nPressione Enter para continuar...")
    
    elif choice == '0':
        print("Saindo...")
    else:
        print("Opção inválida")

if __name__ == '__main__':
    main()


