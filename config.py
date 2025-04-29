#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration pour l'application FlowGlobalApp
"""

import os
from dotenv import load_dotenv

# Chargement des variables d'environnement (si .env existe)
try:
    load_dotenv()
except Exception as e:
    # Simplement logger l'erreur et continuer - Railway utilise des variables d'environnement directement
    print(f"Note: Fichier .env non chargé. Utilisation des variables d'environnement système. {e}")

class Settings:
    """
    Configurations de l'application
    """
    # Informations de base
    APP_NAME: str = "FlowGlobalApp"
    API_V1_STR: str = ""
    
    # Sécurité
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "default_secret_key_change_in_production")
    
    # Configuration Binance (à compléter)
    BINANCE_API_KEY: str = os.environ.get("BINANCE_API_KEY", "")
    BINANCE_API_SECRET: str = os.environ.get("BINANCE_API_SECRET", "")
    
    # Environnement
    DEBUG: bool = os.environ.get("DEBUG", "False").lower() == "true"
    ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "development")
    
    # Railway spécifique
    IS_RAILWAY: bool = os.environ.get("RAILWAY_ENVIRONMENT") is not None

# Instance des paramètres
settings = Settings()
