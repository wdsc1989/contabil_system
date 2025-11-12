@echo off
chcp 65001 > nul
echo ============================================================
echo   GERAÇÃO DE PDF - Tutorial com Imagens
echo ============================================================
echo.

REM Ativa ambiente virtual
if not exist venv (
    echo ❌ Execute install.bat primeiro!
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo 📦 Verificando dependências...
pip show reportlab >nul 2>&1
if errorlevel 1 (
    echo    Instalando reportlab...
    pip install reportlab
)

echo.
echo 🚀 Gerando PDF do tutorial...
echo.

python generate_pdf_tutorial_simple.py

echo.
echo ============================================================
echo   ✅ CONCLUÍDO!
echo ============================================================
echo.
echo 📁 PDF gerado: TUTORIAL_COM_IMAGENS.pdf
echo.
pause


