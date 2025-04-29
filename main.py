#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Application principale FastAPI pour FlowGlobalApp
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routers.flowglobal_router import router as flowglobal_router
from utils.logger import setup_logger
from config import settings

# Configuration de l'application
app = FastAPI(
    title="FlowGlobalApp API",
    description="Backend API pour l'application FlowGlobalApp",
    version="0.1.0"
)

# Configuration CORS optimisée pour Railway
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À remplacer par les domaines spécifiques en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration du logger
logger = setup_logger()

# Inclusion des routers
app.include_router(flowglobal_router, prefix="")

@app.get("/")
async def root():
    logger.info("Requête sur la route racine")
    return {"message": "Bienvenue sur l'API FlowGlobalApp"}

if __name__ == "__main__":
    # Récupération du port depuis la variable d'environnement (pour Railway)
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Démarrage du serveur FlowGlobalApp sur le port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
