"""
===============================================================================
 Script : scrap_plw.py
 Auteur : Bruno Coulet - RTM - Dopex
 Version: 1.0 - Réécriture en Playwright du script de scrapping avec selenium
-------------------------------------------------------------------------------
 Objectif :
     Récupération hebdomadaire des alertes internes (semaine précédente) 
     depuis la plateforme WaryMe.

 Fonctionnement Détaillé :
 
 1. Technologie : 
    Utilise Playwright pour une automatisation asynchrone, plus fiable et rapide 
    que Selenium, en particulier sur les applications JavaScript modernes comme 
    Angular, car il gère mieux les temps d'attente et les événements DOM.

 2. Gestion des Dates (Robustesse Critique) :
    a. Format : Calcule la plage de la semaine précédente et utilise le format 
       critique **MM/DD/YYYY**, exigé par le datepicker de l'application.
    b. Injection Forcée : Pour contourner l'état désactivé (`disabled`) du champ 
       de date (typique d'Angular Material), le script utilise `page.evaluate` 
       pour supprimer l'attribut `disabled` via JavaScript, puis utilise 
       `page.fill()` pour injecter la valeur. Cette combinaison garantit la 
       validation du modèle interne d'Angular.

 3. Export :
    L'export CSV est géré par la méthode native Playwright `page.expect_download`, 
    qui écoute l'événement de téléchargement du navigateur de manière synchrone, 
    assurant qu'aucun fichier n'est manqué.

 4. Téléchargement et Renommage :
    Le fichier téléchargé est déplacé et renommé de manière sécurisée (avec suffixe 
    numérique en cas de doublon) dans le répertoire `alertes/`.

 5. Robustesse Générale :
    Les méthodes Playwright comme `page.click()` et `page.fill()` attendent 
    automatiquement que les éléments soient prêts et visibles, ce qui simplifie 
    le code et réduit le besoin d'attentes manuelles (`time.sleep`).
===============================================================================
"""

import os
import asyncio
import time
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import date, timedelta
import locale
from datetime import date

from dotenv import load_dotenv
from playwright.async_api import async_playwright
# Note : Playwright est généralement utilisé de manière asynchrone

# ========== Configuration & Logging ==========
logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ========== Envoi mail en cas d'erreur ==========
def send_error_mail(subject, body):
    # ... (inchangé) ...
    recipients = ["bcoulet@rtm.fr", "bruno.coulet@laplatefrome.io"]
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = "alerte-bot@rtm.fr"
    msg["To"] = ", ".join(recipients)

    try:
        # Configuration SMTP inchangée
        with smtplib.SMTP("localhost") as server:
            server.sendmail(msg["From"], recipients, msg.as_string())
        logger.info("Mail d'erreur envoyé avec succès")
    except Exception as e:
        logger.error(f"Échec envoi mail d'erreur : {e}")


# ========== Fonctions Principales Playwright ==========

async def login(page, ID, PASSWORD, URL):
    """Effectue la connexion en utilisant les identifiants."""
    logger.info("Ouverture page de connexion")
    await page.goto(URL, wait_until="networkidle")

    # 1. Identifiant (Recherche simple car Playwright est plus tolérant)
    # Playwright attend automatiquement que l'élément soit prêt
    await page.fill("input[formcontrolname='login']", ID)
    logger.info("Identifiant saisi")

    # 2. Bouton Se connecter
    await page.click("text=Se connecter")
    logger.info("Bouton 'Se connecter' cliqué")

    # 3. Mot de passe
    await page.fill("input[type='password']", PASSWORD)
    logger.info("Mot de passe saisi")

    # Appuyer sur Entrée pour soumettre le formulaire (équivalent à Keys.RETURN)
    await page.press("input[type='password']", "Enter")

    # Attendre que l'URL change ou qu'un élément post-login apparaisse
    await page.wait_for_url(lambda url: url != URL, timeout=15000)
    logger.info("Connexion réussie")


