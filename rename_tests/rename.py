
# import pandas as pd
# import numpy as np
# from pathlib import Path
# import re, tempfile, shutil

# SOURCE_DIR = Path(r"C:\Users\bcoulet\Documents\projets\rtm_alerte\waryme\alertes")
# OUTPUT_DIR = Path(r"C:\Users\bcoulet\Documents\projets\rtm_alerte\waryme\alertes_renommees")
# OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# def safe_write_csv(df: pd.DataFrame, path: Path, sep=";", encoding="utf-8-sig"):
#     with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, suffix=".tmp", encoding=encoding) as tmpf:
#         df.to_csv(tmpf.name, sep=sep, index=False, encoding=encoding)
#         tmp_path = Path(tmpf.name)
#     shutil.move(tmp_path, path)

# def normalize_ws(s: pd.Series) -> pd.Series:
#     return (s.astype(str)
#               .str.replace(r"[\u00A0\u200B]", " ", regex=True)
#               .str.replace(r"\s+", " ", regex=True)
#               .str.strip())

# def parse_date_series(series: pd.Series) -> pd.Series:
#     s = normalize_ws(series)
#     d = pd.to_datetime(s, format="%Y/%m/%d %H:%M", errors="coerce")
#     m = d.isna()
#     if m.any():
#         d2 = pd.to_datetime(s[m], format="%d/%m/%Y %H:%M", errors="coerce")
#         d.loc[m] = d2
#     m = d.isna()
#     if m.any():
#         d3 = pd.to_datetime(s[m], errors="coerce", dayfirst=True)
#         d.loc[m] = d3
#     return d

# def detect_ts_col(df) -> str | None:
#     # priorité au 'Timestamp' exact, sinon '(timestamp)'
#     for c in df.columns:
#         if c.strip().lower() == "timestamp":
#             return c
#     for c in df.columns:
#         if re.search(r"\(timestamp\)\s*$", c, flags=re.IGNORECASE):
#             return c
#     return None

# def parse_ts_series(series: pd.Series) -> pd.Series:
#     s = pd.to_numeric(series, errors="coerce")
#     if s.notna().any():
#         med = float(np.nanmedian(s))
#         unit = "ms" if med > 1e12 else "s"
#         try:
#             return pd.to_datetime(s, unit=unit, errors="coerce")
#         except Exception:
#             return pd.to_datetime(s, unit="s", errors="coerce")
#     return pd.Series(pd.NaT, index=series.index)

# # 1) Lire tous les CSV (sources uniquement). Filtre flexible.
# rows = []
# for p in sorted(SOURCE_DIR.iterdir()):
#     if not p.is_file():
#         continue
#     if p.suffix.lower() != ".csv":
#         continue
#     # exclure explicitement les fichiers de sortie (par prudence)
#     if re.match(r"^alertes_\d{4}_\d{2}\.csv$", p.name, flags=re.IGNORECASE):
#         continue
#     # inclure les exports source ("Alertes_-YYYY-MM.csv" et variantes)
#     if re.match(r"^Alertes_-\d{4}-\d{2}.*\.csv$", p.name, flags=re.IGNORECASE):
#         df = pd.read_csv(p, sep=";", encoding="utf-8-sig", dtype=str)
#         df.columns = [c.strip() for c in df.columns]
#         rows.append(df)

# if not rows:
#     raise FileNotFoundError(f"Aucun fichier source trouvé dans {SOURCE_DIR}")

# all_df = pd.concat(rows, ignore_index=True)

# # (option) déduplication par Référence si c'est la clé (évite répétitions)
# if "Référence" in all_df.columns:
#     before = len(all_df)
#     all_df = all_df.drop_duplicates(subset=["Référence"], keep="first")
#     print(f"Déduplication par Référence : {before} -> {len(all_df)} lignes")

# # 2) Construire série DATETIME temporaire (Date puis fallback Timestamp)
# if "Date" in all_df.columns:
#     dates = parse_date_series(all_df["Date"])
# else:
#     dates = pd.Series(pd.NaT, index=all_df.index)

# ts_col = detect_ts_col(all_df)
# if ts_col:
#     dates = dates.fillna(parse_ts_series(all_df[ts_col]))

# na_count = int(dates.isna().sum())
# print(f"Total: {len(all_df)} | Dates valides: {len(all_df)-na_count} | NaT: {na_count}")

# # 3) Groupement par mois/année et écriture
# periods = dates.dt.to_period("M")
# for p in sorted(periods.dropna().unique()):
#     mask = periods == p
#     group = all_df.loc[mask]  # structure/valeurs inchangées
#     out_name = f"alertes_{p.year}_{p.month:02d}.csv"
#     safe_write_csv(group, OUTPUT_DIR / out_name)
#     print(f"✅ Écrit : {out_name}  ({len(group)} lignes)")

# # 4) Audit des lignes sans date
# if na_count:
#     safe_write_csv(all_df.loc[dates.isna()], OUTPUT_DIR / "alertes_sans_date.csv")
#     print(f"⚠️  Écrit : alertes_sans_date.csv  ({na_count} lignes)")




