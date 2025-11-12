"""
Modelo de usuários e permissões
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class User(Base):
    """
    Modelo de usuário do sistema
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(20), nullable=False)  # admin, manager, viewer
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    permissions = relationship('UserClientPermission', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"


class UserClientPermission(Base):
    """
    Modelo de permissões de usuário por cliente
    """
    __tablename__ = 'user_client_permissions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    can_view = Column(Boolean, default=True, nullable=False)
    can_edit = Column(Boolean, default=False, nullable=False)
    can_delete = Column(Boolean, default=False, nullable=False)

    # Relacionamentos
    user = relationship('User', back_populates='permissions')
    client = relationship('Client', back_populates='permissions')

    def __repr__(self):
        return f"<UserClientPermission(user_id={self.user_id}, client_id={self.client_id})>"


