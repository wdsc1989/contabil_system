"""
Página de Importação de Dados
"""
import streamlit as st
import sys
import os
import pandas as pd
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.parser_service import ParserService
from services.import_service import ImportService
from services.ai_service import AIService
from services.data_processor import DataProcessor
from utils.column_mapper import ColumnMapper
from utils.translations import translate_dataframe
from models.client import Client
from models.group import Group, Subgroup
from config.ai_config import AIConfigManager

# Helpers


def _get_group_subgroup_names_mapping(db, client_id: int) -> tuple:
    """
    Cria mapeamento de IDs para nomes de grupos e subgrupos.
    Retorna: (group_mapping, subgroup_mapping)
    """
    from models.group import Group, Subgroup
    
    groups = db.query(Group).filter(Group.client_id == client_id).all()
    group_mapping = {g.id: g.name for g in groups}
    
    subgroups = db.query(Subgroup).join(Group).filter(Group.client_id == client_id).all()
    subgroup_mapping = {sg.id: sg.name for sg in subgroups}
    
    return group_mapping, subgroup_mapping


def _add_group_subgroup_names_to_data(data: list, group_mapping: dict, subgroup_mapping: dict) -> list:
    """
    Adiciona colunas group_name e subgroup_name aos dados baseado nos IDs.
    """
    result = []
    for record in data:
        record_copy = dict(record)
        
        # Adiciona nomes de grupo e subgrupo
        group_id = record_copy.get('group_id')
        subgroup_id = record_copy.get('subgroup_id')
        
        if group_id is not None and not pd.isna(group_id):
            try:
                group_id_int = int(group_id)
                record_copy['group_name'] = group_mapping.get(group_id_int, f'ID: {group_id_int}')
            except (ValueError, TypeError):
                record_copy['group_name'] = '-'
        else:
            record_copy['group_name'] = '-'
        
        if subgroup_id is not None and not pd.isna(subgroup_id):
            try:
                subgroup_id_int = int(subgroup_id)
                record_copy['subgroup_name'] = subgroup_mapping.get(subgroup_id_int, f'ID: {subgroup_id_int}')
            except (ValueError, TypeError):
                record_copy['subgroup_name'] = '-'
        else:
            record_copy['subgroup_name'] = '-'
        
        result.append(record_copy)
    
    return result


def _filter_transaction_rows(df: pd.DataFrame, import_type: str) -> pd.DataFrame:
    """
    Filtra linhas inválidas do DataFrame, removendo:
    - Linhas completamente em branco
    - Linhas que contêm saldo do dia (não são transações)
    
    Mantém apenas linhas que parecem ser transações reais.
    """
    if df.empty:
        return df
    
    # Palavras-chave que indicam saldo (não transação)
    saldo_keywords = [
        'saldo', 'saldo do dia', 'saldo inicial', 'saldo final', 
        'saldo anterior', 'saldo atual', 'saldo anterior do dia',
        'saldo do período', 'saldo consolidado', 'balance'
    ]
    
    # Cria uma cópia para não modificar o original
    filtered_df = df.copy()
    
    # Identifica linhas a remover
    rows_to_remove = []
    
    for idx, row in filtered_df.iterrows():
        should_remove = False
        
        # Verifica se a linha está completamente vazia
        is_empty = True
        for col in filtered_df.columns:
            value = row.get(col)
            if pd.notna(value) and value != '' and str(value).strip() != '':
                is_empty = False
                break
        
        if is_empty:
            should_remove = True
            rows_to_remove.append(idx)
            continue
        
        # Converte todos os valores da linha para string para busca
        row_text = ' '.join([
            str(row.get(col, '')).lower() 
            for col in filtered_df.columns 
            if pd.notna(row.get(col, ''))
        ])
        
        # Verifica se contém palavras-chave de saldo
        contains_saldo_keyword = any(
            keyword.lower() in row_text 
            for keyword in saldo_keywords
        )
        
        # Para bank_statements: verifica se tem apenas balance sem description ou value
        if import_type == 'bank_statements':
            has_balance = pd.notna(row.get('balance')) and str(row.get('balance', '')).strip() != ''
            has_description = pd.notna(row.get('description')) and str(row.get('description', '')).strip() != ''
            has_value = pd.notna(row.get('value')) and str(row.get('value', '')).strip() != ''
            
            # Se tem balance mas não tem description nem value, provavelmente é linha de saldo
            if has_balance and not has_description and not has_value:
                should_remove = True
        
        # Se contém palavra-chave de saldo e não parece ser uma transação válida
        if contains_saldo_keyword:
            # Verifica se tem campos que indicam transação (description, value, date)
            has_transaction_fields = False
            if import_type == 'bank_statements':
                has_transaction_fields = (
                    (pd.notna(row.get('description')) and str(row.get('description', '')).strip() != '') or
                    (pd.notna(row.get('value')) and str(row.get('value', '')).strip() != '')
                )
            elif import_type == 'transactions':
                has_transaction_fields = (
                    (pd.notna(row.get('description')) and str(row.get('description', '')).strip() != '') and
                    (pd.notna(row.get('value')) and str(row.get('value', '')).strip() != '')
                )
            else:
                # Para outros tipos, verifica se tem pelo menos description ou value
                has_transaction_fields = (
                    (pd.notna(row.get('description')) and str(row.get('description', '')).strip() != '') or
                    (pd.notna(row.get('value')) and str(row.get('value', '')).strip() != '')
                )
            
            # Se não tem campos de transação, provavelmente é linha de saldo
            if not has_transaction_fields:
                should_remove = True
        
        if should_remove:
            rows_to_remove.append(idx)
    
    # Remove linhas identificadas
    if rows_to_remove:
        filtered_df = filtered_df.drop(index=rows_to_remove).reset_index(drop=True)
    
    return filtered_df


st.set_page_config(page_title="Importação de Dados", page_icon="📥", layout="wide")

# Esconde o menu automático do Streamlit
from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

# Verifica autenticação
AuthService.init_session_state()
AuthService.require_auth()

# Verifica se usuário é administrador
user = AuthService.get_current_user()
is_admin = user and user.get('role') == 'admin'

# Seção de Prompts de IA (apenas para administradores)
if is_admin:
    from services.ai_multi_agent import AIMultiAgent
    from config.database import SessionLocal
    
    with st.expander("🔧 **Configuração de IA com MCP (Apenas Administrador)**", expanded=False):
        db = SessionLocal()
        try:
            multi_agent = AIMultiAgent(db)
            prompts_info = multi_agent.get_prompts()
            mcp_tools_info = multi_agent.get_mcp_tools_info()
            
            st.info("💡 **Arquitetura MCP:** Os agentes agora usam MCP Tools estruturados. Schemas JSON são gerados automaticamente a partir dos modelos SQLAlchemy.")
            
            # Tabs: Agentes e MCP Tools
            tab1, tab2 = st.tabs(["🤖 Agentes", "🛠️ MCP Tools"])
            
            with tab1:
                st.markdown("### Agentes de Processamento")
                st.caption("Os agentes usam MCP Tools internamente. Prompts customizados são aplicados aos tools correspondentes.")
                
                # Tabs para cada agente
                agent_tabs = st.tabs([info['name'] for info in prompts_info.values()])
                
                for idx, (agent_key, agent_info) in enumerate(prompts_info.items()):
                    with agent_tabs[idx]:
                        st.caption(f"**{agent_info['description']}**")
                        
                        # Mostra MCP Tools usados
                        if 'mcp_tool' in agent_info:
                            st.info(f"🔧 Usa MCP Tool: **{agent_info['mcp_tool']}**")
                        elif 'mcp_tools' in agent_info:
                            st.info(f"🔧 Usa MCP Tools: **{', '.join(agent_info['mcp_tools'])}**")
                        
                        if 'note' in agent_info:
                            st.caption(f"ℹ️ {agent_info['note']}")
                        
                        # Estado de edição para este agente
                        edit_key = f"edit_{agent_key}"
                        if edit_key not in st.session_state:
                            st.session_state[edit_key] = False
                        
                        # Obtém prompt atual (customizado ou padrão)
                        current_prompt = agent_info.get('custom')
                        default_template = agent_info.get('default_template', '')
                        
                        # Status do prompt atual
                        if not current_prompt:
                            prompt_display = default_template if default_template else "**Usando prompts gerados automaticamente pelos MCP Tools**"
                            st.info("ℹ️ Usando prompts padrão dos MCP Tools. A personalização está disponível apenas para agent1 e agent3.")
                        else:
                            prompt_display = current_prompt
                            st.success("✅ Usando prompt customizado.")
                        
                        st.markdown("---")
                        
                        # Text area para exibir/editar prompt (apenas para agentes que suportam)
                        if agent_key in ['agent1', 'agent3']:
                            prompt_text = st.text_area(
                                f"Prompt do {agent_info['name']}",
                                value=prompt_display if st.session_state[edit_key] else (prompt_display[:500] + "..." if len(prompt_display) > 500 and not st.session_state[edit_key] else prompt_display),
                                height=400 if st.session_state[edit_key] else 200,
                                disabled=not st.session_state[edit_key],
                                key=f"prompt_text_{agent_key}",
                                help=f"Placeholders: {', '.join(agent_info.get('placeholders', []))}"
                            )
                            
                            # Botões de ação
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                if st.button("✏️ Editar", key=f"btn_edit_{agent_key}"):
                                    st.session_state[edit_key] = True
                                    st.rerun()
                            
                            with col2:
                                if st.session_state[edit_key]:
                                    if st.button("💾 Salvar", key=f"btn_save_{agent_key}", type="primary"):
                                        if prompt_text and prompt_text.strip():
                                            multi_agent.update_prompt(agent_key, prompt_text.strip())
                                            st.session_state[edit_key] = False
                                            st.success(f"✅ Prompt salvo!")
                                            st.rerun()
                                        else:
                                            st.error("❌ O prompt não pode estar vazio!")
                            
                            with col3:
                                if agent_info.get('custom'):
                                    if st.button("🔄 Restaurar", key=f"btn_reset_{agent_key}"):
                                        multi_agent.reset_prompt(agent_key)
                                        st.session_state[edit_key] = False
                                        st.success(f"✅ Prompt restaurado!")
                                        st.rerun()
                            
                            if agent_info.get('placeholders'):
                                st.caption(f"💡 **Placeholders:** {', '.join(agent_info.get('placeholders', []))}")
                        else:
                            st.info("ℹ️ Este agente usa MCP Tools que geram prompts automaticamente baseados nos schemas. Não é necessário personalizar.")
            
            with tab2:
                st.markdown("### MCP Tools Disponíveis")
                st.caption("Tools estruturados que os agentes usam internamente. Schemas são gerados automaticamente.")
                
                for tool_name, tool_info in mcp_tools_info.items():
                    with st.expander(f"🔧 {tool_name}", expanded=False):
                        st.write(f"**Descrição:** {tool_info['description']}")
                        st.write("**Parâmetros obrigatórios:**")
                        for param in tool_info.get('required_params', []):
                            st.write(f"- `{param}`")
                        
                        if tool_info.get('input_schema', {}).get('properties'):
                            st.write("**Parâmetros disponíveis:**")
                            for param, schema in tool_info['input_schema']['properties'].items():
                                param_type = schema.get('type', 'unknown')
                                param_desc = schema.get('description', '')
                                st.write(f"- `{param}` ({param_type}): {param_desc}")
        finally:
            db.close()
    
    st.markdown("---")

# Usa sidebar centralizada
from utils.sidebar import show_sidebar
show_sidebar()

st.title("📥 Importação de Dados")
st.markdown("**Processamento automático com IA Vision - Suporta CSV, Excel, PDF (incluindo protegidos por senha), OFX e Imagens**")
st.markdown("---")

# Verifica se há cliente selecionado
if not st.session_state.get('selected_client_id'):
    st.warning("⚠️ Selecione um cliente na página inicial para importar dados.")
    st.stop()

client_id = st.session_state.selected_client_id

# Informações do cliente
db = SessionLocal()
try:
    client = db.query(Client).filter(Client.id == client_id).first()
    if client:
        st.info(f"📌 **Cliente:** {client.name}")
