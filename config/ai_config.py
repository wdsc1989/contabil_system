"""
Configuração e gerenciamento de IA
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from models.ai_config import AIConfig
import os


class AIConfigManager:
    """
    Gerenciador de configurações de IA
    """
    
    # Modelos padrão por provedor
    DEFAULT_MODELS = {
        'openai': 'gpt-4o-mini',
        'gemini': 'gemini-1.5-flash',
        'ollama': 'llama3.2',
        'groq': 'llama-3.3-70b-versatile'  # Atualizado: llama-3.1-70b-versatile foi descontinuado
    }
    
    # URLs base padrão
    DEFAULT_BASE_URLS = {
        'ollama': 'http://localhost:11434'
    }

    @staticmethod
    def get_config(db: Session) -> Optional[AIConfig]:
        """
        Obtém a configuração de IA ativa
        """
        return db.query(AIConfig).filter(AIConfig.enabled == True).first()

    @staticmethod
    def get_config_by_provider(db: Session, provider: str) -> Optional[AIConfig]:
        """
        Obtém configuração por provedor
        """
        return db.query(AIConfig).filter(AIConfig.provider == provider).first()

    @staticmethod
    def save_config(
        db: Session,
        provider: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        enabled: bool = True
    ) -> AIConfig:
        """
        Salva ou atualiza configuração de IA
        """
        # Desabilita outras configurações se esta estiver sendo habilitada
        if enabled:
            db.query(AIConfig).filter(AIConfig.enabled == True).update({'enabled': False})
        
        # Busca configuração existente do provedor
        config = db.query(AIConfig).filter(AIConfig.provider == provider).first()
        
        if config:
            # Atualiza existente
            if api_key is not None:
                config.api_key = api_key
            if model is not None:
                config.model = model
            if base_url is not None:
                config.base_url = base_url
            config.enabled = enabled
        else:
            # Cria nova
            if model is None:
                model = AIConfigManager.DEFAULT_MODELS.get(provider)
            if base_url is None and provider in AIConfigManager.DEFAULT_BASE_URLS:
                base_url = AIConfigManager.DEFAULT_BASE_URLS[provider]
            
            config = AIConfig(
                provider=provider,
                api_key=api_key or '',
                model=model,
                base_url=base_url,
                enabled=enabled
            )
            db.add(config)
        
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def delete_config(db: Session, provider: str) -> bool:
        """
        Remove configuração de IA
        """
        config = db.query(AIConfig).filter(AIConfig.provider == provider).first()
        if config:
            db.delete(config)
            db.commit()
            return True
        return False

    @staticmethod
    def get_all_configs(db: Session) -> list[AIConfig]:
        """
        Obtém todas as configurações
        """
        return db.query(AIConfig).all()

    @staticmethod
    def is_configured(db: Session) -> bool:
        """
        Verifica se há alguma configuração de IA ativa
        """
        config = AIConfigManager.get_config(db)
        return config is not None and config.api_key and config.enabled

    @staticmethod
    def get_config_dict(db: Session) -> Optional[Dict[str, Any]]:
        """
        Retorna configuração ativa como dicionário
        """
        config = AIConfigManager.get_config(db)
        if not config:
            return None
        
        return {
            'provider': config.provider,
            'api_key': config.api_key,
            'model': config.model,
            'base_url': config.base_url,
            'enabled': config.enabled
        }

