
"""
===============================================================================
Script : regroupement et renommage d’alertes CSV par mois (avec déduplication)
Auteur : Coulet Bruno  |  Dernière mise à jour : 2025-12-14
Python : 3.10+  |  Dépendances : pandas, numpy

OBJET
-----
Agrège plusieurs fichiers CSV d’alertes (structures possiblement hétérogènes),
aligne leurs colonnes sur un "header de référence", déduplique les lignes,
puis exporte des fichiers mensuels nommés `alertes_YYYY_MM.csv`. Les lignes
sans date exploitable sont exportées dans `alertes_sans_date.csv` (audit).

PRINCIPE DE FONCTIONNEMENT
--------------------------
1) **Découverte des sources** : parcourt `SOURCE_DIR` (récursif) et sélectionne
   tous les fichiers `*.csv` sauf ceux déjà générés par le script
   (`alertes_YYYY_MM.csv` et `alertes_sans_date.csv`).

2) **Header de référence** : lit uniquement l’en-tête (ligne 1) du **fichier
   le plus récent** trouvé et s’en sert comme schéma colonne → ordre attendu.

3) **Lecture & alignement** :
   - Lit chaque CSV **sans** son en-tête (skiprows=1), en `dtype=str`,
     séparateur `;`, encodage `utf-8-sig`, moteur `python` (tolérant).
   - Tronque les colonnes excédentaires si un fichier en possède plus.
   - Renomme/alimente les colonnes selon le header de référence (colonnes
     manquantes → NaN), puis concatène toutes les sources alignées.

4) **Déduplication** :
   - Si la colonne **"Référence"** existe : supprime les doublons sur
     "Référence" (garde le premier).
   - Puis seconde passe de déduplication **sur toutes les colonnes** (lignes
     strictement identiques).

5) **Construction de la date** :
   - Si la colonne **"Date"** existe : parse selon ces formats, dans l’ordre :
       a) `JJ/MM/AAAA HH:MM:SS`
       b) `JJ/MM/AAAA HH:MM`
       c) fallback générique (dayfirst=True)
   - Si une colonne **"Timestamp"** (nom exact, insensible à la casse
     détectée) existe : convertit des timestamps **en secondes ou millisecondes**
     (détection par médiane) et complète les dates manquantes.

6) **Groupement & export** :
   - Regroupe par période mensuelle (année-mois) et écrit un CSV par mois
     dans `OUTPUT_DIR` : `alertes_YYYY_MM.csv`, colonnes dans l’ordre
     du header de référence.
   - Les lignes **sans date** sont exportées dans `alertes_sans_date.csv`.

ENTRÉES / SORTIES
-----------------
• Entrées  : tous les `*.csv` sous `SOURCE_DIR` (séparateur `;`, encodage UTF-8 SIG).
• Sorties  : fichiers `alertes_YYYY_MM.csv` + `alertes_sans_date.csv` sous `OUTPUT_DIR`.
• Encodage : `utf-8-sig` (BOM) pour compatibilité Excel/Windows.

PARAMÈTRES & CONSTANTES
-----------------------
• SOURCE_DIR : dossier racine des CSV sources (à adapter).
• OUTPUT_DIR : dossier de sortie (créé s’il n’existe pas).
• SEP        : séparateur CSV attendu (par défaut `;`).
• ENCODING   : encodage des fichiers (par défaut `utf-8-sig`).

ROBUSTESSE / CHOIX TECHNIQUES
-----------------------------
• Lecture en `engine='python'` pour mieux tolérer des `;` "perdus" dans les données.
• Écritures "safe" : passage par fichier temporaire + `.replace()` (Windows)
  pour éviter les conflits d’accès.
• Normalisation des espaces (espaces insécables, multiples) avant parse des dates.
• Détection auto secondes vs millisecondes pour "Timestamp".

LIMITES & ATTENTES SUR LES DONNÉES
----------------------------------
• Le **header de référence** est celui du fichier **le plus récent** trouvé.
  Si sa structure est incorrecte, l’alignement peut induire des NaN.
• Les fichiers avec **plus de colonnes** que le header verront leurs colonnes
  excédentaires **ignorées**.
• Les formats de date non listés peuvent tomber dans le fallback (dayfirst=True)
  ou échouer (classés "sans date").
• La colonne "Timestamp" doit contenir des valeurs numériques (en s ou ms).

UTILISATION
-----------
1) Vérifier / adapter `SOURCE_DIR` et `OUTPUT_DIR` ci-dessous.
2) Lancer le script : `python rename.py`
3) Surveiller la console pour le résumé (nb de fichiers, dédup, exports).

HISTORIQUE (résumé)
-------------------
• 2025-12-14 : ajout du cartouche documentaire, clarifications, commentaires.
• 2025-??-?? : ajout fallback parse dates + détection s/ms pour "Timestamp".
• 2025-??-?? : écriture sécurisée via fichier temporaire + replace().
===============================================================================
"""



