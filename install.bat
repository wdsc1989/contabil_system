@echo off
chcp 65001 > nul
echo ============================================================
echo   INSTALAÇÃO DO SISTEMA CONTÁBIL
echo ============================================================
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo Por favor, instale o Python 3.8 ou superior:
    echo https://www.python.org/downloads/
    echo.
    echo Marque a opção "Add Python to PATH" durante a instalação!
    echo.
    pause
    exit /b 1
)

echo ✓ Python encontrado
python --version
echo.

REM Cria ambiente virtual
echo 📦 Criando ambiente virtual...
if not exist venv (
    python -m venv venv
    echo ✓ Ambiente virtual criado
) else (
    echo ✓ Ambiente virtual já existe
)
echo.

REM Ativa ambiente virtual e instala dependências
echo 📥 Instalando dependências...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Erro ao instalar dependências
    pause
    exit /b 1
)
echo ✓ Dependências instaladas
echo.

REM Inicializa banco de dados
echo 🗄️ Inicializando banco de dados...
python init_db.py
if errorlevel 1 (
    echo ❌ Erro ao criar banco de dados
    pause
    exit /b 1
)
echo ✓ Banco de dados criado
echo.

REM Popula com dados de teste
echo 📊 Carregando dados de teste (2 anos)...
python tests\seed_data.py --reset
if errorlevel 1 (
    echo ❌ Erro ao carregar dados
    pause
    exit /b 1
)
echo.

echo ============================================================
echo   ✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!
echo ============================================================
echo.
echo 📋 CREDENCIAIS DE ACESSO:
echo    Admin:        admin / admin123
echo    Gerente:      gerente1 / gerente123
echo    Visualizador: viewer1 / viewer123
echo.
echo 🚀 Para executar o sistema, use: run.bat
echo    (ou clique duas vezes no arquivo run.bat)
echo.
echo ============================================================
pause














