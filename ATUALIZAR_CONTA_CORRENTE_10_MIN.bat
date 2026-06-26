@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Conta Corrente de Dispositivos - Atualizacao

set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=python"
set "LOG_DIR=%PROJECT_DIR%logs"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:RUN_ONCE
set "STAMP=%date% %time%"
echo [%STAMP%] Iniciando atualizacao da Conta Corrente de Dispositivos...

cd /d "%PROJECT_DIR%"

%PYTHON_EXE% "%PROJECT_DIR%gerar_conta_corrente_dispositivos.py" >> "%LOG_DIR%\conta_corrente_10min.log" 2>&1
if errorlevel 1 (
  echo [%date% %time%] ERRO no gerador. Push bloqueado. >> "%LOG_DIR%\conta_corrente_10min.log"
  goto END
)

%PYTHON_EXE% "%PROJECT_DIR%validar_conta_corrente_dispositivos.py" >> "%LOG_DIR%\conta_corrente_10min.log" 2>&1
if errorlevel 1 (
  echo [%date% %time%] ERRO no validador. Push bloqueado. >> "%LOG_DIR%\conta_corrente_10min.log"
  goto END
)

git status --short > "%TEMP%\conta_corrente_git_status.txt" 2>nul
for %%A in ("%TEMP%\conta_corrente_git_status.txt") do set "STATUS_SIZE=%%~zA"
if "!STATUS_SIZE!"=="0" (
  echo [%date% %time%] Sem alteracoes para publicar. >> "%LOG_DIR%\conta_corrente_10min.log"
) else (
  git add CONTA_CORRENTE_DISPOSITIVOS.html CONTA_CORRENTE_DISPOSITIVOS_DATA.js CONTA_CORRENTE_DISPOSITIVOS_CONFIG.json gerar_conta_corrente_dispositivos.py validar_conta_corrente_dispositivos.py RELATORIO_VALIDACAO_CONTA_CORRENTE.md ATUALIZAR_CONTA_CORRENTE_10_MIN.bat INSTALAR_ROTINA_CONTA_CORRENTE_10_MIN.bat .nojekyll .gitignore README.md >> "%LOG_DIR%\conta_corrente_10min.log" 2>&1
  git commit -m "Atualiza conta corrente de dispositivos" >> "%LOG_DIR%\conta_corrente_10min.log" 2>&1
  if not errorlevel 1 (
    git push origin main >> "%LOG_DIR%\conta_corrente_10min.log" 2>&1
  )
)

echo [%date% %time%] Ciclo concluido. >> "%LOG_DIR%\conta_corrente_10min.log"

:END
if /I "%~1"=="/loop" (
  echo [%date% %time%] Modo loop ativo. Aguardando 10 minutos... >> "%LOG_DIR%\conta_corrente_10min.log"
  timeout /t 600 /nobreak >nul
  goto RUN_ONCE
)

endlocal
