#!/usr/bin/env python3
"""
Script para FORÇAR adição de colunas - versão que mostra tudo
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine, DATABASE_URL
from sqlalchemy import text, inspect

print("=" * 70)
print("🔧 FORÇAR ADIÇÃO DE COLUNAS")
print("=" * 70)
print()
print(f"📊 Banco de dados: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
print()

# Verificar colunas atuais
inspector = inspect(engine)

print("🔍 VERIFICANDO COLUNAS ATUAIS...")
print()

# Contracts
print("Tabela: contracts")
if inspector.has_table('contracts'):
    cols_contracts = [c['name'] for c in inspector.get_columns('contracts')]
    print(f"   Colunas existentes ({len(cols_contracts)}): {', '.join(cols_contracts[:10])}...")
    print()
    print("   Verificando colunas necessárias:")
    for col in ['seller_name', 'event_location', 'service_hours', 'collaborators', 'invoice_number', 'notes']:
        if col in cols_contracts:
            print(f"   ✓ {col} - EXISTE")
        else:
            print(f"   ✗ {col} - FALTANDO")
else:
    print("   ❌ Tabela 'contracts' não existe!")
    sys.exit(1)

print()

# Accounts Payable
print("Tabela: accounts_payable")
if inspector.has_table('accounts_payable'):
    cols_payable = [c['name'] for c in inspector.get_columns('accounts_payable')]
    print(f"   Colunas existentes ({len(cols_payable)}): {', '.join(cols_payable[:10])}...")
    print()
    print("   Verificando colunas necessárias:")
    for col in ['expense_type', 'expense_category', 'description']:
        if col in cols_payable:
            print(f"   ✓ {col} - EXISTE")
        else:
            print(f"   ✗ {col} - FALTANDO")
else:
    print("   ❌ Tabela 'accounts_payable' não existe!")

print()

# Accounts Receivable
print("Tabela: accounts_receivable")
if inspector.has_table('accounts_receivable'):
    cols_receivable = [c['name'] for c in inspector.get_columns('accounts_receivable')]
    print(f"   Colunas existentes ({len(cols_receivable)}): {', '.join(cols_receivable[:10])}...")
    print()
    print("   Verificando colunas necessárias:")
    for col in ['contract_id']:
        if col in cols_receivable:
            print(f"   ✓ {col} - EXISTE")
        else:
            print(f"   ✗ {col} - FALTANDO")
else:
    print("   ❌ Tabela 'accounts_receivable' não existe!")

print()
print("=" * 70)
print("🔧 ADICIONANDO COLUNAS FALTANTES...")
print("=" * 70)
print()

adicionadas = 0
erros = 0

try:
    with engine.begin() as conn:
        # Contracts
        print("📋 Adicionando em 'contracts':")
        for col, tipo in [
            ('seller_name', 'VARCHAR(200)'),
            ('event_location', 'TEXT'),
            ('service_hours', 'FLOAT'),
            ('collaborators', 'TEXT'),
            ('invoice_number', 'VARCHAR(50)'),
            ('notes', 'TEXT')
        ]:
            try:
                sql = f"ALTER TABLE contracts ADD COLUMN {col} {tipo}"
                print(f"   Executando: {sql}")
                conn.execute(text(sql))
                print(f"   ✅ {col} - ADICIONADO")
                adicionadas += 1
            except Exception as e:
                msg = str(e)
                if "already exists" in msg or "duplicate" in msg.lower() or "column" in msg.lower() and "already" in msg.lower():
                    print(f"   ⚠️  {col} - JÁ EXISTE (ignorando)")
                else:
                    print(f"   ❌ {col} - ERRO: {msg[:150]}")
                    erros += 1
        
        print()
        
        # Accounts Payable
        print("📋 Adicionando em 'accounts_payable':")
        for col, tipo in [
            ('expense_type', 'VARCHAR(20)'),
            ('expense_category', 'VARCHAR(50)'),
            ('description', 'TEXT')
        ]:
            try:
                sql = f"ALTER TABLE accounts_payable ADD COLUMN {col} {tipo}"
                print(f"   Executando: {sql}")
                conn.execute(text(sql))
                print(f"   ✅ {col} - ADICIONADO")
                adicionadas += 1
            except Exception as e:
                msg = str(e)
                if "already exists" in msg or "duplicate" in msg.lower() or "column" in msg.lower() and "already" in msg.lower():
                    print(f"   ⚠️  {col} - JÁ EXISTE (ignorando)")
                else:
                    print(f"   ❌ {col} - ERRO: {msg[:150]}")
                    erros += 1
        
        print()
        
        # Accounts Receivable
        print("📋 Adicionando em 'accounts_receivable':")
        try:
            sql = "ALTER TABLE accounts_receivable ADD COLUMN contract_id INTEGER"
            print(f"   Executando: {sql}")
            conn.execute(text(sql))
            print(f"   ✅ contract_id - ADICIONADO")
            adicionadas += 1
        except Exception as e:
            msg = str(e)
            if "already exists" in msg or "duplicate" in msg.lower() or "column" in msg.lower() and "already" in msg.lower():
                print(f"   ⚠️  contract_id - JÁ EXISTE (ignorando)")
            else:
                print(f"   ❌ contract_id - ERRO: {msg[:150]}")
                erros += 1

except Exception as e:
    print(f"\n❌ ERRO CRÍTICO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 70)
print("📊 RESUMO")
print("=" * 70)
print(f"   Colunas adicionadas: {adicionadas}")
print(f"   Erros: {erros}")
print()

# Verificar novamente
print("🔍 VERIFICANDO NOVAMENTE...")
print()

inspector = inspect(engine)

# Contracts
print("Tabela: contracts")
if inspector.has_table('contracts'):
    cols_contracts = [c['name'] for c in inspector.get_columns('contracts')]
    todas_ok = all(col in cols_contracts for col in ['seller_name', 'event_location', 'service_hours', 'collaborators', 'invoice_number', 'notes'])
    if todas_ok:
        print("   ✅ TODAS as colunas necessárias existem!")
    else:
        print("   ❌ Ainda faltam colunas:")
        for col in ['seller_name', 'event_location', 'service_hours', 'collaborators', 'invoice_number', 'notes']:
            if col not in cols_contracts:
                print(f"      - {col}")

print()

# Accounts Payable
print("Tabela: accounts_payable")
if inspector.has_table('accounts_payable'):
    cols_payable = [c['name'] for c in inspector.get_columns('accounts_payable')]
    todas_ok = all(col in cols_payable for col in ['expense_type', 'expense_category', 'description'])
    if todas_ok:
        print("   ✅ TODAS as colunas necessárias existem!")
    else:
        print("   ❌ Ainda faltam colunas:")
        for col in ['expense_type', 'expense_category', 'description']:
            if col not in cols_payable:
                print(f"      - {col}")

print()

# Accounts Receivable
print("Tabela: accounts_receivable")
if inspector.has_table('accounts_receivable'):
    cols_receivable = [c['name'] for c in inspector.get_columns('accounts_receivable')]
    if 'contract_id' in cols_receivable:
        print("   ✅ Coluna contract_id existe!")
    else:
        print("   ❌ Ainda falta: contract_id")

print()
print("=" * 70)
if adicionadas > 0 or erros == 0:
    print("✅ PROCESSO CONCLUÍDO")
    print("=" * 70)
    print()
    print("💡 PRÓXIMO PASSO:")
    print("   sudo systemctl restart contabil")
    print()
    print("   Depois verifique os logs:")
    print("   sudo journalctl -u contabil.service -f")
else:
    print("⚠️  ATENÇÃO: Verifique os erros acima")
    print("=" * 70)

