#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
flow_logs_manager.py - Module de gestion des logs pour FlowGlobalDynamics™
"""

import logging
import os
import time
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
import config

def setup_logging(logger_name="FlowGlobal", log_level=None, log_file=None):
    """
    Configure le système de logging pour FlowGlobalDynamics™
    
    Args:
        logger_name: Nom du logger (par défaut: "FlowGlobal")
        log_level: Niveau de log (par défaut: utilise la configuration)
        log_file: Chemin du fichier de log (par défaut: utilise la configuration)
        
    Returns:
        Logger configuré
    """
    # Utiliser les valeurs de configuration par défaut si non spécifiées
    if log_level is None:
        log_level = config.LOG_LEVEL
    
    if log_file is None:
        log_file = config.LOG_FILE_PATH
    
    # Créer le répertoire de logs si nécessaire
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Convertir le niveau de log de texte en constante logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configurer le formatteur de logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configurer le logger principal
    logger = logging.getLogger(logger_name)
    logger.setLevel(numeric_level)
    
    # Éviter les gestionnaires de logs en double
    if not logger.handlers:
        # Ajouter un gestionnaire pour la console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Ajouter un gestionnaire pour le fichier (avec rotation)
        if log_file:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10 Mo
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    # Configurer également le logger Flask/FastAPI si nécessaire
    api_logger = logging.getLogger("uvicorn")
    api_logger.setLevel(numeric_level)
    
    logger.info(f"Système de logging initialisé - Niveau: {log_level}, Fichier: {log_file}")
    return logger

def log_event(logger, event_type, data=None, level="INFO"):
    """
    Enregistre un événement structuré dans les logs
    
    Args:
        logger: Logger à utiliser
        event_type: Type d'événement
        data: Données associées à l'événement
        level: Niveau de log (INFO, WARNING, ERROR, CRITICAL)
    """
    event = {
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
        "data": data or {}
    }
    
    # Convertir l'événement en JSON
    event_json = json.dumps(event)
    
    # Enregistrer avec le niveau approprié
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(f"EVENT: {event_json}")

def log_trade(logger, trade_data, operation="NEW"):
    """
    Enregistre un trade dans les logs
    
    Args:
        logger: Logger à utiliser
        trade_data: Données du trade
        operation: Type d'opération (NEW, UPDATE, CLOSE)
    """
    log_event(
        logger,
        f"TRADE_{operation}",
        trade_data,
        "INFO"
    )

def log_error(logger, error_type, error_message, context=None):
    """
    Enregistre une erreur dans les logs
    
    Args:
        logger: Logger à utiliser
        error_type: Type d'erreur
        error_message: Message d'erreur
        context: Contexte supplémentaire
    """
    error_data = {
        "error_type": error_type,
        "error_message": error_message,
        "context": context or {}
    }
    
    log_event(
        logger,
        "ERROR",
        error_data,
        "ERROR"
    )

def log_api_request(logger, method, endpoint, params=None, status_code=None, response_time=None):
    """
    Enregistre une requête API dans les logs
    
    Args:
        logger: Logger à utiliser
        method: Méthode HTTP
        endpoint: Point de terminaison de l'API
        params: Paramètres de la requête
        status_code: Code de statut de la réponse
        response_time: Temps de réponse en ms
    """
    request_data = {
        "method": method,
        "endpoint": endpoint,
        "params": params,
        "status_code": status_code,
        "response_time": response_time
    }
    
    log_event(
        logger,
        "API_REQUEST",
        request_data,
        "INFO"
    )

if __name__ == "__main__":
    # Test de la configuration des logs
    logger = setup_logging()
    logger.info("Test de logging")
    logger.warning("Test d'avertissement")
    logger.error("Test d'erreur")
    
    # Test des fonctions de logging
    log_event(logger, "TEST_EVENT", {"test": "data"})
    log_trade(logger, {"symbol": "BTC/USDT", "side": "BUY", "amount": 0.01})
    log_error(logger, "TEST_ERROR", "Ceci est un test d'erreur")
    log_api_request(logger, "GET", "/api/status", status_code=200, response_time=42)
