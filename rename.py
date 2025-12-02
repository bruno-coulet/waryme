#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
============================================================================
Script : Regroupement des alertes par mois (préservation totale des données)
Auteur : Coulet Bruno
Date   : 2025-11-30

Description :
    - Lit tous les CSV d’un dossier (même source, même structure)
    - Ne modifie AUCUNE donnée (toutes les colonnes lues en str)
    - Ne touche pas aux fichiers source
    - Concatène toutes les données
    - Redistribue dans un CSV par mois (alertes_YYYY_MM.csv)
    - Génère un fichier d’audit pour les dates invalides
============================================================================
"""

import os
import pandas as pd
from datetime import datetime

# ----------------------------- Configuration ------------------------------

FOLDER = "alertes_a_renommer/"
OUTPUT_FOLDER = "alertes_renommees/"
OUTPUT_INVALID = "alertes_lignes_invalides.csv"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ----------------------------- Stockage temporaire ------------------------

invalid_rows = []
all_data = []

total_initial = 0
total_final   = 0

# ----------------------------- Fonctions utiles ---------------------------

def load_csv_raw(path):
    """Lecture brute d'un CSV sans aucune transformation."""
    return pd.read_csv(
        path,
        sep=';',
        encoding='utf-8',
        dtype=str,
        keep_default_na=False,
        na_filter=False
    )


def parse_date_column(df):
    """
    Crée une colonne Date_parsed :
    - parse Date en format français JJ/MM/YYYY HH:MM:SS
    - fallback sur Timestamp (unix s ou ms)
    """
    date_parsed = pd.to_datetime(
        df.get("Date", ""),
        format="%d/%m/%Y %H:%M:%S",
        errors="coerce"
    )

    # Fallback si Timestamp est présent
    if "Timestamp" in df.columns:
        mask = date_parsed.isna() & df["Timestamp"].astype(str).ne("")
        if mask.any():
            sample = df.loc[mask, "Timestamp"].astype(str).iloc[0]
            unit = "ms" if len(sample) > 10 else "s"
            date_parsed.loc[mask] = pd.to_datetime(
                df.loc[mask, "Timestamp"], unit=unit, errors="coerce"
            )

    return date_parsed

# ----------------------------- Traitement principal -----------------------

if not os.path.exists(FOLDER):
    print(f"❌ Le dossier '{FOLDER}' n'existe pas.")
    exit(1)

for filename in os.listdir(FOLDER):
    if not filename.lower().endswith(".csv"):
        continue

    path = os.path.join(FOLDER, filename)
    try:
        df = load_csv_raw(path)
        initial_count = len(df)
        total_initial += initial_count

        print(f"\n📂 Lecture : {filename} ({initial_count} lignes)")

        # Ajouter colonne Date_parsed
        df["Date_parsed"] = parse_date_column(df)

        # Stats min/max
        valid_dates = df["Date_parsed"].dropna()
        if not valid_dates.empty:
            print(f"   ➡️ Dates min: {valid_dates.min()}, max: {valid_dates.max()}")

        # Lignes avec dates invalides
        invalid = df[df["Date_parsed"].isna()]
        if not invalid.empty:
            invalid = invalid.copy()
            invalid["Source"] = filename
            invalid_rows.append(invalid)

        # Garder uniquement les lignes avec date valide
        df_valid = df[df["Date_parsed"].notna()]

        final_count = len(df_valid)
        total_final += final_count

        print(f"   ➡️ Conservées : {final_count}, Invalides : {initial_count - final_count}")

        if final_count > 0:
            all_data.append(df_valid)

    except Exception as e:
        print(f"⚠️ Erreur lecture {filename} : {e}")

# ----------------------------- Audit : invalides -------------------------

if invalid_rows:
    invalid_df = pd.concat(invalid_rows, ignore_index=True)
    invalid_df.to_csv(OUTPUT_INVALID, sep=';', index=False, encoding='utf-8')
    print(f"\n⚠️ Fichier lignes invalides : {OUTPUT_INVALID} ({len(invalid_df)})")
else:
    print("\n✔ Aucune ligne invalide.")

print(f"\n📊 Total initial : {total_initial}")
print(f"📊 Total final   : {total_final}")
print(f"📉 Différence    : {total_initial - total_final}")

if not all_data:
    print("\n❌ Aucun fichier exploitable.")
    exit(1)

# ----------------------------- Regroupement par mois ----------------------

combined = pd.concat(all_data, ignore_index=True)

combined["Année"] = combined["Date_parsed"].dt.year
combined["Mois"]  = combined["Date_parsed"].dt.month

file_count = 0

for (year, month), group in combined.groupby(["Année", "Mois"]):
    month_str = f"{month:02d}"
    out = f"alertes_{year}_{month_str}.csv"
    path = os.path.join(OUTPUT_FOLDER, out)

    # Supprimer les colonnes techniques
    group = group.drop(columns=["Année", "Mois", "Date_parsed"])

    group.to_csv(path, sep=';', index=False, encoding='utf-8-sig')
    print(f"   ✔ {out} ({len(group)} lignes)")
    file_count += 1

print(f"\n🎉 Terminé : {file_count} fichiers générés dans '{OUTPUT_FOLDER}'.")
