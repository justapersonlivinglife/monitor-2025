# Détecteur d'offres de stage → ntfy

Projet indépendant du détecteur de logement, même architecture (GitHub Actions + ntfy).

## Mise en place rapide

1. Crée un **nouveau topic ntfy** dédié (différent de celui du logement), et abonne-toi dedans dans l'app.
2. Crée un **nouveau dépôt GitHub** (public de préférence, pour ne pas être limité en minutes Actions).
3. Uploade tous ces fichiers (sauf le dossier `data/`, il se remplira tout seul).
4. Ajoute un secret `NTFY_TOPIC` (Settings > Secrets and variables > Actions) avec l'URL du nouveau topic.
5. Crée un nouveau Personal Access Token (fine-grained, scope Actions: read/write, limité à ce dépôt).
6. Crée un cronjob sur cron-job.org qui appelle :
   `https://api.github.com/repos/TON_USER/TON_REPO/actions/workflows/scraper.yml/dispatches`
   (méthode POST, headers Authorization/Accept/Content-Type, body `{"ref":"main"}`)
   — exactement la même manip que pour le projet logement.
7. Lance un `Run workflow` manuel pour vérifier que tout tourne.

## Ajouter APEC plus tard

APEC charge son contenu en JavaScript, donc `requests` + `BeautifulSoup` ne suffisent pas.
Il faudra ajouter Playwright (navigateur headless) au projet — à faire dans un second temps.