finally:
    db.close()

# Upload de arquivo
st.subheader("📤 Upload do Arquivo")

uploaded_file = st.file_uploader(
    "Selecione um arquivo para importar",
    type=['csv', 'txt', 'xlsx', 'xls', 'pdf', 'ofx', 'jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp', 'webp'],
    help="Formatos suportados: CSV, Excel, PDF (incluindo protegidos por senha), OFX, Imagens (JPG, PNG, etc). O sistema detecta e processa automaticamente. Para PDFs protegidos, você poderá inserir a senha durante o processamento."
)

if uploaded_file:
    # LÊ O ARQUIVO UMA ÚNICA VEZ NO INÍCIO
    try:
        file_content_initial = uploaded_file.read()
        file_size = len(file_content_initial)
        file_size_kb = file_size / 1024
        
        # Verifica se o arquivo está vazio
        if not file_content_initial or file_size == 0:
            st.error("❌ **Erro:** Arquivo vazio. Verifique se o arquivo foi carregado corretamente.")
            st.stop()
        
        st.success(f"✅ **{uploaded_file.name}** ({file_size_kb:.1f} KB)")
    except Exception as e:
        st.error(f"❌ **Erro ao ler arquivo:** {str(e)}")
        st.stop()
    
    # Verifica se Vision API está disponível
    db = SessionLocal()
    try:
        ai_service = AIService(db)
        
        if not ai_service.is_available():
            st.error("❌ IA não configurada. Configure a IA na página de Administração antes de importar.")
            st.stop()
        
        # Verifica se suporta Vision API
        config = AIConfigManager.get_config_dict(db)
        provider = config.get('provider', '')
        model = config.get('model', '')
        
        if not AIConfigManager.supports_vision(provider, model):
            st.error(f"❌ O modelo {model} do provedor {provider} não suporta Vision API. Configure um modelo compatível (gpt-4o, gpt-4o-mini, etc).")
            st.stop()
        
        # Busca grupos e subgrupos
        groups = db.query(Group).filter(Group.client_id == client_id).all()
        groups_subgroups = []
        for group in groups:
            subgroups = db.query(Subgroup).filter(Subgroup.group_id == group.id).all()
            groups_subgroups.append({
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'subgroups': [
                    {
                        'id': sg.id,
                        'name': sg.name,
                        'description': sg.description
                    }
                    for sg in subgroups
                ]
            })
    finally:
        db.close()
    
    # Processamento direto com Vision API
    st.markdown("---")
    
    # Usa o conteúdo já lido acima
    file_content = file_content_initial
    
    # Verifica se já foi processado
    file_hash = f"{uploaded_file.name}_{len(file_content)}"
    if 'processed_file_hash' not in st.session_state or st.session_state.processed_file_hash != file_hash:
        # Detecta tipo de arquivo pela extensão E pelo conteúdo
        file_extension = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else ''
        is_image_file = file_extension in ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp', 'webp']
        
        # Detecta tipo real do arquivo pelo conteúdo (magic bytes)
        detected_content_type = ParserService.detect_file_type(file_content, uploaded_file.name)
        
        file_type_map = {
            'csv': 'CSV',
            'txt': 'CSV',
            'xlsx': 'Excel',
            'xls': 'Excel',
            'pdf': 'PDF',
            'ofx': 'OFX'
        }
        
        # Usa extensão primeiro, mas valida com conteúdo
        file_type = file_type_map.get(file_extension, 'CSV' if not is_image_file else 'Image')
        
        # Se a extensão diz PDF mas o conteúdo não é PDF, ajusta
        if file_type == 'PDF' and detected_content_type != 'PDF':
            if detected_content_type == 'EXCEL':
                file_type = 'Excel'
                st.warning(f"⚠️ Arquivo tem extensão .pdf mas é realmente um Excel. Processando como Excel...")
            elif detected_content_type == 'IMAGE':
                file_type = 'Image'
                st.warning(f"⚠️ Arquivo tem extensão .pdf mas é realmente uma imagem. Processando como imagem...")
        
        # Se a extensão diz CSV mas o conteúdo é outro tipo, mantém CSV (pode ser texto)
        # Processa arquivo
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_status(message):
            status_text.info(f"🤖 {message}")
        
        update_status(f"Detectando tipo de arquivo: {file_type}...")
        progress_bar.progress(10)
        
        # Parse do arquivo
        df = None
        
        if file_type == 'CSV':
            update_status("Processando arquivo CSV...")
            progress_bar.progress(20)
            # file_content já foi lido acima, não precisa ler novamente
            delimiter = ParserService.detect_delimiter(file_content)
            
            # Tenta diferentes encodings automaticamente
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            df = None
            last_error = None
            
            for encoding in encodings:
                try:
                    df = ParserService.parse_csv(file_content, encoding, delimiter)
                    if df is not None and not df.empty:
                        st.success(f"✅ CSV processado com encoding: {encoding}")
                        break
                except Exception as e:
                    last_error = str(e)
                    continue
            
            if df is None or df.empty:
                # Última tentativa com utf-8 e erro ignorado
                try:
                    df = ParserService.parse_csv(file_content, 'utf-8', delimiter, errors='ignore')
                    if df is not None and not df.empty:
                        st.warning("⚠️ CSV processado com encoding UTF-8 (alguns caracteres podem ter sido ignorados)")
                except Exception as e:
                    last_error = str(e)
                    st.error(f"❌ **Não foi possível processar o arquivo CSV**\n\n")
                    st.error(f"**Erro:** {last_error}")
                    
                    with st.expander("💡 Soluções possíveis", expanded=True):
                        st.markdown("""
                        **O arquivo CSV não pôde ser processado. Tente:**
                        
                        1. **Verificar o formato**: Certifique-se de que é um CSV válido (valores separados por vírgula, ponto-e-vírgula ou tab)
                        2. **Verificar encoding**: O arquivo pode estar em um encoding diferente. Tente salvar como UTF-8
                        3. **Verificar delimitador**: Verifique se o delimitador está correto (vírgula, ponto-e-vírgula, tab)
                        4. **Verificar estrutura**: Certifique-se de que todas as linhas têm o mesmo número de colunas
                        5. **Converter para Excel**: Se possível, converta o CSV para Excel (.xlsx) e importe como Excel
                        """)
                    
                    # Mostra preview do conteúdo para debug
                    try:
                        preview = file_content[:500].decode('utf-8', errors='ignore')
                        with st.expander("🔍 Preview do arquivo (primeiros 500 caracteres)", expanded=False):
                            st.code(preview)
                    except:
                        pass
                    
                    st.stop()
        
        elif file_type == 'Excel':
            update_status("Processando arquivo Excel...")
            progress_bar.progress(20)
            # file_content já foi lido acima
            
            # Processa todas as abas automaticamente
            try:
                df = ParserService.parse_excel(file_content, all_sheets=True)
                if df is None or df.empty:
                    # Fallback: tenta apenas a primeira aba
                    df = ParserService.parse_excel(file_content)
            except Exception as e:
                st.error(f"❌ Erro ao processar Excel: {str(e)}")
                st.stop()
        
        elif file_type == 'PDF':
            update_status("Processando arquivo PDF...")
            progress_bar.progress(20)
            # file_content já foi lido acima
            
            # Inicializa senha do PDF no session_state se não existir
            pdf_password_key = f"pdf_password_{file_hash}"
            if pdf_password_key not in st.session_state:
                st.session_state[pdf_password_key] = ""
            
            # Valida PDF antes de processar (sem senha primeiro para detectar se está protegido)
            is_valid, validation_error = ParserService.validate_pdf(file_content, uploaded_file.name)
            pdf_password = st.session_state[pdf_password_key] if st.session_state[pdf_password_key] else None
            
            # Se PDF está protegido por senha
            if not is_valid and validation_error == "PDF_PROTECTED":
                st.warning("🔒 **PDF Protegido por Senha**")
                st.info("Este PDF está protegido por senha. Por favor, insira a senha para continuar.")
                
                # Campo de senha
                pdf_password_input = st.text_input(
                    "🔑 Senha do PDF",
                    value=st.session_state[pdf_password_key],
                    type="password",
                    key=f"pdf_password_input_{file_hash}",
                    help="Digite a senha do PDF protegido"
                )
                
                # Atualiza session_state quando senha é inserida
                if pdf_password_input != st.session_state[pdf_password_key]:
                    st.session_state[pdf_password_key] = pdf_password_input
                    st.rerun()
                
                # Se senha foi fornecida, tenta validar novamente
                if pdf_password_input:
                    is_valid_with_password, validation_error_with_password = ParserService.validate_pdf(
                        file_content, uploaded_file.name, password=pdf_password_input
                    )
                    if not is_valid_with_password:
                        if "incorrect password" in validation_error_with_password.lower() or "senha incorreta" in validation_error_with_password.lower():
                            st.error("❌ **Senha incorreta.** Por favor, verifique a senha e tente novamente.")
                        else:
                            st.error(f"❌ **Erro:** {validation_error_with_password}")
                        st.stop()
                    else:
                        # Senha correta, continua com o processamento
                        pdf_password = pdf_password_input
                        st.success("✅ Senha correta! Processando PDF...")
                else:
                    st.stop()
            
            # Se ainda não é válido e não é problema de senha
            elif not is_valid:
                st.error(f"❌ **Erro ao Validar PDF**\n\n{validation_error}")
                
                # Detecta tipo real do arquivo para dar sugestões específicas
                detected_type = ParserService.detect_file_type(file_content, uploaded_file.name)
                
                with st.expander("💡 Soluções possíveis", expanded=True):
                    if detected_type == 'EXCEL':
                        st.markdown("""
                        **Este arquivo é um Excel, não um PDF:**
                        
                        1. **Opção 1**: Selecione o tipo de arquivo correto (Excel) ao fazer upload
                        2. **Opção 2**: Converta o Excel para PDF usando "Salvar como PDF" no Excel
                        3. **Opção 3**: Importe diretamente como Excel (o sistema suporta Excel)
                        """)
                    elif detected_type == 'IMAGE':
                        st.markdown("""
                        **Este arquivo é uma imagem, não um PDF:**
                        
                        1. **Opção 1**: Selecione o tipo de arquivo correto (Imagem) ao fazer upload
                        2. **Opção 2**: Converta a imagem para PDF usando um conversor online ou software
                        3. **Opção 3**: Importe diretamente como imagem (o sistema suporta imagens)
                        """)
                    else:
                        st.markdown("""
                        **O arquivo não pôde ser processado como PDF. Tente uma das seguintes soluções:**
                        
                        1. **Verificar o arquivo**: Abra o arquivo em um visualizador apropriado e verifique se está íntegro
                        2. **Re-salvar**: Se for realmente um PDF, abra e salve novamente (pode corrigir problemas de estrutura)
                        3. **Verificar formato**: Certifique-se de que o arquivo é realmente um PDF e não foi apenas renomeado
                        4. **Converter**: Se o arquivo é de outro formato (Excel, Word, Imagem), converta para PDF primeiro
                        5. **Tentar OCR**: Se o PDF é baseado em imagens, tente o botão abaixo para processar com OCR
                        """)
                
                # Oferece tentar processar com OCR mesmo assim
                if st.button("🔄 Tentar processar com OCR (pode demorar)", width='stretch', key="try_ocr_pdf_invalid"):
                    try:
                        update_status("Tentando processar PDF corrompido com OCR...")
                        progress_bar.progress(30)
                        pdf_data = ParserService._parse_pdf_with_ocr_fallback(file_content, password=pdf_password)
                        df = pdf_data.get('dataframe')
                        st.session_state['pdf_full_data'] = pdf_data
                        st.success("✅ PDF processado com OCR! Alguns dados podem estar incompletos.")
                    except Exception as ocr_error:
                        st.error(f"❌ OCR também falhou: {str(ocr_error)}")
                        st.stop()
                else:
                    st.stop()
            else:
                # PDF válido, processa normalmente
                pdf_data = None
                try:
                    pdf_data = ParserService.parse_pdf_complete(file_content, use_ocr_if_needed=True, password=pdf_password)
                    df = pdf_data.get('dataframe')
                    
                    # Se OCR foi usado, informa ao usuário
                    if pdf_data.get('metadata', {}).get('ocr_used', False):
                        st.info("ℹ️ PDF baseado em imagens detectado. OCR foi usado para extrair o texto.")
                except Exception as e:
                    error_msg = str(e).lower()
                    # Verifica se é erro de senha incorreta
                    if "senha incorreta" in error_msg or "incorrect password" in error_msg or "password" in error_msg:
                        st.error("❌ **Senha incorreta.** Por favor, verifique a senha e tente novamente.")
                        # Limpa a senha para permitir nova tentativa
                        st.session_state[pdf_password_key] = ""
                        st.stop()
                    elif "root" in error_msg or "corrompido" in error_msg or "invalid" in error_msg:
                        st.warning(f"⚠️ PDF pode estar corrompido: {str(e)}")
                        st.info("🔄 Tentando processar com OCR como alternativa...")
                        try:
                            pdf_data = ParserService._parse_pdf_with_ocr_fallback(file_content, password=pdf_password)
                            df = pdf_data.get('dataframe')
                            st.session_state['pdf_full_data'] = pdf_data
                            st.success("✅ PDF processado com OCR!")
                        except Exception as ocr_error:
                            st.error(f"❌ Não foi possível processar o PDF: {str(ocr_error)}")
                            st.stop()
                    else:
                        st.warning(f"⚠️ Aviso ao processar PDF: {str(e)}")
                        # Fallback para método simples
                        try:
                            df = ParserService.parse_pdf_to_dataframe(file_content, password=pdf_password)
                        except Exception as fallback_error:
                            st.error(f"❌ Erro ao processar PDF: {str(fallback_error)}")
                            st.stop()
            
            if df is None or df.empty:
                # Se não encontrou tabelas, tenta extrair do texto usando regex
                if pdf_data and pdf_data.get('full_text'):
                    st.info("ℹ️ Nenhuma tabela estruturada encontrada. Tentando extrair dados do texto...")
                    # Tenta criar DataFrame a partir do texto extraído
                    df = ParserService._text_to_dataframe_from_ocr(pdf_data.get('full_text', ''))
                    if df is None or df.empty:
                        st.warning("⚠️ Não foi possível extrair dados estruturados do texto. O texto completo será usado para classificação.")
                        df = pd.DataFrame()
                    # Salva dados completos do PDF para referência
                    st.session_state['pdf_full_data'] = pdf_data
                else:
                    st.error("❌ Não foi possível extrair dados do PDF. Tente converter para CSV ou Excel.")
                    st.stop()
            else:
                # Salva dados completos do PDF para referência
                if pdf_data:
                    st.session_state['pdf_full_data'] = pdf_data
        
        elif file_type == 'OFX':
            update_status("Processando arquivo OFX...")
            progress_bar.progress(20)
            # file_content já foi lido acima
            try:
                df = ParserService.ofx_to_dataframe(file_content)
                if df is not None and not df.empty:
                    st.success("✅ OFX processado com sucesso")
                else:
                    st.error("❌ Não foi possível extrair dados do arquivo OFX.")
                    st.stop()
            except Exception as e:
                st.error(f"❌ Erro ao processar OFX: {str(e)}")
                st.stop()
        elif file_type == 'Image' or is_image_file:
            # file_content já foi lido acima
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            # Tenta usar Vision API primeiro (não requer OCR local)
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Verifica se Vision API está disponível
            db = SessionLocal()
            vision_api_used = False
            try:
                from services.vision_processor import VisionProcessor
                vision_processor = VisionProcessor(db)
                
                if vision_processor.is_available():
                    # Usa Vision API diretamente (melhor opção, não requer OCR local)
                    status_text.info("🤖 Processando imagem com Vision API (não requer OCR local)...")
                    progress_bar.progress(20)
                    
                    try:
                        result = vision_processor.process_file(
                            file_content=file_content,
                            filename=uploaded_file.name,
                            import_type="transactions"
                        )
                        
                        if result and result.get('success') and result.get('processed_data'):
                            progress_bar.progress(80)
                            # Converte dados processados para DataFrame
                            processed_data = result.get('processed_data', [])
                            if processed_data:
                                df = pd.DataFrame(processed_data)
                                st.session_state['pdf_full_data'] = {
                                    'full_text': '',
                                    'dataframe': df,
                                    'metadata': {'ocr_used': False, 'vision_api_used': True}
                                }
                                st.session_state['is_image_file'] = True
                                vision_api_used = True
                                progress_bar.progress(100)
                                status_text.empty()
                                progress_bar.empty()
                                st.success(f"✅ Imagem processada com Vision API! {len(df)} registro(s) extraído(s).")
                            else:
                                # Se não retornou dados estruturados, tenta extrair texto
                                full_text = result.get('full_text', '')
                                if full_text:
                                    df = pd.DataFrame()
                                    st.session_state['pdf_full_data'] = {
                                        'full_text': full_text,
                                        'dataframe': df,
                                        'metadata': {'ocr_used': False, 'vision_api_used': True}
                                    }
                                    st.session_state['is_image_file'] = True
                                    vision_api_used = True
                                    progress_bar.progress(100)
                                    status_text.empty()
                                    progress_bar.empty()
                                    st.success(f"✅ Imagem processada! {len(full_text)} caracteres extraídos. A IA processará o texto...")
                                else:
                                    raise Exception("Vision API não retornou dados ou texto")
                        else:
                            error_msg = result.get('error', 'Erro desconhecido') if result else 'Nenhum resultado retornado'
                            raise Exception(f"Vision API retornou erro: {error_msg}")
                    except Exception as vision_error:
                        # Se Vision API falhar, tenta OCR local como fallback
                        status_text.warning(f"⚠️ Vision API falhou: {str(vision_error)}. Tentando OCR local...")
                        progress_bar.progress(30)
                        raise vision_error  # Re-raise para tentar OCR local
                else:
                    # Vision API não disponível, tenta OCR local
                    status_text.info("🖼️ Vision API não disponível. Tentando OCR local...")
                    progress_bar.progress(10)
                    raise Exception("Vision API não disponível")
            except Exception as vision_error:
                # Fallback: tenta OCR local
                try:
                    status_text.info("🖼️ Processando imagem com OCR local...")
                    progress_bar.progress(30)
                    
                    image_data = ParserService.parse_image(file_content, file_extension)
                    progress_bar.progress(80)
                    
                    df = image_data.get('dataframe')
                    full_text = image_data.get('full_text', '')
                    
                    # Salva dados da imagem para uso pela IA
                    st.session_state['pdf_full_data'] = image_data
                    st.session_state['is_image_file'] = True
                    
                    progress_bar.progress(100)
                    status_text.empty()
                    progress_bar.empty()
                    
                    if df is None or df.empty:
                        if full_text and len(full_text.strip()) > 10:
                            st.success(f"✅ Imagem processada! {len(full_text)} caracteres extraídos. A IA processará o texto extraído...")
                        else:
                            st.warning("⚠️ Pouco texto extraído da imagem. A IA tentará processar mesmo assim...")
                        df = pd.DataFrame()
                    else:
                        st.success(f"✅ Imagem processada! {len(df)} linha(s) extraída(s) com OCR.")
                except Exception as ocr_error:
                    error_msg = str(ocr_error)
                    st.error(f"❌ Erro ao processar imagem: {error_msg}")
                    
                    # Mensagens de ajuda específicas
                    if "tesseract" in error_msg.lower() or "pytesseract" in error_msg.lower() or "easyocr" in error_msg.lower():
                        st.warning("⚠️ **OCR local não está disponível ou configurado.**")
                        st.info("""
                        **Soluções:**
                        
                        **Opção 1 (Recomendada):** Configure a Vision API
                        - Acesse a página de Administração
                        - Configure a IA com OpenAI (gpt-4o ou gpt-4o-mini)
                        - A Vision API processará imagens sem precisar de OCR local
                        
                        **Opção 2:** Instalar OCR local (Windows)
                        - **Tesseract OCR:**
                          1. Baixe de: https://github.com/UB-Mannheim/tesseract/wiki
                          2. Instale o executável
                          3. Adicione ao PATH do sistema ou configure a variável de ambiente
                          4. Instale as bibliotecas Python: `pip install pytesseract Pillow`
                        
                        **Opção 3:** Converter para PDF
                        - Converta a imagem para PDF usando um conversor online
                        - O sistema processará o PDF com a Vision API (se configurada)
                        """)
                    else:
                        st.info("💡 Certifique-se de que as bibliotecas de OCR estão instaladas: pip install pytesseract pdf2image Pillow easyocr")
                    
                    st.stop()
            finally:
                db.close()
        
        # Limpa estado de override após processar
        if 'show_file_type_override' in st.session_state:
            del st.session_state.show_file_type_override
        if 'detected_file_type' in st.session_state:
            del st.session_state.detected_file_type
        
        if df is not None and not df.empty:
            st.markdown("---")
            st.subheader("📊 Dados Extraídos")
            
            # Métricas simplificadas
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Linhas", f"{len(df):,}".replace(',', '.'))
            with col2:
                st.metric("Colunas", len(df.columns))
            
            # Salva DataFrame extraído no session state
            st.session_state['extracted_df'] = df
            
            # Detecção automática do tipo de dado
            st.markdown("---")
            st.subheader("🔍 Tipo de Dado")
            
            db = SessionLocal()
            try:
                # Inicializa import_type como None
                import_type = None
                
                # Verifica se o tipo já foi confirmado anteriormente
                if st.session_state.get('type_confirmed', False) and 'detected_import_type' in st.session_state:
                    import_type = st.session_state.detected_import_type
                # Se for OFX, já sabemos que é extrato bancário
                elif file_type == 'OFX':
                    import_type = 'bank_statements'
                    if 'type_confirmed' not in st.session_state or not st.session_state.type_confirmed:
                        st.session_state.detected_import_type = import_type
                        st.session_state.type_confirmed = True
                        st.rerun()
                    import_type = st.session_state.detected_import_type
                elif ai_service.is_available():
                    # Usa Multi-Agente para detecção (mais preciso, menos alucinações)
                    from services.ai_multi_agent import AIMultiAgent
                    multi_agent = AIMultiAgent(db)
                    
                    if multi_agent.is_available():
                        with st.spinner("🤖 [Agente 1] Detectando tipo de dado..."):
                            columns = list(df.columns)
                            data_sample = ai_service._prepare_data_sample(df, max_rows=20)
                            detection_result = multi_agent.agent_detect_type(columns, data_sample)
                    else:
                        # Fallback para método antigo
                        with st.spinner("🤖 Analisando arquivo para detectar tipo de dado..."):
                            columns = list(df.columns)
                            data_sample = ai_service._prepare_data_sample(df, max_rows=20)
                            detection_result = ai_service.detect_data_type(df, columns, data_sample)
                    
                    if detection_result.get('success'):
                        suggested_type = detection_result.get('suggested_type')
                        confidence = detection_result.get('confidence', 0.0)
                        reasoning = detection_result.get('reasoning', '')
                        alternative_types = detection_result.get('alternative_types', [])
                        key_indicators = detection_result.get('key_indicators', [])
                        
                        # Mapeia tipo para nome amigável
                        type_names = {
                            'transactions': '💳 Transações Financeiras',
                            'bank_statements': '🏦 Extratos Bancários',
                            'contracts': '📝 Contratos/Eventos',
                            'accounts_payable': '💸 Contas a Pagar',
                            'accounts_receivable': '💰 Contas a Receber',
                            'financial_investments': '📈 Extratos de Aplicações Financeiras',
                            'credit_card_invoices': '💳 Faturas de Cartão de Crédito',
                            'card_machine_statements': '🏪 Extratos de Máquina de Cartão',
                            'inventory': '📦 Controle de Estoque'
                        }
                        
                        suggested_name = type_names.get(suggested_type, suggested_type)
                        confidence_percent = int(confidence * 100)
                        
                        # Exibe sugestão simplificada
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if confidence >= 0.7:
                                st.success(f"**{suggested_name}**")
                            else:
                                st.warning(f"**{suggested_name}** (Confiança: {confidence_percent}%)")
                        
                        with col2:
                            # Selectbox para correção se necessário
                            corrected_type = st.selectbox(
                                "Tipo:",
                                options=['transactions', 'bank_statements', 'contracts', 'accounts_payable', 'accounts_receivable',
                                        'financial_investments', 'credit_card_invoices', 'card_machine_statements', 'inventory'],
                                format_func=lambda x: type_names[x],
                                index=['transactions', 'bank_statements', 'contracts', 'accounts_payable', 'accounts_receivable',
                                      'financial_investments', 'credit_card_invoices', 'card_machine_statements', 'inventory'].index(suggested_type) if suggested_type in ['transactions', 'bank_statements', 'contracts', 'accounts_payable', 'accounts_receivable', 'financial_investments', 'credit_card_invoices', 'card_machine_statements', 'inventory'] else 0,
                                key="correct_type_selectbox"
                            )
                        
                        # Botão único de confirmação
                        if st.button("✅ Confirmar e Continuar", width='stretch', type="primary", key="confirm_ai_detected_type"):
                            import_type = corrected_type if corrected_type != suggested_type else suggested_type
                            st.session_state.detected_import_type = import_type
                            st.session_state.type_confirmed = True
                            st.rerun()
                        
                        # Se já foi confirmado anteriormente, usa o tipo confirmado
                        if 'detected_import_type' in st.session_state and st.session_state.get('type_confirmed', False):
                            import_type = st.session_state.detected_import_type
                    else:
                        # Erro na detecção, mostra seleção manual
                        st.warning(f"⚠️ Não foi possível detectar automaticamente. Erro: {detection_result.get('error', 'Desconhecido')}")
                        st.session_state.show_manual_selection = True
                else:
                    # IA não disponível, mostra seleção manual
                    st.info("ℹ️ IA não configurada. Selecione o tipo de dado manualmente.")
                    st.session_state.show_manual_selection = True
                
                # Seleção manual (se necessário)
                if 'show_manual_selection' in st.session_state and st.session_state.show_manual_selection:
                    type_names_map = {
                        'transactions': '💳 Transações Financeiras',
                        'bank_statements': '🏦 Extratos Bancários',
                        'contracts': '📝 Contratos/Eventos',
                        'accounts_payable': '💸 Contas a Pagar',
                        'accounts_receivable': '💰 Contas a Receber',
                        'financial_investments': '📈 Extratos de Aplicações Financeiras',
                        'credit_card_invoices': '💳 Faturas de Cartão de Crédito',
                        'card_machine_statements': '🏪 Extratos de Máquina de Cartão',
                        'inventory': '📦 Controle de Estoque'
                    }
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        import_type = st.selectbox(
                            "Tipo de dado:",
                            options=['transactions', 'bank_statements', 'contracts', 'accounts_payable', 'accounts_receivable',
                                    'financial_investments', 'credit_card_invoices', 'card_machine_statements', 'inventory'],
                            format_func=lambda x: type_names_map[x],
                            key="manual_import_type"
                        )
                    with col2:
                        if st.button("✅ Confirmar", width='stretch', type="primary", key="confirm_manual_type"):
                            st.session_state.detected_import_type = import_type
                            st.session_state.type_confirmed = True
                            st.session_state.show_manual_selection = False
                            st.rerun()
                
                # Se ainda não tem tipo definido, tenta obter do session state ou para
                if not import_type:
                    if 'detected_import_type' in st.session_state:
                        import_type = st.session_state.detected_import_type
                    else:
                        st.warning("⚠️ Tipo de dado não foi definido. Por favor, selecione o tipo de dado acima.")
                        st.stop()
                
                # Verifica se o tipo foi confirmado
                if not st.session_state.get('type_confirmed', False):
                    st.stop()
                
                # Processamento dos dados
                st.markdown("---")
                st.subheader("⚙️ Processamento")
                structure_hash = f"{uploaded_file.name}_{len(df)}_{import_type}_structured"
                previous_structure_valid = (
                    st.session_state.get('last_structure_hash') == structure_hash and
                    st.session_state.get('processed_data_is_structured', False)
                )
                
                if not previous_structure_valid:
                    # Filtra linhas em branco e saldos antes do mapeamento
                    df_filtered = _filter_transaction_rows(df, import_type)
                    rows_before = len(df)
                    rows_after = len(df_filtered)
                    rows_filtered = rows_before - rows_after
                    
                    if rows_filtered > 0:
                        st.info(f"ℹ️ **{rows_filtered} linha(s)** foram filtradas (linhas em branco ou saldos). Processando **{rows_after} transação(ões)** válidas.")
                    
                    processed_data = df_filtered.to_dict('records')
                    for record in processed_data:
                        record['group_id'] = None
                        record['subgroup_id'] = None
                    
                    structure_successful = False
                    structure_method = None
                    
                    db = SessionLocal()
                    try:
                        from services.ai_service import AIService
                        from services.ai_multi_agent import AIMultiAgent
                        ai_service = AIService(db)
                        multi_agent = AIMultiAgent(db)
                        
                        if multi_agent.is_available():
                            with st.spinner("🤖 [Agente 2] Analisando estrutura origem..."):
                                structure_analysis = multi_agent.agent_analyze_structure(df_filtered, import_type)
                            
                            if structure_analysis.get('success'):
                                with st.spinner("🤖 [Agente 3] Mapeando colunas origem → destino..."):
                                    mapping = multi_agent.agent_map_columns(structure_analysis, import_type)
                                    
                                    # Log do mapeamento obtido
                                    mapping_count = len(mapping) if mapping else 0
                                    if mapping_count > 0:
                                        st.info(f"✅ Mapeamento obtido: {mapping_count} coluna(s) mapeada(s)")
                                    
                                    # Se IA não retornou mapeamento, tenta mapeamento automático tradicional
                                    if not mapping:
                                        from utils.column_mapper import ColumnMapper
                                        target_columns = multi_agent._get_target_columns(import_type)
                                        fallback_mapping = ColumnMapper.suggest_mapping(
                                            list(df.columns),
                                            target_columns,
                                            df=df,
                                            db=db,
                                            import_type=import_type
                                        )
                                        # Remove entradas 'ignore' do fallback
                                        mapping = {
                                            source: target
                                            for source, target in fallback_mapping.items()
                                            if target and target != 'ignore'
                                        }
                                        
                                        if mapping:
                                            st.info(f"ℹ️ Usando mapeamento automático: {len(mapping)} coluna(s) mapeada(s)")
                                        else:
                                            st.warning("⚠️ Mapeamento automático falhou. Criando mapeamento básico por nome...")
                                            # Cria mapeamento básico baseado em nomes de colunas
                                            source_cols = list(df.columns)
                                            target_columns = multi_agent._get_target_columns(import_type)
                                            for src_col in source_cols:
                                                src_lower = str(src_col).lower().strip()
                                                for tgt_col in target_columns:
                                                    tgt_lower = str(tgt_col).lower().strip()
                                                    if src_lower == tgt_lower or src_lower in tgt_lower or tgt_lower in src_lower:
                                                        mapping[src_col] = tgt_col
                                                        break
                                            
                                            if mapping:
                                                st.info(f"✅ Mapeamento básico criado: {len(mapping)} coluna(s)")
                                            else:
                                                st.warning("⚠️ Nenhum mapeamento foi criado. Os dados podem não estar corretamente estruturados.")
                                
                                # Garante que sempre há um mapeamento (mesmo que parcial) antes de normalizar
                                if not mapping:
                                    st.error("❌ Não foi possível criar mapeamento. Verifique as colunas do arquivo.")
                                    raise Exception("Mapeamento não pôde ser criado")
                                
                                with st.spinner("🤖 [Agente 4] Extraindo e formatando valores..."):
                                    normalized_records = multi_agent.agent_extract_and_format(
                                        processed_data, import_type, mapping
                                    )
                                
                                target_columns = multi_agent._get_target_columns(import_type)
                                
                                # Validação: verifica se dados normalizados têm colunas destino
                                missing_cols_found = False
                                for record in normalized_records:
                                    for col in target_columns:
                                        if col not in record:
                                            record[col] = None
                                            missing_cols_found = True
                                
                                # Se faltam colunas, aplica mapeamento direto aos dados originais
                                if missing_cols_found and normalized_records:
                                    st.info("ℹ️ Aplicando mapeamento direto para colunas faltantes...")
                                    for idx, record in enumerate(normalized_records):
                                        if idx < len(processed_data):
                                            original_record = processed_data[idx]
                                            # Aplica mapeamento direto para colunas que faltam
                                            for src_col, tgt_col in mapping.items():
                                                if tgt_col not in record or record.get(tgt_col) is None:
                                                    if src_col in original_record:
                                                        record[tgt_col] = original_record[src_col]
                                
                                # Valida se dados têm pelo menos algumas colunas destino
                                sample_record = normalized_records[0] if normalized_records else {}
                                cols_present = [col for col in target_columns if col in sample_record and sample_record.get(col) is not None]
                                if len(cols_present) == 0:
                                    st.warning("⚠️ Dados normalizados não têm colunas destino. Aplicando mapeamento direto...")
                                    # Aplica mapeamento direto a todos os registros
                                    normalized_records = []
                                    for original_record in processed_data:
                                        new_record = {}
                                        for src_col, tgt_col in mapping.items():
                                            if src_col in original_record:
                                                new_record[tgt_col] = original_record[src_col]
                                        # Garante todas as colunas destino
                                        for col in target_columns:
                                            if col not in new_record:
                                                new_record[col] = None
                                        normalized_records.append(new_record)
                                    st.info(f"✅ Mapeamento direto aplicado a {len(normalized_records)} registro(s)")
                                
                                with st.spinner("🤖 [Agente 5] Validando dados estruturados..."):
                                    validation = multi_agent.agent_validate(normalized_records, import_type)
                                
                                # Validação final: verifica se normalização foi bem-sucedida
                                if not normalized_records:
                                    st.warning("⚠️ Normalização retornou vazio. Usando dados originais com mapeamento direto...")
                                    # Aplica mapeamento direto aos dados originais
                                    normalized_records = []
                                    for original_record in processed_data:
                                        new_record = {}
                                        for src_col, tgt_col in mapping.items():
                                            if src_col in original_record:
                                                new_record[tgt_col] = original_record[src_col]
                                        # Garante todas as colunas destino
                                        for col in target_columns:
                                            if col not in new_record:
                                                new_record[col] = None
                                        normalized_records.append(new_record)
                                
                                # Log final do resultado
                                if normalized_records:
                                    sample = normalized_records[0]
                                    cols_mapped = [col for col in target_columns if col in sample]
                                    st.success(f"✅ Processamento concluído: {len(normalized_records)} registro(s) com {len(cols_mapped)}/{len(target_columns)} colunas destino")
                                
                                normalization_result = {
                                    'normalized_data': normalized_records,
                                    'summary': {
                                        'total_rows_processed': len(processed_data),
                                        'successfully_normalized': len(normalized_records),
                                        'validation': validation,
                                        'mapping_applied': mapping,
                                        'columns_mapped': len(mapping) if mapping else 0
                                    }
                                }
                                
                                processed_data = normalized_records
                                structure_successful = True
                                structure_method = 'multi_agent'
                            else:
                                raise Exception("Multi-agent falhou, usando fallback")
                        elif ai_service.is_available():
                            # Fallback: método antigo (single agent)
                            with st.spinner("🤖 Analisando estrutura origem e estruturando para tabela destino..."):
                                try:
                                    # Prepara análise estrutural do DataFrame
                                    structural_analysis = f"""
Estrutura do arquivo origem:
- Colunas encontradas: {', '.join(df.columns.tolist()) if not df.empty else 'Nenhuma'}
- Número de linhas: {len(df)}
- Tipos de dados detectados:
"""
                                    if not df.empty:
                                        for col in df.columns:
                                            dtype = str(df[col].dtype)
                                            sample_values = df[col].dropna().head(3).tolist()
                                            structural_analysis += f"  - {col}: {dtype} (exemplos: {sample_values})\n"
                                    
                                    # Prepara dados completos para análise
                                    file_data = json.dumps(processed_data, ensure_ascii=False, indent=2, default=str)
                                    
                                    # Cria mapeamento inicial vazio
                                    mapping = {}
                                    
                                    # Usa normalize_data (método antigo)
                                    normalization_result = ai_service.normalize_data(
                                        df,
                                        import_type,
                                        mapping,
                                        structural_analysis=structural_analysis
                                    )
                                    
                                except Exception as e:
                                    error_msg = str(e)
                                    st.warning(f"⚠️ Não foi possível estruturar automaticamente: {error_msg}")
                                    normalization_result = None
                                
                                if normalization_result and 'normalized_data' in normalization_result:
                                    normalized_records = normalization_result['normalized_data']
                                        
                                    # VALIDA E CORRIGE VALORES MONETÁRIOS (importante para strings complexas)
                                    from utils.validators import parse_currency
                                    
                                    # Identifica colunas de valor baseado no tipo de importação
                                    value_columns = []
                                    if import_type in ['transactions', 'bank_statements', 'accounts_payable', 'accounts_receivable']:
                                        value_columns = ['value']
                                    elif import_type == 'contracts':
                                        value_columns = ['service_value', 'displacement_value']
                                    elif import_type == 'financial_investments':
                                        value_columns = ['applied_value', 'redeemed_value', 'yield_value', 'balance']
                                    elif import_type == 'credit_card_invoices':
                                        value_columns = ['value']
                                    elif import_type == 'card_machine_statements':
                                        value_columns = ['gross_value', 'fee', 'net_value']
                                    elif import_type == 'inventory':
                                        value_columns = ['unit_value']
                                    
                                    # Valida e corrige valores em todos os registros normalizados
                                    for record in normalized_records:
                                        for value_col in value_columns:
                                            if value_col in record:
                                                value = record[value_col]
                                                if isinstance(value, str):
                                                    # Tenta extrair valor usando função robusta
                                                    parsed = parse_currency(value)
                                                    if parsed is not None:
                                                        record[value_col] = parsed
                                                    else:
                                                        # Se não conseguiu extrair, tenta converter diretamente
                                                        try:
                                                            record[value_col] = float(value)
                                                        except:
                                                            record[value_col] = None
                                                elif value is not None and not isinstance(value, (int, float)):
                                                    try:
                                                        record[value_col] = float(value)
                                                    except:
                                                        record[value_col] = None
                                    
                                    # Se normalizou apenas uma amostra, aplica padrões ao resto
                                    if len(normalized_records) < len(processed_data):
                                        # Para o resto, mantém estrutura original mas garante colunas corretas
                                        remaining = processed_data[len(normalized_records):]
                                        target_columns = ai_service.get_target_columns(import_type)
                                        
                                        # Tenta aplicar o mesmo padrão de mapeamento aos registros restantes
                                        # Usa o primeiro registro normalizado como referência
                                        if normalized_records:
                                            reference_record = normalized_records[0]
                                            # Para cada registro restante, tenta mapear baseado na estrutura do primeiro
                                            for record in remaining:
                                                new_record = {}
                                                # Copia estrutura do registro de referência
                                                for target_col in target_columns:
                                                    # Tenta encontrar valor correspondente no registro original
                                                    found = False
                                                    for orig_key, orig_value in record.items():
                                                        # Se a chave original mapeia para esta coluna destino
                                                        if target_col in reference_record:
                                                            # Usa o valor original se existir, senão usa None
                                                            if orig_key in record:
                                                                new_record[target_col] = record[orig_key]
                                                                found = True
                                                                break
                                                    if not found:
                                                        new_record[target_col] = None
                                                
                                                # Valida valores monetários no registro restante também
                                                for value_col in value_columns:
                                                    if value_col in new_record:
                                                        value = new_record[value_col]
                                                        if isinstance(value, str):
                                                            parsed = parse_currency(value)
                                                            if parsed is not None:
                                                                new_record[value_col] = parsed
                                                            else:
                                                                try:
                                                                    new_record[value_col] = float(value)
                                                                except:
                                                                    new_record[value_col] = None
                                                
                                                record.clear()
                                                record.update(new_record)
                                        
                                        processed_data = normalized_records + remaining
                                    else:
                                        processed_data = normalized_records
                                    
                                    st.success(f"✅ Dados estruturados para {len(processed_data)} registros")
                                    structure_successful = True
                                    structure_method = 'single_agent'
                                    
                                    # Mostra resumo do mapeamento se disponível
                                    if normalization_result.get('summary', {}).get('mapping_applied'):
                                        mapping_applied = normalization_result['summary']['mapping_applied']
                                        if mapping_applied:
                                            with st.expander("ℹ️ Mapeamento aplicado pela IA", expanded=False):
                                                for orig_col, dest_col in mapping_applied.items():
                                                    st.write(f"`{orig_col}` → `{dest_col}`")
                                else:
                                    # Se normalização falhou, mostra opção manual
                                    st.warning("⚠️ IA não conseguiu estruturar automaticamente. Use a opção manual abaixo.")
                                    normalization_result = None
                        else:
                            # IA não disponível
                            pass
                    except Exception as e:
                        error_msg = str(e)
                        st.warning(f"⚠️ Não foi possível estruturar automaticamente: {error_msg}")
                        
                        # Opção para estruturação manual
                        st.markdown("---")
                        st.subheader("✏️ Estruturação Manual (se necessário)")
                        st.info("💡 Se a IA não conseguiu estruturar automaticamente, você pode mapear manualmente as colunas:")
                        
                        # Mostra colunas origem e destino
                        target_columns = ai_service.get_target_columns(import_type)
                        df_columns = list(df.columns) if not df.empty else []
                        
                        if df_columns and target_columns:
                            structure_method = 'manual'
                            structure_successful = True
                            st.markdown("**Colunas do arquivo origem:**")
                            st.write(", ".join(df_columns))
                            
                            st.markdown("**Colunas da tabela destino:**")
                            st.write(", ".join(target_columns))
                            
                            # Permite mapeamento manual (simplificado por enquanto)
                            st.info("💡 O sistema tentará mapear automaticamente baseado nos nomes. Se necessário, edite os dados na tabela de revisão abaixo.")
                            
                            # Continua com dados originais mas garante colunas destino
                            for record in processed_data:
                                new_record = {}
                                # Tenta mapear automaticamente
                                for df_col in df_columns:
                                    df_col_lower = str(df_col).lower().strip()
                                    for target_col in target_columns:
                                        target_col_lower = str(target_col).lower().strip()
                                        if (df_col_lower == target_col_lower or 
                                            df_col_lower in target_col_lower or 
                                            target_col_lower in df_col_lower):
                                            if df_col in record:
                                                new_record[target_col] = record[df_col]
                                            break
                                # Garante todas as colunas destino
                                for target_col in target_columns:
                                    if target_col not in new_record:
                                        new_record[target_col] = None
                                record.clear()
                                record.update(new_record)
                        else:
                            st.error("❌ Não foi possível identificar colunas origem ou destino.")
                            structure_successful = False
                            st.stop()
                    except Exception as e:
                            st.warning(f"⚠️ Erro ao estruturar dados: {str(e)}")
                            pass
                    finally:
                        db.close()
                    
                    for record in processed_data:
                        record['group_id'] = None
                        record['subgroup_id'] = None
                    
                    # CRÍTICO: Salva cópia profunda dos dados normalizados/mapeados
                    st.session_state.processed_data = [dict(record) for record in processed_data]
                    # Reseta editing_data quando processed_data é atualizado
                    st.session_state.editing_data = [dict(record) for record in processed_data]
                    st.session_state.has_pending_changes = False
                    st.session_state.processed_data_is_structured = structure_successful
                    st.session_state.structure_method = structure_method
                    if structure_successful:
                        st.session_state.last_structure_hash = structure_hash
                    else:
                        st.session_state.pop('last_structure_hash', None)
                else:
                    if 'processed_data' in st.session_state:
                        processed_data = [dict(record) for record in st.session_state.processed_data]
                    else:
                        # Filtra linhas em branco e saldos antes do mapeamento
                        df_filtered = _filter_transaction_rows(df, import_type)
                        rows_before = len(df)
                        rows_after = len(df_filtered)
                        rows_filtered = rows_before - rows_after
                        
                        if rows_filtered > 0:
                            st.info(f"ℹ️ **{rows_filtered} linha(s)** foram filtradas (linhas em branco ou saldos). Processando **{rows_after} transação(ões)** válidas.")
                        
                        processed_data = df_filtered.to_dict('records')
                        for record in processed_data:
                            record['group_id'] = None
                            record['subgroup_id'] = None
                        # Salva cópia profunda
                        st.session_state.processed_data = [dict(record) for record in processed_data]
                        # Reseta editing_data quando processed_data é atualizado
                        st.session_state.editing_data = [dict(record) for record in processed_data]
                        st.session_state.has_pending_changes = False
                        st.session_state.last_structure_hash = structure_hash
                        st.session_state.processed_data_is_structured = False
                
                # Cria summary para compatibilidade
                summary = {
                    'processed': len(processed_data),
                    'original_rows': len(df),
                    'processed_rows': len(processed_data),
                    'import_type': import_type
                }
                
                # Limpa dados do PDF da session state após processar
                if 'pdf_full_data' in st.session_state:
                    del st.session_state['pdf_full_data']
                
                if not processed_data:
                    st.warning("⚠️ Nenhum dado foi processado. Verifique o arquivo.")
                    st.stop()
                
                # Define imported_at para extratos bancários (timestamp atual)
                if import_type == 'bank_statements':
                    current_timestamp = datetime.now(timezone.utc).isoformat()
                    for record in processed_data:
                        record['imported_at'] = current_timestamp
                
                # Exibe estatísticas simplificadas
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Registros Processados", len(processed_data))
                with col2:
                    st.metric("Status", "✅ Pronto")
                
                st.markdown("---")
                st.subheader("✏️ Revisão e Edição")
                
                # CRÍTICO: Sempre usa os dados do session_state se disponíveis
                # Os dados normalizados foram salvos em st.session_state.processed_data após o mapeamento
                if 'processed_data' in st.session_state and st.session_state.processed_data:
                    # Sempre usa dados do session_state (contêm dados normalizados/mapeados)
                    processed_data = [dict(record) for record in st.session_state.processed_data]
                
                # Configuração de nome do banco (se aplicável)
                if import_type == 'bank_statements':
                    extracted_bank_name = None
                    for record in processed_data:
                        if record.get('bank_name'):
                            extracted_bank_name = record.get('bank_name')
                            break
                    
                    if 'bank_name_override' not in st.session_state:
                        st.session_state.bank_name_override = extracted_bank_name if extracted_bank_name else ""
                    
                    bank_name = st.text_input(
                        "Nome do banco:",
                        value=st.session_state.bank_name_override if st.session_state.bank_name_override else extracted_bank_name if extracted_bank_name else "Banco",
                        key="bank_name_input_config"
                    )
                    st.session_state.bank_name_override = bank_name
                
                # Prepara dados processados (cria uma cópia para não modificar os originais)
                # IMPORTANTE: working_data deve conter os dados normalizados/mapeados
                working_data = [dict(record) for record in processed_data]  # Cópia profunda
                
                # Remove colunas internas se existirem
                for record in working_data:
                    record.pop('original_row', None)
                    # Garante que group_id e subgroup_id não sejam preenchidos
                    record['group_id'] = None
                    record['subgroup_id'] = None
                
                # Aplica nome do banco extraído/editado aos dados se aplicável
                if import_type == 'bank_statements':
                    # Determina qual nome do banco usar (extraído ou editado)
                    bank_name_to_apply = None
                    if 'bank_name_override' in st.session_state and st.session_state.bank_name_override:
                        bank_name_to_apply = st.session_state.bank_name_override
                    elif extracted_bank_name:
                        bank_name_to_apply = extracted_bank_name
                    
                    if bank_name_to_apply:
                        # Aplica o nome do banco a todos os registros que não têm bank_name definido
                        for record in working_data:
                            current_value = record.get('bank_name')
                            if not current_value or (isinstance(current_value, float) and pd.isna(current_value)):
                                record['bank_name'] = bank_name_to_apply
                
                # Inicializa seleção de linhas
                file_hash = f"{uploaded_file.name}_{len(working_data)}_{import_type}"
                if 'last_file_hash' not in st.session_state or st.session_state.last_file_hash != file_hash:
                    # Cria cópia profunda para o session state
                    st.session_state.processed_data = [dict(record) for record in working_data]
                    # Reseta editing_data quando processed_data é atualizado (novo arquivo)
                    st.session_state.editing_data = [dict(record) for record in working_data]
                    st.session_state.has_pending_changes = False
                    st.session_state.selected_rows = set(range(len(working_data)))
                    st.session_state.last_file_hash = file_hash
                elif 'processed_data' not in st.session_state:
                    # Cria cópia profunda para o session state
                    st.session_state.processed_data = [dict(record) for record in working_data]
                    # Reseta editing_data quando processed_data é atualizado
                    st.session_state.editing_data = [dict(record) for record in working_data]
                    st.session_state.has_pending_changes = False
                    st.session_state.selected_rows = set(range(len(working_data)))
                
                st.markdown("---")
                st.subheader("📥 Importação")
                
                # Garante que selected_rows está inicializado
                if 'selected_rows' not in st.session_state:
                    st.session_state.selected_rows = set(range(len(st.session_state.processed_data))) if 'processed_data' in st.session_state else set()
                
                # Botão de importar
                import_btn = st.button(
                    "📥 Importar Dados",
                    key="import_selected_data",
                    width='stretch',
                    disabled=len(st.session_state.selected_rows) == 0,
                    type="primary"
                )
                
                if import_btn and len(st.session_state.selected_rows) > 0:
                    # Garante que selected_rows está atualizado e válido
                    selected_rows = st.session_state.get('selected_rows', set())
                    if not selected_rows or len(selected_rows) == 0:
                        st.error("❌ **Nenhuma linha selecionada.** Por favor, selecione pelo menos uma linha para importar.")
                        st.stop()
                    
                    # Filtra apenas linhas selecionadas - validação rigorosa
                    selected_indices = sorted([int(i) for i in selected_rows if isinstance(i, (int, str)) and str(i).isdigit()])
                    
                    # Valida que os índices estão dentro do range válido
                    max_index = len(st.session_state.processed_data) - 1
                    selected_indices = [i for i in selected_indices if 0 <= i <= max_index]
                    
                    if not selected_indices:
                        st.error("❌ **Nenhuma linha válida selecionada.** Por favor, selecione linhas válidas para importar.")
                        st.stop()
                    
                    # Filtra apenas linhas selecionadas
                    data_to_import = [st.session_state.processed_data[i] for i in selected_indices]
                    import_df = pd.DataFrame(data_to_import)
                    
                    # Container para mostrar progresso de importação
                    import_progress_container = st.empty()
                    
                    def update_import_progress(message):
                        import_progress_container.info(f"💾 **Importando:** {message}")
                    
                    # Importa dados com feedback de progresso
                    with st.spinner("💾 Preparando importação..."):
                        imported_count = 0
                        import_result = None  # Para armazenar resultado de bank_statements
                        
                        # A IA já classificou cada linha com group_id e subgroup_id
                        # Passamos None para group_id e subgroup_id para forçar uso da classificação por linha
                        if import_type == 'transactions':
                            imported_count = ImportService.import_transactions(
                                db, client_id, import_df, 'imported', uploaded_file.name,
                                None, None, progress_callback=update_import_progress
                            )
                        
                        elif import_type == 'bank_statements':
                            import_result = ImportService.import_bank_statements(
                                db, client_id, import_df, bank_name, uploaded_file.name,
                                None, None, progress_callback=update_import_progress
                            )
                            imported_count = import_result.get('statements', 0)
                            transactions_created = import_result.get('transactions', 0)
                            if imported_count > 0:
                                st.success(f"✅ {imported_count} extrato(s) importado(s) e {transactions_created} transação(ões) criada(s) automaticamente!")
                        
                        elif import_type == 'contracts':
                            imported_count = ImportService.import_contracts(
                                db, client_id, import_df, None, None,
                                progress_callback=update_import_progress
                            )
                        
                        elif import_type == 'accounts_payable':
                            imported_count = ImportService.import_accounts_payable(
                                db, client_id, import_df, None, None,
                                progress_callback=update_import_progress
                            )
                        
                        elif import_type == 'accounts_receivable':
                            imported_count = ImportService.import_accounts_receivable(
                                db, client_id, import_df, None, None,
                                progress_callback=update_import_progress
                            )
                        elif import_type == 'financial_investments':
                            imported_count = ImportService.import_financial_investments(
                                db, client_id, import_df, None, None,
                                progress_callback=update_import_progress
                            )
                        elif import_type == 'credit_card_invoices':
                            imported_count = ImportService.import_credit_card_invoices(
                                db, client_id, import_df, None, None,
                                progress_callback=update_import_progress
                            )
                        elif import_type == 'card_machine_statements':
                            imported_count = ImportService.import_card_machine_statements(
                                db, client_id, import_df, None, None,
                                progress_callback=update_import_progress
                            )
                        elif import_type == 'inventory':
                            imported_count = ImportService.import_inventory(
                                db, client_id, import_df, None, None,
                                progress_callback=update_import_progress
                            )
                    
                    # Limpa o container de progresso após importação
                    import_progress_container.empty()
                    
                    # Armazena resultado da importação no session_state para notificações
                    if import_type == 'bank_statements' and imported_count > 0:
                        transactions_created = import_result.get('transactions', 0)
                        st.session_state.import_result = {
                            'status': 'success',
                            'import_type': import_type,
                            'count': imported_count,
                            'transactions_created': transactions_created,
                            'message': f"{imported_count} extrato(s) importado(s) e {transactions_created} transação(ões) criada(s) automaticamente!",
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        }
                        # Mensagem já foi exibida acima
                    elif import_type != 'bank_statements' and imported_count > 0:
                        st.session_state.import_result = {
                            'status': 'success',
                            'import_type': import_type,
                            'count': imported_count,
                            'message': f"{imported_count} registro(s) importado(s) com sucesso!",
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        }
                        st.success(f"✅ {imported_count} registro(s) importado(s) com sucesso!")
                        st.balloons()
                    elif imported_count == 0:
                        st.session_state.import_result = {
                            'status': 'warning',
                            'import_type': import_type,
                            'count': 0,
                            'message': "⚠️ Nenhum registro foi importado. Verifique os dados.",
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        }
                        st.warning("⚠️ Nenhum registro foi importado. Verifique os dados.")
                    
                    # Limpa estado após importação bem-sucedida
                    if (import_type == 'bank_statements' and imported_count > 0) or (import_type != 'bank_statements' and imported_count > 0):
                        if 'processed_data' in st.session_state:
                            del st.session_state.processed_data
                        if 'selected_rows' in st.session_state:
                            del st.session_state.selected_rows
                        if 'last_file_hash' in st.session_state:
                            del st.session_state.last_file_hash
                        if 'bank_name_override' in st.session_state:
                            del st.session_state.bank_name_override
            finally:
                db.close()
        
    type_names = {
        'transactions': '💳 Transações Financeiras',
        'bank_statements': '🏦 Extratos Bancários',
        'contracts': '📝 Contratos/Eventos',
        'accounts_payable': '💸 Contas a Pagar',
        'accounts_receivable': '💰 Contas a Receber',
        'financial_investments': '📈 Investimentos Financeiros',
        'credit_card_invoices': '💳 Faturas de Cartão',
        'card_machine_statements': '🏪 Extratos de Máquina de Cartão',
        'inventory': '📦 Controle de Estoque'
    }
    
    # IMPORTANTE: Sempre usa os dados do session_state se disponíveis (contêm dados normalizados/mapeados)
    if 'processed_data' in st.session_state and st.session_state.processed_data:
        processed_data = [dict(record) for record in st.session_state.processed_data]
    elif not processed_data:
        st.error("❌ Nenhum dado processado encontrado. Por favor, reprocesse o arquivo.")
        st.stop()
    
    # Normaliza dados
    # Garante que todos os registros têm group_id e subgroup_id como None
    for record in processed_data:
        record['group_id'] = None
        record['subgroup_id'] = None
    
    # Inicializa seleção
    if 'selected_rows' not in st.session_state:
        st.session_state.selected_rows = set(range(len(processed_data)))
    
    # Calcula valor total apenas dos registros selecionados
    # Usa função robusta para extrair valores mesmo de strings complexas
    from utils.validators import parse_currency
    
    selected_data = [processed_data[i] for i in st.session_state.selected_rows if 0 <= i < len(processed_data)]
    total_value_selected = 0.0
    for r in selected_data:
        value = r.get('value')
        if value is not None and pd.notna(value):
            # Tenta converter para float diretamente
            if isinstance(value, (int, float)):
                total_value_selected += float(value)
            elif isinstance(value, str):
                # Usa função robusta para extrair valor de string
                parsed_value = parse_currency(value)
                if parsed_value is not None:
                    total_value_selected += parsed_value
    
    # Métricas em cards mais limpos
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Registros", f"{len(processed_data):,}".replace(',', '.'))
    with col2:
        import_type = summary.get('import_type', 'transactions')
        type_display = type_names.get(import_type, import_type)
        type_short = type_display.split(' ')[-1] if ' ' in type_display else type_display
        st.metric("📋 Tipo", type_short)
    with col3:
        if 'bank_name' in summary and summary.get('bank_name'):
            st.metric("🏦 Banco", summary.get('bank_name', '-'))
        else:
            st.metric("✓ Status", "Pronto")
    with col4:
        if total_value_selected != 0:
            from utils.formatters import format_currency
            st.metric("💰 Valor Total (Selecionados)", format_currency(total_value_selected))
        else:
            st.metric("✓ Classificado", "Sim")
    
    # Controles de seleção simplificados
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("✅ Todas", width='stretch', key="select_all_review"):
            st.session_state.selected_rows = set(range(len(processed_data)))
            st.rerun()
    
    with col2:
        if st.button("❌ Nenhuma", width='stretch', key="deselect_all_review"):
            st.session_state.selected_rows = set()
            st.rerun()
        
    with col3:
        total_selected = len(st.session_state.selected_rows)
        st.caption(f"📌 {total_selected} de {len(processed_data)} selecionados")
    
    # Prepara dados para edição
    db_edit = SessionLocal()
    try:
        # Busca grupos e subgrupos do cliente para seleção manual
        groups = db_edit.query(Group).filter(Group.client_id == client_id).order_by(Group.name).all()
        groups_dict = {g.id: g.name for g in groups}
        groups_options = [None] + [g.id for g in groups]  # None para "Sem grupo"
        groups_labels = ["-"] + [g.name for g in groups]
        
        # Cria mapeamento de grupos para subgrupos
        subgroups_by_group = {}
        for group in groups:
            subgroups = db_edit.query(Subgroup).filter(Subgroup.group_id == group.id).order_by(Subgroup.name).all()
            subgroups_by_group[group.id] = {
                'options': [None] + [sg.id for sg in subgroups],
                'labels': ["-"] + [sg.name for sg in subgroups],
                'mapping': {sg.id: sg.name for sg in subgroups}
            }
        
        group_mapping, subgroup_mapping = _get_group_subgroup_names_mapping(db_edit, client_id)
    finally:
        db_edit.close()
    
    # CRÍTICO: Sempre usa dados do session_state se disponíveis (contêm dados normalizados/mapeados)
    if 'processed_data' in st.session_state and st.session_state.processed_data:
        processed_data = [dict(record) for record in st.session_state.processed_data]
    
    # Inicializa editing_data a partir de processed_data se não existir
    # editing_data armazena dados sendo editados (não confirmados)
    if 'editing_data' not in st.session_state or not st.session_state.editing_data:
        # Cria cópia profunda dos dados processados para edição
        st.session_state.editing_data = [dict(record) for record in processed_data]
        st.session_state.has_pending_changes = False
    
    # Usa editing_data para preparar dados de edição
    editing_data = st.session_state.editing_data
    
    edit_data = []
    for idx, row in enumerate(editing_data):
        row_copy = row.copy()
        # Garante que _select seja sempre boolean (True/False), nunca string ou NaN
        # Usa selected_rows do session_state ou inicializa com todos selecionados
        if 'selected_rows' not in st.session_state:
            st.session_state.selected_rows = set(range(len(editing_data)))
        row_copy['_select'] = bool(idx in st.session_state.selected_rows)
        row_copy['_row_num'] = idx + 1
        edit_data.append(row_copy)
    
    # Adiciona nomes de grupos e subgrupos (para exibição)
    edit_data = _add_group_subgroup_names_to_data(edit_data, group_mapping, subgroup_mapping)
    edit_df = pd.DataFrame(edit_data)
    
    # Configura colunas para edição
    display_cols = ['_row_num', '_select']
    
    # Adiciona outras colunas (exceto group_id e subgroup_id que serão editáveis)
    for col in edit_df.columns:
        if col not in ['_row_num', '_select', 'group_id', 'subgroup_id', 'group_name', 'subgroup_name']:
            display_cols.append(col)
    
    # Adiciona group_id e subgroup_id como colunas editáveis
    if 'group_id' not in edit_df.columns:
        edit_df['group_id'] = None
    if 'subgroup_id' not in edit_df.columns:
        edit_df['subgroup_id'] = None
    
    display_cols.append('group_id')
    display_cols.append('subgroup_id')
    
    edit_df = edit_df[[c for c in display_cols if c in edit_df.columns]]
    
    # Configura colunas editáveis
    column_config = {
        "_row_num": st.column_config.NumberColumn("Linha", width="small", disabled=True),
        "_select": st.column_config.CheckboxColumn("Importar", width="small"),
    }
    
    # Configura group_id como SelectboxColumn editável
    if groups:
        column_config['group_id'] = st.column_config.SelectboxColumn(
            "Grupo",
            options=groups_options,
            format_func=lambda x: groups_dict.get(x, "-") if x is not None and x in groups_dict else "-",
            width="medium"
        )
    else:
        column_config['group_id'] = st.column_config.NumberColumn("Grupo", width="medium", disabled=True)
    
    # Configura subgroup_id como SelectboxColumn editável
    # Mostra todos os subgrupos (o processamento pós-edição garantirá os relacionamentos corretos)
    all_subgroups = []
    all_subgroups_labels = ["-"]
    all_subgroups_mapping = {}
    for group_id, subs_data in subgroups_by_group.items():
        for sg_id, sg_name in subs_data['mapping'].items():
            if sg_id not in all_subgroups:
                all_subgroups.append(sg_id)
                all_subgroups_labels.append(sg_name)
                all_subgroups_mapping[sg_id] = sg_name
    
    if all_subgroups:
        subgroup_options = [None] + all_subgroups
        column_config['subgroup_id'] = st.column_config.SelectboxColumn(
            "Subgrupo",
            options=subgroup_options,
            format_func=lambda x: all_subgroups_mapping.get(x, "-") if x is not None and x in all_subgroups_mapping else "-",
            width="medium",
            help="💡 Dica: Selecione um subgrupo e o grupo será identificado automaticamente. Ou selecione o grupo primeiro."
        )
    else:
        column_config['subgroup_id'] = st.column_config.NumberColumn("Subgrupo", width="medium", disabled=True)
    
    # Adiciona configuração para campos comuns
    if 'date' in edit_df.columns:
        try:
            edit_df['date'] = pd.to_datetime(edit_df['date'], errors='coerce')
            column_config["date"] = st.column_config.DateColumn("Data", format="YYYY-MM-DD")
        except:
            column_config["date"] = st.column_config.TextColumn("Data")
    
    if 'value' in edit_df.columns:
        try:
            edit_df['value'] = pd.to_numeric(edit_df['value'], errors='coerce')
            column_config["value"] = st.column_config.NumberColumn("Valor", format="%.2f")
        except:
            column_config["value"] = st.column_config.TextColumn("Valor")
    
    if 'description' in edit_df.columns:
        column_config["description"] = st.column_config.TextColumn("Descrição", width="large")
    
    if 'bank_name' in edit_df.columns:
        column_config["bank_name"] = st.column_config.TextColumn("Banco", width="medium")
    
    # Cria mapeamento reverso: subgrupo -> grupo
    subgroup_to_group = {}
    for group_id, subs_data in subgroups_by_group.items():
        for sg_id in subs_data['mapping'].keys():
            subgroup_to_group[sg_id] = group_id
    
    # Exibe tabela editável única
    edited_df = st.data_editor(
        edit_df,
        column_config=column_config,
        hide_index=True,
        width='stretch',
        num_rows="fixed",
        height=min(600, max(400, len(edit_df) * 40)),
        key="data_editor_import"
    )
    
    # Armazena edited_df em editing_data temporariamente (não confirma ainda)
    # Isso permite que o usuário faça múltiplas edições antes de aplicar
    # A confirmação só acontece quando o botão "Aplicar Alterações" for clicado
    
    # Verifica se há alterações pendentes comparando edited_df com edit_df
    # Usa uma comparação mais robusta que não depende de equals (que pode falhar com tipos diferentes)
    has_changes = False
    try:
        # Compara valores principais (não estrutura completa)
        if len(edited_df) != len(edit_df):
            has_changes = True
        else:
            # Compara colunas principais que podem ter sido editadas
            key_cols = ['_select', 'group_id', 'subgroup_id', 'date', 'value', 'description']
            for col in key_cols:
                if col in edited_df.columns and col in edit_df.columns:
                    if not edited_df[col].equals(edit_df[col]):
                        has_changes = True
                        break
    except:
        # Se houver erro na comparação, assume que há mudanças
        has_changes = True
    
    if has_changes:
        st.session_state.has_pending_changes = True
    
    # Mostra indicador visual de alterações pendentes
    if st.session_state.get('has_pending_changes', False):
        st.info("⚠️ **Alterações pendentes** - Clique em 'Aplicar Alterações' para confirmar as mudanças.")
    
    # Botões de ação: Aplicar e Descartar
    col_apply, col_discard, col_spacer = st.columns([1, 1, 2])
    
    with col_apply:
        apply_btn = st.button(
            "✅ Aplicar Alterações",
            key="apply_changes_btn",
            type="primary",
            disabled=not st.session_state.get('has_pending_changes', False),
            use_container_width=True
        )
    
    with col_discard:
        discard_btn = st.button(
            "❌ Descartar Alterações",
            key="discard_changes_btn",
            disabled=not st.session_state.get('has_pending_changes', False),
            use_container_width=True
        )
    
    # Handler do botão "Descartar Alterações"
    if discard_btn:
        # Restaura editing_data a partir de processed_data
        st.session_state.editing_data = [dict(record) for record in processed_data]
        st.session_state.has_pending_changes = False
        st.success("✅ Alterações descartadas. Dados restaurados ao estado anterior.")
        st.rerun()
    
    # Handler do botão "Aplicar Alterações"
    if apply_btn:
        # Processa os dados editados para garantir relacionamentos corretos
        # Esta lógica garante que:
        # 1. Se um subgrupo foi selecionado, identifica e define o grupo automaticamente
        # 2. Se um grupo foi selecionado, valida que o subgrupo pertence a ele
        for idx, row in edited_df.iterrows():
            current_group_id = row.get('group_id')
            current_subgroup_id = row.get('subgroup_id')
            
            # Converte para int se necessário
            if pd.notna(current_group_id) and current_group_id is not None:
                try:
                    current_group_id = int(float(current_group_id))
                except:
                    current_group_id = None
            else:
                current_group_id = None
            
            if pd.notna(current_subgroup_id) and current_subgroup_id is not None:
                try:
                    current_subgroup_id = int(float(current_subgroup_id))
                except:
                    current_subgroup_id = None
            else:
                current_subgroup_id = None
            
            # REGRA 1: Se subgrupo foi selecionado mas grupo não, identifica o grupo do subgrupo
            if current_subgroup_id and not current_group_id:
                if current_subgroup_id in subgroup_to_group:
                    edited_df.at[idx, 'group_id'] = subgroup_to_group[current_subgroup_id]
                    current_group_id = subgroup_to_group[current_subgroup_id]
                    # Feedback visual (será mostrado após rerun)
                    if 'group_subgroup_updates' not in st.session_state:
                        st.session_state.group_subgroup_updates = []
                    st.session_state.group_subgroup_updates.append(f"Linha {row.get('_row_num', idx+1)}: Grupo identificado automaticamente a partir do subgrupo selecionado")
            
            # REGRA 2: Se grupo foi selecionado, valida se o subgrupo pertence a ele
            if current_group_id and current_subgroup_id:
                if current_group_id in subgroups_by_group:
                    if current_subgroup_id not in subgroups_by_group[current_group_id]['mapping']:
                        # Subgrupo não pertence ao grupo, remove o subgrupo
                        edited_df.at[idx, 'subgroup_id'] = None
                        if 'group_subgroup_updates' not in st.session_state:
                            st.session_state.group_subgroup_updates = []
                        st.session_state.group_subgroup_updates.append(f"Linha {row.get('_row_num', idx+1)}: Subgrupo removido (não pertence ao grupo selecionado)")
                else:
                    # Grupo não existe mais, remove ambos
                    edited_df.at[idx, 'group_id'] = None
                    edited_df.at[idx, 'subgroup_id'] = None
            
            # REGRA 3: Se grupo foi removido, remove também o subgrupo
            if not current_group_id and current_subgroup_id:
                edited_df.at[idx, 'subgroup_id'] = None
        
        # Processa dados editados e atualiza processed_data e selected_rows
        new_selection = set()
        updated_data = []
        
        for idx, row in edited_df.iterrows():
            row_num = int(row.get('_row_num', idx + 1)) - 1
            
            # Conversão robusta de _select para boolean
            select_value = row.get('_select', False)
            if isinstance(select_value, str):
                # Trata strings "True", "False", "true", "false", etc.
                select_value = select_value.lower().strip() in ('true', '1', 'yes', 'sim')
            elif pd.isna(select_value) or select_value is None:
                select_value = False
            else:
                # Converte para boolean (trata int, float, etc.)
                select_value = bool(select_value)
            
            if select_value:
                new_selection.add(row_num)
            
            # Atualiza dados (remove colunas internas e nomes, mantém apenas IDs)
            row_dict = row.to_dict()
            row_dict.pop('_row_num', None)
            row_dict.pop('_select', None)
            row_dict.pop('group_name', None)
            row_dict.pop('subgroup_name', None)
            
            # PRESERVA group_id e subgroup_id (converte NaN para None e valida)
            if 'group_id' in row_dict:
                group_id_val = row_dict.get('group_id')
                if pd.isna(group_id_val) or group_id_val is None:
                    row_dict['group_id'] = None
                else:
                    try:
                        group_id_int = int(float(group_id_val))
                        # Valida se o group_id existe na lista de grupos disponíveis
                        if 'groups_dict' in locals() and group_id_int in groups_dict:
                            row_dict['group_id'] = group_id_int
                        else:
                            # Se groups_dict não está disponível, aceita o valor
                            row_dict['group_id'] = group_id_int
                    except (ValueError, TypeError):
                        row_dict['group_id'] = None
            else:
                row_dict['group_id'] = None
            
            if 'subgroup_id' in row_dict:
                subgroup_id_val = row_dict.get('subgroup_id')
                if pd.isna(subgroup_id_val) or subgroup_id_val is None:
                    row_dict['subgroup_id'] = None
                else:
                    try:
                        subgroup_id_int = int(float(subgroup_id_val))
                        # Valida se o subgroup_id existe (se all_subgroups_mapping estiver disponível)
                        if 'all_subgroups_mapping' in locals() and subgroup_id_int in all_subgroups_mapping:
                            # Valida se o subgrupo pertence ao grupo selecionado (se houver)
                            group_id_selected = row_dict.get('group_id')
                            if group_id_selected and 'subgroups_by_group' in locals() and group_id_selected in subgroups_by_group:
                                if subgroup_id_int in subgroups_by_group[group_id_selected]['mapping']:
                                    row_dict['subgroup_id'] = subgroup_id_int
                                else:
                                    # Subgrupo não pertence ao grupo selecionado, remove
                                    row_dict['subgroup_id'] = None
                            else:
                                # Aceita o subgrupo se não houver validação de grupo
                                row_dict['subgroup_id'] = subgroup_id_int
                        else:
                            # Se all_subgroups_mapping não está disponível, aceita o valor
                            row_dict['subgroup_id'] = subgroup_id_int
                    except (ValueError, TypeError):
                        row_dict['subgroup_id'] = None
            else:
                row_dict['subgroup_id'] = None
            
            # Converte datas
            if 'date' in row_dict and pd.notna(row_dict.get('date')):
                if isinstance(row_dict['date'], pd.Timestamp):
                    row_dict['date'] = row_dict['date'].strftime('%Y-%m-%d')
            
            # Converte valores
            for col in ['value', 'balance']:
                if col in row_dict and pd.notna(row_dict.get(col)):
                    try:
                        row_dict[col] = float(row_dict[col])
                    except:
                        pass
            
            updated_data.append(row_dict)
        
        # Atualiza estado confirmado (processed_data e selected_rows)
        st.session_state.selected_rows = new_selection
        st.session_state.processed_data = updated_data
        # Atualiza editing_data para refletir as mudanças confirmadas
        st.session_state.editing_data = [dict(record) for record in updated_data]
        st.session_state.has_pending_changes = False
        
        st.success(f"✅ Alterações aplicadas com sucesso! {len(new_selection)} registro(s) selecionado(s) para importação.")
        st.rerun()
    
    # Se não há botão aplicado, apenas mostra feedback se houver atualizações automáticas
    if 'group_subgroup_updates' in st.session_state and st.session_state.group_subgroup_updates:
        for update_msg in st.session_state.group_subgroup_updates:
            st.info(update_msg)
        st.session_state.group_subgroup_updates = []
    
    st.markdown("---")
    
    # Garante que selected_rows está inicializado
    if 'selected_rows' not in st.session_state:
        st.session_state.selected_rows = set(range(len(processed_data))) if processed_data else set()
    
    # Configurações específicas por tipo
    import_type = summary.get('import_type', 'transactions')
    bank_name = "Banco"
    if import_type == 'bank_statements':
        bank_name = st.session_state.get('bank_name_override', summary.get('bank_name', 'Banco'))
    
    # Botão de importar
    col1, col2 = st.columns([2, 1])
    with col1:
        import_btn = st.button(
            "📥 Importar Dados",
            key="import_data_final",
            width='stretch',
            disabled=len(st.session_state.selected_rows) == 0,
            type="primary"
        )
    with col2:
        total_selected = len(st.session_state.selected_rows)
        st.caption(f"{total_selected} selecionado(s)")
    
    if import_btn and len(st.session_state.selected_rows) > 0:
        # Garante que selected_rows está atualizado e válido
        selected_rows = st.session_state.get('selected_rows', set())
        if not selected_rows or len(selected_rows) == 0:
            st.error("❌ **Nenhuma linha selecionada.** Por favor, selecione pelo menos uma linha para importar.")
            st.stop()
        
        # Filtra apenas linhas selecionadas - validação rigorosa
        selected_indices = sorted([int(i) for i in selected_rows if isinstance(i, (int, str)) and str(i).isdigit()])
        
        # Valida que os índices estão dentro do range válido
        max_index = len(st.session_state.processed_data) - 1
        selected_indices = [i for i in selected_indices if 0 <= i <= max_index]
        
        if not selected_indices:
            st.error("❌ **Nenhuma linha válida selecionada.** Por favor, selecione linhas válidas para importar.")
            st.stop()
        
        # Filtra apenas linhas selecionadas
        data_to_import = [st.session_state.processed_data[i] for i in selected_indices]
        import_df = pd.DataFrame(data_to_import)
        
        # Valida se há dados para importar
        if import_df.empty:
            st.error("❌ **Nenhum dado válido para importar.** Verifique se os registros selecionados contêm dados válidos.")
            st.stop()
        
        # Debug: mostra quantas linhas foram selecionadas
        st.info(f"ℹ️ **Importando {len(selected_indices)} de {len(st.session_state.processed_data)} registro(s) selecionado(s).**")
        
        # Prepara dados para importação - garante formato correto
        # Converte datas para string no formato esperado
        if 'date' in import_df.columns:
            def format_date_for_import(val):
                if pd.isna(val) or val is None:
                    return None
                if isinstance(val, pd.Timestamp):
                    return val.strftime('%Y-%m-%d')
                if isinstance(val, datetime):
                    return val.strftime('%Y-%m-%d')
                if isinstance(val, str):
                    # Se já é string, tenta converter para garantir formato
                    try:
                        val = val.strip()
                        if not val:
                            return None
                        if 'T' in val or ' ' in val:
                            # Remove hora se houver
                            val = val.split('T')[0].split(' ')[0]
                        return val
                    except:
                        return str(val) if val else None
                return str(val) if val else None
            
            import_df['date'] = import_df['date'].apply(format_date_for_import)
        
        # Garante que valores são numéricos ou strings válidas
        if 'value' in import_df.columns:
            def format_value_for_import(val):
                if pd.isna(val) or val is None:
                    return None
                if isinstance(val, (int, float)):
                    # Converte para string formatada para o parser processar
                    return str(float(val))
                if isinstance(val, str):
                    # Mantém como string para o parser processar
                    val = val.strip()
                    return val if val else None
                return str(val) if val else None
            
            import_df['value'] = import_df['value'].apply(format_value_for_import)
        
        # Remove linhas que não têm data OU valor (campos obrigatórios)
        required_cols = []
        if 'date' in import_df.columns:
            required_cols.append('date')
        if 'value' in import_df.columns:
            required_cols.append('value')
        
        if required_cols:
            # Filtra apenas linhas com todos os campos obrigatórios preenchidos
            mask = pd.Series([True] * len(import_df))
            for col in required_cols:
                mask = mask & import_df[col].notna()
            
            rows_before = len(import_df)
            import_df = import_df[mask].copy()
            rows_after = len(import_df)
            
            if rows_before > rows_after:
                st.warning(f"⚠️ {rows_before - rows_after} registro(s) foram removidos por falta de dados obrigatórios (data ou valor).")
            
            if import_df.empty:
                st.error("❌ **Nenhum registro válido para importar.** Todos os registros selecionados estão faltando dados obrigatórios (data ou valor).")
                st.stop()
        
        
        # Container para progresso
        import_progress_container = st.empty()
        
        def update_import_progress(message):
            import_progress_container.info(f"💾 **Importando:** {message}")
        
        # Importa dados
        db = SessionLocal()
        try:
            with st.spinner("💾 Preparando importação..."):
                imported_count = 0
                import_result = None
                import_type = summary.get('import_type', 'transactions')
                
                if import_type == 'transactions':
                    imported_count = ImportService.import_transactions(
                        db, client_id, import_df, 'imported', uploaded_file.name,
                        None, None, progress_callback=update_import_progress
                    )
                
                elif import_type == 'bank_statements':
                    import_result = ImportService.import_bank_statements(
                        db, client_id, import_df, bank_name, uploaded_file.name,
                        None, None, progress_callback=update_import_progress
                    )
                    imported_count = import_result.get('statements', 0)
                    transactions_created = import_result.get('transactions', 0)
                
                elif import_type == 'contracts':
                    imported_count = ImportService.import_contracts(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif import_type == 'accounts_payable':
                    imported_count = ImportService.import_accounts_payable(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif import_type == 'accounts_receivable':
                    imported_count = ImportService.import_accounts_receivable(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif import_type == 'financial_investments':
                    imported_count = ImportService.import_financial_investments(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif import_type == 'credit_card_invoices':
                    imported_count = ImportService.import_credit_card_invoices(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif import_type == 'card_machine_statements':
                    imported_count = ImportService.import_card_machine_statements(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif import_type == 'inventory':
                    imported_count = ImportService.import_inventory(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
            
            import_progress_container.empty()
            
            # Container para mensagens de importação (logo abaixo do botão)
            import_message_container = st.container()
            
            with import_message_container:
                # Armazena resultado
                import_type = summary.get('import_type', 'transactions')
                if import_type == 'bank_statements' and imported_count > 0:
                    transactions_created = import_result.get('transactions', 0)
                    st.session_state.import_result = {
                        'status': 'success',
                        'import_type': import_type,
                        'count': imported_count,
                        'transactions_created': transactions_created,
                        'message': f"{imported_count} extrato(s) importado(s) e {transactions_created} transação(ões) criada(s)!",
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    st.success(f"✅ **{imported_count} extrato(s) importado(s) e {transactions_created} transação(ões) criada(s)!**")
                    st.balloons()
                    
                    # Botão para finalizar importação
                    if st.button("✅ Finalizar Importação", key="finish_import_3", type="primary", width='stretch'):
                        # Limpa estado após importação bem-sucedida
                        if 'processed_data' in st.session_state:
                            del st.session_state.processed_data
                        if 'selected_rows' in st.session_state:
                            del st.session_state.selected_rows
                        if 'processed_file_hash' in st.session_state:
                            del st.session_state.processed_file_hash
                        if 'bank_name_override' in st.session_state:
                            del st.session_state.bank_name_override
                        if 'import_result' in st.session_state:
                            del st.session_state.import_result
                        st.rerun()
                elif imported_count > 0:
                    st.session_state.import_result = {
                        'status': 'success',
                        'import_type': import_type,
                        'count': imported_count,
                        'message': f"{imported_count} registro(s) importado(s) com sucesso!",
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    st.success(f"✅ **{imported_count} registro(s) importado(s) com sucesso!**")
                    st.balloons()
                    
                    # Botão para finalizar importação
                    if st.button("✅ Finalizar Importação", key="finish_import_4", type="primary", width='stretch'):
                        # Limpa estado após importação bem-sucedida
                        if 'processed_data' in st.session_state:
                            del st.session_state.processed_data
                        if 'selected_rows' in st.session_state:
                            del st.session_state.selected_rows
                        if 'processed_file_hash' in st.session_state:
                            del st.session_state.processed_file_hash
                        if 'bank_name_override' in st.session_state:
                            del st.session_state.bank_name_override
                        if 'import_result' in st.session_state:
                            del st.session_state.import_result
                        st.rerun()
                else:
                    st.error("❌ **Nenhum registro foi importado.**")
                    
                    # Mostra informações de debug
                    with st.expander("🔍 Detalhes do problema", expanded=True):
                        st.write(f"**Registros selecionados:** {len(st.session_state.selected_rows)}")
                        import_type = summary.get('import_type', 'transactions')
                        st.write(f"**Tipo de importação:** {import_type}")
                        
                        # Verifica problemas comuns
                        issues = []
                        if 'date' in import_df.columns:
                            date_valid = import_df['date'].notna().sum()
                            if date_valid == 0:
                                issues.append("❌ Nenhuma data válida encontrada")
                            elif date_valid < len(import_df):
                                issues.append(f"⚠️ Apenas {date_valid} de {len(import_df)} registros têm data válida")
                        
                        if 'value' in import_df.columns:
                            value_valid = import_df['value'].notna().sum()
                            if value_valid == 0:
                                issues.append("❌ Nenhum valor válido encontrado")
                            elif value_valid < len(import_df):
                                issues.append(f"⚠️ Apenas {value_valid} de {len(import_df)} registros têm valor válido")
                        
                        if issues:
                            st.write("**Problemas identificados:**")
                            for issue in issues:
                                st.write(f"- {issue}")
                        else:
                            st.write("**Possíveis causas:**")
                            st.write("- Os dados não foram parseados corretamente pelo ImportService")
                            st.write("- Erro na validação de grupos/subgrupos")
                            st.write("- Dados duplicados que foram ignorados")
                            st.write("- Erro silencioso durante o processamento")
                    
                    st.info("💡 Verifique os dados na tabela e corrija campos obrigatórios (data e valor) antes de importar novamente.")
    
        except Exception as e:
            st.error(f"❌ Erro ao importar: {str(e)}")
            st.exception(e)
        finally:
            db.close()

else:
    st.info("💡 Faça upload do arquivo e o sistema processará automaticamente. Formatos suportados: CSV, Excel, PDF, Imagens, OFX.")





























