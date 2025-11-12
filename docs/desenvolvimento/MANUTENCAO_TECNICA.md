# 🔧 Guia Técnico de Manutenção

## 📋 Documentação Completa para Desenvolvedores

---

## 🎯 Visão Geral Técnica

Este documento fornece informações detalhadas para manutenção, expansão e troubleshooting do sistema.

---

## 🗃️ Banco de Dados

### Conexão e Sessão

**Arquivo:** `config/database.py`

```python
# Obter sessão
from config.database import SessionLocal

db = SessionLocal()
try:
    # Operações com banco
    result = db.query(Model).all()
finally:
    db.close()  # SEMPRE feche a sessão
```

### Criar Nova Tabela

**1. Criar modelo:**
```python
# models/novo_modelo.py
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base

class NovoModelo(Base):
    __tablename__ = 'novo_modelo'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    nome = Column(String(200), nullable=False)
    valor = Column(Float)
    data = Column(Date, index=True)  # Índice para queries por data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento
    client = relationship('Client', back_populates='novo_modelo')
```

**2. Atualizar Client:**
```python
# models/client.py
# Adicione no relacionamentos:
novo_modelo = relationship('NovoModelo', back_populates='client', cascade='all, delete-orphan')
```

**3. Registrar no __init__:**
```python
# models/__init__.py
from models.novo_modelo import NovoModelo

__all__ = [
    # ... existentes ...
    'NovoModelo',
]
```

**4. Recriar banco:**
```bash
python init_db.py
```

### Migrations com Alembic (Preservar Dados)

**Inicializar Alembic (primeira vez):**
```bash
alembic init alembic
```

**Criar migration:**
```bash
# Após alterar modelos
alembic revision --autogenerate -m "Adiciona campo X"
```

**Aplicar migration:**
```bash
alembic upgrade head
```

**Reverter migration:**
```bash
alembic downgrade -1
```

---

## 🔧 Serviços

### Criar Novo Serviço

**Estrutura:**
```python
# services/novo_service.py
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from models.seu_modelo import SeuModelo

class NovoService:
    """
    Serviço para [descrição]
    """
    
    @staticmethod
    def metodo_principal(db: Session, param1, param2) -> ReturnType:
        """
        Descrição do método
        
        Args:
            db: Sessão do banco
            param1: Descrição
            param2: Descrição
        
        Returns:
            Descrição do retorno
        """
        # Implementação
        result = db.query(SeuModelo).filter(...).all()
        return result
    
    @staticmethod
    def metodo_auxiliar(data: Dict) -> Dict:
        """
        Método auxiliar
        """
        # Processamento
        return processed_data
```

**Uso:**
```python
from services.novo_service import NovoService

result = NovoService.metodo_principal(db, param1, param2)
```

---

## 📄 Páginas

### Template de Nova Página

```python
"""
Descrição da página
"""
import streamlit as st
import sys
import os
import pandas as pd
from datetime import date

# Path setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports
from config.database import SessionLocal
from services.auth_service import AuthService
from models.client import Client
from utils.ui_components import show_client_selector, show_sidebar_navigation
from utils.formatters import format_currency, format_date

# Configuração
st.set_page_config(
    page_title="Título da Página",
    page_icon="🆕",
    layout="wide"
)

# Autenticação
AuthService.init_session_state()
AuthService.require_auth()
# AuthService.require_role(['admin', 'manager'])  # Se necessário

# Sidebar
show_sidebar_navigation()

# Título
st.title("🆕 Título da Página")

# Seletor de cliente
client_id = show_client_selector()
if not client_id:
    st.warning("⚠️ Nenhum cliente disponível.")
    st.stop()

st.markdown("---")

# Conteúdo da página
db = SessionLocal()
try:
    # Seu código aqui
    
    # Exemplo de tabs
    tab1, tab2 = st.tabs(["📋 Lista", "➕ Novo"])
    
    with tab1:
        st.subheader("Lista de Itens")
        # Query e exibição
        
    with tab2:
        st.subheader("Novo Item")
        with st.form("new_item_form"):
            # Campos do formulário
            submit = st.form_submit_button("➕ Cadastrar")
            if submit:
                # Validação e salvamento
                pass

finally:
    db.close()
```

---

## 🎨 Componentes UI

### Usar Componentes Existentes

**Seletor de Cliente:**
```python
from utils.ui_components import show_client_selector

# No topo da página
client_id = show_client_selector()
if not client_id:
    st.stop()
```

