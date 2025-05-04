#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
flowbytebeat_router.py - Router pour le module FlowByteBeat (scalping rapide)
"""

from fastapi import APIRouter, HTTPException, Query, Body, Path
from typing import Dict, Any, List, Optional
import logging
import time
import uuid
import config

# Importer le module FlowByteBeat
try:
    from flow_bytebeat import FlowByteBeat
    flow_bytebeat_instance = FlowByteBeat()
    flow_bytebeat_instance.start()
    module_available = True
except ImportError:
    flow_bytebeat_instance = None
    module_available = False

# Configuration du logger
logger = logging.getLogger("FlowByteBeatRouter")

# Création du router
router = APIRouter()

# Modèles de données (normalement dans models.py, simplifiés ici)
# Ces modèles seraient idéalement des classes Pydantic

@router.get("/status", tags=["FlowByteBeat"])
def get_status():
    """Vérification du statut du module FlowByteBeat"""
    if not module_available:
        raise HTTPException(status_code=503, detail="Module FlowByteBeat non disponible")
    
    return {
        "status": "active" if flow_bytebeat_instance.running else "inactive",
        "module": "FlowByteBeat",
        "version": "1.0.0",
        "mode": "sandbox" if config.MODE_SANDBOX else "production",
        "max_leverage": config.FLOWBYTEBEAT_MAX_LEVERAGE,
        "default_timeframe": config.FLOWBYTEBEAT_DEFAULT_TIMEFRAME
    }

@router.post("/trigger", tags=["FlowByteBeat"])
def trigger_scalping(
    symbol: str = Body(..., description="Symbole de trading (ex: BTC/USDT)"),
    exchange: str = Body("bybit", description="Échange (bybit ou kraken)"),
    direction: str = Body(..., description="Direction du trade (long ou short)"),
    size: float = Body(..., description="Taille de la position"),
    settings: Optional[Dict[str, Any]] = Body(None, description="Paramètres supplémentaires")
):
    """Déclenche une opération de scalping rapide"""
    if not module_available:
        raise HTTPException(status_code=503, detail="Module FlowByteBeat non disponible")
    
    # Valider les paramètres
    if direction not in ["long", "short"]:
        raise HTTPException(status_code=400, detail="Direction invalide, utiliser 'long' ou 'short'")
    
    if size <= 0:
        raise HTTPException(status_code=400, detail="La taille doit être positive")
    
    if exchange not in ["bybit", "kraken"]:
        raise HTTPException(status_code=400, detail="Échange non supporté, utiliser 'bybit' ou 'kraken'")
    
    # Préparer les données du trade
    operation_id = str(uuid.uuid4())
    trade_data = {
        "id": operation_id,
        "symbol": symbol,
        "exchange": exchange,
        "direction": direction,
        "size": size,
        "settings": settings or {},
        "timestamp": time.time()
    }
    
    # En mode sandbox, simuler seulement
    if config.MODE_SANDBOX:
        logger.info(f"Mode sandbox: simulation de l'opération {operation_id}")
        return {
            "operation_id": operation_id,
            "status": "simulated",
            "message": "Opération simulée en mode sandbox",
            "data": trade_data
        }
    
    # Créer un signal de trading
    try:
        # Normalement, nous utiliserions l'API du module
        # Ici, c'est simplifié pour l'exemple
        result = {
            "operation_id": operation_id,
            "status": "initiated",
            "message": f"Opération de scalping initiée pour {symbol}",
            "timestamp": time.time()
        }
        
        # Publication de l'événement via le bus d'événements
        if hasattr(flow_bytebeat_instance, "event_bus"):
            flow_bytebeat_instance.event_bus.publish("trade_signal", {
                "type": "scalp",
                "symbol": symbol,
                "direction": direction,
                "exchange": exchange,
                "size": size,
                "settings": settings,
                "operation_id": operation_id
            })
        
        return result
    except Exception as e:
        logger.error(f"Erreur lors du déclenchement du scalping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du déclenchement: {str(e)}")

@router.get("/trades", tags=["FlowByteBeat"])
def get_trades(
    status: Optional[str] = Query(None, description="Filtrer par statut (open, closed)"),
    symbol: Optional[str] = Query(None, description="Filtrer par symbole"),
    limit: int = Query(10, ge=1, le=100, description="Nombre maximum de trades à retourner")
):
    """Récupère les trades de scalping actifs ou récents"""
    if not module_available:
        raise HTTPException(status_code=503, detail="Module FlowByteBeat non disponible")
    
    # Accéder aux trades via l'instance du module
    active_trades = []
    
    # En mode sandbox, utiliser des données simulées
    if config.MODE_SANDBOX:
        # Générer des trades de test
        test_trades = [
            {
                "id": f"test-{i}",
                "symbol": "BTC/USDT" if i % 2 == 0 else "ETH/USDT",
                "direction": "long" if i % 2 == 0 else "short",
                "entry_price": 48000 + (i * 100) if i % 2 == 0 else 3200 + (i * 10),
                "size": 0.01 * (i + 1),
                "status": "open" if i < 3 else "closed",
                "profit": None if i < 3 else (i - 2) * 0.5,
                "entry_time": time.time() - (i * 600),
                "close_time": None if i < 3 else time.time() - (i * 300)
            }
            for i in range(min(10, limit))
        ]
        active_trades = test_trades
    else:
        # En production, utiliser les données réelles du module
        if hasattr(flow_bytebeat_instance, "active_trades"):
            active_trades = list(flow_bytebeat_instance.active_trades.values())
    
    # Appliquer les filtres
    if status:
        active_trades = [t for t in active_trades if t.get("status") == status]
    
    if symbol:
        active_trades = [t for t in active_trades if t.get("symbol") == symbol]
    
    # Limiter le nombre de résultats
    active_trades = active_trades[:limit]
    
    return {
        "trades": active_trades,
        "count": len(active_trades),
        "timestamp": time.time()
    }

@router.post("/close/{trade_id}", tags=["FlowByteBeat"])
def close_trade(
    trade_id: str = Path(..., description="ID du trade à fermer"),
    reason: str = Body("manual", description="Raison de la fermeture")
):
    """Ferme un trade de scalping actif"""
    if not module_available:
        raise HTTPException(status_code=503, detail="Module FlowByteBeat non disponible")
    
    # En mode sandbox, simuler la fermeture
    if config.MODE_SANDBOX:
        logger.info(f"Mode sandbox: simulation de la fermeture du trade {trade_id}")
        return {
            "trade_id": trade_id,
            "status": "closed",
            "message": "Trade fermé avec succès (simulé)",
            "reason": reason,
            "timestamp": time.time()
        }
    
    # En production, fermer le trade via le module
    try:
        # Vérifier si le trade existe
        if not hasattr(flow_bytebeat_instance, "active_trades") or trade_id not in flow_bytebeat_instance.active_trades:
            raise HTTPException(status_code=404, detail=f"Trade {trade_id} non trouvé")
        
        # Appeler la méthode de fermeture
        if hasattr(flow_bytebeat_instance, "_close_position"):
            flow_bytebeat_instance._close_position(trade_id, reason)
            
            return {
                "trade_id": trade_id,
                "status": "closed",
                "message": "Trade fermé avec succès",
                "reason": reason,
                "timestamp": time.time()
            }
        else:
            raise HTTPException(status_code=501, detail="Fermeture manuelle non implémentée")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la fermeture du trade {trade_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la fermeture: {str(e)}")

@router.get("/settings", tags=["FlowByteBeat"])
def get_settings():
    """Récupère les paramètres actuels du module FlowByteBeat"""
    if not module_available:
        raise HTTPException(status_code=503, detail="Module FlowByteBeat non disponible")
    
    # Récupérer la configuration du module
    settings = {}
    
    if hasattr(flow_bytebeat_instance, "config"):
        settings = flow_bytebeat_instance.config
    else:
        # Configuration par défaut si non disponible
        settings = {
            "exchanges": {
                "bybit": {
                    "enabled": True,
                    "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
                    "max_positions": 3,
                    "position_size_usd": 100,
                    "max_leverage": config.FLOWBYTEBEAT_MAX_LEVERAGE
                },
                "kraken": {
                    "enabled": True,
                    "symbols": ["BTC/USD", "ETH/USD", "XRP/USD"],
                    "max_positions": 2,
                    "position_size_usd": 100,
                    "max_leverage": 3
                }
            },
            "scalping": {
                "min_profit_percent": 0.12,
                "max_loss_percent": 0.15,
                "max_holding_time_seconds": 300,
                "min_volatility": 0.001,
                "max_spread_percent": 0.05,
                "cooldown_after_loss_seconds": 60
            }
        }
    
    return {
        "settings": settings,
        "timestamp": time.time()
    }

@router.post("/settings", tags=["FlowByteBeat"])
def update_settings(
    updates: Dict[str, Any] = Body(..., description="Mises à jour des paramètres")
):
    """Met à jour les paramètres du module FlowByteBeat"""
    if not module_available:
        raise HTTPException(status_code=503, detail="Module FlowByteBeat non disponible")
    
    # En mode sandbox, simuler la mise à jour
    if config.MODE_SANDBOX:
        logger.info(f"Mode sandbox: simulation de la mise à jour des paramètres")
        return {
            "status": "updated",
            "message": "Paramètres mis à jour avec succès (simulé)",
            "updates": updates,
            "timestamp": time.time()
        }
    
    # En production, mettre à jour via le module
    try:
        # Publier la mise à jour de configuration via le bus d'événements
        if hasattr(flow_bytebeat_instance, "event_bus"):
            flow_bytebeat_instance.event_bus.publish("scalping_config_update", {
                "section": "scalping",
                "updates": updates,
                "timestamp": time.time()
            })
            
            return {
                "status": "updated",
                "message": "Paramètres mis à jour avec succès",
                "updates": updates,
                "timestamp": time.time()
            }
        else:
            raise HTTPException(status_code=501, detail="Mise à jour de configuration non implémentée")
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des paramètres: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")
