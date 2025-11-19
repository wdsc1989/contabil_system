#!/usr/bin/env python3
"""
Script de migração de dados do SQLite para PostgreSQL
Migra todas as tabelas preservando dados e relacionamentos

Uso:
    python migrate_sqlite_to_postgres.py [sqlite_path] [postgres_url]

Exemplo:
    python migrate_sqlite_to_postgres.py data/contabil.db postgresql://user:pass@localhost:5432/contabil_db
"""

import sys
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Any

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from config.database import Base
from models import (
    User, UserClientPermission, Client, Group, Subgroup,
    Transaction, BankStatement, Contract, AccountPayable,
    AccountReceivable, ImportMapping, AIConfig,
    FinancialInvestment, CreditCardInvoice, CardMachineStatement, Inventory
)

# Ordem de migração (respeitando dependências de foreign keys)
MIGRATION_ORDER = [
    'users',
    'clients',
    'user_client_permissions',
    'groups',
    'subgroups',
    'transactions',
    'bank_statements',
    'contracts',
    'accounts_payable',
    'accounts_receivable',
    'import_mappings',
    'ai_config',
    'financial_investments',
    'credit_card_invoices',
    'card_machine_statements',
    'inventory',
]

# Mapeamento de modelos para nomes de tabelas
MODEL_TO_TABLE = {
    User: 'users',
    Client: 'clients',
    UserClientPermission: 'user_client_permissions',
    Group: 'groups',
    Subgroup: 'subgroups',
    Transaction: 'transactions',
    BankStatement: 'bank_statements',
    Contract: 'contracts',
    AccountPayable: 'accounts_payable',
    AccountReceivable: 'accounts_receivable',
    ImportMapping: 'import_mappings',
    AIConfig: 'ai_config',
    FinancialInvestment: 'financial_investments',
    CreditCardInvoice: 'credit_card_invoices',
    CardMachineStatement: 'card_machine_statements',
    Inventory: 'inventory',
}


def get_sqlite_connection(sqlite_path: str) -> sqlite3.Connection:
    """Conecta ao banco SQLite"""
    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"Banco SQLite não encontrado: {sqlite_path}")
    
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
    return conn


def get_postgres_engine(postgres_url: str):
    """Cria engine do PostgreSQL"""
    if not postgres_url.startswith('postgresql'):
        raise ValueError("URL do PostgreSQL deve começar com 'postgresql://'")
    
    engine = create_engine(postgres_url, echo=False)
    return engine


def get_table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    """Obtém lista de colunas de uma tabela no SQLite"""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def migrate_table(
    sqlite_conn: sqlite3.Connection,
    postgres_engine,
    table_name: str,
    postgres_session
) -> Dict[str, Any]:
    """Migra uma tabela do SQLite para PostgreSQL"""
    print(f"\n📦 Migrando tabela: {table_name}")
    
    # Verifica se a tabela existe no SQLite
    cursor = sqlite_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    if not cursor.fetchone():
        print(f"  ⚠️  Tabela {table_name} não existe no SQLite, pulando...")
        return {'table': table_name, 'rows': 0, 'status': 'skipped'}
    
    # Obtém colunas da tabela
    columns = get_table_columns(sqlite_conn, table_name)
    if not columns:
        print(f"  ⚠️  Tabela {table_name} não tem colunas, pulando...")
        return {'table': table_name, 'rows': 0, 'status': 'skipped'}
    
    # Lê dados do SQLite
    columns_str = ', '.join(columns)
    cursor = sqlite_conn.execute(f"SELECT {columns_str} FROM {table_name}")
    rows = cursor.fetchall()
    
    if not rows:
        print(f"  ℹ️  Tabela {table_name} está vazia")
        return {'table': table_name, 'rows': 0, 'status': 'empty'}
    
    print(f"  📊 Encontrados {len(rows)} registros")
    
    # Prepara dados para inserção
    inserted = 0
    errors = []
    
    for row in rows:
        try:
            # Converte row para dicionário
            row_dict = {col: row[col] for col in columns}
            
            # Remove None values que podem causar problemas
            row_dict = {k: v for k, v in row_dict.items() if v is not None}
            
            # Prepara valores para inserção
            values_str = ', '.join([f":{col}" for col in row_dict.keys()])
            columns_str_insert = ', '.join(row_dict.keys())
            
            # Insere no PostgreSQL
            query = text(f"""
                INSERT INTO {table_name} ({columns_str_insert})
                VALUES ({values_str})
                ON CONFLICT DO NOTHING
            """)
            
            postgres_session.execute(query, row_dict)
            inserted += 1
            
        except Exception as e:
            errors.append(f"Erro na linha {inserted + 1}: {str(e)}")
            if len(errors) <= 5:  # Mostra apenas os primeiros 5 erros
                print(f"    ⚠️  {errors[-1]}")
    
    postgres_session.commit()
    
    if errors:
        print(f"  ⚠️  {len(errors)} erros durante a migração")
    else:
        print(f"  ✅ {inserted} registros migrados com sucesso")
    
    return {
        'table': table_name,
        'rows': inserted,
        'errors': len(errors),
        'status': 'success' if not errors else 'partial'
    }


