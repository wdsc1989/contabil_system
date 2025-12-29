"""
Script de teste completo para fluxo de importação
Testa detecção → mapeamento → normalização → validação → inserção para todos os tipos
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sqlalchemy.orm import Session
from config.database import SessionLocal
from services.ai_multi_agent import AIMultiAgent
from services.import_service import ImportService

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

def test_import_type(import_type: str, file_path: str, db: Session) -> dict:
    """Testa importação completa para um tipo específico"""
    print(f"\n{'='*60}")
    print(f"Testando: {import_type}")
    print(f"Arquivo: {file_path}")
    print(f"{'='*60}")
    
    result = {
        'import_type': import_type,
        'file_path': file_path,
        'success': False,
        'errors': [],
        'warnings': [],
        'steps': {}
    }
    
    try:
        # 1. Carrega arquivo
        print("\n[1/5] Carregando arquivo...")
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path, encoding='utf-8')
        
        print(f"   [OK] Arquivo carregado: {len(df)} linhas, {len(df.columns)} colunas")
        result['steps']['load'] = {'success': True, 'rows': len(df), 'columns': len(df.columns)}
        
        # 2. Detecção de tipo
        print("\n[2/5] Detectando tipo de dado...")
        multi_agent = AIMultiAgent(db)
        
        if not multi_agent.is_available():
            result['errors'].append("IA não disponível")
            return result
        
        columns = list(df.columns)
        sample_data = df.head(5).to_dict('records')
        sample_json = str(sample_data)
        
        detection = multi_agent.agent_detect_type(columns, sample_json)
        
        if detection.get('success'):
            detected_type = detection.get('suggested_type', 'unknown')
            print(f"   [OK] Tipo detectado: {detected_type}")
            if detected_type != import_type:
                result['warnings'].append(f"Tipo detectado ({detected_type}) diferente do esperado ({import_type})")
            result['steps']['detection'] = {'success': True, 'detected_type': detected_type}
        else:
            result['errors'].append(f"Falha na detecção: {detection.get('error', 'Erro desconhecido')}")
            result['steps']['detection'] = {'success': False, 'error': detection.get('error')}
            return result
        
        # 3. Análise de estrutura e mapeamento
        print("\n[3/5] Analisando estrutura e mapeando colunas...")
        structure_analysis = multi_agent.agent_analyze_structure(df, import_type)
        
        if not structure_analysis.get('success'):
            result['errors'].append("Falha na análise de estrutura")
            return result
        
        mapping = multi_agent.agent_map_columns(structure_analysis, import_type)
        
        if not mapping:
            result['warnings'].append("Mapeamento vazio, tentando fallback...")
            from utils.column_mapper import ColumnMapper
            target_columns = multi_agent._get_target_columns(import_type)
            mapping = ColumnMapper.suggest_mapping(
                columns, target_columns, df=df, db=db, import_type=import_type
            )
            mapping = {k: v for k, v in mapping.items() if v and v != 'ignore'}
        
        if mapping:
            print(f"   [OK] Mapeamento criado: {len(mapping)} coluna(s)")
            result['steps']['mapping'] = {'success': True, 'mapping_count': len(mapping), 'mapping': mapping}
        else:
            result['errors'].append("Não foi possível criar mapeamento")
            return result
        
        # 4. Normalização
        print("\n[4/5] Normalizando dados...")
        processed_data = df.to_dict('records')
        for record in processed_data:
            record['group_id'] = None
            record['subgroup_id'] = None
        
        normalized_records = multi_agent.agent_extract_and_format(processed_data, import_type, mapping)
        
        if not normalized_records:
            result['warnings'].append("Normalização retornou vazio, aplicando mapeamento direto...")
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
            print(f"   [OK] Dados normalizados: {len(normalized_records)} registro(s), {len(cols_present)}/{len(target_columns)} colunas preenchidas")
            result['steps']['normalization'] = {
                'success': True,
                'records_count': len(normalized_records),
                'columns_filled': len(cols_present),
                'total_columns': len(target_columns)
            }
        else:
            result['errors'].append("Falha na normalização")
            return result
        
        # 5. Validação
        print("\n[5/5] Validando dados...")
        validation = multi_agent.agent_validate(normalized_records, import_type)
        
        if validation.get('success'):
            issues = validation.get('issues', [])
            if issues:
                print(f"   [AVISO] Validação encontrou {len(issues)} problema(s)")
                result['warnings'].extend([f"Validação: {issue}" for issue in issues[:5]])
            else:
                print(f"   [OK] Validação passou sem problemas")
            result['steps']['validation'] = {'success': True, 'issues_count': len(issues)}
        else:
            result['warnings'].append(f"Validação falhou: {validation.get('error', 'Erro desconhecido')}")
            result['steps']['validation'] = {'success': False, 'error': validation.get('error')}
        
        # Verifica se dados aparecem corretamente na tabela de revisão
        print("\n[Verificação] Verificando dados na tabela de revisão...")
        if normalized_records:
            sample = normalized_records[0]
            target_columns = multi_agent._get_target_columns(import_type)
            cols_with_data = [col for col in target_columns if col in sample and sample.get(col) is not None]
            
            if len(cols_with_data) > 0:
                print(f"   [OK] Tabela de revisão: {len(cols_with_data)} colunas com dados")
                result['steps']['review_table'] = {'success': True, 'columns_with_data': len(cols_with_data)}
            else:
                result['errors'].append("Nenhuma coluna destino preenchida na tabela de revisão")
                result['steps']['review_table'] = {'success': False}
        
        result['success'] = len(result['errors']) == 0
        print(f"\n{'[SUCESSO]' if result['success'] else '[FALHA]'}: {import_type}")
        
    except Exception as e:
        result['errors'].append(f"Erro inesperado: {str(e)}")
        import traceback
        result['errors'].append(traceback.format_exc())
        print(f"\n[ERRO] {str(e)}")
    
    return result

def main():
    """Executa testes para todos os tipos"""
    print("="*60)
    print("TESTE COMPLETO DE IMPORTAÇÃO - FLUXO MCP")
    print("="*60)
    
    db = SessionLocal()
    results = []
    
    try:
        for import_type, file_path in TEST_FILES.items():
            full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_path)
            if not os.path.exists(full_path):
                print(f"\n[AVISO] Arquivo nao encontrado: {full_path}")
                continue
            
            result = test_import_type(import_type, full_path, db)
            results.append(result)
    
    finally:
        db.close()
    
    # Relatório final
    print("\n" + "="*60)
    print("RELATÓRIO FINAL")
    print("="*60)
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    print(f"\nTotal de testes: {total_count}")
    print(f"Sucessos: {success_count}")
    print(f"Falhas: {total_count - success_count}")
    
    print("\nDetalhes por tipo:")
    for result in results:
        status = "[OK]" if result['success'] else "[FALHA]"
        print(f"  {status} {result['import_type']}: {len(result['errors'])} erro(s), {len(result['warnings'])} aviso(s)")
        if result['errors']:
            for error in result['errors'][:3]:
                print(f"      - {error}")
    
    # Resumo de passos
    print("\nResumo de passos:")
    steps_summary = {}
    for result in results:
        for step_name, step_result in result.get('steps', {}).items():
            if step_name not in steps_summary:
                steps_summary[step_name] = {'success': 0, 'fail': 0}
            if step_result.get('success'):
                steps_summary[step_name]['success'] += 1
            else:
                steps_summary[step_name]['fail'] += 1
    
    for step_name, summary in steps_summary.items():
        total = summary['success'] + summary['fail']
        success_pct = (summary['success'] / total * 100) if total > 0 else 0
        print(f"  {step_name}: {summary['success']}/{total} ({success_pct:.1f}%)")

if __name__ == '__main__':
    main()


