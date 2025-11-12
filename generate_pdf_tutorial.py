"""
Script para gerar PDF do tutorial com imagens reais
"""
import os
import re
from pathlib import Path

def check_image_exists(image_path):
    """Verifica se a imagem existe"""
    return os.path.exists(image_path)

def process_markdown_for_pdf(md_file, output_md_file):
    """Processa markdown removendo referências a imagens inexistentes"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Encontra todas as referências de imagens
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def replace_image(match):
        alt_text = match.group(1)
        image_path = match.group(2)
        
        # Verifica se a imagem existe
        if check_image_exists(image_path):
            return match.group(0)  # Mantém a referência
        else:
            # Remove a linha inteira se a imagem não existe
            return f"<!-- Imagem não encontrada: {image_path} -->"
    
    # Substitui referências de imagens inexistentes
    processed_content = re.sub(image_pattern, replace_image, content)
    
    # Remove linhas com "> **📸 Capturar:**" que são instruções
    processed_content = re.sub(r'^> \*\*📸 Capturar:\*\*.*$', '', processed_content, flags=re.MULTILINE)
    
    # Salva versão processada
    with open(output_md_file, 'w', encoding='utf-8') as f:
        f.write(processed_content)
    
    return processed_content

def generate_html_from_markdown(md_content):
    """Converte Markdown para HTML"""
    try:
        import markdown2
        html = markdown2.markdown(md_content, extras=['fenced-code-blocks', 'tables', 'break-on-newline'])
        return html
    except ImportError:
        # Fallback simples se markdown2 não estiver disponível
        print("⚠️ markdown2 não encontrado. Usando conversão básica...")
        return simple_markdown_to_html(md_content)

def simple_markdown_to_html(md_content):
    """Conversão básica de Markdown para HTML"""
    html = md_content
    
    # Headers
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    
    # Bold
    html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)
    
    # Italic
    html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)
    
    # Code blocks
    html = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
    
    # Inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Images
    html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" style="max-width: 100%; height: auto; margin: 10px 0;" />', html)
    
    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Lists
    lines = html.split('\n')
    in_list = False
    result = []
    for line in lines:
        if re.match(r'^[-*+] (.+)$', line):
            if not in_list:
                result.append('<ul>')
                in_list = True
            content = re.match(r'^[-*+] (.+)$', line).group(1)
            result.append(f'<li>{content}</li>')
        elif re.match(r'^\d+\. (.+)$', line):
            if not in_list:
                result.append('<ol>')
                in_list = True
            content = re.match(r'^\d+\. (.+)$', line).group(1)
            result.append(f'<li>{content}</li>')
        else:
            if in_list:
                result.append('</ul>' if '<ul>' in result[-2] else '</ol>')
                in_list = False
            if line.strip():
                result.append(f'<p>{line}</p>')
            else:
                result.append('<br/>')
    
    if in_list:
        result.append('</ul>')
    
    html = '\n'.join(result)
    
    # Horizontal rules
    html = html.replace('---', '<hr/>')
    
    return html

def create_html_document(html_content, css_style):
    """Cria documento HTML completo"""
    html_doc = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tutorial com Imagens - Sistema Contábil</title>
    <style>
        {css_style}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""
    return html_doc

def generate_pdf_from_html(html_file, pdf_file):
    """Gera PDF a partir de HTML"""
    try:
        from weasyprint import HTML
        HTML(filename=html_file).write_pdf(pdf_file)
        return True
    except ImportError:
        print("⚠️ weasyprint não encontrado. Tentando pdfkit...")
        try:
            import pdfkit
            pdfkit.from_file(html_file, pdf_file)
            return True
        except ImportError:
            print("⚠️ pdfkit não encontrado. Tentando reportlab...")
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.lib import colors
                from html.parser import HTMLParser
                import base64
                
                # Conversão básica com reportlab
                print("⚠️ Usando reportlab (conversão limitada)...")
                return generate_pdf_with_reportlab(html_file, pdf_file)
            except ImportError:
                print("❌ Nenhuma biblioteca de PDF encontrada!")
                print("\n📦 Para gerar PDF, instale uma das opções:")
                print("   pip install weasyprint")
                print("   OU")
                print("   pip install pdfkit")
                print("   (e instale wkhtmltopdf)")
                return False

def generate_pdf_with_reportlab(html_file, pdf_file):
    """Gera PDF usando reportlab (conversão limitada)"""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    
    doc = SimpleDocTemplate(pdf_file, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Lê HTML e extrai texto básico
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Extrai texto e imagens básico
    # (implementação simplificada)
    
    print("⚠️ Conversão com reportlab é limitada. Use weasyprint para melhor resultado.")
    return False

def main():
    print("=" * 70)
    print("  GERAÇÃO DE PDF - Tutorial com Imagens")
    print("=" * 70)
    print()
    
    # Arquivos
    md_file = "TUTORIAL_COM_IMAGENS.md"
    processed_md = "TUTORIAL_PROCESSADO.md"
    html_file = "TUTORIAL_TEMP.html"
    pdf_file = "TUTORIAL_COM_IMAGENS.pdf"
    
    # Verifica se arquivo markdown existe
    if not os.path.exists(md_file):
        print(f"❌ Arquivo não encontrado: {md_file}")
        return
    
    print(f"📄 Processando: {md_file}")
    
    # Processa markdown
    md_content = process_markdown_for_pdf(md_file, processed_md)
    print(f"✅ Markdown processado: {processed_md}")
    
    # Converte para HTML
    print("🔄 Convertendo Markdown para HTML...")
    html_content = generate_html_from_markdown(md_content)
    
    # CSS para PDF
    css_style = """
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 30px;
        }
        h2 {
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 8px;
            margin-top: 25px;
        }
        h3 {
            color: #555;
            margin-top: 20px;
        }
        img {
            max-width: 100%;
            height: auto;
            margin: 15px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 10pt;
        }
        pre {
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #3498db;
        }
        ul, ol {
            margin: 10px 0;
            padding-left: 30px;
        }
        li {
            margin: 5px 0;
        }
        hr {
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 30px 0;
        }
        strong {
            color: #2c3e50;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin: 15px 0;
            color: #7f8c8d;
            font-style: italic;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #3498db;
            color: white;
        }
    """
    
    # Cria HTML completo
    html_doc = create_html_document(html_content, css_style)
    
    # Salva HTML temporário
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    print(f"✅ HTML gerado: {html_file}")
    
    # Converte para PDF
    print("🔄 Convertendo HTML para PDF...")
    if generate_pdf_from_html(html_file, pdf_file):
        print(f"✅ PDF gerado com sucesso: {pdf_file}")
        print()
        print("📊 Estatísticas:")
        if os.path.exists(pdf_file):
            size_mb = os.path.getsize(pdf_file) / (1024 * 1024)
            print(f"   Tamanho: {size_mb:.2f} MB")
        
        # Conta imagens incluídas
        image_count = len(re.findall(r'<img[^>]+>', html_doc))
        print(f"   Imagens: {image_count}")
        
        print()
        print("🎉 Tutorial em PDF pronto!")
        print(f"📁 Localização: {os.path.abspath(pdf_file)}")
    else:
        print("❌ Erro ao gerar PDF")
        print()
        print("💡 Solução:")
        print("   1. Instale weasyprint:")
        print("      pip install weasyprint")
        print()
        print("   2. Ou use o HTML gerado:")
        print(f"      Abra: {html_file}")
        print("      E salve como PDF no navegador (Ctrl+P)")
    
    # Limpa arquivos temporários (opcional)
    # os.remove(html_file)
    # os.remove(processed_md)

if __name__ == "__main__":
    main()


