#!/usr/bin/env python3
"""
Script para adicionar colunas faltantes no banco de dados PostgreSQL
Executa SQL direto para garantir que todas as colunas sejam criadas
"""
import sys
import os

# Configura encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from config.database import engine, SessionLocal

def column_exists(table_name: str, column_name: str) -> bool:
    """Verifica se uma coluna existe em uma tabela"""
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def add_missing_columns():
    """Adiciona todas as colunas faltantes"""
    db = SessionLocal()
    try:
        print("=" * 70)
        print("🔧 CORREÇÃO: Adicionando Colunas Faltantes")
        print("=" * 70)
        print()
        
        total_added = 0
        total_skipped = 0
        
        # Colunas para tabela contracts
        print("📋 Tabela: contracts")
        contract_columns = [
            ('seller_name', 'VARCHAR(200)', 'Vendedor responsável'),
            ('event_location', 'TEXT', 'Local do evento'),
            ('service_hours', 'FLOAT', 'Horas de serviço'),
            ('collaborators', 'TEXT', 'Colaboradores envolvidos'),
            ('invoice_number', 'VARCHAR(50)', 'Número da NF'),
            ('notes', 'TEXT', 'Observações gerais')
        ]
        
        for col_name, col_type, description in contract_columns:
            if column_exists('contracts', col_name):
                print(f"   ✓ {col_name} - já existe")
                total_skipped += 1
            else:
                try:
                    db.execute(text(f"ALTER TABLE contracts ADD COLUMN {col_name} {col_type}"))
                    db.commit()
                    print(f"   ✅ {col_name} - adicionado")
                    total_added += 1
                except Exception as e:
                    db.rollback()
                    print(f"   ❌ {col_name} - ERRO: {e}")
        
        print()
        
        # Colunas para tabela accounts_payable
        print("📋 Tabela: accounts_payable")
        payable_columns = [
            ('expense_type', 'VARCHAR(20)', 'Tipo CPF ou CNPJ'),
            ('expense_category', 'VARCHAR(50)', 'Categoria de despesa'),
            ('description', 'TEXT', 'Descrição detalhada')
        ]
        
        for col_name, col_type, description in payable_columns:
            if column_exists('accounts_payable', col_name):
                print(f"   ✓ {col_name} - já existe")
                total_skipped += 1
            else:
                try:
                    db.execute(text(f"ALTER TABLE accounts_payable ADD COLUMN {col_name} {col_type}"))
                    db.commit()
                    print(f"   ✅ {col_name} - adicionado")
                    total_added += 1
                except Exception as e:
                    db.rollback()
                    print(f"   ❌ {col_name} - ERRO: {e}")
        
        print()
        
        # Colunas para tabela accounts_receivable
        print("📋 Tabela: accounts_receivable")
        receivable_columns = [
            ('contract_id', 'INTEGER', 'Vínculo com contrato')
        ]
        
        for col_name, col_type, description in receivable_columns:
            if column_exists('accounts_receivable', col_name):
                print(f"   ✓ {col_name} - já existe")
                total_skipped += 1
            else:
                try:
                    # Primeiro adiciona a coluna
                    db.execute(text(f"ALTER TABLE accounts_receivable ADD COLUMN {col_name} {col_type}"))
                    db.commit()
                    # Depois adiciona a foreign key se possível
                    try:
                        db.execute(text(f"""
                            ALTER TABLE accounts_receivable 
                            ADD CONSTRAINT fk_accounts_receivable_contract 
                            FOREIGN KEY (contract_id) REFERENCES contracts(id)
                        """))
                        db.commit()
                        print(f"   ✅ {col_name} - adicionado com foreign key")
                    except:
                        print(f"   ✅ {col_name} - adicionado (sem foreign key)")
                    total_added += 1
                except Exception as e:
                    db.rollback()
                    print(f"   ❌ {col_name} - ERRO: {e}")
        
        print()
        print("=" * 70)
        print("✅ CORREÇÃO CONCLUÍDA")
        print("=" * 70)
        print(f"   • Colunas adicionadas: {total_added}")
        print(f"   • Colunas já existentes: {total_skipped}")
        print()
        
        if total_added > 0:
            print("💡 Próximo passo: Reiniciar o serviço")
            print("   sudo systemctl restart contabil")
        else:
            print("✅ Todas as colunas já existem!")
        
        return total_added > 0
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🔧 CORREÇÃO DE COLUNAS FALTANTES")
    print("=" * 70)
    print()
    
    success = add_missing_columns()
    
    if success:
        print("\n✅ Correção aplicada com sucesso!")
        sys.exit(0)
    else:
        print("\n⚠️  Nenhuma alteração necessária ou erro ocorreu")
        sys.exit(0)

