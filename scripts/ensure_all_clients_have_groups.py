#!/usr/bin/env python3
"""
Script para garantir que todos os clientes tenham grupos e subgrupos padrão pré-cadastrados.
Uso: python scripts/ensure_all_clients_have_groups.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Carrega variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Se dotenv não estiver instalado, tenta carregar manualmente
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

from config.database import SessionLocal, init_db
from models.client import Client
from services.group_template_service import GroupTemplateService


def ensure_all_clients_have_groups():
    """
    Garante que todos os clientes ativos tenham grupos e subgrupos padrão.
    """
    print("=" * 70)
    print("📋 GARANTIR GRUPOS E SUBGRUPOS PARA TODOS OS CLIENTES")
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
        # Busca todos os clientes ativos
        clients = db.query(Client).filter(Client.active == True).all()
        
        if not clients:
            print("ℹ️  Nenhum cliente ativo encontrado.")
            return 0
        
        print(f"📊 Encontrados {len(clients)} cliente(s) ativo(s)")
        print()
        
        total_groups_created = 0
        total_subgroups_created = 0
        clients_processed = 0
        
        for client in clients:
            print(f"🔄 Processando cliente: {client.name} (ID: {client.id})")
            
            # Aplica grupos e subgrupos padrão
            result = GroupTemplateService.ensure_default_groups(db, client.id)
            
            groups_created = result.get("groups_created", 0)
            subgroups_created = result.get("subgroups_created", 0)
            
            if groups_created > 0 or subgroups_created > 0:
                print(f"   ✅ Criados: {groups_created} grupo(s), {subgroups_created} subgrupo(s)")
                total_groups_created += groups_created
                total_subgroups_created += subgroups_created
            else:
                print(f"   ℹ️  Cliente já possui todos os grupos e subgrupos necessários")
            
            clients_processed += 1
            print()
        
        # Resumo
        print("=" * 70)
        print("📊 RESUMO")
        print("=" * 70)
        print(f"   Clientes processados: {clients_processed}")
        print(f"   Grupos criados: {total_groups_created}")
        print(f"   Subgrupos criados: {total_subgroups_created}")
        print()
        print("✅ Processo concluído com sucesso!")
        print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Erro ao processar clientes: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(ensure_all_clients_have_groups())

