"""Script para criar arquivo Excel de contratos"""
import pandas as pd
import os

output_dir = os.path.join(os.path.dirname(__file__), 'sample_files')
os.makedirs(output_dir, exist_ok=True)

data = [
    {'Data Início': '2024-01-10', 'Data Evento': '2024-02-15', 'Nome Contratante': 'João e Maria Silva', 'Valor Serviço': 5000.00, 'Valor Deslocamento': 200.00, 'Tipo Evento': 'Casamento', 'Serviço Vendido': 'Decoração completa', 'Número Convidados': 150, 'Status': 'Confirmado'},
    {'Data Início': '2024-01-12', 'Data Evento': '2024-03-20', 'Nome Contratante': 'Pedro Santos', 'Valor Serviço': 3000.00, 'Valor Deslocamento': 150.00, 'Tipo Evento': 'Aniversário', 'Serviço Vendido': 'Decoração e buffet', 'Número Convidados': 80, 'Status': 'Confirmado'},
    {'Data Início': '2024-01-15', 'Data Evento': '2024-04-10', 'Nome Contratante': 'Ana Costa', 'Valor Serviço': 4500.00, 'Valor Deslocamento': 180.00, 'Tipo Evento': 'Casamento', 'Serviço Vendido': 'Decoração e flores', 'Número Convidados': 120, 'Status': 'Pendente'},
    {'Data Início': '2024-01-18', 'Data Evento': '2024-05-05', 'Nome Contratante': 'Carlos Oliveira', 'Valor Serviço': 2500.00, 'Valor Deslocamento': 100.00, 'Tipo Evento': 'Formatura', 'Serviço Vendido': 'Decoração temática', 'Número Convidados': 60, 'Status': 'Confirmado'},
    {'Data Início': '2024-01-20', 'Data Evento': '2024-06-15', 'Nome Contratante': 'Mariana Souza', 'Valor Serviço': 6000.00, 'Valor Deslocamento': 250.00, 'Tipo Evento': 'Casamento', 'Serviço Vendido': 'Decoração premium', 'Número Convidados': 200, 'Status': 'Confirmado'}
]

df = pd.DataFrame(data)
df.to_excel(os.path.join(output_dir, 'contracts.xlsx'), index=False)
print("Arquivo contracts.xlsx criado com sucesso!")



