@echo off
REM Script de demarrage pour Windows
echo ================================================================================
echo SCRAPER CENTRIS - MONITORING CONTINU
echo ================================================================================
echo.
echo Ce script va demarrer le monitoring continu.
echo Le systeme verifiera les nouvelles annonces toutes les heures.
echo.
echo Appuyez sur Ctrl+C pour arreter le monitoring.
echo.
pause

python scraper_production.py

pause




