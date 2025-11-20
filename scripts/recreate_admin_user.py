#!/usr/bin/env python3
"""
Script para recriar ou atualizar usuário admin
Uso: python3 scripts/recreate_admin_user.py
"""
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Carrega variáveis de ambiente do .env
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Arquivo .env carregado: {env_path}")
else:
    print(f"⚠️  Arquivo .env não encontrado em: {env_path}")

from config.database import SessionLocal, init_db
from services.auth_service import AuthService
from models.user import User

def recreate_admin_user():
    """Recria ou atualiza usuário admin"""
    print("=" * 70)
    print("👤 RECRIAR/ATUALIZAR USUÁRIO ADMIN")
    print("=" * 70)
    print()
    
    # Garante que o banco está inicializado
    try:
        print("🔄 Verificando inicialização do banco de dados...")
        init_db()
        print("✅ Banco de dados inicializado")
        print()
    except Exception as e:
        print(f"⚠️  Aviso ao inicializar banco: {e}")
        print()
    
    db = SessionLocal()
    try:
        # Verifica se usuário admin existe
        admin = db.query(User).filter(User.username == 'admin').first()
        
        if admin:
            print("📋 Usuário admin encontrado. Atualizando...")
            print(f"   ID: {admin.id}")
            print(f"   Email atual: {admin.email}")
            print(f"   Role atual: {admin.role}")
            print()
            
            # Atualiza role para admin (garantir que seja admin, não viewer)
            admin.role = 'admin'
            
            # Atualiza senha
            admin.password_hash = AuthService.hash_password('admin123')
            
            # Ativa usuário se estiver inativo
            if hasattr(admin, 'active'):
                admin.active = True
            
            db.commit()
            db.refresh(admin)
            
            print("✅ Usuário admin atualizado com sucesso!")
            print()
            print("📋 Credenciais:")
            print("   Usuário: admin")
            print("   Senha: admin123")
            print("   Role: admin")
            print(f"   Email: {admin.email}")
            print()
            print("⚠️  IMPORTANTE: Altere a senha após o primeiro acesso!")
            
        else:
            print("📋 Usuário admin não encontrado. Criando novo usuário...")
            print()
            
            # Cria novo usuário admin
            try:
                admin = AuthService.create_user(
                    db=db,
                    username='admin',
                    password='admin123',
                    email='admin@contabil.com',
                    role='admin'
                )
                db.commit()
                
                print("✅ Usuário admin criado com sucesso!")
                print()
                print("📋 Credenciais:")
                print("   Usuário: admin")
                print("   Senha: admin123")
                print("   Role: admin")
                print("   Email: admin@contabil.com")
                print()
                print("⚠️  IMPORTANTE: Altere a senha após o primeiro acesso!")
            except Exception as create_error:
                db.rollback()
                print(f"❌ Erro ao criar usuário: {create_error}")
                import traceback
                traceback.print_exc()
                return False
        
        print()
        print("=" * 70)
        print("✅ Operação concluída com sucesso!")
        print("=" * 70)
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == '__main__':
    try:
        success = recreate_admin_user()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