**Header do Cliente:**
```python
from utils.ui_components import show_client_header

# Versão compacta
show_client_header(client_id, compact=True)

# Versão completa
show_client_header(client_id, compact=False)
```

**Cards de Métricas:**
```python
from utils.ui_components import show_stat_cards

stats = [
    {'label': 'Total', 'value': 'R$ 10.000', 'icon': '💰', 'delta': '+10%'},
    {'label': 'Pendente', 'value': 'R$ 2.000', 'icon': '⏳'},
]
show_stat_cards(stats)
```

**Caixa de Informação:**
```python
from utils.ui_components import show_info_box

show_info_box(
    title="Atenção",
    content="Mensagem importante aqui",
    box_type="warning"  # info, success, warning, error
)
```

---

## 📥 Importação de Dados

### Adicionar Novo Formato

**1. Adicionar parser:**
```python
# services/parser_service.py

@staticmethod
def parse_novo_formato(file_content: bytes) -> pd.DataFrame:
    """
    Faz parse de novo formato
    """
    try:
        # Lógica de parse
        df = ...
        return df
    except Exception as e:
        raise Exception(f"Erro ao fazer parse: {str(e)}")
```

**2. Adicionar à página de importação:**
```python
# pages/2_Importacao_Dados.py

file_type = st.radio(
    "Formato do arquivo:",
    options=['CSV', 'Excel', 'PDF', 'OFX', 'Novo'],  # Adicione aqui
    horizontal=True
)

# Adicione lógica de parse
if file_type == 'Novo':
    df = ParserService.parse_novo_formato(file_content)
```

### Adicionar Novo Tipo de Dado

**1. Definir colunas alvo:**
```python
# services/import_service.py

@staticmethod
def get_target_columns(import_type: str) -> List[str]:
    columns_map = {
        # ... existentes ...
        'novo_tipo': ['campo1', 'campo2', 'campo3', 'campo4']
    }
    return columns_map.get(import_type, [])
```

**2. Criar método de importação:**
```python
# services/import_service.py

@staticmethod
def import_novo_tipo(db: Session, client_id: int, df: pd.DataFrame) -> int:
    """
    Importa novo tipo de dado
    """
    imported_count = 0
    
    for _, row in df.iterrows():
        try:
            # Parse dos campos
            campo1 = parse_date(str(row.get('campo1', '')))
            campo2 = parse_currency(str(row.get('campo2', 0)))
            
            if not campo1 or not campo2:
                continue
            
            # Criar objeto
            obj = NovoModelo(
                client_id=client_id,
                campo1=campo1,
                campo2=campo2
            )
            
            db.add(obj)
            imported_count += 1
        
        except Exception as e:
            print(f"Erro: {e}")
            continue
    
    db.commit()
    return imported_count
```

**3. Adicionar à interface:**
```python
# pages/2_Importacao_Dados.py

import_type = st.selectbox(
    "Tipo de dado:",
    options=[..., 'novo_tipo'],
    format_func=lambda x: {
        ...,
        'novo_tipo': '🆕 Novo Tipo'
    }[x]
)

# Na importação:
elif import_type == 'novo_tipo':
    imported_count = ImportService.import_novo_tipo(db, client_id, mapped_df)
```

---

## 📊 Dashboards

### Adicionar Nova Análise

**1. Criar método no ReportService:**
```python
# services/report_service.py

@staticmethod
def get_nova_analise(db: Session, client_id: int, 
                     start_date: date, end_date: date) -> Dict[str, Any]:
    """
    Gera nova análise
    """
    # Query de dados
    dados = db.query(Transaction).filter(
        Transaction.client_id == client_id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()
    
    # Processamento
    resultado = {
        'total': sum(d.value for d in dados),
        'media': sum(d.value for d in dados) / len(dados) if dados else 0,
        'detalhes': [...]
    }
    
    return resultado
```

**2. Usar na página:**
```python
# pages/6_DRE.py ou nova página

analise = ReportService.get_nova_analise(db, client_id, start_date, end_date)

st.subheader("🆕 Nova Análise")

col1, col2 = st.columns(2)
with col1:
    st.metric("Total", format_currency(analise['total']))
with col2:
    st.metric("Média", format_currency(analise['media']))

# Gráfico
import plotly.graph_objects as go

fig = go.Figure(data=[go.Bar(
    x=[...],
    y=[...],
    marker_color='#3498db'
)])

st.plotly_chart(fig, use_container_width=True)
```

### Criar Novo Dashboard

