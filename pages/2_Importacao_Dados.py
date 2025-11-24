"""
Página de Importação de Dados
"""
import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from services.auth_service import AuthService
from services.parser_service import ParserService
from services.import_service import ImportService
from services.ai_service import AIService
from services.ai_classifier import AIClassifier
from services.data_processor import DataProcessor
from utils.column_mapper import ColumnMapper
from utils.translations import translate_dataframe
from models.client import Client
from models.group import Group, Subgroup
from config.ai_config import AIConfigManager

# Constantes
CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.70  # 70% de confiança mínima para classificação

# Helpers
def _ensure_classification_confidence(record: dict) -> dict:
    """
    Normaliza o campo classification_confidence nos registros retornados pela IA.
    """
    if (
        "classification_confidence" not in record
        and "confidence" in record
        and record["confidence"] is not None
    ):
        record["classification_confidence"] = record.pop("confidence")
    else:
        record.pop("confidence", None)
    return record


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


st.set_page_config(page_title="Importação de Dados", page_icon="📥", layout="wide")

# Esconde o menu automático do Streamlit
from utils.hide_auto_menu import hide_streamlit_menu
hide_streamlit_menu()

# Verifica autenticação
AuthService.init_session_state()
AuthService.require_auth()

# Verifica se há resultado de importação concluída
if 'import_result' in st.session_state and st.session_state.import_result:
    result = st.session_state.import_result
    # Mostra notificação se a importação foi concluída recentemente (últimos 5 minutos)
    from datetime import datetime, timedelta
    try:
        timestamp = datetime.fromisoformat(result.get('timestamp', ''))
        if datetime.now() - timestamp < timedelta(minutes=5):
            if result.get('status') == 'success':
                st.success(f"✅ **Importação Concluída:** {result.get('message', '')}")
            elif result.get('status') == 'warning':
                st.warning(f"⚠️ **Importação:** {result.get('message', '')}")
            
            # Botão para limpar notificação
            if st.button("✖️ Fechar notificação", key="clear_import_notification"):
                del st.session_state.import_result
                st.rerun()
    except:
        pass


# Usa sidebar centralizada
from utils.sidebar import show_sidebar
show_sidebar()

st.title("📥 Importação de Dados")
st.markdown("**Processamento automático com IA Vision - Suporta CSV, Excel, PDF, OFX e Imagens**")
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
    help="Formatos suportados: CSV, Excel, PDF, OFX, Imagens (JPG, PNG, etc). O sistema detecta e processa automaticamente."
)

if uploaded_file:
    file_size = len(uploaded_file.read())
    uploaded_file.seek(0)  # Reset para ler novamente depois
    file_size_kb = file_size / 1024
    st.success(f"✅ **{uploaded_file.name}** ({file_size_kb:.1f} KB)")
    
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
    
    file_content = uploaded_file.read()
    
    # Verifica se já foi processado
    file_hash = f"{uploaded_file.name}_{len(file_content)}"
    if 'processed_file_hash' not in st.session_state or st.session_state.processed_file_hash != file_hash:
        # Processa arquivo
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_status(message):
            status_text.info(f"🤖 {message}")
        
