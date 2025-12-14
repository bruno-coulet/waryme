"""
===============================================================================
 Script : scrap.py
 Auteur : Bruno Coulet - RTM - Dopex
 Date   : 06/06/2025 (Mise à jour pour Chrome/Angular : 12/12/2025)
 Version: 2.5 - Optimisation et Correction du Format MM/DD/YYYY
-------------------------------------------------------------------------------
 Objectif :
     Ce script automatise la récupération hebdomadaire des alertes internes 
     depuis la plateforme WaryMe pour la SEMAINE PRÉCÉDENTE.

 Fonctionnement Détaillé :
 
 1. Initialisation : 
    Charge les identifiants depuis le fichier `.env`. Le chemin du ChromeDriver 
    n'est plus nécessaire grâce à Selenium Manager. Le script calcule ensuite 
    précisément le lundi et le dimanche de la semaine précédente.

 2. Lancement du Navigateur :
    Lance une instance de Chrome via Selenium Manager avec un profil configuré 
    pour autoriser les téléchargements automatiques dans le dossier `alertes/`.

 3. Connexion (login) :
    Navigue vers l'URL WaryMe et utilise la fonction `safe_find` pour localiser 
    les champs d'identifiant et de mot de passe de manière robuste (gestion 
    des sélecteurs multiples en cascade).

 4. Application des Filtres (apply_filters) :
    a. Navigation : Accède au menu "Alertes internes" et clique sur "Filtrer".
    b. Injection des dates (Robustesse Angular) : Pour contourner les validations 
       strictes de la plateforme Angular, le script utilise une injection 
       JavaScript (`inject_date_js`) qui :
       * Supprime l'attribut `disabled` des champs.
       * Définit directement la valeur au format **MM/DD/YYYY** (Mois/Jour/Année), 
         le format que l'application WaryMe exige, malgré l'interface française.
       * Déclenche manuellement les événements DOM (`input`, `change`, `blur`) 
         nécessaires pour forcer la mise à jour du modèle Angular.
    c. Application : Clique sur le bouton "Appliquer les filtres" et attend 
       que la grille de résultats se rafraîchisse.

 5. Export et Sauvegarde (export_csv) :
    a. Export : Clique sur le bouton "Exporter", également via une injection 
       JavaScript forcée pour garantir le déclenchement du téléchargement.
    b. Attente et Renommage : Attend l'apparition du fichier CSV dans le répertoire 
       `alertes/` (tout en ignorant les fichiers temporaires `.crdownload`). Le 
       fichier est ensuite renommé au format `alertes_YYYY-MM-JJ_YYYY-MM-JJ.csv` 
       de manière sécurisée, ajoutant un suffixe numérique (`_1`, `_2`, etc.) 
       en cas de doublon.

 6. Gestion des Erreurs :
    En cas de `TimeoutException` (élément non trouvé, chargement trop long) ou 
    d'autres exceptions, le script envoie automatiquement un email d'alerte 
    aux destinataires définis et ferme le navigateur (`driver.quit()`).
===============================================================================
"""

import os
import time
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import date, timedelta

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Assurez-vous que ces fonctions sont définies dans utils.py
from utils import click_menu_item, safe_find 

# ========== Logging ==========
logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ========== Envoi mail en cas d'erreur ==========
def send_error_mail(subject, body):
    recipients = ["bcoulet@rtm.fr", "bruno.coulet@laplatefrome.io"]
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = "alerte-bot@rtm.fr"
    msg["To"] = ", ".join(recipients)

    try:
        with smtplib.SMTP("localhost") as server:
            server.sendmail(msg["From"], recipients, msg.as_string())
        logger.info("Mail d'erreur envoyé avec succès")
    except Exception as e:
        logger.error(f"Échec envoi mail d'erreur : {e}")


# ========== Charger variables .env ==========
load_dotenv()
ID = os.getenv("ID")
PASSWORD = os.getenv("PASSWORD")
URL = os.getenv("URL")

# ========== Répertoire de téléchargement des alertes ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "alertes")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ========== Chrome Options ==========
chrome_options = Options()
prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True,
}
chrome_options.add_experimental_option("prefs", prefs)

# ================================================================
# FONCTION DE SUPPORT (Extraction de la fonction locale)
# ================================================================

def inject_date_js(driver, element, date_string):
    """
    Définit la date par JS, enlève disabled, et simule les événements clés
    pour forcer la validation Angular.
    """
    # 1. Enlever disabled
    driver.execute_script("arguments[0].removeAttribute('disabled');", element)
    time.sleep(0.1)
    
    # 2. Définir la valeur directement via la propriété value
    driver.execute_script("arguments[0].value = arguments[1];", element, date_string)
    time.sleep(0.1)
    
    # 3. Simuler les événements nécessaires (Input, Change, Blur)
    driver.execute_script("""
        arguments[0].dispatchEvent(new Event('input',  { bubbles: true }));
        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        arguments[0].dispatchEvent(new Event('blur',   { bubbles: true })); 
    """, element)
    time.sleep(0.2)

# ================================================================
# FONCTIONS PRINCIPALES
# ================================================================

