@echo off
REM ========================================
REM Script de lancement pour scrap.py
REM ========================================

REM Obtenir le chemin du script
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Logger le debut d'execution
echo ========================================= >> run_scraper.log
echo [%date% %time%] Demarrage du script >> run_scraper.log
echo ========================================= >> run_scraper.log

REM Activer l'environnement virtuel si il existe
if exist "venv\Scripts\activate.bat" (
    echo Activation environnement virtuel... >> run_scraper.log
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Activation environnement virtuel... >> run_scraper.log
    call .venv\Scripts\activate.bat
)

REM Executer le script Python
echo Execution de scrap.py... >> run_scraper.log
python scrap.py >> run_scraper.log 2>&1

REM Capturer le code de sortie
set EXIT_CODE=%ERRORLEVEL%

REM Logger la fin
echo [%date% %time%] Fin execution - Code sortie: %EXIT_CODE% >> run_scraper.log
echo. >> run_scraper.log

REM Optionnel: garder la fenetre ouverte en cas d'erreur (a commenter pour le planificateur)
REM if %EXIT_CODE% NEQ 0 pause

exit /b %EXIT_CODE%