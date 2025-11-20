#!/usr/bin/env python3
"""
Script para verificar a configuração do .env e conexão com o banco
Uso: python3 scripts/verificar_env.py
"""
import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from config.database import engine, DATABASE_URL
from sqlalchemy import text, inspect

def verificar_env():
    """Verifica a configuração do .env e conexão com o banco"""
    
    app_dir = Path(__file__).parent.parent
    env_file = app_dir / '.env'
    
    print("=" * 60)
    print("🔍 Verificar Configuração .env e Banco de Dados")
    print("=" * 60)
    print()
    
    # Verifica se .env existe
    if not env_file.exists():
        print(f"❌ Arquivo .env não encontrado em: {env_file}")
        return False
    
    print(f"✅ Arquivo .env encontrado: {env_file}")
    print()
    
    # Carrega .env
    load_dotenv(dotenv_path=env_file)
    
    # Verifica DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não encontrado no .env")
        return False
    
    print(f"📋 DATABASE_URL: {database_url}")
    print()
    
    # Detecta tipo de banco
    if database_url.startswith('postgresql'):
        print("✅ Tipo de banco: PostgreSQL")
        is_postgres = True
    elif database_url.startswith('sqlite'):
        print("⚠️  Tipo de banco: SQLite (desenvolvimento)")
        is_postgres = False
    else:
        print("❌ Tipo de banco desconhecido")
        return False
    
    print()
    print("🔌 Testando conexão com o banco...")
    
    try:
        with engine.connect() as conn:
            if is_postgres:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ Conexão PostgreSQL OK!")
                print(f"   Versão: {version[:80]}...")
            else:
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.scalar()
                print(f"✅ Conexão SQLite OK!")
                print(f"   Versão: {version}")
            
            # Verifica se as tabelas existem
            print()
            print("📊 Verificando tabelas...")
            inspector = inspect(engine)
            tabelas = inspector.get_table_names()
            
            if tabelas:
                print(f"✅ {len(tabelas)} tabela(s) encontrada(s):")
                for tabela in sorted(tabelas):
                    print(f"   - {tabela}")
            else:
                print("⚠️  Nenhuma tabela encontrada (banco vazio)")
            
            print()
            print("=" * 60)
            print("✅ Verificação concluída com sucesso!")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        print()
        print("💡 Dicas:")
        if is_postgres:
            print("   - Verifique se o PostgreSQL está rodando: sudo systemctl status postgresql")
            print("   - Verifique se o usuário e senha estão corretos")
            print("   - Verifique se o banco de dados existe")
        else:
            print("   - Verifique se o arquivo SQLite existe e tem permissões de leitura/escrita")
        return False

if __name__ == '__main__':
    try:
        sucesso = verificar_env()
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

