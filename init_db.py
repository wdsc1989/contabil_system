"""
Script para inicializar o banco de dados
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import Base, engine
from models import (
    User, UserClientPermission, Client, Group, Subgroup,
    Transaction, BankStatement, Contract,
    AccountPayable, AccountReceivable, ImportMapping
)


def init_database():
    """
    Cria todas as tabelas no banco de dados
    """
    print("Criando banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("Banco de dados criado com sucesso!")
    print(f"Tabelas criadas: {', '.join(Base.metadata.tables.keys())}")


if __name__ == "__main__":
    init_database()


