"""
Script para verificar se todas as dependências do requirements.txt estão instaladas
"""
import subprocess
import sys
import re

def get_installed_packages():
    """Retorna dicionário com pacotes instalados e suas versões"""
    result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                          capture_output=True, text=True)
    packages = {}
    for line in result.stdout.split('\n')[2:]:  # Pula cabeçalho
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                packages[parts[0].lower()] = parts[1]
    return packages

def parse_requirements():
    """Lê requirements.txt e retorna lista de pacotes"""
    requirements = []
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove comentários inline
                if '#' in line:
                    line = line.split('#')[0].strip()
                # Extrai nome do pacote (remove versão)
                match = re.match(r'([a-zA-Z0-9_-]+[a-zA-Z0-9_.-]*)', line)
                if match:
                    package_name = match.group(1).lower()
                    # Normaliza nomes
                    if package_name == 'psycopg2-binary':
                        package_name = 'psycopg2'
                    elif package_name == 'pymupdf':
                        package_name = 'fitz'  # PyMuPDF é importado como fitz
                    requirements.append((package_name, line))
    return requirements

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    installed = get_installed_packages()
    requirements = parse_requirements()
    
    missing = []
    installed_count = 0
    
    print("=" * 60)
    print("VERIFICAÇÃO DE DEPENDÊNCIAS")
    print("=" * 60)
    print()
    
    for package_name, requirement_line in requirements:
        # Normaliza nome para comparação
        check_name = package_name
        if check_name == 'psycopg2':
            # psycopg2-binary instala como psycopg2
            check_name = 'psycopg2'
        elif check_name == 'fitz':
            # PyMuPDF é importado como fitz, mas instalado como pymupdf
            check_name = 'pymupdf'
        
        # Verifica se está instalado
        is_installed = check_name in installed
        
        # Verificação especial para fitz (PyMuPDF)
        if check_name == 'pymupdf' and not is_installed:
            try:
                import fitz
                is_installed = True
                version = getattr(fitz, '__version__', 'installed')
            except:
                pass
        
        # Verificação especial para psycopg2
        if check_name == 'psycopg2' and not is_installed:
            try:
                import psycopg2
                is_installed = True
                version = getattr(psycopg2, '__version__', 'installed')
            except:
                pass
        
        if is_installed:
            version = installed.get(check_name, 'installed')
            print(f"✅ {package_name:30s} - {version}")
            installed_count += 1
        else:
            print(f"❌ {package_name:30s} - NÃO INSTALADO")
            missing.append(requirement_line)
    
    print()
    print("=" * 60)
    print(f"RESUMO: {installed_count}/{len(requirements)} instalados")
    print("=" * 60)
    
    if missing:
        print()
        print("📦 PACOTES FALTANDO:")
        print("-" * 60)
        for req in missing:
            print(f"  {req}")
        print()
        print("Para instalar, execute:")
        print("  pip install -r requirements.txt")
    else:
        print()
        print("✅ Todas as dependências estão instaladas!")
    
    # Verifica bibliotecas opcionais de OCR
    print()
    print("=" * 60)
    print("VERIFICAÇÃO DE BIBLIOTECAS OPCIONAIS (OCR)")
    print("=" * 60)
    
    ocr_libs = {
        'pytesseract': 'pytesseract',
        'easyocr': 'easyocr'
    }
    
    for lib_name, import_name in ocr_libs.items():
        try:
            __import__(import_name)
            print(f"✅ {lib_name:30s} - Instalado")
        except ImportError:
            print(f"⚠️  {lib_name:30s} - Não instalado (opcional)")
        except (OSError, Exception) as e:
            error_msg = str(e)
            if "DLL" in error_msg or "Visual C++" in error_msg:
                print(f"⚠️  {lib_name:30s} - Instalado mas requer Visual C++ Redistributable")
            else:
                print(f"⚠️  {lib_name:30s} - Erro ao importar: {str(e)[:50]}")
    
    # Verifica PyMuPDF (fitz)
    try:
        import fitz
        print(f"✅ PyMuPDF (fitz)          - {fitz.__version__}")
    except ImportError:
        print(f"❌ PyMuPDF (fitz)          - Não instalado")
    
    # Verifica pdf2image
    try:
        from pdf2image import convert_from_bytes
        print(f"✅ pdf2image               - Instalado")
    except ImportError:
        print(f"⚠️  pdf2image               - Não instalado (opcional)")
    
    print()

if __name__ == '__main__':
    check_dependencies()

