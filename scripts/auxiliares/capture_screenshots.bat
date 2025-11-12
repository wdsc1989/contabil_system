@echo off
chcp 65001 > nul
echo ============================================================
echo   CAPTURA AUTOMÁTICA DE SCREENSHOTS
echo ============================================================
echo.

REM Ativa ambiente virtual
if not exist venv (
    echo ❌ Execute install.bat primeiro!
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo 📦 Verificando Playwright...
pip show playwright >nul 2>&1
if errorlevel 1 (
    echo    Playwright não encontrado. Instalando...
    pip install playwright
    playwright install chromium
    echo    ✓ Playwright instalado
) else (
    echo    ✓ Playwright já instalado
)
echo.

echo ⚠️  IMPORTANTE:
echo    1. O sistema DEVE estar rodando (execute run.bat em outra janela)
echo    2. Acesse http://localhost:8501 para verificar
echo    3. O navegador abrirá automaticamente
echo    4. NÃO feche o navegador durante a captura
echo.

set /p confirm="Sistema está rodando? (S/N): "
if /i not "%confirm%"=="S" (
    echo.
    echo ❌ Execute run.bat primeiro em outra janela!
    pause
    exit /b 0
)

echo.
echo 🚀 Iniciando captura automática...
echo.

python capture_screenshots.py

echo.
echo ============================================================
echo   ✅ CAPTURA CONCLUÍDA!
echo ============================================================
echo.
echo 📁 Screenshots salvos em: screenshots\
echo.
echo 💡 Próximo passo:
echo    1. Verifique as imagens em screenshots\
echo    2. Abra TUTORIAL_COM_IMAGENS.md
echo    3. Imagens aparecerão automaticamente
echo.
pause