**Arquivo:** `pages/11_Novo_Dashboard.py`

```python
"""
Novo Dashboard
"""
import streamlit as st
import plotly.graph_objects as go
from datetime import date
from dateutil.relativedelta import relativedelta

# ... imports padrão ...

st.set_page_config(page_title="Novo Dashboard", page_icon="📊", layout="wide")

AuthService.init_session_state()
AuthService.require_auth()

show_sidebar_navigation()

st.title("📊 Novo Dashboard")

client_id = show_client_selector()
if not client_id:
    st.stop()

# Filtros de período
st.subheader("📅 Período")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("De:", value=date.today() - relativedelta(months=6))
with col2:
    end_date = st.date_input("Até:", value=date.today())

st.markdown("---")

# Buscar dados
db = SessionLocal()
try:
    dados = ReportService.get_nova_analise(db, client_id, start_date, end_date)
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("KPI 1", dados['kpi1'])
    # ... outros KPIs
    
    # Gráficos
    st.subheader("📊 Visualização")
    # ... gráficos
    
finally:
    db.close()
```

---

## 🔍 Queries Otimizadas

### Exemplos de Queries Eficientes

**Query com relacionamentos:**
```python
from sqlalchemy.orm import joinedload

# ✅ Carrega relacionamentos de uma vez (evita N+1)
transactions = db.query(Transaction)\
    .options(joinedload(Transaction.group))\
    .options(joinedload(Transaction.subgroup))\
    .filter(Transaction.client_id == client_id)\
    .all()

# Agora pode acessar t.group.name sem query adicional
```

**Query com agregação:**
```python
from sqlalchemy import func

# Total por categoria
result = db.query(
    Transaction.category,
    func.sum(Transaction.value).label('total'),
    func.count(Transaction.id).label('quantidade')
).filter(
    Transaction.client_id == client_id,
    Transaction.type == 'entrada'
).group_by(Transaction.category).all()

for categoria, total, qtd in result:
    print(f"{categoria}: {total} ({qtd} transações)")
```

**Query com filtros dinâmicos:**
```python
# Inicia query
query = db.query(Transaction).filter(Transaction.client_id == client_id)

# Adiciona filtros condicionalmente
if tipo_filter:
    query = query.filter(Transaction.type.in_(tipo_filter))

if date_from:
    query = query.filter(Transaction.date >= date_from)

if search:
    query = query.filter(Transaction.description.contains(search))

# Executa
results = query.order_by(Transaction.date.desc()).limit(100).all()
```

**Query com subquery:**
```python
from sqlalchemy import select

# Subquery para contar
subq = select(func.count(Transaction.id))\
    .where(Transaction.client_id == client_id)\
    .scalar_subquery()

# Usa na query principal
client = db.query(Client).filter(Client.id == client_id).first()
total_trans = db.scalar(subq)
```

---

## 🎨 Interface Streamlit

### Layouts Comuns

**Colunas:**
```python
# 2 colunas iguais
col1, col2 = st.columns(2)
with col1:
    st.write("Coluna 1")
with col2:
    st.write("Coluna 2")

# 3 colunas com proporções
col1, col2, col3 = st.columns([2, 1, 1])  # 50%, 25%, 25%

# 4 colunas
col1, col2, col3, col4 = st.columns(4)
```

**Tabs:**
```python
tab1, tab2, tab3 = st.tabs(["📋 Tab 1", "➕ Tab 2", "📊 Tab 3"])

with tab1:
    st.write("Conteúdo tab 1")

with tab2:
    st.write("Conteúdo tab 2")
```

**Expanders:**
```python
# Recolhido por padrão
with st.expander("Clique para expandir"):
    st.write("Conteúdo oculto")

# Expandido por padrão
with st.expander("Detalhes", expanded=True):
    st.write("Conteúdo visível")

# Aninhado
with st.expander("Nível 1"):
    st.write("Conteúdo nível 1")
    
    with st.expander("Nível 2"):
        st.write("Conteúdo nível 2")
```

**Formulários:**
```python
with st.form("meu_form"):
    # Campos do formulário
    campo1 = st.text_input("Campo 1")
    campo2 = st.number_input("Campo 2")
    
    # Botões
    col1, col2 = st.columns(2)
    with col1:
        submit = st.form_submit_button("💾 Salvar", use_container_width=True)
    with col2:
        cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
    
    if submit:
        # Processar
        pass
```

