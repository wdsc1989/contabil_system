"""
Modelo de extratos de máquina de cartão
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class CardMachineStatement(Base):
    """
    Modelo de extrato da máquina de cartão
    """
    __tablename__ = 'card_machine_statements'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    date = Column(Date, nullable=False, index=True)
    gross_value = Column(Float, nullable=False)  # Valor bruto
    fee = Column(Float)  # Taxa
    net_value = Column(Float, nullable=False)  # Valor líquido
    card_brand = Column(String(50))  # Bandeira do cartão (Visa, Mastercard, Elo, etc)
    transaction_type = Column(String(20))  # debito, credito
    description = Column(String(500))
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)
    subgroup_id = Column(Integer, ForeignKey('subgroups.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    client = relationship('Client', back_populates='card_machine_statements')
    group = relationship('Group', back_populates='card_machine_statements')
    subgroup = relationship('Subgroup', back_populates='card_machine_statements')

    def __repr__(self):
        return f"<CardMachineStatement(date='{self.date}', net_value={self.net_value}, type='{self.transaction_type}')>"

