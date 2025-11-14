"""
Configuração do banco de dados SQLite com SQLAlchemy
"""
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Diretório do banco de dados
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
os.makedirs(DB_DIR, exist_ok=True)

# URL do banco de dados SQLite
DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'contabil.db')}"

# Engine do SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Necessário para SQLite
    echo=False  # Set to True para debug SQL
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos
Base = declarative_base()


def get_db():
    """
    Dependency para obter uma sessão do banco de dados
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def column_exists(table_name: str, column_name: str) -> bool:
    """Verifica se uma coluna existe em uma tabela"""
    try:
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return False
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except:
        return False


def run_migrations():
    """
    Executa migrações automáticas para adicionar colunas faltantes
    """
    db = SessionLocal()
    try:
        tables_to_update = [
            'bank_statements',
            'contracts',
            'accounts_payable',
            'accounts_receivable'
        ]
        
        for table in tables_to_update:
            # Verifica se a tabela existe
            inspector = inspect(engine)
            if not inspector.has_table(table):
                continue
            
            # Verifica e adiciona group_id
            if not column_exists(table, 'group_id'):
                try:
                    db.execute(text(f"""
                        ALTER TABLE {table} 
                        ADD COLUMN group_id INTEGER REFERENCES groups(id)
                    """))
                    db.commit()
                    print(f"✅ Migração: Coluna group_id adicionada à tabela {table}")
                except Exception as e:
                    db.rollback()
                    print(f"⚠️ Erro ao adicionar group_id à {table}: {e}")
            
            # Verifica e adiciona subgroup_id
            if not column_exists(table, 'subgroup_id'):
                try:
                    db.execute(text(f"""
                        ALTER TABLE {table} 
                        ADD COLUMN subgroup_id INTEGER REFERENCES subgroups(id)
                    """))
                    db.commit()
                    print(f"✅ Migração: Coluna subgroup_id adicionada à tabela {table}")
                except Exception as e:
                    db.rollback()
                    print(f"⚠️ Erro ao adicionar subgroup_id à {table}: {e}")
        
    except Exception as e:
        print(f"⚠️ Erro durante migrações automáticas: {e}")
    finally:
        db.close()


def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas e executando migrações
    """
    from models import (user, client, transaction, contract, account, group, ai_config,
                       financial_investment, credit_card, card_machine, inventory)
    Base.metadata.create_all(bind=engine)
    
    # Executa migrações automáticas para adicionar colunas faltantes
    run_migrations()


