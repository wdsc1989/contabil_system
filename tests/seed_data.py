"""
Script para popular o banco de dados com dados de teste
Gera dados de 2 anos para análises comparativas
"""
import sys
import os
import argparse
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import random

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal, Base, engine
from services.auth_service import AuthService
from models.user import User, UserClientPermission
from models.client import Client
from models.group import Group, Subgroup
from models.transaction import Transaction, BankStatement
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable


def clear_database():
    """Limpa todas as tabelas do banco de dados"""
    print("Limpando banco de dados...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✓ Banco de dados limpo")


def create_users(db):
    """Cria usuários de teste"""
    print("\nCriando usuários...")
    
    users = [
        ('admin', 'admin123', 'admin@sistema.com', 'admin'),
        ('gerente1', 'gerente123', 'gerente1@sistema.com', 'manager'),
        ('viewer1', 'viewer123', 'viewer1@sistema.com', 'viewer'),
    ]
    
    created_users = []
    for username, password, email, role in users:
        user = AuthService.create_user(db, username, password, email, role)
        created_users.append(user)
        print(f"✓ Usuário criado: {username} ({role})")
    
    return created_users


def create_clients(db):
    """Cria clientes de teste"""
    print("\nCriando clientes...")
    
    clients_data = [
        ('Empresa de Eventos Ltda', '12.345.678/0001-90', 'Eventos'),
        ('Consultoria XYZ', '98.765.432/0001-10', 'Consultoria'),
        ('Prestador de Serviços', '123.456.789-00', 'Serviços'),
        ('Comércio ABC', '11.222.333/0001-44', 'Comércio'),
        ('Indústria Tech', '55.666.777/0001-88', 'Indústria'),
    ]
    
    clients = []
    for name, cpf_cnpj, tipo in clients_data:
        client = Client(
            name=name, 
            cpf_cnpj=cpf_cnpj, 
            tipo_empresa=tipo,
            active=True
        )
        db.add(client)
        clients.append(client)
    
    db.commit()
    
    for client in clients:
        print(f"✓ Cliente criado: {client.name} [{client.tipo_empresa}]")
    
    return clients


def create_permissions(db, users, clients):
    """Cria permissões de acesso"""
    print("\nCriando permissões...")
    
    # Gerente tem acesso aos 3 primeiros clientes
    gerente = next(u for u in users if u.role == 'manager')
    for client in clients[:3]:
        perm = UserClientPermission(
            user_id=gerente.id,
            client_id=client.id,
            can_view=True,
            can_edit=True,
            can_delete=False
        )
        db.add(perm)
    
    # Viewer tem acesso aos 2 primeiros clientes (apenas visualização)
    viewer = next(u for u in users if u.role == 'viewer')
    for client in clients[:2]:
        perm = UserClientPermission(
            user_id=viewer.id,
            client_id=client.id,
            can_view=True,
            can_edit=False,
            can_delete=False
        )
        db.add(perm)
    
    db.commit()
    print("✓ Permissões criadas")


def create_groups_and_subgroups(db, clients):
    """Cria grupos e subgrupos para classificação"""
    print("\nCriando grupos e subgrupos...")
    
    groups_data = {
        'Receitas': ['Vendas', 'Serviços', 'Eventos', 'Consultorias'],
        'Despesas Operacionais': ['Salários', 'Aluguel', 'Energia', 'Internet', 'Material'],
        'Despesas Comerciais': ['Marketing', 'Comissões', 'Viagens'],
        'Investimentos': ['Equipamentos', 'Software', 'Treinamento']
    }
    
    for client in clients:
        for group_name, subgroups in groups_data.items():
            group = Group(
                client_id=client.id,
                name=group_name,
                description=f"Grupo de {group_name.lower()}"
            )
            db.add(group)
            db.flush()
            
            for subgroup_name in subgroups:
                subgroup = Subgroup(
                    group_id=group.id,
                    name=subgroup_name,
                    description=f"Subgrupo de {subgroup_name.lower()}"
                )
                db.add(subgroup)
    
    db.commit()
    print("✓ Grupos e subgrupos criados")