**Métricas:**
```python
# Métrica simples
st.metric("Label", "Valor")

# Com delta
st.metric("Receitas", "R$ 10.000", delta="+20%")

# Delta inverso (vermelho para aumento)
st.metric("Despesas", "R$ 5.000", delta="+10%", delta_color="inverse")

# Com help
st.metric("KPI", "100", help="Descrição do KPI")
```

**DataFrames:**
```python
# DataFrame simples
st.dataframe(df)

# Com opções
st.dataframe(
    df,
    use_container_width=True,  # Usa largura total
    hide_index=True,            # Esconde índice
    height=400                  # Altura fixa
)

# DataFrame editável
edited_df = st.data_editor(df)
```

---

## 📊 Gráficos Plotly

### Gráfico de Barras

```python
import plotly.graph_objects as go

fig = go.Figure()

fig.add_trace(go.Bar(
    name='Série 1',
    x=['A', 'B', 'C'],
    y=[10, 20, 15],
    marker_color='#3498db',
    text=['R$ 10', 'R$ 20', 'R$ 15'],
    textposition='auto'
))

fig.update_layout(
    title="Título do Gráfico",
    xaxis_title="Eixo X",
    yaxis_title="Eixo Y",
    height=400,
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True)
```

### Gráfico de Linhas

```python
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=datas,
    y=valores,
    mode='lines+markers',
    name='Série',
    line=dict(color='#2ecc71', width=3),
    marker=dict(size=8)
))

# Linha de referência
fig.add_hline(y=media, line_dash="dash", line_color="red")

st.plotly_chart(fig, use_container_width=True)
```

### Gráfico de Pizza

```python
fig = go.Figure(data=[go.Pie(
    labels=['A', 'B', 'C'],
    values=[30, 50, 20],
    hole=0.4,  # Donut chart
    marker=dict(colors=['#2ecc71', '#3498db', '#e74c3c'])
)])

st.plotly_chart(fig, use_container_width=True)
```

### Heatmap

```python
fig = go.Figure(data=go.Heatmap(
    z=matriz_valores,  # [[val1, val2], [val3, val4]]
    x=['Col1', 'Col2'],
    y=['Row1', 'Row2'],
    colorscale='RdYlGn',
    text=matriz_valores,
    texttemplate='%{text}',
    colorbar=dict(title="Valor")
))

st.plotly_chart(fig, use_container_width=True)
```

---

## 🔐 Segurança e Permissões

### Verificar Permissões

**Em páginas:**
```python
# Exigir autenticação
AuthService.require_auth()

# Exigir role específica
AuthService.require_role(['admin', 'manager'])

# Verificar permissão para cliente
user = AuthService.get_current_user()
if not AuthService.check_permission(db, user['id'], client_id, 'edit'):
    st.error("❌ Você não tem permissão para editar este cliente")
    st.stop()
```

**Em operações:**
```python
# Antes de excluir
if AuthService.check_permission(db, user['id'], client_id, 'delete'):
    db.delete(objeto)
    db.commit()
else:
    st.error("Sem permissão para excluir")
```

### Adicionar Novo Perfil

**1. Atualizar modelo:**
```python
# models/user.py
# role pode ser: admin, manager, viewer, novo_perfil
```

**2. Atualizar lógica de permissões:**
```python
# services/auth_service.py

@staticmethod
def get_user_clients(db: Session, user_id: int) -> List[Client]:
    user = db.query(User).filter(User.id == user_id).first()
    
    # Admin e novo_perfil têm acesso total
    if user.role in ['admin', 'novo_perfil']:
        return db.query(Client).filter(Client.active == True).all()
    
    # Outros veem apenas com permissão
    # ...
```

**3. Atualizar páginas:**
```python
# Onde usa require_role:
AuthService.require_role(['admin', 'manager', 'novo_perfil'])
```

---

## 📈 Performance

### Otimizações

**1. Paginação:**
```python
# Limite de resultados
transactions = db.query(Transaction)\
    .filter(...)\
    .order_by(Transaction.date.desc())\
    .limit(100)\  # Mostra apenas 100
    .all()

st.caption(f"Mostrando 100 de {total_count} registros")
```

**2. Índices:**
```python
# Adicione índices em colunas filtradas frequentemente
date = Column(Date, index=True)
client_id = Column(Integer, ForeignKey('clients.id'), index=True)
```

**3. Cache:**
```python
@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_dados_pesados(client_id, start_date, end_date):
    # Query pesada
    return dados

# Uso
dados = get_dados_pesados(client_id, start_date, end_date)
```

