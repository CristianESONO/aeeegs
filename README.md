# AEEEGS - Project Setup Guide

Ce projet est une application web basée sur Flask pour l'Association des Estudiants Ecuatoguineanos au Sénégal.

## Configuration Rapide

### 1. Prérequis
- Python 3.10+
- pip (gestionnaire de paquets Python)

### 2. Installation
Clonez le dépôt ou téléchargez les fichiers, puis installez les dépendances :
```bash
pip install -r requirements.txt
```

### 3. Configuration de l'environnement
Copiez le fichier `.env.example` vers un nouveau fichier nommé `.env` :
```bash
cp .env.example .env
```
Éditez le fichier `.env` pour y ajouter vos propres configurations (clés secrètes, paramètres email, etc.).

### 4. Lancement de l'application
Pour démarrer le serveur de développement :
```bash
python app.py
```
L'application sera accessible sur `http://127.0.0.1:5000`.

## Fonctionnalités
- Gestion d'articles (Blog)
- Système de commentaires (avec réponses et likes)
- Dashboard Admin pour la gestion du contenu
- Formulaire de contact avec envoi d'email
- Support multi-catégories
