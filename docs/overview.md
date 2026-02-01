# StudioBoard — Overview

StudioBoard est une application Django destinée à organiser des idées sous forme de Kanban.

## Concepts
- Board : espace de travail
- Colonne : étape du workflow
- Idée : carte avec Markdown, tags, impact
- Template : structure Markdown réutilisable

## Objectifs
- Simplicité
- Rapidité de capture
- Réutilisation des structures
- Hébergement léger (Raspberry Pi)

## Stack
- Django
- SQLite (initialement)
- Gunicorn + Nginx (prod)