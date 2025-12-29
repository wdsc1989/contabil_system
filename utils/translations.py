"""
Sistema de tradução de colunas e campos do banco de dados para português
"""
from typing import Dict, Optional
import pandas as pd

# Mapeamento de colunas em inglês para português
COLUMN_TRANSLATIONS: Dict[str, str] = {
    # Transações
    'id': 'ID',
    'date': 'Data',
    'description': 'Descrição',
    'value': 'Valor',
    'type': 'Tipo',
    'category': 'Categoria',
    'account': 'Conta',
    'bank_name': 'Banco',
    'document_type': 'Tipo de Documento',
    'imported_from': 'Importado de',
    'created_at': 'Data de Criação',
    'group_id': 'ID do Grupo',
    'subgroup_id': 'ID do Subgrupo',
    
    # Extratos Bancários
    'transaction_date': 'Data',
    'balance': 'Saldo',
    'imported_at': 'Data de Importação',
    
    # Contratos
    'contract_start': 'Data de Início',
    'event_date': 'Data do Evento',
    'service_value': 'Valor do Serviço',
    'displacement_value': 'Valor de Deslocamento',
    'event_type': 'Tipo de Evento',
    'service_sold': 'Serviço Vendido',
    'guests_count': 'Número de Convidados',
    'contractor_name': 'Nome do Contratante',
    'payment_terms': 'Condições de Pagamento',
    'status': 'Status',
    'contract_number': 'Número do Contrato',
    
    # Contas a Pagar
    'account_name': 'Nome da Conta',
    'due_date': 'Data de Vencimento',
    'cpf_cnpj': 'CPF/CNPJ',
    'month_ref': 'Mês de Referência',
    'paid': 'Pago',
    'payment_date': 'Data de Pagamento',
    'monthly_installments': 'Parcelas Mensais',
    'total_monthly_outflow': 'Total de Saída Mensal',
    'installment_number': 'Número da Parcela',
    
    # Contas a Receber
    'receipt_date': 'Data de Recebimento',
    'received': 'Recebido',
    'event_date': 'Data do Evento',
    'contract_value': 'Valor do Contrato',
    'payment_method': 'Forma de Pagamento',
    'total_expected_inflow': 'Total de Entrada Esperada',
    
    # Aplicações Financeiras
    'investment_type': 'Tipo de Investimento',
    'institution': 'Instituição',
    'operation_type': 'Tipo de Operação',
    'applied_value': 'Valor Aplicado',
    'redeemed_value': 'Valor Resgatado',
    'yield_value': 'Rendimento',
    
    # Faturas de Cartão
    'establishment': 'Estabelecimento',
    'installment_number': 'Número da Parcela',
    'total_installments': 'Total de Parcelas',
    'card_brand': 'Bandeira do Cartão',
    
    # Máquina de Cartão
    'gross_value': 'Valor Bruto',
    'fee': 'Taxa',
    'net_value': 'Valor Líquido',
    'transaction_type': 'Tipo de Transação',
    
    # Estoque
    'product_name': 'Nome do Produto',
    'quantity': 'Quantidade',
    'unit_value': 'Valor Unitário',
    'total_value': 'Valor Total',
    'movement_date': 'Data do Movimento',
    'movement_type': 'Tipo de Movimento',
    
    # Clientes
    'name': 'Nome',
    'tipo_empresa': 'Tipo de Empresa',
    'active': 'Ativo',
    
    # Grupos e Subgrupos
    'group': 'Grupo',
    'subgroup': 'Subgrupo',
    'group_name': 'Nome do Grupo',
    'subgroup_name': 'Nome do Subgrupo',
    
    # Relatórios
    'month': 'Mês',
    'year': 'Ano',
    'entradas': 'Entradas',
    'saidas': 'Saídas',
    'saldo': 'Saldo',
    'receitas': 'Receitas',
    'despesas': 'Despesas',
    'resultado': 'Resultado',
    'margem': 'Margem',
}

