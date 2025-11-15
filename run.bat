@echo off
chcp 65001 > nul
echo ============================================================
echo   SISTEMA CONTÁBIL - Iniciando...
echo ============================================================
echo.

REM Verifica se o ambiente virtual existe
if not exist venv (
    echo ❌ Ambiente virtual não encontrado!
    echo.
    echo Execute primeiro: install.bat
    echo.
    pause
    exit /b 1
)

REM Ativa ambiente virtual
call venv\Scripts\activate.bat

REM Verifica se o banco existe
if not exist data\contabil.db (
    echo ⚠️ Banco de dados não encontrado. Criando...
    python init_db.py
    python tests\seed_data.py --reset
    echo.
)

echo ✓ Iniciando Sistema Contábil...
echo.
echo 🌐 O sistema abrirá automaticamente no navegador
echo 📍 URL: http://localhost:8501
echo.
echo 📋 Credenciais:
echo    Admin: admin / admin123
echo.
echo ⚠️ Para parar o sistema, feche esta janela ou pressione Ctrl+C
echo.
echo ============================================================
echo.

REM Inicia o Streamlit
streamlit run app.py

pause





