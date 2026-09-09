# -*- coding: utf-8 -*-
"""
Configuration des sites de STAGE à surveiller.

Mode "new_items" : on notifie quand un NOUVEL identifiant (lien) apparaît
dans la liste — le cas normal pour des offres d'emploi/stage.

Champs communs :
  - url                     : URL de la page de recherche à scraper
  - item_selector           : sélecteur CSS du conteneur répété pour CHAQUE offre
  - link_selector            : sélecteur CSS (relatif à item_selector) du lien <a>
                                -> son href sert d'identifiant unique
  - name_selector             : sélecteur CSS du titre de l'offre
  - company_selector          : (optionnel) sélecteur CSS du nom de l'entreprise
  - location_selector         : (optionnel) sélecteur CSS du lieu affiché
  - location_filter_keywords  : (optionnel) liste de mots-clés ; si présente,
                                 seules les offres dont le lieu (ou le texte de
                                 l'item) contient un de ces mots-clés sont retenues

Astuce pour trouver ces sélecteurs : F12 sur la page > clic sur une offre
avec l'outil "inspecter" > repère la classe CSS/attribut qui se répète.
"""

import os

NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
if not NTFY_TOPIC:
    raise RuntimeError(
        "NTFY_TOPIC n'est pas défini. En local : mets-le en variable "
        "d'environnement. Sur GitHub Actions : ajoute un secret nommé "
        "NTFY_TOPIC dans Settings > Secrets and variables > Actions."
    )

SITES = [
    {
        "name": "WTTJ Stage Cyber",
        "url": "https://www.welcometothejungle.com/fr/jobs?query=cybersecurit%C3%A9&refinementList%5Boffices.country_code%5D%5B%5D=FR&refinementList%5Bcontract_type%5D%5B%5D=internship",
        "mode": "new_items",
        "item_selector": "div[class*='cursor-pointer'][class*='rounded-xl']",
        "link_selector": "a[href*='/jobs/']",
        "name_selector": "a[href*='/jobs/']",
        "company_selector": "p[class*='variant-body-lg-strong']",
        "location_selector": "[data-testid='job-card-tag-location']",
        "location_filter_keywords": ["Paris", "Île-de-France", "Ile-de-France"],
    },
    {
        "name": "HelloWork Stage Cyber",
        "url": "https://www.hellowork.com/fr-fr/emploi/recherche.html?k=cybersecurit%C3%A9&k_autocomplete=&l=%C3%8Ele-de-France&l_autocomplete=http%3A%2F%2Fwww.rj.com%2Fcommun%2Flocalite%2Fregion%2F11&st=relevance&c=Stage&cod=all&msa=0&ray=50&d=all",
        "mode": "new_items",
        "item_selector": "li[data-id-storage-item-id]",
        "link_selector": "a[data-cy='offerTitle']",
        "name_selector": "a[data-cy='offerTitle'] p.typo-l",
        "company_selector": "p.typo-s.inline",
        "location_selector": "[data-cy='localisationCard']",
        "location_filter_keywords": ["Paris", "Île-de-France", "Ile-de-France"],
    },
    {
        "name": "Stage.fr Cyber",
        "url": "https://www.stage.fr/jobs/?q=cybersecurit%C3%A9&l=%C3%8Ele-de-France%2C+France",
        "mode": "new_items",
        "item_selector": "article.listing-item",
        "link_selector": "div.listing-item__title a",
        "name_selector": "div.listing-item__title a",
        "company_selector": "span.listing-item__info--item-company",
        "location_selector": "span.listing-item__info--item-location",
        "location_filter_keywords": ["Paris", "Île-de-France", "Ile-de-France"],
    },
]

CHECK_INTERVAL_MINUTES = 15