**4. Lazy Loading:**
```python
# Carregue dados apenas quando necessário
with st.expander("Detalhes"):
    # Query executada apenas se expandir
    detalhes = db.query(...).all()
    st.dataframe(detalhes)
```

---

## 🧪 Testes

### Testar Nova Funcionalidade

**1. Teste manual:**
```python
# Execute o sistema
streamlit run app.py

# Teste:
# - Login com diferentes perfis
# - Operações CRUD
# - Filtros e buscas
# - Importação de dados
# - Geração de relatórios
```

**2. Teste com dados:**
```python
# Adicione dados ao seed
# tests/seed_data.py

def test_nova_funcionalidade(db, client):
    # Cria dados de teste específicos
    pass
```

**3. Teste unitário (opcional):**
```python
# tests/test_services.py
import pytest
from services.novo_service import NovoService

def test_metodo():
    result = NovoService.metodo(param1, param2)
    assert result == expected
```

---

## 🐛 Debug

### Logs e Print

**Durante desenvolvimento:**
```python
# Print no terminal
print(f"Debug: {variavel}")

# Log de queries SQL
# config/database.py
engine = create_engine(DATABASE_URL, echo=True)  # Mostra SQL
```

**Em produção:**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Operação realizada")
logger.error(f"Erro: {e}")
```

### Streamlit Debug

**Ver session state:**
```python
# Adicione temporariamente
st.write("Session State:", st.session_state)
```

**Ver exceções:**
```python
try:
    # código
except Exception as e:
    st.exception(e)  # Mostra stack trace completo
```

---

## 📦 Deployment

### Servidor Local (Rede Interna)

**1. Instale em servidor:**
```bash
cd contabil_system
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
python tests\seed_data.py --reset
```

**2. Execute:**
```bash
streamlit run app.py --server.address=0.0.0.0
```

**3. Acesse de outros computadores:**
```
http://IP_DO_SERVIDOR:8501
Ex: http://192.168.1.100:8501
```

### Docker (Opcional)

**Criar Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python init_db.py
RUN python tests/seed_data.py --reset

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

**Executar:**
```bash
docker build -t sistema-contabil .
docker run -p 8501:8501 sistema-contabil
```

---

## 🔄 Atualizações

### Atualizar Dependências

```bash
# Atualizar todas
pip install -r requirements.txt --upgrade

# Atualizar específica
pip install streamlit --upgrade

# Gerar novo requirements
pip freeze > requirements.txt
```

### Migrar para PostgreSQL

**1. Instale driver:**
```bash
pip install psycopg2-binary
```

**2. Altere database.py:**
```python
DATABASE_URL = "postgresql://user:password@localhost/contabil"
```

**3. Recrie banco:**
```bash
python init_db.py
```

---

## 📚 Recursos Adicionais

### Documentação Oficial:
- **Streamlit:** https://docs.streamlit.io
- **SQLAlchemy:** https://docs.sqlalchemy.org
- **Plotly:** https://plotly.com/python/
- **Pandas:** https://pandas.pydata.org

### Exemplos de Código:
- Veja `pages/` para exemplos de páginas
- Veja `services/` para lógica de negócio
- Veja `utils/` para funções auxiliares

---

## ✅ Checklist de Manutenção

### Antes de Modificar:

- [ ] Entenda o código existente
- [ ] Faça backup do banco (`data/`)
- [ ] Teste em ambiente de desenvolvimento
- [ ] Documente as alterações

### Ao Adicionar Funcionalidade:

- [ ] Crie/atualize modelo se necessário
- [ ] Crie/atualize serviço
- [ ] Crie/atualize página
- [ ] Adicione ao menu (app.py)
- [ ] Teste com dados reais
- [ ] Atualize documentação
- [ ] Atualize seed_data.py se relevante

### Antes de Distribuir:

- [ ] Teste em computador limpo
- [ ] Verifique credenciais padrão
- [ ] Atualize versão
- [ ] Gere executável (se necessário)
- [ ] Atualize LEIA-ME.txt
- [ ] Teste install.bat e run.bat

---

## 🎉 Conclusão

**Documentação técnica completa para manutenção!**

Este guia cobre:
- ✅ Arquitetura detalhada
- ✅ Todos os modelos e relacionamentos
- ✅ Todos os serviços e métodos
- ✅ Todas as páginas e funcionalidades
- ✅ Exemplos de código
- ✅ Boas práticas
- ✅ Troubleshooting
- ✅ Otimizações
- ✅ Deployment

**Use como referência para qualquer manutenção futura!** 🚀


