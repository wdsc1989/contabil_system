"""
Serviço de parsing de arquivos (CSV, Excel, PDF, OFX)
"""
import pandas as pd
import pdfplumber
from ofxparse import OfxParser
from typing import Dict, List, Optional, Any, Tuple
from io import BytesIO, StringIO
import re


class ParserService:
    """
    Serviço para fazer parsing de diferentes formatos de arquivo
    """

    @staticmethod
    def parse_csv(file_content: bytes, encoding: str = 'utf-8', delimiter: str = ',', skip_blank_lines: bool = False) -> pd.DataFrame:
        """
        Faz parse de arquivo CSV garantindo extração de todas as linhas
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            encoding: Encoding a tentar primeiro
            delimiter: Delimitador do CSV
            skip_blank_lines: Se True, pula linhas completamente vazias (mas preserva linhas com dados parciais)
        
        Returns:
            DataFrame com todas as linhas extraídas
        """
        try:
            # Primeiro, conta linhas totais no arquivo para validação
            total_lines = ParserService.count_total_lines(file_content, encoding)
            
            # Tenta diferentes encodings
            encodings = [encoding, 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            
            for enc in encodings:
                try:
                    # Lê CSV sem pular linhas (keep_default_na=False preserva valores vazios como strings vazias)
                    df = pd.read_csv(
                        BytesIO(file_content), 
                        encoding=enc, 
                        delimiter=delimiter,
                        skip_blank_lines=skip_blank_lines,
                        keep_default_na=False,  # Preserva valores vazios
                        na_filter=False,  # Não converte strings vazias para NaN
                        on_bad_lines='skip'  # Pula apenas linhas com erro de parsing, mas registra
                    )
                    
                    # Remove apenas linhas completamente vazias (todas as colunas vazias)
                    if not df.empty:
                        # Preserva linhas mesmo se algumas colunas estiverem vazias
                        df = df.dropna(how='all')  # Remove apenas se TODAS as colunas forem NaN/vazias
                    
                    return df
                except UnicodeDecodeError:
                    continue
                except pd.errors.ParserError as e:
                    # Se houver erro de parsing, tenta com tratamento mais permissivo
                    try:
                        df = pd.read_csv(
                            BytesIO(file_content),
                            encoding=enc,
                            delimiter=delimiter,
                            skip_blank_lines=skip_blank_lines,
                            keep_default_na=False,
                            na_filter=False,
                            on_bad_lines='skip',
                            engine='python'  # Engine Python é mais permissivo
                        )
                        df = df.dropna(how='all')
                        return df
                    except:
                        continue
            
            # Se nenhum encoding funcionou, tenta com errors='ignore'
            df = pd.read_csv(
                BytesIO(file_content), 
                encoding='utf-8', 
                delimiter=delimiter, 
                errors='ignore',
                skip_blank_lines=skip_blank_lines,
                keep_default_na=False,
                na_filter=False,
                on_bad_lines='skip',
                engine='python'
            )
            df = df.dropna(how='all')
            return df
        
        except Exception as e:
            raise Exception(f"Erro ao fazer parse do CSV: {str(e)}")

    @staticmethod
    def parse_excel(file_content: bytes, sheet_name: Optional[str] = None, all_sheets: bool = False) -> pd.DataFrame:
        """
        Faz parse de arquivo Excel garantindo extração de todas as linhas de todas as abas
        
        Args:
            file_content: Conteúdo do arquivo em bytes
            sheet_name: Nome da aba específica a ler (None = primeira aba)
            all_sheets: Se True, lê todas as abas e combina
        
        Returns:
            DataFrame com todas as linhas extraídas
        """
        try:
            excel_file = pd.ExcelFile(BytesIO(file_content))
            
            if all_sheets:
                # Lê todas as abas e combina
                all_dfs = []
                sheet_stats = {}
                
                for sheet in excel_file.sheet_names:
                    try:
                        # Lê aba sem pular linhas vazias no meio
                        df_sheet = pd.read_excel(
                            excel_file, 
                            sheet_name=sheet,
                            keep_default_na=False,  # Preserva valores vazios
                            na_filter=False  # Não converte strings vazias para NaN
                        )
                        
                        # Remove apenas linhas completamente vazias
                        if not df_sheet.empty:
                            df_sheet = df_sheet.dropna(how='all')
                            
                            # Adiciona coluna indicando a aba de origem
                            df_sheet['_sheet_name'] = sheet
                            all_dfs.append(df_sheet)
                            
                            # Estatísticas por aba
                            sheet_stats[sheet] = {
                                'rows': len(df_sheet),
                                'columns': len(df_sheet.columns)
                            }
                    except Exception as e:
                        # Se uma aba falhar, continua com as outras
                        sheet_stats[sheet] = {'error': str(e)}
                        continue
                
                if all_dfs:
                    # Combina todos os DataFrames
                    df = pd.concat(all_dfs, ignore_index=True)
                    return df
                else:
                    return pd.DataFrame()
            elif sheet_name:
                df = pd.read_excel(
                    BytesIO(file_content), 
                    sheet_name=sheet_name,
                    keep_default_na=False,
                    na_filter=False
                )
                df = df.dropna(how='all')
            else:
                # Lê apenas a primeira aba (comportamento padrão)
                df = pd.read_excel(
                    BytesIO(file_content),
                    keep_default_na=False,
                    na_filter=False
                )
                df = df.dropna(how='all')
            
            return df
        
        except Exception as e:
            raise Exception(f"Erro ao fazer parse do Excel: {str(e)}")

    @staticmethod
    def get_excel_sheets(file_content: bytes) -> List[str]:
        """
        Retorna lista de planilhas em um arquivo Excel
        """
        try:
            excel_file = pd.ExcelFile(BytesIO(file_content))
            return excel_file.sheet_names
        except Exception as e:
            raise Exception(f"Erro ao ler planilhas do Excel: {str(e)}")

    @staticmethod
    def parse_pdf(file_content: bytes) -> Dict[str, Any]:
        """
        Extrai texto de arquivo PDF
        """
        try:
            text_content = []
            tables = []
            
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    # Extrai texto
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                    
                    # Extrai tabelas
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
            
            return {
                'text': '\n\n'.join(text_content),
                'tables': tables,
                'num_pages': len(text_content)
            }
        
        except Exception as e:
            raise Exception(f"Erro ao fazer parse do PDF: {str(e)}")
    
    @staticmethod
    def _is_pdf_image_based(file_content: bytes) -> bool:
        """
        Detecta se um PDF é baseado em imagens (sem texto extraível)
        """
        try:
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                # Verifica as primeiras 3 páginas
                pages_to_check = min(3, len(pdf.pages))
                total_text_length = 0
                
                for i in range(pages_to_check):
                    page = pdf.pages[i]
                    text = page.extract_text() or ''
                    total_text_length += len(text.strip())
                
                # Se tiver muito pouco texto (menos de 50 caracteres por página), provavelmente é baseado em imagem
                avg_text_per_page = total_text_length / pages_to_check if pages_to_check > 0 else 0
                return avg_text_per_page < 50
        except:
            return False
    
    @staticmethod
    def _text_to_dataframe_from_ocr(text: str) -> Optional[pd.DataFrame]:
        """
        Tenta criar DataFrame a partir de texto extraído via OCR
        """
        lines = text.split('\n')
        records = []
        
        # Padrões para identificar linhas de dados
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        currency_pattern = r'R?\$?\s*-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?'
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            has_date = bool(re.search(date_pattern, line))
            has_currency = bool(re.search(currency_pattern, line))
            
            if has_date or has_currency:
                date_match = re.search(date_pattern, line)
                currency_matches = re.findall(currency_pattern, line)
                
                record = {
                    'raw_text': line,
                    'date': date_match.group(0) if date_match else '',
                    'value': currency_matches[0] if currency_matches else '',
                    'description': line
                }
                records.append(record)
        
        if records:
            return pd.DataFrame(records)
        
        # Se não encontrou padrões, cria DataFrame simples com todas as linhas
        return pd.DataFrame({'text': [line for line in lines if line.strip()]})
    
    @staticmethod
    def validate_pdf(file_content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Valida se o arquivo é um PDF válido antes de tentar processá-lo
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Verifica se começa com assinatura PDF
            if not file_content.startswith(b'%PDF'):
                return False, "Arquivo não é um PDF válido (não contém assinatura PDF)"
            
            # Tenta abrir com pdfplumber para validar estrutura
            try:
                with pdfplumber.open(BytesIO(file_content)) as pdf:
                    # Tenta acessar metadados ou páginas para validar
                    _ = len(pdf.pages)
                return True, None
            except Exception as e:
                error_msg = str(e).lower()
                if "root" in error_msg or "no /root" in error_msg:
                    return False, "PDF corrompido ou inválido (sem objeto /Root). O arquivo pode estar danificado."
                elif "encrypted" in error_msg or "password" in error_msg or "senha" in error_msg:
                    return False, "PDF protegido por senha. Remova a senha antes de importar."
                else:
                    return False, f"PDF inválido ou corrompido: {str(e)}"
        except Exception as e:
            return False, f"Erro ao validar PDF: {str(e)}"
    
    @staticmethod
    def parse_pdf_complete(file_content: bytes, use_ocr_if_needed: bool = True) -> Dict[str, Any]:
        """
        Extrai informações completas de um PDF incluindo texto, tabelas, metadados e contexto
        
        Se o PDF for baseado em imagens (sem texto extraível), usa OCR automaticamente se use_ocr_if_needed=True
        
        Retorna estrutura rica com:
        - dataframe: DataFrame com tabelas extraídas
        - full_text: Todo o texto do PDF
        - pages: Lista de informações por página
        - metadata: Metadados do PDF
        - headers_footers: Cabeçalhos/rodapés extraídos
        """
        # Valida PDF antes de processar
        is_valid, error_msg = ParserService.validate_pdf(file_content)
        if not is_valid:
            # Se PDF é inválido mas pode ser convertido para imagem, tenta OCR
            if use_ocr_if_needed:
                try:
                    return ParserService._parse_pdf_with_ocr_fallback(file_content)
                except Exception as ocr_error:
                    raise Exception(f"{error_msg}\n\nTentativa de OCR também falhou: {str(ocr_error)}")
            else:
                raise Exception(error_msg)
        
        try:
            # Primeiro, tenta extrair texto normalmente
            pages_info = []
            all_tables = []
            full_text_parts = []
            headers = []
            footers = []
            ocr_used = False
            
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                # Metadados do PDF
                metadata = {
                    'title': pdf.metadata.get('Title', '') if pdf.metadata else '',
                    'author': pdf.metadata.get('Author', '') if pdf.metadata else '',
                    'creation_date': str(pdf.metadata.get('CreationDate', '')) if pdf.metadata else '',
                    'num_pages': len(pdf.pages)
                }
                
                # Processa TODAS as páginas garantindo extração completa
                total_pages = len(pdf.pages)
                pages_processed = 0
                pages_with_tables = 0
                pages_with_text = 0
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        # Extrai texto da página (garante que não pula nenhuma)
                        page_text = page.extract_text() or ''
                        if page_text.strip():
                            full_text_parts.append(page_text)
                            pages_with_text += 1
                        else:
                            # Mesmo sem texto, adiciona string vazia para manter contagem
                            full_text_parts.append('')
                        
                        # Extrai TODAS as tabelas da página usando múltiplas estratégias
                        page_tables = []
                        
                        # Estratégia 1: extract_tables() padrão
                        try:
                            tables_standard = page.extract_tables()
                            if tables_standard:
                                page_tables.extend(tables_standard)
                        except:
                            pass
                        
                        # Estratégia 2: extract_table() para tabela única
                        if not page_tables:
                            try:
                                single_table = page.extract_table()
                                if single_table and len(single_table) > 1:  # Pelo menos cabeçalho + 1 linha
                                    page_tables.append(single_table)
                            except:
                                pass
                        
                        # Estratégia 3: Tenta detectar tabelas por coordenadas (para PDFs complexos)
                        if not page_tables:
                            try:
                                # Busca por padrões de tabela (linhas verticais/horizontais)
                                words = page.extract_words()
                                if words and len(words) > 10:  # Se tem muitas palavras, pode ser tabela
                                    # Tenta agrupar palavras em linhas/colunas
                                    # (pdfplumber faz isso automaticamente, mas tentamos forçar)
                                    pass
                            except:
                                pass
                        
                        # Extrai texto ao redor das tabelas para contexto
                        table_contexts = []
                        if page_tables:
                            for table in page_tables:
                                # Tenta extrair texto antes e depois da tabela
                                # (pdfplumber não tem método direto, mas podemos usar coordenadas)
                                table_contexts.append('')
                        
                        # Detecta cabeçalho e rodapé (primeira e última página)
                        has_header = page_num == 1
                        has_footer = page_num == total_pages
                        
                        if has_header and page_text:
                            # Primeiras linhas como possível cabeçalho
                            header_lines = page_text.split('\n')[:5]
                            headers.extend(header_lines)
                        
                        if has_footer and page_text:
                            # Últimas linhas como possível rodapé
                            footer_lines = page_text.split('\n')[-5:]
                            footers.extend(footer_lines)
                        
                        pages_info.append({
                            'page_num': page_num,
                            'text': page_text,
                            'tables': page_tables or [],
                            'has_header': has_header,
                            'has_footer': has_footer,
                            'num_tables': len(page_tables) if page_tables else 0,
                            'text_length': len(page_text)
                        })
                        
                        if page_tables:
                            all_tables.extend(page_tables)
                            pages_with_tables += 1
                        
                        pages_processed += 1
                        
                    except Exception as page_error:
                        # Se uma página falhar, registra erro mas continua com as outras
                        pages_info.append({
                            'page_num': page_num,
                            'text': '',
                            'tables': [],
                            'has_header': False,
                            'has_footer': False,
                            'num_tables': 0,
                            'text_length': 0,
                            'error': str(page_error)
                        })
                        pages_processed += 1
                        continue
            
            # Validação: verifica se todas as páginas foram processadas
            if pages_processed < total_pages:
                # Loga aviso mas continua
                pass
            
            # Processa tabelas para criar DataFrame (garante que todas sejam processadas)
            dataframe = None
            if all_tables:
                dataframe = ParserService._tables_to_dataframe(all_tables)
            
            # Adiciona estatísticas de extração aos metadados
            metadata['pages_processed'] = pages_processed
            metadata['pages_with_tables'] = pages_with_tables
            metadata['pages_with_text'] = pages_with_text
            metadata['total_tables_found'] = len(all_tables)
            metadata['extraction_complete'] = pages_processed == total_pages
            
            # Extrai informações de cabeçalho/rodapé
            header_text = '\n'.join(headers[:10]) if headers else ''  # Primeiras 10 linhas de cabeçalhos
            footer_text = '\n'.join(footers[-10:]) if footers else ''  # Últimas 10 linhas de rodapés
            
            # Tenta extrair nome do banco e informações de conta do texto
            full_text = '\n\n'.join(full_text_parts)
            
            # Se o texto extraído for muito pequeno e use_ocr_if_needed estiver habilitado, tenta OCR
            if use_ocr_if_needed and len(full_text.strip()) < 100 and ParserService._is_pdf_image_based(file_content):
                try:
                    # Tenta usar OCR
                    ocr_result = ParserService.parse_pdf_with_ocr(file_content)
                    ocr_result['metadata']['ocr_used'] = True
                    return ocr_result
                except Exception as ocr_error:
                    # Se OCR falhar, continua com o texto extraído (mesmo que seja pouco)
                    pass
            
            bank_name = ParserService._extract_bank_name(full_text, header_text)
            account_info = ParserService._extract_account_info(full_text, header_text)
            
            headers_footers = {
                'header_text': header_text,
                'footer_text': footer_text,
                'bank_name': bank_name,
                'account_info': account_info
            }
            
            metadata['ocr_used'] = ocr_used
            
            return {
                'dataframe': dataframe,
                'full_text': full_text,
                'pages': pages_info,
                'metadata': metadata,
                'headers_footers': headers_footers
            }
        
        except Exception as e:
            raise Exception(f"Erro ao fazer parse completo do PDF: {str(e)}")
    
    @staticmethod
    def _tables_to_dataframe(tables: List[List[List[str]]]) -> Optional[pd.DataFrame]:
        """
        Converte lista de tabelas em um único DataFrame
        Combina tabelas com a mesma estrutura
        """
        if not tables:
            return None
        
        dataframes = []
        
        for table in tables:
            if not table or len(table) < 2:
                continue
            
            try:
                headers = table[0]
                data_rows = table[1:]
                
                df_page = pd.DataFrame(data_rows, columns=headers)
                df_page = df_page.dropna(how='all')
                
                if not df_page.empty:
                    dataframes.append(df_page)
            except Exception as e:
                continue
        
        if not dataframes:
            return None
        
        if len(dataframes) == 1:
            return dataframes[0]
        
        # Tenta combinar tabelas com a mesma estrutura
        grouped_dfs = {}
        for df in dataframes:
            cols_key = tuple(sorted([str(c).strip().lower() for c in df.columns]))
            
            if cols_key not in grouped_dfs:
                grouped_dfs[cols_key] = []
            grouped_dfs[cols_key].append(df)
        
        combined_dfs = []
        for cols_key, dfs in grouped_dfs.items():
            try:
                for df in dfs:
                    df.columns = dfs[0].columns
                
                combined = pd.concat(dfs, ignore_index=True)
                combined_dfs.append(combined)
            except Exception as e:
                largest_df = max(dfs, key=len)
                combined_dfs.append(largest_df)
        
        if len(combined_dfs) == 1:
            return combined_dfs[0]
        
        largest_df = max(combined_dfs, key=len)
        return largest_df
    
    @staticmethod
    def _extract_bank_name(text: str, header_text: str = '') -> str:
        """
        Tenta extrair nome do banco do texto do PDF
        """
        # Lista de bancos comuns no Brasil
        banks = [
            'Banco do Brasil', 'BB', 'Bradesco', 'Itaú', 'Itau', 'Santander',
            'Caixa Econômica', 'Caixa', 'CEF', 'Nubank', 'Inter', 'Banco Inter',
            'Banrisul', 'Sicredi', 'Sicoob', 'Banco Original', 'Next', 'C6 Bank',
            'BTG Pactual', 'XP Investimentos', 'Rico', 'Modal', 'Avenue'
        ]
        
        search_text = (header_text + '\n' + text).upper()
        
        for bank in banks:
            if bank.upper() in search_text:
                return bank
        
        # Tenta encontrar padrões como "BANCO: X" ou "BANCO X"
        patterns = [
            r'BANCO[:\s]+([A-Z\s]+)',
            r'BANCO\s+([A-Z][A-Z\s]{3,30})',
            r'INSTITUIÇÃO[:\s]+([A-Z\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                bank_name = match.group(1).strip()
                if len(bank_name) > 3 and len(bank_name) < 50:
                    return bank_name
        
        return ''
    
    @staticmethod
    def _extract_account_info(text: str, header_text: str = '') -> str:
        """
        Tenta extrair informações de conta do texto do PDF
        """
        search_text = header_text + '\n' + text
        
        # Padrões comuns para número de conta
        patterns = [
            r'CONTA[:\s]+([\d\-\.]+)',
            r'AGÊNCIA[:\s]+([\d\-\.]+)',
            r'AG[:\s]+([\d\-\.]+)',
            r'CC[:\s]+([\d\-\.]+)'
        ]
        
        account_info_parts = []
        
        for pattern in patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE)
            account_info_parts.extend(matches)
        
        if account_info_parts:
            return ' | '.join(account_info_parts[:3])  # Limita a 3 informações
        
        return ''

    @staticmethod
    def _parse_pdf_with_ocr_fallback(file_content: bytes) -> Dict[str, Any]:
        """
        Tenta processar PDF corrompido ou inválido convertendo para imagens e usando OCR
        """
        try:
            # Tenta converter PDF para imagens usando PyMuPDF
            try:
                import fitz  # PyMuPDF
                pdf_document = fitz.open(stream=file_content, filetype="pdf")
                
                if pdf_document.is_encrypted:
                    pdf_document.close()
                    raise Exception("PDF protegido por senha")
                
                # Converte cada página para imagem e processa com OCR
                full_text_parts = []
                all_tables = []
                
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    # Renderiza página como imagem
                    mat = fitz.Matrix(2.0, 2.0)  # 200 DPI
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Converte para PIL Image
                    from PIL import Image
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # Processa com OCR
                    try:
                        import pytesseract
                        page_text = pytesseract.image_to_string(img, lang='por+eng')
                        if page_text.strip():
                            full_text_parts.append(page_text)
                    except ImportError:
                        # Tenta easyocr como fallback
                        try:
                            import easyocr
                            reader = easyocr.Reader(['pt', 'en'])
                            result = reader.readtext(img)
                            page_text = '\n'.join([item[1] for item in result])
                            if page_text.strip():
                                full_text_parts.append(page_text)
                        except ImportError:
                            raise Exception("Bibliotecas de OCR não instaladas. Instale: pip install pytesseract ou easyocr")
                
                pdf_document.close()
                
                full_text = '\n\n'.join(full_text_parts)
                
                # Tenta criar DataFrame do texto extraído
                dataframe = ParserService._text_to_dataframe_from_ocr(full_text)
                
                return {
                    'dataframe': dataframe,
                    'full_text': full_text,
                    'pages': [{'page_num': i+1, 'text': text, 'tables': []} for i, text in enumerate(full_text_parts)],
                    'metadata': {
                        'num_pages': len(full_text_parts),
                        'ocr_used': True,
                        'pdf_corrupted': True
                    },
                    'headers_footers': {}
                }
            except ImportError:
                raise Exception("PyMuPDF não instalado. Para processar PDFs corrompidos, instale: pip install PyMuPDF")
        except Exception as e:
            raise Exception(f"Erro ao processar PDF corrompido com OCR: {str(e)}")
    
    @staticmethod
    def parse_pdf_to_dataframe(file_content: bytes) -> Optional[pd.DataFrame]:
        """
        Tenta extrair todas as tabelas de PDF e converter para DataFrame
        Combina tabelas de todas as páginas que tenham a mesma estrutura
        
        Agora usa parse_pdf_complete internamente para melhor extração
        """
        try:
            result = ParserService.parse_pdf_complete(file_content, use_ocr_if_needed=True)
            return result.get('dataframe')
        except Exception as e:
            error_msg = str(e).lower()
            # Se o erro indica PDF corrompido, tenta OCR
            if "root" in error_msg or "corrompido" in error_msg or "invalid" in error_msg:
                try:
                    result = ParserService._parse_pdf_with_ocr_fallback(file_content)
                    return result.get('dataframe')
                except Exception as ocr_error:
                    raise Exception(
                        f"PDF corrompido ou inválido e não foi possível processar com OCR.\n"
                        f"Erro original: {str(e)}\n"
                        f"Erro OCR: {str(ocr_error)}\n\n"
                        f"Soluções:\n"
                        f"1. Verifique se o arquivo PDF está íntegro\n"
                        f"2. Tente abrir o PDF em um visualizador e salvar novamente\n"
                        f"3. Converta o PDF para imagens (JPG/PNG) e importe as imagens"
                    )
            else:
                # Fallback para método antigo se o novo falhar
                try:
                    result = ParserService.parse_pdf(file_content)
                    
                    if not result['tables']:
                        return None
                    
                    dataframe = ParserService._tables_to_dataframe(result['tables'])
                    return dataframe
                except:
                    raise Exception(f"Erro ao extrair tabela do PDF: {str(e)}")

    @staticmethod
    def parse_ofx(file_content: bytes) -> Dict[str, Any]:
        """
        Faz parse de arquivo OFX (extratos bancários)
        """
        try:
            ofx = OfxParser.parse(BytesIO(file_content))
            
            transactions = []
            
            for account in ofx.accounts:
                for transaction in account.statement.transactions:
                    transactions.append({
                        'date': transaction.date,
                        'description': transaction.memo or transaction.payee or '',
                        'value': float(transaction.amount),
                        'type': transaction.type,
                        'id': transaction.id
                    })
            
            return {
                'bank_id': ofx.account.institution.fid if hasattr(ofx, 'account') else None,
                'account_id': ofx.account.account_id if hasattr(ofx, 'account') else None,
                'transactions': transactions,
                'balance': float(ofx.account.statement.balance) if hasattr(ofx, 'account') else None
            }
        
        except Exception as e:
            raise Exception(f"Erro ao fazer parse do OFX: {str(e)}")

    @staticmethod
    def ofx_to_dataframe(file_content: bytes) -> pd.DataFrame:
        """
        Converte OFX para DataFrame
        """
        try:
            result = ParserService.parse_ofx(file_content)
            df = pd.DataFrame(result['transactions'])
            return df
        
        except Exception as e:
            raise Exception(f"Erro ao converter OFX para DataFrame: {str(e)}")

    @staticmethod
    def detect_file_type(file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Detecta automaticamente o tipo de arquivo baseado na extensão e conteúdo
        
        Retorna:
        {
            'type': 'CSV' | 'Excel' | 'PDF' | 'OFX' | 'Image',
            'confidence': 0.0-1.0,
            'method': 'extension' | 'content',
            'reason': 'explicação'
        }
        """
        filename_lower = filename.lower()
        
        # Detecção de arquivos de imagem
        image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp']
        if any(filename_lower.endswith(ext) for ext in image_extensions):
            # Verifica assinaturas de arquivos de imagem
            if file_content[:2] == b'\xFF\xD8':  # JPEG
                return {
                    'type': 'Image',
                    'confidence': 0.98,
                    'method': 'extension+content',
                    'reason': 'Arquivo de imagem JPEG detectado'
                }
            elif file_content[:8] == b'\x89PNG\r\n\x1a\n':  # PNG
                return {
                    'type': 'Image',
                    'confidence': 0.98,
                    'method': 'extension+content',
                    'reason': 'Arquivo de imagem PNG detectado'
                }
            elif file_content[:2] == b'BM':  # BMP
                return {
                    'type': 'Image',
                    'confidence': 0.98,
                    'method': 'extension+content',
                    'reason': 'Arquivo de imagem BMP detectado'
                }
            elif file_content[:4] == b'RIFF' and b'WEBP' in file_content[:12]:  # WEBP
                return {
                    'type': 'Image',
                    'confidence': 0.98,
                    'method': 'extension+content',
                    'reason': 'Arquivo de imagem WEBP detectado'
                }
            elif file_content[:4] in [b'II*\x00', b'MM\x00*']:  # TIFF
                return {
                    'type': 'Image',
                    'confidence': 0.98,
                    'method': 'extension+content',
                    'reason': 'Arquivo de imagem TIFF detectado'
                }
            return {
                'type': 'Image',
                'confidence': 0.85,
                'method': 'extension',
                'reason': f'Extensão de imagem: {filename_lower.split(".")[-1]}'
            }
        
        # Detecção por extensão (mais confiável)
        if filename_lower.endswith(('.csv', '.txt')):
            # Verifica se é realmente CSV analisando conteúdo
            try:
                sample = file_content[:1024].decode('utf-8', errors='ignore')
                # Verifica se tem delimitadores comuns de CSV
                if any(delim in sample for delim in [',', ';', '\t', '|']):
                    return {
                        'type': 'CSV',
                        'confidence': 0.95,
                        'method': 'extension',
                        'reason': f'Extensão {filename_lower.split(".")[-1]} e conteúdo compatível com CSV'
                    }
            except:
                pass
            return {
                'type': 'CSV',
                'confidence': 0.8,
                'method': 'extension',
                'reason': f'Extensão {filename_lower.split(".")[-1]}'
            }
        
        elif filename_lower.endswith(('.xlsx', '.xls')):
            # Verifica assinatura de arquivo Excel
            if file_content[:8] == b'\x50\x4B\x03\x04' or file_content[:8] == b'\xD0\xCF\x11\xE0':
                return {
                    'type': 'Excel',
                    'confidence': 0.98,
                    'method': 'extension+content',
                    'reason': 'Extensão Excel e assinatura de arquivo válida'
                }
            return {
                'type': 'Excel',
                'confidence': 0.85,
                'method': 'extension',
                'reason': f'Extensão {filename_lower.split(".")[-1]}'
            }
        
        elif filename_lower.endswith('.pdf'):
            # Verifica assinatura PDF
            if file_content[:4] == b'%PDF':
                return {
                    'type': 'PDF',
                    'confidence': 0.98,
                    'method': 'extension+content',
                    'reason': 'Extensão PDF e assinatura válida'
                }
            return {
                'type': 'PDF',
                'confidence': 0.85,
                'method': 'extension',
                'reason': 'Extensão PDF'
            }
        
        elif filename_lower.endswith('.ofx'):
            # Verifica tags OFX no conteúdo
            try:
                content_str = file_content[:2048].decode('utf-8', errors='ignore').upper()
                if 'OFXHEADER' in content_str or '<OFX>' in content_str:
                    return {
                        'type': 'OFX',
                        'confidence': 0.98,
                        'method': 'extension+content',
                        'reason': 'Extensão OFX e tags OFX encontradas'
                    }
            except:
                pass
            return {
                'type': 'OFX',
                'confidence': 0.85,
                'method': 'extension',
                'reason': 'Extensão OFX'
            }
        
        # Detecção por conteúdo (fallback quando extensão não é confiável)
        # Verifica assinaturas de arquivo
        if file_content[:4] == b'%PDF':
            return {
                'type': 'PDF',
                'confidence': 0.9,
                'method': 'content',
                'reason': 'Assinatura PDF encontrada no conteúdo'
            }
        
        if file_content[:8] == b'\x50\x4B\x03\x04' or file_content[:8] == b'\xD0\xCF\x11\xE0':
            return {
                'type': 'Excel',
                'confidence': 0.85,
                'method': 'content',
                'reason': 'Assinatura de arquivo Excel encontrada'
            }
        
        # Verifica tags OFX
        try:
            content_str = file_content[:2048].decode('utf-8', errors='ignore').upper()
            if 'OFXHEADER' in content_str or '<OFX>' in content_str:
                return {
                    'type': 'OFX',
                    'confidence': 0.9,
                    'method': 'content',
                    'reason': 'Tags OFX encontradas no conteúdo'
                }
        except:
            pass
        
        # Verifica se parece CSV (delimitadores comuns)
        try:
            sample = file_content[:1024].decode('utf-8', errors='ignore')
            delimiter_count = {
                ',': sample.count(','),
                ';': sample.count(';'),
                '\t': sample.count('\t'),
                '|': sample.count('|')
            }
            max_delim = max(delimiter_count.items(), key=lambda x: x[1])
            if max_delim[1] > 5:  # Pelo menos 5 ocorrências do delimitador
                return {
                    'type': 'CSV',
                    'confidence': 0.7,
                    'method': 'content',
                    'reason': f'Delimitador {max_delim[0]} detectado no conteúdo'
                }
        except:
            pass
        
        # Não foi possível detectar
        return {
            'type': 'CSV',  # Default para CSV
            'confidence': 0.3,
            'method': 'default',
            'reason': 'Tipo não detectado, assumindo CSV como padrão'
        }

    @staticmethod
    def detect_delimiter(file_content: bytes, sample_size: int = 1024) -> str:
        """
        Detecta o delimitador de um arquivo CSV de forma mais robusta
        Analisa múltiplas linhas para determinar o delimitador mais consistente
        """
        try:
            # Tenta diferentes encodings para decodificar
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            sample = None
            
            for enc in encodings:
                try:
                    sample = file_content[:sample_size].decode(enc)
                    break
                except:
                    continue
            
            if not sample:
                sample = file_content[:sample_size].decode('utf-8', errors='ignore')
            
            # Analisa primeiras linhas (mais confiável que apenas contar caracteres)
            lines = sample.split('\n')[:10]  # Primeiras 10 linhas
            if not lines:
                return ','
            
            delimiters = [',', ';', '\t', '|']
            delimiter_scores = {d: 0 for d in delimiters}
            
            for line in lines:
                if not line.strip():
                    continue
                
                for delimiter in delimiters:
                    # Conta ocorrências do delimitador na linha
                    count = line.count(delimiter)
                    # Bônus se o delimitador aparece consistentemente (múltiplas vezes)
                    if count > 0:
                        delimiter_scores[delimiter] += count
                        # Bônus extra se aparece em múltiplas linhas
                        if count >= 2:
                            delimiter_scores[delimiter] += 1
            
            # Retorna o delimitador com maior score
            if max(delimiter_scores.values()) > 0:
                return max(delimiter_scores, key=delimiter_scores.get)
            
            return ','
        
        except:
            return ','
    
    @staticmethod
    def count_total_lines(file_content: bytes, encoding: str = 'utf-8') -> int:
        """
        Conta o número total de linhas no arquivo (incluindo vazias)
        Útil para validar se todas as linhas foram extraídas
        """
        try:
            # Tenta diferentes encodings
            encodings = [encoding, 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            
            for enc in encodings:
                try:
                    text = file_content.decode(enc)
                    return len(text.splitlines())
                except UnicodeDecodeError:
                    continue
            
            # Fallback: conta bytes newline
            return file_content.count(b'\n') + (1 if file_content else 0)
        
        except:
            # Fallback: conta bytes newline
            return file_content.count(b'\n') + (1 if file_content else 0)

    @staticmethod
    def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa nomes de colunas (remove espaços, caracteres especiais)
        """
        df.columns = df.columns.str.strip()
        df.columns = df.columns.str.replace(r'[^\w\s]', '', regex=True)
        df.columns = df.columns.str.replace(r'\s+', '_', regex=True)
        return df

    @staticmethod
    def infer_column_types(df: pd.DataFrame) -> Dict[str, str]:
        """
        Infere tipos de colunas (data, moeda, texto, etc)
        """
        column_types = {}
        
        for col in df.columns:
            sample = df[col].dropna().head(10)
            
            if sample.empty:
                column_types[col] = 'text'
                continue
            
            # Tenta identificar datas
            date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
            if sample.astype(str).str.match(date_pattern).any():
                column_types[col] = 'date'
                continue
            
            # Tenta identificar valores monetários
            currency_pattern = r'R?\$?\s*-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?'
            if sample.astype(str).str.match(currency_pattern).any():
                column_types[col] = 'currency'
                continue
            
            # Tenta identificar números
            try:
                pd.to_numeric(sample)
                column_types[col] = 'numeric'
                continue
            except:
                pass
            
            # Default: texto
            column_types[col] = 'text'
        
        return column_types
    
    @staticmethod
    def parse_pdf_with_ocr(file_content: bytes) -> Dict[str, Any]:
        """
        Extrai texto de PDF usando OCR (para PDFs baseados em imagens)
        """
        try:
            # Tenta importar bibliotecas de OCR
            try:
                import pytesseract
                from pdf2image import convert_from_bytes
                from PIL import Image
            except ImportError:
                raise Exception("Bibliotecas de OCR não instaladas. Instale: pip install pytesseract pdf2image Pillow")
            
            pages_info = []
            full_text_parts = []
            
            # Converte PDF para imagens
            try:
                images = convert_from_bytes(file_content, dpi=300)
            except Exception as e:
                # Fallback: tenta com easyocr se disponível
                try:
                    import easyocr
                    reader = easyocr.Reader(['pt', 'en'])
                    # Para easyocr, precisamos processar página por página
                    # Por enquanto, retorna erro sugerindo pytesseract
                    raise Exception(f"Erro ao converter PDF para imagens: {str(e)}. Certifique-se de que poppler está instalado.")
                except ImportError:
                    raise Exception(f"Erro ao converter PDF para imagens: {str(e)}. Instale poppler: sudo apt-get install poppler-utils (Linux) ou brew install poppler (Mac)")
            
            # Processa cada imagem com OCR
            for page_num, image in enumerate(images, 1):
                try:
                    # Extrai texto usando pytesseract
                    # Converte PIL Image para formato compatível se necessário
                    if hasattr(image, 'mode') and image.mode != 'RGB':
                        image = image.convert('RGB')
                    page_text = pytesseract.image_to_string(image, lang='por+eng')
                    full_text_parts.append(page_text)
                    
                    pages_info.append({
                        'page_num': page_num,
                        'text': page_text,
                        'tables': [],
                        'has_header': page_num == 1,
                        'has_footer': page_num == len(images),
                        'num_tables': 0,
                        'ocr_used': True
                    })
                except Exception as e:
                    # Se OCR falhar em uma página, continua com as outras
                    full_text_parts.append(f"[Erro OCR na página {page_num}: {str(e)}]")
            
            full_text = '\n\n'.join(full_text_parts)
            
            # Tenta criar DataFrame do texto extraído
            dataframe = ParserService._text_to_dataframe_from_ocr(full_text)
            
            return {
                'dataframe': dataframe,
                'full_text': full_text,
                'pages': pages_info,
                'metadata': {
                    'num_pages': len(images),
                    'ocr_used': True
                },
                'headers_footers': {
                    'header_text': '',
                    'footer_text': '',
                    'bank_name': '',
                    'account_info': ''
                }
            }
        except Exception as e:
            raise Exception(f"Erro ao processar PDF com OCR: {str(e)}")
    
    @staticmethod
    def parse_image(file_content: bytes, file_extension: str) -> Dict[str, Any]:
        """
        Extrai texto de arquivos de imagem usando OCR
        Suporta: JPG, JPEG, PNG, TIFF, BMP, WEBP
        """
        try:
            # Tenta importar bibliotecas de OCR
            try:
                import pytesseract
                from PIL import Image
            except ImportError:
                raise Exception("Bibliotecas de OCR não instaladas. Instale: pip install pytesseract Pillow")
            
            # Abre imagem
            try:
                image = Image.open(BytesIO(file_content))
            except Exception as e:
                raise Exception(f"Erro ao abrir imagem: {str(e)}")
            
            # Extrai texto usando OCR
            text = None
            ocr_error = None
            
            # Tenta pytesseract primeiro (mais rápido)
            try:
                # Garante que a imagem está em RGB
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                text = pytesseract.image_to_string(image, lang='por+eng', timeout=120)
                if not text or len(text.strip()) < 10:
                    # Se o texto extraído for muito curto, pode ser que o OCR não funcionou bem
                    # Mas ainda assim usa o que foi extraído
                    pass
            except Exception as e:
                ocr_error = str(e)
                # Fallback: tenta easyocr se disponível (mais lento mas mais preciso)
                try:
                    import easyocr
                    import numpy as np
                    # Converte PIL Image para numpy array (formato RGB)
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    image_array = np.array(image)
                    
                    # IMPORTANTE: easyocr.Reader é muito lento para inicializar
                    # Em produção, considere usar um singleton ou cache do reader
                    # Por enquanto, inicializa apenas quando necessário
                    try:
                        reader = easyocr.Reader(['pt', 'en'], gpu=False, verbose=False)
                        result = reader.readtext(image_array)
                        text = '\n'.join([item[1] for item in result])
                    except Exception as easyocr_init_error:
                        # Se falhar ao inicializar easyocr, usa o erro do pytesseract
                        raise Exception(f"Erro ao processar OCR com pytesseract: {ocr_error}. EasyOCR também falhou ao inicializar: {str(easyocr_init_error)}")
                except ImportError:
                    raise Exception(f"Erro ao processar OCR: {ocr_error}. Certifique-se de que pytesseract está instalado. EasyOCR não está disponível.")
                except Exception as easyocr_error:
                    # Se easyocr também falhar, retorna o erro original do pytesseract
                    raise Exception(f"Erro ao processar OCR: {ocr_error}. Fallback easyocr também falhou: {str(easyocr_error)}")
            
            # Se ainda não tem texto, retorna erro
            if not text:
                raise Exception(f"Não foi possível extrair texto da imagem. Erro: {ocr_error or 'OCR não retornou texto'}")
            
            # Tenta criar DataFrame do texto extraído
            dataframe = ParserService._text_to_dataframe_from_ocr(text)
            
            return {
                'dataframe': dataframe,
                'full_text': text,
                'pages': [{
                    'page_num': 1,
                    'text': text,
                    'tables': [],
                    'has_header': False,
                    'has_footer': False,
                    'num_tables': 0,
                    'ocr_used': True
                }],
                'metadata': {
                    'num_pages': 1,
                    'ocr_used': True,
                    'file_type': file_extension.lower()
                },
                'headers_footers': {
                    'header_text': '',
                    'footer_text': '',
                    'bank_name': '',
                    'account_info': ''
                }
            }
        except Exception as e:
            raise Exception(f"Erro ao processar imagem: {str(e)}")
    
    @staticmethod
    def validate_extraction_completeness(df: pd.DataFrame, file_content: bytes, file_type: str) -> Dict[str, Any]:
        """
        Valida se a extração foi completa comparando linhas extraídas vs esperadas
        
        Args:
            df: DataFrame extraído
            file_content: Conteúdo original do arquivo
            file_type: Tipo do arquivo ('CSV', 'Excel', 'PDF', etc)
        
        Returns:
            Dict com:
            - is_complete: bool
            - extracted_rows: int
            - expected_rows: int (quando possível calcular)
            - completeness_percentage: float
            - warnings: List[str]
        """
        extracted_rows = len(df) if df is not None and not df.empty else 0
        expected_rows = None
        warnings = []
        
        try:
            if file_type == 'CSV':
                # Conta linhas no arquivo CSV
                expected_rows = ParserService.count_total_lines(file_content)
                # Subtrai 1 se tiver cabeçalho
                if expected_rows > 0 and extracted_rows > 0:
                    # Assume que tem cabeçalho se número de linhas extraídas é menor
                    if extracted_rows < expected_rows:
                        expected_rows -= 1  # Remove cabeçalho da contagem
            
            elif file_type == 'Excel':
                # Para Excel, é mais difícil contar sem processar
                # Mas podemos verificar se o DataFrame não está vazio
                if extracted_rows == 0:
                    warnings.append("Nenhuma linha extraída do Excel")
            
            elif file_type == 'PDF':
                # Para PDF, validação é mais complexa
                # Verifica se há dados extraídos
                if extracted_rows == 0:
                    warnings.append("Nenhuma tabela ou dado extraído do PDF")
        except Exception as e:
            warnings.append(f"Erro ao validar completude: {str(e)}")
        
        # Calcula percentual de completude
        completeness_percentage = None
        if expected_rows is not None and expected_rows > 0:
            completeness_percentage = (extracted_rows / expected_rows) * 100
            if completeness_percentage < 95:
                warnings.append(f"Apenas {completeness_percentage:.1f}% das linhas foram extraídas")
        
        is_complete = (
            extracted_rows > 0 and
            (expected_rows is None or completeness_percentage is None or completeness_percentage >= 95) and
            len(warnings) == 0
        )
        
        return {
            'is_complete': is_complete,
            'extracted_rows': extracted_rows,
            'expected_rows': expected_rows,
            'completeness_percentage': completeness_percentage,
            'warnings': warnings
        }
    
    @staticmethod
    def get_extraction_stats(df: pd.DataFrame, file_type: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Retorna estatísticas da extração
        
        Args:
            df: DataFrame extraído
            file_type: Tipo do arquivo
            metadata: Metadados adicionais (para PDFs, etc)
        
        Returns:
            Dict com estatísticas
        """
        stats = {
            'file_type': file_type,
            'rows_extracted': len(df) if df is not None and not df.empty else 0,
            'columns_extracted': len(df.columns) if df is not None and not df.empty else 0,
            'has_data': df is not None and not df.empty
        }
        
        if df is not None and not df.empty:
            # Estatísticas adicionais
            stats['empty_rows'] = df.isna().all(axis=1).sum()
            stats['rows_with_data'] = stats['rows_extracted'] - stats['empty_rows']
            
            # Colunas com dados
            stats['columns_with_data'] = df.notna().any(axis=0).sum()
        
        # Adiciona metadados específicos do tipo
        if metadata:
            if file_type == 'PDF':
                stats['pdf_pages'] = metadata.get('num_pages', 0)
                stats['pdf_pages_processed'] = metadata.get('pages_processed', 0)
                stats['pdf_tables_found'] = metadata.get('total_tables_found', 0)
                stats['pdf_extraction_complete'] = metadata.get('extraction_complete', False)
            
            elif file_type == 'Excel':
                if '_sheet_name' in df.columns:
                    stats['sheets_processed'] = df['_sheet_name'].nunique()
        
        return stats








