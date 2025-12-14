#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ===============================
# 
# Ouvre Chrome à l'URL de waryme 
# entre les identifiants
# selectionne alertes internes
# filtre les dates : du lundi au dimanche (dernier dimanche à date)
# Exporte les  .csv dans le dossier  scrap_waryme/alertes
# 
# nom de fichier souhaité :  alertes_YYYY_dd_mm_au_dd-mm
# 

# ===============================

import os
import time
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
from utils import select_date, click_menu_item, safe_find

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--start-maximized")

# Chemin absolu vers chromedriver
service = Service(r"C:\Users\bcoulet\Documents\projets\rtm_alerte\scrap_waryme\chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)
# Import de chjromedriver
# from webdriver_manager.chrome import ChromeDriverManager
# service = Service(ChromeDriverManager().install()) 




# ========== Logging ==========
logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding='utf-8'
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


# ========== Charger variables .env pour se connecter à WaryMe ==========
load_dotenv()
ID = os.getenv("ID")
PASSWORD = os.getenv("PASSWORD")
URL = os.getenv("URL")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")

# ========== Répertoire de téléchargement des alertes ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "alertes")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ========== Dates ==========
today = date.today()
start_date = today - timedelta(days=today.weekday() + 7)  # lundi dernier
end_date = start_date + timedelta(days=6)                 # dimanche dernier
start_dt = datetime.combine(start_date, datetime.min.time())
# end_dt = datetime.combine(end_date, datetime.max.time())
end_dt = datetime.combine(end_date, datetime.strptime("23:59:59", "%H:%M:%S").time())

print(f"Plage des alertes : {start_date} , {end_date}")

# ========== Chrome Options ==========
chrome_options = Options()
prefs = {
    "download.default_directory": DOWNLOAD_DIR,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.add_argument("--start-maximized")

# ========== Fonctions principales ==========
def login(driver):
    logger.info("Ouverture page de connexion")
    driver.get(URL)
    WebDriverWait(driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')

    # Identifiant
    # username_element = WebDriverWait(driver, 15).until(
    #     EC.element_to_be_clickable((By.CSS_SELECTOR, "input[formcontrolname='login']"))
    # )
    username_element = safe_find(driver, [
    ("css", "input[formcontrolname='login']"),         # sélecteur actuel
    ("css", "input[placeholder='Email']"),             # fallback si dispo
    ("xpath", "//input[@type='text' or @type='email']") # fallback générique
    ])
    username_element.send_keys(ID)
    logger.info("Identifiant saisi")

    # Bouton Se connecter
    next_button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(),'Se connecter')]]"))
    )
    next_button.click()
    logger.info("Bouton 'Se connecter' clique")

    # Mot de passe
    # password_element = WebDriverWait(driver, 30).until(
    #     EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password']"))
    # )
    password_element = safe_find(driver, [
    ("css", "input[type='password']"),                 # sélecteur actuel
    ("css", "input[aria-label='Mot de passe']"),       # fallback
    ("xpath", "//input[@type='password']")             # fallback générique
    ])

    password_element.send_keys(PASSWORD + Keys.RETURN)
    logger.info("Mot de passe saisi")

    WebDriverWait(driver, 15).until(lambda d: d.current_url != URL)
    logger.info("Connexion réussie")


def apply_filters(driver):
    # Menu Alertes internes
    click_menu_item(driver, "Alertes internes", screenshot_path="debug_alertes.png")

    # Bouton Filtrer
    filtrer_btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Filtrer']]"))
    )
    driver.execute_script("arguments[0].click();", filtrer_btn)
    logger.info("Bouton 'Filtrer' clique")

    # Sélection dates
    # select_date(driver, start_dt, toggle_selector="mat-datepicker-toggle[data-mat-calendar='mat-datepicker-0'] button")
    # select_date(driver, end_dt, toggle_selector="mat-datepicker-toggle[data-mat-calendar='mat-datepicker-1'] button")
    toggles = driver.find_elements(By.CSS_SELECTOR, "mat-datepicker-toggle button")
    select_date(driver, start_dt, toggle_selector=toggles[0])
    select_date(driver, end_dt, toggle_selector=toggles[1])



    # Appliquer filtres
    apply_btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//span[normalize-space(text())='Appliquer les filtres']/ancestor::button"))
    )
    driver.execute_script("arguments[0].click();", apply_btn)
    logger.info("Bouton 'Appliquer les filtres' clique")


def export_csv(driver):
    before = set(os.listdir(DOWNLOAD_DIR))

    export_btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//span[normalize-space(text())='Exporter']/ancestor::button"))
    )
    driver.execute_script("arguments[0].click();", export_btn)
    logger.info("Bouton 'Exporter' clique")

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
        raise Exception("Aucun fichier CSV téléchargé")

    # Nouveau nom basé sur les dates
    start_year_month = start_date.strftime('%Y_%m')
    start_day = start_date.strftime('%d')
    end_day_month = end_date.strftime('%d-%m')

    # new_name = f"alertes_{start_date.strftime('%Y_%m-%d')}_au_{end_date.strftime('%m-%d')}.csv"
    new_name = f"alertes_{start_year_month}_du_{start_day}_au_{end_day_month}.csv"
   
    new_path = os.path.join(DOWNLOAD_DIR, new_name)

    # Si le fichier existe déjà → ajouter suffixe
    counter = 1
    base_new_path = new_path
    while os.path.exists(new_path):
        new_path = base_new_path.replace(".csv", f"_{counter}.csv")
        counter += 1

    # Un seul renommage
    os.rename(file_path, new_path)
    logger.info(f"Fichier téléchargé et renommé : {new_path}")
    print(f"Fichier sauvegardé : {new_path}")



# ========== Main ==========
if __name__ == "__main__":
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        login(driver)
        apply_filters(driver)
        export_csv(driver)
        print("Script terminé avec succès")

    except (TimeoutException, NoSuchElementException, Exception) as e:
        logger.error(f"Erreur dans le script : {e}")
        # send_error_mail("Échec scraping alertes", f"Le script a échoué avec l'erreur :\n{e}")
        print(f"Erreur : {e}")

    finally:
        driver.quit()
        logger.info("Navigateur fermé")