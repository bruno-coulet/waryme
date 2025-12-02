# select_date()
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime

#  safe_find()
import logging

# click_menu_item()
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

def select_date(driver, dt: datetime, toggle_selector="mat-datepicker-toggle[matSuffix] button", timeout=15):
    """
    Selectionne la date `dt` (datetime) dans le mat-datepicker Angular Material :
    - clic sur le toggle du datepicker
    - clic sur le bouton periode (mois/annee)
    - selection de l'annee
    - selection du mois
    - selection du jour
    """

    year_txt = str(dt.year)                     # ex: "2025"
    month_abbr = dt.strftime("%b").upper()      # ex: "SEP"
    day_txt = str(dt.day)                       # ex: "18"

    def latest_overlay():
        """Retourne le dernier overlay actif (popup calendrier)."""
        overlays = driver.find_elements(By.CSS_SELECTOR, "div.cdk-overlay-pane")
        return overlays[-1] if overlays else None

    # --- 1) ouvrir le datepicker
    if isinstance(toggle_selector, str):
        toggle = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, toggle_selector))
        )
    else:
        toggle = toggle_selector  # si c'est dejà un WebElement


    driver.execute_script("arguments[0].click();", toggle)
    print("Datepicker ouvert")
    time.sleep(0.3)

    overlay = WebDriverWait(driver, timeout).until(lambda d: latest_overlay())

    # --- 2) bouton periode (mois/annee)
    period_btn = WebDriverWait(overlay, timeout).until(
        lambda ov: ov.find_element(By.CSS_SELECTOR, "button.mat-calendar-period-button")
    )
    driver.execute_script("arguments[0].click();", period_btn)
    print("Selecteur mois/annee ouvert")
    time.sleep(0.3)

    # --- 3) choisir l'annee
    year_btn = WebDriverWait(overlay, timeout).until(
        lambda ov: ov.find_element(By.XPATH, f".//button[@aria-label='{year_txt}']")
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", year_btn)
    driver.execute_script("arguments[0].click();", year_btn)
    print(f"Annee {year_txt} selectionnee")
    time.sleep(0.3)

    # --- 4) choisir le mois
    month_btn = WebDriverWait(overlay, timeout).until(
        lambda ov: ov.find_element(By.XPATH, f".//span[normalize-space(text())='{month_abbr}']")
    )
    driver.execute_script("arguments[0].click();", month_btn)
    print(f"Mois {month_abbr} selectionne")
    time.sleep(0.3)

    # --- 5) choisir le jour
    day_btn = WebDriverWait(overlay, timeout).until(
        lambda ov: ov.find_element(By.XPATH, f".//span[normalize-space(text())='{day_txt}']")
    )
    driver.execute_script("arguments[0].click();", day_btn)
    print(f"Jour {day_txt} selectionne")
    time.sleep(0.3)

    
    # Après avoir cliqué sur le jour
    driver.execute_script("""
        const input = document.querySelector('input[formcontrolname="startDate"]'); 
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    """)



# ============ Au cas ou le selecteur de login change ============
def safe_find(driver, selectors, timeout=15):
    """
    Essaie plusieurs Selecteurs (CSS ou XPATH) jusqu'à trouver un element cliquable.
    selectors = [("css", "input[...]"), ("xpath", "//input[...]"), ...]
    """
    for method, value in selectors:
        try:
            if method == "css":
                return WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, value))
                )
            elif method == "xpath":
                return WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, value))
                )
        except TimeoutException:
            continue
    raise TimeoutException(f"Aucun Selecteur valide trouve parmi : {selectors}")


# logger = logging.getLogger(__name__)

# def safe_find(driver, selectors, timeout=15):
#     """
#     Recherche un element sur la page avec plusieurs Selecteurs possibles (fallback) de manière robuste.

#     Paramètres :
#         driver : WebDriver
#             L'instance Selenium WebDriver.
#         selectors : list[str]
#             Liste de Selecteurs CSS ou XPATH à tester dans l'ordre.
#             Exemple : ["input[formcontrolname='login']", "input[placeholder='Email']"]
#         timeout : int, optionnel (par defaut=15)
#             Temps maximum (en secondes) pour attendre qu'un element devienne cliquable.

#     Retour :
#         WebElement
#             L'element trouve et cliquable.

#     Exceptions :
#         TimeoutException
#             Si aucun des Selecteurs ne permet de trouver un element cliquable dans le timeout.

#     Description :
#         - Teste chaque Selecteur dans l'ordre.
#         - Attends que l'element soit cliquable.
#         - Logue chaque tentative et succès.
#         - Lève une exception claire si aucun Selecteur ne fonctionne.
#     """
#     for idx, sel in enumerate(selectors, start=1):
#         try:
#             logger.info(f"Essai #{idx} avec le Selecteur : {sel}")
#             if sel.strip().startswith("//"):
#                 # XPath
#                 element = WebDriverWait(driver, timeout).until(
#                     EC.element_to_be_clickable((By.XPATH, sel))
#                 )
#             else:
#                 # CSS
#                 element = WebDriverWait(driver, timeout).until(
#                     EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
#                 )
#             logger.info(f"Élement trouve avec le Selecteur #{idx} : {sel}")
#             return element
#         except TimeoutException:
#             logger.warning(f"❌ Selecteur #{idx} non trouve : {sel}")
#         except Exception as e:
#             logger.error(f"Erreur avec le Selecteur #{idx} ({sel}) : {e}")

