
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils import select_date, click_menu_item, safe_find

# ========== Logging ==========
logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

# ========== Charger variables .env ==========
load_dotenv()
ID = os.getenv("ID")
PASSWORD = os.getenv("PASSWORD")
URL = os.getenv("URL")

# ========== Répertoire de téléchargement ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "alertes")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ========== Dates ==========
today = date.today()
start_date = today - timedelta(days=today.weekday() + 7)  # lundi dernier
end_date = start_date + timedelta(days=6)                 # dimanche dernier
start_dt = datetime.combine(start_date, datetime.min.time())
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
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--allow-insecure-localhost")

# ========== ChromeDriver local ==========
CHROMEDRIVER_PATH = r"C:\Users\bcoulet\Documents\projets\rtm_alerte\scrap_waryme\chromedriver.exe"
service = Service(CHROMEDRIVER_PATH)
print("ChromeDriver utilisé :", service.path)

driver = webdriver.Chrome(service=service, options=chrome_options)

# ========== Fonctions ==========
def login(driver):
    logger.info("Ouverture page de connexion")
    driver.get(URL)
    WebDriverWait(driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')

    # Champ identifiant
    username_element = safe_find(driver, [
        ("css", "input[formcontrolname='login']"),
        ("css", "input[placeholder='Email']"),
        ("xpath", "//input[@type='text' or @type='email']")
    ])
    username_element.send_keys(ID)
    logger.info("Identifiant saisi")

    # Bouton Se connecter
    next_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(),'Se connecter')]]"))
    )
    try:
        next_button.click()
    except:
        driver.execute_script("arguments[0].click();", next_button)  # Fallback JS
    logger.info("Bouton 'Se connecter' cliqué")

    # Champ mot de passe
    password_element = safe_find(driver, [
        ("css", "input[type='password']"),
        ("css", "input[aria-label='Mot de passe']"),
        ("xpath", "//input[@type='password']")
    ])
    password_element.send_keys(PASSWORD)
    logger.info("Mot de passe saisi")

    WebDriverWait(driver, 15).until(lambda d: d.current_url != URL)
    logger.info("Connexion réussie")

        # Bouton Se connecter
    next_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(),'Se connecter')]]"))
    )
    try:
        next_button.click()
    except:
        driver.execute_script("arguments[0].click();", next_button)  # Fallback JS
    logger.info("Bouton 'Se connecter' cliqué")

def apply_filters(driver):
    # Menu Alertes internes
    click_menu_item(driver, "Alertes internes")

    # Bouton Filtrer
    filtrer_btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Filtrer']]"))
    )
    driver.execute_script("arguments[0].click();", filtrer_btn)
    logger.info("Bouton 'Filtrer' cliqué")


    # Sélection dates
    toggles = driver.find_elements(By.CSS_SELECTOR, "mat-datepicker-toggle button")
    select_date(driver, start_dt, toggle_selector=toggles[0])
    select_date(driver, end_dt, toggle_selector=toggles[1])

    # Appliquer filtres
    apply_btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//span[normalize-space(text())='Appliquer les filtres']/ancestor::button"))
    )
    driver.execute_script("arguments[0].click();", apply_btn)
    logger.info("Filtres appliqués")

def export_csv(driver):
    before = set(os.listdir(DOWNLOAD_DIR))
    export_btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//span[normalize-space(text())='Exporter']/ancestor::button"))
    )
    driver.execute_script("arguments[0].click();", export_btn)
    logger.info("Export CSV lancé")

    end_time = time.time() + 60
    while time.time() < end_time:
        after = set(os.listdir(DOWNLOAD_DIR))
        new_files = after - before
        if new_files:
            logger.info(f"Fichier téléchargé : {new_files}")
            break
        time.sleep(1)

# ========== Exécution ==========
try:
    login(driver)
    apply_filters(driver)
    
    print(driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='startDate']").get_attribute("value"))
    print(driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='endDate']").get_attribute("value"))
    print("Start:", driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='startDate']").get_attribute("value"))

    export_csv(driver)
    logger.info("Script terminé avec succès")
except Exception as e:
    logger.error(f"Erreur : {e}")
finally:
    # input("Appuyez sur Entrée pour fermer le navigateur...")
    time.sleep(2)  # Attend 2 secondes avant fermeture
    driver.quit()
