from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from routers import flowbytebeat_router, flowsniper_router, flowupspin_router
from core.flow_validator import validate_all_modules
from core.flow_logs_manager import setup_logging
import config

# Configuration du logger
logger = setup_logging()

app = FastAPI(
    title="FlowGlobal API",
    description="API de trading algorithmique pour les marchés crypto",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Peut être ajusté pour la production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware d'authentification
async def verify_token(x_access_token: str = Header(...)):
    if x_access_token != config.ACCESS_TOKEN:
        logger.warning(f"Tentative d'accès avec un token invalide: {x_access_token[:5]}...")
        raise HTTPException(status_code=403, detail="Token d'accès invalide")
    return x_access_token

# Routers
app.include_router(
    flowbytebeat_router.router, 
    prefix="/flowbytebeat", 
    tags=["FlowByteBeat"],
    dependencies=[Depends(verify_token)]
)
app.include_router(
    flowsniper_router.router, 
    prefix="/flowsniper", 
    tags=["FlowSniper"],
    dependencies=[Depends(verify_token)]
)
app.include_router(
    flowupspin_router.router, 
    prefix="/flowupspin", 
    tags=["FlowUpSpin"],
    dependencies=[Depends(verify_token)]
)

@app.get("/", tags=["Root"])
def root():
    """Point d'entrée principal de l'API"""
    return {
        "message": "Bienvenue sur l'API FlowGlobal", 
        "documentation": "/docs", 
        "version": "1.0.0"
    }

@app.get("/status", tags=["System"])
def status():
    """Vérification du statut de l'API"""
    return {
        "status": "OK", 
        "version": "V1", 
        "sandbox": config.MODE_SANDBOX
    }

# Validation au démarrage
@app.on_event("startup")
def startup_event():
    """Événement de démarrage pour valider les modules"""
    logger.info("Démarrage de l'API FlowGlobal en mode " + 
                ("sandbox" if config.MODE_SANDBOX else "production"))
    validate_all_modules()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
