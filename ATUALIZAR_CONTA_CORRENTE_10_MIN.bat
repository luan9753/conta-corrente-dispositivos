@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Conta Corrente de Dispositivos - Atualizacao

set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=C:\Users\Administrador\AppData\Local\Programs\Python\Python311\python.exe"
set "LOG_DIR=%PROJECT_DIR%logs"
set "LOCK_DIR=%PROJECT_DIR%.conta_corrente_update.lock"
set "REPORT_FILE=%PROJECT_DIR%RELATORIO_VALIDACAO_CONTA_CORRENTE.md"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

mkdir "%LOCK_DIR%" 2>nul
if errorlevel 1 (
  echo [%date% %time%] Outra atualizacao ainda esta em andamento. Encerrando este disparo.
  exit /b 0
)

:RUN_ONCE
set "STAMP=%date% %time%"
set "RUN_ID=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "RUN_ID=%RUN_ID: =0%"
set "LOG_FILE=%LOG_DIR%\conta_corrente_%RUN_ID%.log"
echo [%STAMP%] Iniciando atualizacao da Conta Corrente de Dispositivos...
echo [%STAMP%] Iniciando atualizacao da Conta Corrente de Dispositivos... >> "%LOG_FILE%"
echo Log: "%LOG_FILE%"
echo Relatorio: "%REPORT_FILE%"

cd /d "%PROJECT_DIR%"

echo.
echo [1/3] Executando gerador...
"%PYTHON_EXE%" -u "%PROJECT_DIR%gerar_conta_corrente_dispositivos.py" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo [%date% %time%] ERRO no gerador. Commit/push bloqueado.
  echo [%date% %time%] ERRO no gerador. Commit/push bloqueado. >> "%LOG_FILE%"
  goto END
)
echo Gerador concluido.

echo.
echo [2/3] Executando validador...
"%PYTHON_EXE%" -u "%PROJECT_DIR%validar_conta_corrente_dispositivos.py" >> "%LOG_FILE%" 2>&1
set "VALIDATOR_EXIT=%ERRORLEVEL%"
if exist "%REPORT_FILE%" (
  findstr /C:"Falhas obrigatorias:" /C:"Alertas:" "%REPORT_FILE%"
  echo Relatorio de validacao: "%REPORT_FILE%"
) else (
  echo Relatorio de validacao nao encontrado: "%REPORT_FILE%"
)

findstr /C:"Falhas obrigatorias: 0" "%REPORT_FILE%" >nul 2>nul
if errorlevel 1 (
  echo [%date% %time%] VALIDACAO COM FALHAS OBRIGATORIAS. Commit/push bloqueado.
  echo [%date% %time%] VALIDACAO COM FALHAS OBRIGATORIAS. Commit/push bloqueado. >> "%LOG_FILE%"
  goto END
)
if not "%VALIDATOR_EXIT%"=="0" (
  echo [%date% %time%] ERRO no validador. Commit/push bloqueado.
  echo [%date% %time%] ERRO no validador. Commit/push bloqueado. >> "%LOG_FILE%"
  goto END
)
echo Validador aprovado sem falhas obrigatorias.

echo.
echo [3/3] Verificando alteracoes para publicar...
git status --short > "%TEMP%\conta_corrente_git_status.txt" 2>nul
for %%A in ("%TEMP%\conta_corrente_git_status.txt") do set "STATUS_SIZE=%%~zA"
if "!STATUS_SIZE!"=="0" (
  echo [%date% %time%] Sem alteracoes para publicar.
  echo [%date% %time%] Sem alteracoes para publicar. >> "%LOG_FILE%"
) else (
  echo [%date% %time%] Validacao OK. Iniciando commit/push automatico...
  echo [%date% %time%] Validacao OK. Iniciando commit/push automatico... >> "%LOG_FILE%"
  git add CONTA_CORRENTE_DISPOSITIVOS.html CONTA_CORRENTE_DISPOSITIVOS_DATA.js CONTA_CORRENTE_DISPOSITIVOS_CONFIG.json gerar_conta_corrente_dispositivos.py validar_conta_corrente_dispositivos.py RELATORIO_VALIDACAO_CONTA_CORRENTE.md ATUALIZAR_CONTA_CORRENTE_10_MIN.bat INSTALAR_ROTINA_CONTA_CORRENTE_10_MIN.bat .nojekyll .gitignore README.md >> "%LOG_FILE%" 2>&1
  git commit -m "Atualiza conta corrente de dispositivos" >> "%LOG_FILE%" 2>&1
  if not errorlevel 1 (
    git push origin main >> "%LOG_FILE%" 2>&1
  )
)

echo [%date% %time%] Ciclo concluido.
echo [%date% %time%] Ciclo concluido. >> "%LOG_FILE%"

:END
if /I "%~1"=="/loop" (
  echo [%date% %time%] Modo loop ativo. Aguardando 10 minutos... >> "%LOG_FILE%"
  timeout /t 600 /nobreak >nul
  goto RUN_ONCE
)

rmdir "%LOCK_DIR%" 2>nul
endlocal
