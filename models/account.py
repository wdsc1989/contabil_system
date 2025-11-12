"""
Modelo de contas a pagar, receber e mapeamentos de importação
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class AccountPayable(Base):
    """
    Modelo de conta a pagar
    """
    __tablename__ = 'accounts_payable'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    account_name = Column(String(200), nullable=False)
    cpf_cnpj = Column(String(18))
    due_date = Column(Date, nullable=False, index=True)
    value = Column(Float, nullable=False)
    month_ref = Column(String(7))  # YYYY-MM
    paid = Column(Boolean, default=False, nullable=False)
    payment_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    client = relationship('Client', back_populates='accounts_payable')

    def __repr__(self):
        return f"<AccountPayable(account='{self.account_name}', due_date='{self.due_date}', value={self.value})>"


class AccountReceivable(Base):
    """
    Modelo de conta a receber
    """
    __tablename__ = 'accounts_receivable'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    account_name = Column(String(200), nullable=False)
    cpf_cnpj = Column(String(18))
    due_date = Column(Date, nullable=False, index=True)
    value = Column(Float, nullable=False)
    month_ref = Column(String(7))  # YYYY-MM
    received = Column(Boolean, default=False, nullable=False)
    receipt_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    client = relationship('Client', back_populates='accounts_receivable')

    def __repr__(self):
        return f"<AccountReceivable(account='{self.account_name}', due_date='{self.due_date}', value={self.value})>"


class ImportMapping(Base):
    """
    Modelo de mapeamento de colunas para importação
    """
    __tablename__ = 'import_mappings'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    import_type = Column(String(50), nullable=False)  # extrato_bancario, contratos, etc
    source_column = Column(String(100), nullable=False)
    target_column = Column(String(100), nullable=False)
    transformation_rule = Column(Text)  # Regra de transformação opcional (JSON)

    # Relacionamentos
    client = relationship('Client', back_populates='import_mappings')

    def __repr__(self):
        return f"<ImportMapping(type='{self.import_type}', {self.source_column}->{self.target_column})>"


