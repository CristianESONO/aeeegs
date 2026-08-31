# AEEEGS — Plateforme Web Officielle

[![Site Web](https://img.shields.io/badge/Site_Web-aeeegs.com-blue?style=for-the-badge&logo=googlechrome)](https://aeeegs.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-black?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon_Cloud-blue?style=for-the-badge&logo=postgresql)](https://neon.tech/)
[![Render](https://img.shields.io/badge/Hosted_on-Render-informational?style=for-the-badge&logo=render)](https://render.com/)

Plateforme web officielle de l'**Association des Étudiants Équato-guinéens au Sénégal (AEEEGS)**. Ce site permet de publier les actualités de l'association, de présenter la structure organisationnelle de la directive, et de favoriser les échanges au sein de la communauté étudiante.

🌐 **URL de Production :** [https://aeeegs.com/](https://aeeegs.com/)

---

## 🚀 Fonctionnalités Principales

- 📰 **Gestion d'Articles & Blog :** Publication d'actualités classées par catégories, gestion des médias, système d'interactions (likes) et commentaires imbriqués (réponses aux commentaires).
- 👔 **Organigramme & Directive Dynamique :** Consultation du bureau exécutif actuel et historique par année académique et par département.
- 🌍 **Système Multilingue (i18n) :** Traduction instantanée en **Espagnol (ES)**, **Français (FR)** et **Anglais (EN)** avec sélecteur de langue interactif et moteur de traduction dynamique.
- 🔐 **Panel d'Administration sécurisé :** Espace d'administration complet pour créer, modifier et supprimer des articles, des catégories, des mandats directifs, des membres du bureau et des informations de contact.
- ✉️ **Formulaire de Contact & Emailing :** Envoi automatique de messages aux administrateurs via `Flask-Mail` (SMTP).
- 🎨 **Design Moderne & Responsive :** Interface fluide en *Glassmorphism*, adaptée aux mobiles, tablettes et ordinateurs.

---

## 🛠️ Stack Technique

- **Backend :** Python 3.10+, Flask, SQLAlchemy, Flask-Migrate, Flask-Mail, Gunicorn
- **Base de données :** 
  - **Production :** PostgreSQL (Hébergé sur Neon.tech)
  - **Développement :** SQLite (Local)
- **Frontend :** Jinja2 Templates, HTML5, CSS3 Vanilla (Glassmorphism), JavaScript (ES6+), Bootstrap 5
- **Déploiement & Cloud :** Render (Web Service), UptimeRobot (Monitoring Keep-Alive 24/7)

---

## ⚙️ Configuration & Installation Locale

### 1. Prérequis
- Python 3.10 ou supérieur
- Git

### 2. Installation
Clonez le dépôt puis installez les dépendances :
```bash
git clone https://github.com/CristianESONO/aeeegs.git
cd aeeegs
pip install -r requirements.txt
```

### 3. Variables d'Environnement
Copiez le fichier `.env.example` vers `.env` et ajustez vos paramètres :
```bash
cp .env.example .env
```
Fichier `.env` :
```env
SECRET_KEY=votre_cle_secrete
DATABASE_URL=sqlite:///instance/site.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=votre_mot_de_passe
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre_email@gmail.com
MAIL_PASSWORD=votre_mot_de_passe_application
```

### 4. Lancement de l'Application
```bash
python app.py
```
L'application sera disponible sur `http://127.0.0.1:5000`.

---

## 🌐 Déploiement en Production (Render + Neon)

1. **Base de données :** Déployée sur [Neon.tech](https://neon.tech/) (PostgreSQL Serverless).
2. **Hébergement Web :** Déployé sur [Render.com](https://render.com/) avec le point d'entrée défini dans le `Procfile` :
   ```text
   web: python init_db.py && gunicorn app:app
   ```
3. **Maintien en Éveil (Keep-Alive) :** Surveillé via [UptimeRobot](https://uptimerobot.com/) (ping HTTP toutes les 5 minutes sur `https://aeeegs.com/`).

---

## 📄 Licence & Crédits

Projet développé pour l'**Association des Étudiants Équato-guinéens au Sénégal (AEEEGS)**.  
Tous droits réservés © 2026.