def generate_transactions(db, client, start_date, end_date):
    """Gera transações financeiras realistas para um período"""
    print(f"\nGerando transações para {client.name}...")
    
    # Obtém grupos e subgrupos do cliente
    groups = db.query(Group).filter(Group.client_id == client.id).all()
    
    if not groups:
        print("⚠️ Nenhum grupo encontrado para o cliente")
        return
    
    receitas_group = next((g for g in groups if 'Receita' in g.name), groups[0])
    despesas_op_group = next((g for g in groups if 'Operacional' in g.name), groups[1] if len(groups) > 1 else groups[0])
    despesas_com_group = next((g for g in groups if 'Comercial' in g.name), groups[2] if len(groups) > 2 else groups[0])
    
    receitas_subgroups = db.query(Subgroup).filter(Subgroup.group_id == receitas_group.id).all()
    despesas_op_subgroups = db.query(Subgroup).filter(Subgroup.group_id == despesas_op_group.id).all()
    despesas_com_subgroups = db.query(Subgroup).filter(Subgroup.group_id == despesas_com_group.id).all()
    
    current_date = start_date
    transaction_count = 0
    
    while current_date <= end_date:
        # Número de transações por mês varia (sazonalidade)
        month = current_date.month
        
        # Meses de alta temporada (mais transações)
        if month in [11, 12, 1, 2]:  # Final de ano e verão
            num_receitas = random.randint(15, 25)
            num_despesas = random.randint(20, 30)
        # Meses de baixa temporada
        elif month in [6, 7, 8]:  # Inverno
            num_receitas = random.randint(5, 12)
            num_despesas = random.randint(15, 20)
        # Meses normais
        else:
            num_receitas = random.randint(10, 18)
            num_despesas = random.randint(18, 25)
        
        # Gera receitas
        for _ in range(num_receitas):
            day = random.randint(1, 28)
            trans_date = date(current_date.year, current_date.month, day)
            
            subgroup = random.choice(receitas_subgroups) if receitas_subgroups else None
            
            # Valores realistas de receitas
            if subgroup and 'Evento' in subgroup.name:
                value = random.uniform(3000, 15000)
            elif subgroup and 'Consultoria' in subgroup.name:
                value = random.uniform(2000, 8000)
            else:
                value = random.uniform(500, 5000)
            
            transaction = Transaction(
                client_id=client.id,
                date=trans_date,
                description=f"Receita de {subgroup.name if subgroup else 'serviços'}",
                value=round(value, 2),
                type='entrada',
                category='Receita',
                group_id=receitas_group.id,
                subgroup_id=subgroup.id if subgroup else None,
                document_type='manual',
                imported_from='seed_data'
            )
            db.add(transaction)
            transaction_count += 1
        
        # Gera despesas operacionais
        for _ in range(num_despesas):
            day = random.randint(1, 28)
            trans_date = date(current_date.year, current_date.month, day)
            
            subgroup = random.choice(despesas_op_subgroups) if despesas_op_subgroups else None
            
            # Valores realistas de despesas
            if subgroup and 'Salário' in subgroup.name:
                value = random.uniform(3000, 8000)
            elif subgroup and 'Aluguel' in subgroup.name:
                value = random.uniform(2000, 5000)
            else:
                value = random.uniform(100, 2000)
            
            transaction = Transaction(
                client_id=client.id,
                date=trans_date,
                description=f"Despesa com {subgroup.name if subgroup else 'operações'}",
                value=round(value, 2),
                type='saida',
                category='Despesa Operacional',
                group_id=despesas_op_group.id,
                subgroup_id=subgroup.id if subgroup else None,
                document_type='manual',
                imported_from='seed_data'
            )
            db.add(transaction)
            transaction_count += 1
        
        # Gera algumas despesas comerciais
        for _ in range(random.randint(3, 8)):
            day = random.randint(1, 28)
            trans_date = date(current_date.year, current_date.month, day)
            
            subgroup = random.choice(despesas_com_subgroups) if despesas_com_subgroups else None
            value = random.uniform(200, 3000)
            
            transaction = Transaction(
                client_id=client.id,
                date=trans_date,
                description=f"Despesa com {subgroup.name if subgroup else 'comercial'}",
                value=round(value, 2),
                type='saida',
                category='Despesa Comercial',
                group_id=despesas_com_group.id,
                subgroup_id=subgroup.id if subgroup else None,
                document_type='manual',
                imported_from='seed_data'
            )
            db.add(transaction)
            transaction_count += 1
        
        # Próximo mês
        current_date = current_date + relativedelta(months=1)
    
    db.commit()
    print(f"✓ {transaction_count} transações criadas")


