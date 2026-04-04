@echo off
setlocal

:: Configurações do NSS Sabla
set SCRIPTS_DIR=%~dp0
set VENV_PYTHON=%SCRIPTS_DIR%..\.venv\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
    echo [X] Erro: Ambiente virtual não encontrado em .venv\Scripts\python.exe.
    echo      Execute 'python setup_nss.py' antes de usar este agendador.
    exit /b 1
)

echo ==================================================
echo   NUTRICIONES SABLA - AGENDAMENTO DE SERVICOS      
echo ==================================================

:: 07:00 - Gerar Digest Diário para o Profissional
schtasks /create /tn "NSS_Digest_Diario" /tr "%VENV_PYTHON% %SCRIPTS_DIR%enviar_digest_diario.py" /sc daily /st 07:00 /f
echo [✔] Digest Diário agendado para as 07:00 (Diário).

:: A cada 30 min - Gmail Listener (Ouvinte de Mensagens e Exames)
schtasks /create /tn "NSS_Gmail_Listener" /tr "%VENV_PYTHON% %SCRIPTS_DIR%testar_escuta_gmail.py" /sc minute /mo 30 /f
echo [✔] Escuta do Gmail agendada a cada 30 minutos.

:: 20:00 - Executar Tarefas Diárias (Régua de Confirmação e Conteúdo)
schtasks /create /tn "NSS_Tarefas_Diarias" /tr "%VENV_PYTHON% %SCRIPTS_DIR%executar_tarefas_diarias.py" /sc daily /st 20:00 /f
echo [✔] Régua de Confirmação agendada para as 20:00 (Diário).

echo ==================================================
echo   SERVICOS AGENDADOS COM SUCESSO NO WINDOWS        
echo   Verifique no 'Agendador de Tarefas' do sistema.   
echo ==================================================
pause