import pandas as pd
import numpy as np
from pathlib import Path
import re
import tempfile
import os

# --- Configuration et Chemins ---
# VEUILLEZ VÉRIFIER QUE LE CHEMIN EST CORRECT
SOURCE_DIR = Path(r"C:\Users\bcoulet\Documents\projets\rtm_alerte\waryme\alertes_a_renommer") 
OUTPUT_DIR = Path(r"C:\Users\bcoulet\Documents\projets\rtm_alerte\waryme\alertes_recomposees")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SEP = ";"
ENCODING = "utf-8-sig"

# --- Fonctions Utilitaires ---

def safe_write_csv(df: pd.DataFrame, path: Path):
    """Écrit le DataFrame dans un fichier CSV de manière sécurisée (via tempfile) et utilise replace()."""
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, suffix=".tmp", encoding=ENCODING) as tmpf:
        df.to_csv(tmpf.name, sep=SEP, index=False, encoding=ENCODING)
        tmp_path = Path(tmpf.name)
        
    # Utilisation de .replace() pour forcer l'écrasement sur Windows (correction de FileExistsError)
    Path(tmp_path).replace(path)

def normalize_ws(s: pd.Series) -> pd.Series:
    """Nettoie les espaces non-standards et multiples."""
    return (s.astype(str)
             .str.replace(r"[\u00A0\u200B]", " ", regex=True)
             .str.replace(r"\s+", " ", regex=True)
             .str.strip())

def parse_date_series(series: pd.Series) -> pd.Series:
    """Parse les dates en se concentrant sur le format JJ/MM/AAAA HH:MM:SS (et variantes)."""
    s = normalize_ws(series)
    dates = pd.Series(pd.NaT, index=s.index)

    # 1. Essai du format JJ/MM/AAAA HH:MM:SS (selon votre description)
    d1 = pd.to_datetime(s, format="%d/%m/%Y %H:%M:%S", errors="coerce")
    dates.loc[d1.notna()] = d1.loc[d1.notna()]
    
    # 2. Essai du format JJ/MM/AAAA HH:MM (si les secondes manquent)
    mask = dates.isna()
    d2 = pd.to_datetime(s[mask], format="%d/%m/%Y %H:%M", errors="coerce")
    dates.loc[mask] = d2
    
    # 3. Fallback générique (pour les cas exceptionnels, par exemple le nouveau format 2025/01/31)
    mask = dates.isna()
    dates.loc[mask] = pd.to_datetime(s[mask], errors="coerce", dayfirst=True)

    return dates

def detect_ts_col(df) -> str | None:
    """Détecte la colonne de timestamp."""
    # On se concentre sur 'Timestamp' comme identifié précédemment
    for c in df.columns:
        if c.strip().lower() == "timestamp":
            return c
    return None

def parse_ts_series(series: pd.Series) -> pd.Series:
    """Convertit un timestamp numérique (s ou ms) en datetime."""
    s = pd.to_numeric(series, errors="coerce")
    if s.notna().any():
        med = float(np.nanmedian(s.dropna()))
        unit = "ms" if med > 1e12 else "s"
        return pd.to_datetime(s, unit=unit, errors="coerce")
    return pd.Series(pd.NaT, index=series.index)


# --- Processus Principal ---

print(f"Dossier source : {SOURCE_DIR}")
print(f"Dossier d'exportation : {OUTPUT_DIR}")

# 1. Lister tous les fichiers source
files = []
for p in sorted(SOURCE_DIR.rglob("*.csv")):
    name = p.name
    # Exclure les fichiers générés par le script
    if re.match(r"^alertes_\d{4}_\d{2}\.csv$", name, flags=re.IGNORECASE):
        continue
    if name.lower() == "alertes_sans_date.csv":
        continue
    files.append(p)

if not files:
    print(f"❌ AUCUN fichier source trouvé dans {SOURCE_DIR}.")
    exit()

print(f"\nFichiers sources pris en compte ({len(files)}) : {[p.name for p in files]}")

# 2. Déterminer le header de référence (du fichier le plus récent)
latest_file_path = files[-1]
try:
    # Lire uniquement la première ligne pour obtenir les noms de colonnes
    header_reference_df = pd.read_csv(latest_file_path, sep=SEP, encoding=ENCODING, nrows=0)
    # Nettoyer et définir l'ordre de référence des colonnes
    header_reference = [c.strip() for c in header_reference_df.columns]
    print(f"Header de référence (du fichier {latest_file_path.name}) : {len(header_reference)} colonnes.")
