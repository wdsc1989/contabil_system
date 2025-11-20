"""
Script para criar arquivos de exemplo para importação
Gera Excel e PDF com dados de teste
"""
import pandas as pd
from datetime import datetime, timedelta
import os

# Diretório de saída
output_dir = os.path.join(os.path.dirname(__file__), 'sample_files')
os.makedirs(output_dir, exist_ok=True)

print("Criando arquivos de exemplo...")
print("=" * 60)

# 1. FATURA DE CARTÃO (Excel)
print("\n📄 Criando: fatura_cartao_exemplo.xlsx")
fatura_data = {
    'Data': [
        '05/11/2025', '06/11/2025', '08/11/2025', '10/11/2025', '12/11/2025',
        '15/11/2025', '18/11/2025', '20/11/2025', '22/11/2025', '25/11/2025',
        '26/11/2025', '28/11/2025', '29/11/2025', '30/11/2025'
    ],
    'Estabelecimento': [
        'Supermercado Bom Preço', 'Posto de Gasolina', 'Restaurante Sabor',
        'Livraria Central', 'Farmácia Saúde', 'Loja de Informática',
        'Padaria Pão Quente', 'Material de Construção', 'Pet Shop Amigo',
        'Academia Fitness', 'Papelaria Escolar', 'Cafeteria Aroma',
        'Loja de Roupas', 'Mercado Orgânico'
    ],
    'Valor': [
        450.80, 250.00, 180.50, 95.00, 68.90,
        1200.00, 45.00, 680.00, 120.00, 150.00,
        85.50, 42.00, 320.00, 280.00
    ],
    'Categoria': [
        'Alimentação', 'Combustível', 'Alimentação', 'Material',
        'Saúde', 'Equipamento', 'Alimentação', 'Material',
        'Outros', 'Saúde', 'Material', 'Alimentação',
        'Vestuário', 'Alimentação'
    ]
}

df_fatura = pd.DataFrame(fatura_data)
df_fatura.to_excel(os.path.join(output_dir, 'fatura_cartao_exemplo.xlsx'), index=False)
print("✓ Criado: fatura_cartao_exemplo.xlsx")

# 2. PLANILHA DE CONTRATOS (Excel com múltiplas abas)
print("\n📄 Criando: contratos_completo_exemplo.xlsx")

# Aba 1: Contratos
contratos_data = {
    'Data Contrato': ['15/10/2025', '20/10/2025', '25/10/2025', '01/11/2025', '05/11/2025'],
    'Data Evento': ['20/12/2025', '15/01/2026', '10/11/2025', '05/12/2025', '25/11/2025'],
    'Cliente': ['João Silva', 'Maria Santos', 'Empresa Tech', 'Pedro Costa', 'Ana Paula'],
    'Tipo': ['Casamento', 'Aniversário', 'Corporativo', 'Formatura', 'Festa'],
    'Valor Serviço': [12000.00, 8500.00, 15000.00, 10500.00, 4500.00],
    'Valor Deslocamento': [500.00, 300.00, 0.00, 400.00, 200.00],
    'Convidados': [200, 150, 80, 120, 80],
    'Status': ['pendente', 'em_andamento', 'concluido', 'pendente', 'concluido']
}

# Aba 2: Resumo
resumo_data = {
    'Mês': ['Outubro', 'Novembro', 'Dezembro'],
    'Contratos': [2, 3, 1],
    'Valor Total': [20500.00, 30000.00, 12000.00],
    'Média por Contrato': [10250.00, 10000.00, 12000.00]
}

with pd.ExcelWriter(os.path.join(output_dir, 'contratos_completo_exemplo.xlsx')) as writer:
    pd.DataFrame(contratos_data).to_excel(writer, sheet_name='Contratos', index=False)
    pd.DataFrame(resumo_data).to_excel(writer, sheet_name='Resumo', index=False)

print("✓ Criado: contratos_completo_exemplo.xlsx (2 abas)")

# 3. DIÁRIO DE GASTOS (Excel)
print("\n📄 Criando: diario_gastos_exemplo.xlsx")

