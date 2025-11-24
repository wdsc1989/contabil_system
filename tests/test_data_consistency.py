"""
Script de teste para verificar consistência dos dados e criar dados fictícios
para todos os tipos de dados e importações
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
from sqlalchemy import func
from models.client import Client
from models.user import User
from models.group import Group, Subgroup
from models.transaction import Transaction, BankStatement
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable
from models.financial_investment import FinancialInvestment
from models.credit_card import CreditCardInvoice
from models.card_machine import CardMachineStatement
from models.inventory import Inventory
from models.client_report_config import ClientReportConfig
from services.report_config_service import ReportConfigService
from services.group_template_service import GroupTemplateService
from services.report_service import ReportService


TEST_CLIENT_NAME = "Cliente Ficticio QA"


def reset_client_data(db, client_id: int):
    """
    Remove todos os dados financeiros associados ao cliente fictício
    para garantir cenário determinístico de testes.
    """
    models_to_clear = [
        Transaction,
        BankStatement,
        Contract,
        AccountPayable,
        AccountReceivable,
        FinancialInvestment,
        CreditCardInvoice,
        CardMachineStatement,
        Inventory,
    ]
    for model in models_to_clear:
        db.query(model).filter(model.client_id == client_id).delete()
    db.commit()


def create_test_data():
    """
    Cria dados fictícios para todos os tipos de dados
    """
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("CRIANDO DADOS FICTÍCIOS PARA TESTES")
        print("=" * 60)
        
        # 1. Criar ou obter cliente de teste
        print("\n1. Criando cliente de teste...")
        client = db.query(Client).filter(Client.name == TEST_CLIENT_NAME).first()
        if not client:
            # Tenta criar com CPF/CNPJ único
            cpf_cnpj = f"{random.randint(10000000, 99999999)}/0001-{random.randint(10, 99)}"
            # Verifica se já existe
            while db.query(Client).filter(Client.cpf_cnpj == cpf_cnpj).first():
                cpf_cnpj = f"{random.randint(10000000, 99999999)}/0001-{random.randint(10, 99)}"
            
            client = Client(
                name=TEST_CLIENT_NAME,
                cpf_cnpj=cpf_cnpj,
                tipo_empresa="MEI",
                active=True
            )
            db.add(client)
            db.commit()
            db.refresh(client)
            print(f"   ✅ Cliente criado: {client.name} (ID: {client.id}, CPF/CNPJ: {client.cpf_cnpj})")
        else:
            print(f"   ✅ Cliente já existe: {client.name} (ID: {client.id}, CPF/CNPJ: {client.cpf_cnpj})")

        reset_client_data(db, client.id)
        GroupTemplateService.ensure_default_groups(db, client.id)
        
        # 2. Criar grupos e subgrupos
        print("\n2. Criando grupos e subgrupos...")
        groups_data = [
            ("Receitas", [
                "Vendas de Produtos",
                "Prestação de Serviços",
                "Receitas Financeiras"
            ]),
            ("Despesas", [
                "Fornecedores",
                "Salários e Encargos",
                "Despesas Administrativas",
                "Impostos e Taxas"
            ]),
            ("Investimentos", [
                "Aplicações Financeiras",
                "Resgates"
            ])
        ]
        
        groups = {}
        for group_name, subgroups in groups_data:
            group = db.query(Group).filter(
                Group.name == group_name,
                Group.client_id == client.id
            ).first()
            
            if not group:
                group = Group(
                    name=group_name,
                    client_id=client.id,
                    description=f"Grupo {group_name} para testes"
                )
                db.add(group)
                db.commit()
                db.refresh(group)
                print(f"   ✅ Grupo criado: {group.name} (ID: {group.id})")
            else:
                print(f"   ✅ Grupo já existe: {group.name} (ID: {group.id})")
            
            groups[group_name] = group
            
            # Criar subgrupos
            for subgroup_name in subgroups:
                subgroup = db.query(Subgroup).filter(
                    Subgroup.name == subgroup_name,
                    Subgroup.group_id == group.id
                ).first()
                
                if not subgroup:
                    subgroup = Subgroup(
                        name=subgroup_name,
                        group_id=group.id,
                        description=f"Subgrupo {subgroup_name} para testes"
                    )
                    db.add(subgroup)
                    db.commit()
                    print(f"      ✅ Subgrupo criado: {subgroup.name} (ID: {subgroup.id})")
        
        # 3. Criar Transações
        print("\n3. Criando transações...")
        receitas_group = groups["Receitas"]
        despesas_group = groups["Despesas"]
        
        receitas_subgroup = db.query(Subgroup).filter(
            Subgroup.group_id == receitas_group.id
        ).first()
        
        despesas_subgroup = db.query(Subgroup).filter(
            Subgroup.group_id == despesas_group.id
        ).first()
        
        transactions = []
        for i in range(20):
            is_entrada = i % 3 != 0  # 2/3 são entradas
            transaction = Transaction(
                client_id=client.id,
                date=date.today() - timedelta(days=random.randint(0, 90)),
                description=f"Transação teste {i+1} - {'Entrada' if is_entrada else 'Saída'}",
                value=random.uniform(100, 5000),
                type='entrada' if is_entrada else 'saida',
                category=f"Categoria {i % 5 + 1}",
                group_id=receitas_group.id if is_entrada else despesas_group.id,
                subgroup_id=receitas_subgroup.id if is_entrada else despesas_subgroup.id
            )
            transactions.append(transaction)
        
        db.bulk_save_objects(transactions)
        db.commit()
        print(f"   ✅ {len(transactions)} transações criadas")
        
        # 4. Criar Extratos Bancários
        print("\n4. Criando extratos bancários...")
        bank_statements = []
        for i in range(15):
            bank_statement = BankStatement(
                client_id=client.id,
                bank_name=f"Banco Teste {i % 3 + 1}",
                account=f"12345-{i}",
                date=date.today() - timedelta(days=random.randint(0, 60)),
                description=f"Extrato bancário teste {i+1}",
                value=random.uniform(50, 3000),
                balance=random.uniform(1000, 10000),
                imported_at=datetime.now() if i % 2 == 0 else datetime(2000, 1, 1),  # Alguns importados, outros manuais (usa data antiga)
                group_id=receitas_group.id if i % 2 == 0 else despesas_group.id,
                subgroup_id=receitas_subgroup.id if i % 2 == 0 else despesas_subgroup.id
            )
            bank_statements.append(bank_statement)
        
        db.bulk_save_objects(bank_statements)
        db.commit()
        print(f"   ✅ {len(bank_statements)} extratos bancários criados")
        
        # 5. Criar Contratos
        print("\n5. Criando contratos...")
        contracts = []
        for i in range(10):
            event_date = date.today() - timedelta(days=random.randint(0, 120))
            contract = Contract(
                client_id=client.id,
                contractor_name=f"Cliente Contratante {i+1}",
                contract_start=event_date - timedelta(days=30),
                event_date=event_date,
                service_value=random.uniform(1000, 10000),
                displacement_value=random.uniform(50, 500),
                status=random.choice(['pendente', 'em_andamento', 'concluido']),
                group_id=receitas_group.id,
                subgroup_id=receitas_subgroup.id
            )
            contracts.append(contract)
        
        db.bulk_save_objects(contracts)
        db.commit()
        print(f"   ✅ {len(contracts)} contratos criados")
        
        # 6. Criar Contas a Pagar
        print("\n6. Criando contas a pagar...")
        accounts_payable = []
        for i in range(12):
            due_date = date.today() + timedelta(days=random.randint(-30, 60))
            is_paid = due_date < date.today() and random.choice([True, False])
            account = AccountPayable(
                client_id=client.id,
                account_name=f"Fornecedor Teste {i+1}",
                value=random.uniform(200, 2000),
                due_date=due_date,
                paid=is_paid,
                payment_date=due_date - timedelta(days=random.randint(0, 5)) if is_paid else None,
                group_id=despesas_group.id,
                subgroup_id=despesas_subgroup.id
            )
            accounts_payable.append(account)
        
        db.bulk_save_objects(accounts_payable)
        db.commit()
        print(f"   ✅ {len(accounts_payable)} contas a pagar criadas")
        
        # 7. Criar Contas a Receber
        print("\n7. Criando contas a receber...")
        accounts_receivable = []
        for i in range(10):
            due_date = date.today() + timedelta(days=random.randint(-60, 90))
            is_received = due_date < date.today() and random.choice([True, False])
            account = AccountReceivable(
                client_id=client.id,
                account_name=f"Cliente Teste {i+1}",
                value=random.uniform(500, 5000),
                due_date=due_date,
                receipt_date=due_date if is_received else None,
                received=is_received,
                group_id=receitas_group.id,
                subgroup_id=receitas_subgroup.id
            )
            accounts_receivable.append(account)
        
        db.bulk_save_objects(accounts_receivable)
        db.commit()
        print(f"   ✅ {len(accounts_receivable)} contas a receber criadas")
        
        # 8. Criar Aplicações Financeiras
        print("\n8. Criando aplicações financeiras...")
        investments_group = groups["Investimentos"]
        investment_subgroup = db.query(Subgroup).filter(
            Subgroup.group_id == investments_group.id
        ).first()
        
        investments = []
        for i in range(8):
            investment = FinancialInvestment(
                client_id=client.id,
                investment_type=random.choice(['CDB', 'LCI', 'LCA', 'Tesouro Direto', 'Poupança']),
                institution=f"Instituição Financeira {i % 3 + 1}",
                description=f"Aplicação financeira teste {i+1}",
                date=date.today() - timedelta(days=random.randint(0, 180)),
                applied_value=random.uniform(1000, 50000),
                redeemed_value=random.uniform(0, 30000) if i % 3 == 0 else None,
                yield_value=random.uniform(50, 2000),
                group_id=investments_group.id,
                subgroup_id=investment_subgroup.id
            )
            investments.append(investment)
        
        db.bulk_save_objects(investments)
        db.commit()
        print(f"   ✅ {len(investments)} aplicações financeiras criadas")
        
        # 9. Criar Faturas de Cartão
        print("\n9. Criando faturas de cartão...")
        invoices = []
        for i in range(15):
            total_installments = random.choice([1, 1, 1, 2, 3, 4, 5, 6])  # Maioria sem parcelas
            invoice = CreditCardInvoice(
                client_id=client.id,
                transaction_date=date.today() - timedelta(days=random.randint(0, 90)),
                description=f"Compra no cartão teste {i+1}",
                value=random.uniform(50, 2000),
                establishment=f"Estabelecimento {i % 5 + 1}",
                card_brand=random.choice(['Visa', 'Mastercard', 'Elo', 'Amex']),
                category=f"Categoria {i % 4 + 1}",
                installment_number=1 if total_installments == 1 else random.randint(1, total_installments),
                total_installments=total_installments if total_installments > 1 else None,
                group_id=despesas_group.id,
                subgroup_id=despesas_subgroup.id
            )
            invoices.append(invoice)
        
        db.bulk_save_objects(invoices)
        db.commit()
        print(f"   ✅ {len(invoices)} faturas de cartão criadas")
        
        # 10. Criar Extratos de Máquina de Cartão
        print("\n10. Criando extratos de máquina de cartão...")
        card_machine_statements = []
        for i in range(12):
            gross_value = random.uniform(500, 10000)
            fee = gross_value * random.uniform(0.02, 0.05)  # Taxa de 2% a 5%
            net_value = gross_value - fee
            
            statement = CardMachineStatement(
                client_id=client.id,
                date=date.today() - timedelta(days=random.randint(0, 60)),
                description=f"Venda na máquina teste {i+1}",
                gross_value=gross_value,
                fee=fee,
                net_value=net_value,
                card_brand=random.choice(['Visa', 'Mastercard', 'Elo']),
                transaction_type=random.choice(['credito', 'debito']),
                group_id=receitas_group.id,
                subgroup_id=receitas_subgroup.id
            )
            card_machine_statements.append(statement)
        
        db.bulk_save_objects(card_machine_statements)
        db.commit()
        print(f"   ✅ {len(card_machine_statements)} extratos de máquina de cartão criados")
        
        # 11. Criar Movimentações de Estoque
        print("\n11. Criando movimentações de estoque...")
        inventory_movements = []
        for i in range(20):
            movement_type = random.choice(['entrada', 'saida'])
            quantity = random.randint(1, 100)
            unit_value = random.uniform(10, 500)
            total_value = quantity * unit_value
            
            movement = Inventory(
                client_id=client.id,
                movement_date=date.today() - timedelta(days=random.randint(0, 90)),
                product_name=f"Produto Teste {i % 10 + 1}",
                description=f"Movimentação de estoque teste {i+1}",
                movement_type=movement_type,
                quantity=quantity,
                unit_value=unit_value,
                total_value=total_value,
                group_id=despesas_group.id if movement_type == 'entrada' else receitas_group.id,
                subgroup_id=despesas_subgroup.id if movement_type == 'entrada' else receitas_subgroup.id
            )
            inventory_movements.append(movement)
        
        db.bulk_save_objects(inventory_movements)
        db.commit()
        print(f"   ✅ {len(inventory_movements)} movimentações de estoque criadas")
        
        # 12. Criar configuração de relatórios
        print("\n12. Criando configuração de relatórios...")
        ReportConfigService.ensure_default_config(db, client.id)
        print(f"   ✅ Configuração de relatórios criada para cliente {client.id}")
        
        print("\n" + "=" * 60)
        print("✅ DADOS FICTÍCIOS CRIADOS COM SUCESSO!")
        print("=" * 60)
        
        return client.id
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERRO ao criar dados: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


def check_data_consistency():
    """
    Verifica a consistência dos dados no banco
    """
    db = SessionLocal()
    
    try:
        print("\n" + "=" * 60)
        print("VERIFICANDO CONSISTÊNCIA DOS DADOS")
        print("=" * 60)
        
        errors = []
        warnings = []
        
        # 1. Verificar Foreign Keys - client_id
        print("\n1. Verificando foreign keys (client_id)...")
        models_to_check = [
            (Transaction, "Transações"),
            (BankStatement, "Extratos Bancários"),
            (Contract, "Contratos"),
            (AccountPayable, "Contas a Pagar"),
            (AccountReceivable, "Contas a Receber"),
            (FinancialInvestment, "Aplicações Financeiras"),
            (CreditCardInvoice, "Faturas de Cartão"),
            (CardMachineStatement, "Extratos de Máquina de Cartão"),
            (Inventory, "Estoque")
        ]
        
        for model, name in models_to_check:
            invalid = db.query(model).filter(
                ~model.client_id.in_(db.query(Client.id))
            ).all()
            
            if invalid:
                errors.append(f"   ❌ {name}: {len(invalid)} registros com client_id inválido")
            else:
                print(f"   ✅ {name}: Todos os client_id são válidos")
        
        # 2. Verificar Foreign Keys - group_id
        print("\n2. Verificando foreign keys (group_id)...")
        for model, name in models_to_check:
            if hasattr(model, 'group_id'):
                invalid = db.query(model).filter(
                    model.group_id.isnot(None),
                    ~model.group_id.in_(db.query(Group.id))
                ).all()
                
                if invalid:
                    errors.append(f"   ❌ {name}: {len(invalid)} registros com group_id inválido")
                else:
                    print(f"   ✅ {name}: Todos os group_id são válidos")
        
        # 3. Verificar Foreign Keys - subgroup_id
        print("\n3. Verificando foreign keys (subgroup_id)...")
        for model, name in models_to_check:
            if hasattr(model, 'subgroup_id'):
                invalid = db.query(model).filter(
                    model.subgroup_id.isnot(None),
                    ~model.subgroup_id.in_(db.query(Subgroup.id))
                ).all()
                
                if invalid:
                    errors.append(f"   ❌ {name}: {len(invalid)} registros com subgroup_id inválido")
                else:
                    print(f"   ✅ {name}: Todos os subgroup_id são válidos")
        
        # 4. Verificar relacionamento subgroup -> group
        print("\n4. Verificando relacionamento subgroup -> group...")
        invalid_subgroups = db.query(Subgroup).filter(
            ~Subgroup.group_id.in_(db.query(Group.id))
        ).all()
        
        if invalid_subgroups:
            errors.append(f"   ❌ Subgrupos: {len(invalid_subgroups)} subgrupos com group_id inválido")
        else:
            print(f"   ✅ Subgrupos: Todos os subgrupos têm group_id válido")
        
        # 5. Verificar valores negativos onde não deveriam ter
        print("\n5. Verificando valores negativos...")
        negative_transactions = db.query(Transaction).filter(Transaction.value < 0).count()
        if negative_transactions > 0:
            warnings.append(f"   ⚠️ Transações: {negative_transactions} transações com valor negativo")
        else:
            print(f"   ✅ Transações: Nenhum valor negativo")
        
        # 6. Verificar datas inconsistentes
        print("\n6. Verificando datas inconsistentes...")
        future_bank_statements = db.query(BankStatement).filter(
            BankStatement.date > date.today()
        ).count()
        if future_bank_statements > 0:
            warnings.append(f"   ⚠️ Extratos Bancários: {future_bank_statements} com data futura")
        else:
            print(f"   ✅ Extratos Bancários: Nenhuma data futura")
        
        # 7. Verificar contas a pagar/receber
        print("\n7. Verificando contas a pagar/receber...")
        paid_without_date = db.query(AccountPayable).filter(
            AccountPayable.paid == True,
            AccountPayable.payment_date.is_(None)
        ).count()
        if paid_without_date > 0:
            warnings.append(f"   ⚠️ Contas a Pagar: {paid_without_date} marcadas como pagas sem data de pagamento")
        
        received_without_date = db.query(AccountReceivable).filter(
            AccountReceivable.received == True,
            AccountReceivable.receipt_date.is_(None)
        ).count()
        if received_without_date > 0:
            warnings.append(f"   ⚠️ Contas a Receber: {received_without_date} marcadas como recebidas sem data")
        
        # 8. Verificar parcelas de cartão
        print("\n8. Verificando parcelas de cartão...")
        invalid_installments = db.query(CreditCardInvoice).filter(
            CreditCardInvoice.installment_number > CreditCardInvoice.total_installments
        ).count()
        if invalid_installments > 0:
            errors.append(f"   ❌ Faturas de Cartão: {invalid_installments} com número de parcela maior que total")
        
        # 9. Verificar máquina de cartão
        print("\n9. Verificando máquina de cartão...")
        invalid_fees = db.query(CardMachineStatement).filter(
            CardMachineStatement.net_value > CardMachineStatement.gross_value
        ).count()
        if invalid_fees > 0:
            errors.append(f"   ❌ Máquina de Cartão: {invalid_fees} com valor líquido maior que bruto")
        
        # 10. Verificar configurações de relatórios
        print("\n10. Verificando configurações de relatórios...")
        clients_without_config = []
        all_clients = db.query(Client).filter(Client.active == True).all()
        for client in all_clients:
            configs = db.query(ClientReportConfig).filter(
                ClientReportConfig.client_id == client.id
            ).count()
            if configs < 3:  # Deve ter pelo menos 3 (DRE, DFC, Sazonalidade)
                clients_without_config.append(client.name)
        
        if clients_without_config:
            warnings.append(f"   ⚠️ Clientes sem configuração completa: {', '.join(clients_without_config)}")
        else:
            print(f"   ✅ Todos os clientes têm configuração de relatórios")
        
        # Resumo
        print("\n" + "=" * 60)
        print("RESUMO DA VERIFICAÇÃO")
        print("=" * 60)
        
        if errors:
            print(f"\n❌ ERROS ENCONTRADOS: {len(errors)}")
            for error in errors:
                print(error)
        else:
            print("\n✅ Nenhum erro encontrado!")
        
        if warnings:
            print(f"\n⚠️ AVISOS: {len(warnings)}")
            for warning in warnings:
                print(warning)
        else:
            print("\n✅ Nenhum aviso!")
        
        return len(errors) == 0
        
    except Exception as e:
        print(f"\n❌ ERRO ao verificar consistência: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def show_statistics():
    """
    Mostra estatísticas dos dados criados
    """
    db = SessionLocal()
    
    try:
        print("\n" + "=" * 60)
        print("ESTATÍSTICAS DOS DADOS")
        print("=" * 60)
        
        client = db.query(Client).filter(Client.name == TEST_CLIENT_NAME).first()
        if not client:
            print("\n⚠️ Cliente de teste não encontrado!")
            return
        
        print(f"\nCliente: {client.name} (ID: {client.id})")
        print(f"CPF/CNPJ: {client.cpf_cnpj}")
        
        stats = {
            "Transações": db.query(Transaction).filter(Transaction.client_id == client.id).count(),
            "Extratos Bancários": db.query(BankStatement).filter(BankStatement.client_id == client.id).count(),
            "Contratos": db.query(Contract).filter(Contract.client_id == client.id).count(),
            "Contas a Pagar": db.query(AccountPayable).filter(AccountPayable.client_id == client.id).count(),
            "Contas a Receber": db.query(AccountReceivable).filter(AccountReceivable.client_id == client.id).count(),
            "Aplicações Financeiras": db.query(FinancialInvestment).filter(FinancialInvestment.client_id == client.id).count(),
            "Faturas de Cartão": db.query(CreditCardInvoice).filter(CreditCardInvoice.client_id == client.id).count(),
            "Extratos de Máquina de Cartão": db.query(CardMachineStatement).filter(CardMachineStatement.client_id == client.id).count(),
            "Movimentações de Estoque": db.query(Inventory).filter(Inventory.client_id == client.id).count(),
        }
        
        print("\nQuantidade de registros por tipo:")
        for name, count in stats.items():
            print(f"  {name}: {count}")
        
        # Totais
        total_transactions = db.query(func.sum(Transaction.value)).filter(
            Transaction.client_id == client.id,
            Transaction.type == 'entrada'
        ).scalar() or 0
        
        total_expenses = db.query(func.sum(Transaction.value)).filter(
            Transaction.client_id == client.id,
            Transaction.type == 'saida'
        ).scalar() or 0
        
        print(f"\nTotal de Receitas (Transações): R$ {total_transactions:,.2f}")
        print(f"Total de Despesas (Transações): R$ {total_expenses:,.2f}")
        print(f"Saldo: R$ {total_transactions - total_expenses:,.2f}")
        
    except Exception as e:
        print(f"\n❌ ERRO ao mostrar estatísticas: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def validate_reports(client_id: int):
    """
    Executa validações automáticas nos relatórios DRE, DFC e Sazonalidade
    para garantir que todos reflitam os dados importados.
    """
    db = SessionLocal()
    try:
        today = date.today()
        start_date = today - timedelta(days=120)

        dre = ReportService.get_dre_data(db, client_id, start_date, today)
        assert dre['receitas_por_subgrupo'], "DRE sem receitas por subgrupo classificadas"
        assert dre['despesas_por_subgrupo'], "DRE sem despesas por subgrupo classificadas"

        dfc = ReportService.get_dfc_data(db, client_id, start_date, today)
        assert dfc['fluxo_mensal'], "DFC sem fluxo mensal calculado"

        sazonalidade = ReportService.get_seasonality_data(db, client_id)
        assert sazonalidade['por_ano'], "Sazonalidade sem dados consolidados"

        print("\n✅ Relatórios DRE/DFC/Sazonalidade validados com sucesso.")
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTE DE CONSISTÊNCIA DE DADOS")
    print("=" * 60)
    
    # Inicializa banco de dados
    print("\nInicializando banco de dados...")
    init_db()
    print("✅ Banco de dados inicializado")
    
    # Cria dados fictícios
    client_id = create_test_data()
    
    # Verifica consistência
    is_consistent = check_data_consistency()
    
    # Mostra estatísticas
    show_statistics()
    validate_reports(client_id)
    
    print("\n" + "=" * 60)
    if is_consistent:
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("⚠️ TESTE CONCLUÍDO COM AVISOS/ERROS")
    print("=" * 60)






