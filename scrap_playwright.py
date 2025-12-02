import os
import time
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import date, timedelta, datetime

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError

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

# ========== Répertoire download ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "alertes")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ========== Calcul dates ==========
today = date.today()
start_date = today - timedelta(days=today.weekday() + 7)
end_date = start_date + timedelta(days=6)

# ================= Fonctions =================
def login(page):
    logger.info("Connexion en cours…")
    page.goto(URL)

    page.fill("input[formcontrolname='login'], input[placeholder='Email']", ID)
    page.click("button:has-text('Se connecter')")

    page.fill("input[type='password']", PASSWORD)
    page.keyboard.press("Enter")

    page.wait_for_selector("button:has-text('Filtrer')", timeout=20000)
    logger.info("Connexion réussie")

def go_to_alertes(page):
    logger.info("Navigation vers Alertes internes")
    page.click("text='Alertes internes'")

def apply_filters(page):
    logger.info("Application des filtres dates")
    page.click("button:has-text('Filtrer')")

    # attendre que les inputs soient visibles
    page.wait_for_selector("input[formcontrolname='startDate']", timeout=15000)
    # Remplissage direct des champs date (valeurs obligatoires)
    page.fill("input[formcontrolname='startDate']", start_date.strftime("%Y-%m-%d"))

    page.wait_for_selector("input[formcontrolname='endDate']", timeout=15000)
    page.fill("input[formcontrolname='endDate']", end_date.strftime("%Y-%m-%d"))

    page.click("button:has-text('Appliquer les filtres')")

def export_csv(page):
    logger.info("Export CSV")

    with page.expect_download(timeout=60000) as download_info:
        page.click("button:has-text('Exporter')")
    download = download_info.value

    target = os.path.join(
        DOWNLOAD_DIR,
        f"alertes_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.csv"
    )

    # Évite écrasement
    base_target = target
    counter = 1
    while os.path.exists(target):
        target = base_target.replace(".csv", f"_{counter}.csv")
        counter += 1

    download.save_as(target)
    logger.info(f"CSV téléchargé → {target}")
    print(f"📁 Export sauvegardé : {target}")

# ================= Main =================
if __name__ == "__main__":
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=50)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            login(page)
            go_to_alertes(page)
            apply_filters(page)
            export_csv(page)

            print("🎉 Script terminé avec succès")
            logger.info("Script terminé avec succès")

            browser.close()

    except Exception as e:
        logger.error(f"Erreur : {e}")
        send_error_mail("🚨 Échec scraping alertes", f"Erreur :\n{e}")
        print(f"❌ Erreur : {e}")
