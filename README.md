# StudioBoard

Projet Django pour gerer des idees et les convertir en projets, avec categories et status.

## Demarrage rapide

1. Activer l'environnement virtuel :

```bash
source .venv/bin/activate
```

2. Installer les dependances :

```bash
pip install -r requirements.txt
```

3. Appliquer les migrations :

```bash
python manage.py migrate
```

4. Creer un compte admin (optionnel) :

```bash
python manage.py createsuperuser
```

5. Lancer le serveur :

```bash
python manage.py runserver 0.0.0.0:8000
```

Ensuite, ouvre `http://localhost:8000`.

## Production

1. Definis une cle secrete :

```bash
export DJANGO_SECRET_KEY="change-moi"
```

2. Collecte les assets statiques :

```bash
python manage.py collectstatic
```

3. Exemple de configuration `.env` :

```bash
DJANGO_ENV=production
DJANGO_SECRET_KEY=change-moi
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=studioboard.local,192.168.1.20
DJANGO_CSRF_TRUSTED_ORIGINS=https://studioboard.local

DJANGO_SECURE_SSL_REDIRECT=1
DJANGO_SESSION_COOKIE_SECURE=1
DJANGO_CSRF_COOKIE_SECURE=1
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=1
DJANGO_SECURE_HSTS_PRELOAD=1

DJANGO_FILE_UPLOAD_MAX_MEMORY_SIZE=26214400
DJANGO_DATA_UPLOAD_MAX_MEMORY_SIZE=26214400
```

## Notes

- La langue est en francais (LANGUAGE_CODE=fr-fr) et le fuseau horaire est Europe/Paris dans `studioboard/settings.py`.
- Les status sont adaptes au type (idee ou projet) et la conversion d'une idee en projet met a jour le status si besoin.
- Le dossier de projets pour l'explorateur est `BASE_DIR/projects` par defaut. Tu peux le modifier avec la variable d'environnement `STUDIOBOARD_PROJECTS_ROOT`.
- Pages utiles: `/systeme/` pour les infos Raspberry Pi, `/projets/` pour l'explorateur et l'import de projets.
- L'import de dossiers non zippes fonctionne via un navigateur desktop compatible (Chrome/Edge/Brave) avec `webkitdirectory`.