def login(driver):
    logger.info("Ouverture page de connexion")
    driver.get(URL)
    WebDriverWait(driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')

    # Identifiant 
    username_element = safe_find(driver, [
        ("css", "input[formcontrolname='login']"), 
        ("css", "input[placeholder='Email']"), 
        ("xpath", "//input[@type='text' or @type='email']") 
    ])
    username_element.send_keys(ID)
    logger.info("Identifiant saisi")

    # Bouton Se connecter
    next_button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(),'Se connecter')]]"))
    )
    next_button.click()
    logger.info("Bouton 'Se connecter' cliqué")

    # Mot de passe
    password_element = safe_find(driver, [
        ("css", "input[type='password']"), 
        ("css", "input[aria-label='Mot de passe']"), 
        ("xpath", "//input[@type='password']") 
    ])

    password_element.send_keys(PASSWORD + Keys.RETURN)
    logger.info("Mot de passe saisi")

    WebDriverWait(driver, 15).until(lambda d: d.current_url != URL)
    logger.info("Connexion réussie")


def apply_filters(driver, start_date: date, end_date: date):
    logger.info("Accès au menu 'Alertes internes'")
    click_menu_item(driver, "Alertes internes", screenshot_path="debug_alertes.png")
    time.sleep(2)

    # Bouton Filtrer
    filtrer_btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Filtrer']]"))
    )
    driver.execute_script("arguments[0].click();", filtrer_btn)
    logger.info("Bouton 'Filtrer' cliqué, panneau de filtre ouvert")
    time.sleep(1) 

    # ------------------------------------
    # Injection des dates : Utilisation de la fonction externalisée
    # ------------------------------------
    
    # Format MM/DD/YYYY (Mois/Jour/Année - format requis par l'UI)
    start_txt = start_date.strftime("%m/%d/%Y")
    end_txt   = end_date.strftime("%m/%d/%Y")

    logger.info(f"Injection des dates (format MM/DD/YYYY par JS): {start_txt} -> {end_txt}")
    
    begin_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "beginDate")))
    end_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "endDate")))

    # Appel des fonctions d'injection
    inject_date_js(driver, begin_input, start_txt)
    inject_date_js(driver, end_input, end_txt)
    time.sleep(1) 

    # ------------------------------------
    # Appliquer filtres
    # ------------------------------------
    apply_btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//span[normalize-space(text())='Appliquer les filtres']/ancestor::button"))
    )
    
    driver.execute_script("arguments[0].click();", apply_btn)
    logger.info("Bouton 'Appliquer les filtres' cliqué")
    
    # Attente conditionnelle pour le rafraîchissement de la grille
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//tr[@role='row' or contains(@class, 'mat-row')]"))
        )
        logger.info("La grille d'alertes s'est rafraîchie.")
    except TimeoutException:
        logger.warning("La grille d'alertes ne s'est pas rafraîchie ou est vide.")

    time.sleep(3)


def export_csv(driver, start_date: date, end_date: date):
    before = set(os.listdir(DOWNLOAD_DIR))

    # Trouver et cliquer sur le bouton Export
    export_btn = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((
            By.XPATH,
            "//button[.//span[normalize-space(text())='Exporter']]"
        ))
    )
    
    # Forcer le clic via JS 
    driver.execute_script("""
        const btn = arguments[0];
        btn.removeAttribute('disabled');
        btn.click();
    """, export_btn)
    logger.info("Bouton 'Exporter' cliqué via JS forcé")
    print("🔎 Vérification JS : export_btn.disabled =", driver.execute_script("return arguments[0].disabled;", export_btn))

    print("📥 En attente de téléchargement dans :", DOWNLOAD_DIR)

    # Attente du fichier téléchargé
    file_path = None
    end_time = time.time() + 60
    while time.time() < end_time:
        after = set(os.listdir(DOWNLOAD_DIR))
        new_files = after - before
        csvs = [f for f in new_files if f.endswith(".csv") and not f.endswith(".crdownload")]
        if csvs:
            file_path = os.path.join(DOWNLOAD_DIR, csvs[0])
            if not file_path.endswith(".crdownload"):
                break
        time.sleep(1)

    if not file_path:
        page_content = driver.page_source
        if "Aucune alerte trouvée" in page_content or "No alerts found" in page_content:
             logger.warning("Aucun fichier CSV téléchargé, probablement car la grille est vide.")
        raise Exception("Aucun fichier CSV téléchargé")

    # Nouveau nom basé sur les dates
    base_name = f"alertes_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
    new_path = os.path.join(DOWNLOAD_DIR, f"{base_name}.csv")

    # Si le fichier existe déjà → ajouter suffixe (Logique simplifiée)
    counter = 1
    while os.path.exists(new_path):
        new_path = os.path.join(DOWNLOAD_DIR, f"{base_name}_{counter}.csv")
        counter += 1

    # Un seul renommage
    os.rename(file_path, new_path)
    logger.info(f"Fichier téléchargé et renommé : {new_path}")
    print(f"✅ Fichier sauvegardé : {new_path}")


# ========== Main Execution ==========
if __name__ == "__main__":
    
    # Correction de la logique de date pour obtenir la SEMAINE PRÉCÉDENTE
    today = date.today()
    start_date = today - timedelta(days=today.weekday()) - timedelta(days=7) 
    end_date = start_date + timedelta(days=6) 
    print(f"🗓️ Plage des alertes : {start_date} → {end_date}")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        print("✅ Debug : driver.title =", driver.title)
        login(driver)
        
        apply_filters(driver, start_date, end_date)
        export_csv(driver, start_date, end_date)
        
        print("✅ Script terminé avec succès")

    except (TimeoutException, NoSuchElementException, Exception) as e:
        logger.error(f"Erreur dans le script : {e}")
        send_error_mail("🚨 Échec scraping alertes", f"Le script a échoué avec l'erreur :\n{e}")
        print(f"❌ Erreur : {e}")

    finally:
        driver.quit()
        logger.info("Navigateur fermé")