# Mapeamento de valores específicos para português
VALUE_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'type': {
        'entrada': 'Entrada',
        'saida': 'Saída',
        'income': 'Entrada',
        'expense': 'Saída',
    },
    'status': {
        'pendente': 'Pendente',
        'em_andamento': 'Em Andamento',
        'concluido': 'Concluído',
        'cancelado': 'Cancelado',
        'pending': 'Pendente',
        'in_progress': 'Em Andamento',
        'completed': 'Concluído',
        'cancelled': 'Cancelado',
    },
    'paid': {
        True: 'Sim',
        False: 'Não',
        'true': 'Sim',
        'false': 'Não',
    },
    'received': {
        True: 'Sim',
        False: 'Não',
        'true': 'Sim',
        'false': 'Não',
    },
    'active': {
        True: 'Ativo',
        False: 'Inativo',
        'true': 'Ativo',
        'false': 'Inativo',
    },
    'movement_type': {
        'entrada': 'Entrada',
        'saida': 'Saída',
        'input': 'Entrada',
        'output': 'Saída',
    },
    'transaction_type': {
        'credito': 'Crédito',
        'debito': 'Débito',
        'credit': 'Crédito',
        'debit': 'Débito',
    },
    'document_type': {
        'extrato_bancario': 'Extrato Bancário',
        'fatura_cartao': 'Fatura de Cartão',
        'bank_statement': 'Extrato Bancário',
        'credit_card_invoice': 'Fatura de Cartão',
    },
}


def translate_column_name(column_name: str) -> str:
    """
    Traduz o nome de uma coluna do inglês para português
    
    Args:
        column_name: Nome da coluna em inglês
        
    Returns:
        Nome da coluna em português
    """
    # Remove espaços e converte para minúsculas para comparação
    column_lower = column_name.lower().strip()
    
    # Verifica se existe tradução direta
    if column_lower in COLUMN_TRANSLATIONS:
        return COLUMN_TRANSLATIONS[column_lower]
    
    # Tenta encontrar tradução parcial (para casos como "group.name")
    for key, translation in COLUMN_TRANSLATIONS.items():
        if key in column_lower or column_lower in key:
            return translation
    
    # Se não encontrar, retorna o nome original capitalizado
    return column_name.replace('_', ' ').title()


def translate_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Traduz os nomes das colunas de um DataFrame para português
    
    Args:
        df: DataFrame com colunas em inglês
        
    Returns:
        DataFrame com colunas traduzidas para português
    """
    if df is None or df.empty:
        return df
    
    # Cria dicionário de tradução
    translation_dict = {}
    for col in df.columns:
        translated = translate_column_name(str(col))
        if translated != col:
            translation_dict[col] = translated
    
    # Renomeia colunas
    if translation_dict:
        df = df.rename(columns=translation_dict)
    
    return df


def translate_value(column_name: str, value: any) -> any:
    """
    Traduz um valor específico de uma coluna para português
    
    Args:
        column_name: Nome da coluna
        value: Valor a ser traduzido
        
    Returns:
        Valor traduzido ou original se não houver tradução
    """
    if value is None:
        return value
    
    column_lower = column_name.lower().strip()
    
    # Verifica se existe tradução para esta coluna
    if column_lower in VALUE_TRANSLATIONS:
        value_str = str(value).lower()
        if value_str in VALUE_TRANSLATIONS[column_lower]:
            return VALUE_TRANSLATIONS[column_lower][value_str]
        # Tenta com o valor original (para booleanos)
        if value in VALUE_TRANSLATIONS[column_lower]:
            return VALUE_TRANSLATIONS[column_lower][value]
    
    return value


def translate_dataframe_values(df: pd.DataFrame, columns_to_translate: Optional[list] = None) -> pd.DataFrame:
    """
    Traduz valores específicos de um DataFrame para português
    
    Args:
        df: DataFrame
        columns_to_translate: Lista de colunas para traduzir valores. Se None, traduz todas as colunas conhecidas
        
    Returns:
        DataFrame com valores traduzidos
    """
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    # Se não especificou colunas, traduz todas as colunas conhecidas
    if columns_to_translate is None:
        columns_to_translate = list(VALUE_TRANSLATIONS.keys())
    
    # Traduz valores de cada coluna
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if col_lower in columns_to_translate or any(key in col_lower for key in columns_to_translate):
            df[col] = df[col].apply(lambda x: translate_value(col_lower, x))
    
    return df


def translate_dataframe(df: pd.DataFrame, translate_columns: bool = True, translate_values: bool = True) -> pd.DataFrame:
    """
    Traduz completamente um DataFrame (colunas e valores) para português
    
    Args:
        df: DataFrame
        translate_columns: Se True, traduz nomes das colunas
        translate_values: Se True, traduz valores específicos
        
    Returns:
        DataFrame traduzido
    """
    if df is None or df.empty:
        return df
    
    df = df.copy()
    
    if translate_columns:
        df = translate_dataframe_columns(df)
    
    if translate_values:
        df = translate_dataframe_values(df)
    
    return df

























