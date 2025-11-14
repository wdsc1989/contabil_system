"""
Modelo de configuração de IA
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime
from config.database import Base


class AIConfig(Base):
    """
    Modelo de configuração de IA do sistema
    """
    __tablename__ = 'ai_config'

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False)  # openai, gemini, ollama
    api_key = Column(Text, nullable=True)  # Chave de API (criptografada ou não)
    model = Column(String(100), nullable=True)  # Modelo específico (gpt-4, gemini-pro, etc)
    enabled = Column(Boolean, default=False, nullable=False)
    base_url = Column(String(500), nullable=True)  # Para Ollama ou APIs customizadas
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AIConfig(provider='{self.provider}', enabled={self.enabled})>"


