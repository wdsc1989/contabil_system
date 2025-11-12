"""
Script simplificado para gerar PDF do tutorial
Usa reportlab para gerar PDF diretamente
"""
import os
import re
from pathlib import Path

def check_image_exists(image_path):
    """Verifica se a imagem existe"""
    return os.path.exists(image_path)

def extract_images_from_markdown(md_file):
    """Extrai todas as referências de imagens do markdown"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Padrão para encontrar imagens
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    images = []
    
    for match in re.finditer(image_pattern, content):
        alt_text = match.group(1)
        image_path = match.group(2)
        if check_image_exists(image_path):
            images.append({
                'alt': alt_text,
                'path': image_path,
                'full_match': match.group(0)
            })
    
    return images

def parse_markdown_sections(md_file):
    """Parse markdown em seções estruturadas"""
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    sections = []
    current_section = {'type': 'text', 'content': []}
    
    for line in lines:
        # Headers
        if line.startswith('# '):
            if current_section['content']:
                sections.append(current_section)
            sections.append({'type': 'h1', 'content': line[2:].strip()})
            current_section = {'type': 'text', 'content': []}
        elif line.startswith('## '):
            if current_section['content']:
                sections.append(current_section)
            sections.append({'type': 'h2', 'content': line[3:].strip()})
            current_section = {'type': 'text', 'content': []}
        elif line.startswith('### '):
            if current_section['content']:
                sections.append(current_section)
            sections.append({'type': 'h3', 'content': line[4:].strip()})
            current_section = {'type': 'text', 'content': []}
        elif line.startswith('#### '):
            if current_section['content']:
                sections.append(current_section)
            sections.append({'type': 'h4', 'content': line[5:].strip()})
            current_section = {'type': 'text', 'content': []}
        # Images
        elif re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line):
            match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line)
            image_path = match.group(2)
            if check_image_exists(image_path):
                if current_section['content']:
                    sections.append(current_section)
                sections.append({
                    'type': 'image',
                    'path': image_path,
                    'alt': match.group(1)
                })
                current_section = {'type': 'text', 'content': []}
        # Horizontal rule
        elif line.strip() == '---':
            if current_section['content']:
                sections.append(current_section)
            sections.append({'type': 'hr'})
            current_section = {'type': 'text', 'content': []}
        # Code blocks
        elif line.startswith('```'):
            if current_section['content']:
                sections.append(current_section)
            # Skip code blocks for now
            current_section = {'type': 'text', 'content': []}
        # Regular text
        else:
            # Skip instruction lines
            if not line.strip().startswith('> **📸'):
                if line.strip():
                    current_section['content'].append(line.rstrip())
    
    if current_section['content']:
        sections.append(current_section)
    
    return sections

def generate_pdf_with_reportlab(md_file, pdf_file):
    """Gera PDF usando reportlab"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, KeepTogether
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        from reportlab.pdfgen import canvas
        
        # Parse markdown
        sections = parse_markdown_sections(md_file)
        
        # Cria documento
        doc = SimpleDocTemplate(
            pdf_file,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilos customizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
        )
        
        h1_style = ParagraphStyle(
            'CustomH1',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=20,
            spaceBefore=30,
        )
        
        h2_style = ParagraphStyle(
            'CustomH2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=15,
            spaceBefore=25,
        )
        
        h3_style = ParagraphStyle(
            'CustomH3',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#555555'),
            spaceAfter=10,
            spaceBefore=20,
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
        )
        
        # Story (conteúdo)
        story = []
        
        # Processa seções
        for section in sections:
            if section['type'] == 'h1':
                story.append(Paragraph(section['content'], title_style))
                story.append(Spacer(1, 0.2*cm))
            elif section['type'] == 'h2':
                story.append(Spacer(1, 0.3*cm))
                story.append(Paragraph(section['content'], h1_style))
                story.append(Spacer(1, 0.2*cm))
            elif section['type'] == 'h3':
                story.append(Spacer(1, 0.2*cm))
                story.append(Paragraph(section['content'], h2_style))
                story.append(Spacer(1, 0.1*cm))
            elif section['type'] == 'h4':
                story.append(Paragraph(section['content'], h3_style))
                story.append(Spacer(1, 0.1*cm))
            elif section['type'] == 'image':
                try:
                    img = Image(section['path'], width=16*cm, height=12*cm, kind='proportional')
                    story.append(Spacer(1, 0.3*cm))
                    story.append(img)
                    if section['alt']:
                        story.append(Spacer(1, 0.1*cm))
                        story.append(Paragraph(
                            f"<i>{section['alt']}</i>",
                            ParagraphStyle('ImageCaption', parent=normal_style, fontSize=9, textColor=colors.grey, alignment=TA_CENTER)
                        ))
                    story.append(Spacer(1, 0.3*cm))
                except Exception as e:
                    print(f"⚠️ Erro ao adicionar imagem {section['path']}: {e}")
                    story.append(Paragraph(f"[Imagem: {section['alt']}]", normal_style))
            elif section['type'] == 'hr':
                story.append(Spacer(1, 0.5*cm))
                # Linha horizontal simples
                story.append(Spacer(1, 0.2*cm))
            elif section['type'] == 'text' and section['content']:
                # Processa texto
                for line in section['content']:
                    if line.strip():
                        # Processa formatação básica
                        formatted = line
                        # Bold
                        formatted = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', formatted)
                        # Italic
                        formatted = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', formatted)
                        # Inline code
                        formatted = re.sub(r'`([^`]+)`', r'<font name="Courier" size="9">\1</font>', formatted)
                        # Links (simplificado)
                        formatted = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', formatted)
                        
                        story.append(Paragraph(formatted, normal_style))
        
        # Gera PDF
        doc.build(story)
        return True
        
    except ImportError:
        print("❌ reportlab não está instalado!")
        print("   Execute: pip install reportlab")
        return False
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 70)
    print("  GERAÇÃO DE PDF - Tutorial com Imagens (ReportLab)")
    print("=" * 70)
    print()
    
    md_file = "TUTORIAL_COM_IMAGENS.md"
    pdf_file = "TUTORIAL_COM_IMAGENS.pdf"
    
    if not os.path.exists(md_file):
        print(f"❌ Arquivo não encontrado: {md_file}")
        return
    
    print(f"📄 Processando: {md_file}")
    
    # Conta imagens disponíveis
    images = extract_images_from_markdown(md_file)
    print(f"📸 Imagens encontradas: {len(images)}")
    
    print("🔄 Gerando PDF...")
    if generate_pdf_with_reportlab(md_file, pdf_file):
        print(f"✅ PDF gerado com sucesso: {pdf_file}")
        if os.path.exists(pdf_file):
            size_mb = os.path.getsize(pdf_file) / (1024 * 1024)
            print(f"📊 Tamanho: {size_mb:.2f} MB")
            print(f"📸 Imagens incluídas: {len(images)}")
            print()
            print("🎉 Tutorial em PDF pronto!")
            print(f"📁 Localização: {os.path.abspath(pdf_file)}")
    else:
        print("❌ Erro ao gerar PDF")

if __name__ == "__main__":
    main()