except Exception as e:
    print(f"❌ Erreur critique lors de la lecture du header de référence du fichier {latest_file_path.name}: {e}")
    exit()

# 3. Lire toutes les sources (sans header), les aligner et les concaténer
rows = []
print("\n--- Étape 3 : Lecture, Alignement et Concaténation ---")
for p in files:
    try:
        # 1. Lire les données en sautant la ligne d'en-tête (header=None)
        df = pd.read_csv(
            p, 
            sep=SEP, 
            encoding=ENCODING, 
            header=None,  
            skiprows=1,   
            dtype=str,  # Lecture en chaîne de caractères pour éviter les confusions de types
            # CORRECTION : Utilisation du moteur Python pour tolérer les erreurs de formatage (;) dans les données  
            engine='python'
        )
        
        # S'assurer que le nombre de colonnes du DataFrame n'excède pas le header de référence
        # C'est une vérification de sécurité
        if df.shape[1] > len(header_reference):
             print(f"⚠️ Avertissement : Le fichier {p.name} a plus de colonnes de données ({df.shape[1]}) que le header de référence ({len(header_reference)}). Les colonnes excédentaires seront ignorées.")
             df = df.iloc[:, :len(header_reference)]
             
        # 2. Renommer les colonnes lues (0, 1, 2...) avec les noms du header de référence
        df.columns = header_reference[:df.shape[1]]
        
        # 3. Alignement explicite sur toutes les colonnes de référence (ajoute les colonnes manquantes en NaN)
        df_aligned = df.reindex(columns=header_reference) 
        rows.append(df_aligned)
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement du fichier {p.name} : {e}")

if not rows:
    print("Aucune donnée valide à traiter.")
    exit()

# Concaténation de toutes les données ALIGNÉES
all_df = pd.concat(rows, ignore_index=True)
header = header_reference 

total_rows_before_dedup = len(all_df)
print(f"\nNombre total de lignes avant déduplication : {total_rows_before_dedup}")

# 4. Déduplication globale
df_final = all_df.copy()

if "Référence" in df_final.columns:
    # 1. Déduplication sur l'ID de référence
    df_final['Référence'] = df_final['Référence'].astype(str)
    df_final = df_final.drop_duplicates(subset=["Référence"], keep="first")
    
# 2. Déduplication sur l'ensemble des colonnes (pour capturer les lignes sans Référence ou les doublons stricts)
df_final = df_final.astype(str).drop_duplicates(keep="first")


rows_after_dedup = len(df_final)
print(f"Nombre total de lignes après déduplication : {rows_after_dedup} (supprimé {total_rows_before_dedup - rows_after_dedup})")


# 5. Construction de la série datetime TEMP pour le groupement
dates = pd.Series(pd.NaT, index=df_final.index) 

if "Date" in df_final.columns:
    dates = parse_date_series(df_final["Date"]) 

ts_col = detect_ts_col(df_final)
if ts_col:
    # Utiliser le Timestamp pour combler les dates manquantes
    dates = dates.fillna(parse_ts_series(df_final[ts_col]))

na_count = int(dates.isna().sum())
print(f"Dates valides pour le groupement: {len(df_final)-na_count} | Dates manquantes/invalides (NaT): {na_count}")


# 6. Groupement par mois/année et Exportation
periods = dates.dt.to_period("M")
unique_periods = sorted(periods.dropna().unique())

print(f"\nDébut de l'exportation par mois dans le dossier : {OUTPUT_DIR}")

for p in unique_periods:
    mask = periods == p
    group = df_final.loc[mask].copy() 
    
    # S'assurer que les colonnes sont dans l'ordre du header de référence
    group_to_export = group[header]
    
    # Nommage du fichier selon le format "alertes_YYYY_MM.csv"
    out_name = f"alertes_{p.year}_{p.month:02d}.csv"
    out_path = OUTPUT_DIR / out_name
    
    safe_write_csv(group_to_export, out_path)
    print(f"✅ Écrit : {out_name} ({len(group_to_export)} lignes)")

# 7. Lignes sans date (audit)
if na_count > 0:
    df_sans_date = df_final.loc[dates.isna()]
    out_name_audit = "alertes_sans_date.csv"
    safe_write_csv(df_sans_date[header], OUTPUT_DIR / out_name_audit)
    print(f"⚠️ Écrit l'audit des lignes sans date : {out_name_audit} ({len(df_sans_date)} lignes)")

print("\nProcessus de traitement et d'exportation terminé.")