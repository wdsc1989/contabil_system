#!/usr/bin/env python3
"""
Script para atualizar o arquivo .env com configuração PostgreSQL
Uso: python3 scripts/atualizar_env_postgres.py
"""
import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

def atualizar_env():
    """Atualiza o arquivo .env com configuração PostgreSQL"""
    
    app_dir = Path(__file__).parent.parent
    env_file = app_dir / '.env'
    env_example = app_dir / 'env.example.txt'
    
    print("=" * 60)
    print("🔧 Atualizar .env para PostgreSQL")
    print("=" * 60)
    print()
    
    # Verifica se .env existe
    if not env_file.exists():
        print(f"❌ Arquivo .env não encontrado em: {env_file}")
        print(f"   Copiando de {env_example}...")
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print(f"✅ Arquivo .env criado!")
        else:
            print(f"❌ Arquivo env.example.txt também não encontrado!")
            return False
    
    # Lê o conteúdo atual
    print(f"📖 Lendo arquivo .env atual...")
    with open(env_file, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Solicita informações do PostgreSQL
    print()
    print("📝 Configure as informações do PostgreSQL:")
    print()
    
    postgres_user = input("Usuário PostgreSQL [contabil_user]: ").strip() or "contabil_user"
    postgres_password = input("Senha PostgreSQL: ").strip()
    if not postgres_password:
        print("❌ Senha é obrigatória!")
        return False
    
    postgres_db = input("Nome do banco [contabil_db]: ").strip() or "contabil_db"
    postgres_host = input("Host [localhost]: ").strip() or "localhost"
    postgres_port = input("Porta [5432]: ").strip() or "5432"
    
    # Gera SECRET_KEY se não existir
    import secrets
    secret_key = secrets.token_urlsafe(32)
    
    # Monta DATABASE_URL
    database_url = f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    
    # Atualiza o conteúdo
    linhas = conteudo.split('\n')
    novo_conteudo = []
    atualizado = {
        'DATABASE_URL': False,
        'POSTGRES_USER': False,
        'POSTGRES_PASSWORD': False,
        'POSTGRES_DB': False,
        'POSTGRES_HOST': False,
        'POSTGRES_PORT': False,
        'SECRET_KEY': False
    }
    
    for linha in linhas:
        linha_original = linha
        linha_stripped = linha.strip()
        
        # Ignora comentários e linhas vazias
        if linha_stripped.startswith('#') or not linha_stripped:
            novo_conteudo.append(linha)
            continue
        
        # Atualiza variáveis
        if linha_stripped.startswith('DATABASE_URL='):
            novo_conteudo.append(f"DATABASE_URL={database_url}")
            atualizado['DATABASE_URL'] = True
        elif linha_stripped.startswith('POSTGRES_USER='):
            novo_conteudo.append(f"POSTGRES_USER={postgres_user}")
            atualizado['POSTGRES_USER'] = True
        elif linha_stripped.startswith('POSTGRES_PASSWORD='):
            novo_conteudo.append(f"POSTGRES_PASSWORD={postgres_password}")
            atualizado['POSTGRES_PASSWORD'] = True
        elif linha_stripped.startswith('POSTGRES_DB='):
            novo_conteudo.append(f"POSTGRES_DB={postgres_db}")
            atualizado['POSTGRES_DB'] = True
        elif linha_stripped.startswith('POSTGRES_HOST='):
            novo_conteudo.append(f"POSTGRES_HOST={postgres_host}")
            atualizado['POSTGRES_HOST'] = True
        elif linha_stripped.startswith('POSTGRES_PORT='):
            novo_conteudo.append(f"POSTGRES_PORT={postgres_port}")
            atualizado['POSTGRES_PORT'] = True
        elif linha_stripped.startswith('SECRET_KEY='):
            # Só atualiza se estiver vazio ou com valor padrão
            if 'SUA_SENHA_AQUI' in linha or 'GERE_UMA_CHAVE' in linha or not linha.split('=', 1)[1].strip():
                novo_conteudo.append(f"SECRET_KEY={secret_key}")
            else:
                novo_conteudo.append(linha)
            atualizado['SECRET_KEY'] = True
        else:
            novo_conteudo.append(linha)
    
    # Adiciona variáveis que não existiam
    if not atualizado['DATABASE_URL']:
        novo_conteudo.append(f"\n# Banco de Dados PostgreSQL")
        novo_conteudo.append(f"DATABASE_URL={database_url}")
    if not atualizado['POSTGRES_USER']:
        novo_conteudo.append(f"POSTGRES_USER={postgres_user}")
    if not atualizado['POSTGRES_PASSWORD']:
        novo_conteudo.append(f"POSTGRES_PASSWORD={postgres_password}")
    if not atualizado['POSTGRES_DB']:
        novo_conteudo.append(f"POSTGRES_DB={postgres_db}")
    if not atualizado['POSTGRES_HOST']:
        novo_conteudo.append(f"POSTGRES_HOST={postgres_host}")
    if not atualizado['POSTGRES_PORT']:
        novo_conteudo.append(f"POSTGRES_PORT={postgres_port}")
    if not atualizado['SECRET_KEY']:
        novo_conteudo.append(f"\n# Segurança")
        novo_conteudo.append(f"SECRET_KEY={secret_key}")
    
    # Salva o arquivo
    print()
    print("💾 Salvando arquivo .env...")
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(novo_conteudo))
    
    print()
    print("✅ Arquivo .env atualizado com sucesso!")
    print()
    print("📋 Configuração aplicada:")
    print(f"   DATABASE_URL={database_url}")
    print(f"   POSTGRES_USER={postgres_user}")
    print(f"   POSTGRES_DB={postgres_db}")
    print(f"   POSTGRES_HOST={postgres_host}")
    print(f"   POSTGRES_PORT={postgres_port}")
    print()
    print("⚠️  IMPORTANTE: Reinicie o serviço para aplicar as mudanças:")
    print("   sudo systemctl restart contabil")
    print()
    
    return True

if __name__ == '__main__':
    try:
        sucesso = atualizar_env()
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

