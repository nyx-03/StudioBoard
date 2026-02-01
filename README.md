# BlueprintStudio

Studio personnel de suivi d'idées, projets et modules.

## Lancer le projet
cd server
source .venv/bin/activate
python manage.py runserver

# StudioBoard 🧠📋

![Python](https://img.shields.io/badge/Python-3.14-blue.svg)
![Django](https://img.shields.io/badge/Django-5.x-success.svg)
![Status](https://img.shields.io/badge/Status-Active%20Development-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20%7C%20Linux%20%7C%20macOS-informational)

**StudioBoard** est une application Django de type *studio personnel* permettant de capturer, organiser et structurer des idées sous forme de **Kanban**, avec support avancé du **Markdown**, des **templates réutilisables**, et une **navigation multi-board intelligente**.

---

## ✨ Fonctionnalités principales

### 🗂️ Boards & Kanban
- Multiples **boards indépendants**
- Colonnes personnalisables (workflow)
- Cartes d’idées avec :
  - titre
  - tags
  - impact
  - next action
  - contenu Markdown

### 🧠 Templates Markdown
- Créer un template depuis une idée existante
- Appliquer un template à la création ou à l’édition
- Templates globaux, réutilisables dans tous les boards

### ✍️ Markdown avancé
- Édition Markdown
- **Preview live automatique** (rendu serveur sécurisé)
- Support :
  - code blocks
  - tables
  - listes
  - citations
  - liens sécurisés (XSS-safe)

### ⚡ Quick Add
Ajouter une idée rapidement via une seule ligne :
```
Refonte page d’accueil #marketing @Backlog !impact=3
```

### 🧭 Navigation intelligente
- **Board courant** mémorisé automatiquement
- Sélecteur de board dans le header
- Accès rapide au Kanban et aux Templates

### 🏠 Page d’accueil
- Présentation du projet
- Guide d’utilisation
- Quick Add cheat-sheet
- Affichage des **3 dernières idées créées**

---

## 🛠️ Stack technique

- **Backend** : Django
- **Langage** : Python 3.14
- **Base de données** : SQLite (par défaut)
- **Frontend** : Django Templates + CSS moderne
- **Markdown** : `markdown` + `bleach` (sécurisé)
- **Déploiement cible** :
  - Raspberry Pi
  - Gunicorn + Nginx
- **IDE recommandé** : PyCharm

---

## 📁 Structure du projet

```
StudioBoard/
├── docs/               # Documentation projet
├── scripts/            # Scripts utilitaires (init, deploy, backup…)
├── server/
│   ├── board/          # App principale
│   │   ├── templates/
│   │   ├── static/
│   │   ├── views.py
│   │   └── models.py
│   ├── config/         # Configuration Django
│   ├── manage.py
│   └── db.sqlite3
├── .gitignore
└── README.md
```

---

## 🚀 Installation (environnement local)

### Pré-requis
- Python **3.14**
- `pip`
- `venv`

### Installation
```bash
cd server
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

### Lancer le serveur
```bash
python manage.py runserver
```

- Application : http://127.0.0.1:8000/
- Admin : http://127.0.0.1:8000/admin/

---

## 🧪 État du projet

- ✔️ Fonctionnel
- 🚧 En développement actif
- 🔒 Sécurisé (Markdown XSS-safe)
- 🧩 Architecture prête pour :
  - Django + HTMX
  - Django + Next.js (API)

---

## 🧭 Roadmap

- [ ] Sélecteur de board avancé
- [ ] Archivage des idées
- [ ] Duplication d’idées
- [ ] Export Markdown / PDF
- [ ] Auth multi-utilisateur
- [ ] Frontend Next.js (optionnel)

---

## 🌍 Déploiement

StudioBoard est conçu pour être **auto-hébergé**, notamment sur un **Raspberry Pi**.

Stack cible :
- Gunicorn
- Nginx
- systemd
- SQLite ou PostgreSQL

> Une documentation dédiée sera ajoutée dans `docs/deployment.md`.

---

## 📜 Licence

Ce projet est distribué sous licence **MIT**.  
Tu es libre de l’utiliser, le modifier et l’héberger.

---

## 👤 Auteur

Développé par **Ludo**  
Projet personnel orienté productivité, structuration d’idées et workflows créatifs.

---

> *StudioBoard est un studio, pas juste un Kanban.*