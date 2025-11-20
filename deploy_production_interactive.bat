@echo off
REM Script interativo de deploy para produção
REM Guia o usuário através do processo de deploy

echo.
echo ============================================================
echo   DEPLOY PARA PRODUCAO - Sistema Contabil
echo ============================================================
echo.

REM Verificar se está no diretório correto
if not exist "app.py" (
    echo ERRO: Execute este script de dentro do diretorio contabil_system
    pause
    exit /b 1
)

echo [1/5] Verificando conexao com GitHub...
git fetch origin
if errorlevel 1 (
    echo ERRO: Nao foi possivel conectar ao GitHub
    echo Verifique sua conexao com a internet e tente novamente
    pause
    exit /b 1
)
echo OK: Conexao com GitHub estabelecida
echo.

echo [2/5] Verificando status do repositorio...
git status --short
echo.
set /p confirm="Deseja continuar com o deploy? (S/N): "
if /i not "%confirm%"=="S" (
    echo Deploy cancelado
    pause
    exit /b 0
)
echo.

echo [3/5] Informacoes do servidor
echo.
set /p SERVER_IP="Digite o IP do servidor (ex: 72.61.56.204): "
set /p SERVER_USER="Digite o usuario SSH (ex: root): "
set /p APP_DIR="Digite o diretorio da aplicacao no servidor (ex: /opt/contabil): "
if "%APP_DIR%"=="" set APP_DIR=/opt/contabil
echo.

echo [4/5] Preparando comandos de deploy...
echo.
echo Comandos que serao executados no servidor:
echo   1. cd %APP_DIR%
echo   2. git pull origin main
echo   3. bash deploy/deploy.sh
echo.

set /p confirm="Confirma o deploy? (S/N): "
if /i not "%confirm%"=="S" (
    echo Deploy cancelado
    pause
    exit /b 0
)
echo.

echo [5/5] Conectando ao servidor e executando deploy...
echo.
echo Conectando via SSH...
echo.

REM Conecta via SSH e executa o deploy
ssh %SERVER_USER%@%SERVER_IP% "cd %APP_DIR% && git pull origin main && bash deploy/deploy.sh"

if errorlevel 1 (
    echo.
    echo ERRO: Falha no deploy
    echo Verifique os logs acima para mais detalhes
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   DEPLOY CONCLUIDO COM SUCESSO!
echo ============================================================
echo.
echo Aplicacao disponivel em:
echo   http://%SERVER_IP%:8501
echo.
echo Comandos uteis:
echo   Ver logs: ssh %SERVER_USER%@%SERVER_IP% "journalctl -u contabil.service -f"
echo   Status: ssh %SERVER_USER%@%SERVER_IP% "systemctl status contabil.service"
echo.
pause

