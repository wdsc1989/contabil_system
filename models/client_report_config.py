"""
Modelo de configuração de relatórios por cliente
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from config.database import Base


class ClientReportConfig(Base):
    """
    Modelo de configuração de relatórios por cliente
    Define quais tipos de dados devem aparecer em cada relatório
    """
    __tablename__ = 'client_report_configs'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    report_type = Column(String(50), nullable=False)  # 'dre', 'dfc', 'sazonalidade'
    data_type = Column(String(50), nullable=False)  # 'transactions', 'bank_statements', etc.
    enabled = Column(Boolean, default=True, nullable=False)

    # Relacionamentos
    client = relationship('Client', back_populates='report_configs')

    # Constraint único: um cliente não pode ter duas configurações para o mesmo report_type e data_type
    __table_args__ = (
        UniqueConstraint('client_id', 'report_type', 'data_type', name='uq_client_report_data_type'),
    )

    def __repr__(self):
        return f"<ClientReportConfig(client_id={self.client_id}, report_type='{self.report_type}', data_type='{self.data_type}', enabled={self.enabled})>"
