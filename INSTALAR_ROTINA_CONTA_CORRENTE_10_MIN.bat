@echo off
setlocal EnableExtensions
title Instalar rotina - Conta Corrente de Dispositivos

set "PROJECT_DIR=%~dp0"
set "TASK_NAME=ContaCorrenteDispositivos10Min"
set "BAT_FILE=%PROJECT_DIR%ATUALIZAR_CONTA_CORRENTE_10_MIN.bat"

if not exist "%BAT_FILE%" (
  echo Arquivo nao encontrado: "%BAT_FILE%"
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$taskName='%TASK_NAME%'; $bat='%BAT_FILE%'; $action=New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c \"' + $bat + '\"') -WorkingDirectory (Split-Path $bat -Parent); $trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 10); Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Description 'Atualiza e publica a Conta Corrente de Dispositivos a cada 10 minutos' -Force | Out-Null"
if errorlevel 1 (
  echo Falha ao criar a tarefa "%TASK_NAME%".
  exit /b 1
)

echo Tarefa "%TASK_NAME%" criada para executar a cada 10 minutos.
echo Para executar manualmente agora: schtasks /Run /TN "%TASK_NAME%"
endlocal
