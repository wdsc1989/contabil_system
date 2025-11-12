"""
Script para capturar screenshots automaticamente do sistema
Usa Playwright para navegar e capturar telas
"""
import os
import time
from playwright.sync_api import sync_playwright
import sys

# Configurações
SYSTEM_URL = "http://localhost:8501"
SCREENSHOTS_DIR = "screenshots"
USERNAME = "admin"
PASSWORD = "admin123"

# Cria diretório de screenshots
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

print("=" * 70)
print("  CAPTURA AUTOMÁTICA DE SCREENSHOTS - Sistema Contábil")
print("=" * 70)
print()
print("⚠️  IMPORTANTE: O sistema deve estar rodando em http://localhost:8501")
print()
input("Pressione Enter para começar a captura...")
print()

def capture_screenshot(page, filename, description, wait_time=2):
    """Captura screenshot com descrição"""
    print(f"📸 Capturando: {description}")
    time.sleep(wait_time)  # Aguarda carregamento
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    page.screenshot(path=filepath, full_page=False)
    print(f"   ✓ Salvo: {filepath}")
    return filepath

def main():
    with sync_playwright() as p:
        # Inicia navegador
        print("🌐 Iniciando navegador...")
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        try:
            print(f"🔗 Acessando: {SYSTEM_URL}")
            page.goto(SYSTEM_URL, wait_until="networkidle")
            time.sleep(3)
            
            # 01. Tela de Login
            print("\n" + "=" * 70)
            print("CAPTURANDO: TELA DE LOGIN")
            print("=" * 70)
            capture_screenshot(page, "02_tela_login.png", "Tela de login", 2)
            
            # Fazer login
            print("\n🔐 Fazendo login...")
            page.fill('input[type="text"]', USERNAME)
            page.fill('input[type="password"]', PASSWORD)
            page.click('button:has-text("Entrar")')
            time.sleep(5)  # Aguarda login e carregamento
            
            # 02. Tela Inicial
            print("\n" + "=" * 70)
            print("CAPTURANDO: TELA INICIAL")
            print("=" * 70)
            capture_screenshot(page, "03_tela_inicial.png", "Tela inicial após login", 3)
            
            # 03. Sidebar com Cliente
            print("\n" + "=" * 70)
            print("CAPTURANDO: SELEÇÃO DE CLIENTE")
            print("=" * 70)
            capture_screenshot(page, "04_seletor_cliente.png", "Seletor de cliente na sidebar", 2)
            
            # Clica no seletor de cliente
            try:
                page.click('div[data-testid="stSelectbox"]')
                time.sleep(1)
                capture_screenshot(page, "05_lista_clientes.png", "Lista de clientes aberta", 1)
                page.keyboard.press("Escape")
            except:
                print("   ⚠️ Não foi possível abrir lista de clientes")
            
            # 04. Importação de Dados
            print("\n" + "=" * 70)
            print("CAPTURANDO: IMPORTAÇÃO DE DADOS")
            print("=" * 70)
            
            # Navega para importação
            try:
                page.click('a:has-text("Importação")')
                time.sleep(3)
                capture_screenshot(page, "07_pagina_importacao.png", "Página de importação", 2)
                
                # Tipo de importação
                page.click('div[data-testid="stSelectbox"]:has-text("Tipo")')
                time.sleep(1)
                capture_screenshot(page, "08_tipo_importacao.png", "Dropdown de tipo aberto", 1)
                page.keyboard.press("Escape")
                
            except Exception as e:
                print(f"   ⚠️ Erro na importação: {e}")
            
            # 05. Transações
            print("\n" + "=" * 70)
            print("CAPTURANDO: TRANSAÇÕES")
            print("=" * 70)
            
            try:
                page.click('a:has-text("Transações")')
                time.sleep(3)
                capture_screenshot(page, "15_pagina_transacoes.png", "Página de transações", 3)
                
                # Scroll para ver tabela
                page.evaluate("window.scrollTo(0, 400)")
                time.sleep(1)
                capture_screenshot(page, "18_tabela_transacoes.png", "Tabela de transações", 2)
                
            except Exception as e:
                print(f"   ⚠️ Erro em transações: {e}")
            
            # 06. Contratos
            print("\n" + "=" * 70)
            print("CAPTURANDO: CONTRATOS")
            print("=" * 70)
            
            try:
                page.click('a:has-text("Contratos")')
                time.sleep(3)
                capture_screenshot(page, "21_pagina_contratos.png", "Página de contratos", 3)
                
            except Exception as e:
                print(f"   ⚠️ Erro em contratos: {e}")
            
            # 07. Contas
            print("\n" + "=" * 70)
            print("CAPTURANDO: CONTAS")
            print("=" * 70)
            
            try:
                page.click('a:has-text("Contas")')
                time.sleep(3)
                capture_screenshot(page, "25_contas_pagar.png", "Página de contas", 3)
                
            except Exception as e:
                print(f"   ⚠️ Erro em contas: {e}")
            
            # 08. DRE
            print("\n" + "=" * 70)
            print("CAPTURANDO: DASHBOARD DRE")
            print("=" * 70)
            
            try:
                page.click('a:has-text("DRE")')
                time.sleep(4)
                capture_screenshot(page, "30_dashboard_dre.png", "Dashboard DRE", 3)
                
                # KPIs
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
                capture_screenshot(page, "32_kpis_dre.png", "KPIs do DRE", 2)
                
                # Gráficos
                page.evaluate("window.scrollTo(0, 600)")
                time.sleep(1)
                capture_screenshot(page, "33_grafico_receitas_despesas.png", "Gráfico Receitas vs Despesas", 2)
                
                # Detalhamento
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                
                # Tenta expandir detalhamento
                try:
                    page.click('summary:has-text("Detalhamento")')
                    time.sleep(2)
                    capture_screenshot(page, "38_detalhamento_aberto.png", "Detalhamento DRE expandido", 2)
                except:
                    print("   ⚠️ Não foi possível expandir detalhamento")
                
            except Exception as e:
                print(f"   ⚠️ Erro em DRE: {e}")
            
            # 09. DFC
            print("\n" + "=" * 70)
            print("CAPTURANDO: DASHBOARD DFC")
            print("=" * 70)
            
            try:
                page.click('a:has-text("DFC")')
                time.sleep(4)
                capture_screenshot(page, "42_dashboard_dfc.png", "Dashboard DFC", 3)
                
                # KPIs
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
                capture_screenshot(page, "43_kpis_dfc.png", "KPIs do DFC", 2)
                
                # Gráfico fluxo
                page.evaluate("window.scrollTo(0, 600)")
                time.sleep(1)
                capture_screenshot(page, "44_fluxo_mensal.png", "Gráfico de fluxo mensal", 2)
                
            except Exception as e:
                print(f"   ⚠️ Erro em DFC: {e}")
            
            # 10. Sazonalidade
            print("\n" + "=" * 70)
            print("CAPTURANDO: SAZONALIDADE")
            print("=" * 70)
            
            try:
                page.click('a:has-text("Sazonalidade")')
                time.sleep(4)
                capture_screenshot(page, "52_dashboard_sazonalidade.png", "Dashboard Sazonalidade", 3)
                
                # Média mensal
                page.evaluate("window.scrollTo(0, 400)")
                time.sleep(1)
                capture_screenshot(page, "53_media_mensal.png", "Gráfico média mensal", 2)
                
                # Heatmap
                page.evaluate("window.scrollTo(0, 1000)")
                time.sleep(1)
                capture_screenshot(page, "54_heatmap.png", "Heatmap de sazonalidade", 2)
                
            except Exception as e:
                print(f"   ⚠️ Erro em sazonalidade: {e}")
            
            # 11. Relatórios
            print("\n" + "=" * 70)
            print("CAPTURANDO: RELATÓRIOS")
            print("=" * 70)
            
            try:
                page.click('a:has-text("Relatórios")')
                time.sleep(3)
                capture_screenshot(page, "58_pagina_relatorios.png", "Página de relatórios", 3)
                
            except Exception as e:
                print(f"   ⚠️ Erro em relatórios: {e}")
            
            # 12. Gestão de Clientes
            print("\n" + "=" * 70)
            print("CAPTURANDO: GESTÃO DE CLIENTES")
            print("=" * 70)
            
            try:
                page.click('a:has-text("Gestão de Clientes")')
                time.sleep(3)
                capture_screenshot(page, "64_gestao_clientes.png", "Página gestão de clientes", 3)
                
                # Tabela
                page.evaluate("window.scrollTo(0, 400)")
                time.sleep(1)
                capture_screenshot(page, "65_lista_clientes.png", "Lista de clientes", 2)
                
            except Exception as e:
                print(f"   ⚠️ Erro em gestão de clientes: {e}")
            
            # 13. Administração
            print("\n" + "=" * 70)
            print("CAPTURANDO: ADMINISTRAÇÃO")
            print("=" * 70)
            
            try:
                page.click('a:has-text("Administração")')
                time.sleep(3)
                capture_screenshot(page, "71_pagina_admin.png", "Página de administração", 3)
                
                # Tabela usuários
                page.evaluate("window.scrollTo(0, 400)")
                time.sleep(1)
                capture_screenshot(page, "72_lista_usuarios.png", "Lista de usuários", 2)
                
            except Exception as e:
                print(f"   ⚠️ Erro em admin: {e}")
            
            print("\n" + "=" * 70)
            print("✅ CAPTURA CONCLUÍDA!")
            print("=" * 70)
            print(f"\n📁 Screenshots salvos em: {os.path.abspath(SCREENSHOTS_DIR)}")
            print(f"📊 Total de capturas: {len(os.listdir(SCREENSHOTS_DIR))}")
            print()
            
        except Exception as e:
            print(f"\n❌ Erro geral: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n⏸️  Pressione Enter para fechar o navegador...")
            input()
            browser.close()

if __name__ == "__main__":
    # Verifica se Playwright está instalado
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright não está instalado!")
        print()
        print("Para instalar, execute:")
        print("  pip install playwright")
        print("  playwright install chromium")
        print()
        sys.exit(1)
    
    main()


