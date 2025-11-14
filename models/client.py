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

    # Relacionamentos
    permissions = relationship('UserClientPermission', back_populates='client', cascade='all, delete-orphan')
    groups = relationship('Group', back_populates='client', cascade='all, delete-orphan')
    transactions = relationship('Transaction', back_populates='client', cascade='all, delete-orphan')
    contracts = relationship('Contract', back_populates='client', cascade='all, delete-orphan')
    accounts_payable = relationship('AccountPayable', back_populates='client', cascade='all, delete-orphan')
    accounts_receivable = relationship('AccountReceivable', back_populates='client', cascade='all, delete-orphan')
    bank_statements = relationship('BankStatement', back_populates='client', cascade='all, delete-orphan')
    financial_investments = relationship('FinancialInvestment', back_populates='client', cascade='all, delete-orphan')
    credit_card_invoices = relationship('CreditCardInvoice', back_populates='client', cascade='all, delete-orphan')
    card_machine_statements = relationship('CardMachineStatement', back_populates='client', cascade='all, delete-orphan')
    inventory = relationship('Inventory', back_populates='client', cascade='all, delete-orphan')
    import_mappings = relationship('ImportMapping', back_populates='client', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Client(name='{self.name}', cpf_cnpj='{self.cpf_cnpj}')>"

