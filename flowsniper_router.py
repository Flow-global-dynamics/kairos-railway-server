#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
flowsniper_router.py - Router pour le module FlowSniper (entrées précises sur niveaux clés)
"""

from fastapi import APIRouter, HTTPException, Query, Body, Path
from typing import Dict, Any, List, Optional
import logging
import time
import uuid
import config

# Configuration du logger
logger = logging.getLogger("FlowSniperRouter")

# Création du router
router = APIRouter()

# Définition des routes

@router.get("/status", tags=["FlowSniper"])
def get_status():
    """Vérification du statut du module FlowSniper"""
    return {
        "status": "active",
        "module": "FlowSniper",
        "version": "1.0.0",
        "mode": "sandbox" if config.MODE_SANDBOX else "production",
        "max_entries": config.FLOWSNIPER_MAX_ENTRIES,
        "default_slippage": config.FLOWSNIPER_DEFAULT_SLIPPAGE
    }

@router.post("/trigger", tags=["FlowSniper"])
def trigger_sniper(
    symbol: str = Body(..., description="Symbole de trading (ex: BTC/USDT)"),
    exchange: str = Body("bybit", description="Échange (bybit ou kraken)"),
    direction: str = Body(..., description="Direction du trade (long ou short)"),
    entry_price: float = Body(..., description="Prix d'entrée ciblé"),
    stop_loss: float = Body(..., description="Niveau de stop loss"),
    take_profit: float = Body(..., description="Niveau de prise de profit"),
    size: float = Body(..., description="Taille de la position"),
    timeout_hours: float = Body(24, description="Délai d'expiration en heures"),
    settings: Optional[Dict[str, Any]] = Body(None, description="Paramètres supplémentaires")
):
    """Déclenche une opération de sniper (ordre limit à un niveau clé)"""
    # Valider les paramètres
    if direction not in ["long", "short"]:
        raise HTTPException(status_code=400, detail="Direction invalide, utiliser 'long' ou 'short'")
    
    if size <= 0:
        raise HTTPException(status_code=400, detail="La taille doit être positive")
    
    if exchange not in ["bybit", "kraken"]:
        raise HTTPException(status_code=400, detail="Échange non supporté, utiliser 'bybit' ou 'kraken'")
    
    # Valider les prix en fonction de la direction
    if direction == "long":
        if stop_loss >= entry_price:
            raise HTTPException(status_code=400, detail="Pour un long, le stop loss doit être inférieur au prix d'entrée")
        if take_profit <= entry_price:
            raise HTTPException(status_code=400, detail="Pour un long, le take profit doit être supérieur au prix d'entrée")
    else:  # short
        if stop_loss <= entry_price:
            raise HTTPException(status_code=400, detail="Pour un short, le stop loss doit être supérieur au prix d'entrée")
        if take_profit >= entry_price:
            raise HTTPException(status_code=400, detail="Pour un short, le take profit doit être inférieur au prix d'entrée")
    
    # Préparer les données du trade
    operation_id = str(uuid.uuid4())
    trade_data = {
        "id": operation_id,
        "symbol": symbol,
        "exchange": exchange,
        "direction": direction,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "size": size,
        "expires_at": time.time() + (timeout_hours * 3600),
        "settings": settings or {},
        "timestamp": time.time()
    }
    
    # En mode sandbox, simuler seulement
    if config.MODE_SANDBOX:
        logger.info(f"Mode sandbox: simulation de l'opération sniper {operation_id}")
        return {
            "operation_id": operation_id,
            "status": "simulated",
            "message": "Opération sniper simulée en mode sandbox",
            "data": trade_data
        }
    
    # Créer un ordre sniper
    try:
        # Normalement, nous utiliserions une instance d'un module FlowSniper
        # Ici, c'est simplifié pour l'exemple
        result = {
            "operation_id": operation_id,
            "status": "scheduled",
            "message": f"Ordre sniper planifié pour {symbol} à {entry_price}",
            "expiration_timestamp": trade_data["expires_at"],
            "timestamp": time.time()
        }
        
        # Simulation de la publication d'un événement
        logger.info(f"Événement 'sniper_order_created' publié pour {operation_id}")
        
        return result
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'ordre sniper: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")

@router.get("/orders", tags=["FlowSniper"])
def get_sniper_orders(
    status: Optional[str] = Query(None, description="Filtrer par statut (pending, filled, expired, cancelled)"),
    symbol: Optional[str] = Query(None, description="Filtrer par symbole"),
    limit: int = Query(10, ge=1, le=100, description="Nombre maximum d'ordres à retourner")
):
    """Récupère les ordres sniper actifs ou récents"""
    # Simuler des données pour l'exemple
    statuses = ["pending", "filled", "expired", "cancelled"]
    test_orders = [
        {
            "id": f"sniper-{i}",
            "symbol": "BTC/USDT" if i % 2 == 0 else "ETH/USDT",
            "direction": "long" if i % 2 == 0 else "short",
            "entry_price": 48000 + (i * 100) if i % 2 == 0 else 3200 + (i * 10),
            "stop_loss": 47500 - (i * 50) if i % 2 == 0 else 3300 + (i * 5),
            "take_profit": 49000 + (i * 200) if i % 2 == 0 else 3000 - (i * 20),
            "size": 0.01 * (i + 1),
            "status": statuses[i % 4],
            "created_at": time.time() - (i * 3600),
            "filled_at": time.time() - (i * 1800) if i % 4 == 1 else None,
            "expires_at": time.time() + (24 * 3600) if i % 4 == 0 else time.time() - (i * 1800)
        }
        for i in range(min(20, limit))
    ]
    
    # Appliquer les filtres
    filtered_orders = test_orders
    
    if status:
        filtered_orders = [o for o in filtered_orders if o.get("status") == status]
    
    if symbol:
        filtered_orders = [o for o in filtered_orders if o.get("symbol") == symbol]
    
    # Limiter le nombre de résultats
    filtered_orders = filtered_orders[:limit]
    
    return {
        "orders": filtered_orders,
        "count": len(filtered_orders),
        "timestamp": time.time()
    }

@router.post("/cancel/{order_id}", tags=["FlowSniper"])
def cancel_order(
    order_id: str = Path(..., description="ID de l'ordre à annuler"),
    reason: str = Body("manual", description="Raison de l'annulation")
):
    """Annule un ordre sniper actif"""
    # En mode sandbox, simuler l'annulation
    if config.MODE_SANDBOX:
        logger.info(f"Mode sandbox: simulation de l'annulation de l'ordre {order_id}")
        return {
            "order_id": order_id,
            "status": "cancelled",
            "message": "Ordre annulé avec succès (simulé)",
            "reason": reason,
            "timestamp": time.time()
        }
    
    # En production, annuler l'ordre via le module
    try:
        # Normalement, nous vérifierions si l'ordre existe, puis l'annulerions
        # Ici, c'est simplifié pour l'exemple
        return {
            "order_id": order_id,
            "status": "cancelled",
            "message": "Ordre annulé avec succès",
            "reason": reason,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation de l'ordre {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'annulation: {str(e)}")

@router.get("/levels/{symbol}", tags=["FlowSniper"])
def get_key_levels(
    symbol: str = Path(..., description="Symbole pour lequel récupérer les niveaux clés"),
    timeframe: str = Query("1h", description="Unité de temps (1m, 5m, 15m, 1h, 4h, 1d)")
):
    """Récupère les niveaux clés (support/résistance) pour un symbole"""
    # Valider les paramètres
    valid_timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
    if timeframe not in valid_timeframes:
        raise HTTPException(status_code=400, detail=f"Timeframe invalide, utiliser l'un de: {', '.join(valid_timeframes)}")
    
    # Simuler des niveaux clés
    if symbol.startswith("BTC"):
        support_levels = [47500, 46800, 45500, 44000, 42500]
        resistance_levels = [48500, 49200, 50000, 52000, 55000]
    elif symbol.startswith("ETH"):
        support_levels = [3150, 3050, 2900, 2750, 2500]
        resistance_levels = [3250, 3400, 3600, 3800, 4000]
    else:
        support_levels = [100, 95, 90, 85, 80]
        resistance_levels = [105, 110, 115, 120, 125]
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "support_levels": support_levels,
        "resistance_levels": resistance_levels,
        "fibonacci_levels": {
            "0": support_levels[0],
            "0.236": support_levels[0] + (resistance_levels[0] - support_levels[0]) * 0.236,
            "0.382": support_levels[0] + (resistance_levels[0] - support_levels[0]) * 0.382,
            "0.5": support_levels[0] + (resistance_levels[0] - support_levels[0]) * 0.5,
            "0.618": support_levels[0] + (resistance_levels[0] - support_levels[0]) * 0.618,
            "0.786": support_levels[0] + (resistance_levels[0] - support_levels[0]) * 0.786,
            "1": resistance_levels[0]
        },
        "pivot_points": {
            "r3": resistance_levels[0] + 50,
            "r2": resistance_levels[0] + 25,
            "r1": resistance_levels[0],
            "pivot": (support_levels[0] + resistance_levels[0]) / 2,
            "s1": support_levels[0],
            "s2": support_levels[0] - 25,
            "s3": support_levels[0] - 50
        },
        "timestamp": time.time()
    }

@router.get("/settings", tags=["FlowSniper"])
def get_settings():
    """Récupère les paramètres actuels du module FlowSniper"""
    # Configuration par défaut
    settings = {
        "default_timeframe": "1h",
        "max_active_orders": config.FLOWSNIPER_MAX_ENTRIES,
        "default_timeout_hours": 24,
        "default_slippage": config.FLOWSNIPER_DEFAULT_SLIPPAGE,
        "risk_management": {
            "max_risk_per_trade": 0.02,  # 2% du capital
            "trailing_stop_enabled": True,
            "auto_adjust_entries": True
        },
        "level_detection": {
            "sensitivity": 0.8,
            "confirmation_candles": 3,
            "min_bounce_count": 2
        }
    }
    
    return {
        "settings": settings,
        "timestamp": time.time()
    }

@router.post("/settings", tags=["FlowSniper"])
def update_settings(
    updates: Dict[str, Any] = Body(..., description="Mises à jour des paramètres")
):
    """Met à jour les paramètres du module FlowSniper"""
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
        logger.info(f"Mise à jour des paramètres: {updates}")
        
        return {
            "status": "updated",
            "message": "Paramètres mis à jour avec succès",
            "updates": updates,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des paramètres: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")
