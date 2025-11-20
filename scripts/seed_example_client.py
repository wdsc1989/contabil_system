"""
Script para criar cliente exemplo com 2 meses de dados genéricos
Popula todas as tabelas para validação completa do sistema
"""
import sys
import os
from datetime import date, datetime, timedelta
import random

# Configura encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal, init_db
from models.client import Client
from models.group import Group, Subgroup
from models.transaction import Transaction, BankStatement
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable
from models.financial_investment import FinancialInvestment
from models.credit_card import CreditCardInvoice
from models.card_machine import CardMachineStatement
from models.inventory import Inventory
from services.report_config_service import ReportConfigService
from services.group_template_service import GroupTemplateService


EXAMPLE_CLIENT_NAME = "Empresa Exemplo - Eventos"
EXAMPLE_CNPJ = "12.345.678/0001-90"


def create_example_client():
    """
    Cria cliente exemplo com 2 meses de dados (Nov/Dez 2025)
    """
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("🎨 CRIANDO CLIENTE EXEMPLO COM 2 MESES DE DADOS")
        print("=" * 70)
        
        # 1. Criar cliente
        print("\n1. Criando cliente exemplo...")
        client = Client(
            name=EXAMPLE_CLIENT_NAME,
            cpf_cnpj=EXAMPLE_CNPJ,
            tipo_empresa="Empresa de Eventos",
            active=True
        )
        db.add(client)
        db.commit()
        db.refresh(client)
        print(f"   ✅ Cliente criado: {client.name} (ID: {client.id})")
        
        # 2. Aplicar grupos e subgrupos
        print("\n2. Aplicando plano de contas (grupos/subgrupos)...")
        GroupTemplateService.ensure_default_groups(db, client.id)
        
        # Busca grupos criados
        grupos = db.query(Group).filter(Group.client_id == client.id).all()
        print(f"   ✅ {len(grupos)} grupos aplicados")
        
        grupos_map = {g.name: g for g in grupos}
        
        # Busca subgrupos
        receitas_subgrupos = db.query(Subgroup).join(Group).filter(
            Group.client_id == client.id,
            Group.name.contains('Receita')
        ).all()
        
        despesas_subgrupos = db.query(Subgroup).join(Group).filter(
            Group.client_id == client.id,
            Group.name.contains('Despesa')
        ).all()
        
        # 3. Criar contratos/eventos (Nov e Dez 2025)
        print("\n3. Criando contratos/eventos...")
        
        contratos_data = [
            # Novembro 2025
            {"data": date(2025, 11, 15), "cliente": "Marina Costa", "evento": "Casamento", "valor": 18500, "convidados": 180, "local": "Espaço Villa - SP"},
            {"data": date(2025, 11, 22), "cliente": "Empresa TechCorp", "evento": "Confraternização", "valor": 8500, "convidados": 100, "local": "Salão Empresarial - SP"},
            {"data": date(2025, 11, 28), "cliente": "Ana Silva", "evento": "15 Anos", "valor": 12000, "convidados": 150, "local": "Casa de Festas Alegria - SP"},
            {"data": date(2025, 11, 30), "cliente": "João Oliveira", "evento": "Aniversário", "valor": 5500, "convidados": 80, "local": "Chácara Vista Linda - SP"},
            # Dezembro 2025
            {"data": date(2025, 12, 6), "cliente": "Carla Mendes", "evento": "Casamento", "valor": 22000, "convidados": 200, "local": "Haras Morena - SP"},
            {"data": date(2025, 12, 13), "cliente": "Empresa LogiTech", "evento": "Confraternização", "valor": 15000, "convidados": 150, "local": "Hotel Grand Plaza - SP"},
            {"data": date(2025, 12, 20), "cliente": "Paula Santos", "evento": "Casamento", "valor": 20000, "convidados": 190, "local": "Fazenda Santa Cruz - SP"},
            {"data": date(2025, 12, 27), "cliente": "Marcos Lima", "evento": "Reveillon", "valor": 25000, "convidados": 250, "local": "Clube Náutico - SP"},
        ]
        
        contratos = []
        receitas_group = grupos_map.get("Receitas Operacionais")
        receitas_subgroup = receitas_subgrupos[0] if receitas_subgrupos else None
        
        for i, c_data in enumerate(contratos_data):
            contract = Contract(
                client_id=client.id,
                contractor_name=c_data["cliente"],
                contract_start=c_data["data"] - timedelta(days=60),  # Contrato 2 meses antes
                event_date=c_data["data"],
                service_value=c_data["valor"],
                displacement_value=random.uniform(500, 1500),  # Deslocamento aleatório
                event_type=c_data["evento"],
                service_sold="Bar de drinks e buffet completo",
                guests_count=c_data["convidados"],
                status='concluido' if c_data["data"] < date.today() else 'em_andamento',
                group_id=receitas_group.id if receitas_group else None,
                subgroup_id=receitas_subgroup.id if receitas_subgroup else None
            )
            contratos.append(contract)
        
        db.bulk_save_objects(contratos)
        db.commit()
        print(f"   ✅ {len(contratos)} contratos criados")
        
        # 4. Criar contas a receber (parcelas dos contratos)
        print("\n4. Criando contas a receber...")
        
        contas_receber = []
        for contract_data, contract_obj in zip(contratos_data, contratos):
            # Contratos acima de 15k parcelados em 2x, outros à vista
            valor_total = contract_data["valor"]
            
            if valor_total >= 15000:
                # 2 parcelas
                for parcela in range(1, 3):
                    account = AccountReceivable(
                        client_id=client.id,
                        account_name=contract_data["cliente"],
                        due_date=contract_data["data"] + timedelta(days=30 * parcela),
                        value=valor_total / 2,
                        received=parcela == 1,  # Primeira parcela recebida
                        receipt_date=contract_data["data"] + timedelta(days=30 * parcela) if parcela == 1 else None,
                        group_id=receitas_group.id if receitas_group else None,
                        subgroup_id=receitas_subgroup.id if receitas_subgroup else None
                    )
                    contas_receber.append(account)
            else:
                # À vista
                account = AccountReceivable(
                    client_id=client.id,
                    account_name=contract_data["cliente"],
                    due_date=contract_data["data"] + timedelta(days=15),
                    value=valor_total,
                    received=True,
                    receipt_date=contract_data["data"] + timedelta(days=15),
                    group_id=receitas_group.id if receitas_group else None,
                    subgroup_id=receitas_subgroup.id if receitas_subgroup else None
                )
                contas_receber.append(account)
        
        db.bulk_save_objects(contas_receber)
        db.commit()
        print(f"   ✅ {len(contas_receber)} contas a receber criadas")
        
        # 5. Criar contas a pagar (despesas fixas e variáveis, CPF e CNPJ)
        print("\n5. Criando contas a pagar...")
        
        despesas_group = grupos_map.get("Despesas Operacionais")
        despesas_subgroup = despesas_subgrupos[0] if despesas_subgrupos else None
        
        # Despesas fixas CNPJ (mensais)
        despesas_fixas_cnpj = [
            ("Aluguel Escritório", 3500, "11.111.111/0001-11"),
            ("Internet Empresarial", 200, "22.222.222/0001-22"),
            ("Contador", 800, "33.333.333/0001-33"),
            ("Software/Sistemas", 450, "44.444.444/0001-44"),
        ]
        
        # Despesas fixas CPF (mensais)
        despesas_fixas_cpf = [
            ("Aluguel Casa", 2200, "123.456.789-01"),
            ("Água/Luz/Gás", 350, "123.456.789-01"),
            ("Internet Residencial", 120, "123.456.789-01"),
        ]
        
        # Despesas variáveis CNPJ
        despesas_variaveis_cnpj = [
            ("Insumos para eventos", 1500),
            ("Freelancer - Garçom", 800),
            ("Freelancer - Barman", 900),
            ("Logística - Transporte", 600),
            ("Material de limpeza", 180),
            ("Combustível", 350),
        ]
        
        contas_pagar = []
        
        # Novembro e Dezembro
        for mes in [11, 12]:
            # Fixas CNPJ
            for nome, valor, cnpj in despesas_fixas_cnpj:
                account = AccountPayable(
                    client_id=client.id,
                    account_name=nome,
                    cpf_cnpj=cnpj,
                    due_date=date(2025, mes, 10),
                    value=valor,
                    paid=mes == 11,  # Novembro já pago
                    payment_date=date(2025, mes, 10) if mes == 11 else None,
                    group_id=despesas_group.id if despesas_group else None,
                    subgroup_id=despesas_subgroup.id if despesas_subgroup else None
                )
                contas_pagar.append(account)
            
            # Fixas CPF
            for nome, valor, cpf in despesas_fixas_cpf:
                account = AccountPayable(
                    client_id=client.id,
                    account_name=nome,
                    cpf_cnpj=cpf,
                    due_date=date(2025, mes, 5),
                    value=valor,
                    paid=mes == 11,
                    payment_date=date(2025, mes, 5) if mes == 11 else None,
                    group_id=despesas_group.id if despesas_group else None,
                    subgroup_id=despesas_subgroup.id if despesas_subgroup else None
                )
                contas_pagar.append(account)
        
        # Variáveis CNPJ (algumas em cada mês)
        for mes in [11, 12]:
            for nome, valor in random.sample(despesas_variaveis_cnpj, 3):
                account = AccountPayable(
                    client_id=client.id,
                    account_name=nome,
                    cpf_cnpj="99.999.999/0001-99",
                    due_date=date(2025, mes, random.randint(15, 28)),
                    value=valor + random.uniform(-100, 100),
                    paid=mes == 11,
                    payment_date=date(2025, mes, random.randint(15, 28)) if mes == 11 else None,
                    group_id=despesas_group.id if despesas_group else None,
                    subgroup_id=despesas_subgroup.id if despesas_subgroup else None
                )
                contas_pagar.append(account)
        
        db.bulk_save_objects(contas_pagar)
        db.commit()
        print(f"   ✅ {len(contas_pagar)} contas a pagar criadas")
        
        # 6. Criar transações diárias (Nubank e Itaú)
        print("\n6. Criando transações diárias (diário de gastos)...")
        
        descricoes_gastos = [
            "Café da manhã", "Almoço executivo", "Combustível", "Estacionamento",
            "Material escritório", "Correio", "Táxi", "Lanche", "Jantar cliente",
            "Pedágio", "Uber", "Papelaria", "Material limpeza", "Café",
            "Água mineral", "Delivery", "Farmácia", "Compra supermercado"
        ]
        
        transacoes = []
        
        # Nov e Dez 2025
        start_nov = date(2025, 11, 1)
        end_dez = date(2025, 12, 31)
        
        current_date = start_nov
        while current_date <= end_dez:
            # 1-3 gastos por dia
            num_gastos = random.randint(1, 3)
            
            for _ in range(num_gastos):
                banco = random.choice(["Nubank", "Itaú"])
                descricao = random.choice(descricoes_gastos)
                valor = random.uniform(10, 200)
                
                transaction = Transaction(
                    client_id=client.id,
                    date=current_date,
                    description=descricao,
                    value=valor,
                    type='saida',
                    category=random.choice(["Alimentação", "Transporte", "Material", "Outros"]),
                    bank_name=banco,
                    account=f"Conta {banco}",
                    document_type='extrato_bancario',
                    imported_from=f'Extrato {banco}',
                    group_id=despesas_group.id if despesas_group else None,
                    subgroup_id=despesas_subgroup.id if despesas_subgroup else None
                )
                transacoes.append(transaction)
            
            current_date += timedelta(days=1)
        
        # Adiciona algumas entradas (recebimentos de clientes)
        for i in range(10):
            transaction = Transaction(
                client_id=client.id,
                date=date(2025, 11, random.randint(1, 30)) if i < 5 else date(2025, 12, random.randint(1, 31)),
                description=f"Recebimento cliente - Evento {i+1}",
                value=random.uniform(5000, 15000),
                type='entrada',
                category="Receita Eventos",
                bank_name=random.choice(["Nubank", "Itaú"]),
                document_type='extrato_bancario',
                imported_from='Extrato Bancário',
                group_id=receitas_group.id if receitas_group else None,
                subgroup_id=receitas_subgroup.id if receitas_subgroup else None
            )
            transacoes.append(transaction)
        
        db.bulk_save_objects(transacoes)
        db.commit()
        print(f"   ✅ {len(transacoes)} transações criadas (diário de gastos)")
        
        # 7. Criar extratos bancários (alguns lançamentos)
        print("\n7. Criando extratos bancários...")
        
        extratos = []
        for i in range(15):
            mes = 11 if i < 8 else 12
            dia = random.randint(1, 28)
            valor = random.uniform(100, 5000)
            tipo_lanc = random.choice(['credito', 'debito'])
            
            extrato = BankStatement(
                client_id=client.id,
                bank_name=random.choice(["Nubank", "Itaú"]),
                account=f"12345-{i}",
                date=date(2025, mes, dia),
                description=f"{'Crédito' if tipo_lanc == 'credito' else 'Débito'} - Lançamento {i+1}",
                value=valor if tipo_lanc == 'credito' else -valor,
                balance=random.uniform(5000, 25000),
                imported_at=datetime.now(),
                group_id=receitas_group.id if tipo_lanc == 'credito' and receitas_group else despesas_group.id if despesas_group else None,
                subgroup_id=receitas_subgroup.id if tipo_lanc == 'credito' and receitas_subgroup else despesas_subgroup.id if despesas_subgroup else None
            )
            extratos.append(extrato)
        
        db.bulk_save_objects(extratos)
        db.commit()
        print(f"   ✅ {len(extratos)} extratos bancários criados")
        
        # 8. Criar aplicações financeiras
        print("\n8. Criando aplicações financeiras...")
        
        investimentos_group = grupos_map.get("Resultado Financeiro")
        invest_subgroups = db.query(Subgroup).join(Group).filter(
            Group.client_id == client.id,
            Subgroup.name.contains('Receita')
        ).all()
        invest_subgroup = invest_subgroups[0] if invest_subgroups else None
        
        investments = []
        for i, mes in enumerate([11, 12]):
            investment = FinancialInvestment(
                client_id=client.id,
                investment_type=random.choice(['CDB', 'LCI', 'Tesouro Direto']),
                institution=random.choice(['Banco Inter', 'Nubank', 'BTG']),
                description=f"Aplicação financeira {i+1}",
                date=date(2025, mes, 15),
                applied_value=random.uniform(10000, 50000),
                yield_value=random.uniform(100, 500),
                group_id=investimentos_group.id if investimentos_group else None,
                subgroup_id=invest_subgroup.id if invest_subgroup else None
            )
            investments.append(investment)
        
        db.bulk_save_objects(investments)
        db.commit()
        print(f"   ✅ {len(investments)} aplicações financeiras criadas")
        
        # 9. Criar faturas de cartão
        print("\n9. Criando faturas de cartão...")
        
        invoices = []
        for mes in [11, 12]:
            for i in range(8):
                invoice = CreditCardInvoice(
                    client_id=client.id,
                    transaction_date=date(2025, mes, random.randint(1, 28)),
                    description=random.choice(["Compra Material", "Restaurante", "Combustível", "Software", "Fornecedor"]),
                    value=random.uniform(50, 800),
                    establishment=f"Estabelecimento {i % 5 + 1}",
                    card_brand=random.choice(['Visa', 'Mastercard', 'Elo']),
                    category="Despesas Operacionais",
                    group_id=despesas_group.id if despesas_group else None,
                    subgroup_id=despesas_subgroup.id if despesas_subgroup else None
                )
                invoices.append(invoice)
        
        db.bulk_save_objects(invoices)
        db.commit()
        print(f"   ✅ {len(invoices)} faturas de cartão criadas")
        
        # 10. Criar extratos de máquina de cartão (recebimentos)
        print("\n10. Criando extratos de máquina de cartão...")
        
        card_statements = []
        for mes in [11, 12]:
            for i in range(5):
                gross = random.uniform(3000, 8000)
                fee = gross * 0.03  # Taxa 3%
                net = gross - fee
                
                statement = CardMachineStatement(
                    client_id=client.id,
                    date=date(2025, mes, random.randint(5, 28)),
                    description=f"Recebimento evento - cliente {i+1}",
                    gross_value=gross,
                    fee=fee,
                    net_value=net,
                    card_brand=random.choice(['Visa', 'Mastercard', 'Elo']),
                    transaction_type=random.choice(['credito', 'debito']),
                    group_id=receitas_group.id if receitas_group else None,
                    subgroup_id=receitas_subgroup.id if receitas_subgroup else None
                )
                card_statements.append(statement)
        
        db.bulk_save_objects(card_statements)
        db.commit()
        print(f"   ✅ {len(card_statements)} extratos de máquina criados")
        
        # 11. Criar movimentações de estoque
        print("\n11. Criando movimentações de estoque...")
        
        produtos = [
            "Taças de vidro",
            "Guardanapos",
            "Toalhas de mesa",
            "Velas decorativas",
            "Copos descartáveis",
            "Pratos descartáveis"
        ]
        
        inventory_movements = []
        for mes in [11, 12]:
            for produto in produtos:
                # Entrada (compra)
                entrada = Inventory(
                    client_id=client.id,
                    movement_date=date(2025, mes, random.randint(1, 10)),
                    product_name=produto,
                    description="Compra para estoque",
                    movement_type='entrada',
                    quantity=random.randint(50, 200),
                    unit_value=random.uniform(2, 20),
                    total_value=0,  # Será calculado
                    group_id=despesas_group.id if despesas_group else None,
                    subgroup_id=despesas_subgroup.id if despesas_subgroup else None
                )
                entrada.total_value = entrada.quantity * entrada.unit_value
                inventory_movements.append(entrada)
                
                # Saída (uso em evento)
                saida = Inventory(
                    client_id=client.id,
                    movement_date=date(2025, mes, random.randint(15, 28)),
                    product_name=produto,
                    description="Uso em evento",
                    movement_type='saida',
                    quantity=random.randint(20, 100),
                    unit_value=entrada.unit_value,
                    total_value=0,
                    group_id=despesas_group.id if despesas_group else None,
                    subgroup_id=despesas_subgroup.id if despesas_subgroup else None
                )
                saida.total_value = saida.quantity * saida.unit_value
                inventory_movements.append(saida)
        
        db.bulk_save_objects(inventory_movements)
        db.commit()
        print(f"   ✅ {len(inventory_movements)} movimentações de estoque criadas")
        
        # 12. Criar configuração de relatórios
        print("\n12. Criando configuração de relatórios...")
        ReportConfigService.ensure_default_config(db, client.id)
        print(f"   ✅ Configuração de relatórios criada")
        
        # Resumo
        print("\n" + "=" * 70)
        print("✅ CLIENTE EXEMPLO CRIADO COM SUCESSO!")
        print("=" * 70)
        print(f"\n📊 Cliente: {client.name}")
        print(f"   CNPJ: {client.cpf_cnpj}")
        print(f"   Período: Nov/Dez 2025 (2 meses)")
        print("\n📈 Dados criados:")
        print(f"   • Contratos/Eventos: {len(contratos)}")
        print(f"   • Contas a Receber: {len(contas_receber)}")
        print(f"   • Contas a Pagar: {len(contas_pagar)}")
        print(f"   • Transações Diárias: {len(transacoes)}")
        print(f"   • Extratos Bancários: {len(extratos)}")
        print(f"   • Aplicações: {len(investments)}")
        print(f"   • Faturas Cartão: {len(invoices)}")
        print(f"   • Máquina Cartão: {len(card_statements)}")
        print(f"   • Estoque: {len(inventory_movements)}")
        
        # Totais financeiros
        total_receitas_contratos = sum(c["valor"] for c in contratos_data)
        total_despesas = sum(t.value for t in transacoes if t.type == 'saida')
        total_entradas = sum(t.value for t in transacoes if t.type == 'entrada')
        
        print(f"\n💰 Resumo Financeiro:")
        print(f"   • Receita Contratos: R$ {total_receitas_contratos:,.2f}")
        print(f"   • Entradas (diário): R$ {total_entradas:,.2f}")
        print(f"   • Despesas (diário): R$ {total_despesas:,.2f}")
        print(f"   • Saldo Estimado: R$ {(total_receitas_contratos + total_entradas - total_despesas):,.2f}")
        
        print("\n✅ Sistema pronto para validação!")
        print("   Acesse: streamlit run app.py")
        
        return client.id
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERRO ao criar cliente exemplo: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


def main():
    """
    Função principal
    """
    print("\n" + "=" * 70)
    print("🎨 SCRIPT DE CRIAÇÃO DE CLIENTE EXEMPLO")
    print("=" * 70)
    
    # Inicializa banco de dados
    print("\nInicializando banco de dados...")
    init_db()
    print("✅ Banco de dados inicializado")
    
    # Cria cliente exemplo
    client_id = create_example_client()
    
    print("\n" + "=" * 70)
    print("✅ SCRIPT CONCLUÍDO COM SUCESSO!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit(main())

