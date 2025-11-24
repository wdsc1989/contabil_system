@echo off
REM Script de deploy para Windows - Conecta na VPS e executa deploy
REM Uso: deploy_production.bat

echo ========================================
echo   DEPLOY EM PRODUCAO - Sistema Contabil
echo ========================================
echo.

echo [1/3] Verificando status do Git...
git status
echo.

echo [2/3] Conectando na VPS...
echo.
echo Execute os seguintes comandos na VPS:
echo.
echo   cd /opt/contabil/contabil_system
echo   bash deploy/deploy.sh main
echo.
echo ========================================
echo   COMANDOS PARA COPIAR E COLAR NA VPS:
echo ========================================
echo.
echo cd /opt/contabil/contabil_system ^&^& bash deploy/deploy.sh main
echo.
echo ========================================
echo.

pause
echo.
echo Conectando na VPS...
ssh root@72.61.56.204





