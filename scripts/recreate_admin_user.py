#!/usr/bin/env python3
"""
Script para recriar ou atualizar usuário admin
Uso: python3 scripts/recreate_admin_user.py

IMPORTANTE: Execute este script com o ambiente virtual ativado!
Exemplo:
    source venv/bin/activate
    python3 scripts/recreate_admin_user.py
"""
import sys
import os
from pathlib import Path

# Verifica se está em ambiente virtual
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    venv_path = Path(__file__).parent.parent / 'venv'
    if venv_path.exists():
        print("⚠️  AVISO: Ambiente virtual não detectado!")
        print(f"   Execute: source {venv_path}/bin/activate")
        print("   E então execute este script novamente.")
        print()
        # Tenta usar o Python do venv automaticamente
        venv_python = venv_path / 'bin' / 'python3'
        if venv_python.exists():
            print(f"🔄 Tentando usar Python do venv: {venv_python}")
            os.execv(str(venv_python), [str(venv_python)] + sys.argv)
        else:
            sys.exit(1)

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Carrega variáveis de ambiente do .env (opcional)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Arquivo .env carregado: {env_path}")
    else:
        print(f"⚠️  Arquivo .env não encontrado em: {env_path}")
except ImportError:
    # Se dotenv não estiver instalado, tenta carregar manualmente
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        print(f"📋 Carregando .env manualmente...")
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
        print(f"✅ Variáveis de ambiente carregadas de: {env_path}")
    else:
        print(f"⚠️  Arquivo .env não encontrado em: {env_path}")
        print("   Usando variáveis de ambiente do sistema")

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
        # Verifica se usuário admin existe por username OU email
        admin = db.query(User).filter(
            (User.username == 'admin') | (User.email == 'admin@contabil.com')
        ).first()
        
        if admin:
            print("📋 Usuário admin encontrado. Atualizando...")
            print(f"   ID: {admin.id}")
            print(f"   Username atual: {admin.username}")
            print(f"   Email atual: {admin.email}")
            print(f"   Role atual: {admin.role}")
            print()
            
            # Atualiza username para 'admin' (caso esteja diferente)
            admin.username = 'admin'
            
            # Atualiza role para admin (garantir que seja admin, não viewer)
            admin.role = 'admin'
            
            # Atualiza email para garantir que seja o correto
            admin.email = 'admin@contabil.com'
            
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
                # Se erro for de duplicação, tenta atualizar o usuário existente
                if 'duplicate key' in str(create_error).lower() or 'unique' in str(create_error).lower():
                    print("⚠️  Usuário com email já existe. Tentando atualizar...")
                    # Busca por email
                    existing_user = db.query(User).filter(User.email == 'admin@contabil.com').first()
                    if existing_user:
                        existing_user.username = 'admin'
                        existing_user.role = 'admin'
                        existing_user.password_hash = AuthService.hash_password('admin123')
                        if hasattr(existing_user, 'active'):
                            existing_user.active = True
                        db.commit()
                        db.refresh(existing_user)
                        print("✅ Usuário atualizado com sucesso!")
                        print()
                        print("📋 Credenciais:")
                        print("   Usuário: admin")
                        print("   Senha: admin123")
                        print("   Role: admin")
                        print(f"   Email: {existing_user.email}")
                    else:
                        print(f"❌ Erro ao criar usuário: {create_error}")
                        import traceback
                        traceback.print_exc()
                        return False
                else:
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





