@echo off
chcp 65001 > nul
echo ============================================================
echo   CRIANDO EXECUTÁVEL DO SISTEMA CONTÁBIL
echo ============================================================
echo.

REM Ativa ambiente virtual
if not exist venv (
    echo ❌ Execute install.bat primeiro!
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo 📦 Instalando PyInstaller...
pip install pyinstaller
echo.

echo 🔨 Criando executável...
echo    Isso pode levar alguns minutos...
echo.

REM Cria o executável
pyinstaller --name="SistemaContabil" ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --add-data="pages;pages" ^
    --add-data="models;models" ^
    --add-data="services;services" ^
    --add-data="config;config" ^
    --add-data="utils;utils" ^
    --add-data="tests;tests" ^
    --hidden-import=streamlit ^
    --hidden-import=pandas ^
    --hidden-import=plotly ^
    --hidden-import=sqlalchemy ^
    --collect-all=streamlit ^
    app.py

if errorlevel 1 (
    echo.
    echo ❌ Erro ao criar executável
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   ✅ EXECUTÁVEL CRIADO COM SUCESSO!
echo ============================================================
echo.
echo 📁 Localização: dist\SistemaContabil.exe
echo.
echo 📝 Instruções:
echo    1. Copie o arquivo dist\SistemaContabil.exe
echo    2. Cole onde quiser usar
echo    3. Clique duas vezes para executar
echo.
echo ⚠️ NOTA: O executável é grande (~200-300MB)
echo    Isso é normal, pois inclui Python e todas as bibliotecas.
echo.
echo ============================================================
pause







