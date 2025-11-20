#!/usr/bin/env python3
"""
Script para VERIFICAR e CORRIGIR colunas faltantes
Mostra o status atual e adiciona apenas o que falta
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
from sqlalchemy import text, inspect

def verificar_coluna(table_name, column_name):
    """Verifica se uma coluna existe"""
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def main():
    print("=" * 70)
    print("🔍 VERIFICANDO E CORRIGINDO COLUNAS")
    print("=" * 70)
    print()
    
    # Lista de colunas a verificar
    colunas_contracts = [
        ('seller_name', 'VARCHAR(200)'),
        ('event_location', 'TEXT'),
        ('service_hours', 'FLOAT'),
        ('collaborators', 'TEXT'),
        ('invoice_number', 'VARCHAR(50)'),
        ('notes', 'TEXT')
    ]
    
    colunas_accounts_payable = [
        ('expense_type', 'VARCHAR(20)'),
        ('expense_category', 'VARCHAR(50)'),
        ('description', 'TEXT')
    ]
    
    colunas_accounts_receivable = [
        ('contract_id', 'INTEGER')
    ]
    
    total_faltantes = 0
    total_adicionadas = 0
    
    try:
        # Verificar e adicionar colunas em contracts
        print("📋 Tabela: contracts")
        for col_name, col_type in colunas_contracts:
            existe = verificar_coluna('contracts', col_name)
            if existe:
                print(f"   ✓ {col_name} - EXISTE")
            else:
                print(f"   ✗ {col_name} - FALTANDO (adicionando...)")
                total_faltantes += 1
                try:
                    with engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE contracts ADD COLUMN {col_name} {col_type}"))
                    print(f"   ✅ {col_name} - ADICIONADO")
                    total_adicionadas += 1
                except Exception as e:
                    print(f"   ❌ {col_name} - ERRO: {e}")
        print()
        
        # Verificar e adicionar colunas em accounts_payable
        print("📋 Tabela: accounts_payable")
        for col_name, col_type in colunas_accounts_payable:
            existe = verificar_coluna('accounts_payable', col_name)
            if existe:
                print(f"   ✓ {col_name} - EXISTE")
            else:
                print(f"   ✗ {col_name} - FALTANDO (adicionando...)")
                total_faltantes += 1
                try:
                    with engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE accounts_payable ADD COLUMN {col_name} {col_type}"))
                    print(f"   ✅ {col_name} - ADICIONADO")
                    total_adicionadas += 1
                except Exception as e:
                    print(f"   ❌ {col_name} - ERRO: {e}")
        print()
        
        # Verificar e adicionar colunas em accounts_receivable
        print("📋 Tabela: accounts_receivable")
        for col_name, col_type in colunas_accounts_receivable:
            existe = verificar_coluna('accounts_receivable', col_name)
            if existe:
                print(f"   ✓ {col_name} - EXISTE")
            else:
                print(f"   ✗ {col_name} - FALTANDO (adicionando...)")
                total_faltantes += 1
                try:
                    with engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE accounts_receivable ADD COLUMN {col_name} {col_type}"))
                    print(f"   ✅ {col_name} - ADICIONADO")
                    total_adicionadas += 1
                except Exception as e:
                    print(f"   ❌ {col_name} - ERRO: {e}")
        print()
        
        print("=" * 70)
        print("📊 RESUMO")
        print("=" * 70)
        print(f"   Colunas faltantes encontradas: {total_faltantes}")
        print(f"   Colunas adicionadas: {total_adicionadas}")
        print()
        
        if total_adicionadas > 0:
            print("✅ CORREÇÃO APLICADA COM SUCESSO!")
            print()
            print("💡 Próximo passo:")
            print("   sudo systemctl restart contabil")
        elif total_faltantes == 0:
            print("✅ TODAS AS COLUNAS JÁ EXISTEM!")
            print()
            print("⚠️  Se os erros persistem, pode ser cache do SQLAlchemy.")
            print("   Tente reiniciar o serviço:")
            print("   sudo systemctl restart contabil")
        else:
            print("⚠️  Algumas colunas não puderam ser adicionadas.")
            print("   Verifique os erros acima.")
        
        print()
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

