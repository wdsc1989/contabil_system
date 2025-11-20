"""
Migração para adicionar novos campos aos modelos AccountPayable e AccountReceivable
Adiciona: expense_type, expense_category, description (contas a pagar)
Adiciona: contract_id (contas a receber)
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


def add_accounts_payable_fields():
    """Adiciona novos campos à tabela accounts_payable"""
    db = SessionLocal()
    try:
        print("\n1️⃣ Expandindo tabela de Contas a Pagar...")
        
        fields_to_add = [
            ('expense_type', 'VARCHAR(20)', 'Tipo CPF ou CNPJ'),
            ('expense_category', 'VARCHAR(50)', 'Categoria: fixa/variavel/financeira/investimento'),
            ('description', 'TEXT', 'Descrição detalhada')
        ]
        
        added_count = 0
        skipped_count = 0
        
        for field_name, field_type, description in fields_to_add:
            if column_exists('accounts_payable', field_name):
                print(f"   ℹ️  Campo '{field_name}' já existe")
                skipped_count += 1
            else:
                print(f"   ➕ Adicionando campo '{field_name}' ({description})...")
                try:
                    db.execute(text(f"""
                        ALTER TABLE accounts_payable 
                        ADD COLUMN {field_name} {field_type}
                    """))
                    db.commit()
                    print(f"   ✅ Campo '{field_name}' adicionado")
                    added_count += 1
                except Exception as e:
                    db.rollback()
                    print(f"   ❌ Erro ao adicionar '{field_name}': {e}")
        
        print(f"\n   📊 Contas a Pagar: {added_count} campos adicionados, {skipped_count} já existentes")
        return added_count
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERRO: {e}")
        return 0
    finally:
        db.close()


def add_accounts_receivable_fields():
    """Adiciona novos campos à tabela accounts_receivable"""
    db = SessionLocal()
    try:
        print("\n2️⃣ Expandindo tabela de Contas a Receber...")
        
        fields_to_add = [
            ('contract_id', 'INTEGER REFERENCES contracts(id)', 'Vínculo com contrato de origem')
        ]
        
        added_count = 0
        skipped_count = 0
        
        for field_name, field_type, description in fields_to_add:
            if column_exists('accounts_receivable', field_name):
                print(f"   ℹ️  Campo '{field_name}' já existe")
                skipped_count += 1
            else:
                print(f"   ➕ Adicionando campo '{field_name}' ({description})...")
                try:
                    db.execute(text(f"""
                        ALTER TABLE accounts_receivable 
                        ADD COLUMN {field_name} {field_type}
                    """))
                    db.commit()
                    print(f"   ✅ Campo '{field_name}' adicionado")
                    added_count += 1
                except Exception as e:
                    db.rollback()
                    print(f"   ❌ Erro ao adicionar '{field_name}': {e}")
        
        print(f"\n   📊 Contas a Receber: {added_count} campos adicionados, {skipped_count} já existentes")
        return added_count
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERRO: {e}")
        return 0
    finally:
        db.close()


def main():
    """Executa a migração"""
    print("\n" + "=" * 70)
    print("🔄 MIGRAÇÃO: Expandir Modelos de Contas")
    print("=" * 70)
    
    total_added = 0
    total_added += add_accounts_payable_fields()
    total_added += add_accounts_receivable_fields()
    
    print("\n" + "=" * 70)
    if total_added > 0:
        print("✅ MIGRAÇÃO CONCLUÍDA")
        print("=" * 70)
        print(f"   • Total de campos adicionados: {total_added}")
        print("\n💡 Próximo passo: Atualizar interfaces e lógica de negócio")
    else:
        print("⚠️  NENHUMA ALTERAÇÃO NECESSÁRIA")
        print("=" * 70)
        print("   • Todos os campos já existem")
    
    return 0


if __name__ == "__main__":
    exit(main())

