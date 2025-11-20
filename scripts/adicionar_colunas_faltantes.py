#!/usr/bin/env python3
"""
Script robusto para adicionar colunas faltantes no banco de dados
Funciona com SQLite e PostgreSQL
Uso: python3 scripts/adicionar_colunas_faltantes.py
"""
import sys
import os
from pathlib import Path

# Configura encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from config.database import engine, SessionLocal, DATABASE_URL

def is_postgres():
    """Verifica se está usando PostgreSQL"""
    return DATABASE_URL.startswith('postgresql')

def is_sqlite():
    """Verifica se está usando SQLite"""
    return DATABASE_URL.startswith('sqlite')

def column_exists(table_name: str, column_name: str) -> bool:
    """Verifica se uma coluna existe em uma tabela"""
    try:
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            return False
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception as e:
        print(f"   ⚠️  Erro ao verificar coluna {table_name}.{column_name}: {e}")
        return False

def add_column_safe(db, table_name: str, column_name: str, column_type: str, description: str = ""):
    """Adiciona uma coluna de forma segura (verifica se já existe)"""
    if column_exists(table_name, column_name):
        return 'exists'
    
    try:
        # PostgreSQL e SQLite usam sintaxe similar para ADD COLUMN
        if is_postgres():
            # PostgreSQL: suporta IF NOT EXISTS
            sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type}"
        else:
            # SQLite: não suporta IF NOT EXISTS, então verificamos antes
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        
        db.execute(text(sql))
        db.commit()
        return 'added'
    except Exception as e:
        db.rollback()
        error_msg = str(e).lower()
        # Se a coluna já existe, não é um erro crítico
        if 'already exists' in error_msg or 'duplicate column' in error_msg:
            return 'exists'
        return f'error: {e}'

def add_foreign_key_safe(db, table_name: str, column_name: str, ref_table: str, ref_column: str = 'id'):
    """Adiciona foreign key de forma segura (apenas PostgreSQL)"""
    if not is_postgres():
        return 'skipped'  # SQLite não suporta ADD CONSTRAINT facilmente
    
    constraint_name = f"fk_{table_name}_{column_name}"
    
    try:
        # Verifica se a constraint já existe
        result = db.execute(text(f"""
            SELECT COUNT(*) 
            FROM information_schema.table_constraints 
            WHERE constraint_name = '{constraint_name}'
            AND table_name = '{table_name}'
        """))
        if result.scalar() > 0:
            return 'exists'
        
        # Adiciona a foreign key
        sql = f"""
            ALTER TABLE {table_name} 
            ADD CONSTRAINT {constraint_name} 
            FOREIGN KEY ({column_name}) REFERENCES {ref_table}({ref_column})
        """
        db.execute(text(sql))
        db.commit()
        return 'added'
    except Exception as e:
        db.rollback()
        error_msg = str(e).lower()
        if 'already exists' in error_msg or 'duplicate' in error_msg:
            return 'exists'
        return f'error: {e}'

def add_missing_columns():
    """Adiciona todas as colunas faltantes"""
    db = SessionLocal()
    try:
        print("=" * 70)
        print("🔧 ADICIONAR COLUNAS FALTANTES")
        print("=" * 70)
        print()
        print(f"📊 Banco de dados: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
        print(f"   Tipo: {'PostgreSQL' if is_postgres() else 'SQLite'}")
        print()
        
        total_added = 0
        total_exists = 0
        total_errors = 0
        
        # ========== TABELA: contracts ==========
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
            result = add_column_safe(db, 'contracts', col_name, col_type, description)
            if result == 'added':
                print(f"   ✅ {col_name} - adicionado")
                total_added += 1
            elif result == 'exists':
                print(f"   ✓ {col_name} - já existe")
                total_exists += 1
            else:
                print(f"   ❌ {col_name} - {result}")
                total_errors += 1
        
        print()
        
        # ========== TABELA: accounts_payable ==========
        print("📋 Tabela: accounts_payable")
        payable_columns = [
            ('expense_type', 'VARCHAR(20)', 'Tipo CPF ou CNPJ'),
            ('expense_category', 'VARCHAR(50)', 'Categoria de despesa'),
            ('description', 'TEXT', 'Descrição detalhada')
        ]
        
        for col_name, col_type, description in payable_columns:
            result = add_column_safe(db, 'accounts_payable', col_name, col_type, description)
            if result == 'added':
                print(f"   ✅ {col_name} - adicionado")
                total_added += 1
            elif result == 'exists':
                print(f"   ✓ {col_name} - já existe")
                total_exists += 1
            else:
                print(f"   ❌ {col_name} - {result}")
                total_errors += 1
        
        print()
        
        # ========== TABELA: accounts_receivable ==========
        print("📋 Tabela: accounts_receivable")
        receivable_columns = [
            ('contract_id', 'INTEGER', 'Vínculo com contrato')
        ]
        
        for col_name, col_type, description in receivable_columns:
            result = add_column_safe(db, 'accounts_receivable', col_name, col_type, description)
            if result == 'added':
                print(f"   ✅ {col_name} - adicionado")
                total_added += 1
                
                # Tenta adicionar foreign key (apenas PostgreSQL)
                if is_postgres():
                    fk_result = add_foreign_key_safe(db, 'accounts_receivable', 'contract_id', 'contracts', 'id')
                    if fk_result == 'added':
                        print(f"   ✅ Foreign key para {col_name} - adicionada")
                    elif fk_result == 'exists':
                        print(f"   ✓ Foreign key para {col_name} - já existe")
                    elif fk_result != 'skipped':
                        print(f"   ⚠️  Foreign key para {col_name} - {fk_result}")
                
            elif result == 'exists':
                print(f"   ✓ {col_name} - já existe")
                total_exists += 1
            else:
                print(f"   ❌ {col_name} - {result}")
                total_errors += 1
        
        print()
        print("=" * 70)
        print("✅ CONCLUSÃO")
        print("=" * 70)
        print(f"   • Colunas adicionadas: {total_added}")
        print(f"   • Colunas já existentes: {total_exists}")
        if total_errors > 0:
            print(f"   • Erros: {total_errors}")
        print()
        
        if total_added > 0:
            print("💡 Próximo passo: Reiniciar o serviço")
            print("   sudo systemctl restart contabil")
            return True
        elif total_errors > 0:
            print("⚠️  Alguns erros ocorreram. Verifique os logs acima.")
            return False
        else:
            print("✅ Todas as colunas já existem!")
            return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print()
    success = add_missing_columns()
    print()
    sys.exit(0 if success else 1)

