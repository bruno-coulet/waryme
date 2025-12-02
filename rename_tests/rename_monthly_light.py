import csv
import os
from datetime import datetime

INPUT_FOLDER = "alertes_a_renommer"
OUTPUT_FOLDER = "output_by_month"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

writers = {}
files_out = {}

global_ok = 0
global_errors = 0
global_total = 0


def get_month_key(date_str):
    # Format : "31/12/2024 21:59"
    dt = datetime.strptime(date_str.strip(), "%d/%m/%Y %H:%M")
    return dt.strftime("%Y_%m")


print("\n============================")
print("   TRAITEMENT CSV (OK)")
print("============================\n")


for file in os.listdir(INPUT_FOLDER):
    if not file.endswith(".csv"):
        continue

    print(f"\n=== Traitement : {file} ===")

    file_total = 0
    file_ok = 0
    file_errors = 0

    with open(os.path.join(INPUT_FOLDER, file), "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=";")

        try:
            header = next(reader)
        except StopIteration:
            print("⚠ Fichier vide")
            continue

        for row in reader:
            file_total += 1
            global_total += 1

            if not row or len(row) < 2:
                file_errors += 1
                global_errors += 1
                continue

            try:
                key = get_month_key(row[1])
            except Exception:
                file_errors += 1
                global_errors += 1
                continue

            out_path = os.path.join(OUTPUT_FOLDER, f"{key}.csv")

            if key not in writers:
                fout = open(out_path, "w", newline="", encoding="utf-8")
                files_out[key] = fout
                writer = csv.writer(fout, delimiter=";")
                writers[key] = writer
                writer.writerow(header)

            writers[key].writerow(row)
            file_ok += 1
            global_ok += 1

    print(f"--- Résumé fichier {file} ---")
    print(f"  ✔ OK      : {file_ok}")
    print(f"  ❌ Erreurs : {file_errors}")
    print(f"  ➜ Total    : {file_total}")


# fermeture
for fout in files_out.values():
    fout.close()

print("\n==========================")
print("✔ Lignes OK :", global_ok)
print("❌ Erreurs   :", global_errors)
print("➡ Total     :", global_total)
print("==========================")