def validate_migration(
    sqlite_conn: sqlite3.Connection,
    postgres_engine,
    table_name: str
) -> bool:
    """Valida se a migração foi bem-sucedida comparando contagens"""
    try:
        # Conta no SQLite
        cursor = sqlite_conn.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        sqlite_count = cursor.fetchone()['count']
        
        # Conta no PostgreSQL
        with postgres_engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) as count FROM {table_name}"))
            postgres_count = result.fetchone()[0]
        
        if sqlite_count == postgres_count:
            print(f"  ✅ Validação OK: {sqlite_count} registros")
            return True
        else:
            print(f"  ⚠️  Divergência: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
            return False
    except Exception as e:
        print(f"  ⚠️  Erro na validação: {e}")
        return False


def main():
    """Função principal de migração"""
    print("=" * 60)
    print("🔄 MIGRAÇÃO SQLITE → POSTGRESQL")
    print("=" * 60)
    
    # Obtém parâmetros
    if len(sys.argv) < 3:
        print("\n❌ Uso: python migrate_sqlite_to_postgres.py [sqlite_path] [postgres_url]")
        print("\nExemplo:")
        print("  python migrate_sqlite_to_postgres.py data/contabil.db postgresql://user:pass@localhost:5432/contabil_db")
        sys.exit(1)
    
    sqlite_path = sys.argv[1]
    postgres_url = sys.argv[2]
    
    print(f"\n📂 SQLite: {sqlite_path}")
    print(f"🗄️  PostgreSQL: {postgres_url.split('@')[1] if '@' in postgres_url else postgres_url}")
    print(f"⏰ Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Conecta aos bancos
    try:
        print("\n🔌 Conectando aos bancos de dados...")
        sqlite_conn = get_sqlite_connection(sqlite_path)
        postgres_engine = get_postgres_engine(postgres_url)
        postgres_session = sessionmaker(bind=postgres_engine)()
        
        # Cria tabelas no PostgreSQL se não existirem
        print("\n🏗️  Criando estrutura de tabelas no PostgreSQL...")
        Base.metadata.create_all(bind=postgres_engine)
        print("  ✅ Estrutura criada")
        
    except Exception as e:
        print(f"\n❌ Erro ao conectar: {e}")
        sys.exit(1)
    
    # Estatísticas
    results = []
    total_rows = 0
    
    # Migra cada tabela na ordem correta
    print("\n" + "=" * 60)
    print("📦 INICIANDO MIGRAÇÃO DE DADOS")
    print("=" * 60)
    
    for table_name in MIGRATION_ORDER:
        try:
            result = migrate_table(sqlite_conn, postgres_engine, table_name, postgres_session)
            results.append(result)
            total_rows += result.get('rows', 0)
            
            # Valida migração
            if result['status'] != 'skipped':
                validate_migration(sqlite_conn, postgres_engine, table_name)
                
        except Exception as e:
            print(f"  ❌ Erro ao migrar {table_name}: {e}")
            results.append({
                'table': table_name,
                'rows': 0,
                'status': 'error',
                'error': str(e)
            })
    
    # Fecha conexões
    sqlite_conn.close()
    postgres_session.close()
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE MIGRAÇÃO")
    print("=" * 60)
    
    successful = sum(1 for r in results if r['status'] == 'success')
    partial = sum(1 for r in results if r['status'] == 'partial')
    errors = sum(1 for r in results if r['status'] == 'error')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    
    print(f"\n✅ Tabelas migradas com sucesso: {successful}")
    print(f"⚠️  Tabelas com erros parciais: {partial}")
    print(f"❌ Tabelas com erros: {errors}")
    print(f"⏭️  Tabelas puladas: {skipped}")
    print(f"📊 Total de registros migrados: {total_rows:,}")
    
    print("\n📋 Detalhes por tabela:")
    for result in results:
        status_icon = {
            'success': '✅',
            'partial': '⚠️',
            'error': '❌',
            'skipped': '⏭️',
            'empty': 'ℹ️'
        }.get(result['status'], '❓')
        
        rows = result.get('rows', 0)
        print(f"  {status_icon} {result['table']}: {rows} registros")
    
    print(f"\n⏰ Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if errors > 0:
        print("\n⚠️  ATENÇÃO: Algumas tabelas tiveram erros durante a migração!")
        print("   Revise os logs acima e execute novamente se necessário.")
        sys.exit(1)
    else:
        print("\n✅ Migração concluída com sucesso!")
        print("💡 IMPORTANTE: Faça um backup do PostgreSQL agora!")


if __name__ == '__main__':
    main()

