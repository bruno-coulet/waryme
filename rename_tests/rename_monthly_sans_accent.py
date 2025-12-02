
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import unicodedata
from datetime import datetime

FOLDER = "alertes_a_renommer/"
OUTPUT_FOLDER = "alertes_renommees/"
DATE_MAX = datetime(2025, 11, 16, 23, 59, 59)
OUTPUT_INVALID = "lignes_invalides.csv"
OUTPUT_FILTERED = "lignes_filtrees.csv"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

invalid_rows = []
filtered_rows = []
total_initial = 0
total_final = 0
all_data = []

def normalize_column_names(columns):
    """Supprime les accents et normalise les noms de colonnes."""
    normalized = []
    for col in columns:
        col_norm = unicodedata.normalize('NFKD', col).encode('ascii', 'ignore').decode('utf-8')
        normalized.append(col_norm)
    return normalized

if not os.path.exists(FOLDER):
    print(f"❌ Le dossier '{FOLDER}' n'existe pas.")
    exit(1)

for filename in os.listdir(FOLDER):
    if filename.lower().endswith(".csv"):
        file_path = os.path.join(FOLDER, filename)
        try:
            df = pd.read_csv(file_path, sep=';', encoding='utf-8')
            initial_count = len(df)
            total_initial += initial_count
            print(f"📂 Lecture : {filename} ({initial_count} lignes)")

            # Normalisation des colonnes
            df.columns = normalize_column_names(df.columns)

            # Conversion Date avec format français forcé
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
            else:
                df['Date'] = pd.NaT

            # Fallback sur Timestamp si Date invalide
            if 'Timestamp' in df.columns:
                mask_invalid = df['Date'].isna()
                if mask_invalid.any():
                    ts_sample = df.loc[mask_invalid, 'Timestamp'].dropna().astype(str).iloc[0]
                    if len(ts_sample) > 10:  # millisecondes
                        df.loc[mask_invalid, 'Date'] = pd.to_datetime(df.loc[mask_invalid, 'Timestamp'], unit='ms')
                    else:
                        df.loc[mask_invalid, 'Date'] = pd.to_datetime(df.loc[mask_invalid, 'Timestamp'], unit='s')

            # Afficher min/max avant filtrage
            if not df['Date'].dropna().empty:
                print(f"   ➡️ Dates min: {df['Date'].min()}, max: {df['Date'].max()}")

            # Lignes invalides
            invalid = df[df['Date'].isna()]
            if not invalid.empty:
                cols_to_keep = [c for c in ['Reference', 'Date'] if c in invalid.columns]
                invalid = invalid[cols_to_keep]
                invalid['Source'] = filename
                invalid_rows.append(invalid)

            # Lignes filtrées (Date > DATE_MAX)
            filtered = df[df['Date'] > DATE_MAX]
            if not filtered.empty:
                cols_to_keep = [c for c in ['Reference', 'Date'] if c in filtered.columns]
                filtered = filtered[cols_to_keep]
                filtered['Source'] = filename
                filtered_rows.append(filtered)

            # Supprimer invalides et filtrées
            df = df.dropna(subset=['Date'])
            df = df[df['Date'] <= DATE_MAX]

            final_count = len(df)
            total_final += final_count
            print(f"   ➡️ Conservées : {final_count}, Perdues : {initial_count - final_count}")

            if final_count > 0:
                all_data.append(df)

        except Exception as e:
            print(f"⚠️ Erreur lecture {filename} : {e}")

# Sauvegarde des lignes invalides
if invalid_rows:
    invalid_df = pd.concat(invalid_rows, ignore_index=True)
    invalid_df.to_csv(OUTPUT_INVALID, sep=';', index=False, encoding='utf-8')
    print(f"✅ Fichier généré : {OUTPUT_INVALID} ({len(invalid_df)} lignes invalides)")
else:
    print("✅ Aucune ligne invalide trouvée.")

# Sauvegarde des lignes filtrées
if filtered_rows:
    filtered_df = pd.concat(filtered_rows, ignore_index=True)
    filtered_df.to_csv(OUTPUT_FILTERED, sep=';', index=False, encoding='utf-8')
    print(f"✅ Fichier généré : {OUTPUT_FILTERED} ({len(filtered_df)} lignes filtrées)")
else:
    print("✅ Aucune ligne filtrée trouvée.")

print(f"\n📊 Total initial : {total_initial}, Total final : {total_final}, Différence : {total_initial - total_final}")

if not all_data:
    print("❌ Aucun fichier valide trouvé.")
    exit(1)

# Regroupement par mois
combined_df = pd.concat(all_data, ignore_index=True)
combined_df['Annee'] = combined_df['Date'].dt.year
combined_df['Mois'] = combined_df['Date'].dt.month

file_count = 0
for (year, month), group in combined_df.groupby(['Annee', 'Mois']):
    group = group.sort_values(by='Date')
    month_str = str(month).zfill(2)
    output_filename = f"alertes_{year}_{month_str}.csv"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    group.drop(columns=['Annee', 'Mois']).to_csv(output_path, sep=';', index=False, encoding='utf-8')
    print(f"✅ Fichier créé : {output_filename} ({len(group)} lignes)")
    file_count += 1

print(f"\n🎉 Terminé : {file_count} fichiers créés, {total_final} lignes réparties dans '{OUTPUT_FOLDER}'.")
