@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Conta Corrente de Dispositivos - Atualizacao

set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=C:\Users\Administrador\AppData\Local\Programs\Python\Python311\python.exe"
set "LOG_DIR=%PROJECT_DIR%logs"
set "LOCK_DIR=%PROJECT_DIR%.conta_corrente_update.lock"
set "REPORT_FILE=%PROJECT_DIR%RELATORIO_VALIDACAO_CONTA_CORRENTE.md"
set "LOCK_MAX_MINUTES=15"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

if exist "%LOCK_DIR%" (
  set "LOCK_AGE_MINUTES="
  for /f "usebackq delims=" %%A in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$lock='%LOCK_DIR%'; if(Test-Path -LiteralPath $lock){ [int]((Get-Date)-(Get-Item -LiteralPath $lock).CreationTime).TotalMinutes } else { -1 }"`) do set "LOCK_AGE_MINUTES=%%A"
  if defined LOCK_AGE_MINUTES (
    if !LOCK_AGE_MINUTES! GEQ %LOCK_MAX_MINUTES% (
      echo [%date% %time%] Lock antigo encontrado ^(!LOCK_AGE_MINUTES! min^). Limpando lock de execucao interrompida.
      rmdir /s /q "%LOCK_DIR%" 2>nul
    )
  )
)

mkdir "%LOCK_DIR%" 2>nul
if errorlevel 1 (
  echo [%date% %time%] Outra atualizacao ainda esta em andamento. Encerrando este disparo.
  echo Se a rotina foi interrompida com Ctrl+C, aguarde %LOCK_MAX_MINUTES% minutos ou remova: "%LOCK_DIR%"
  exit /b 0
)
echo Inicio: %date% %time% > "%LOCK_DIR%\started.txt"
echo Usuario: %COMPUTERNAME%\%USERNAME% >> "%LOCK_DIR%\started.txt"
echo Pasta: %PROJECT_DIR% >> "%LOCK_DIR%\started.txt"

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
echo Esta etapa pode levar alguns minutos. Acompanhe o log: "%LOG_FILE%"
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
  echo [%date% %time%] VALIDACAO COM FALHAS OBRIGATORIAS. Publicacao liberada para validacao controlada em producao.
  echo [%date% %time%] VALIDACAO COM FALHAS OBRIGATORIAS. Publicacao liberada para validacao controlada em producao. >> "%LOG_FILE%"
  set "VALIDATION_STATUS=COM_FALHAS"
) else (
  set "VALIDATION_STATUS=OK"
)
if not "%VALIDATOR_EXIT%"=="0" (
  if exist "%REPORT_FILE%" (
    echo [%date% %time%] Validador retornou codigo %VALIDATOR_EXIT%, mas gerou relatorio. Publicacao liberada para validacao controlada.
    echo [%date% %time%] Validador retornou codigo %VALIDATOR_EXIT%, mas gerou relatorio. Publicacao liberada para validacao controlada. >> "%LOG_FILE%"
    set "VALIDATION_STATUS=COM_FALHAS"
  ) else (
    echo [%date% %time%] ERRO no validador sem relatorio gerado. Commit/push bloqueado.
    echo [%date% %time%] ERRO no validador sem relatorio gerado. Commit/push bloqueado. >> "%LOG_FILE%"
    goto END
  )
)
if "%VALIDATION_STATUS%"=="OK" (
  echo Validador aprovado sem falhas obrigatorias.
) else (
  echo Validador executado com falhas obrigatorias registradas no relatorio. Publicacao seguira mesmo assim.
)

echo.
echo [3/3] Verificando alteracoes para publicar...
git status --short > "%TEMP%\conta_corrente_git_status.txt" 2>nul
for %%A in ("%TEMP%\conta_corrente_git_status.txt") do set "STATUS_SIZE=%%~zA"
if "!STATUS_SIZE!"=="0" (
  echo [%date% %time%] Sem alteracoes para publicar.
  echo [%date% %time%] Sem alteracoes para publicar. >> "%LOG_FILE%"
) else (
  echo [%date% %time%] Validacao concluida ^(!VALIDATION_STATUS!^). Iniciando commit/push automatico...
  echo [%date% %time%] Validacao concluida ^(!VALIDATION_STATUS!^). Iniciando commit/push automatico... >> "%LOG_FILE%"
  git add CONTA_CORRENTE_DISPOSITIVOS.html CONTA_CORRENTE_DISPOSITIVOS_DATA.js CONTA_CORRENTE_DISPOSITIVOS_CONFIG.json RELATORIO_VALIDACAO_CONTA_CORRENTE.md ATUALIZAR_CONTA_CORRENTE_10_MIN.bat INSTALAR_ROTINA_CONTA_CORRENTE_10_MIN.bat .nojekyll .gitignore README.md >> "%LOG_FILE%" 2>&1
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

if exist "%LOCK_DIR%" rmdir /s /q "%LOCK_DIR%" 2>nul
endlocal
