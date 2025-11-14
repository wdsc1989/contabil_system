"""
Serviço para processamento completo de dados com IA
"""
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session

from services.ai_service import AIService
from services.import_service import ImportService
from utils.column_mapper import ColumnMapper


class DataProcessor:
    """
    Processador de dados que orquestra análise, mapeamento, normalização e validação com IA
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o processador com serviços necessários
        """
        self.db = db
        self.ai_service = AIService(db)
    
    def process_file(
        self,
        df: pd.DataFrame,
        import_type: str,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Processa arquivo completo: análise → mapeamento → normalização → validação
        
        Retorna:
        {
            'success': bool,
            'structural_analysis': dict,
            'mapping': dict,
            'normalized_data': list,
            'validated_data': list,
            'summary': dict,
            'errors': list
        }
        """
        result = {
            'success': False,
            'structural_analysis': {},
            'mapping': {},
            'normalized_data': [],
            'validated_data': [],
            'summary': {},
            'errors': []
        }
        
        try:
            # 1. Análise Estrutural
            structural_analysis = {}
            if use_ai and self.ai_service.is_available():
                with pd.option_context('display.max_columns', None):
                    structural_analysis = self.ai_service.analyze_structure(df, import_type)
                result['structural_analysis'] = structural_analysis
            
            # 2. Mapeamento Inteligente
            mapping_result = {}
            if use_ai and self.ai_service.is_available():
                # Tenta mapeamento inteligente mesmo sem análise estrutural
                mapping_result = self.ai_service.intelligent_mapping(
                    df, import_type, structural_analysis if structural_analysis else None
                )
                
                # Extrai mapeamento simples do resultado
                if 'mapping' in mapping_result and mapping_result['mapping']:
                    simple_mapping = {}
                    for col, mapping_info in mapping_result['mapping'].items():
                        if isinstance(mapping_info, dict):
                            simple_mapping[col] = mapping_info.get('target_field', 'ignore')
                        else:
                            simple_mapping[col] = mapping_info
                    result['mapping'] = simple_mapping
                    result['mapping_details'] = mapping_result
                else:
                    # Fallback para mapeamento tradicional
                    target_columns = ImportService.get_target_columns(import_type)
                    result['mapping'] = ColumnMapper.suggest_mapping(
                        list(df.columns),
                        target_columns,
                        df=df,
                        db=self.db,
                        import_type=import_type
                    )
            else:
                # Fallback para mapeamento tradicional
                target_columns = ImportService.get_target_columns(import_type)
                result['mapping'] = ColumnMapper.suggest_mapping(
                    list(df.columns),
                    target_columns,
                    df=df,
                    db=self.db,
                    import_type=import_type
                )
            
            # 3. Aplica mapeamento básico primeiro
            mapped_df = ImportService.apply_mapping(df, result['mapping'])
            
            # 4. Normalização com IA (se disponível)
            # Nota: A normalização com IA processa apenas uma amostra (20 linhas) para economizar tokens
            # Os padrões identificados podem ser aplicados ao resto dos dados
            if use_ai and self.ai_service.is_available() and result['mapping']:
                normalization_result = self.ai_service.normalize_data(
                    df,
                    import_type,
                    result['mapping'],
                    structural_analysis
                )
                
                if normalization_result and 'normalized_data' in normalization_result:
                    # Usa dados normalizados da IA (amostra)
                    normalized_sample = normalization_result['normalized_data']
                    result['normalized_data'] = normalized_sample
                    result['normalization_summary'] = normalization_result.get('summary', {})
                    result['normalization_patterns'] = normalization_result.get('summary', {}).get('common_issues', [])
                    
                    # Para o resto dos dados, aplica mapeamento básico
                    # Em produção, poderia aplicar os padrões identificados
                    if len(normalized_sample) < len(df):
                        remaining_data = mapped_df.iloc[len(normalized_sample):].to_dict('records')
                        result['normalized_data'].extend(remaining_data)
                else:
                    # Fallback: usa dados mapeados sem normalização IA
                    result['normalized_data'] = mapped_df.to_dict('records')
            else:
                # Fallback: converte DataFrame mapeado para lista de dicts
                result['normalized_data'] = mapped_df.to_dict('records')
            
            # 5. Validação (se dados normalizados disponíveis)
            if result['normalized_data'] and use_ai and self.ai_service.is_available():
                validation_result = self.ai_service.validate_data(
                    result['normalized_data'],
                    import_type
                )
                
                if validation_result and 'validated_data' in validation_result:
                    result['validated_data'] = validation_result['validated_data']
                    result['validation_summary'] = validation_result.get('validation_summary', {})
                    result['recommendations'] = validation_result.get('recommendations', [])
                else:
                    # Fallback: marca todos como válidos
                    result['validated_data'] = [
                        {'row': i+1, 'data': row, 'status': 'valid', 'confidence': 1.0}
                        for i, row in enumerate(result['normalized_data'])
                    ]
            else:
                # Fallback: marca todos como válidos
                result['validated_data'] = [
                    {'row': i+1, 'data': row, 'status': 'valid', 'confidence': 1.0}
                    for i, row in enumerate(result['normalized_data'])
                ]
            
            # 6. Prepara resumo
            result['summary'] = {
                'total_rows': len(df),
                'mapped_columns': len([k for k, v in result['mapping'].items() if v != 'ignore']),
                'normalized_rows': len(result['normalized_data']),
                'validated_rows': len(result['validated_data']),
                'valid_rows': len([v for v in result['validated_data'] if v.get('status') == 'valid']),
                'ai_used': use_ai and self.ai_service.is_available()
            }
            
            result['success'] = True
            
        except Exception as e:
            result['errors'].append(f"Erro no processamento: {str(e)}")
            result['success'] = False
        
        return result
    
    def get_processed_dataframe(
        self,
        processed_result: Dict[str, Any]
    ) -> Optional[pd.DataFrame]:
        """
        Converte dados processados de volta para DataFrame
        """
        if not processed_result.get('validated_data'):
            return None
        
        try:
            # Extrai apenas os dados validados
            data_list = []
            for item in processed_result['validated_data']:
                if isinstance(item, dict) and 'data' in item:
                    data_list.append(item['data'])
                else:
                    data_list.append(item)
            
            if data_list:
                return pd.DataFrame(data_list)
        except Exception as e:
            print(f"Erro ao converter para DataFrame: {e}")
        
        return None
    
    def get_mapping_for_ui(
        self,
        processed_result: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Retorna mapeamento no formato esperado pela UI
        """
        return processed_result.get('mapping', {})
    
    def get_processing_summary(
        self,
        processed_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Retorna resumo do processamento para exibição
        """
        summary = processed_result.get('summary', {})
        validation_summary = processed_result.get('validation_summary', {})
        normalization_summary = processed_result.get('normalization_summary', {})
        
        return {
            'total_rows': summary.get('total_rows', 0),
            'mapped_columns': summary.get('mapped_columns', 0),
            'normalized_rows': summary.get('normalized_rows', 0),
            'valid_rows': summary.get('valid_rows', 0),
            'with_warnings': validation_summary.get('with_warnings', 0),
            'with_errors': validation_summary.get('with_errors', 0),
            'ai_used': summary.get('ai_used', False),
            'recommendations': processed_result.get('recommendations', [])
        }

