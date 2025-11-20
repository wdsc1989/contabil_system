"""
Serviço para garantir o cadastro de grupos e subgrupos padronizados por cliente
"""
from typing import List, Dict
from sqlalchemy.orm import Session

from models.group import Group, Subgroup


class GroupTemplateService:
    """
    Mantém templates padronizados de grupos/subgrupos (DRE, DFC, Sazonalidade)
    e garante que cada cliente tenha essa estrutura mínima.
    """

    # Estruturas baseadas nas sugestões do requisito
    _DRE_TEMPLATE: List[Dict] = [
        {
            "name": "Receitas Operacionais",
            "description": "Faturamento principal da operação",
            "subgroups": [
                {"name": "Vendas de Produtos", "description": "Receitas com mercadorias"},
                {"name": "Prestação de Serviços", "description": "Receitas com serviços"},
                {"name": "Outras Receitas Operacionais", "description": "Receitas diversas da operação"},
            ],
        },
        {
            "name": "Deducoes da Receita",
            "description": "Descontos e impostos sobre receita",
            "subgroups": [
                {"name": "Impostos sobre Vendas", "description": "ISS, ICMS, PIS/COFINS"},
                {"name": "Devolucoes e Descontos", "description": "Abatimentos concedidos"},
            ],
        },
        {
            "name": "Custos Operacionais",
            "description": "Custos diretamente ligados à entrega",
            "subgroups": [
                {"name": "Custo de Produtos Vendidos", "description": "Matéria-prima, mercadorias"},
                {"name": "Custo de Servicos Prestados", "description": "Equipe técnica, insumos"},
                {"name": "Logistica e Entregas", "description": "Fretes, armazenagem"},
            ],
        },
        {
            "name": "Despesas Operacionais",
            "description": "Despesas administrativas e comerciais",
            "subgroups": [
                {"name": "Administrativas", "description": "Estrutura corporativa"},
                {"name": "Comerciais e Marketing", "description": "Vendas, publicidade"},
                {"name": "Pessoal e Beneficios", "description": "Folha administrativa"},
                {"name": "Tecnologia e Sistemas", "description": "Softwares, hardware"},
            ],
        },
        {
            "name": "Resultado Financeiro",
            "description": "Receitas e despesas financeiras",
            "subgroups": [
                {"name": "Receitas Financeiras", "description": "Rendimentos, juros ativos"},
                {"name": "Despesas Financeiras", "description": "Juros, tarifas bancarias"},
            ],
        },
        {
            "name": "Resultado Antes dos Impostos",
            "description": "Resultado operacional antes dos tributos",
            "subgroups": [
                {"name": "Lucro Operacional", "description": "Lucro antes do imposto"},
            ],
        },
        {
            "name": "Impostos sobre o Lucro",
            "description": "Tributos sobre resultado",
            "subgroups": [
                {"name": "IR e CSLL", "description": "Imposto de renda, CSLL"},
                {"name": "Outros Impostos sobre Lucro", "description": "Tributos adicionais"},
            ],
        },
        {
            "name": "Lucro Liquido",
            "description": "Resultado final do periodo",
            "subgroups": [
                {"name": "Resultado do Periodo", "description": "Lucro/Prejuizo liquido"},
            ],
        },
    ]

    _DFC_TEMPLATE: List[Dict] = [
        {
            "name": "Atividades Operacionais",
            "description": "Fluxos operacionais de caixa",
            "subgroups": [
                {"name": "Entradas Operacionais", "description": "Clientes, recebimentos"},
                {"name": "Saidas Operacionais", "description": "Fornecedores, folha"},
            ],
        },
        {
            "name": "Atividades de Investimento",
            "description": "Aplicacoes e investimentos",
            "subgroups": [
                {"name": "Aquisições/Investimentos", "description": "Compras de ativos"},
                {"name": "Resgates/Desinvestimentos", "description": "Venda de ativos"},
            ],
        },
        {
            "name": "Atividades de Financiamento",
            "description": "Capital de terceiros/proprio",
            "subgroups": [
                {"name": "Captações", "description": "Emprestimos, aportes"},
                {"name": "Amortizacoes", "description": "Pagamentos de financiamentos"},
            ],
        },
        {
            "name": "Variacao de Caixa",
            "description": "Resumo das variacoes de caixa",
            "subgroups": [
                {"name": "Aumento de Caixa", "description": "Saldo positivo"},
                {"name": "Reducao de Caixa", "description": "Saldo negativo"},
            ],
        },
        {
            "name": "Saldo Final de Caixa",
            "description": "Consolidado do periodo",
            "subgroups": [
                {"name": "Saldo Final", "description": "Saldo contabilizado"},
            ],
        },
    ]

    _SAZ_TEMPLATE: List[Dict] = [
        {
            "name": "Receitas por Periodo",
            "description": "Receitas agrupadas por sazonalidade",
            "subgroups": [
                {"name": "Picos de Receita", "description": "Meses com alta performance"},
                {"name": "Vales de Receita", "description": "Meses com baixa performance"},
            ],
        },
        {
            "name": "Despesas por Periodo",
            "description": "Despesas agrupadas por sazonalidade",
            "subgroups": [
                {"name": "Picos de Despesa", "description": "Meses com custos elevados"},
                {"name": "Vales de Despesa", "description": "Meses com custos reduzidos"},
            ],
        },
        {
            "name": "Fluxos Financeiros Sazonais",
            "description": "Fluxos de caixa por periodo",
            "subgroups": [
                {"name": "Meses Positivos", "description": "Fluxos superavitarios"},
                {"name": "Meses Negativos", "description": "Fluxos deficitarios"},
            ],
        },
    ]

    # Template específico para empresa de eventos (CPF/CNPJ, Fixas/Variáveis)
    _EVENT_BUSINESS_TEMPLATE: List[Dict] = [
        {
            "name": "Despesas Pessoais (CPF)",
            "description": "Despesas pessoa física do proprietário",
            "subgroups": [
                {"name": "Moradia - Aluguel", "description": "Aluguel residencial"},
                {"name": "Moradia - Contas", "description": "Água, luz, gás residencial"},
                {"name": "Comunicação Pessoal", "description": "Internet, telefone PF"},
                {"name": "Transporte Pessoal", "description": "Veículos, IPVA, seguro"},
                {"name": "Patrimônio", "description": "Terrenos, IPTU, taxas"},
                {"name": "Cartões PF", "description": "Cartões de crédito pessoais"},
                {"name": "Alimentação Pessoal", "description": "Gastos com alimentação PF"},
                {"name": "Saúde e Bem-estar", "description": "Plano de saúde, farmácia"},
                {"name": "Educação", "description": "Cursos, livros"},
                {"name": "Lazer", "description": "Entretenimento pessoal"},
                {"name": "Outros Pessoais", "description": "Despesas diversas PF"},
            ],
        },
        {
            "name": "Despesas Fixas (CNPJ)",
            "description": "Despesas empresariais recorrentes",
            "subgroups": [
                {"name": "Aluguel Comercial", "description": "Escritório, espaço de eventos"},
                {"name": "Internet Empresarial", "description": "Conexão do negócio"},
                {"name": "Contabilidade", "description": "Honorários contador"},
                {"name": "Sistemas e Software", "description": "Licenças, assinaturas"},
                {"name": "Seguros Empresariais", "description": "Seguro do espaço, equipamentos"},
                {"name": "Manutenção Predial", "description": "Limpeza, reparos"},
            ],
        },
        {
            "name": "Despesas Variáveis (CNPJ)",
            "description": "Despesas empresariais por demanda",
            "subgroups": [
                {"name": "Insumos para Eventos", "description": "Café, bebidas, descartáveis"},
                {"name": "Freelancers", "description": "Garçons, barmen, auxiliares"},
                {"name": "Logística", "description": "Transporte, fretes, combustível"},
                {"name": "Material de Consumo", "description": "Limpeza, escritório"},
                {"name": "Marketing e Publicidade", "description": "Anúncios, materiais promocionais"},
                {"name": "Degustações", "description": "Provas para clientes"},
                {"name": "Manutenção Equipamentos", "description": "Reparos pontuais"},
            ],
        },
        {
            "name": "Impostos e Tributos (CNPJ)",
            "description": "Obrigações fiscais",
            "subgroups": [
                {"name": "DAS/Simples Nacional", "description": "Imposto mensal MEI/Simples"},
                {"name": "IR Pessoa Jurídica", "description": "Imposto de renda PJ"},
                {"name": "INSS/FGTS", "description": "Contribuições sociais"},
                {"name": "Outros Impostos", "description": "Taxas e tributos diversos"},
            ],
        },
        {
            "name": "Despesas Financeiras",
            "description": "Custos com bancos e financiamentos",
            "subgroups": [
                {"name": "Tarifas Bancárias", "description": "Manutenção conta, TED, DOC"},
                {"name": "Juros de Empréstimos", "description": "Financiamentos ativos"},
                {"name": "Cartões PJ - Juros", "description": "Encargos cartões empresariais"},
                {"name": "Multas e Juros Diversos", "description": "Atrasos, penalidades"},
            ],
        },
        {
            "name": "Receitas de Eventos",
            "description": "Faturamento principal",
            "subgroups": [
                {"name": "Casamentos", "description": "Eventos de casamento"},
                {"name": "Formaturas", "description": "Eventos de formatura"},
                {"name": "Aniversários", "description": "Festas de aniversário"},
                {"name": "Confraternizações", "description": "Eventos corporativos"},
                {"name": "Outros Eventos", "description": "Eventos diversos"},
            ],
        },
    ]

    _ALL_TEMPLATES: List[Dict] = _DRE_TEMPLATE + _DFC_TEMPLATE + _SAZ_TEMPLATE + _EVENT_BUSINESS_TEMPLATE

    @classmethod
    def ensure_default_groups(
        cls,
        db: Session,
        client_id: int,
        commit: bool = True,
    ) -> Dict[str, int]:
        """
        Garante que o cliente possua todos os grupos/subgrupos padrao.
        Retorna o numero de grupos/subgrupos criados.
        """
        created_groups = 0
        created_subgroups = 0

        existing_groups = {
            g.name: g
            for g in db.query(Group)
            .filter(Group.client_id == client_id)
            .all()
        }

        for template in cls._ALL_TEMPLATES:
            group = existing_groups.get(template["name"])
            if not group:
                group = Group(
                    client_id=client_id,
                    name=template["name"],
                    description=template.get("description"),
                )
                db.add(group)
                db.flush()  # precisamos do ID para subgrupos
                existing_groups[group.name] = group
                created_groups += 1

            existing_sub_names = {sg.name for sg in group.subgroups}
            for sub_template in template.get("subgroups", []):
                if sub_template["name"] in existing_sub_names:
                    continue
                subgroup = Subgroup(
                    group_id=group.id,
                    name=sub_template["name"],
                    description=sub_template.get("description"),
                )
                db.add(subgroup)
                created_subgroups += 1

        if commit:
            db.commit()
        else:
            db.flush()

        return {
            "groups_created": created_groups,
            "subgroups_created": created_subgroups,
        }

