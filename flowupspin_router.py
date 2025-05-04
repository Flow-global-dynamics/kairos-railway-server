#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
flowupspin_router.py - Router pour le module FlowUpSpin (stratégie de suivi de tendance)
"""

from fastapi import APIRouter, HTTPException, Query, Body, Path
from typing import Dict, Any, List, Optional
import logging
import time
import uuid
import config

# Configuration du logger
logger = logging.getLogger("FlowUpSpinRouter")

# Création du router
router = APIRouter()

# Définition des routes

@router.get("/status", tags=["FlowUpSpin"])
def get_status():
    """Vérification du statut du module FlowUpSpin"""
    return {
        "status": "active",
        "module": "FlowUpSpin",
        "version": "1.0.0",
        "mode": "sandbox" if config.MODE_SANDBOX else "production",
        "default_trade_size": config.FLOWUPSPIN_DEFAULT_TRADE_SIZE,
        "smart_exit": config.FLOWUPSPIN_SMART_EXIT
    }

@router.post("/trigger", tags=["FlowUpSpin"])
def trigger_upspin(
    symbol: str = Body(..., description="Symbole de trading (ex: BTC/USDT)"),
    exchange: str = Body("bybit", description="Échange (bybit ou kraken)"),
    direction: str = Body(..., description="Direction du trade (long ou short)"),
    size: float = Body(..., description="Taille de la position"),
    timeframe: str = Body("1h", description="Unité de temps (15m, 1h, 4h, 1d)"),
    strategy: str = Body("trend_following", description="Stratégie à utiliser"),
    settings: Optional[Dict[str, Any]] = Body(None, description="Paramètres supplémentaires")
):
    """Déclenche une stratégie de suivi de tendance UpSpin"""
    # Valider les paramètres
    if direction not in ["long", "short"]:
        raise HTTPException(status_code=400, detail="Direction invalide, utiliser 'long' ou 'short'")
    
    if size <= 0:
        raise HTTPException(status_code=400, detail="La taille doit être positive")
    
    if exchange not in ["bybit", "kraken"]:
        raise HTTPException(status_code=400, detail="Échange non supporté, utiliser 'bybit' ou 'kraken'")
    
    if timeframe not in ["15m", "1h", "4h", "1d"]:
        raise HTTPException(status_code=400, detail="Timeframe invalide, utiliser '15m', '1h', '4h' ou '1d'")
    
    valid_strategies = ["trend_following", "breakout", "pullback", "momentum"]
    if strategy not in valid_strategies:
        raise HTTPException(status_code=400, detail=f"Stratégie invalide, utiliser l'une de: {', '.join(valid_strategies)}")
    
    # Préparer les données du trade
    operation_id = str(uuid.uuid4())
    trade_data = {
        "id": operation_id,
        "symbol": symbol,
        "exchange": exchange,
        "direction": direction,
        "size": size,
        "timeframe": timeframe,
        "strategy": strategy,
        "settings": settings or {},
        "timestamp": time.time()
    }
    
    # En mode sandbox, simuler seulement
    if config.MODE_SANDBOX:
        logger.info(f"Mode sandbox: simulation de l'opération UpSpin {operation_id}")
        return {
            "operation_id": operation_id,
            "status": "simulated",
            "message": "Opération UpSpin simulée en mode sandbox",
            "data": trade_data
        }
    
    # Déclencher la stratégie
    try:
        # Normalement, nous utiliserions une instance d'un module FlowUpSpin
        # Ici, c'est simplifié pour l'exemple
        result = {
            "operation_id": operation_id,
            "status": "started",
            "message": f"Stratégie UpSpin {strategy} démarrée pour {symbol} ({timeframe})",
            "timestamp": time.time()
        }
        
        # Simulation de la publication d'un événement
        logger.info(f"Événement 'upspin_strategy_started' publié pour {operation_id}")
        
        return result
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de la stratégie UpSpin: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors du démarrage: {str(e)}")

@router.get("/strategies", tags=["FlowUpSpin"])
def get_strategies():
    """Récupère les stratégies disponibles dans le module UpSpin"""
    strategies = [
        {
            "id": "trend_following",
            "name": "Trend Following",
            "description": "Stratégie de suivi de tendance utilisant les moyennes mobiles et le RSI",
            "recommended_timeframes": ["1h", "4h", "1d"],
            "parameters": [
                {"name": "ma_fast", "type": "int", "default": 10, "description": "Période de la moyenne mobile rapide"},
                {"name": "ma_slow", "type": "int", "default": 30, "description": "Période de la moyenne mobile lente"},
                {"name": "rsi_period", "type": "int", "default": 14, "description": "Période du RSI"}
            ]
        },
        {
            "id": "breakout",
            "name": "Breakout",
            "description": "Stratégie de breakout sur les niveaux de support/résistance",
            "recommended_timeframes": ["15m", "1h", "4h"],
            "parameters": [
                {"name": "lookback_periods", "type": "int", "default": 20, "description": "Nombre de périodes pour identifier les niveaux"},
                {"name": "confirmation_candles", "type": "int", "default": 2, "description": "Bougies de confirmation requises"},
                {"name": "volume_increase", "type": "float", "default": 1.5, "description": "Augmentation de volume minimale pour confirmation"}
            ]
        },
        {
            "id": "pullback",
            "name": "Pullback",
            "description": "Stratégie de pullback en tendance",
            "recommended_timeframes": ["1h", "4h"],
            "parameters": [
                {"name": "trend_ma", "type": "int", "default": 50, "description": "MA pour la direction de la tendance"},
                {"name": "pullback_threshold", "type": "float", "default": 0.382, "description": "Niveau de retracement minimal"},
                {"name": "max_pullback", "type": "float", "default": 0.618, "description": "Niveau de retracement maximal"}
            ]
        },
        {
            "id": "momentum",
            "name": "Momentum",
            "description": "Stratégie basée sur le momentum (MACD, RSI)",
            "recommended_timeframes": ["15m", "1h"],
            "parameters": [
                {"name": "macd_fast", "type": "int", "default": 12, "description": "Période rapide du MACD"},
                {"name": "macd_slow", "type": "int", "default": 26, "description": "Période lente du MACD"},
                {"name": "macd_signal", "type": "int", "default": 9, "description": "Période du signal MACD"}
            ]
        }
    ]
    
    return {
        "strategies": strategies,
        "count": len(strategies),
        "timestamp": time.time()
    }

@router.get("/active", tags=["FlowUpSpin"])
def get_active_strategies(
    symbol: Optional[str] = Query(None, description="Filtrer par symbole"),
    strategy: Optional[str] = Query(None, description="Filtrer par type de stratégie"),
    limit: int = Query(10, ge=1, le=100, description="Nombre maximum de stratégies à retourner")
):
    """Récupère les stratégies UpSpin actives"""
    # Simuler des données pour l'exemple
    strategies = ["trend_following", "breakout", "pullback", "momentum"]
    test_strategies = [
        {
            "id": f"upspin-{i}",
            "symbol": "BTC/USDT" if i % 3 == 0 else ("ETH/USDT" if i % 3 == 1 else "SOL/USDT"),
            "direction": "long" if i % 2 == 0 else "short",
            "strategy": strategies[i % 4],
            "timeframe": ["15m", "1h", "4h", "1d"][i % 4],
            "size": 0.01 * (i + 1),
            "entry_price": 48000 + (i * 100) if i % 3 == 0 else (3200 + (i * 10) if i % 3 == 1 else 120 + i),
            "current_price": 48500 + (i * 80) if i % 3 == 0 else (3300 + (i * 8) if i % 3 == 1 else 125 + i),
            "profit_percent": 1.5 if i % 2 == 0 else -0.8,
            "status": "active",
            "start_time": time.time() - (i * 3600 * 24),
            "duration_days": i + 1
        }
        for i in range(min(15, limit))
    ]
    
    # Appliquer les filtres
    filtered_strategies = test_strategies
    
    if symbol:
        filtered_strategies = [s for s in filtered_strategies if s.get("symbol") == symbol]
    
    if strategy:
        filtered_strategies = [s for s in filtered_strategies if s.get("strategy") == strategy]
    
    # Limiter le nombre de résultats
    filtered_strategies = filtered_strategies[:limit]
    
    return {
        "strategies": filtered_strategies,
        "count": len(filtered_strategies),
        "timestamp": time.time()
    }

@router.post("/stop/{strategy_id}", tags=["FlowUpSpin"])
def stop_strategy(
    strategy_id: str = Path(..., description="ID de la stratégie à arrêter"),
    reason: str = Body("manual", description="Raison de l'arrêt")
):
    """Arrête une stratégie UpSpin active"""
    # En mode sandbox, simuler l'arrêt
    if config.MODE_SANDBOX:
        logger.info(f"Mode sandbox: simulation de l'arrêt de la stratégie {strategy_id}")
        return {
            "strategy_id": strategy_id,
            "status": "stopped",
            "message": "Stratégie arrêtée avec succès (simulé)",
            "reason": reason,
            "timestamp": time.time()
        }
    
    # En production, arrêter la stratégie via le module
    try:
        # Normalement, nous vérifierions si la stratégie existe, puis l'arrêterions
        # Ici, c'est simplifié pour l'exemple
        return {
            "strategy_id": strategy_id,
            "status": "stopped",
            "message": "Stratégie arrêtée avec succès",
            "reason": reason,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt de la stratégie {strategy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'arrêt: {str(e)}")

@router.get("/performance", tags=["FlowUpSpin"])
def get_performance(
    days: int = Query(30, ge=1, le=365, description="Nombre de jours à analyser"),
    symbol: Optional[str] = Query(None, description="Filtrer par symbole"),
    strategy: Optional[str] = Query(None, description="Filtrer par type de stratégie")
):
    """Récupère les performances des stratégies UpSpin"""
    # Simuler des données pour l'exemple
    strategies = ["trend_following", "breakout", "pullback", "momentum"]
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    
    # Performances globales
    global_perf = {
        "trades_count": 124,
        "win_rate": 0.68,
        "profit_factor": 1.85,
        "average_profit": 2.3,
        "average_loss": -1.2,
        "max_drawdown": 8.5,
        "sharpe_ratio": 1.4,
        "average_holding_time_hours": 38
    }
    
    # Performances par stratégie
    strategy_perf = {
        strategy_name: {
            "trades_count": 20 + (i * 10),
            "win_rate": 0.6 + (i * 0.05),
            "profit_factor": 1.5 + (i * 0.1),
            "average_profit": 2.0 + (i * 0.2),
            "average_loss": -1.0 - (i * 0.1),
            "total_profit_percent": 15 + (i * 5)
        }
        for i, strategy_name in enumerate(strategies)
    }
    
    # Performances par symbole
    symbol_perf = {
        symbol_name: {
            "trades_count": 30 + (i * 15),
            "win_rate": 0.65 + (i * 0.03),
            "profit_factor": 1.7 + (i * 0.15),
            "average_profit": 2.2 + (i * 0.3),
            "average_loss": -1.1 - (i * 0.15),
            "total_profit_percent": 18 + (i * 7)
        }
        for i, symbol_name in enumerate(symbols)
    }
    
    # Appliquer les filtres
    if strategy:
        if strategy in strategy_perf:
            strategy_perf = {strategy: strategy_perf[strategy]}
        else:
            strategy_perf = {}
    
    if symbol:
        if symbol in symbol_perf:
            symbol_perf = {symbol: symbol_perf[symbol]}
        else:
            symbol_perf = {}
    
    return {
        "period_days": days,
        "global": global_perf,
        "by_strategy": strategy_perf,
        "by_symbol": symbol_perf,
        "timestamp": time.time()
    }

@router.get("/settings", tags=["FlowUpSpin"])
def get_settings():
    """Récupère les paramètres actuels du module FlowUpSpin"""
    # Configuration par défaut
    settings = {
        "trade_size": {
            "default": config.FLOWUPSPIN_DEFAULT_TRADE_SIZE,
            "auto_sizing": True,
            "max_risk_percent": 2.0
        },
        "risk_management": {
            "stop_loss_atr_multiplier": 1.5,
            "take_profit_ratio": 2.0,  # Ratio risque/récompense
            "trailing_stop": True,
            "smart_exit": config.FLOWUPSPIN_SMART_EXIT
        },
        "backtesting": {
            "lookback_days": 90,
            "auto_optimize": True,
            "performance_metric": "sharpe_ratio"
        },
        "execution": {
            "slippage_tolerance": 0.1,
            "retry_attempts": 3,
            "max_spread_percent": 0.5
        }
    }
    
    return {
        "settings": settings,
        "timestamp": time.time()
    }

@router.post("/settings", tags=["FlowUpSpin"])
def update_settings(
    updates: Dict[str, Any] = Body(..., description="Mises à jour des paramètres")
):
    """Met à jour les paramètres du module FlowUpSpin"""
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

@router.post("/backtest", tags=["FlowUpSpin"])
def run_backtest(
    symbol: str = Body(..., description="Symbole de trading (ex: BTC/USDT)"),
    strategy: str = Body(..., description="Stratégie à tester"),
    timeframe: str = Body("1h", description="Unité de temps"),
    start_date: str = Body(..., description="Date de début (YYYY-MM-DD)"),
    end_date: Optional[str] = Body(None, description="Date de fin (YYYY-MM-DD, défaut: aujourd'hui)"),
    parameters: Optional[Dict[str, Any]] = Body(None, description="Paramètres spécifiques à la stratégie")
):
    """Lance un backtest pour une stratégie UpSpin"""
    # Valider les paramètres
    valid_strategies = ["trend_following", "breakout", "pullback", "momentum"]
    if strategy not in valid_strategies:
        raise HTTPException(status_code=400, detail=f"Stratégie invalide, utiliser l'une de: {', '.join(valid_strategies)}")
    
    # Simulation du démarrage d'un backtest
    backtest_id = f"backtest-{uuid.uuid4()}"
    
    return {
        "backtest_id": backtest_id,
        "status": "started",
        "message": f"Backtest lancé pour {symbol} avec la stratégie {strategy}",
        "parameters": {
            "symbol": symbol,
            "strategy": strategy,
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date or time.strftime("%Y-%m-%d"),
            "custom_parameters": parameters or {}
        },
        "estimated_completion_seconds": 30,
        "timestamp": time.time()
    }
