#!/usr/bin/env python3
"""
Script DIRETO para adicionar colunas faltantes - versão simplificada
Executa SQL direto sem verificações complexas
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
from sqlalchemy import text

def main():
    print("=" * 70)
    print("🔧 ADICIONANDO COLUNAS FALTANTES")
    print("=" * 70)
    print()
    
    try:
        with engine.begin() as conn:
            # Contracts
            print("📋 Adicionando colunas em 'contracts'...")
            try:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN seller_name VARCHAR(200)"))
                print("   ✅ seller_name")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print("   ⚠️  seller_name já existe")
                else:
                    print(f"   ❌ seller_name: {e}")
            
            try:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN event_location TEXT"))
                print("   ✅ event_location")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print("   ⚠️  event_location já existe")
                else:
                    print(f"   ❌ event_location: {e}")
            
            try:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN service_hours FLOAT"))
                print("   ✅ service_hours")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print("   ⚠️  service_hours já existe")
                else:
                    print(f"   ❌ service_hours: {e}")
            
            try:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN collaborators TEXT"))
                print("   ✅ collaborators")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print("   ⚠️  collaborators já existe")
                else:
                    print(f"   ❌ collaborators: {e}")
            
            try:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN invoice_number VARCHAR(50)"))
                print("   ✅ invoice_number")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print("   ⚠️  invoice_number já existe")
                else:
                    print(f"   ❌ invoice_number: {e}")
            
            try:
                conn.execute(text("ALTER TABLE contracts ADD COLUMN notes TEXT"))
                print("   ✅ notes")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print("   ⚠️  notes já existe")
                else:
                    print(f"   ❌ notes: {e}")
            
            print()
            
            # Accounts Payable
            print("📋 Adicionando colunas em 'accounts_payable'...")
            try:
                conn.execute(text("ALTER TABLE accounts_payable ADD COLUMN expense_type VARCHAR(20)"))
                print("   ✅ expense_type")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print("   ⚠️  expense_type já existe")
                else:
                    print(f"   ❌ expense_type: {e}")
            
            try:
                conn.execute(text("ALTER TABLE accounts_payable ADD COLUMN expense_category VARCHAR(50)"))
                print("   ✅ expense_category")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print("   ⚠️  expense_category já existe")
                else:
                    print(f"   ❌ expense_category: {e}")
            
            try:
                conn.execute(text("ALTER TABLE accounts_payable ADD COLUMN description TEXT"))
                print("   ✅ description")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print("   ⚠️  description já existe")
                else:
                    print(f"   ❌ description: {e}")
            
            print()
            
            # Accounts Receivable
            print("📋 Adicionando colunas em 'accounts_receivable'...")
            try:
                conn.execute(text("ALTER TABLE accounts_receivable ADD COLUMN contract_id INTEGER"))
                print("   ✅ contract_id")
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    print("   ⚠️  contract_id já existe")
                else:
                    print(f"   ❌ contract_id: {e}")
            
            print()
            print("=" * 70)
            print("✅ PROCESSO CONCLUÍDO")
            print("=" * 70)
            print()
            print("💡 Próximo passo: Reiniciar o serviço")
            print("   sudo systemctl restart contabil")
            print()
            
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

