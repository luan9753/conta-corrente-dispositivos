@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Conta Corrente de Dispositivos - Atualizacao 10 min

set "PROJECT_DIR=%~dp0"
set "PYTHON_EXE=python"
set "LOG_DIR=%PROJECT_DIR%logs"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:LOOP
set "STAMP=%date% %time%"
echo [%STAMP%] Iniciando atualizacao da Conta Corrente de Dispositivos...

cd /d "%PROJECT_DIR%"

%PYTHON_EXE% "%PROJECT_DIR%gerar_conta_corrente_dispositivos.py" >> "%LOG_DIR%\conta_corrente_10min.log" 2>&1
if errorlevel 1 (
  echo [%date% %time%] ERRO no gerador. Proxima tentativa em 10 minutos. >> "%LOG_DIR%\conta_corrente_10min.log"
  timeout /t 600 /nobreak >nul
  goto LOOP
)

%PYTHON_EXE% "%PROJECT_DIR%validar_conta_corrente_dispositivos.py" >> "%LOG_DIR%\conta_corrente_10min.log" 2>&1
if errorlevel 1 (
  echo [%date% %time%] ERRO no validador. Push bloqueado. Proxima tentativa em 10 minutos. >> "%LOG_DIR%\conta_corrente_10min.log"
  timeout /t 600 /nobreak >nul
  goto LOOP
)

git status --short > "%TEMP%\conta_corrente_git_status.txt" 2>nul
for %%A in ("%TEMP%\conta_corrente_git_status.txt") do set "STATUS_SIZE=%%~zA"
if "!STATUS_SIZE!"=="0" (
  echo [%date% %time%] Sem alteracoes para publicar. >> "%LOG_DIR%\conta_corrente_10min.log"
) else (
  git add CONTA_CORRENTE_DISPOSITIVOS.html CONTA_CORRENTE_DISPOSITIVOS_DATA.js CONTA_CORRENTE_DISPOSITIVOS_CONFIG.json gerar_conta_corrente_dispositivos.py validar_conta_corrente_dispositivos.py RELATORIO_VALIDACAO_CONTA_CORRENTE.md ATUALIZAR_CONTA_CORRENTE_10_MIN.bat .nojekyll .gitignore README.md >> "%LOG_DIR%\conta_corrente_10min.log" 2>&1
  git commit -m "Atualiza conta corrente de dispositivos" >> "%LOG_DIR%\conta_corrente_10min.log" 2>&1
  if not errorlevel 1 (
    git push origin main >> "%LOG_DIR%\conta_corrente_10min.log" 2>&1
  )
)

echo [%date% %time%] Ciclo concluido. Aguardando 10 minutos... >> "%LOG_DIR%\conta_corrente_10min.log"
timeout /t 600 /nobreak >nul
goto LOOP