async def apply_filters(page, start_date: date, end_date: date):
    """Accède aux filtres et injecte les dates."""
    
    logger.info("Accès au menu 'Alertes internes'")
    await page.click("text=Alertes internes")
    await page.wait_for_load_state('networkidle')

    # Bouton Filtrer
    await page.click("button:has-text('Filtrer')")
    logger.info("Bouton 'Filtrer' cliqué, panneau de filtre ouvert")

    # ------------------------------------
    # Injection des dates : Format MM/DD/YYYY et injection forcée, utiliser .fill()
    # ------------------------------------
    
    start_txt = start_date.strftime("%m/%d/%Y")
    end_txt   = end_date.strftime("%m/%d/%Y")
    logger.info(f"Injection des dates (format MM/DD/YYYY): {start_txt} -> {end_txt}")

    # Définition des sélecteurs (ici pour éviter le NameError)
    begin_input_selector = "input[name='beginDate']"
    end_input_selector = "input[name='endDate']"

    # --- Date de début ---
    # Étape critique : Supprimer l'attribut 'disabled' via JS (méthode fiable)
    await page.evaluate("selector => document.querySelector(selector).removeAttribute('disabled')", begin_input_selector)
    await page.fill(begin_input_selector, start_txt)
    
    # --- Date de fin ---
    # Étape critique : Supprimer l'attribut 'disabled' via JS (méthode fiable)
    await page.evaluate("selector => document.querySelector(selector).removeAttribute('disabled')", end_input_selector)
    await page.fill(end_input_selector, end_txt)
    
    # Simuler la perte de focus pour garantir la validation Angular
    await page.focus(end_input_selector)
    await page.keyboard.press("Tab") 
    await asyncio.sleep(1) # Petite pause pour laisser Angular valider les dates

    # ------------------------------------
    # Appliquer filtres
    # ------------------------------------
    await page.click("button:has-text('Appliquer les filtres')")
    logger.info("Bouton 'Appliquer les filtres' cliqué")
    
    # Attendre que la grille de données ait potentiellement des lignes
    await page.wait_for_selector("//tr[@role='row' or contains(@class, 'mat-row')]", 
                                state='attached', timeout=10000)
    logger.info("La grille d'alertes s'est rafraîchie.")


async def export_csv(page, start_date: date, end_date: date, DOWNLOAD_DIR):
    """Déclenche l'export et gère le téléchargement/renommage."""
    
    logger.info("Déclenchement de l'export CSV")
    
    # Playwright gère l'écoute des événements de téléchargement nativement
    async with page.expect_download() as download_info:
        await page.click("button:has-text('Exporter')")
        
    download = await download_info.value
    
    # Renommage du fichier téléchargé
    base_name = f"alertes_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
    new_name = f"{base_name}.csv"
    new_path = os.path.join(DOWNLOAD_DIR, new_name)

    # Si le fichier existe déjà → ajouter suffixe (Logique simplifiée)
    counter = 1
    while os.path.exists(new_path):
        new_path = os.path.join(DOWNLOAD_DIR, f"{base_name}_{counter}.csv")
        counter += 1

    # Sauvegarde du fichier téléchargé vers le nouveau chemin
    await download.save_as(new_path)
    
    logger.info(f"Fichier téléchargé et renommé : {new_path}")
    print(f"✅ Fichier sauvegardé : {new_path}")


async def main():
    """Fonction principale asynchrone."""
    
    # ========== Chargement des variables ==========
    load_dotenv()
    ID = os.getenv("ID")
    PASSWORD = os.getenv("PASSWORD")
    URL = os.getenv("URL")
    
    # ========== Répertoire de téléchargement ==========
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DOWNLOAD_DIR = os.path.join(BASE_DIR, "alertes")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # ========== Calcul des Dates de la Semaine PRÉCÉDENTE ==========
    # Définir la locale française
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')  # sur Linux/macOS
    # Sur Windows, parfois : 'French_France' ou 'fra'
    today = date.today()
    start_date = today - timedelta(days=today.weekday()) - timedelta(days=7) 
    end_date = start_date + timedelta(days=6) 
    print(f"🗓️ Plage des alertes : {start_date.strftime('%d-%b-%Y')} → {end_date.strftime('%d-%b-%Y')}")

    # Lancement du contexte Playwright
    async with async_playwright() as p:
        # Utiliser Chromium pour la compatibilité avec Chrome
        browser = await p.chromium.launch(headless=True) # Mettre True pour le mode silencieux
        page = await browser.new_page(
            # Configurer le répertoire de téléchargement natif de Playwright
            accept_downloads=True,
            java_script_enabled=True,
        )

        try:
            await login(page, ID, PASSWORD, URL)
            await apply_filters(page, start_date, end_date)
            await export_csv(page, start_date, end_date, DOWNLOAD_DIR)
            
            print("✅ Script terminé avec succès")

        except Exception as e:
            logger.error(f"Erreur dans le script : {e}")
            send_error_mail("🚨 Échec scraping alertes (Playwright)", f"Le script a échoué avec l'erreur :\n{e}")
            print(f"❌ Erreur : {e}")

        finally:
            await browser.close()
            logger.info("Navigateur fermé")


# ========== Main Execution ==========
if __name__ == "__main__":
    # Exécuter la fonction principale asynchrone
    asyncio.run(main())