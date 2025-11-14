"""
Página de Importação de Dados
"""
import streamlit as st
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.parser_service import ParserService
from services.import_service import ImportService
from services.ai_service import AIService
from services.data_processor import DataProcessor
from utils.column_mapper import ColumnMapper
from models.client import Client
from models.group import Group, Subgroup

st.set_page_config(page_title="Importação de Dados", page_icon="📥", layout="wide")

# Verifica autenticação
AuthService.init_session_state()
AuthService.require_auth()


def show_sidebar():
    """Mostra a sidebar de navegação"""
    with st.sidebar:
        st.title("📊 Sistema Contábil")
        user = AuthService.get_current_user()
        st.markdown(f"**Usuário:** {user['username']}")
        st.markdown(f"**Perfil:** {user['role'].title()}")
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            AuthService.logout()
            st.rerun()


show_sidebar()

st.title("📥 Importação de Dados")
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
        st.info(f"📌 Importando dados para: **{client.name}**")
finally:
    db.close()

# Upload de arquivo
st.subheader("1️⃣ Faça Upload do Arquivo")

uploaded_file = st.file_uploader(
    "Selecione um arquivo (CSV, Excel, PDF, OFX)",
    type=['csv', 'txt', 'xlsx', 'xls', 'pdf', 'ofx'],
    help="O sistema detectará automaticamente o tipo de arquivo"
)

