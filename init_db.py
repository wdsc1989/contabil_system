"""
Script para inicializar o banco de dados
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import Base, engine, SessionLocal
from models import (
    User, UserClientPermission, Client, Group, Subgroup,
    Transaction, BankStatement, Contract,
    AccountPayable, AccountReceivable, ImportMapping,
    ClientReportConfig
)
from services.report_config_service import ReportConfigService
from services.group_template_service import GroupTemplateService


def init_database():
    """
    Cria todas as tabelas no banco de dados e configurações padrão
    """
    print("Criando banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("Banco de dados criado com sucesso!")
    print(f"Tabelas criadas: {', '.join(Base.metadata.tables.keys())}")
    
    # Cria configurações padrão e grupos/subgrupos para clientes existentes
    print("\nCriando configurações padrão de relatórios e grupos/subgrupos para clientes existentes...")
    db = SessionLocal()
    try:
        clients = db.query(Client).all()
        for client in clients:
            # Configurações de relatórios
            ReportConfigService.ensure_default_config(db, client.id)
            # Grupos e subgrupos padrão
            GroupTemplateService.ensure_default_groups(db, client.id)
        print(f"✅ Configurações padrão e grupos/subgrupos criados para {len(clients)} cliente(s).")
    except Exception as e:
        print(f"⚠️ Aviso ao criar configurações padrão: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_database()


