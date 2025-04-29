#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'authentification pour l'application FlowGlobalApp
"""

from fastapi import HTTPException, Header, Depends
from config import settings
from utils.logger import get_logger

logger = get_logger()

async def verify_token(authorization: str = Header(None)):
    """
    Vérifie le token d'authentification
    
    Cette implémentation est très basique et devrait être améliorée
    avec JWT ou OAuth2 pour un environnement de production.
    """
    logger.info("Vérification du token d'authentification")
    
    if not authorization:
        logger.warning("Tentative d'accès sans token")
        raise HTTPException(status_code=401, detail="Token d'authentification manquant")
    
    # Exemple très simple - à remplacer par une vérification JWT appropriée
    # Le format attendu est "Bearer montoken"
    scheme, _, token = authorization.partition(" ")
    
    if scheme.lower() != "bearer":
        logger.warning(f"Schéma d'authentification invalide: {scheme}")
        raise HTTPException(
            status_code=401, 
            detail="Schéma d'authentification invalide, utiliser 'Bearer'"
        )
    
    # Vérification simpliste du token
    # En production, utilisez JWT ou un autre système sécurisé
    if token != settings.SECRET_KEY:
        logger.warning("Token d'authentification invalide")
        raise HTTPException(status_code=401, detail="Token d'authentification invalide")
    
    logger.info("Token d'authentification validé")
    return token
