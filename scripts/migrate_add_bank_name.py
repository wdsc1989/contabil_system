"""
Script de migração para adicionar campo bank_name em Transaction
e preencher com dados de bank_statements ou imported_from
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from config.database import engine, SessionLocal
from models.transaction import Transaction, BankStatement
import re


def column_exists(table_name: str, column_name: str) -> bool:
    """Verifica se uma coluna existe em uma tabela"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_bank_name_column():
    """Adiciona coluna bank_name à tabela transactions se não existir"""
    db = SessionLocal()
    try:
        if not column_exists('transactions', 'bank_name'):
            print("Adicionando coluna bank_name à tabela transactions...")
            db.execute(text("""
                ALTER TABLE transactions 
                ADD COLUMN bank_name VARCHAR(100)
            """))
            db.commit()
            print("✅ Coluna bank_name adicionada à tabela transactions")
        else:
            print("ℹ️ Coluna bank_name já existe na tabela transactions")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao adicionar coluna: {e}")
        raise
    finally:
        db.close()


def fill_bank_name_from_bank_statements():
    """Preenche bank_name em transactions a partir de bank_statements correspondentes"""
    db = SessionLocal()
    try:
        # Busca todas as transações de extratos bancários sem bank_name
        transactions = db.query(Transaction).filter(
            Transaction.document_type == 'extrato_bancario',
            (Transaction.bank_name == None) | (Transaction.bank_name == '')
        ).all()
        
        print(f"\n📊 Encontradas {len(transactions)} transações de extratos sem bank_name...")
        
        updated_count = 0
        
        for trans in transactions:
            # Tenta encontrar bank_statement correspondente
            bank_stmt = db.query(BankStatement).filter(
                BankStatement.client_id == trans.client_id,
                BankStatement.date == trans.date,
                BankStatement.description == trans.description,
                BankStatement.value == (trans.value if trans.type == 'entrada' else -trans.value)
            ).first()
            
            if bank_stmt and bank_stmt.bank_name:
                trans.bank_name = bank_stmt.bank_name
                updated_count += 1
            else:
                # Tenta extrair de imported_from
                if trans.imported_from:
                    # Formato: "Extrato: Nome do Banco"
                    match = re.search(r'Extrato:\s*(.+)', trans.imported_from)
                    if match:
                        bank_name = match.group(1).strip()
                        if bank_name and bank_name != 'Banco':
                            trans.bank_name = bank_name
                            updated_count += 1
        
        if updated_count > 0:
            db.commit()
            print(f"✅ {updated_count} transação(ões) atualizada(s) com bank_name")
        else:
            print("ℹ️ Nenhuma transação precisou ser atualizada")
        
        return updated_count
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao preencher bank_name: {e}")
        raise
    finally:
        db.close()


def main():
    """Executa a migração completa"""
    print("=" * 60)
    print("🔄 Iniciando migração: Adicionar bank_name em Transaction")
    print("=" * 60)
    
    try:
        # 1. Adiciona coluna
        print("\n1️⃣ Adicionando coluna bank_name...")
        add_bank_name_column()
        
        # 2. Preenche dados existentes
        print("\n2️⃣ Preenchendo bank_name em transações existentes...")
        updated = fill_bank_name_from_bank_statements()
        
        print("\n" + "=" * 60)
        print("✅ Migração concluída com sucesso!")
        print("=" * 60)
        print(f"\n📊 Resumo:")
        print(f"   - Coluna bank_name adicionada")
        print(f"   - {updated} transações atualizadas com bank_name")
        print("\n💡 Agora extratos bancários usam transactions como fonte única!")
        
    except Exception as e:
        print(f"\n❌ Erro durante a migração: {e}")
        print("⚠️ A migração foi interrompida. Verifique os erros acima.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())




