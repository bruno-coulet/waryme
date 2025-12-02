


#!/bin/bash
# ===============================
# Wrapper pour exécuter scrap.py
# Windows ne reconnait pas nativmeent les .sh, il faut l'executer via WSL
# ===============================

# Dossier du script
# SCRIPT_DIR="/home/username/projets/rtm_waryme"
SCRIPT_DIR="C:\Users\bcoulet\Documents\projets\RTM_alerte\rtm_waryme"
cd "$SCRIPT_DIR" || exit 1

# Python à utiliser (ou python3 si dans PATH)
# PYTHON="/usr/bin/python3"
PYTHON="/c/Users/bcoulet/AppData/Local/anaconda3/python"

# Lancer le script et capturer logs
$PYTHON scrap.py >> scraper_run.log 2>&1

# Vérifier code retour
if [ $? -ne 0 ]; then
    echo "❌ Erreur détectée, vérifier scraper_run.log"
fi