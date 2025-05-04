# FlowGlobal Kairos V2 – GitHub Ready

Ce dépôt contient la version stable du backend FlowGlobalDynamics™ Kairos V2.
Prêt à être déployé sur Railway via GitHub.

## Structure

- `main.py` – point d’entrée FastAPI
- `Procfile` – pour Railway (web: python main.py)
- `requirements.txt` – dépendances
- `config.py` – activation des modules IA (True/False)
- Modules IA dans le même dossier

## Déploiement

1. Cloner le repo GitHub avec GitHub Desktop
2. Remplacer le contenu par les fichiers de ce dossier
3. Commit + Push
4. Railway détecte `Procfile` → déploiement automatique
