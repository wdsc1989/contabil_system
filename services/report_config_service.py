"""
Serviço de configuração de relatórios por cliente
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from models.client_report_config import ClientReportConfig

# Tipos de dados disponíveis para relatórios
AVAILABLE_DATA_TYPES = [
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

# Tipos de relatórios disponíveis
REPORT_TYPES = ['dre', 'dfc', 'sazonalidade']

# Mapeamento de tipos de dados para labels (usado na interface)
DATA_TYPES = {
    'transactions': 'Transações Financeiras',
    'bank_statements': 'Extratos Bancários',
    'contracts': 'Contratos/Eventos',
    'accounts_payable': 'Contas a Pagar',
    'accounts_receivable': 'Contas a Receber',
    'financial_investments': 'Aplicações Financeiras',
    'credit_card_invoices': 'Faturas de Cartão de Crédito',
    'card_machine_statements': 'Extratos de Máquina de Cartão',
    'inventory': 'Controle de Estoque'
}


class ReportConfigService:
    """
    Serviço para gerenciar configurações de relatórios por cliente
    """

    @staticmethod
    def get_client_report_config(db: Session, client_id: int, report_type: str) -> Dict[str, bool]:
        """
        Retorna configuração de um relatório para um cliente
        Retorna dicionário com data_type -> enabled
        """
        configs = db.query(ClientReportConfig).filter(
            ClientReportConfig.client_id == client_id,
            ClientReportConfig.report_type == report_type
        ).all()
        
        result = {}
        for config in configs:
            result[config.data_type] = config.enabled
        
        return result

    @staticmethod
    def update_client_report_config(
        db: Session, 
        client_id: int, 
        report_type: str, 
        data_types: Dict[str, bool]
    ) -> None:
        """
        Atualiza configuração de um relatório para um cliente
        data_types: dicionário com data_type -> enabled
        """
        # Remove configurações existentes para este report_type
        db.query(ClientReportConfig).filter(
            ClientReportConfig.client_id == client_id,
            ClientReportConfig.report_type == report_type
        ).delete()
        
        # Cria novas configurações
        for data_type, enabled in data_types.items():
            if data_type in AVAILABLE_DATA_TYPES:
                config = ClientReportConfig(
                    client_id=client_id,
                    report_type=report_type,
                    data_type=data_type,
                    enabled=enabled
                )
                db.add(config)
        
        db.commit()

    @staticmethod
    def ensure_default_config(db: Session, client_id: int) -> None:
        """
        Cria configuração padrão para um cliente se não existir
        Por padrão, todos os tipos de dados estão habilitados para todos os relatórios
        """
        # Verifica se já existe configuração
        existing = db.query(ClientReportConfig).filter(
            ClientReportConfig.client_id == client_id
        ).first()
        
        if existing:
            return  # Já existe configuração
        
        # Cria configuração padrão: todos habilitados
        for report_type in REPORT_TYPES:
            for data_type in AVAILABLE_DATA_TYPES:
                config = ClientReportConfig(
                    client_id=client_id,
                    report_type=report_type,
                    data_type=data_type,
                    enabled=True
                )
                db.add(config)
        
        db.commit()

    @staticmethod
    def is_data_type_enabled(
        db: Session, 
        client_id: int, 
        report_type: str, 
        data_type: str
    ) -> bool:
        """
        Verifica se um tipo de dado está habilitado para um relatório
        Se não houver configuração, retorna True (comportamento padrão)
        """
        config = db.query(ClientReportConfig).filter(
            ClientReportConfig.client_id == client_id,
            ClientReportConfig.report_type == report_type,
            ClientReportConfig.data_type == data_type
        ).first()
        
        if config is None:
            # Se não houver configuração, retorna True (comportamento padrão)
            return True
        
        return config.enabled

    @staticmethod
    def get_enabled_data_types(
        db: Session, 
        client_id: int, 
        report_type: str
    ) -> List[str]:
        """
        Retorna lista de tipos de dados habilitados para um relatório
        Se não houver configuração, retorna todos os tipos (comportamento padrão)
        Se houver configuração parcial, retorna apenas os habilitados explicitamente
        """
        # Verifica se existe alguma configuração para este cliente e report_type
        has_any_config = db.query(ClientReportConfig).filter(
            ClientReportConfig.client_id == client_id,
            ClientReportConfig.report_type == report_type
        ).first()
        
        if not has_any_config:
            # Se não houver configuração alguma, retorna todos os tipos (comportamento padrão)
            return AVAILABLE_DATA_TYPES.copy()
        
        # Se houver configuração, retorna apenas os habilitados
        configs = db.query(ClientReportConfig).filter(
            ClientReportConfig.client_id == client_id,
            ClientReportConfig.report_type == report_type,
            ClientReportConfig.enabled == True
        ).all()
        
        return [c.data_type for c in configs]

    @staticmethod
    def get_all_configs(db: Session, client_id: int) -> Dict[str, Dict[str, bool]]:
        """
        Retorna todas as configurações de um cliente
        Retorna dicionário: report_type -> {data_type -> enabled}
        """
        configs = db.query(ClientReportConfig).filter(
            ClientReportConfig.client_id == client_id
        ).all()
        
        result = {}
        for report_type in REPORT_TYPES:
            result[report_type] = {}
            for data_type in AVAILABLE_DATA_TYPES:
                result[report_type][data_type] = True  # Default
        
        for config in configs:
            if config.report_type not in result:
                result[config.report_type] = {}
            result[config.report_type][config.data_type] = config.enabled
        
        return result

