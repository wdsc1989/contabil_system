"""
Configurações de produção
"""
import os
from typing import Optional

# Configurações de ambiente
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Configurações do banco de dados
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL deve ser configurada em produção")

# Configurações de segurança
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY deve ser configurada em produção")

# Configurações do Streamlit
STREAMLIT_SERVER_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', '8501'))
STREAMLIT_SERVER_ADDRESS = os.getenv('STREAMLIT_SERVER_ADDRESS', '127.0.0.1')
STREAMLIT_SERVER_HEADLESS = os.getenv('STREAMLIT_SERVER_HEADLESS', 'true').lower() == 'true'

# Configurações de logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DIR = os.getenv('LOG_DIR', '/var/log/contabil')

# Configurações de backup
BACKUP_DIR = os.getenv('BACKUP_DIR', '/var/backups/contabil/postgresql')
BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '7'))

# Configurações de email (opcional)
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_FROM = os.getenv('SMTP_FROM')

# Configurações de domínio
DOMAIN = os.getenv('DOMAIN', 'localhost')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else []

def get_config_dict() -> dict:
    """Retorna dicionário com todas as configurações"""
    return {
        'environment': ENVIRONMENT,
        'debug': DEBUG,
        'database_url': DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else '***',
        'streamlit_port': STREAMLIT_SERVER_PORT,
        'streamlit_address': STREAMLIT_SERVER_ADDRESS,
        'log_level': LOG_LEVEL,
        'backup_dir': BACKUP_DIR,
        'domain': DOMAIN,
    }

























