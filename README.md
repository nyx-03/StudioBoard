# StudioBoard 🧠📋
**StudioBoard** est un **studio personnel de gestion d’idées et de projets** basé sur un **Kanban**.  
L’objectif : capturer une idée, la structurer rapidement (tags, impact, prochaine action), l’enrichir en **Markdown**, puis la faire évoluer dans un workflow clair.

➡️ Stack actuelle : **Django (API)** + **Next.js (UI)**, pensée pour être **auto‑hébergée** (Raspberry Pi, Linux, macOS).

---

## ✅ Fonctionnalités

### 🗂️ Boards & Kanban
- Multiples **boards** indépendants
- Colonnes configurables (workflow)
- Cartes d’idées avec :
  - titre
  - tags
  - impact
  - prochaine action
  - contenu Markdown
- **Drag & Drop persistant** :
  - intra‑colonne (reorder)
  - inter‑colonnes (move)

### ⚡ Quick Add intelligent
Ajout d’une idée depuis une seule ligne :
```text
Refonte landing page #marketing @Backlog !impact=3
```
- `#tag` → tags
- `@Colonne` → colonne cible (si reconnue)
- `!impact=3` → impact
- reste du texte → titre

### ✍️ Markdown avec preview
- Édition Markdown
- Preview automatique
- Rendu sécurisé (XSS‑safe)

### 🧠 Templates réutilisables
- Créer un template depuis une idée
- Appliquer un template à la création ou en édition

### 🔐 Auth & sécurité
- Auth via session Django
- CSRF correctement géré (important en réseau local / mobile)

---

## 🏗️ Architecture

### Backend — Django (API)
- Python **3.14**
- Django **5.x**
- API découplée, factorisée (views/services/serializers/parsing)

### Frontend — Next.js (UI)
- Next.js **16.x** (App Router)
- React + hooks
- CSS Modules
- DnD basé sur `@dnd-kit`
- UX responsive (desktop + mobile)

---

## 📁 Structure du repo

```text
StudioBoard/
├── client/                      # Frontend Next.js
│   ├── src/
│   │   ├── app/                 # Routes (App Router)
│   │   ├── features/kanban/     # Feature Kanban (components + hooks)
│   │   ├── hooks/               # Auth, guards, etc.
│   │   └── lib/                 # API client
│   └── next.config.mjs
│
├── server/                      # Backend Django
│   ├── board/
│   │   ├── api/                 # API (urls, views_*, services, serializers)
│   │   ├── migrations/
│   │   └── models.py
│   ├── config/
│   └── manage.py
│
├── docs/                        # Documentation (déploiement, décisions)
├── scripts/                     # Scripts utilitaires (backup, deploy, etc.)
└── README.md
```

---

## 🚀 Démarrage rapide (local)

### Prérequis
- **Python 3.14**
- **Node.js ≥ 20**
- `pip` / `venv`
- `npm`

---

### 1) Backend (Django)
```bash
cd server
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API dispo sur :
- `http://127.0.0.1:8000/`

---

### 2) Frontend (Next.js)
```bash
cd client
npm install
npm run dev
```

UI dispo sur :
- `http://localhost:3000/`

---

## 🔧 Configuration (environnement)

### Django
- Variables (selon ton setup) : `.env` côté serveur (non versionné)
- En local, tu peux rester en SQLite (par défaut)

### Next.js
- `.env.local` (non versionné)
- Le client appelle l’API via `/api/...` (proxy / rewrites côté Next)

---

## 🧪 Tests & qualité

Backend :
```bash
cd server
source .venv/bin/activate
python manage.py test
```

Frontend :
```bash
cd client
npm run build
```

---

## 🧭 Roadmap (prochaines étapes)
- [ ] Undo (annuler un move / reorder)
- [ ] Recherche globale + filtres (tags/impact)
- [ ] Historique d’activité d’une idée
- [ ] Raccourcis clavier
- [ ] Tests automatisés (services Django + UI critical path)
- [ ] Optimisations perf (memoization, batching, cache API)
- [ ] Déploiement Raspberry Pi documenté (Gunicorn + Nginx + systemd)

---

## 🌍 Déploiement (objectif)
StudioBoard est pensé pour être **auto‑hébergé**, notamment sur Raspberry Pi.

Stack cible :
- Gunicorn
- Nginx
- systemd
- SQLite ou PostgreSQL

La doc associée sera maintenue dans `docs/`.

---

## 📜 Licence
MIT

---

## 👤 Auteur
Développé par **Ludo**.

> StudioBoard : un espace de réflexion structuré, pas juste un Kanban.