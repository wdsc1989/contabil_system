"""
Modelo de contratos e eventos
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class Contract(Base):
    """
    Modelo de contrato/evento
    """
    __tablename__ = 'contracts'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    contract_start = Column(Date, nullable=False)
    event_date = Column(Date, nullable=False, index=True)
    service_value = Column(Float, nullable=False)
    displacement_value = Column(Float, default=0)
    event_type = Column(String(100))
    service_sold = Column(String(200))
    guests_count = Column(Integer)
    contractor_name = Column(String(200), nullable=False)
    payment_terms = Column(Text)
    status = Column(String(50), default='pendente')  # pendente, em_andamento, concluido, cancelado
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True)
    subgroup_id = Column(Integer, ForeignKey('subgroups.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    client = relationship('Client', back_populates='contracts')
    group = relationship('Group', back_populates='contracts')
    subgroup = relationship('Subgroup', back_populates='contracts')

    def __repr__(self):
        return f"<Contract(contractor='{self.contractor_name}', event_date='{self.event_date}', status='{self.status}')>"




