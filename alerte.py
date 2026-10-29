"""
Alertes erreurs de prix -> Discord
Lit le flux RSS des nouveaux deals Dealabs et envoie une alerte Discord pour
tout deal à -70 % ou plus (ou signalé comme erreur de prix), toutes catégories.
La tech (téléphones, PC, cartes graphiques...) est mise en avant.
Aucune dépendance : Python 3.9+ standard.
"""
import html
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

# ---------------------------------------------------------------- Réglages
REDUCTION_MIN = 70  # en %

FLUX = [
    "https://www.dealabs.com/rss/nouveaux",
]

# Surveiller toutes les catégories (True) ou seulement la tech (False)
TOUTES_CATEGORIES = True

# Catégories Dealabs considérées comme "tech"
CATEGORIES_TECH = {"high-tech", "informatique"}

# Mots-clés tech (pour les deals rangés dans une autre catégorie)
MOTS_TECH = [
    "smartphone", "téléphone", "telephone", "iphone", "galaxy", "pixel",
    "xiaomi", "oneplus", "ordinateur", "pc portable", "laptop", "macbook",
    "imac", "mac mini", "ultrabook", "chromebook", "carte graphique",
    "rtx", "gtx", "radeon", "rx 7", "rx 9", "geforce", "processeur",
    "ryzen", "intel core", "ssd", "écran pc", "moniteur", "ipad",
    "tablette", "pc gamer", "pc fixe",
]

# Mots qui signalent une erreur de prix probable -> alerte même sans %
MOTS_ERREUR = ["erreur de prix", "erreur", "bug de prix", "prix bug"]

FICHIER_VUS = Path(__file__).parent / "deja_vus.json"
MAX_VUS = 2000

# Données lues par l'appli (dossier docs/, publié avec GitHub Pages)
FICHIER_DEALS = Path(__file__).parent / "docs" / "deals.json"
MAX_DEALS = 300
# -------------------------------------------------------------------------

NS = {"pepper": "http://www.pepper.com/rss", "media": "http://search.yahoo.com/mrss/"}
UA = "Mozilla/5.0 (compatible; alertes-erreurs-de-prix/1.0)"


def prix_en_float(texte):
    if not texte:
        return None
    t = texte.replace("\u202f", "").replace("\xa0", "").replace(" ", "")
    t = t.replace("€", "").replace(",", ".")
    m = re.search(r"\d+(?:\.\d+)?", t)
    return float(m.group()) if m else None


def texte_brut(fragment_html):
    sans_balises = re.sub(r"<[^>]+>", " ", fragment_html or "")
    return re.sub(r"\s+", " ", html.unescape(sans_balises)).strip()


def trouver_reduction(texte, prix):
    """Renvoie la meilleure réduction trouvée (en %) ou None."""
    candidats = []

    # "-72%" / "-72 %" / "72 % de réduction"
    for m in re.finditer(r"-\s?(\d{2})\s?%", texte):
        candidats.append(int(m.group(1)))
    for m in re.finditer(r"(\d{2})\s?%\s*(?:de\s*)?(?:réduction|remise|reduc)", texte, re.I):
        candidats.append(int(m.group(1)))

    # Ancien prix explicite -> calcul
    if prix:
        motifs = [
            r"au lieu de\s*([\d\s.,]+)\s*€",
            r"prix\s*(?:conseillé|barré|habituel|de référence)[^\d]{0,25}([\d\s.,]+)\s*€",
            r"habituellement\s*([\d\s.,]+)\s*€",
            r"(?:avant|était)\s*à?\s*([\d\s.,]+)\s*€",
        ]
        for motif in motifs:
            for m in re.finditer(motif, texte, re.I):
                ancien = prix_en_float(m.group(1))
                if ancien and ancien > prix:
                    candidats.append(round((1 - prix / ancien) * 100))

    candidats = [c for c in candidats if 0 < c < 100]
    return max(candidats) if candidats else None


def est_tech(categorie, titre):
    if categorie.lower() in CATEGORIES_TECH:
        return True
    t = titre.lower()
    return any(mot in t for mot in MOTS_TECH)


