#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de logging pour l'application FlowGlobalApp
"""

import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name="flowglobal", level=logging.INFO):
    """
    Configure un logger avec sortie console adaptée pour Railway
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Éviter les doublons de handlers
    if logger.handlers:
        return logger
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler console (toujours disponible)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Environnement Railway utilise généralement stdout/stderr pour les logs
    # mais on essaie quand même de créer un fichier log si possible
    if os.environ.get("RAILWAY_ENVIRONMENT") != "production":
        try:
            # Handler fichier (rotating) - uniquement en local
            log_dir = os.environ.get("LOG_DIR", ".")
            file_handler = RotatingFileHandler(
                os.path.join(log_dir, 'flowglobal.log'),
                maxBytes=10485760,  # 10MB
                backupCount=2
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Impossible de créer le fichier log: {e}")
    
    return logger

def get_logger(name="flowglobal"):
    """
    Récupère une instance du logger
    """
    return logging.getLogger(name)
