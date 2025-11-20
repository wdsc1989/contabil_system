"""
Modelo de clientes
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class Client(Base):
    """
    Modelo de cliente
    """
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    cpf_cnpj = Column(String(18), unique=True, nullable=False, index=True)
    tipo_empresa = Column(String(100))  # Tipo/Grupo de empresa
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos - usando lazy='dynamic' para evitar problemas de importação circular
    permissions = relationship('UserClientPermission', back_populates='client', cascade='all, delete-orphan', lazy='dynamic')
    groups = relationship('Group', back_populates='client', cascade='all, delete-orphan', lazy='dynamic')
    transactions = relationship('Transaction', back_populates='client', cascade='all, delete-orphan', lazy='dynamic')
    contracts = relationship('Contract', back_populates='client', cascade='all, delete-orphan', lazy='dynamic')
    accounts_payable = relationship('AccountPayable', back_populates='client', cascade='all, delete-orphan', lazy='dynamic')
    accounts_receivable = relationship('AccountReceivable', back_populates='client', cascade='all, delete-orphan', lazy='dynamic')
    bank_statements = relationship('BankStatement', back_populates='client', cascade='all, delete-orphan', lazy='dynamic')
    financial_investments = relationship('FinancialInvestment', back_populates='client', cascade='all, delete-orphan', lazy='dynamic')
    credit_card_invoices = relationship('CreditCardInvoice', back_populates='client', cascade='all, delete-orphan', lazy='dynamic')
    card_machine_statements = relationship('CardMachineStatement', back_populates='client', cascade='all, delete-orphan', lazy='dynamic')
    inventory = relationship('Inventory', back_populates='client', cascade='all, delete-orphan', lazy='dynamic')
    import_mappings = relationship('ImportMapping', back_populates='client', cascade='all, delete-orphan', lazy='dynamic')
    report_configs = relationship('ClientReportConfig', back_populates='client', cascade='all, delete-orphan', lazy='dynamic')

    def __repr__(self):
        return f"<Client(name='{self.name}', cpf_cnpj='{self.cpf_cnpj}')>"


