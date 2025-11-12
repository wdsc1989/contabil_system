@echo off
chcp 65001 > nul
echo ============================================================
echo   RESETAR DADOS DE TESTE
echo ============================================================
echo.
echo ⚠️ ATENÇÃO: Isso irá apagar todos os dados e recriar
echo    os dados de teste (3 usuários, 5 clientes, 2 anos de dados)
echo.
set /p confirm="Deseja continuar? (S/N): "
if /i not "%confirm%"=="S" (
    echo.
    echo Operação cancelada.
    pause
    exit /b 0
)

echo.
echo 🔄 Resetando dados...

REM Ativa ambiente virtual
call venv\Scripts\activate.bat

REM Reseta dados
python tests\seed_data.py --reset

echo.
echo ============================================================
echo   ✅ DADOS RESETADOS COM SUCESSO!
echo ============================================================
echo.
echo 📋 Credenciais:
echo    Admin:        admin / admin123
echo    Gerente:      gerente1 / gerente123
echo    Visualizador: viewer1 / viewer123
echo.
echo 📊 Dados carregados:
echo    - 5 clientes com tipos diferentes
echo    - 2 anos de transações (~5.200)
echo    - Contratos, contas a pagar/receber
echo.
pause


