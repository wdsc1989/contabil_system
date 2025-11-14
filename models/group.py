"""
Modelo de grupos e subgrupos para classificação de transações
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from config.database import Base


class Group(Base):
    """
    Modelo de grupo de classificação
    """
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Relacionamentos
    client = relationship('Client', back_populates='groups')
    subgroups = relationship('Subgroup', back_populates='group', cascade='all, delete-orphan')
    transactions = relationship('Transaction', back_populates='group')
    bank_statements = relationship('BankStatement', back_populates='group')
    contracts = relationship('Contract', back_populates='group')
    accounts_payable = relationship('AccountPayable', back_populates='group')
    accounts_receivable = relationship('AccountReceivable', back_populates='group')
    financial_investments = relationship('FinancialInvestment', back_populates='group')
    credit_card_invoices = relationship('CreditCardInvoice', back_populates='group')
    card_machine_statements = relationship('CardMachineStatement', back_populates='group')
    inventory = relationship('Inventory', back_populates='group')

    def __repr__(self):
        return f"<Group(name='{self.name}')>"


class Subgroup(Base):
    """
    Modelo de subgrupo de classificação
    """
    __tablename__ = 'subgroups'

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Relacionamentos
    group = relationship('Group', back_populates='subgroups')
    transactions = relationship('Transaction', back_populates='subgroup')
    bank_statements = relationship('BankStatement', back_populates='subgroup')
    contracts = relationship('Contract', back_populates='subgroup')
    accounts_payable = relationship('AccountPayable', back_populates='subgroup')
    accounts_receivable = relationship('AccountReceivable', back_populates='subgroup')
    financial_investments = relationship('FinancialInvestment', back_populates='subgroup')
    credit_card_invoices = relationship('CreditCardInvoice', back_populates='subgroup')
    card_machine_statements = relationship('CardMachineStatement', back_populates='subgroup')
    inventory = relationship('Inventory', back_populates='subgroup')

    def __repr__(self):
        return f"<Subgroup(name='{self.name}')>"




