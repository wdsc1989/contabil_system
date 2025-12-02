#!/usr/bin/env python3
"""
Script para LIMPAR e RECRIAR banco de dados PostgreSQL em produção
ATENÇÃO: Este script apaga TODOS os dados!
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine, Base, DATABASE_URL
from sqlalchemy import text, inspect

# Importar todos os modelos para garantir que sejam criados
from models import (
    user, client, transaction, contract, account, group, 
    ai_config, financial_investment, credit_card, card_machine, inventory,
    client_report_config
)

def confirmar():
    """Solicita confirmação do usuário"""
    print("=" * 70)
    print("⚠️  ATENÇÃO: ESTE SCRIPT VAI APAGAR TODOS OS DADOS!")
    print("=" * 70)
    print()
    print(f"Banco de dados: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    print()
    print("Esta operação é IRREVERSÍVEL!")
    print()
    
    # Se não for interativo, pede confirmação via argumento
    if len(sys.argv) > 1 and sys.argv[1] == '--confirm':
        print("✅ Confirmação via argumento recebida")
        return True
    
    resposta = input("Digite 'SIM' para confirmar: ")
    return resposta.upper() == 'SIM'

def limpar_banco():
    """Limpa todas as tabelas do banco"""
    print()
    print("=" * 70)
    print("🗑️  LIMPANDO BANCO DE DADOS...")
    print("=" * 70)
    print()
    
    # Detectar tipo de banco
    is_postgres = DATABASE_URL.startswith('postgresql')
    is_sqlite = DATABASE_URL.startswith('sqlite')
    
    print(f"   Tipo de banco: {'PostgreSQL' if is_postgres else 'SQLite' if is_sqlite else 'Desconhecido'}")
    print()
    
    try:
        with engine.begin() as conn:
            # Desabilitar foreign keys temporariamente
            print("1️⃣ Desabilitando constraints...")
            if is_postgres:
                conn.execute(text("SET session_replication_role = 'replica'"))
            elif is_sqlite:
                conn.execute(text("PRAGMA foreign_keys = OFF"))
            print("   ✅ Constraints desabilitadas")
            
            # Listar todas as tabelas
            print("2️⃣ Listando tabelas...")
            inspector = inspect(engine)
            tabelas = inspector.get_table_names()
            print(f"   Encontradas {len(tabelas)} tabelas")
            
            # Deletar dados de todas as tabelas (em ordem reversa para evitar FK errors)
            print("3️⃣ Deletando dados...")
            ordem_deletar = [
                'accounts_receivable',
                'accounts_payable',
                'contracts',
                'transactions',
                'bank_statements',
                'credit_card_invoices',
                'card_machine_statements',
                'financial_investments',
                'inventory',
                'client_report_configs',
                'user_client_permissions',
                'subgroups',
                'groups',
                'clients',
                'users'
            ]
            
            for tabela in ordem_deletar:
                if tabela in tabelas:
                    try:
                        # SQLite precisa de aspas em alguns casos, PostgreSQL não
                        if is_sqlite:
                            conn.execute(text(f'DELETE FROM "{tabela}"'))
                        else:
                            conn.execute(text(f"DELETE FROM {tabela}"))
                        print(f"   ✅ {tabela} - dados deletados")
                    except Exception as e:
                        print(f"   ⚠️  {tabela} - {str(e)[:100]}")
            
            # Reabilitar foreign keys
            print("4️⃣ Reabilitando constraints...")
            if is_postgres:
                conn.execute(text("SET session_replication_role = 'origin'"))
            elif is_sqlite:
                conn.execute(text("PRAGMA foreign_keys = ON"))
            print("   ✅ Constraints reabilitadas")
            
    except Exception as e:
        print(f"\n❌ ERRO ao limpar dados: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def recriar_tabelas():
    """Recria todas as tabelas com as colunas corretas"""
    print()
    print("=" * 70)
    print("🔨 RECRIANDO TABELAS...")
    print("=" * 70)
    print()
    
    try:
        # Drop todas as tabelas
        print("1️⃣ Removendo tabelas antigas...")
        with engine.begin() as conn:
            inspector = inspect(engine)
            tabelas = inspector.get_table_names()
            
            # Desabilitar foreign keys
            conn.execute(text("SET session_replication_role = 'replica'"))
            
            for tabela in tabelas:
                try:
                    if is_postgres:
                        conn.execute(text(f"DROP TABLE IF EXISTS {tabela} CASCADE"))
                    else:
                        # SQLite não suporta CASCADE, mas aceita IF EXISTS
                        conn.execute(text(f"DROP TABLE IF EXISTS {tabela}"))
                    print(f"   ✅ {tabela} - removida")
                except Exception as e:
                    print(f"   ⚠️  {tabela} - {str(e)[:100]}")
            
            conn.execute(text("SET session_replication_role = 'origin'"))
        
        # Recriar todas as tabelas
        print()
        print("2️⃣ Criando tabelas novas...")
        Base.metadata.create_all(bind=engine)
        print("   ✅ Todas as tabelas criadas com colunas corretas")
        
        # Verificar colunas criadas
        print()
        print("3️⃣ Verificando colunas criadas...")
        inspector = inspect(engine)
        
        # Verificar contracts
        if inspector.has_table('contracts'):
            cols = [c['name'] for c in inspector.get_columns('contracts')]
            print(f"   contracts: {len(cols)} colunas")
            for col in ['seller_name', 'event_location', 'service_hours', 'collaborators', 'invoice_number', 'notes']:
                if col in cols:
                    print(f"      ✅ {col}")
                else:
                    print(f"      ❌ {col} - FALTANDO!")
        
        # Verificar accounts_payable
        if inspector.has_table('accounts_payable'):
            cols = [c['name'] for c in inspector.get_columns('accounts_payable')]
            print(f"   accounts_payable: {len(cols)} colunas")
            for col in ['expense_type', 'expense_category', 'description']:
                if col in cols:
                    print(f"      ✅ {col}")
                else:
                    print(f"      ❌ {col} - FALTANDO!")
        
        # Verificar accounts_receivable
        if inspector.has_table('accounts_receivable'):
            cols = [c['name'] for c in inspector.get_columns('accounts_receivable')]
            print(f"   accounts_receivable: {len(cols)} colunas")
            if 'contract_id' in cols:
                print(f"      ✅ contract_id")
            else:
                print(f"      ❌ contract_id - FALTANDO!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO ao recriar tabelas: {e}")
        import traceback
        traceback.print_exc()
        return False

def criar_usuario_admin():
    """Cria usuário admin padrão"""
    print()
    print("=" * 70)
    print("👤 CRIANDO USUÁRIO ADMIN...")
    print("=" * 70)
    print()
    
    try:
        from config.database import SessionLocal
        from services.auth_service import AuthService
        
        db = SessionLocal()
        try:
            # Verificar se já existe
            from models.user import User
            admin = db.query(User).filter(User.username == 'admin').first()
            if admin:
                print("   ⚠️  Usuário admin já existe")
                return True
            
            # Criar admin
            AuthService.create_user(
                db=db,
                username='admin',
                password='admin123',
                email='admin@contabil.com',
                role='admin'
            )
            db.commit()
            print("   ✅ Usuário admin criado")
            print("      Usuário: admin")
            print("      Senha: admin123")
            print("      ⚠️  ALTERE A SENHA APÓS O PRIMEIRO ACESSO!")
            return True
        finally:
            db.close()
    except Exception as e:
        print(f"   ⚠️  Erro ao criar admin: {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print("🔄 RESET COMPLETO DO BANCO DE DADOS POSTGRESQL")
    print("=" * 70)
    print()
    
    if not confirmar():
        print("\n❌ Operação cancelada")
        return 1
    
    # Limpar banco
    if not limpar_banco():
        print("\n❌ Falha ao limpar banco")
        return 1
    
    # Recriar tabelas
    if not recriar_tabelas():
        print("\n❌ Falha ao recriar tabelas")
        return 1
    
    # Criar admin
    criar_usuario_admin()
    
    print()
    print("=" * 70)
    print("✅ RESET CONCLUÍDO COM SUCESSO!")
    print("=" * 70)
    print()
    print("💡 Próximos passos:")
    print("   1. Reiniciar o serviço: sudo systemctl restart contabil")
    print("   2. Acessar a aplicação e fazer login com admin/admin123")
    print("   3. Criar um cliente de exemplo")
    print("   4. Importar dados ou usar scripts de seed")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())







