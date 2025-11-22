"""
Migração para adicionar novos campos ao modelo Contract
Adiciona: seller_name, event_location, service_hours, collaborators, invoice_number, notes
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


def add_contract_fields():
    """Adiciona novos campos à tabela contracts"""
    db = SessionLocal()
    try:
        print("=" * 70)
        print("🔄 Migração: Expandir tabela de contratos")
        print("=" * 70)
        
        fields_to_add = [
            ('seller_name', 'VARCHAR(200)', 'Vendedor responsável'),
            ('event_location', 'TEXT', 'Local do evento'),
            ('service_hours', 'FLOAT', 'Horas de serviço'),
            ('collaborators', 'TEXT', 'Colaboradores envolvidos'),
            ('invoice_number', 'VARCHAR(50)', 'Número da NF'),
            ('notes', 'TEXT', 'Observações gerais')
        ]
        
        added_count = 0
        skipped_count = 0
        
        for field_name, field_type, description in fields_to_add:
            if column_exists('contracts', field_name):
                print(f"   ℹ️  Campo '{field_name}' já existe")
                skipped_count += 1
            else:
                print(f"   ➕ Adicionando campo '{field_name}' ({description})...")
                try:
                    db.execute(text(f"""
                        ALTER TABLE contracts 
                        ADD COLUMN {field_name} {field_type}
                    """))
                    db.commit()
                    print(f"   ✅ Campo '{field_name}' adicionado")
                    added_count += 1
                except Exception as e:
                    db.rollback()
                    print(f"   ❌ Erro ao adicionar '{field_name}': {e}")
        
        print("\n" + "=" * 70)
        print("✅ MIGRAÇÃO CONCLUÍDA")
        print("=" * 70)
        print(f"   • Campos adicionados: {added_count}")
        print(f"   • Campos já existentes: {skipped_count}")
        
        return added_count > 0
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERRO na migração: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Executa a migração"""
    print("\n" + "=" * 70)
    print("🔄 MIGRAÇÃO: Expandir Modelo de Contratos")
    print("=" * 70)
    
    success = add_contract_fields()
    
    if success:
        print("\n✅ Migração aplicada com sucesso!")
        print("💡 Próximo passo: Atualizar interfaces e importação")
        return 0
    else:
        print("\n⚠️  Nenhuma alteração necessária (campos já existem)")
        return 0


if __name__ == "__main__":
    exit(main())