import pandas as pd
import numpy as np
from pathlib import Path
import re, tempfile, shutil

SOURCE_DIR = Path(r"C:\Users\bcoulet\Documents\projets\rtm_alerte\waryme\alertes")
OUTPUT_DIR = Path(r"C:\Users\bcoulet\Documents\projets\rtm_alerte\waryme\alertes_renommees")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def safe_write_csv(df: pd.DataFrame, path: Path, sep=";", encoding="utf-8-sig"):
    with tempfile.NamedTemporaryFile("w", delete=False, dir=path.parent, suffix=".tmp", encoding=encoding) as tmpf:
        df.to_csv(tmpf.name, sep=sep, index=False, encoding=encoding)
        tmp_path = Path(tmpf.name)
    Path(tmp_path).rename(path)

def normalize_ws(s: pd.Series) -> pd.Series:
    return (s.astype(str)
              .str.replace(r"[\u00A0\u200B]", " ", regex=True)   # espaces non standard
              .str.replace(r"\s+", " ", regex=True)
              .str.strip())

def parse_date_series(series: pd.Series) -> pd.Series:
    s = normalize_ws(series)
    d = pd.to_datetime(s, format="%Y/%m/%d %H:%M", errors="coerce")   # ex: 2025/01/31 21:00
    m = d.isna()
    if m.any():
        d2 = pd.to_datetime(s[m], format="%d/%m/%Y %H:%M", errors="coerce")  # ex: 31/01/2025 21:00
        d.loc[m] = d2
    m = d.isna()
    if m.any():
        d3 = pd.to_datetime(s[m], errors="coerce", dayfirst=True)     # ISO ou variantes
        d.loc[m] = d3
    return d

def detect_ts_col(df) -> str | None:
    for c in df.columns:
        if c.strip().lower() == "timestamp":
            return c
    for c in df.columns:
        if re.search(r"\(timestamp\)\s*$", c.strip(), flags=re.IGNORECASE):
            return c
    return None

def parse_ts_series(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    if s.notna().any():
        med = float(np.nanmedian(s))
        unit = "ms" if med > 1e12 else "s"
        try:
            return pd.to_datetime(s, unit=unit, errors="coerce")
        except Exception:
            return pd.to_datetime(s, unit="s", errors="coerce")
    return pd.Series(pd.NaT, index=series.index)

# 1) Lister les fichiers sources (annuels + mensuels), exclure les outputs
files = []
for p in sorted(SOURCE_DIR.rglob("*.csv")):  # rglob si sous-dossiers
    name = p.name
    # exclure les fichiers générés par le script
    if re.match(r"^alertes_\d{4}_\d{2}\.csv$", name, flags=re.IGNORECASE):
        continue
    if name.lower() == "alertes_sans_date.csv":
        continue
    # inclure les sources : Alertes_-YYYY.csv et Alertes_-YYYY-MM*.csv
    if re.match(r"^Alertes_-\d{4}(?:-\d{2})?.*\.csv$", name, flags=re.IGNORECASE):
        files.append(p)

print("Fichiers pris en compte :", [p.name for p in files])
if not files:
    raise FileNotFoundError(f"Aucun fichier source trouvé dans {SOURCE_DIR}")

# 2) Lire toutes les sources (préserver structure/valeurs)
rows = []
for p in files:
    df = pd.read_csv(p, sep=";", encoding="utf-8-sig", dtype=str)
    df.columns = [c.strip() for c in df.columns]  # trim noms de colonnes
    rows.append(df)

all_df = pd.concat(rows, ignore_index=True)

# 3) Construire la série datetime TEMP (Date puis fallback Timestamp)
if "Date" in all_df.columns:
    dates = parse_date_series(all_df["Date"])
else:
    dates = pd.Series(pd.NaT, index=all_df.index)

ts_col = detect_ts_col(all_df)
if ts_col:
    dates = dates.fillna(parse_ts_series(all_df[ts_col]))

na_count = int(dates.isna().sum())
print(f"Total: {len(all_df)} | Dates valides: {len(all_df)-na_count} | NaT: {na_count}")

# 4) Groupement par mois/année (Period('M')) et DÉDOUBLONNAGE PAR MOIS
periods = dates.dt.to_period("M")
unique_periods = sorted(periods.dropna().unique())

for p in unique_periods:
    mask = periods == p
    group = all_df.loc[mask].copy()  # structure/valeurs inchangées

    # dédoublonnage PAR MOIS (évite de “perdre” un mois si Référence apparaît dans un autre fichier)
    if "Référence" in group.columns:
        before = len(group)
        group = group.drop_duplicates(subset=["Référence"], keep="first")
        after = len(group)
        print(f"   {p}: dédup Référence {before}->{after}")

    out_name = f"alertes_{p.year}_{p.month:02d}.csv"
    safe_write_csv(group, OUTPUT_DIR / out_name)
    print(f"✅ Écrit : {out_name}  ({len(group)} lignes)")

# 5) Lignes sans date (audit)
if na_count:
    safe_write_csv(all_df.loc[dates.isna()], OUTPUT_DIR / "alertes_sans_date.csv")
