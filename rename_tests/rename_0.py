#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# ===== Script pour renommer des fichiers CSV en fonction des dates ========
#
# Ce script parcourt le dossier FOLDER et renomme les fichiers CSV
# en fonction du FORMAT souhaité (anglais ou français)
#
# Exemple de nom de fichier en format anglais  : 2025-10-24_au_2025-10-30.csv
# Exemple de nom de fichier en format français : 24-10-2025_au_30-10-2025.csv
#
# Nouveau format de nom de fichier visé : YYYY_DD-MM_au_DD-MM.csv
#
#============================================================================

import os
import re


# Dossier contenant les fichiers à renommer
FOLDER = "alertes_a_renommer/"
FORMAT = "anglais"  # ou "français"


# Vérification si le dossier existe
if not os.path.exists(FOLDER):
    print(f"❌ Le dossier '{FOLDER}' n'existe pas.")
    exit(1)


for filename in os.listdir(FOLDER):
    if not filename.lower().endswith(".csv"):
        continue

    old_path = os.path.join(FOLDER, filename)

    if FORMAT == "anglais":
        # Match formats case-insensitively and always produce filenames
        # starting with 'alertes_'
        # Format: YYYY-MM-DD_au_YYYY-MM-DD.csv
        match = re.search(r"(\d{4})[-_]?(\d{2})-(\d{2}).*?au.*?(\d{2})-(\d{2})", filename, re.IGNORECASE)
        if match:
            year, m1, d1, m2, d2 = match.groups()
            # interversion (anglais mm-dd → français dd-mm)
            d1, m1 = m1, d1
            d2, m2 = m2, d2
            new_filename = f"alertes_{year}_{d1}-{m1}_au_{d2}-{m2}.csv"

        # Format: Alertes_YYYY.csv
        elif re.search(r"Alertes[-_](\d{4})\.csv", filename, re.IGNORECASE):
            year = re.search(r"Alertes[-_](\d{4})\.csv", filename, re.IGNORECASE).group(1)
            new_filename = f"alertes_{year}_complet.csv"

        # Format: Alertes_YYYY-MM à MM.csv
        elif re.search(r"Alertes[-_](\d{4})-(\d{2})[ àa](\d{2})\.csv", filename, re.IGNORECASE):
            match = re.search(r"Alertes[-_](\d{4})-(\d{2})[ àa](\d{2})\.csv", filename, re.IGNORECASE)
            year, m1, m2 = match.groups()
            new_filename = f"alertes_{year}_{m1}-{m2}_complet.csv"

        # Format: Alertes_YYYY-MM_DDauDD.csv
        elif re.search(r"Alertes[-_](\d{4})-(\d{2})[-_](\d{2})au(\d{2})\.csv", filename, re.IGNORECASE):
            match = re.search(r"Alertes[-_](\d{4})-(\d{2})[-_](\d{2})au(\d{2})\.csv", filename, re.IGNORECASE)
            year, month, d1, d2 = match.groups()
            new_filename = f"alertes_{year}_{d1}-{month}_au_{d2}-{month}.csv"

        # Format: Alertes_YYYY-MM-DD.csv (single date)
        elif re.search(r"Alertes[-_](\d{4})-(\d{2})-(\d{2})\.csv", filename, re.IGNORECASE):
            match = re.search(r"Alertes[-_](\d{4})-(\d{2})-(\d{2})\.csv", filename, re.IGNORECASE)
            year, month, day = match.groups()
            new_filename = f"alertes_{year}_{day}-{month}.csv"

        else:
            print(f"⚠️ Format non reconnu : {filename}")
            continue

    elif FORMAT == "français":
        # Exemple : 24-10-2025_au_30-10-2025.csv
        match = re.search(r"(\d{2})-(\d{2})-(\d{4}).*?au.*?(\d{2})-(\d{2})-(\d{4})", filename)
        if not match:
            print(f"⚠️ Format non reconnu : {filename}")
            continue

        d1, m1, year1, d2, m2, year2 = match.groups()
        # Pas d'inversion : on garde dd-mm
        # On suppose que les deux années sont identiques
        new_filename = f"alertes_{year1}_{d1}-{m1}_au_{d2}-{m2}.csv"

    else:
        print(f"⚠️ FORMAT inconnu : {FORMAT}")
        break

    new_path = os.path.join(FOLDER, new_filename)
    if os.path.exists(new_path):
        print(f"⚠️ Le fichier {new_filename} existe déjà, renommage ignoré.")
        continue

    os.rename(old_path, new_path)
    print(f"✅ {filename} → {new_filename}")

print("\n🎉 Tous les fichiers ont été renommés !")