diario_data = {
    'Data': pd.date_range(start='2025-11-01', periods=30, freq='D').strftime('%d/%m/%Y').tolist(),
    'Descrição': [
        'Café da manhã', 'Combustível', 'Almoço', 'Material escritório', 'Lanche',
        'Jantar cliente', 'Estacionamento', 'Pedágio', 'Correio', 'Cópias',
        'Café', 'Táxi', 'Almoço', 'Material limpeza', 'Lanche',
        'Jantar', 'Uber', 'Papelaria', 'Café', 'Almoço',
        'Combustível', 'Estacionamento', 'Lanche', 'Jantar', 'Táxi',
        'Café', 'Almoço', 'Material', 'Lanche', 'Jantar'
    ],
    'Valor': [
        15.00, 80.00, 35.00, 120.00, 12.00,
        180.00, 15.00, 12.50, 25.00, 18.00,
        10.00, 45.00, 38.00, 65.00, 15.00,
        95.00, 32.00, 48.00, 12.00, 42.00,
        85.00, 18.00, 14.00, 110.00, 38.00,
        11.00, 40.00, 95.00, 16.00, 125.00
    ],
    'Categoria': [
        'Alimentação', 'Transporte', 'Alimentação', 'Material', 'Alimentação',
        'Representação', 'Transporte', 'Transporte', 'Correio', 'Material',
        'Alimentação', 'Transporte', 'Alimentação', 'Material', 'Alimentação',
        'Alimentação', 'Transporte', 'Material', 'Alimentação', 'Alimentação',
        'Transporte', 'Transporte', 'Alimentação', 'Alimentação', 'Transporte',
        'Alimentação', 'Alimentação', 'Material', 'Alimentação', 'Alimentação'
    ],
    'Forma Pagamento': [
        'Dinheiro', 'Cartão', 'Cartão', 'Cartão', 'Dinheiro',
        'Cartão', 'Dinheiro', 'Dinheiro', 'Dinheiro', 'Dinheiro',
        'Dinheiro', 'Dinheiro', 'Cartão', 'Cartão', 'Dinheiro',
        'Cartão', 'Cartão', 'Cartão', 'Dinheiro', 'Cartão',
        'Cartão', 'Dinheiro', 'Dinheiro', 'Cartão', 'Dinheiro',
        'Dinheiro', 'Cartão', 'Cartão', 'Dinheiro', 'Cartão'
    ]
}

df_diario = pd.DataFrame(diario_data)
df_diario.to_excel(os.path.join(output_dir, 'diario_gastos_exemplo.xlsx'), index=False)
print("✓ Criado: diario_gastos_exemplo.xlsx")

# 4. EXTRATO FORMATO DIFERENTE (CSV com ponto e vírgula)
print("\n📄 Criando: extrato_formato2_exemplo.csv")
extrato2_data = {
    'dt_movimento': ['01/11/2025', '02/11/2025', '03/11/2025', '05/11/2025', '06/11/2025'],
    'historico': ['DEP JOÃO SILVA', 'PIX RECEBIDO', 'TED ENVIADA', 'DEB AUTO ALUGUEL', 'RECEB SERVICO'],
    'vlr_movimento': ['2500,00', '1800,50', '-850,00', '-3000,00', '4200,00'],
    'saldo_final': ['15000,00', '16800,50', '15950,50', '12950,50', '17150,50']
}

df_extrato2 = pd.DataFrame(extrato2_data)
df_extrato2.to_csv(
    os.path.join(output_dir, 'extrato_formato2_exemplo.csv'),
    index=False,
    sep=';',
    encoding='utf-8'
)
print("✓ Criado: extrato_formato2_exemplo.csv")

print("\n" + "=" * 60)
print("✅ Todos os arquivos de exemplo foram criados!")
print("=" * 60)
print(f"\n📁 Localização: {output_dir}")
print("\nArquivos criados:")
print("  1. extrato_bancario_exemplo.csv")
print("  2. transacoes_exemplo.csv")
print("  3. contratos_exemplo.csv")
print("  4. contas_pagar_exemplo.csv")
print("  5. contas_receber_exemplo.csv")
print("  6. fatura_cartao_exemplo.xlsx")
print("  7. contratos_completo_exemplo.xlsx")
print("  8. diario_gastos_exemplo.xlsx")
print("  9. extrato_formato2_exemplo.csv")
print("\n🎉 Use estes arquivos para testar a importação!")










