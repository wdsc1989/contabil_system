"""
Serviço de parsing de arquivos (CSV, Excel, PDF, OFX)
"""
import pandas as pd
import pdfplumber
from ofxparse import OfxParser
from typing import Dict, List, Optional, Any
from io import BytesIO, StringIO
import re


class ParserService:
    """
    Serviço para fazer parsing de diferentes formatos de arquivo
    """

    @staticmethod
    def parse_csv(file_content: bytes, encoding: str = 'utf-8', delimiter: str = ',') -> pd.DataFrame:
        """
        Faz parse de arquivo CSV
        """
        try:
            # Tenta diferentes encodings
            encodings = [encoding, 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            
            for enc in encodings:
                try:
                    df = pd.read_csv(BytesIO(file_content), encoding=enc, delimiter=delimiter)
                    return df
                except UnicodeDecodeError:
                    continue
            
            # Se nenhum encoding funcionou, tenta com errors='ignore'
            df = pd.read_csv(BytesIO(file_content), encoding='utf-8', delimiter=delimiter, errors='ignore')
            return df
        
        except Exception as e:
            raise Exception(f"Erro ao fazer parse do CSV: {str(e)}")

    @staticmethod
    def parse_excel(file_content: bytes, sheet_name: Optional[str] = None, all_sheets: bool = False) -> pd.DataFrame:
        """
        Faz parse de arquivo Excel
        Se all_sheets=True, lê todas as abas e combina em um único DataFrame
        """
        try:
            if all_sheets:
                # Lê todas as abas e combina
                excel_file = pd.ExcelFile(BytesIO(file_content))
                all_dfs = []
                
                for sheet in excel_file.sheet_names:
                    df_sheet = pd.read_excel(excel_file, sheet_name=sheet)
                    if not df_sheet.empty:
                        # Adiciona coluna indicando a aba de origem
                        df_sheet['_sheet_name'] = sheet
                        all_dfs.append(df_sheet)
                
                if all_dfs:
                    # Combina todos os DataFrames
                    df = pd.concat(all_dfs, ignore_index=True)
                    return df
                else:
                    return pd.DataFrame()
            elif sheet_name:
                df = pd.read_excel(BytesIO(file_content), sheet_name=sheet_name)
            else:
                # Lê apenas a primeira aba (comportamento padrão)
                df = pd.read_excel(BytesIO(file_content))
            
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
                
                # Processa cada página
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text() or ''
                    full_text_parts.append(page_text)
                    
                    # Extrai tabelas da página
                    page_tables = page.extract_tables()
                    if not page_tables:
                        # Tenta extrair tabela única
                        try:
                            single_table = page.extract_table()
                            if single_table:
                                page_tables = [single_table]
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
                    has_footer = page_num == len(pdf.pages)
                    
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
                        'num_tables': len(page_tables) if page_tables else 0
                    })
                    
                    if page_tables:
                        all_tables.extend(page_tables)
            
            # Processa tabelas para criar DataFrame
            dataframe = None
            if all_tables:
                dataframe = ParserService._tables_to_dataframe(all_tables)
            
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
    def parse_pdf_to_dataframe(file_content: bytes) -> Optional[pd.DataFrame]:
        """
        Tenta extrair todas as tabelas de PDF e converter para DataFrame
        Combina tabelas de todas as páginas que tenham a mesma estrutura
        
        Agora usa parse_pdf_complete internamente para melhor extração
        """
        try:
            result = ParserService.parse_pdf_complete(file_content)
            return result.get('dataframe')
        except Exception as e:
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
        Detecta o delimitador de um arquivo CSV
        """
        try:
            sample = file_content[:sample_size].decode('utf-8', errors='ignore')
            
            delimiters = [',', ';', '\t', '|']
            delimiter_counts = {}
            
            for delimiter in delimiters:
                count = sample.count(delimiter)
                delimiter_counts[delimiter] = count
            
            # Retorna o delimitador mais comum
            return max(delimiter_counts, key=delimiter_counts.get)
        
        except:
            return ','

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
            try:
                text = pytesseract.image_to_string(image, lang='por+eng')
            except Exception as e:
                # Fallback: tenta easyocr se disponível
                try:
                    import easyocr
                    reader = easyocr.Reader(['pt', 'en'])
                    result = reader.readtext(image)
                    text = '\n'.join([item[1] for item in result])
                except ImportError:
                    raise Exception(f"Erro ao processar OCR: {str(e)}")
            
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


