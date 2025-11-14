"""
Script de migração para adicionar grupos/subgrupos a todas as tabelas
e converter extratos bancários existentes em transações
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from config.database import engine, SessionLocal, Base
from models.transaction import Transaction, BankStatement
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable
from datetime import datetime


def column_exists(table_name: str, column_name: str) -> bool:
    """Verifica se uma coluna existe em uma tabela"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def add_columns_if_not_exists():
    """Adiciona colunas group_id e subgroup_id às tabelas se não existirem"""
    db = SessionLocal()
    try:
        tables_to_update = [
            'bank_statements',
            'contracts',
            'accounts_payable',
            'accounts_receivable'
        ]
        
        for table in tables_to_update:
            # Verifica e adiciona group_id
            if not column_exists(table, 'group_id'):
                print(f"Adicionando coluna group_id à tabela {table}...")
                db.execute(text(f"""
                    ALTER TABLE {table} 
                    ADD COLUMN group_id INTEGER REFERENCES groups(id)
                """))
                db.commit()
                print(f"✅ Coluna group_id adicionada à tabela {table}")
            else:
                print(f"ℹ️ Coluna group_id já existe na tabela {table}")
            
            # Verifica e adiciona subgroup_id
            if not column_exists(table, 'subgroup_id'):
                print(f"Adicionando coluna subgroup_id à tabela {table}...")
                db.execute(text(f"""
                    ALTER TABLE {table} 
                    ADD COLUMN subgroup_id INTEGER REFERENCES subgroups(id)
                """))
                db.commit()
                print(f"✅ Coluna subgroup_id adicionada à tabela {table}")
            else:
                print(f"ℹ️ Coluna subgroup_id já existe na tabela {table}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao adicionar colunas: {e}")
        raise
    finally:
        db.close()


def convert_existing_bank_statements():
    """Converte extratos bancários existentes em transações (se ainda não convertidos)"""
    db = SessionLocal()
    try:
        # Busca todos os extratos bancários
        statements = db.query(BankStatement).all()
        
        converted_count = 0
        skipped_count = 0
        
        print(f"\n📊 Encontrados {len(statements)} extratos bancários para processar...")
        
        for statement in statements:
            # Verifica se já existe transação correspondente
            existing = db.query(Transaction).filter(
                Transaction.client_id == statement.client_id,
                Transaction.date == statement.date,
                Transaction.description == statement.description,
                Transaction.value == abs(statement.value),
                Transaction.document_type == 'extrato_bancario'
            ).first()
            
            if not existing:
                # Cria transação correspondente
                transaction = Transaction(
                    client_id=statement.client_id,
                    date=statement.date,
                    description=statement.description,
                    value=abs(statement.value),
                    type='entrada' if statement.value > 0 else 'saida',
                    group_id=statement.group_id,
                    subgroup_id=statement.subgroup_id,
                    account=statement.account,
                    document_type='extrato_bancario',
                    imported_from=f'Extrato: {statement.bank_name or "Banco"}'
                )
                db.add(transaction)
                converted_count += 1
            else:
                skipped_count += 1
        
        if converted_count > 0:
            db.commit()
            print(f"✅ {converted_count} extrato(s) convertido(s) em transações")
        
        if skipped_count > 0:
            print(f"ℹ️ {skipped_count} extrato(s) já possuíam transações correspondentes")
        
        return converted_count
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao converter extratos: {e}")
        raise
    finally:
        db.close()


def main():
    """Executa a migração completa"""
    print("=" * 60)
    print("🔄 Iniciando migração: Adicionar Grupos/Subgrupos")
    print("=" * 60)
    
    try:
        # 1. Adiciona colunas
        print("\n1️⃣ Adicionando colunas group_id e subgroup_id...")
        add_columns_if_not_exists()
        
        # 2. Converte extratos existentes
        print("\n2️⃣ Convertendo extratos bancários existentes em transações...")
        converted = convert_existing_bank_statements()
        
        print("\n" + "=" * 60)
        print("✅ Migração concluída com sucesso!")
        print("=" * 60)
        print(f"\n📊 Resumo:")
        print(f"   - Colunas adicionadas às tabelas")
        print(f"   - {converted} extratos convertidos em transações")
        print("\n💡 Agora todos os dados importados podem usar grupos/subgrupos")
        print("   e aparecerão nos relatórios DRE/DFC!")
        
    except Exception as e:
        print(f"\n❌ Erro durante a migração: {e}")
        print("⚠️ A migração foi interrompida. Verifique os erros acima.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

