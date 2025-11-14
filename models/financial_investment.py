"""
Modelo de aplicações financeiras
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class FinancialInvestment(Base):
    """
    Modelo de extrato de aplicações financeiras
    """
    __tablename__ = 'financial_investments'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    date = Column(Date, nullable=False, index=True)
    investment_type = Column(String(100))  # Tipo de aplicação (CDB, LCI, LCA, Tesouro, etc)
    institution = Column(String(200))  # Instituição financeira
    operation_type = Column(String(50))  # aplicado, resgatado
    applied_value = Column(Float)  # Valor aplicado
    redeemed_value = Column(Float)  # Valor resgatado
    yield_value = Column(Float)  # Rendimento
    balance = Column(Float)  # Saldo atual
    description = Column(String(500))
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)
    subgroup_id = Column(Integer, ForeignKey('subgroups.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    client = relationship('Client', back_populates='financial_investments')
    group = relationship('Group', back_populates='financial_investments')
    subgroup = relationship('Subgroup', back_populates='financial_investments')

    def __repr__(self):
        return f"<FinancialInvestment(date='{self.date}', type='{self.investment_type}', value={self.applied_value or self.redeemed_value})>"

