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

from config.database import SessionLocal
from services.auth_service import AuthService
from models.user import User

def recreate_admin_user():
    """Recria ou atualiza usuário admin"""
    print("=" * 70)
    print("👤 RECRIAR/ATUALIZAR USUÁRIO ADMIN")
    print("=" * 70)
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
            admin.active = True
            
            db.commit()
            db.refresh(admin)
            
            print("✅ Usuário admin atualizado com sucesso!")
            print()
            print("📋 Credenciais:")
            print("   Usuário: admin")
            print("   Senha: admin123")
            print("   Role: admin")
            print("   Email: " + admin.email)
            print()
            print("⚠️  IMPORTANTE: Altere a senha após o primeiro acesso!")
            
        else:
            print("📋 Usuário admin não encontrado. Criando novo usuário...")
            print()
            
            # Cria novo usuário admin
            admin = AuthService.create_user(
                db=db,
                username='admin',
                password='admin123',
                email='admin@contabil.com',
                role='admin'
            )
            
            print("✅ Usuário admin criado com sucesso!")
            print()
            print("📋 Credenciais:")
            print("   Usuário: admin")
            print("   Senha: admin123")
            print("   Role: admin")
            print("   Email: admin@contabil.com")
            print()
            print("⚠️  IMPORTANTE: Altere a senha após o primeiro acesso!")
        
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