if uploaded_file:
    st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
    
    try:
        # Detecta tipo de arquivo automaticamente
        file_content_preview = uploaded_file.read()
        uploaded_file.seek(0)  # Reset para ler novamente depois
        
        detection_result = ParserService.detect_file_type(file_content_preview, uploaded_file.name)
        detected_type = detection_result.get('type', 'CSV')
        confidence = detection_result.get('confidence', 0.0)
        method = detection_result.get('method', 'unknown')
        reason = detection_result.get('reason', '')
        
        # Exibe tipo detectado
        col1, col2 = st.columns([3, 1])
        with col1:
            type_icons = {
                'CSV': '📄',
                'Excel': '📊',
                'PDF': '📑',
                'OFX': '🏦'
            }
            icon = type_icons.get(detected_type, '📄')
            confidence_percent = int(confidence * 100)
            
            if confidence >= 0.8:
                st.info(f"{icon} **Tipo detectado:** {detected_type} ({confidence_percent}% de confiança)")
            elif confidence >= 0.6:
                st.warning(f"{icon} **Tipo detectado:** {detected_type} ({confidence_percent}% de confiança)")
            else:
                st.warning(f"{icon} **Tipo detectado:** {detected_type} ({confidence_percent}% de confiança - baixa confiança)")
        
        with col2:
            if st.button("✏️ Alterar Tipo", use_container_width=True):
                st.session_state.show_file_type_override = True
                st.rerun()
        
        if reason and confidence < 0.8:
            with st.expander("ℹ️ Detalhes da detecção"):
                st.write(f"**Método:** {method}")
                st.write(f"**Razão:** {reason}")
        
        # Permite override manual se necessário
        file_type = detected_type
        if 'show_file_type_override' in st.session_state and st.session_state.show_file_type_override:
            st.markdown("---")
            st.subheader("✏️ Seleção Manual do Tipo de Arquivo")
            file_type = st.selectbox(
                "Tipo de arquivo:",
                options=['CSV', 'Excel', 'PDF', 'OFX'],
                index=['CSV', 'Excel', 'PDF', 'OFX'].index(detected_type) if detected_type in ['CSV', 'Excel', 'PDF', 'OFX'] else 0,
                key="manual_file_type"
            )
            if st.button("✅ Confirmar Tipo", use_container_width=True):
                st.session_state.detected_file_type = file_type
                st.session_state.show_file_type_override = False
                st.rerun()
            
            if 'detected_file_type' in st.session_state:
                file_type = st.session_state.detected_file_type
        
        # Parse do arquivo
        df = None
        
        if file_type == 'CSV':
            file_content = uploaded_file.read()
            delimiter = ParserService.detect_delimiter(file_content)
            
            col1, col2 = st.columns(2)
            with col1:
                encoding = st.selectbox("Encoding:", ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252'])
            with col2:
                delimiter = st.selectbox("Delimitador:", [',', ';', '\t', '|'], 
                                        index=[',', ';', '\t', '|'].index(delimiter))
            
            df = ParserService.parse_csv(file_content, encoding, delimiter)
        
        elif file_type == 'Excel':
            file_content = uploaded_file.read()
            sheets = ParserService.get_excel_sheets(file_content)
            
            if len(sheets) > 1:
                col1, col2 = st.columns(2)
                with col1:
                    read_all = st.checkbox("📋 Ler todas as abas", value=False, 
                                          help="Se marcado, combina dados de todas as abas em um único arquivo")
                with col2:
                    if not read_all:
                        selected_sheet = st.selectbox("Selecione a planilha:", sheets)
                    else:
                        st.info(f"📊 {len(sheets)} abas serão processadas")
                
                if read_all:
                    df = ParserService.parse_excel(file_content, all_sheets=True)
                    st.success(f"✅ {len(sheets)} abas processadas e combinadas")
                else:
                    df = ParserService.parse_excel(file_content, selected_sheet)
            else:
                df = ParserService.parse_excel(file_content)
        
        elif file_type == 'PDF':
            file_content = uploaded_file.read()
            
            # Tenta extrair usando método completo primeiro
            pdf_data = None
            try:
                pdf_data = ParserService.parse_pdf_complete(file_content)
                df = pdf_data.get('dataframe')
            except Exception as e:
                st.warning(f"⚠️ Aviso ao processar PDF: {str(e)}")
                # Fallback para método simples
                df = ParserService.parse_pdf_to_dataframe(file_content)
            
            if df is None or df.empty:
                # Se não encontrou tabelas, tenta extrair do texto
                if pdf_data and pdf_data.get('full_text'):
                    st.info("ℹ️ Nenhuma tabela estruturada encontrada. Tentando extrair dados do texto...")
                    # A IA processará o texto completo
                    # Cria DataFrame vazio para passar o texto completo via session_state
                    df = pd.DataFrame()
                    st.session_state['pdf_full_data'] = pdf_data
                else:
                    st.error("❌ Não foi possível extrair dados do PDF. Tente converter para CSV ou Excel.")
                    st.stop()
            else:
                # Salva dados completos do PDF para uso pela IA
                if pdf_data:
                    st.session_state['pdf_full_data'] = pdf_data
        
        elif file_type == 'OFX':
            file_content = uploaded_file.read()
            df = ParserService.ofx_to_dataframe(file_content)
            # OFX é sempre extrato bancário
            auto_detected_type = 'bank_statements'
        else:
            auto_detected_type = None
        
        # Limpa estado de override após processar
        if 'show_file_type_override' in st.session_state:
            del st.session_state.show_file_type_override
        if 'detected_file_type' in st.session_state:
            del st.session_state.detected_file_type
        
        if df is not None and not df.empty:
            st.markdown("---")
            st.subheader("2️⃣ Preview dos Dados Originais")
            st.dataframe(df.head(10), use_container_width=True)
            st.success(f"✅ Arquivo carregado com sucesso: **{len(df)} linhas** e **{len(df.columns)} colunas**")
            st.caption(f"📊 Total de linhas: {len(df)} | 📋 Total de colunas: {len(df.columns)}")
            
            # Detecção automática do tipo de dado
            st.markdown("---")
            st.subheader("3️⃣ Tipo de Dado Detectado")
            
            db = SessionLocal()
            try:
                ai_service = AIService(db)
                import_type = None
                detection_result = None
                
                # Se for OFX, já sabemos que é extrato bancário
                if file_type == 'OFX':
                    import_type = 'bank_statements'
                    st.info("🏦 **Tipo detectado automaticamente:** Extratos Bancários (formato OFX)")
                elif ai_service.is_available():
                    # Tenta detectar com IA
                    with st.spinner("🤖 Analisando arquivo para detectar tipo de dado..."):
                        columns = list(df.columns)
                        data_sample = ai_service._prepare_data_sample(df, max_rows=15)
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
                        
                        # Exibe sugestão
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if confidence >= 0.7:
                                st.success(f"🤖 **IA Sugeriu:** {suggested_name}")
                            elif confidence >= 0.5:
                                st.warning(f"🤖 **IA Sugeriu:** {suggested_name}")
                            else:
                                st.info(f"🤖 **IA Sugeriu:** {suggested_name} (baixa confiança)")
                        
                        with col2:
                            st.metric("Confiança", f"{confidence_percent}%")
                        
                        if reasoning:
                            with st.expander("💡 Motivo da detecção"):
                                st.write(reasoning)
                                if key_indicators:
                                    st.write("**Indicadores encontrados:**")
                                    for indicator in key_indicators:
                                        st.write(f"- {indicator}")
                        
                        # Tipos alternativos
                        if alternative_types:
                            with st.expander("📋 Tipos alternativos"):
                                for alt in alternative_types:
                                    alt_name = type_names.get(alt.get('type'), alt.get('type'))
                                    alt_confidence = int(alt.get('confidence', 0) * 100)
                                    st.write(f"- {alt_name} ({alt_confidence}% de confiança)")
                        
                        # Opções de confirmação
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("✅ Confirmar e Continuar", use_container_width=True, type="primary"):
                                import_type = suggested_type
                                st.session_state.detected_import_type = import_type
                                st.rerun()
                        
                        with col_btn2:
                            if st.button("✏️ Alterar Tipo Manualmente", use_container_width=True):
                                st.session_state.show_manual_selection = True
                                st.rerun()
                        
                        # Se já foi confirmado anteriormente, usa o tipo confirmado
                        if 'detected_import_type' in st.session_state:
                            import_type = st.session_state.detected_import_type
                    else:
                        # Erro na detecção, mostra seleção manual
                        st.warning(f"⚠️ Não foi possível detectar automaticamente. Erro: {detection_result.get('error', 'Desconhecido')}")
                        st.session_state.show_manual_selection = True
                else:
                    # IA não disponível, mostra seleção manual
                    st.info("ℹ️ IA não configurada. Selecione o tipo de dado manualmente.")
                    st.session_state.show_manual_selection = True
                
                # Seleção manual (se necessário ou se usuário escolheu)
                if 'show_manual_selection' in st.session_state and st.session_state.show_manual_selection:
                    st.markdown("---")
                    st.subheader("✏️ Seleção Manual do Tipo de Dado")
                    import_type = st.selectbox(
                        "Tipo de dado:",
                        options=['transactions', 'bank_statements', 'contracts', 'accounts_payable', 'accounts_receivable',
                                'financial_investments', 'credit_card_invoices', 'card_machine_statements', 'inventory'],
                        format_func=lambda x: {
                            'transactions': '💳 Transações Financeiras',
                            'bank_statements': '🏦 Extratos Bancários',
                            'contracts': '📝 Contratos/Eventos',
                            'accounts_payable': '💸 Contas a Pagar',
                            'accounts_receivable': '💰 Contas a Receber',
                            'financial_investments': '📈 Extratos de Aplicações Financeiras',
                            'credit_card_invoices': '💳 Faturas de Cartão de Crédito',
                            'card_machine_statements': '🏪 Extratos de Máquina de Cartão',
                            'inventory': '📦 Controle de Estoque'
                        }[x],
                        key="manual_import_type"
                    )
                    if st.button("✅ Confirmar Tipo", use_container_width=True):
                        st.session_state.detected_import_type = import_type
                        st.session_state.show_manual_selection = False
                        st.rerun()
                
                # Se ainda não tem tipo definido, para aqui
                if not import_type:
                    if 'detected_import_type' not in st.session_state:
                        st.stop()
                    import_type = st.session_state.detected_import_type
                
                st.markdown("---")
                st.subheader("4️⃣ Processamento Automático com IA")
                
                if not ai_service.is_available():
                    st.error("❌ IA não configurada. Configure a IA na página de Administração antes de importar.")
                    st.stop()
                
                # Busca grupos e subgrupos do cliente
                db = SessionLocal()
                try:
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
                
                # Container para status em tempo real
                status_container = st.empty()
                status_messages = []  # Lista para armazenar mensagens de status
                
                def update_status(message):
                    status_messages.append(message)
                    # Atualiza o container com a última mensagem
                    status_container.info(f"🤖 **Status:** {message}")
                
                # Processa automaticamente
                with st.spinner("🤖 Processando arquivo com IA (isso pode levar alguns segundos)..."):
                    # Passa dados completos do PDF se disponível
                    pdf_full_data = st.session_state.get('pdf_full_data')
                    result = ai_service.process_and_structure_data(
                        df, 
                        import_type,
                        pdf_full_data=pdf_full_data,
                        groups_subgroups=groups_subgroups if groups_subgroups else None,
                        status_callback=update_status
                    )
                    
                    # Limpa dados do PDF da session state após processar
                    if 'pdf_full_data' in st.session_state:
                        del st.session_state['pdf_full_data']
                    
                    # Limpa o container de status após processar
                    status_container.empty()
                
                if not result.get('success'):
                    st.error(f"❌ Erro no processamento: {result.get('error', 'Erro desconhecido')}")
                    if 'raw_response' in result:
                        with st.expander("🔍 Ver resposta da IA"):
                            st.code(result['raw_response'], language='text')
                    st.stop()
                
                # Exibe estatísticas
                summary = result.get('summary', {})
                processed_data = result.get('processed_data', [])
                
                if not processed_data:
                    st.warning("⚠️ Nenhum dado foi processado. Verifique o arquivo.")
                    st.stop()
                
                st.success("✅ Processamento concluído!")
                
                # Extrai nome do banco se disponível (para extratos bancários)
                extracted_bank_name = summary.get('bank_name', '') if summary else ''
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Processado", summary.get('processed', len(processed_data)))
                with col2:
                    if import_type == 'transactions':
                        st.metric("Entradas", summary.get('entradas', 0))
                    else:
                        st.metric("Linhas", summary.get('processed', len(processed_data)))
                with col3:
                    if import_type == 'transactions':
                        st.metric("Saídas", summary.get('saidas', 0))
                    else:
                        st.metric("Válidas", summary.get('processed', len(processed_data)))
                with col4:
                    st.metric("Erros", summary.get('errors', 0))
                
                # Mostra problemas se houver
                issues = result.get('issues', [])
                if issues:
                    with st.expander("⚠️ Problemas Encontrados"):
                        for issue in issues:
                            st.warning(issue)
                
                st.markdown("---")
                st.subheader("5️⃣ Preview Completo dos Dados Processados")
                
                # Prepara dados para preview (cria uma cópia para não modificar os originais)
                preview_data = [dict(record) for record in processed_data]  # Cópia profunda
                
                # Remove colunas internas se existirem (apenas para exibição)
                for record in preview_data:
                    record.pop('original_row', None)
                    record.pop('confidence', None)
                
                # Converte para DataFrame para preview
                preview_df = pd.DataFrame(preview_data)
                
                # Exibe preview completo de todos os dados
                st.markdown("**Visualize todos os dados que foram processados pela IA:**")
                st.dataframe(preview_df, use_container_width=True, height=400)
                st.caption(f"Total de {len(preview_df)} registro(s) processado(s)")
                
                st.markdown("---")
                st.subheader("6️⃣ Configurações e Revisão")
                
                # Exibe e permite editar nome do banco se aplicável
                if import_type == 'bank_statements':
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        if extracted_bank_name:
                            st.info(f"🏦 **Nome do banco identificado automaticamente:** {extracted_bank_name}")
                        else:
                            st.info("🏦 Nome do banco não foi identificado automaticamente")
                    
                    with col2:
                        # Armazena o nome do banco no session state para uso posterior
                        if 'bank_name_override' not in st.session_state:
                            st.session_state.bank_name_override = extracted_bank_name if extracted_bank_name else ""
                        
                        edited_bank_name = st.text_input(
                            "Editar nome do banco:",
                            value=st.session_state.bank_name_override if st.session_state.bank_name_override else extracted_bank_name if extracted_bank_name else "Banco",
                            key="bank_name_input"
                        )
                        
                        # Atualiza o session state
                        st.session_state.bank_name_override = edited_bank_name
                        
                        # Botão para aplicar o nome do banco a todos os registros
                        if st.button("🔄 Aplicar a Todos os Registros", use_container_width=True, key="apply_bank_name"):
                            if 'processed_data' in st.session_state:
                                for record in st.session_state.processed_data:
                                    record['bank_name'] = edited_bank_name
                                st.success(f"✅ Nome do banco '{edited_bank_name}' aplicado a todos os registros!")
                                st.rerun()
                        
                        st.caption("💡 Clique no botão acima para aplicar o nome a todos os registros, ou edite individualmente na tabela abaixo.")
                
                st.markdown("---")
                st.subheader("7️⃣ Edição e Seleção de Dados para Importação")
                
                # Prepara dados processados (cria uma cópia para não modificar os originais)
                working_data = [dict(record) for record in processed_data]  # Cópia profunda
                
                # Remove colunas internas se existirem
                for record in working_data:
                    record.pop('original_row', None)
                    record.pop('confidence', None)
                
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
                            if 'bank_name' not in record or not record.get('bank_name') or (isinstance(record.get('bank_name'), float) and pd.isna(record.get('bank_name'))):
                                record['bank_name'] = bank_name_to_apply
                
                # Converte para DataFrame APENAS após todas as transformações
                processed_df = pd.DataFrame(working_data)
                
                # Inicializa seleção de linhas
                # Usa working_data (lista de dicts) diretamente, não o DataFrame
                file_hash = f"{uploaded_file.name}_{len(working_data)}_{import_type}"
                if 'last_file_hash' not in st.session_state or st.session_state.last_file_hash != file_hash:
                    # Cria cópia profunda para o session state
                    st.session_state.processed_data = [dict(record) for record in working_data]
                    st.session_state.selected_rows = set(range(len(working_data)))
                    st.session_state.last_file_hash = file_hash
                elif 'processed_data' not in st.session_state:
                    # Cria cópia profunda para o session state
                    st.session_state.processed_data = [dict(record) for record in working_data]
                    st.session_state.selected_rows = set(range(len(working_data)))
                
                # Controles de seleção
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("✅ Selecionar Todas", use_container_width=True):
                        st.session_state.selected_rows = set(range(len(processed_df)))
                        st.rerun()
                
                with col2:
                    if st.button("❌ Desselecionar Todas", use_container_width=True):
                        st.session_state.selected_rows = set()
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Remover Selecionadas", use_container_width=True):
                        # Remove linhas selecionadas
                        selected_indices = sorted(list(st.session_state.selected_rows), reverse=True)
                        current_data = st.session_state.processed_data.copy()
                        for idx in selected_indices:
                            if 0 <= idx < len(current_data):
                                current_data.pop(idx)
                        st.session_state.processed_data = current_data
                        st.session_state.selected_rows = set(range(len(current_data)))
                        st.rerun()
                
                with col4:
                    total_selected = len(st.session_state.selected_rows)
                    st.metric("Linhas Selecionadas", f"{total_selected} / {len(st.session_state.processed_data)}")
                
                # Tabela editável
                st.markdown("**Revise e edite os dados processados:**")
                
                # Prepara dados para edição
                edit_data = []
                for idx, row in enumerate(st.session_state.processed_data):
                    row_copy = row.copy()
                    row_copy['_select'] = idx in st.session_state.selected_rows
                    row_copy['_row_num'] = idx + 1
                    edit_data.append(row_copy)
                
                edit_df = pd.DataFrame(edit_data)
                
                # Reordena colunas
                cols = ['_row_num', '_select'] + [c for c in edit_df.columns if c not in ['_row_num', '_select']]
                edit_df = edit_df[cols]
                
                # Converte tipos de dados antes de editar
                # Converte datas de string para datetime se existirem
                if 'date' in edit_df.columns:
                    try:
                        edit_df['date'] = pd.to_datetime(edit_df['date'], errors='coerce')
                    except:
                        pass  # Se não conseguir converter, mantém como string
                
                # Converte valores numéricos
                numeric_columns = ['value', 'balance']
                for col in numeric_columns:
                    if col in edit_df.columns:
                        try:
                            edit_df[col] = pd.to_numeric(edit_df[col], errors='coerce')
                        except:
                            pass
                
                # Configura colunas editáveis
                column_config = {
                    "_row_num": st.column_config.NumberColumn("Linha", width="small", disabled=True),
                    "_select": st.column_config.CheckboxColumn("Importar", width="small"),
                }
                
                # Adiciona configuração para campos editáveis baseado no tipo
                if import_type == 'transactions':
                    # Verifica se date é datetime ou string
                    if 'date' in edit_df.columns:
                        if pd.api.types.is_datetime64_any_dtype(edit_df['date']):
                            column_config["date"] = st.column_config.DateColumn("Data", format="YYYY-MM-DD")
                        else:
                            column_config["date"] = st.column_config.TextColumn("Data (YYYY-MM-DD)")
                    
                    column_config.update({
                        "description": st.column_config.TextColumn("Descrição", width="medium"),
                        "type": st.column_config.SelectboxColumn("Tipo", options=["entrada", "saida"], width="small"),
                        "category": st.column_config.TextColumn("Categoria", width="medium"),
                        "account": st.column_config.TextColumn("Conta", width="small"),
                    })
                    
                    if 'value' in edit_df.columns:
                        if pd.api.types.is_numeric_dtype(edit_df['value']):
                            column_config["value"] = st.column_config.NumberColumn("Valor", format="%.2f")
                        else:
                            column_config["value"] = st.column_config.TextColumn("Valor")
                            
                elif import_type == 'bank_statements':
                    # Verifica se date é datetime ou string
                    if 'date' in edit_df.columns:
                        if pd.api.types.is_datetime64_any_dtype(edit_df['date']):
                            column_config["date"] = st.column_config.DateColumn("Data", format="YYYY-MM-DD", width="small")
                        else:
                            column_config["date"] = st.column_config.TextColumn("Data (YYYY-MM-DD)", width="small")
                    
                    # Garante que todos os campos sejam editáveis
                    column_config.update({
                        "description": st.column_config.TextColumn("Descrição", width="medium"),
                        "bank_name": st.column_config.TextColumn("Banco", width="medium"),
                        "account": st.column_config.TextColumn("Conta", width="small"),
                    })
                    
                    if 'value' in edit_df.columns:
                        if pd.api.types.is_numeric_dtype(edit_df['value']):
                            column_config["value"] = st.column_config.NumberColumn("Valor", format="%.2f", width="small")
                        else:
                            column_config["value"] = st.column_config.TextColumn("Valor", width="small")
                    
                    if 'balance' in edit_df.columns:
                        if pd.api.types.is_numeric_dtype(edit_df['balance']):
                            column_config["balance"] = st.column_config.NumberColumn("Saldo", format="%.2f", width="small")
                        else:
                            column_config["balance"] = st.column_config.TextColumn("Saldo", width="small")
                
                # Adiciona configuração para outros campos que possam existir (genérico)
                for col in edit_df.columns:
                    if col not in column_config and col not in ['_row_num', '_select']:
                        # Tenta inferir o tipo
                        if pd.api.types.is_numeric_dtype(edit_df[col]):
                            column_config[col] = st.column_config.NumberColumn(col, width="small")
                        elif pd.api.types.is_datetime64_any_dtype(edit_df[col]):
                            column_config[col] = st.column_config.DateColumn(col, format="YYYY-MM-DD", width="small")
                        else:
                            column_config[col] = st.column_config.TextColumn(col, width="medium")
                
                # Exibe tabela editável
                edited_df = st.data_editor(
                    edit_df,
                    column_config=column_config,
                    hide_index=True,
                    use_container_width=True,
                    num_rows="fixed",
                    height=min(500, max(300, len(edit_df) * 35))
                )
                
                # Atualiza seleção e dados
                new_selection = set()
                updated_data = []
                
                for idx, row in edited_df.iterrows():
                    row_num = int(row.get('_row_num', idx + 1)) - 1
                    if row.get('_select', False):
                        new_selection.add(row_num)
                    
                    # Atualiza dados (remove colunas internas)
                    row_dict = row.to_dict()
                    row_dict.pop('_row_num', None)
                    row_dict.pop('_select', None)
                    
                    # Converte datas de datetime para string YYYY-MM-DD
                    if 'date' in row_dict and pd.notna(row_dict.get('date')):
                        if isinstance(row_dict['date'], pd.Timestamp):
                            row_dict['date'] = row_dict['date'].strftime('%Y-%m-%d')
                        elif isinstance(row_dict['date'], str):
                            # Tenta converter e formatar
                            try:
                                dt = pd.to_datetime(row_dict['date'])
                                row_dict['date'] = dt.strftime('%Y-%m-%d')
                            except:
                                pass  # Mantém como está
                    
                    # Converte valores numéricos para float
                    for col in ['value', 'balance']:
                        if col in row_dict and pd.notna(row_dict.get(col)):
                            try:
                                row_dict[col] = float(row_dict[col])
                            except:
                                pass
                    
                    updated_data.append(row_dict)
                
                st.session_state.selected_rows = new_selection
                st.session_state.processed_data = updated_data
                
                # Preview das linhas selecionadas
                st.markdown("---")
                st.subheader("8️⃣ Preview das Linhas Selecionadas para Importação")
                
                if st.session_state.selected_rows:
                    selected_indices = sorted(list(st.session_state.selected_rows))
                    selected_data = [st.session_state.processed_data[i] for i in selected_indices if 0 <= i < len(st.session_state.processed_data)]
                    selected_df = pd.DataFrame(selected_data)
                    
                    st.dataframe(selected_df, use_container_width=True, height=300)
                    st.success(f"✅ {len(selected_indices)} linha(s) selecionada(s) para importação")
                else:
                    st.warning("⚠️ Nenhuma linha selecionada. Selecione pelo menos uma linha para importar.")
                
                st.markdown("---")
                st.subheader("9️⃣ Importação Final")
                
                # Opções adicionais para classificação
                group_id = None
                subgroup_id = None
                bank_name = "Banco"
                
                # Seleção de grupo/subgrupo para todos os tipos
                groups = db.query(Group).filter(Group.client_id == client_id).all()
                if groups:
                    st.markdown("### 📁 Classificação por Grupos/Subgrupos")
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_group = st.selectbox(
                            "Grupo (opcional):",
                            options=[None] + groups,
                            format_func=lambda x: "Nenhum" if x is None else x.name,
                            key="import_group"
                        )
                        if selected_group:
                            group_id = selected_group.id
                    
                    with col2:
                        if selected_group:
                            subgroups = db.query(Subgroup).filter(Subgroup.group_id == group_id).all()
                            if subgroups:
                                selected_subgroup = st.selectbox(
                                    "Subgrupo (opcional):",
                                    options=[None] + subgroups,
                                    format_func=lambda x: "Nenhum" if x is None else x.name,
                                    key="import_subgroup"
                                )
                                if selected_subgroup:
                                    subgroup_id = selected_subgroup.id
                        else:
                            st.selectbox(
                                "Subgrupo (opcional):",
                                options=[None],
                                format_func=lambda x: "Selecione um grupo primeiro",
                                disabled=True,
                                key="import_subgroup_disabled"
                            )
                    
                    st.caption("💡 Os grupos/subgrupos selecionados serão aplicados a todos os registros importados.")
                    st.markdown("---")
                
                # Configurações específicas por tipo
                if import_type == 'bank_statements':
                    # Usa nome do banco do session state (que pode ter sido editado)
                    bank_name = st.session_state.get('bank_name_override', extracted_bank_name if extracted_bank_name else "Banco")
                    st.info(f"🏦 Nome do banco que será usado na importação: **{bank_name}**")
                    st.caption("💡 Você pode alterar o nome do banco na seção de configurações acima, ou editar individualmente na tabela de revisão.")
                    st.info("ℹ️ **Importante:** Os extratos serão salvos na tabela de extratos bancários E automaticamente convertidos em transações para aparecer nos relatórios DRE/DFC.")
                
                # Botão de importar
                import_btn = st.button(
                    "📥 Importar Dados Selecionados",
                    use_container_width=True,
                    disabled=len(st.session_state.selected_rows) == 0,
                    type="primary"
                )
                
                if import_btn and len(st.session_state.selected_rows) > 0:
                    with st.spinner("Importando dados..."):
                        # Filtra apenas linhas selecionadas
                        selected_indices = sorted(list(st.session_state.selected_rows))
                        data_to_import = [st.session_state.processed_data[i] for i in selected_indices if 0 <= i < len(st.session_state.processed_data)]
                        import_df = pd.DataFrame(data_to_import)
                        
                        # Importa dados
                        imported_count = 0
                        
                        if import_type == 'transactions':
                            imported_count = ImportService.import_transactions(
                                db, client_id, import_df, 'imported', uploaded_file.name,
                                group_id, subgroup_id
                            )
                        
                        elif import_type == 'bank_statements':
                            result = ImportService.import_bank_statements(
                                db, client_id, import_df, bank_name, uploaded_file.name,
                                group_id, subgroup_id
                            )
                            imported_count = result.get('statements', 0)
                            transactions_created = result.get('transactions', 0)
                            if imported_count > 0:
                                st.success(f"✅ {imported_count} extrato(s) importado(s) e {transactions_created} transação(ões) criada(s) automaticamente!")
                        
                        elif import_type == 'contracts':
                            imported_count = ImportService.import_contracts(
                                db, client_id, import_df, group_id, subgroup_id
                            )
                        
                        elif import_type == 'accounts_payable':
                            imported_count = ImportService.import_accounts_payable(
                                db, client_id, import_df, group_id, subgroup_id
                            )
                        
                        elif import_type == 'accounts_receivable':
                            imported_count = ImportService.import_accounts_receivable(
                                db, client_id, import_df, group_id, subgroup_id
                            )
                        elif import_type == 'financial_investments':
                            imported_count = ImportService.import_financial_investments(
                                db, client_id, import_df, group_id, subgroup_id
                            )
                        elif import_type == 'credit_card_invoices':
                            imported_count = ImportService.import_credit_card_invoices(
                                db, client_id, import_df, group_id, subgroup_id
                            )
                        elif import_type == 'card_machine_statements':
                            imported_count = ImportService.import_card_machine_statements(
                                db, client_id, import_df, group_id, subgroup_id
                            )
                        elif import_type == 'inventory':
                            imported_count = ImportService.import_inventory(
                                db, client_id, import_df, group_id, subgroup_id
                            )
                        
                        if import_type != 'bank_statements' and imported_count > 0:
                            st.success(f"✅ {imported_count} registro(s) importado(s) com sucesso!")
                            st.balloons()
                        
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
                        
                        if import_type != 'bank_statements' and imported_count == 0:
                            st.warning("⚠️ Nenhum registro foi importado. Verifique os dados.")
            
            finally:
                db.close()
        
        else:
            st.error("❌ Não foi possível ler o arquivo. Verifique o formato.")
    
    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo: {str(e)}")
        st.exception(e)

else:
    st.info("ℹ️ Faça upload de um arquivo para começar.")

# Informações sobre formatos
with st.expander("ℹ️ Informações sobre Formatos"):
    st.markdown("""
    ### Formatos Suportados
    
    **CSV (Comma-Separated Values)**
    - Formato texto com valores separados por vírgula, ponto-e-vírgula ou tabulação
    - Suporta diferentes encodings (UTF-8, Latin-1, etc)
    
    **Excel (XLSX/XLS)**
    - Planilhas do Microsoft Excel
    - Suporta múltiplas abas
    
    **PDF**
    - Extração automática de tabelas
    - Funciona melhor com PDFs que contêm tabelas estruturadas
    
    **OFX (Open Financial Exchange)**
    - Formato padrão de extratos bancários
    - Usado por bancos brasileiros (BB, Itaú, Bradesco, etc)
    """)

with st.expander("✏️ Edição de Dados Importados"):
    st.markdown("""
    ### Como Editar Dados Importados
    
    Após importar seus dados, você pode editá-los nas páginas específicas:
    
    - **💳 Transações** → Edite, exclua ou adicione transações manualmente
    - **📝 Contratos** → Gerencie contratos importados ou manuais
    - **💰 Contas** → Edite contas a pagar e receber
    
    **Dica:** Todos os dados importados podem ser editados ou excluídos individualmente!
    """)