#     logger.error(f"❌ Aucun des Selecteurs n'a fonctionne : {selectors}")
#     raise TimeoutException(f"Aucun element cliquable trouve avec les Selecteurs : {selectors}")



# ============== Debuggage =============
def click_menu_item(driver, text, timeout=20, screenshot_path='debug_alertes.png'):
    """
    Tente de cliquer sur un item de menu contenant `text` en multipliant les approches.
    Sauvegarde un screenshot et l'outerHTML des elements candidats si echec.
    """
    xpaths = [
        f"//span[normalize-space()='{text}']",
        f"//span[contains(normalize-space(.),'{text}')]",
        f"//*[normalize-space(text())='{text}']",
        f"//*[contains(normalize-space(.),'{text}')]"
    ]

    # Recuperer candidats (presence)
    candidates = []
    for xp in xpaths:
        try:
            elems = WebDriverWait(driver, timeout).until(
                EC.presence_of_all_elements_located((By.XPATH, xp))
            )
            if elems:
                candidates.extend(elems)
        except TimeoutException:
            pass

    if not candidates:
        print(f"Aucun element trouve pour le texte '{text}' (xpaths testes). Je sauvegarde un screenshot.")
        driver.save_screenshot(screenshot_path)
        raise TimeoutException(f"Aucun element trouve pour '{text}'")

    print(f"Found {len(candidates)} candidate(s) — je vais tenter plusieurs methodes de clic...")

    for idx, el in enumerate(candidates, start=1):
        try:
            outer = driver.execute_script("return arguments[0].outerHTML;", el)
            print(f"\n--- Candidate #{idx} ---\n{outer[:1000]}\n--- end outerHTML ---")
        except Exception:
            print(f"Candidate #{idx}: impossible d'obtenir outerHTML")

        # Assurer que l'element est visible
        try:
            if not el.is_displayed():
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                time.sleep(0.3)
        except Exception:
            pass

        # 1) click() direct
        try:
            el.click()
            print("click() direct reussi")
            return True
        except Exception as e:
            print("click() direct echoue :", repr(e))

        # 2) ActionChains move_to_element + click
        try:
            ActionChains(driver).move_to_element(el).click().perform()
            print("ActionChains click reussi")
            return True
        except Exception as e:
            print("ActionChains echoue :", repr(e))

        # 3) JS click
        try:
            driver.execute_script("arguments[0].click();", el)
            print("JS click reussi")
            return True
        except Exception as e:
            print("JS click echoue :", repr(e))

        # 4) clic par offset (au centre) + diagnostic overlay
        try:
            rect = driver.execute_script("return arguments[0].getBoundingClientRect();", el)
            cx = rect.get('left', 0) + rect.get('width', 0) / 2
            cy = rect.get('top', 0) + rect.get('height', 0) / 2
            try:
                top_html = driver.execute_script(
                    "let e = document.elementFromPoint(arguments[0], arguments[1]); return e ? e.outerHTML : null;",
                    cx, cy
                )
                print("Element au point central (peut être un overlay) :", (top_html or "")[:400])
            except Exception:
                pass

            ActionChains(driver).move_to_element_with_offset(el, rect.get('width', 1)/2 - 1, rect.get('height', 1)/2 - 1).click().perform()
            print("move_to_element_with_offset click reussi")
            return True
        except Exception as e:
            print("move_to_element_with_offset echoue :", repr(e))

        # 5) tenter les ancêtres (monte jusqu'à 6 niveaux)
        try:
            ancestors = driver.execute_script("""
                let el = arguments[0];
                let res = [];
                let a = el.parentElement;
                while(a && res.length < 6){
                  res.push(a);
                  a = a.parentElement;
                }
                return res;
            """, el)
            for i, anc in enumerate(ancestors, start=1):
                try:
                    print(f"Essai clic sur ancêtre niveau {i}")
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", anc)
                except Exception:
                    pass
                try:
                    anc.click()
                    print(f"click() sur ancêtre niveau {i} reussi")
                    return True
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", anc)
                        print(f"JS click sur ancêtre niveau {i} reussi")
                        return True
                    except Exception as e:
                        print(f"clic sur ancêtre niveau {i} echoue :", repr(e))
        except Exception as e:
            print("Erreur lors du parcours des ancêtres :", repr(e))

    # Si on arrive ici, aucun essai n'a marche
    print(f"Impossible de cliquer sur '{text}' après plusieurs tentatives — je sauvegarde un screenshot : {screenshot_path}")
    driver.save_screenshot(screenshot_path)
    raise Exception(f"Impossible de cliquer sur '{text}'. Voir {screenshot_path} et les outerHTML imprimes pour debug.")

    driver.execute_script("arguments[0].click();", alertes_btn)
    print("Bouton 'Alertes internes' clique (JS fallback)")