<<<<<<< HEAD
        # Permite override manual se necessário
        file_type = detected_type
        if 'show_file_type_override' in st.session_state and st.session_state.show_file_type_override:
            st.markdown("---")
            st.subheader("✏️ Seleção Manual do Tipo de Arquivo")
            file_type = st.selectbox(
                "Tipo de arquivo:",
                options=['CSV', 'Excel', 'PDF', 'OFX', 'Image'],
                index=['CSV', 'Excel', 'PDF', 'OFX', 'Image'].index(detected_type) if detected_type in ['CSV', 'Excel', 'PDF', 'OFX', 'Image'] else 0,
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
            
            # Tenta extrair usando método completo primeiro (com OCR se necessário)
            pdf_data = None
            try:
                pdf_data = ParserService.parse_pdf_complete(file_content, use_ocr_if_needed=True)
                df = pdf_data.get('dataframe')
                
                # Se OCR foi usado, informa ao usuário
                if pdf_data.get('metadata', {}).get('ocr_used', False):
                    st.info("ℹ️ PDF baseado em imagens detectado. OCR foi usado para extrair o texto.")
            except Exception as e:
                st.warning(f"⚠️ Aviso ao processar PDF: {str(e)}")
                # Fallback para método simples
                df = ParserService.parse_pdf_to_dataframe(file_content)
            
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
            file_content = uploaded_file.read()
            df = ParserService.ofx_to_dataframe(file_content)
            # OFX é sempre extrato bancário
            auto_detected_type = 'bank_statements'
        elif file_type == 'Image' or is_image_file:
            file_content = uploaded_file.read()
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            # Processa imagem com OCR
            try:
                # Mostra progresso mais detalhado
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.info("🖼️ Iniciando processamento de imagem com OCR...")
                progress_bar.progress(10)
                
                # Processa imagem com timeout implícito (o pytesseract tem timeout de 120s)
                status_text.info("🖼️ Extraindo texto da imagem (isso pode levar até 2 minutos para imagens grandes)...")
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
            except Exception as e:
                error_msg = str(e)
                st.error(f"❌ Erro ao processar imagem: {error_msg}")
                
                # Mensagens de ajuda específicas
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    st.warning("⏱️ O processamento demorou muito. Tente:")
                    st.markdown("- Redimensionar a imagem para um tamanho menor")
                    st.markdown("- Converter para PDF e tentar novamente")
                    st.markdown("- Usar uma imagem com melhor qualidade/resolução")
                elif "tesseract" in error_msg.lower() or "pytesseract" in error_msg.lower():
                    st.info("💡 Certifique-se de que o Tesseract OCR está instalado:")
                    st.code("sudo apt-get install tesseract-ocr tesseract-ocr-por tesseract-ocr-eng")
                else:
                    st.info("💡 Certifique-se de que as bibliotecas de OCR estão instaladas: pip install pytesseract pdf2image Pillow easyocr")
                
                st.stop()
            auto_detected_type = None
        else:
            auto_detected_type = None
        
        # Limpa estado de override após processar
        if 'show_file_type_override' in st.session_state:
            del st.session_state.show_file_type_override
        if 'detected_file_type' in st.session_state:
            del st.session_state.detected_file_type
        
        if df is not None and not df.empty:
            st.markdown("---")
            st.subheader("2️⃣ Validação da Extração")
            
            # Valida completude da extração
            file_content_for_validation = uploaded_file.read()
            uploaded_file.seek(0)  # Reset para uso posterior
            
            validation_result = ParserService.validate_extraction_completeness(
                df, file_content_for_validation, file_type
            )
            
            # Exibe resultados da validação
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Linhas Extraídas", f"{validation_result['extracted_rows']:,}".replace(',', '.'))
            with col2:
                if validation_result['expected_rows']:
                    st.metric("Linhas Esperadas", f"{validation_result['expected_rows']:,}".replace(',', '.'))
                else:
                    st.metric("Status", "✅ Extraído")
            with col3:
                if validation_result['completeness_percentage']:
                    percentage = validation_result['completeness_percentage']
                    if percentage >= 95:
                        st.metric("Completude", f"{percentage:.1f}%", delta="Completo")
                    else:
                        st.metric("Completude", f"{percentage:.1f}%", delta="Incompleto", delta_color="inverse")
                else:
                    st.metric("Completude", "N/A")
            
            # Avisos se houver problemas
            if validation_result['warnings']:
                for warning in validation_result['warnings']:
                    st.warning(f"⚠️ {warning}")
            
            if not validation_result['is_complete'] and validation_result['completeness_percentage']:
                st.error("❌ **Atenção:** A extração pode estar incompleta. Algumas linhas podem não ter sido extraídas.")
                if st.button("🔄 Tentar Reprocessar", use_container_width=True):
                    # Limpa estado e recarrega
                    if 'extracted_df' in st.session_state:
                        del st.session_state.extracted_df
                    st.rerun()
            
            st.markdown("---")
            st.subheader("3️⃣ Preview dos Dados Extraídos")
            
            # Remove linhas completamente vazias para melhor visualização
            df_preview = df.dropna(how='all').copy()
            
            # Opção para ver preview completo ou limitado
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"✅ **{len(df)} linhas** e **{len(df.columns)} colunas** extraídas com sucesso")
            with col2:
                show_full_preview = st.checkbox("📋 Ver todos os dados", value=False, 
                                                help="Mostra todos os dados com barra de rolagem")
            
            # Exibe preview (traduzido para português)
            df_preview_translated = translate_dataframe(df_preview.copy(), translate_columns=True, translate_values=False)
            if show_full_preview:
                st.dataframe(df_preview_translated, use_container_width=True, height=400)
                st.caption(f"📊 Exibindo todas as {len(df_preview_translated)} linhas (após remover linhas vazias)")
            else:
                st.dataframe(df_preview_translated.head(10), use_container_width=True)
                st.caption(f"📊 Mostrando 10 primeiras linhas de {len(df_preview_translated)} (após remover linhas vazias) | Total: {len(df)} linhas, {len(df.columns)} colunas")
            
            # Salva DataFrame extraído no session state
            st.session_state['extracted_df'] = df
            
            # Prepara metadados para estatísticas
            metadata = None
            if file_type == 'PDF' and 'pdf_full_data' in st.session_state:
                metadata = st.session_state['pdf_full_data'].get('metadata')
            
            st.session_state['extraction_stats'] = ParserService.get_extraction_stats(
                df, file_type, metadata
            )
            
            # Detecção automática do tipo de dado
            st.markdown("---")
            st.subheader("3️⃣ Tipo de Dado Detectado")
            
            db = SessionLocal()
            try:
                # Verifica se o tipo já foi confirmado anteriormente - se sim, pula toda a detecção
                if st.session_state.get('type_confirmed', False) and 'detected_import_type' in st.session_state:
                    import_type = st.session_state.detected_import_type
                    st.info(f"✅ **Tipo confirmado:** {import_type}")
                # Se for OFX, já sabemos que é extrato bancário
                elif file_type == 'OFX':
                    import_type = 'bank_statements'
                    st.info("🏦 **Tipo detectado automaticamente:** Extratos Bancários (formato OFX)")
                    
                    # Requer confirmação explícita do usuário
                    if 'type_confirmed' not in st.session_state or not st.session_state.type_confirmed:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if st.button("✅ Confirmar e Continuar", use_container_width=True, type="primary"):
                                st.session_state.detected_import_type = import_type
                                st.session_state.type_confirmed = True
                                st.rerun()
                        with col2:
                            if st.button("✏️ Alterar Tipo Manualmente", use_container_width=True):
                                st.session_state.show_manual_selection = True
                                st.session_state.type_confirmed = False  # Limpa confirmação anterior
                                st.rerun()
                        
                        # Se ainda não foi confirmado, para aqui
                        if 'detected_import_type' not in st.session_state:
                            st.stop()
                        import_type = st.session_state.detected_import_type
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
                        
                        # Exibe sugestão de forma mais concisa
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            if confidence >= 0.7:
                                st.success(f"🤖 **Tipo detectado:** {suggested_name}")
                            elif confidence >= 0.5:
                                st.warning(f"🤖 **Tipo detectado:** {suggested_name}")
                            else:
                                st.info(f"🤖 **Tipo detectado:** {suggested_name} (baixa confiança)")
                        
                        with col2:
                            st.metric("Confiança", f"{confidence_percent}%")
                        
                        with col3:
                            if st.button("✏️ Alterar", use_container_width=True, help="Selecione manualmente se a detecção estiver incorreta"):
                                st.session_state.show_manual_selection = True
                                st.session_state.type_confirmed = False
                                st.rerun()
                        
                        # Detalhes opcionais (colapsados)
                        if reasoning or key_indicators or alternative_types:
                            with st.expander("ℹ️ Detalhes da detecção"):
                                if reasoning:
                                    st.write(f"**Motivo:** {reasoning}")
                                if key_indicators:
                                    st.write("**Indicadores:** " + ", ".join(key_indicators))
                                if alternative_types:
                                    st.write("**Alternativas:**")
                                    for alt in alternative_types[:3]:  # Mostra apenas top 3
                                        alt_name = type_names.get(alt.get('type'), alt.get('type'))
                                        alt_confidence = int(alt.get('confidence', 0) * 100)
                                        st.write(f"- {alt_name} ({alt_confidence}%)")
                        
                        # Botão de confirmação
                        if st.button("✅ Confirmar e Continuar", use_container_width=True, type="primary"):
                            import_type = suggested_type
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
                
                # Seleção manual (se necessário ou se usuário escolheu)
                if 'show_manual_selection' in st.session_state and st.session_state.show_manual_selection:
                    st.markdown("---")
                    st.subheader("✏️ Seleção Manual do Tipo de Dado")
                    st.info("💡 Selecione o tipo de dado que melhor descreve o conteúdo do arquivo.")
                    
                    # Define mapeamento de tipos para nomes amigáveis
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
                    
                    # Se havia uma sugestão anterior, mostra como referência
                    if 'detected_import_type' in st.session_state:
                        previous_suggestion = st.session_state.detected_import_type
                        previous_name = type_names_map.get(previous_suggestion, previous_suggestion)
                        st.caption(f"💡 Sugestão anterior da IA: {previous_name}")
                    
                    import_type = st.selectbox(
                        "Tipo de dado:",
                        options=['transactions', 'bank_statements', 'contracts', 'accounts_payable', 'accounts_receivable',
                                'financial_investments', 'credit_card_invoices', 'card_machine_statements', 'inventory'],
                        format_func=lambda x: type_names_map[x],
                        key="manual_import_type"
                    )
                    if st.button("✅ Confirmar Tipo", use_container_width=True):
                        st.session_state.detected_import_type = import_type
                        st.session_state.type_confirmed = True
                        st.session_state.show_manual_selection = False
                        st.rerun()
                
                # Se ainda não tem tipo definido, para aqui
                if not import_type:
                    if 'detected_import_type' not in st.session_state:
                        st.stop()
                    import_type = st.session_state.detected_import_type
                
                # Verifica se o tipo foi confirmado pelo usuário antes de processar
                if not st.session_state.get('type_confirmed', False):
                    st.info("ℹ️ Por favor, confirme o tipo de dado detectado acima para continuar com o processamento.")
                    st.stop()
                
                st.markdown("---")
                st.subheader("4️⃣ Classificação com IA (Opcional)")
                
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
                
                # Verifica se há grupos para classificação
                use_ai_classification = False
                if groups_subgroups:
                    use_ai_classification = st.checkbox(
                        "🤖 Usar IA para classificar por grupos/subgrupos",
                        value=True,
                        help="Classifica automaticamente cada registro com group_id e subgroup_id baseado na descrição e valor"
                    )
                
                processed_data = []
                classification_result = None
                
                if use_ai_classification:
                    # Inicializa classificador
                    classifier = AIClassifier(db)
                    
                    if not classifier.is_available():
                        st.error("❌ IA não configurada. Configure a IA na página de Administração antes de usar classificação automática.")
                        use_ai_classification = False
                    else:
                        # Container para status em tempo real
                        status_container = st.empty()
                        status_messages = []
                        
                        def update_status(message):
                            status_messages.append(message)
                            status_container.info(f"🤖 **Classificando:** {message}")
                        
                        # Classifica dados extraídos
                        with st.spinner(f"🤖 Classificando {len(df)} registros com IA..."):
                            classification_result = classifier.classify_dataframe(
                                df,
                                groups_subgroups=groups_subgroups,
                                import_type=import_type,
                                status_callback=update_status
                            )
                            
                            status_container.empty()
                        
                        if classification_result.get('success'):
                            processed_data = classification_result.get('classified_data', [])
                            # Se tipo foi detectado, atualiza
                            if classification_result.get('detected_type'):
                                import_type = classification_result.get('detected_type')
                            
                            # Mostra estatísticas de classificação
                            classified_count = sum(1 for r in processed_data if r.get('group_id') is not None)
                            high_conf_count = sum(1 for r in processed_data if r.get('classification_confidence', 0) >= CLASSIFICATION_CONFIDENCE_THRESHOLD)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Registros Classificados", f"{classified_count}/{len(processed_data)}")
                            with col2:
                                st.metric("Alta Confiança", f"{high_conf_count}/{len(processed_data)}")
                            with col3:
                                issues_count = len(classification_result.get('issues', []))
                                st.metric("Avisos", issues_count)
                            
                            if classification_result.get('issues'):
                                with st.expander("⚠️ Avisos da Classificação"):
                                    for issue in classification_result.get('issues', []):
                                        st.warning(issue)
                        else:
                            st.error(f"❌ Erro na classificação: {classification_result.get('error', 'Erro desconhecido')}")
                            # Continua sem classificação
                            processed_data = df.to_dict('records')
                            for record in processed_data:
                                record['group_id'] = None
                                record['subgroup_id'] = None
                                record['classification_confidence'] = 0.0
                
                # Se não usou IA, converte DataFrame para lista de dicionários
                if not processed_data:
                    processed_data = df.to_dict('records')
                    # Adiciona campos de classificação vazios
                    for record in processed_data:
                        record['group_id'] = None
                        record['subgroup_id'] = None
                        record['classification_confidence'] = 1.0  # Sem classificação = confiança máxima (dados já extraídos)
                
                # Normaliza dados
                processed_data = [_ensure_classification_confidence(dict(record)) for record in processed_data]
                
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
                
                # Validação: verifica se todas as linhas foram processadas
                original_rows = len(df)
                processed_rows = len(processed_data)
                rows_diff = original_rows - processed_rows
                
                if rows_diff > 0:
                    st.warning(
                        f"⚠️ **ATENÇÃO:** {rows_diff} linha(s) não foram processadas. "
                        f"Esperado: {original_rows}, Processado: {processed_rows}."
                    )
                else:
                    st.success(f"✅ Processamento concluído! Todas as {processed_rows} linhas foram processadas com sucesso.")
                
                # Identifica registros com baixa confiança de classificação
                low_conf_indexes = [
                    idx for idx, record in enumerate(processed_data)
                    if record.get('classification_confidence', 1) is not None
                    and record.get('classification_confidence', 1) < CLASSIFICATION_CONFIDENCE_THRESHOLD
                ]
                low_conf_line_numbers = [idx + 1 for idx in low_conf_indexes]
                
                # Exibe estatísticas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Processado", processed_rows)
                with col2:
                    classified_count = sum(1 for r in processed_data if r.get('group_id') is not None)
                    st.metric("Classificados", f"{classified_count}/{processed_rows}")
                with col3:
                    high_conf_count = sum(1 for r in processed_data if r.get('classification_confidence', 0) >= CLASSIFICATION_CONFIDENCE_THRESHOLD)
                    st.metric("Alta Confiança", f"{high_conf_count}/{processed_rows}")
                with col4:
                    st.metric("Baixa Confiança", len(low_conf_indexes))
                
                if low_conf_line_numbers:
                    preview_lines = ", ".join(str(num) for num in low_conf_line_numbers[:10])
                    extra = ""
                    if len(low_conf_line_numbers) > 10:
                        extra = f" (total de {len(low_conf_line_numbers)} linhas)"
                    st.warning(
                        f"⚠️ {len(low_conf_line_numbers)} linha(s) com confiança abaixo de "
                        f"{int(CLASSIFICATION_CONFIDENCE_THRESHOLD * 100)}%: {preview_lines}{extra}. "
                        "Revise a classificação antes de importar."
                    )
                
                # Mostra problemas se houver (da classificação)
                if classification_result and classification_result.get('issues'):
                    with st.expander("⚠️ Problemas Encontrados na Classificação"):
                        for issue in classification_result.get('issues', []):
                            st.warning(issue)
                
                st.markdown("---")
                st.subheader("5️⃣ Preview Completo dos Dados Processados")
                
                # Prepara dados para preview (cria uma cópia para não modificar os originais)
                preview_data = [dict(record) for record in processed_data]  # Cópia profunda
                
                # Remove colunas internas se existirem (apenas para exibição)
                for record in preview_data:
                    record.pop('original_row', None)
                    _ensure_classification_confidence(record)
                
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
                    # Tenta extrair nome do banco dos dados
                    extracted_bank_name = None
                    for record in processed_data:
                        if record.get('bank_name'):
                            extracted_bank_name = record.get('bank_name')
                            break
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        if extracted_bank_name:
                            st.info(f"🏦 **Nome do banco identificado:** {extracted_bank_name}")
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
                    _ensure_classification_confidence(record)
                
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
                if low_conf_line_numbers:
                    st.info(
                        "As linhas com confiança baixa permanecem selecionadas; utilize a coluna "
                        "'Confiança Classificação' para identificar e ajustar grupos/subgrupos."
                    )
                
                # Busca mapeamento de grupos e subgrupos
                db_edit = SessionLocal()
                try:
                    group_mapping, subgroup_mapping = _get_group_subgroup_names_mapping(db_edit, client_id)
                finally:
                    db_edit.close()
                
                # Prepara dados para edição e adiciona nomes de grupos/subgrupos
                edit_data = []
                for idx, row in enumerate(st.session_state.processed_data):
                    row_copy = row.copy()
                    row_copy['_select'] = idx in st.session_state.selected_rows
                    row_copy['_row_num'] = idx + 1
                    edit_data.append(row_copy)
                
                # Adiciona nomes de grupos e subgrupos
                edit_data = _add_group_subgroup_names_to_data(edit_data, group_mapping, subgroup_mapping)
                
                edit_df = pd.DataFrame(edit_data)
                
                # Reordena colunas - coloca group_name e subgroup_name antes de group_id e subgroup_id
                # e oculta group_id e subgroup_id na visualização
                display_cols = ['_row_num', '_select']
                other_cols = []
                hidden_cols = []
                
                for col in edit_df.columns:
                    if col not in ['_row_num', '_select', 'group_id', 'subgroup_id', 'group_name', 'subgroup_name']:
                        other_cols.append(col)
                    elif col in ['group_id', 'subgroup_id']:
                        hidden_cols.append(col)
                
                # Adiciona group_name e subgroup_name se existirem
                if 'group_name' in edit_df.columns:
                    display_cols.append('group_name')
                if 'subgroup_name' in edit_df.columns:
                    display_cols.append('subgroup_name')
                
                # Adiciona outras colunas
                display_cols.extend(other_cols)
                
                # Adiciona colunas ocultas no final (para manter os dados, mas não exibir)
                all_cols = display_cols + hidden_cols
                edit_df = edit_df[[c for c in all_cols if c in edit_df.columns]]
                
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
                
                if 'classification_confidence' in edit_df.columns:
                    try:
                        edit_df['classification_confidence'] = pd.to_numeric(
                            edit_df['classification_confidence'], errors='coerce'
                        )
                    except:
                        pass
                
                # Configura colunas editáveis
                column_config = {
                    "_row_num": st.column_config.NumberColumn("Linha", width="small", disabled=True),
                    "_select": st.column_config.CheckboxColumn("Importar", width="small"),
                }
                if 'classification_confidence' in edit_df.columns:
                    column_config["classification_confidence"] = st.column_config.NumberColumn(
                        "Confiança Classificação", format="%.2f", disabled=True, width="small"
                    )
                
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
                
                # Adiciona configuração para group_name e subgroup_name
                if 'group_name' in edit_df.columns:
                    column_config['group_name'] = st.column_config.TextColumn("Grupo", width="medium", disabled=True)
                if 'subgroup_name' in edit_df.columns:
                    column_config['subgroup_name'] = st.column_config.TextColumn("Subgrupo", width="medium", disabled=True)
                
                # Oculta group_id e subgroup_id na visualização
                if 'group_id' in edit_df.columns:
                    column_config['group_id'] = st.column_config.NumberColumn("group_id", width=0, disabled=True)
                if 'subgroup_id' in edit_df.columns:
                    column_config['subgroup_id'] = st.column_config.NumberColumn("subgroup_id", width=0, disabled=True)
                
                # Adiciona configuração para outros campos que possam existir (genérico)
                # Importa função de tradução
                from utils.translations import translate_column_name
                
                for col in edit_df.columns:
                    if col not in column_config and col not in ['_row_num', '_select', 'group_id', 'subgroup_id', 'group_name', 'subgroup_name']:
                        # Traduz nome da coluna para português
                        translated_col_name = translate_column_name(col)
                        
                        # Tenta inferir o tipo
                        if pd.api.types.is_bool_dtype(edit_df[col]):
                            # Colunas booleanas devem usar CheckboxColumn
                            column_config[col] = st.column_config.CheckboxColumn(translated_col_name, width="small")
                        elif pd.api.types.is_datetime64_any_dtype(edit_df[col]):
                            column_config[col] = st.column_config.DateColumn(translated_col_name, format="YYYY-MM-DD", width="small")
                        elif pd.api.types.is_numeric_dtype(edit_df[col]):
                            column_config[col] = st.column_config.NumberColumn(translated_col_name, width="small")
                        else:
                            column_config[col] = st.column_config.TextColumn(translated_col_name, width="medium")
                
                # Exibe tabela editável (com colunas traduzidas)
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
                    
                    # Atualiza dados (remove colunas internas e nomes, mantém apenas IDs)
                    row_dict = row.to_dict()
                    row_dict.pop('_row_num', None)
                    row_dict.pop('_select', None)
                    row_dict.pop('group_name', None)  # Remove nome, mantém apenas ID
                    row_dict.pop('subgroup_name', None)  # Remove nome, mantém apenas ID
                    
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
                    
                    # Adiciona nomes de grupos e subgrupos ao preview
                    db_preview = SessionLocal()
                    try:
                        group_mapping, subgroup_mapping = _get_group_subgroup_names_mapping(db_preview, client_id)
                        selected_data = _add_group_subgroup_names_to_data(selected_data, group_mapping, subgroup_mapping)
                    finally:
                        db_preview.close()
                    
                    selected_df = pd.DataFrame(selected_data)
                    
                    # Reordena colunas para mostrar nomes antes de IDs e ocultar IDs
                    preview_cols = []
                    for col in selected_df.columns:
                        if col not in ['group_id', 'subgroup_id']:
                            preview_cols.append(col)
                    
                    # Coloca group_name e subgroup_name antes de outras colunas (se existirem)
                    if 'group_name' in preview_cols:
                        preview_cols.remove('group_name')
                        preview_cols.insert(0, 'group_name')
                    if 'subgroup_name' in preview_cols:
                        preview_cols.remove('subgroup_name')
                        if 'group_name' in preview_cols:
                            preview_cols.insert(preview_cols.index('group_name') + 1, 'subgroup_name')
                        else:
                            preview_cols.insert(0, 'subgroup_name')
                    
                    selected_df = selected_df[preview_cols]
                    
                    st.dataframe(selected_df, use_container_width=True, height=300)
                    st.success(f"✅ {len(selected_indices)} linha(s) selecionada(s) para importação")
                else:
                    st.warning("⚠️ Nenhuma linha selecionada. Selecione pelo menos uma linha para importar.")
                
                st.markdown("---")
                st.subheader("9️⃣ Importação Final")
                
                # A IA já classificou cada linha individualmente com grupo/subgrupo
                # Não há necessidade de seleção manual, pois cada transação pode ser entrada, saída, resgate, etc.
                group_id = None
                subgroup_id = None
                bank_name = "Banco"
                
                st.info("💡 **Classificação Automática:** A IA já classificou cada linha individualmente com grupo e subgrupo baseado no contexto (entrada, saída, resgate, etc.). Você pode editar a classificação na tabela de revisão acima se necessário.")
                
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
                    # Filtra apenas linhas selecionadas
                    selected_indices = sorted(list(st.session_state.selected_rows))
                    data_to_import = [st.session_state.processed_data[i] for i in selected_indices if 0 <= i < len(st.session_state.processed_data)]
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
                    from datetime import datetime
                    if import_type == 'bank_statements' and imported_count > 0:
                        transactions_created = import_result.get('transactions', 0)
                        st.session_state.import_result = {
                            'status': 'success',
                            'import_type': import_type,
                            'count': imported_count,
                            'transactions_created': transactions_created,
                            'message': f"{imported_count} extrato(s) importado(s) e {transactions_created} transação(ões) criada(s) automaticamente!",
                            'timestamp': datetime.now().isoformat()
                        }
                        # Mensagem já foi exibida acima
                    elif import_type != 'bank_statements' and imported_count > 0:
                        st.session_state.import_result = {
                            'status': 'success',
                            'import_type': import_type,
                            'count': imported_count,
                            'message': f"{imported_count} registro(s) importado(s) com sucesso!",
                            'timestamp': datetime.now().isoformat()
                        }
                        st.success(f"✅ {imported_count} registro(s) importado(s) com sucesso!")
                        st.balloons()
                    elif imported_count == 0:
                        st.session_state.import_result = {
                            'status': 'warning',
                            'import_type': import_type,
                            'count': 0,
                            'message': "⚠️ Nenhum registro foi importado. Verifique os dados.",
                            'timestamp': datetime.now().isoformat()
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
    
    # Normaliza dados
    processed_data = [_ensure_classification_confidence(dict(record)) for record in processed_data]
    
    # Inicializa seleção
    if 'selected_rows' not in st.session_state:
        st.session_state.selected_rows = set(range(len(processed_data)))
    
    # Calcula valor total apenas dos registros selecionados
    selected_data = [processed_data[i] for i in st.session_state.selected_rows if 0 <= i < len(processed_data)]
    total_value_selected = sum(float(r.get('value', 0)) for r in selected_data if r.get('value') and pd.notna(r.get('value')))
    
    # Métricas em cards mais limpos
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Registros", f"{len(processed_data):,}".replace(',', '.'))
    with col2:
        type_display = type_names.get(detected_type, detected_type)
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
    
    st.markdown("---")
    st.subheader("✏️ Revisão e Edição")
    
    # Controles de seleção simplificados
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        if st.button("✅ Selecionar Todas", use_container_width=True):
            st.session_state.selected_rows = set(range(len(processed_data)))
            st.rerun()
    
    with col2:
        if st.button("❌ Desselecionar Todas", use_container_width=True):
            st.session_state.selected_rows = set()
            st.rerun()
        
    with col3:
        total_selected = len(st.session_state.selected_rows)
        st.info(f"📌 **{total_selected} de {len(processed_data)}** registros selecionados para importação")
    
    # Prepara dados para edição
    db_edit = SessionLocal()
    try:
        group_mapping, subgroup_mapping = _get_group_subgroup_names_mapping(db_edit, client_id)
    finally:
        db_edit.close()
    
    edit_data = []
    for idx, row in enumerate(processed_data):
        row_copy = row.copy()
        row_copy['_select'] = idx in st.session_state.selected_rows
        row_copy['_row_num'] = idx + 1
        edit_data.append(row_copy)
    
    # Adiciona nomes de grupos e subgrupos
    edit_data = _add_group_subgroup_names_to_data(edit_data, group_mapping, subgroup_mapping)
    edit_df = pd.DataFrame(edit_data)
    
    # Configura colunas para edição
    display_cols = ['_row_num', '_select']
    if 'group_name' in edit_df.columns:
        display_cols.append('group_name')
    if 'subgroup_name' in edit_df.columns:
        display_cols.append('subgroup_name')
    
    # Adiciona outras colunas
    for col in edit_df.columns:
        if col not in ['_row_num', '_select', 'group_id', 'subgroup_id', 'group_name', 'subgroup_name']:
            display_cols.append(col)
    
    # Adiciona colunas ocultas (group_id, subgroup_id)
    all_cols = display_cols + ['group_id', 'subgroup_id'] if 'group_id' in edit_df.columns else display_cols
    edit_df = edit_df[[c for c in all_cols if c in edit_df.columns]]
    
    # Configura colunas editáveis
    column_config = {
        "_row_num": st.column_config.NumberColumn("Linha", width="small", disabled=True),
        "_select": st.column_config.CheckboxColumn("Importar", width="small"),
    }
    
    if 'group_name' in edit_df.columns:
        column_config['group_name'] = st.column_config.TextColumn("Grupo", width="medium", disabled=True)
    if 'subgroup_name' in edit_df.columns:
        column_config['subgroup_name'] = st.column_config.TextColumn("Subgrupo", width="medium", disabled=True)
    if 'group_id' in edit_df.columns:
        column_config['group_id'] = st.column_config.NumberColumn("group_id", width=0, disabled=True)
    if 'subgroup_id' in edit_df.columns:
        column_config['subgroup_id'] = st.column_config.NumberColumn("subgroup_id", width=0, disabled=True)
    
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
    
    # Dica de uso
    if len(edit_df) > 10:
        st.caption(f"💡 **{len(edit_df)} registros encontrados.** Edite os dados diretamente na tabela e use as checkboxes para selecionar quais importar.")
    else:
        st.caption("💡 Edite os dados diretamente na tabela e selecione quais registros importar.")
    
    # Exibe tabela editável
    edited_df = st.data_editor(
        edit_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        height=min(600, max(400, len(edit_df) * 40)),
        key="data_editor_import"
    )
    
    # Atualiza seleção e dados
    new_selection = set()
    updated_data = []
    
    for idx, row in edited_df.iterrows():
        row_num = int(row.get('_row_num', idx + 1)) - 1
        if row.get('_select', False):
            new_selection.add(row_num)
        
        # Atualiza dados (remove colunas internas e nomes, mantém apenas IDs)
        row_dict = row.to_dict()
        row_dict.pop('_row_num', None)
        row_dict.pop('_select', None)
        row_dict.pop('group_name', None)
        row_dict.pop('subgroup_name', None)
        
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
    
    st.session_state.selected_rows = new_selection
    st.session_state.processed_data = updated_data
    
    # Recalcula valor total dos selecionados após edição e mostra atualização
    if new_selection != st.session_state.get('last_selection', set()):
        selected_data_updated = [updated_data[i] for i in new_selection if 0 <= i < len(updated_data)]
        total_value_selected_updated = sum(float(r.get('value', 0)) for r in selected_data_updated if r.get('value') and pd.notna(r.get('value')))
        if total_value_selected_updated != 0:
            from utils.formatters import format_currency
            st.info(f"💰 **Valor total atualizado:** {format_currency(total_value_selected_updated)} ({len(new_selection)} registro(s) selecionado(s))")
        st.session_state.last_selection = new_selection
    
    st.markdown("---")
    st.subheader("📥 Importação")
    
    # Configurações específicas por tipo (apenas se necessário)
    bank_name = "Banco"
    if detected_type == 'bank_statements':
        bank_name = summary.get('bank_name', 'Banco')
        if 'bank_name_override' not in st.session_state:
            st.session_state.bank_name_override = bank_name
        
        bank_name = st.text_input(
            "Nome do banco:",
            value=st.session_state.get('bank_name_override', bank_name),
            key="bank_name_input"
        )
        st.session_state.bank_name_override = bank_name
    
    # Botão de importar (mais destacado)
    col1, col2 = st.columns([1, 2])
    with col1:
        import_btn = st.button(
            "📥 **Importar Dados**",
            use_container_width=True,
            disabled=len(st.session_state.selected_rows) == 0,
            type="primary"
        )
    with col2:
        if len(st.session_state.selected_rows) == 0:
            st.warning("⚠️ Selecione pelo menos um registro para importar")
    
    if import_btn and len(st.session_state.selected_rows) > 0:
        # Filtra apenas linhas selecionadas
        selected_indices = sorted(list(st.session_state.selected_rows))
        data_to_import = [st.session_state.processed_data[i] for i in selected_indices if 0 <= i < len(st.session_state.processed_data)]
        import_df = pd.DataFrame(data_to_import)
        
        # Valida se há dados para importar
        if import_df.empty:
            st.error("❌ **Nenhum dado válido para importar.** Verifique se os registros selecionados contêm dados válidos.")
            st.stop()
        
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
        
        # Debug: mostra informações sobre os dados
        debug_info = st.expander("🔍 Debug: Informações dos dados selecionados", expanded=False)
        with debug_info:
            st.write(f"**Total de registros selecionados:** {len(import_df)}")
            st.write(f"**Colunas:** {list(import_df.columns)}")
            if 'date' in import_df.columns:
                date_valid = import_df['date'].notna().sum()
                st.write(f"**Datas válidas:** {date_valid}/{len(import_df)}")
                st.write(f"**Exemplo de datas:** {import_df['date'].head(3).tolist()}")
            if 'value' in import_df.columns:
                value_valid = import_df['value'].notna().sum()
                st.write(f"**Valores válidos:** {value_valid}/{len(import_df)}")
                st.write(f"**Exemplo de valores:** {import_df['value'].head(3).tolist()}")
            if 'group_id' in import_df.columns:
                group_valid = import_df['group_id'].notna().sum()
                st.write(f"**Group IDs válidos:** {group_valid}/{len(import_df)}")
            if 'subgroup_id' in import_df.columns:
                subgroup_valid = import_df['subgroup_id'].notna().sum()
                st.write(f"**Subgroup IDs válidos:** {subgroup_valid}/{len(import_df)}")
        
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
                
                if detected_type == 'transactions':
                    imported_count = ImportService.import_transactions(
                        db, client_id, import_df, 'imported', uploaded_file.name,
                        None, None, progress_callback=update_import_progress
                    )
                
                elif detected_type == 'bank_statements':
                    import_result = ImportService.import_bank_statements(
                        db, client_id, import_df, bank_name, uploaded_file.name,
                        None, None, progress_callback=update_import_progress
                    )
                    imported_count = import_result.get('statements', 0)
                    transactions_created = import_result.get('transactions', 0)
                
                elif detected_type == 'contracts':
                    imported_count = ImportService.import_contracts(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif detected_type == 'accounts_payable':
                    imported_count = ImportService.import_accounts_payable(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif detected_type == 'accounts_receivable':
                    imported_count = ImportService.import_accounts_receivable(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif detected_type == 'financial_investments':
                    imported_count = ImportService.import_financial_investments(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif detected_type == 'credit_card_invoices':
                    imported_count = ImportService.import_credit_card_invoices(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif detected_type == 'card_machine_statements':
                    imported_count = ImportService.import_card_machine_statements(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
                
                elif detected_type == 'inventory':
                    imported_count = ImportService.import_inventory(
                        db, client_id, import_df, None, None,
                        progress_callback=update_import_progress
                    )
            
            import_progress_container.empty()
            
            # Armazena resultado
            from datetime import datetime
            if detected_type == 'bank_statements' and imported_count > 0:
                transactions_created = import_result.get('transactions', 0)
                st.session_state.import_result = {
                    'status': 'success',
                    'import_type': detected_type,
                    'count': imported_count,
                    'transactions_created': transactions_created,
                    'message': f"{imported_count} extrato(s) importado(s) e {transactions_created} transação(ões) criada(s)!",
                    'timestamp': datetime.now().isoformat()
                }
                st.success(f"✅ {imported_count} extrato(s) importado(s) e {transactions_created} transação(ões) criada(s)!")
            elif imported_count > 0:
                st.session_state.import_result = {
                    'status': 'success',
                    'import_type': detected_type,
                    'count': imported_count,
                    'message': f"{imported_count} registro(s) importado(s) com sucesso!",
                    'timestamp': datetime.now().isoformat()
                }
                st.success(f"✅ {imported_count} registro(s) importado(s) com sucesso!")
                st.balloons()
            else:
                st.error("❌ **Nenhum registro foi importado.**")
                
                # Mostra informações de debug
                with st.expander("🔍 Detalhes do problema", expanded=True):
                    st.write(f"**Registros selecionados:** {len(st.session_state.selected_rows)}")
                    st.write(f"**Tipo de importação:** {detected_type}")
                    
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
                
                st.info("""
                **Soluções:**
                - Verifique os dados na tabela e corrija campos obrigatórios (data e valor)
                - Certifique-se de que as datas estão no formato correto (DD/MM/YYYY ou YYYY-MM-DD)
                - Verifique se os valores são números válidos
                - Verifique se os grupos/subgrupos estão corretos
                - Tente importar novamente após fazer as correções
                """)
            
            # Limpa estado após importação
            if imported_count > 0:
                if 'processed_data' in st.session_state:
                    del st.session_state.processed_data
                if 'selected_rows' in st.session_state:
                    del st.session_state.selected_rows
                if 'processed_file_hash' in st.session_state:
                    del st.session_state.processed_file_hash
                if 'bank_name_override' in st.session_state:
                    del st.session_state.bank_name_override
                st.rerun()
            
        except Exception as e:
            st.error(f"❌ Erro ao importar: {str(e)}")
            st.exception(e)
        finally:
            db.close()

else:
    st.info("💡 **Como funciona:** Faça upload do arquivo e o sistema processará automaticamente com IA Vision, detectando o tipo de dado e classificando por grupos/subgrupos.")
    
    st.markdown("---")
    with st.expander("ℹ️ Sobre o Processamento Automático"):
        st.markdown("""
        **Formatos Suportados:**
        - 📄 CSV, Excel, TXT
        - 📑 PDF (incluindo PDFs escaneados/imagens)
        - 🖼️ Imagens (JPG, PNG, TIFF, etc)
        - 💳 OFX (extratos bancários)
        
        **O que a IA faz automaticamente:**
        - ✅ Detecta o tipo de dado (transações, extratos, contratos, etc)
        - ✅ Extrai todos os dados estruturados
        - ✅ Classifica por grupos e subgrupos
        - ✅ Normaliza datas e valores
        - ✅ Identifica tipo de transação (entrada/saída)
        
        **Você só precisa:**
        1. Fazer upload do arquivo
        2. Revisar e editar se necessário
        3. Importar!
        """)








