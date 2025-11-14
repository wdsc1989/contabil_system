"""
Modelo de faturas de cartão de crédito
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class CreditCardInvoice(Base):
    """
    Modelo de fatura de cartão de crédito
    """
    __tablename__ = 'credit_card_invoices'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    transaction_date = Column(Date, nullable=False, index=True)
    description = Column(String(500), nullable=False)
    value = Column(Float, nullable=False)
    category = Column(String(100))
    establishment = Column(String(200))  # Estabelecimento
    installment_number = Column(Integer)  # Número da parcela (1, 2, 3...)
    total_installments = Column(Integer)  # Total de parcelas
    card_brand = Column(String(50))  # Bandeira do cartão (Visa, Mastercard, etc)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)
    subgroup_id = Column(Integer, ForeignKey('subgroups.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    client = relationship('Client', back_populates='credit_card_invoices')
    group = relationship('Group', back_populates='credit_card_invoices')
    subgroup = relationship('Subgroup', back_populates='credit_card_invoices')

    def __repr__(self):
        return f"<CreditCardInvoice(date='{self.transaction_date}', value={self.value}, establishment='{self.establishment}')>"

