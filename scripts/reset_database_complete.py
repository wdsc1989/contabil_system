"""
Script para reset completo do banco de dados
Remove TODOS os clientes e dados financeiros, mantendo apenas usuários e configurações
ATENÇÃO: Esta operação é IRREVERSÍVEL!
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from models.client import Client
from models.transaction import Transaction, BankStatement
from models.contract import Contract
from models.account import AccountPayable, AccountReceivable, ImportMapping
from models.financial_investment import FinancialInvestment
from models.credit_card import CreditCardInvoice
from models.card_machine import CardMachineStatement
from models.inventory import Inventory
from models.group import Group, Subgroup
from models.client_report_config import ClientReportConfig
from models.user import UserClientPermission


def confirm_reset():
    """
    Solicita confirmação tripla do usuário
    """
    print("\n" + "=" * 70)
    print("⚠️  ATENÇÃO: RESET COMPLETO DO BANCO DE DADOS")
    print("=" * 70)
    print("\nEsta operação irá:")
    print("  ❌ Remover TODOS os clientes")
    print("  ❌ Remover TODOS os dados financeiros (transações, contratos, contas, etc.)")
    print("  ❌ Remover TODOS os grupos e subgrupos")
    print("  ❌ Remover TODAS as configurações de relatórios")
    print("\nSerá preservado:")
    print("  ✅ Usuários do sistema")
    print("  ✅ Configurações de IA")
    print("\n" + "=" * 70)
    
    # Primeira confirmação
    resposta1 = input("\n❓ Você tem CERTEZA que deseja continuar? (digite 'SIM' para confirmar): ")
    if resposta1.strip().upper() != 'SIM':
        print("\n✖️  Operação cancelada pelo usuário.")
        return False
    
    # Segunda confirmação
    resposta2 = input("\n❓ Esta operação é IRREVERSÍVEL. Confirma novamente? (digite 'CONFIRMAR'): ")
    if resposta2.strip().upper() != 'CONFIRMAR':
        print("\n✖️  Operação cancelada pelo usuário.")
        return False
    
    # Terceira confirmação
    resposta3 = input("\n❓ Última confirmação. Digite 'RESET COMPLETO' para prosseguir: ")
    if resposta3.strip().upper() != 'RESET COMPLETO':
        print("\n✖️  Operação cancelada pelo usuário.")
        return False
    
    return True


def reset_database():
    """
    Executa o reset completo do banco de dados
    """
    db = SessionLocal()
    
    try:
        print("\n" + "=" * 70)
        print("🔄 Iniciando reset do banco de dados...")
        print("=" * 70)
        
        # Contadores
        totals = {
            'clients': 0,
            'transactions': 0,
            'bank_statements': 0,
            'contracts': 0,
            'accounts_payable': 0,
            'accounts_receivable': 0,
            'financial_investments': 0,
            'credit_card_invoices': 0,
            'card_machine_statements': 0,
            'inventory': 0,
            'groups': 0,
            'subgroups': 0,
            'import_mappings': 0,
            'report_configs': 0,
            'user_permissions': 0
        }
        
        # 1. Remove dados financeiros (ordem importa por causa das FKs)
        print("\n1️⃣ Removendo dados financeiros...")
        
        # Import Mappings
        count = db.query(ImportMapping).delete()
        totals['import_mappings'] = count
        print(f"   ✅ {count} mapeamentos de importação removidos")
        
        # Transações
        count = db.query(Transaction).delete()
        totals['transactions'] = count
        print(f"   ✅ {count} transações removidas")
        
        # Extratos Bancários
        count = db.query(BankStatement).delete()
        totals['bank_statements'] = count
        print(f"   ✅ {count} extratos bancários removidos")
        
        # Contratos
        count = db.query(Contract).delete()
        totals['contracts'] = count
        print(f"   ✅ {count} contratos removidos")
        
        # Contas a Pagar
        count = db.query(AccountPayable).delete()
        totals['accounts_payable'] = count
        print(f"   ✅ {count} contas a pagar removidas")
        
        # Contas a Receber
        count = db.query(AccountReceivable).delete()
        totals['accounts_receivable'] = count
        print(f"   ✅ {count} contas a receber removidas")
        
        # Aplicações Financeiras
        count = db.query(FinancialInvestment).delete()
        totals['financial_investments'] = count
        print(f"   ✅ {count} aplicações financeiras removidas")
        
        # Faturas de Cartão
        count = db.query(CreditCardInvoice).delete()
        totals['credit_card_invoices'] = count
        print(f"   ✅ {count} faturas de cartão removidas")
        
        # Extratos Máquina de Cartão
        count = db.query(CardMachineStatement).delete()
        totals['card_machine_statements'] = count
        print(f"   ✅ {count} extratos de máquina removidos")
        
        # Estoque
        count = db.query(Inventory).delete()
        totals['inventory'] = count
        print(f"   ✅ {count} movimentações de estoque removidas")
        
        db.commit()
        
        # 2. Remove grupos e subgrupos
        print("\n2️⃣ Removendo grupos e subgrupos...")
        
        count = db.query(Subgroup).delete()
        totals['subgroups'] = count
        print(f"   ✅ {count} subgrupos removidos")
        
        count = db.query(Group).delete()
        totals['groups'] = count
        print(f"   ✅ {count} grupos removidos")
        
        db.commit()
        
        # 3. Remove configurações de relatórios
        print("\n3️⃣ Removendo configurações de relatórios...")
        
        count = db.query(ClientReportConfig).delete()
        totals['report_configs'] = count
        print(f"   ✅ {count} configurações de relatórios removidas")
        
        db.commit()
        
        # 4. Remove permissões de usuários
        print("\n4️⃣ Removendo permissões de usuários...")
        
        count = db.query(UserClientPermission).delete()
        totals['user_permissions'] = count
        print(f"   ✅ {count} permissões de usuários removidas")
        
        db.commit()
        
        # 5. Remove clientes
        print("\n5️⃣ Removendo clientes...")
        
        count = db.query(Client).delete()
        totals['clients'] = count
        print(f"   ✅ {count} clientes removidos")
        
        db.commit()
        
        # Resumo
        print("\n" + "=" * 70)
        print("✅ RESET COMPLETO CONCLUÍDO COM SUCESSO!")
        print("=" * 70)
        print("\n📊 Resumo das Remoções:")
        print(f"   • Clientes: {totals['clients']}")
        print(f"   • Transações: {totals['transactions']}")
        print(f"   • Extratos Bancários: {totals['bank_statements']}")
        print(f"   • Contratos: {totals['contracts']}")
        print(f"   • Contas a Pagar: {totals['accounts_payable']}")
        print(f"   • Contas a Receber: {totals['accounts_receivable']}")
        print(f"   • Aplicações Financeiras: {totals['financial_investments']}")
        print(f"   • Faturas de Cartão: {totals['credit_card_invoices']}")
        print(f"   • Extratos Máquina: {totals['card_machine_statements']}")
        print(f"   • Estoque: {totals['inventory']}")
        print(f"   • Grupos: {totals['groups']}")
        print(f"   • Subgrupos: {totals['subgroups']}")
        print(f"   • Config. Relatórios: {totals['report_configs']}")
        print(f"   • Permissões: {totals['user_permissions']}")
        print(f"   • Mapeamentos: {totals['import_mappings']}")
        
        total_removido = sum(totals.values())
        print(f"\n   📊 TOTAL GERAL: {total_removido} registros removidos")
        
        print("\n💡 Próximo passo:")
        print("   Execute: python scripts/seed_example_client.py")
        print("   Para criar o cliente exemplo com dados de 2 meses")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERRO durante o reset: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """
    Função principal
    """
    print("\n" + "=" * 70)
    print("🗑️  SCRIPT DE RESET COMPLETO DO BANCO DE DADOS")
    print("=" * 70)
    
    # Solicita confirmação
    if not confirm_reset():
        return 1
    
    # Executa reset
    success = reset_database()
    
    if success:
        print("\n" + "=" * 70)
        print("✅ BANCO DE DADOS RESETADO COM SUCESSO!")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print("❌ ERRO AO RESETAR BANCO DE DADOS")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit(main())