def generate_contracts(db, client, start_date, end_date):
    """Gera contratos de teste"""
    print(f"\nGerando contratos para {client.name}...")
    
    event_types = ['Casamento', 'Aniversário', 'Formatura', 'Corporativo', 'Festa']
    services = ['Buffet Completo', 'Decoração', 'Som e Iluminação', 'Fotografia', 'Assessoria']
    statuses = ['concluido', 'concluido', 'concluido', 'em_andamento', 'pendente']
    
    current_date = start_date
    contract_count = 0
    
    while current_date <= end_date:
        # Número de contratos por mês varia
        num_contracts = random.randint(2, 8)
        
        for _ in range(num_contracts):
            day = random.randint(1, 28)
            event_date = date(current_date.year, current_date.month, day)
            contract_start = event_date - timedelta(days=random.randint(30, 90))
            
            contract = Contract(
                client_id=client.id,
                contract_start=contract_start,
                event_date=event_date,
                service_value=round(random.uniform(2000, 12000), 2),
                displacement_value=round(random.uniform(0, 500), 2),
                event_type=random.choice(event_types),
                service_sold=random.choice(services),
                guests_count=random.randint(50, 300),
                contractor_name=f"Cliente {random.randint(1, 100)}",
                payment_terms="50% entrada, 50% no evento",
                status=random.choice(statuses)
            )
            db.add(contract)
            contract_count += 1
        
        current_date = current_date + relativedelta(months=1)
    
    db.commit()
    print(f"✓ {contract_count} contratos criados")


def generate_accounts(db, client, start_date, end_date):
    """Gera contas a pagar e receber"""
    print(f"\nGerando contas para {client.name}...")
    
    fornecedores = ['Fornecedor A', 'Fornecedor B', 'Prestador C', 'Empresa D', 'Serviços E']
    clientes_contas = ['Cliente X', 'Cliente Y', 'Cliente Z', 'Empresa W', 'Contratante V']
    
    current_date = start_date
    payable_count = 0
    receivable_count = 0
    
    while current_date <= end_date:
        # Contas a pagar
        for _ in range(random.randint(5, 12)):
            day = random.randint(1, 28)
            due_date = date(current_date.year, current_date.month, day)
            
            # 70% das contas estão pagas
            is_paid = random.random() < 0.7
            payment_date = due_date + timedelta(days=random.randint(0, 15)) if is_paid else None
            
            account = AccountPayable(
                client_id=client.id,
                account_name=random.choice(fornecedores),
                cpf_cnpj=f"{random.randint(10, 99)}.{random.randint(100, 999)}.{random.randint(100, 999)}/0001-{random.randint(10, 99)}",
                due_date=due_date,
                value=round(random.uniform(500, 5000), 2),
                month_ref=current_date.strftime('%Y-%m'),
                paid=is_paid,
                payment_date=payment_date
            )
            db.add(account)
            payable_count += 1
        
        # Contas a receber
        for _ in range(random.randint(3, 10)):
            day = random.randint(1, 28)
            due_date = date(current_date.year, current_date.month, day)
            
            # 80% das contas estão recebidas
            is_received = random.random() < 0.8
            receipt_date = due_date + timedelta(days=random.randint(0, 10)) if is_received else None
            
            account = AccountReceivable(
                client_id=client.id,
                account_name=random.choice(clientes_contas),
                cpf_cnpj=f"{random.randint(100, 999)}.{random.randint(100, 999)}.{random.randint(100, 999)}-{random.randint(10, 99)}",
                due_date=due_date,
                value=round(random.uniform(1000, 8000), 2),
                month_ref=current_date.strftime('%Y-%m'),
                received=is_received,
                receipt_date=receipt_date
            )
            db.add(account)
            receivable_count += 1
        
        current_date = current_date + relativedelta(months=1)
    
    db.commit()
    print(f"✓ {payable_count} contas a pagar criadas")
    print(f"✓ {receivable_count} contas a receber criadas")


def main():
    parser = argparse.ArgumentParser(description='Popula o banco de dados com dados de teste')
    parser.add_argument('--reset', action='store_true', help='Limpa o banco antes de popular')
    args = parser.parse_args()
    
    print("=" * 60)
    print("SEED DE DADOS DE TESTE - Sistema Contábil")
    print("=" * 60)
    
    if args.reset:
        clear_database()
    
    db = SessionLocal()
    
    try:
        # Cria usuários
        users = create_users(db)
        
        # Cria clientes
        clients = create_clients(db)
        
        # Cria permissões
        create_permissions(db, users, clients)
        
        # Cria grupos e subgrupos
        create_groups_and_subgroups(db, clients)
        
        # Define período de 2 anos
        end_date = date.today()
        start_date = end_date - relativedelta(years=2)
        
        print(f"\n📅 Gerando dados de {start_date} a {end_date} (2 anos)")
        
        # Gera dados para cada cliente
        for client in clients:
            generate_transactions(db, client, start_date, end_date)
            generate_contracts(db, client, start_date, end_date)
            generate_accounts(db, client, start_date, end_date)
        
        print("\n" + "=" * 60)
        print("✅ SEED CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print("\n📋 CREDENCIAIS DE ACESSO:")
        print("-" * 60)
        print("Admin:        admin / admin123")
        print("Gerente:      gerente1 / gerente123")
        print("Visualizador: viewer1 / viewer123")
        print("-" * 60)
        print("\n🚀 Execute: streamlit run app.py")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

