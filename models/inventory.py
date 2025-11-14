"""
Modelo de controle de estoque
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class Inventory(Base):
    """
    Modelo de controle de estoque
    """
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Float, nullable=False)  # Quantidade (pode ser decimal para produtos fracionados)
    unit_value = Column(Float, nullable=False)  # Valor unitário
    total_value = Column(Float, nullable=False)  # Valor total (quantity * unit_value)
    movement_date = Column(Date, nullable=False, index=True)
    movement_type = Column(String(20), nullable=False)  # entrada, saida
    description = Column(String(500))
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)
    subgroup_id = Column(Integer, ForeignKey('subgroups.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    client = relationship('Client', back_populates='inventory')
    group = relationship('Group', back_populates='inventory')
    subgroup = relationship('Subgroup', back_populates='inventory')

    def __repr__(self):
        return f"<Inventory(product='{self.product_name}', quantity={self.quantity}, type='{self.movement_type}')>"

