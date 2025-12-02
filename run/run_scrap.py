import os
import subprocess
import sys
import io

# Force l'encodage UTF-8 pour stdout et stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Chemin absolu du dossier du script
SCRIPT_DIR = r"C:\Users\bcoulet\Documents\projets\RTM_alerte\rtm_waryme"
os.chdir(SCRIPT_DIR)

# Chemin vers l'exécutable Python de l'environnement uv
UV_PYTHON = os.path.join(SCRIPT_DIR, ".venv", "Scripts", "python.exe")

# Vérifie si l'environnement uv existe et utilise-le
if os.path.exists(UV_PYTHON):
    python_exe = UV_PYTHON
    print(f"Utilisation de l'environnement uv : {python_exe}")
else:
    python_exe = r"C:\Users\bcoulet\AppData\Local\anaconda3\python.exe"
    print("Attention : L'environnement uv n'est pas trouvé. Selenium peut manquer.")

# Exécuter scrap.py avec l'encodage UTF-8
try:
    result = subprocess.run(
        [python_exe, "scrap.py"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # text=True,
        encoding='utf-8',  # Force l'encodage UTF-8 pour subprocess
        errors='replace',  # Remplace les caractères invalides
    )

    # Écrire les logs dans run_scraper.log (avec encodage UTF-8)
    with open("run_scraper.log", "a", encoding='utf-8') as log_file:
        # log_file.write("=== Exécution réussie ===\n")
        # log_file.write(result.stdout + "\n")
        if result.stdout:
            log_file.write(result.stdout + "\n")
        if result.stderr:
            log_file.write("Erreurs : " + result.stderr + "\n")

except subprocess.CalledProcessError as e:
    with open("run_scraper.log", "a", encoding='utf-8') as log_file:
        log_file.write("=== ERREUR lors de l'exécution ===\n")
        log_file.write(e.stdout + "\n")
        log_file.write(e.stderr + "\n")
    print("Erreur détectée, vérifier run_scraper.log")
    sys.exit(1)
