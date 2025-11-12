"""
Modelo de transações e extratos bancários
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class Transaction(Base):
    """
    Modelo de transação financeira
    """
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    date = Column(Date, nullable=False, index=True)
    description = Column(Text, nullable=False)
    value = Column(Float, nullable=False)
    type = Column(String(20), nullable=False)  # entrada, saida
    category = Column(String(100))
    group_id = Column(Integer, ForeignKey('groups.id'))
    subgroup_id = Column(Integer, ForeignKey('subgroups.id'))
    account = Column(String(100))
    document_type = Column(String(50))  # extrato_bancario, fatura_cartao, etc
    imported_from = Column(String(255))  # nome do arquivo importado
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    client = relationship('Client', back_populates='transactions')
    group = relationship('Group', back_populates='transactions')
    subgroup = relationship('Subgroup', back_populates='transactions')

    def __repr__(self):
        return f"<Transaction(date='{self.date}', value={self.value}, type='{self.type}')>"


class BankStatement(Base):
    """
    Modelo de extrato bancário
    """
    __tablename__ = 'bank_statements'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    bank_name = Column(String(100))
    account = Column(String(50))
    date = Column(Date, nullable=False, index=True)
    description = Column(Text, nullable=False)
    value = Column(Float, nullable=False)
    balance = Column(Float)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    client = relationship('Client', back_populates='bank_statements')

    def __repr__(self):
        return f"<BankStatement(date='{self.date}', value={self.value})>"


