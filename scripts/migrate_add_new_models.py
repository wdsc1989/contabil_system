"""
Script de migração para adicionar novos modelos e campos ao banco de dados
Adiciona campos em AccountPayable, AccountReceivable e cria novas tabelas
"""
import sys
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa Base e engine do config.database
from config.database import Base, engine, SessionLocal

def migrate_database():
    """
    Executa migração para adicionar novos campos e tabelas
    """
    db = SessionLocal()
    inspector = inspect(engine)
    
    try:
        print("============================================================")
        print("🔄 Iniciando migração: Novos modelos e campos")
        print("============================================================")
        
        # 1. Adicionar novos campos em accounts_payable
        print("\n1️⃣ Adicionando campos em accounts_payable...")
        with engine.connect() as connection:
            columns = [col['name'] for col in inspector.get_columns('accounts_payable')]
            
            if 'monthly_installments' not in columns:
                connection.execute(text("ALTER TABLE accounts_payable ADD COLUMN monthly_installments INTEGER"))
                print("   ✅ monthly_installments adicionado")
            else:
                print("   ℹ️ monthly_installments já existe")
            
            if 'total_monthly_outflow' not in columns:
                connection.execute(text("ALTER TABLE accounts_payable ADD COLUMN total_monthly_outflow FLOAT"))
                print("   ✅ total_monthly_outflow adicionado")
            else:
                print("   ℹ️ total_monthly_outflow já existe")
            
            if 'installment_number' not in columns:
                connection.execute(text("ALTER TABLE accounts_payable ADD COLUMN installment_number INTEGER"))
                print("   ✅ installment_number adicionado")
            else:
                print("   ℹ️ installment_number já existe")
            
            connection.commit()
        
        # 2. Adicionar novos campos em accounts_receivable
        print("\n2️⃣ Adicionando campos em accounts_receivable...")
        with engine.connect() as connection:
            columns = [col['name'] for col in inspector.get_columns('accounts_receivable')]
            
            if 'event_date' not in columns:
                connection.execute(text("ALTER TABLE accounts_receivable ADD COLUMN event_date DATE"))
                print("   ✅ event_date adicionado")
            else:
                print("   ℹ️ event_date já existe")
            
            if 'contract_value' not in columns:
                connection.execute(text("ALTER TABLE accounts_receivable ADD COLUMN contract_value FLOAT"))
                print("   ✅ contract_value adicionado")
            else:
                print("   ℹ️ contract_value já existe")
            
            if 'payment_method' not in columns:
                connection.execute(text("ALTER TABLE accounts_receivable ADD COLUMN payment_method VARCHAR(100)"))
                print("   ✅ payment_method adicionado")
            else:
                print("   ℹ️ payment_method já existe")
            
            if 'monthly_installments' not in columns:
                connection.execute(text("ALTER TABLE accounts_receivable ADD COLUMN monthly_installments INTEGER"))
                print("   ✅ monthly_installments adicionado")
            else:
                print("   ℹ️ monthly_installments já existe")
            
            if 'total_expected_inflow' not in columns:
                connection.execute(text("ALTER TABLE accounts_receivable ADD COLUMN total_expected_inflow FLOAT"))
                print("   ✅ total_expected_inflow adicionado")
            else:
                print("   ℹ️ total_expected_inflow já existe")
            
            if 'installment_number' not in columns:
                connection.execute(text("ALTER TABLE accounts_receivable ADD COLUMN installment_number INTEGER"))
                print("   ✅ installment_number adicionado")
            else:
                print("   ℹ️ installment_number já existe")
            
            connection.commit()
        
        # 3. Criar novas tabelas usando Base.metadata
        print("\n3️⃣ Criando novas tabelas...")
        from models.financial_investment import FinancialInvestment
        from models.credit_card import CreditCardInvoice
        from models.card_machine import CardMachineStatement
        from models.inventory import Inventory
        
        # Cria todas as tabelas que não existem
        Base.metadata.create_all(bind=engine)
        
        tables = inspector.get_table_names()
        new_tables = ['financial_investments', 'credit_card_invoices', 'card_machine_statements', 'inventory']
        
        for table in new_tables:
            if table in tables:
                print(f"   ✅ Tabela {table} criada/existe")
            else:
                print(f"   ⚠️ Tabela {table} não foi criada")
        
        print("\n============================================================")
        print("✅ Migração concluída com sucesso!")
        print("============================================================")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Erro durante a migração: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_database()

