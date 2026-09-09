# -*- coding: utf-8 -*-
"""
Détecteur de nouvelles offres de stage.

Fonctionnement :
  1. Pour chaque site défini dans config.py, télécharge la page et extrait
     la liste des annonces actuelles (identifiées par leur lien).
  2. Compare cette liste à celle sauvegardée lors du run précédent
     (fichier data/<site>.json).
  3. Toute nouvelle annonce déclenche une notification ntfy.
  4. Sauvegarde la nouvelle liste comme référence pour le prochain run.

Usage :
  python scraper.py            # un seul passage (à lancer via cron/tâche planifiée)
  python scraper.py --loop     # tourne en continu, avec pause entre chaque cycle
"""

import json
import os
import sys
import time
import argparse
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import SITES, NTFY_TOPIC, CHECK_INTERVAL_MINUTES

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def state_path(site_name: str) -> str:
    safe_name = site_name.lower().replace(" ", "_")
    return os.path.join(DATA_DIR, f"{safe_name}.json")


def load_previous_state(site_name: str) -> dict:
    path = state_path(site_name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(site_name: str, listings: dict) -> None:
    with open(state_path(site_name), "w", encoding="utf-8") as f:
        json.dump(listings, f, ensure_ascii=False, indent=2)


def fetch_listings(site: dict) -> dict:
    """
    Retourne un dict {identifiant_unique: {"title": ..., "available": bool|None}}
    des offres de stage actuellement présentes sur la page du site.

    "available" vaut None en mode "new_items" (non pertinent), et un booléen
    en mode "availability".
    """
    mode = site.get("mode", "new_items")

    resp = requests.get(site["url"], headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    items = soup.select(site["item_selector"])
    listings = {}

    location_filter = [kw.lower() for kw in site.get("location_filter_keywords", [])]

    for item in items:
        link_el = item.select_one(site["link_selector"])
        if not link_el or not link_el.get("href"):
            continue

        href = urljoin(site["url"], link_el["href"])

        if site.get("name_selector"):
            name_el = item.select_one(site["name_selector"])
            title = name_el.get_text(strip=True) if name_el else href
        else:
            title = link_el.get_text(strip=True) or href

        company_text = None
        if site.get("company_selector"):
            company_el = item.select_one(site["company_selector"])
            if company_el:
                company_text = company_el.get_text(strip=True)

        location_text = None
        if site.get("location_selector"):
            location_el = item.select_one(site["location_selector"])
            if location_el:
                location_text = location_el.get_text(strip=True)

        # Filtre localisation : si des mots-clés sont définis et qu'aucun ne
        # matche le texte de localisation (ou, à défaut, le texte complet de
        # l'item), on ignore cette entrée.
        if location_filter:
            haystack = (location_text or item.get_text(" ", strip=True)).lower()
            if not any(kw in haystack for kw in location_filter):
                continue

        available = None
        status_text = None
        price_text = None

        if mode == "availability":
            avail_type = site.get("availability_type", "img_src")
            avail_el = item.select_one(site.get("availability_selector", ""))

            if avail_type == "text":
                status_text = avail_el.get_text(strip=True) if avail_el else None
                positive_values = site.get("positive_values", [])
                available = status_text in positive_values
            else:
                available = True  # par défaut si on ne trouve pas l'indicateur
                if avail_el is not None:
                    marker = avail_el.get("src", "")
                    unavailable_kw = site.get("unavailable_keyword", "non_disponible")
                    available = unavailable_kw not in marker

            if site.get("price_selector"):
                price_el = item.select_one(site["price_selector"])
                if price_el:
                    price_text = price_el.get_text(strip=True)

        listings[href] = {
            "title": title,
            "available": available,
            "status": status_text,
            "price": price_text,
            "company": company_text,
            "location": location_text,
        }

    return listings


def send_notification(site_name: str, title: str, url: str) -> None:
    message = f"{title}\n{url}"
    try:
        requests.post(
            NTFY_TOPIC,
            data=message.encode("utf-8"),
            headers={
                "Title": f"Nouvelle offre - {site_name}".encode("utf-8"),
                "Priority": "high",
                "Tags": "house,bell",
            },
            timeout=10,
        )
    except requests.RequestException as e:
        print(f"[!] Échec envoi notif ntfy pour {site_name}: {e}")


def check_site(site: dict) -> None:
    name = site["name"]
    print(f"[*] Vérification : {name}")

    if site["item_selector"] == "TODO_A_COMPLETER":
        print(f"    -> sélecteur non configuré pour {name}, ignoré (voir config.py)")
        return

    try:
        current = fetch_listings(site)
    except Exception as e:
        print(f"    -> erreur lors du scraping de {name}: {e}")
        return

    if not current:
        print(f"    -> aucune annonce trouvée, vérifie item_selector pour {name}")
        return

    previous = load_previous_state(name)
    mode = site.get("mode", "new_items")

    if not previous:
        # Premier run : on enregistre l'état sans notifier (sinon spam au démarrage)
        print(f"    -> premier run pour {name}, {len(current)} entrée(s) enregistrée(s)")
    elif mode == "availability":
        notified = 0
        for listing_id, rec in current.items():
            prev_rec = previous.get(listing_id)
            was_available = bool(prev_rec and prev_rec.get("available"))
            is_available = bool(rec.get("available"))
            if is_available and not was_available:
                extra = []
                if rec.get("status"):
                    extra.append(rec["status"])
                if rec.get("price"):
                    extra.append(f"{rec['price']}€")
                suffix = f" ({', '.join(extra)})" if extra else ""
                full_title = f"{rec['title']}{suffix}"
                print(f"    -> DEVENU DISPONIBLE : {full_title}")
                send_notification(name, full_title, listing_id)
                notified += 1
        if notified == 0:
            print(f"    -> rien de nouveau ({len(current)} résidence(s) suivie(s))")
    else:
        new_ids = set(current) - set(previous)
        for listing_id in new_ids:
            rec = current[listing_id]
            extra = []
            if rec.get("company"):
                extra.append(rec["company"])
            if rec.get("location"):
                extra.append(rec["location"])
            suffix = f" — {' · '.join(extra)}" if extra else ""
            full_title = f"{rec['title']}{suffix}"
            print(f"    -> NOUVELLE ANNONCE : {full_title}")
            send_notification(name, full_title, listing_id)
        if not new_ids:
            print(f"    -> rien de nouveau ({len(current)} annonce(s) au total)")

    save_state(name, current)


def run_once() -> None:
    for site in SITES:
        check_site(site)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--loop", action="store_true",
        help="Tourne en continu au lieu d'un seul passage (utile en local, sinon préfère cron)"
    )
    args = parser.parse_args()

    if args.loop:
        interval_seconds = CHECK_INTERVAL_MINUTES * 60
        print(f"Boucle active, vérification toutes les {CHECK_INTERVAL_MINUTES} min. Ctrl+C pour arrêter.")
        while True:
            run_once()
            time.sleep(interval_seconds)
    else:
        run_once()


if __name__ == "__main__":
    main()
