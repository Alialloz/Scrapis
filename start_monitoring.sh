#!/bin/bash
# Script de démarrage pour Linux/Mac

echo "================================================================================"
echo "SCRAPER CENTRIS - MONITORING CONTINU"
echo "================================================================================"
echo ""
echo "Ce script va démarrer le monitoring continu."
echo "Le système vérifiera les nouvelles annonces toutes les heures."
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le monitoring."
echo ""

python3 scraper_production.py