def lire_flux(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def date_iso(texte):
    try:
        return parsedate_to_datetime(texte).astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def analyser(xml_bytes):
    racine = ET.fromstring(xml_bytes)
    for item in racine.iter("item"):
        marchand = item.find("pepper:merchant", NS)
        image = item.find("media:content", NS)
        yield {
            "id": (item.findtext("guid") or item.findtext("link") or "").strip(),
            "titre": (item.findtext("title") or "").strip(),
            "lien": (item.findtext("link") or "").strip(),
            "categorie": (item.findtext("category") or "").strip(),
            "marchand": marchand.get("name", "") if marchand is not None else "",
            "prix_txt": marchand.get("price", "") if marchand is not None else "",
            "description": texte_brut(item.findtext("description") or ""),
            "image": image.get("url") if image is not None else None,
            "date": date_iso(item.findtext("pubDate")),
        }


def infos_deal(deal):
    tech = est_tech(deal["categorie"], deal["titre"])
    prix = prix_en_float(deal["prix_txt"])
    texte = f'{deal["titre"]} {deal["description"]}'
    reduction = trouver_reduction(texte, prix)
    erreur = any(m in texte.lower() for m in MOTS_ERREUR)
    alerte = (tech or TOUTES_CATEGORIES) and (
        (reduction is not None and reduction >= REDUCTION_MIN) or erreur
    )
    return {"prix": prix, "reduction": reduction, "erreur": erreur, "tech": tech, "alerte": alerte}


def doit_alerter(deal):
    info = infos_deal(deal)
    return info if info["alerte"] else None


def fiche_appli(deal, info):
    """Version compacte d'un deal pour l'appli."""
    return {
        "id": deal["id"],
        "titre": deal["titre"],
        "lien": deal["lien"],
        "categorie": deal["categorie"],
        "marchand": deal["marchand"],
        "prix": deal["prix_txt"],
        "image": deal["image"],
        "date": deal["date"],
        "extrait": deal["description"][:220],
        "reduction": info["reduction"],
        "erreur": info["erreur"],
        "tech": info["tech"],
        "alerte": info["alerte"],
    }


def charger_deals_appli():
    try:
        return json.loads(FICHIER_DEALS.read_text()).get("deals", [])
    except Exception:
        return []


def sauver_deals_appli(deals):
    deals.sort(key=lambda d: d.get("date", ""), reverse=True)
    FICHIER_DEALS.parent.mkdir(parents=True, exist_ok=True)
    FICHIER_DEALS.write_text(json.dumps({
        "maj": datetime.now(timezone.utc).isoformat(),
        "deals": deals[:MAX_DEALS],
    }, ensure_ascii=False))


def envoyer_discord(webhook, deal, info):
    champs = []
    if deal["prix_txt"]:
        champs.append({"name": "Prix", "value": deal["prix_txt"], "inline": True})
    if info["reduction"]:
        champs.append({"name": "Réduction", "value": f'-{info["reduction"]} %', "inline": True})
    if deal["marchand"]:
        champs.append({"name": "Marchand", "value": deal["marchand"], "inline": True})

    if info["erreur"]:
        entete = "🚨 Erreur de prix probable" + (" (tech)" if info["tech"] else "")
    elif info["tech"]:
        entete = "🔥 Grosse réduction tech"
    else:
        entete = f'💸 Super deal • {deal["categorie"] or "autre"}'

    embed = {
        "title": deal["titre"][:250],
        "url": deal["lien"],
        "color": 0xE74C3C if info["erreur"] else (0xF39C12 if info["tech"] else 0x2ECC71),
        "fields": champs,
        "footer": {"text": f'Dealabs • {deal["categorie"]}'},
    }
    if deal["image"]:
        embed["thumbnail"] = {"url": deal["image"]}

    corps = json.dumps({"content": entete, "embeds": [embed]}).encode()
    req = urllib.request.Request(
        webhook, data=corps,
        headers={"Content-Type": "application/json", "User-Agent": UA},
    )
    urllib.request.urlopen(req, timeout=30)


def main():
    webhook = os.environ.get("DISCORD_WEBHOOK", "").strip()
    test = "--test" in sys.argv  # n'envoie rien, affiche seulement

    if not webhook and not test:
        sys.exit("ERREUR : le secret DISCORD_WEBHOOK est vide ou introuvable. Ajoute-le dans Settings > Secrets and variables > Actions > onglet Secrets > Repository secrets.")

    premier_lancement = not FICHIER_VUS.exists()
    vus = [] if premier_lancement else json.loads(FICHIER_VUS.read_text())
    deja = set(vus)

    deals_appli = charger_deals_appli()
    ids_appli = {d["id"] for d in deals_appli}

    alertes = 0
    for url in FLUX:
        try:
            deals = list(analyser(lire_flux(url)))
        except Exception as e:  # un flux en panne ne bloque pas les autres
            print(f"Flux illisible {url} : {e}")
            continue

        for deal in deals:
            if not deal["id"] or deal["id"] in deja:
                continue
            deja.add(deal["id"])
            vus.append(deal["id"])

            info = infos_deal(deal)
            if deal["id"] not in ids_appli:
                deals_appli.append(fiche_appli(deal, info))
                ids_appli.add(deal["id"])

            if premier_lancement:
                continue  # on mémorise sans spammer au 1er passage

            if info["alerte"]:
                alertes += 1
                print(f'ALERTE : {deal["titre"]} ({deal["prix_txt"]}, {info})')
                if not test:
                    envoyer_discord(webhook, deal, info)

    if not test:
        FICHIER_VUS.write_text(json.dumps(vus[-MAX_VUS:]))
        sauver_deals_appli(deals_appli)
    print(f"Terminé : {alertes} alerte(s)." + (" (1er lancement : deals mémorisés)" if premier_lancement else ""))


if __name__ == "__main__":
    main()
