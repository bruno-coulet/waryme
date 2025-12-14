import argparse
import os
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def detect_date_column(df: pd.DataFrame):
    # Try to find a column that looks like a date
    for col in df.columns:
        sample = df[col].dropna().astype(str).iloc[:5]
        for s in sample:
            try:
                pd.to_datetime(s, dayfirst=True)
                return col
            except Exception:
                break
    return None


def normalize_date_col(df: pd.DataFrame, col: str):
    df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
    return df


def main(input_dir, output_dir, dry_run=False):
    os.makedirs(output_dir, exist_ok=True)

    all_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith('.csv')]
    logger.info(f"Found {len(all_files)} CSV files in {input_dir}")

    # global set of hashes to avoid duplicates across months
    seen_hashes = set()

    monthly_groups = {}  # (year, month) -> list of rows (DataFrame)

    for fp in all_files:
        try:
            df = pd.read_csv(fp)
        except Exception as e:
            logger.error(f"Failed to read {fp}: {e}")
            continue

        date_col = detect_date_column(df)
        if not date_col:
            logger.warning(f"No date-like column detected in {fp}, skipping")
            continue

        df = normalize_date_col(df, date_col)
        if df[date_col].isna().all():
            logger.warning(f"All dates invalid in {fp}, skipping")
            continue

        # For each row, determine month-year and append
        for _, row in df.iterrows():
            dt = row[date_col]
            if pd.isna(dt):
                continue
            key = (dt.year, dt.month)
            row_tuple = tuple(row.astype(str).tolist())
            row_hash = hash(row_tuple)
            if (row_hash) in seen_hashes:
                continue
            seen_hashes.add(row_hash)
            if key not in monthly_groups:
                monthly_groups[key] = []
            monthly_groups[key].append(row)

    # Write per-month files
    for (y, m), rows in sorted(monthly_groups.items()):
        out_name = os.path.join(output_dir, f"alertes_{y:04d}-{m:02d}.csv")
        logger.info(f"Writing {len(rows)} rows to {out_name}")
        if dry_run:
            continue
        out_df = pd.DataFrame(rows)
        # ensure date column is first column
        cols = list(out_df.columns)
        # try to place date-like col first
        for c in cols:
            try:
                if pd.api.types.is_datetime64_any_dtype(out_df[c]):
                    cols.insert(0, cols.pop(cols.index(c)))
                    break
            except Exception:
                pass
        out_df = out_df[cols]
        out_df.to_csv(out_name, index=False, encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', default='alertes', help='Input folder with CSVs')
    parser.add_argument('--output', '-o', default='alertes_merged', help='Output folder')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    main(args.input, args.output, args.dry_run)
