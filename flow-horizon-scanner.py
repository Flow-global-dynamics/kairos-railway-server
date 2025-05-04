#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowHorizonScanner.py - Module de scan d'horizon pour FlowGlobalDynamics™
"""

import logging
import time
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Import local
try:
    from flow_eventbus import get_event_bus
except ImportError:
    # Support mode hors ligne
    class DummyEventBus:
        def publish(self, *args, **kwargs): pass
        def subscribe(self, *args, **kwargs): pass
        def unsubscribe(self, *args, **kwargs): pass
    
    def get_event_bus():
        return DummyEventBus()

class FlowHorizonScanner:
    """
    Scanner d'horizon pour détecter les opportunités émergentes et les tendances de marché
    """
    
    def __init__(self):
        """Initialisation du FlowHorizonScanner"""
        self.running = False
        self.threads = {}
        self.logger = self._setup_logger()
        self.event_bus = get_event_bus()
        self.config = self._load_configuration()
        
        # État du scanner
        self.scan_data = {
            "trends": {},           # Tendances détectées
            "opportunities": {},    # Opportunités émergentes
            "correlations": {},     # Corrélations entre actifs
            "market_regime": {},    # Régime de marché actuel
            "alerts": []           # Alertes importantes
        }
        
        self.last_scan = {
            "quick": 0,
            "deep": 0,
            "correlation_matrix": 0
        }
        
        # Données historiques pour l'analyse
        self.historical_data = {}
        
    def _setup_logger(self):
        """Configuration du logger"""
        logger = logging.getLogger("FlowHorizonScanner")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Charge la configuration du scanner
        
        Returns:
            Configuration du scanner
        """
        # Configuration par défaut
        default_config = {
            "scan_intervals": {
                "quick_scan_seconds": 300,      # 5 minutes
                "deep_scan_seconds": 3600,      # 1 heure
                "correlation_scan_seconds": 1800 # 30 minutes
            },
            "market_data": {
                "timeframes": ["1d", "4h", "1h"],
                "lookback_days": 30,
                "min_data_points": 100
            },
            "detection_thresholds": {
                "trend_strength_min": 0.3,
                "opportunity_strength_min": 0.5,
                "correlation_min": 0.7,
                "volatility_threshold": 0.2
            },
            "asset_categories": {
                "crypto": ["BTC", "ETH", "BNB", "SOL", "ADA", "XRP"],
                "forex": ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"],
                "indices": ["SPX", "NDX", "DJI", "DAX"]
            },
            "analysis": {
                "ml_enabled": False,  # Machine Learning activé
                "sentiment_analysis": True,
                "volume_analysis": True,
                "cross_asset_analysis": True
            },
            "alert_levels": {
                "low_threshold": 0.3,
                "medium_threshold": 0.6,
                "high_threshold": 0.8
            }
        }
        
        try:
            # Tenter de charger depuis un fichier
            # with open("horizon_scanner_config.json", "r") as f:
            #     return json.load(f)
            return default_config
        except Exception as e:
            self.logger.warning(f"Impossible de charger la configuration: {str(e)}. Utilisation des valeurs par défaut.")
            return default_config
    
    def start(self):
        """Démarrage du scanner d'horizon"""
        if self.running:
            self.logger.warning("FlowHorizonScanner est déjà en cours d'exécution")
            return
            
        self.running = True
        
        # Démarrage des threads de scan
        self._start_scan_threads()
        
        self._register_events()
        self.logger.info("FlowHorizonScanner démarré")
        
    def stop(self):
        """Arrêt du scanner d'horizon"""
        if not self.running:
            self.logger.warning("FlowHorizonScanner n'est pas en cours d'exécution")
            return
            
        self.running = False
        
        # Arrêt des threads de scan
        for thread_name, thread in self.threads.items():
            if thread and thread.is_alive():
                thread.join(timeout=2.0)
                self.logger.debug(f"Thread {thread_name} arrêté")
        
        self._unregister_events()
        self.logger.info("FlowHorizonScanner arrêté")
    
    def _start_scan_threads(self):
        """Démarre les threads de scan"""
        # Thread de scan rapide
        self.threads["quick_scan"] = threading.Thread(
            target=self._quick_scan_loop, 
            daemon=True
        )
        self.threads["quick_scan"].start()
        
        # Thread de scan approfondi
        self.threads["deep_scan"] = threading.Thread(
            target=self._deep_scan_loop, 
            daemon=True
        )
        self.threads["deep_scan"].start()
        
        # Thread d'analyse de corrélation
        self.threads["correlation_scan"] = threading.Thread(
            target=self._correlation_scan_loop, 
            daemon=True
        )
        self.threads["correlation_scan"].start()
        
        # Thread de détection d'opportunités
        self.threads["opportunity_detector"] = threading.Thread(
            target=self._opportunity_detector_loop, 
            daemon=True
        )
        self.threads["opportunity_detector"].start()
    
    def _register_events(self):
        """Enregistrement des abonnements aux événements"""
        self.event_bus.subscribe("market_data_update", self._handle_market_data)
        self.event_bus.subscribe("horizon_scan_request", self._handle_scan_request)
        self.event_bus.subscribe("market_patterns_detected", self._handle_market_patterns)
        self.event_bus.subscribe("trade_result", self._handle_trade_result)
    
    def _unregister_events(self):
        """Désenregistrement des abonnements aux événements"""
        self.event_bus.unsubscribe("market_data_update", self._handle_market_data)
        self.event_bus.unsubscribe("horizon_scan_request", self._handle_scan_request)
        self.event_bus.unsubscribe("market_patterns_detected", self._handle_market_patterns)
        self.event_bus.unsubscribe("trade_result", self._handle_trade_result)
    
    def _quick_scan_loop(self):
        """Boucle de scan rapide"""
        while self.running:
            try:
                current_time = time.time()
                
                # Vérifier si un scan rapide est nécessaire
                if current_time - self.last_scan["quick"] > self.config["scan_intervals"]["quick_scan_seconds"]:
                    self._perform_quick_scan()
                    self.last_scan["quick"] = current_time
                
                time.sleep(60)  # Vérification périodique
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de scan rapide: {str(e)}")
                time.sleep(60)
    
    def _deep_scan_loop(self):
        """Boucle de scan approfondi"""
        while self.running:
            try:
                current_time = time.time()
                
                # Vérifier si un scan approfondi est nécessaire
                if current_time - self.last_scan["deep"] > self.config["scan_intervals"]["deep_scan_seconds"]:
                    self._perform_deep_scan()
                    self.last_scan["deep"] = current_time
                
                time.sleep(300)  # Vérification toutes les 5 minutes
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de scan approfondi: {str(e)}")
                time.sleep(300)
    
    def _correlation_scan_loop(self):
        """Boucle d'analyse de corrélation"""
        while self.running:
            try:
                current_time = time.time()
                
                # Vérifier si une analyse de corrélation est nécessaire
                if current_time - self.last_scan["correlation_matrix"] > self.config["scan_intervals"]["correlation_scan_seconds"]:
                    self._perform_correlation_analysis()
                    self.last_scan["correlation_matrix"] = current_time
                
                time.sleep(180)  # Vérification toutes les 3 minutes
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle d'analyse de corrélation: {str(e)}")
                time.sleep(180)
    
    def _opportunity_detector_loop(self):
        """Boucle de détection d'opportunités"""
        while self.running:
            try:
                # Détecter de nouvelles opportunités
                self._detect_emerging_opportunities()
                
                # Analyser le régime de marché actuel
                self._analyze_market_regime()
                
                time.sleep(120)  # Vérification toutes les 2 minutes
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de détection d'opportunités: {str(e)}")
                time.sleep(120)
    
    def _perform_quick_scan(self):
        """Effectue un scan rapide des tendances émergentes"""
        self.logger.debug("Exécution d'un scan rapide...")
        
        new_trends = {}
        alerts = []
        
        # Analyser chaque catégorie d'actifs
        for category, assets in self.config["asset_categories"].items():
            new_trends[category] = []
            
            for asset in assets:
                if asset in self.historical_data and len(self.historical_data[asset]) >= 20:
                    # Analyser la tendance récente
                    trend_strength = self._analyze_short_term_trend(asset)
                    
                    if trend_strength > self.config["detection_thresholds"]["trend_strength_min"]:
                        new_trends[category].append({
                            "asset": asset,
                            "strength": trend_strength,
                            "direction": "bullish" if trend_strength > 0 else "bearish",
                            "timeframe": "short",
                            "confidence": abs(trend_strength)
                        })
                        
                        # Créer une alerte si la tendance est forte
                        if abs(trend_strength) > self.config["alert_levels"]["medium_threshold"]:
                            alerts.append({
                                "type": "trend_emergence",
                                "asset": asset,
                                "category": category,
                                "strength": trend_strength,
                                "timestamp": time.time()
                            })
        
        # Mettre à jour les données de scan
        self.scan_data["trends"].update(new_trends)
        self.scan_data["alerts"].extend(alerts)
        
        # Publier les résultats
        self.event_bus.publish("horizon_scan_quick", {
            "trends": new_trends,
            "alerts": alerts,
            "timestamp": time.time()
        })
    
    def _perform_deep_scan(self):
        """Effectue un scan approfondi du marché"""
        self.logger.info("Exécution d'un scan approfondi...")
        
        deep_analysis = {
            "long_term_trends": {},
            "structural_changes": [],
            "emerging_themes": [],
            "risk_assessment": {}
        }
        
        # Analyser les tendances à long terme
        for category, assets in self.config["asset_categories"].items():
            deep_analysis["long_term_trends"][category] = {}
            
            for asset in assets:
                if asset in self.historical_data:
                    # Analyse des tendances multiples timeframes
                    multi_tf_analysis = self._analyze_multi_timeframe(asset)
                    deep_analysis["long_term_trends"][category][asset] = multi_tf_analysis
        
        # Détecter les changements structurels
        structural_changes = self._detect_structural_changes()
        deep_analysis["structural_changes"] = structural_changes
        
        # Identifier les thèmes émergents
        emerging_themes = self._identify_emerging_themes()
        deep_analysis["emerging_themes"] = emerging_themes
        
        # Évaluation des risques
        risk_assessment = self._perform_risk_assessment()
        deep_analysis["risk_assessment"] = risk_assessment
        
        # Publier les résultats
        self.event_bus.publish("horizon_scan_deep", {
            "analysis": deep_analysis,
            "timestamp": time.time()
        })
    
    def _perform_correlation_analysis(self):
        """Effectue une analyse de corrélation entre actifs"""
        self.logger.debug("Analyse de corrélation en cours...")
        
        correlations = {}
        
        # Calculer les corrélations entre catégories
        categories = list(self.config["asset_categories"].keys())
        for i in range(len(categories)):
            for j in range(i + 1, len(categories)):
                cat1, cat2 = categories[i], categories[j]
                correlation = self._calculate_cross_category_correlation(cat1, cat2)
                
                if abs(correlation) > self.config["detection_thresholds"]["correlation_min"]:
                    correlations[f"{cat1}_{cat2}"] = {
                        "value": correlation,
                        "strength": "strong" if abs(correlation) > 0.8 else "moderate",
                        "timestamp": time.time()
                    }
        
        # Calculer les corrélations intra-catégorie
        for category, assets in self.config["asset_categories"].items():
            if len(assets) >= 2:
                intra_correlations = self._calculate_intra_category_correlations(assets)
                correlations[f"{category}_internal"] = intra_correlations
        
        # Mettre à jour les données de corrélation
        self.scan_data["correlations"] = correlations
        
        # Publier les résultats
        self.event_bus.publish("correlation_update", {
            "correlations": correlations,
            "timestamp": time.time()
        })
    
    def _detect_emerging_opportunities(self):
        """Détecte les opportunités émergentes"""
        opportunities = []
        
        # Analyser chaque actif pour des opportunités
        for asset, data in self.historical_data.items():
            if len(data) >= self.config["market_data"]["min_data_points"]:
                # Détecter les opportunités basées sur différents facteurs
                opp = self._evaluate_opportunity(asset, data)
                
                if opp and opp["strength"] > self.config["detection_thresholds"]["opportunity_strength_min"]:
                    opportunities.append(opp)
        
        # Trier les opportunités par force
        opportunities.sort(key=lambda x: x["strength"], reverse=True)
        
        # Mettre à jour les données d'opportunités
        self.scan_data["opportunities"] = {
            "current": opportunities[:10],  # Top 10
            "timestamp": time.time()
        }
        
        # Publier les opportunités
        if opportunities:
            self.event_bus.publish("horizon_opportunities", {
                "opportunities": opportunities[:5],  # Top 5 pour publication
                "timestamp": time.time()
            })
    
    def _analyze_market_regime(self):
        """Analyse le régime de marché actuel"""
        regime_data = {
            "volatility_state": self._assess_market_volatility(),
            "trend_state": self._assess_market_trend(),
            "correlation_state": self._assess_correlation_regime(),
            "risk_state": self._assess_risk_environment()
        }
        
        # Déterminer le régime global
        overall_regime = self._determine_overall_regime(regime_data)
        
        # Mettre à jour les données de régime
        self.scan_data["market_regime"] = {
            "regime": overall_regime,
            "components": regime_data,
            "confidence": self._calculate_regime_confidence(regime_data),
            "timestamp": time.time()
        }
        
        # Publier le régime de marché
        self.event_bus.publish("market_regime_update", {
            "regime": overall_regime,
            "confidence": self.scan_data["market_regime"]["confidence"],
            "timestamp": time.time()
        })
    
    def _analyze_short_term_trend(self, asset: str) -> float:
        """
        Analyse la tendance à court terme d'un actif
        
        Args:
            asset: Actif à analyser
            
        Returns:
            Force de la tendance (positif = haussier, négatif = baissier)
        """
        if asset not in self.historical_data or len(self.historical_data[asset]) < 20:
            return 0.0
            
        # Récupérer les 20 dernières données
        recent_data = self.historical_data[asset][-20:]
        
        # Calculer la tendance simple (pente)
        x = list(range(len(recent_data)))
        y = [d["close"] for d in recent_data]
        
        # Régression linéaire simple
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(a * b for a, b in zip(x, y))
        sum_x2 = sum(a * a for a in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Normaliser la pente
        normalized_slope = slope / (sum_y / n)
        
        return normalized_slope
    
    def _analyze_multi_timeframe(self, asset: str) -> Dict[str, Any]:
        """
        Analyse multi-timeframe d'un actif
        
        Args:
            asset: Actif à analyser
            
        Returns:
            Analyse multi-timeframe
        """
        analysis = {}
        
        for timeframe in self.config["market_data"]["timeframes"]:
            # Simuler l'analyse pour différents timeframes
            # Dans un système réel, utiliser des données réelles
            
            if asset in self.historical_data:
                # Simplification pour l'exemple
                if timeframe == "1d":
                    data_points = self.historical_data[asset][-30:]
                elif timeframe == "4h":
                    data_points = self.historical_data[asset][-120:]
                else:  # 1h
                    data_points = self.historical_data[asset][-240:]
                
                if data_points:
                    analysis[timeframe] = {
                        "trend": self._calculate_trend(data_points),
                        "momentum": self._calculate_momentum(data_points),
                        "volatility": self._calculate_volatility(data_points),
                        "volume_profile": self._analyze_volume_profile(data_points)
                    }
        
        return analysis
    
    def _calculate_trend(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule la tendance à partir des données
        
        Args:
            data: Liste des données OHLCV
            
        Returns:
            Analyse de tendance
        """
        if not data:
            return {"direction": "neutral", "strength": 0.0}
            
        # Calculer SMA simple
        sma_20 = sum(d["close"] for d in data[-20:]) / min(20, len(data)) if len(data) >= 20 else sum(d["close"] for d in data) / len(data)
        current_price = data[-1]["close"]
        
        trend_strength = (current_price - sma_20) / sma_20
        
        return {
            "direction": "bullish" if trend_strength > 0 else "bearish",
            "strength": abs(trend_strength),
            "sma_distance": trend_strength
        }
    
    def _calculate_momentum(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule le momentum
        
        Args:
            data: Liste des données OHLCV
            
        Returns:
            Analyse de momentum
        """
        if len(data) < 14:
            return {"rsi": 50.0, "macd": 0.0}
            
        # Simuler RSI
        close_prices = [d["close"] for d in data]
        gains = []
        losses = []
        
        for i in range(1, len(close_prices)):
            change = close_prices[i] - close_prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else sum(gains) / len(gains)
        avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else sum(losses) / len(losses)
        
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))
        
        return {
            "rsi": rsi,
            "overbought": rsi > 70,
            "oversold": rsi < 30
        }
    
    def _calculate_volatility(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule la volatilité
        
        Args:
            data: Liste des données OHLCV
            
        Returns:
            Analyse de volatilité
        """
        if not data:
            return {"atr": 0.0, "normalized_volatility": 0.0}
            
        # Calculer ATR simplifié
        atr_values = []
        for i in range(1, len(data)):
            high = data[i]["high"]
            low = data[i]["low"]
            prev_close = data[i-1]["close"]
            
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            atr_values.append(tr)
        
        atr = sum(atr_values[-14:]) / min(14, len(atr_values)) if atr_values else 0
        current_price = data[-1]["close"]
        normalized_volatility = atr / current_price if current_price > 0 else 0
        
        return {
            "atr": atr,
            "normalized_volatility": normalized_volatility,
            "volatility_regime": "high" if normalized_volatility > 0.05 else "low"
        }
    
    def _analyze_volume_profile(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyse le profil de volume
        
        Args:
            data: Liste des données OHLCV
            
        Returns:
            Analyse de volume
        """
        if not data:
            return {"trend": "neutral", "relative_volume": 1.0}
            
        volumes = [d["volume"] for d in data]
        avg_volume = sum(volumes) / len(volumes)
        recent_volume = volumes[-1] if volumes else 0
        
        relative_volume = recent_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Détecter la tendance de volume
        if len(volumes) >= 5:
            recent_avg = sum(volumes[-5:]) / 5
            older_avg = sum(volumes[-10:-5]) / 5 if len(volumes) >= 10 else recent_avg
            volume_trend = "increasing" if recent_avg > older_avg else "decreasing"
        else:
            volume_trend = "neutral"
        
        return {
            "trend": volume_trend,
            "relative_volume": relative_volume,
            "above_average": relative_volume > 1.2
        }
    
    def _detect_structural_changes(self) -> List[Dict[str, Any]]:
        """
        Détecte les changements structurels du marché
        
        Returns:
            Liste des changements structurels détectés
        """
        structural_changes = []
        
        # Analyser les changements de corrélation à long terme
        historical_correlations = self._get_historical_correlations()
        current_correlations = self.scan_data.get("correlations", {})
        
        for key, current_corr in current_correlations.items():
            if key in historical_correlations:
                historical_avg = historical_correlations[key]["avg"]
                current_value = current_corr["value"]
                
                change = abs(current_value - historical_avg)
                if change > 0.3:  # Changement significatif
                    structural_changes.append({
                        "type": "correlation_shift",
                        "assets": key,
                        "change": change,
                        "direction": "increased" if current_value > historical_avg else "decreased",
                        "significance": "high" if change > 0.5 else "moderate"
                    })
        
        # Détecter les changements de volatilité structurelle
        volatility_change = self._detect_volatility_regime_change()
        if volatility_change:
            structural_changes.append(volatility_change)
        
        return structural_changes
    
    def _get_historical_correlations(self) -> Dict[str, Dict[str, float]]:
        """
        Récupère les corrélations historiques moyennes
        
        Returns:
            Corrélations historiques
        """
        # Simuler des corrélations historiques
        # Dans un système réel, charger depuis une base de données
        historical = {}
        
        for corr_key in ["crypto_forex", "crypto_indices", "forex_indices", "crypto_internal", "forex_internal"]:
            if "internal" in corr_key:
                historical[corr_key] = {"avg": 0.4}  # Corrélation moyenne interne
            else:
                historical[corr_key] = {"avg": 0.2}  # Corrélation moyenne inter-catégorie
        
        return historical
    
    def _detect_volatility_regime_change(self) -> Optional[Dict[str, Any]]:
        """
        Détecte un changement de régime de volatilité
        
        Returns:
            Changement de régime détecté ou None
        """
        current_volatility = self._assess_market_volatility()
        
        # Simuler une détection de changement de régime
        # Dans un système réel, comparer avec l'historique
        if current_volatility.get("level", "normal") != "normal":
            return {
                "type": "volatility_regime_change",
                "new_regime": current_volatility["level"],
                "change_magnitude": abs(current_volatility.get("z_score", 0)),
                "affected_markets": ["crypto", "forex"]
            }
        
        return None
    
    def _identify_emerging_themes(self) -> List[Dict[str, Any]]:
        """
        Identifie les thèmes émergents du marché
        
        Returns:
            Liste des thèmes émergents
        """
        emerging_themes = []
        
        # Analyser les mouvements de secteurs
        sector_analysis = self._analyze_sector_movements()
        for sector, data in sector_analysis.items():
            if data["strength"] > 0.6 and data["consistency"] > 0.7:
                emerging_themes.append({
                    "theme": f"{sector}_trend",
                    "description": f"Forte tendance dans le secteur {sector}",
                    "strength": data["strength"],
                    "assets_involved": data["top_assets"],
                    "timeframe": "medium_term"
                })
        
        # Détecter les thèmes de corrélation croisée
        cross_asset_themes = self._detect_cross_asset_themes()
        emerging_themes.extend(cross_asset_themes)
        
        return emerging_themes
    
    def _analyze_sector_movements(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyse les mouvements par secteur
        
        Returns:
            Analyse par secteur
        """
        sector_analysis = {}
        
        for sector, assets in self.config["asset_categories"].items():
            sector_trends = []
            top_assets = []
            
            for asset in assets:
                if asset in self.historical_data:
                    trend_strength = self._analyze_short_term_trend(asset)
                    sector_trends.append(trend_strength)
                    
                    if trend_strength > 0.5:
                        top_assets.append({
                            "asset": asset,
                            "strength": trend_strength
                        })
            
            if sector_trends:
                avg_strength = sum(sector_trends) / len(sector_trends)
                consistency = sum(1 for t in sector_trends if t * avg_strength > 0) / len(sector_trends)
                
                sector_analysis[sector] = {
                    "strength": abs(avg_strength),
                    "direction": "bullish" if avg_strength > 0 else "bearish",
                    "consistency": consistency,
                    "top_assets": sorted(top_assets, key=lambda x: x["strength"], reverse=True)[:3]
                }
        
        return sector_analysis
    
    def _detect_cross_asset_themes(self) -> List[Dict[str, Any]]:
        """
        Détecte les thèmes transversaux entre actifs
        
        Returns:
            Liste des thèmes transversaux
        """
        cross_themes = []
        
        # Analyser les mouvements synchronisés
        synchronized_moves = self._detect_synchronized_movements()
        
        for sync_group in synchronized_moves:
            cross_themes.append({
                "theme": "synchronized_movement",
                "description": f"Mouvement synchronisé détecté entre {', '.join(sync_group['assets'])}",
                "strength": sync_group["correlation"],
                "assets_involved": sync_group["assets"],
                "direction": sync_group["direction"]
            })
        
        return cross_themes
    
    def _detect_synchronized_movements(self) -> List[Dict[str, Any]]:
        """
        Détecte les mouvements synchronisés entre actifs
        
        Returns:
            Liste des mouvements synchronisés
        """
        synchronized = []
        assets = []
        
        # Collecter tous les actifs avec des données
        for asset, data in self.historical_data.items():
            if len(data) >= 20:
                assets.append(asset)
        
        # Analyser les mouvements des 5 derniers jours
        for i in range(len(assets)):
            for j in range(i + 1, len(assets)):
                asset1, asset2 = assets[i], assets[j]
                
                # Calculer la corrélation des mouvements
                moves1 = []
                moves2 = []
                
                for idx in range(-5, 0):  # 5 derniers jours
                    if idx < -len(self.historical_data[asset1]) or idx < -len(self.historical_data[asset2]):
                        continue
                        
                    move1 = self.historical_data[asset1][idx]["close"] - self.historical_data[asset1][idx-1]["close"]
                    move2 = self.historical_data[asset2][idx]["close"] - self.historical_data[asset2][idx-1]["close"]
                    
                    moves1.append(move1)
                    moves2.append(move2)
                
                if moves1 and moves2:
                    correlation = self._calculate_simple_correlation(moves1, moves2)
                    
                    if correlation > 0.7:  # Forte corrélation
                        direction = "bullish" if sum(moves1) > 0 else "bearish"
                        synchronized.append({
                            "assets": [asset1, asset2],
                            "correlation": correlation,
                            "direction": direction
                        })
        
        return synchronized
    
    def _calculate_simple_correlation(self, x: List[float], y: List[float]) -> float:
        """
        Calcule une corrélation simple entre deux listes
        
        Args:
            x: Première série
            y: Deuxième série
            
        Returns:
            Coefficient de corrélation
        """
        if len(x) != len(y) or len(x) < 2:
            return 0.0
            
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(a * b for a, b in zip(x, y))
        sum_x2 = sum(a * a for a in x)
        sum_y2 = sum(b * b for b in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
        
        if denominator == 0:
            return 0.0
            
        return numerator / denominator
    
    def _perform_risk_assessment(self) -> Dict[str, Any]:
        """
        Effectue une évaluation des risques
        
        Returns:
            Évaluation des risques
        """
        risk_assessment = {
            "overall_risk": 0.0,
            "risk_factors": [],
            "market_stress": 0.0,
            "risk_by_category": {}
        }
        
        # Évaluer le risque de volatilité
        volatility_risk = self._assess_volatility_risk()
        risk_assessment["risk_factors"].append(volatility_risk)
        
        # Évaluer le risque de corrélation
        correlation_risk = self._assess_correlation_risk()
        risk_assessment["risk_factors"].append(correlation_risk)
        
        # Évaluer le risque de liquidité
        liquidity_risk = self._assess_liquidity_risk()
        risk_assessment["risk_factors"].append(liquidity_risk)
        
        # Calculer le risque global
        total_risk_score = sum(factor["score"] for factor in risk_assessment["risk_factors"])
        risk_assessment["overall_risk"] = total_risk_score / len(risk_assessment["risk_factors"])
        
        # Calculer le stress du marché
        risk_assessment["market_stress"] = self._calculate_market_stress()
        
        # Risque par catégorie
        for category in self.config["asset_categories"].keys():
            risk_assessment["risk_by_category"][category] = self._assess_category_risk(category)
        
        return risk_assessment
    
    def _assess_volatility_risk(self) -> Dict[str, Any]:
        """
        Évalue le risque de volatilité
        
        Returns:
            Évaluation du risque de volatilité
        """
        current_volatility = self._assess_market_volatility()
        
        score = 0.0
        if "level" in current_volatility:
            if current_volatility["level"] == "high":
                score = 0.8
            elif current_volatility["level"] == "elevated":
                score = 0.5
            else:
                score = 0.2
        
        return {
            "factor": "volatility",
            "score": score,
            "level": current_volatility.get("level", "normal"),
            "description": f"Risque de volatilité: {current_volatility.get('level', 'normal')}"
        }
    
    def _assess_correlation_risk(self) -> Dict[str, Any]:
        """
        Évalue le risque de corrélation
        
        Returns:
            Évaluation du risque de corrélation
        """
        correlations = self.scan_data.get("correlations", {})
        
        high_correlation_count = 0
        for corr_data in correlations.values():
            if isinstance(corr_data, dict) and "value" in corr_data:
                if abs(corr_data["value"]) > 0.8:
                    high_correlation_count += 1
        
        correlation_ratio = high_correlation_count / len(correlations) if correlations else 0
        score = min(1.0, correlation_ratio * 2)  # Score entre 0 et 1
        
        return {
            "factor": "correlation",
            "score": score,
            "high_correlation_count": high_correlation_count,
            "description": f"Risque de corrélation élevée détecté dans {high_correlation_count} paires"
        }
    
    def _assess_liquidity_risk(self) -> Dict[str, Any]:
        """
        Évalue le risque de liquidité
        
        Returns:
            Évaluation du risque de liquidité
        """
        # Simuler une évaluation du risque de liquidité
        # Dans un système réel, analyser les volumes et la profondeur de marché
        
        low_liquidity_assets = []
        for asset, data in self.historical_data.items():
            if data and len(data) > 0:
                recent_volume = data[-1].get("volume", 0)
                if recent_volume < self._get_average_volume(asset) * 0.5:
                    low_liquidity_assets.append(asset)
        
        score = min(1.0, len(low_liquidity_assets) / 5)  # Score basé sur le nombre d'actifs à faible liquidité
        
        return {
            "factor": "liquidity",
            "score": score,
            "low_liquidity_assets": low_liquidity_assets,
            "description": f"Risque de liquidité détecté sur {len(low_liquidity_assets)} actifs"
        }
    
    def _get_average_volume(self, asset: str) -> float:
        """
        Obtient le volume moyen d'un actif
        
        Args:
            asset: Actif
            
        Returns:
            Volume moyen
        """
        if asset not in self.historical_data or not self.historical_data[asset]:
            return 0.0
            
        volumes = [d.get("volume", 0) for d in self.historical_data[asset]]
        return sum(volumes) / len(volumes) if volumes else 0.0
    
    def _calculate_market_stress(self) -> float:
        """
        Calcule l'indice de stress du marché
        
        Returns:
            Indice de stress (0-1)
        """
        stress_factors = []
        
        # Stress de volatilité
        volatility_state = self._assess_market_volatility()
        if "level" in volatility_state:
            if volatility_state["level"] == "high":
                stress_factors.append(0.8)
            elif volatility_state["level"] == "elevated":
                stress_factors.append(0.5)
            else:
                stress_factors.append(0.2)
        
        # Stress de corrélation
        high_correlations = 0
        for corr_data in self.scan_data.get("correlations", {}).values():
            if isinstance(corr_data, dict) and abs(corr_data.get("value", 0)) > 0.8:
                high_correlations += 1
        stress_factors.append(min(1.0, high_correlations / 5))
        
        # Stress de tendance (divergence)
        trend_divergence = self._calculate_trend_divergence()
        stress_factors.append(trend_divergence)
        
        return sum(stress_factors) / len(stress_factors) if stress_factors else 0.0
    
    def _calculate_trend_divergence(self) -> float:
        """
        Calcule la divergence des tendances
        
        Returns:
            Indice de divergence (0-1)
        """
        category_trends = {}
        
        for category, assets in self.config["asset_categories"].items():
            trend_directions = []
            for asset in assets:
                if asset in self.historical_data:
                    trend = self._analyze_short_term_trend(asset)
                    trend_directions.append(1 if trend > 0 else -1 if trend < 0 else 0)
            
            if trend_directions:
                consensus = abs(sum(trend_directions)) / len(trend_directions)
                category_trends[category] = consensus
        
        if not category_trends:
            return 0.0
            
        # Calculer la divergence entre catégories
        max_consensus = max(category_trends.values())
        min_consensus = min(category_trends.values())
        
        return max(0.0, max_consensus - min_consensus)
    
    def _assess_category_risk(self, category: str) -> Dict[str, Any]:
        """
        Évalue le risque pour une catégorie d'actifs
        
        Args:
            category: Catégorie d'actifs
            
        Returns:
            Évaluation du risque
        """
        if category not in self.config["asset_categories"]:
            return {"risk_level": 0.0, "description": "Catégorie inconnue"}
            
        assets = self.config["asset_categories"][category]
        risk_scores = []
        
        for asset in assets:
            if asset in self.historical_data:
                # Calculer le risque de volatilité
                vol_data = self._calculate_volatility(self.historical_data[asset])
                vol_risk = vol_data.get("normalized_volatility", 0) * 2  # Normaliser sur 0-1
                
                # Calculer le risque de tendance
                trend = self._analyze_short_term_trend(asset)
                trend_risk = abs(trend) if trend < 0 else 0  # Risque élevé dans les tendances baissières
                
                asset_risk = (vol_risk + trend_risk) / 2
                risk_scores.append(asset_risk)
        
        if risk_scores:
            avg_risk = sum(risk_scores) / len(risk_scores)
            max_risk = max(risk_scores)
            
            if avg_risk > 0.7:
                risk_level = "high"
            elif avg_risk > 0.4:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                "risk_level": risk_level,
                "risk_score": avg_risk,
                "max_risk": max_risk,
                "assets_at_risk": [assets[i] for i, score in enumerate(risk_scores) if score > 0.6],
                "description": f"Risque {risk_level} pour la catégorie {category}"
            }
        else:
            return {
                "risk_level": "unknown",
                "risk_score": 0.0,
                "description": f"Données insuffisantes pour évaluer le risque de {category}"
            }
    
    def _evaluate_opportunity(self, asset: str, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Évalue une opportunité pour un actif
        
        Args:
            asset: Actif à évaluer
            data: Données historiques
            
        Returns:
            Opportunité détectée ou None
        """
        # Analyseurs multiples
        trend_score = self._evaluate_trend_opportunity(data)
        momentum_score = self._evaluate_momentum_opportunity(data)
        volatility_score = self._evaluate_volatility_opportunity(data)
        value_score = self._evaluate_value_opportunity(data)
        
        # Combiner les scores
        overall_score = (
            trend_score * 0.3 +
            momentum_score * 0.25 +
            volatility_score * 0.2 +
            value_score * 0.25
        )
        
        if overall_score > self.config["detection_thresholds"]["opportunity_strength_min"]:
            # Déterminer la direction
            direction = "bullish" if trend_score > 0 else "bearish"
            
            # Calculer les niveaux
            current_price = data[-1]["close"]
            entry_zone = self._calculate_entry_zone(data)
            target = self._calculate_target(data, direction)
            stop_loss = self._calculate_stop_loss(data, direction)
            
            return {
                "asset": asset,
                "type": direction,
                "strength": overall_score,
                "entry_zone": entry_zone,
                "target": target,
                "stop_loss": stop_loss,
                "risk_reward": abs(target - current_price) / abs(current_price - stop_loss),
                "timeframe": "medium",  # Basé sur l'analyse
                "confidence": min(1.0, overall_score * 1.2),
                "factors": {
                    "trend": trend_score,
                    "momentum": momentum_score,
                    "volatility": volatility_score,
                    "value": value_score
                }
            }
        
        return None
    
    def _evaluate_trend_opportunity(self, data: List[Dict[str, Any]]) -> float:
        """
        Évalue l'opportunité basée sur la tendance
        
        Args:
            data: Données historiques
            
        Returns:
            Score de tendance
        """
        # Calculer plusieurs moyennes mobiles
        sma_20 = sum(d["close"] for d in data[-20:]) / 20 if len(data) >= 20 else 0
        sma_50 = sum(d["close"] for d in data[-50:]) / 50 if len(data) >= 50 else 0
        current_price = data[-1]["close"]
        
        # Score basé sur la position des prix
        price_score = 0.0
        if sma_20 > sma_50 and current_price > sma_20:
            price_score = 0.5  # Tendance haussière
        elif sma_20 < sma_50 and current_price < sma_20:
            price_score = -0.5  # Tendance baissière
        
        # Score basé sur la pente de la tendance
        if len(data) >= 10:
            slope_score = (current_price - data[-10]["close"]) / data[-10]["close"]
            slope_score = max(-0.5, min(0.5, slope_score * 10))  # Normaliser
        else:
            slope_score = 0.0
        
        return price_score + slope_score
    
    def _evaluate_momentum_opportunity(self, data: List[Dict[str, Any]]) -> float:
        """
        Évalue l'opportunité basée sur le momentum
        
        Args:
            data: Données historiques
            
        Returns:
            Score de momentum
        """
        if len(data) < 14:
            return 0.0
            
        # Calculer RSI
        close_prices = [d["close"] for d in data]
        gains = []
        losses = []
        
        for i in range(1, len(close_prices)):
            change = close_prices[i] - close_prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # Score basé sur RSI
        if rsi < 30:
            return 0.8  # Survente, opportunité haussière
        elif rsi > 70:
            return -0.8  # Surachat, opportunité baissière
        elif 40 < rsi < 50:
            return 0.3  # Zone neutre avec momentum possible
        else:
            return 0.0
    
    def _evaluate_volatility_opportunity(self, data: List[Dict[str, Any]]) -> float:
        """
        Évalue l'opportunité basée sur la volatilité
        
        Args:
            data: Données historiques
            
        Returns:
            Score de volatilité
        """
        if not data:
            return 0.0
            
        # Calculer la volatilité récente
        volatility = self._calculate_volatility(data)
        current_vol = volatility.get("normalized_volatility", 0)
        
        # Score basé sur la volatilité
        # Volatilité modérée est idéale pour le trading
        if 0.02 < current_vol < 0.05:
            return 0.5  # Volatilité optimale
        elif current_vol > 0.1:
            return -0.3  # Trop volatile
        elif current_vol < 0.01:
            return -0.2  # Trop calme
        else:
            return 0.2  # Volatilité acceptable
    
    def _evaluate_value_opportunity(self, data: List[Dict[str, Any]]) -> float:
        """
        Évalue l'opportunité basée sur la valeur
        
        Args:
            data: Données historiques
            
        Returns:
            Score de valeur
        """
        if len(data) < 20:
            return 0.0
            
        # Calculer la distance par rapport aux moyennes
        current_price = data[-1]["close"]
        sma_20 = sum(d["close"] for d in data[-20:]) / 20
        
        # Score basé sur l'écart par rapport à la moyenne
        deviation = (current_price - sma_20) / sma_20
        
        # Opportunité si le prix est significativement en dessous de la moyenne
        if deviation < -0.05:
            return min(0.5, -deviation * 10)  # Potentielle sous-évaluation
        elif deviation > 0.05:
            return max(-0.5, -deviation * 10)  # Potentielle surévaluation
        else:
            return 0.0
    
    def _calculate_entry_zone(self, data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calcule la zone d'entrée idéale
        
        Args:
            data: Données historiques
            
        Returns:
            Zone d'entrée
        """
        current_price = data[-1]["close"]
        volatility = self._calculate_volatility(data)
        atr = volatility.get("atr", 0)
        
        # Zone d'entrée basée sur la volatilité
        entry_range = atr * 0.5  # 50% de l'ATR pour la zone d'entrée
        
        return {
            "lower": current_price - entry_range,
            "upper": current_price + entry_range,
            "center": current_price
        }
    
    def _calculate_target(self, data: List[Dict[str, Any]], direction: str) -> float:
        """
        Calcule le niveau cible
        
        Args:
            data: Données historiques
            direction: Direction de l'opportunité
            
        Returns:
            Niveau cible
        """
        current_price = data[-1]["close"]
        volatility = self._calculate_volatility(data)
        atr = volatility.get("atr", 0)
        
        # Cible basée sur l'ATR
        target_distance = atr * 2  # 2x ATR comme cible
        
        if direction == "bullish":
            return current_price + target_distance
        else:
            return current_price - target_distance
    
    def _calculate_stop_loss(self, data: List[Dict[str, Any]], direction: str) -> float:
        """
        Calcule le niveau de stop loss
        
        Args:
            data: Données historiques
            direction: Direction de l'opportunité
            
        Returns:
            Niveau de stop loss
        """
        current_price = data[-1]["close"]
        volatility = self._calculate_volatility(data)
        atr = volatility.get("atr", 0)
        
        # Stop loss basé sur l'ATR
        stop_distance = atr * 1.5  # 1.5x ATR comme stop loss
        
        if direction == "bullish":
            return current_price - stop_distance
        else:
            return current_price + stop_distance
    
    def _calculate_cross_category_correlation(self, cat1: str, cat2: str) -> float:
        """
        Calcule la corrélation entre deux catégories
        
        Args:
            cat1: Première catégorie
            cat2: Deuxième catégorie
            
        Returns:
            Coefficient de corrélation
        """
        # Simplification - calcul basique pour l'exemple
        assets1 = self.config["asset_categories"].get(cat1, [])
        assets2 = self.config["asset_categories"].get(cat2, [])
        
        correlations = []
        for asset1 in assets1[:3]:  # Limiter pour l'exemple
            for asset2 in assets2[:3]:
                if asset1 in self.historical_data and asset2 in self.historical_data:
                    # Calculer la corrélation entre les mouvements récents
                    moves1 = []
                    moves2 = []
                    
                    for i in range(-10, 0):  # 10 dernières périodes
                        if (i >= -len(self.historical_data[asset1]) and 
                            i >= -len(self.historical_data[asset2])):
                            move1 = (self.historical_data[asset1][i]["close"] - 
                                    self.historical_data[asset1][i-1]["close"]) / self.historical_data[asset1][i-1]["close"]
                            move2 = (self.historical_data[asset2][i]["close"] - 
                                    self.historical_data[asset2][i-1]["close"]) / self.historical_data[asset2][i-1]["close"]
                            moves1.append(move1)
                            moves2.append(move2)
                    
                    if moves1 and moves2:
                        corr = self._calculate_simple_correlation(moves1, moves2)
                        correlations.append(corr)
        
        return sum(correlations) / len(correlations) if correlations else 0.0
    
    def _calculate_intra_category_correlations(self, assets: List[str]) -> Dict[str, float]:
        """
        Calcule les corrélations internes d'une catégorie
        
        Args:
            assets: Liste des actifs
            
        Returns:
            Corrélations intra-catégorie
        """
        correlations = {}
        
        for i in range(len(assets)):
            for j in range(i + 1, len(assets)):
                asset1, asset2 = assets[i], assets[j]
                
                if asset1 in self.historical_data and asset2 in self.historical_data:
                    corr = self._calculate_asset_correlation(asset1, asset2)
                    correlations[f"{asset1}_{asset2}"] = corr
        
        return correlations
    
    def _calculate_asset_correlation(self, asset1: str, asset2: str) -> float:
        """
        Calcule la corrélation entre deux actifs
        
        Args:
            asset1: Premier actif
            asset2: Deuxième actif
            
        Returns:
            Coefficient de corrélation
        """
        data1 = self.historical_data.get(asset1, [])
        data2 = self.historical_data.get(asset2, [])
        
        if not data1 or not data2:
            return 0.0
            
        # Extraire les prix de clôture
        prices1 = [d["close"] for d in data1]
        prices2 = [d["close"] for d in data2]
        
        # Aligner les longueurs
        min_len = min(len(prices1), len(prices2))
        prices1 = prices1[-min_len:]
        prices2 = prices2[-min_len:]
        
        # Calculer les rendements
        returns1 = []
        returns2 = []
        
        for i in range(1, min_len):
            returns1.append((prices1[i] - prices1[i-1]) / prices1[i-1])
            returns2.append((prices2[i] - prices2[i-1]) / prices2[i-1])
        
        return self._calculate_simple_correlation(returns1, returns2)
    
    def _assess_market_volatility(self) -> Dict[str, Any]:
        """
        Évalue la volatilité globale du marché
        
        Returns:
            Évaluation de la volatilité
        """
        volatilities = []
        
        # Calculer la volatilité pour chaque actif
        for asset, data in self.historical_data.items():
            if data:
                vol_data = self._calculate_volatility(data)
                volatilities.append(vol_data.get("normalized_volatility", 0))
        
        if not volatilities:
            return {"level": "unknown", "value": 0.0}
        
        # Calculer la moyenne et l'écart-type
        avg_volatility = sum(volatilities) / len(volatilities)
        
        # Définir les niveaux de volatilité
        if avg_volatility > 0.1:
            level = "high"
            desc = "Volatilité élevée"
        elif avg_volatility > 0.05:
            level = "elevated"
            desc = "Volatilité modérée à élevée"
        elif avg_volatility > 0.02:
            level = "normal"
            desc = "Volatilité normale"
        else:
            level = "low"
            desc = "Volatilité faible"
        
        return {
            "level": level,
            "value": avg_volatility,
            "description": desc,
            "assets_count": len(volatilities)
        }
    
    def _assess_market_trend(self) -> Dict[str, Any]:
        """
        Évalue la tendance globale du marché
        
        Returns:
            Évaluation de la tendance
        """
        trend_strengths = []
        bullish_count = 0
        bearish_count = 0
        
        # Analyser la tendance pour chaque actif
        for asset, data in self.historical_data.items():
            if data and len(data) >= 20:
                trend = self._analyze_short_term_trend(asset)
                trend_strengths.append(trend)
                
                if trend > 0:
                    bullish_count += 1
                elif trend < 0:
                    bearish_count += 1
        
        if not trend_strengths:
            return {"direction": "unknown", "strength": 0.0}
        
        # Calculer la tendance globale
        avg_trend = sum(trend_strengths) / len(trend_strengths)
        bullish_ratio = bullish_count / len(trend_strengths)
        
        # Déterminer la direction
        if avg_trend > 0.2 and bullish_ratio > 0.6:
            direction = "strongly_bullish"
        elif avg_trend > 0.1 and bullish_ratio > 0.5:
            direction = "bullish"
        elif avg_trend < -0.2 and bullish_ratio < 0.4:
            direction = "strongly_bearish"
        elif avg_trend < -0.1 and bullish_ratio < 0.5:
            direction = "bearish"
        else:
            direction = "neutral"
        
        return {
            "direction": direction,
            "strength": abs(avg_trend),
            "bullish_ratio": bullish_ratio,
            "assets_analyzed": len(trend_strengths)
        }
    
    def _assess_correlation_regime(self) -> Dict[str, Any]:
        """
        Évalue le régime de corrélation actuel
        
        Returns:
            Évaluation du régime de corrélation
        """
        correlations = []
        
        # Collecter toutes les corrélations
        for corr_data in self.scan_data.get("correlations", {}).values():
            if isinstance(corr_data, dict) and "value" in corr_data:
                correlations.append(abs(corr_data["value"]))
        
        if not correlations:
            return {"regime": "unknown", "strength": 0.0}
        
        # Calculer la moyenne des corrélations
        avg_correlation = sum(correlations) / len(correlations)
        
        # Déterminer le régime
        if avg_correlation > 0.7:
            regime = "high_correlation"
            desc = "Corrélations élevées entre actifs"
        elif avg_correlation > 0.4:
            regime = "moderate_correlation"
            desc = "Corrélations modérées entre actifs"
        else:
            regime = "low_correlation"
            desc = "Faibles corrélations entre actifs"
        
        return {
            "regime": regime,
            "strength": avg_correlation,
            "description": desc,
            "correlations_count": len(correlations)
        }
    
    def _assess_risk_environment(self) -> Dict[str, Any]:
        """
        Évalue l'environnement de risque global
        
        Returns:
            Évaluation de l'environnement de risque
        """
        risk_factors = []
        
        # Facteur de volatilité
        volatility_state = self._assess_market_volatility()
        if volatility_state.get("level") == "high":
            risk_factors.append(0.8)
        elif volatility_state.get("level") == "elevated":
            risk_factors.append(0.5)
        else:
            risk_factors.append(0.2)
        
        # Facteur de corrélation
        correlation_state = self._assess_correlation_regime()
        if correlation_state.get("regime") == "high_correlation":
            risk_factors.append(0.7)
        elif correlation_state.get("regime") == "moderate_correlation":
            risk_factors.append(0.4)
        else:
            risk_factors.append(0.2)
        
        # Calculer le risque global
        avg_risk = sum(risk_factors) / len(risk_factors)
        
        # Déterminer le niveau de risque
        if avg_risk > 0.6:
            risk_level = "high"
            desc = "Environnement à haut risque"
        elif avg_risk > 0.4:
            risk_level = "moderate"
            desc = "Risque modéré"
        else:
            risk_level = "low"
            desc = "Environnement à faible risque"
        
        return {
            "risk_level": risk_level,
            "risk_score": avg_risk,
            "description": desc,
            "factors": {
                "volatility": volatility_state.get("level"),
                "correlation": correlation_state.get("regime")
            }
        }
    
    def _determine_overall_regime(self, regime_data: Dict[str, Dict[str, Any]]) -> str:
        """
        Détermine le régime de marché global
        
        Args:
            regime_data: Données des composants du régime
            
        Returns:
            Régime de marché global
        """
        # Analyser chaque composant
        volatility_level = regime_data.get("volatility_state", {}).get("level")
        trend_direction = regime_data.get("trend_state", {}).get("direction")
        correlation_regime = regime_data.get("correlation_state", {}).get("regime")
        risk_level = regime_data.get("risk_state", {}).get("risk_level")
        
        # Déterminer le régime global
        if volatility_level == "high" and risk_level == "high":
            return "stressed_market"
        elif trend_direction in ["strongly_bullish", "strongly_bearish"] and volatility_level in ["low", "normal"]:
            return "trending_market"
        elif correlation_regime == "high_correlation" and risk_level == "moderate":
            return "synchronized_market"
        elif volatility_level == "low" and risk_level == "low":
            return "stable_market"
        elif trend_direction == "neutral" and volatility_level in ["normal", "low"]:
            return "ranging_market"
        else:
            return "transitional_market"
    
    def _calculate_regime_confidence(self, regime_data: Dict[str, Dict[str, Any]]) -> float:
        """
        Calcule la confiance dans l'identification du régime
        
        Args:
            regime_data: Données des composants du régime
            
        Returns:
            Niveau de confiance (0-1)
        """
        confidence_factors = []
        
        # Confiance en volatilité
        volatility_data = regime_data.get("volatility_state", {})
        if "value" in volatility_data:
            # Plus la volatilité est extrême, plus la confiance est élevée
            vol_confidence = min(1.0, abs(volatility_data["value"] - 0.05) * 10)
            confidence_factors.append(vol_confidence)
        
        # Confiance en tendance
        trend_data = regime_data.get("trend_state", {})
        if "strength" in trend_data:
            # Plus la tendance est forte, plus la confiance est élevée
            trend_confidence = min(1.0, trend_data["strength"] * 2)
            confidence_factors.append(trend_confidence)
        
        # Confiance en corrélation
        correlation_data = regime_data.get("correlation_state", {})
        if "strength" in correlation_data:
            # Plus la corrélation est extrême (haute ou basse), plus la confiance est élevée
            corr_confidence = min(1.0, abs(correlation_data["strength"] - 0.35) * 2)
            confidence_factors.append(corr_confidence)
        
        # Calculer la confiance globale
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
    
    def _handle_market_data(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les mises à jour de données de marché
        
        Args:
            data: Données de marché
        """
        symbol = data.get("symbol")
        if not symbol:
            return
        
        # Mettre à jour les données historiques
        if symbol not in self.historical_data:
            self.historical_data[symbol] = []
        
        # Construire un enregistrement OHLCV
        candle = {
            "timestamp": data.get("timestamp", time.time()),
            "open": data.get("open", data.get("price", 0)),
            "high": data.get("high", data.get("price", 0)),
            "low": data.get("low", data.get("price", 0)),
            "close": data.get("price", 0),
            "volume": data.get("volume", 0)
        }
        
        # Ajouter au historique
        self.historical_data[symbol].append(candle)
        
        # Limiter la taille de l'historique
        max_history = self.config["market_data"]["lookback_days"] * 24  # Supposer des données horaires
        if len(self.historical_data[symbol]) > max_history:
            self.historical_data[symbol] = self.historical_data[symbol][-max_history:]
    
    def _handle_scan_request(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les demandes de scan
        
        Args:
            data: Données de la demande
        """
        request_id = data.get("request_id", "unknown")
        scan_type = data.get("scan_type", "quick")
        
        if scan_type == "quick":
            self._perform_quick_scan()
        elif scan_type == "deep":
            self._perform_deep_scan()
        elif scan_type == "correlation":
            self._perform_correlation_analysis()
        elif scan_type == "full":
            # Effectuer tous les types de scan
            self._perform_quick_scan()
            self._perform_deep_scan()
            self._perform_correlation_analysis()
        
        # Publier la réponse
        self.event_bus.publish("horizon_scan_response", {
            "request_id": request_id,
            "scan_type": scan_type,
            "status": "completed",
            "scan_data": self.scan_data,
            "timestamp": time.time()
        })
    
    def _handle_market_patterns(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les patterns de marché détectés
        
        Args:
            data: Données des patterns
        """
        patterns = data.get("patterns", [])
        
        # Analyser les patterns pour des opportunités d'horizon
        for pattern in patterns:
            asset = pattern.get("symbol")
            pattern_type = pattern.get("pattern")
            strength = pattern.get("strength", 0)
            
            # Si le pattern est suffisamment fort, évaluer comme opportunité
            if strength > 0.6 and asset in self.historical_data:
                opportunity = self._evaluate_pattern_opportunity(asset, pattern)
                if opportunity:
                    # Ajouter aux opportunités détectées
                    self.scan_data["opportunities"]["current"].append(opportunity)
    
    def _evaluate_pattern_opportunity(self, asset: str, pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Évalue une opportunité basée sur un pattern
        
        Args:
            asset: Actif concerné
            pattern: Pattern détecté
            
        Returns:
            Opportunité ou None
        """
        pattern_type = pattern.get("pattern")
        strength = pattern.get("strength", 0)
        direction = pattern.get("direction", "neutral")
        
        if direction == "neutral":
            return None
        
        # Obtenir les données historiques
        data = self.historical_data.get(asset, [])
        if not data:
            return None
        
        current_price = data[-1]["close"]
        
        # Créer une opportunité basée sur le pattern
        opportunity = {
            "asset": asset,
            "type": "bullish" if direction == "bullish" else "bearish",
            "strength": strength * 0.9,  # Réduire légèrement la force car basé sur pattern
            "source": "pattern_detection",
            "pattern": pattern_type,
            "entry_zone": {
                "center": current_price,
                "lower": current_price * 0.98,
                "upper": current_price * 1.02
            },
            "target": current_price * 1.05 if direction == "bullish" else current_price * 0.95,
            "stop_loss": current_price * 0.97 if direction == "bullish" else current_price * 1.03,
            "timeframe": "short_to_medium",
            "confidence": strength
        }
        
        return opportunity
    
    def _handle_trade_result(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les résultats de trades
        
        Args:
            data: Données du résultat de trade
        """
        trade_id = data.get("trade_id")
        profit = data.get("profit", 0)
        symbol = data.get("symbol")
        strategy = data.get("strategy")
        
        # Utiliser les résultats de trades pour affiner l'analyse
        if symbol and profit != 0:
            # Mettre à jour les indicateurs de succès pour cet actif
            if symbol in self.scan_data["trends"]:
                # Ajuster la force des tendances détectées basées sur les résultats
                if profit > 0:
                    # Renforcer les signaux qui ont fonctionné
                    self._reinforce_successful_signals(symbol, strategy)
                else:
                    # Réduire la force des signaux qui ont échoué
                    self._weaken_failed_signals(symbol, strategy)
    
    def _reinforce_successful_signals(self, symbol: str, strategy: str):
        """
        Renforce les signaux qui ont fonctionné
        
        Args:
            symbol: Actif concerné
            strategy: Stratégie utilisée
        """
        # Implémentation simplifiée
        # Dans un système réel, ajuster les poids des indicateurs utilisés
        for category, trends in self.scan_data.get("trends", {}).items():
            for trend in trends:
                if trend.get("asset") == symbol:
                    # Augmenter légèrement la force du signal
                    trend["strength"] = min(1.0, trend["strength"] * 1.1)
    
    def _weaken_failed_signals(self, symbol: str, strategy: str):
        """
        Réduit la force des signaux qui ont échoué
        
        Args:
            symbol: Actif concerné
            strategy: Stratégie utilisée
        """
        # Implémentation simplifiée
        # Dans un système réel, ajuster les poids des indicateurs utilisés
        for category, trends in self.scan_data.get("trends", {}).items():
            for trend in trends:
                if trend.get("asset") == symbol:
                    # Réduire la force du signal
                    trend["strength"] = max(0.0, trend["strength"] * 0.9)

if __name__ == "__main__":
    # Test simple du scanner d'horizon
    scanner = FlowHorizonScanner()
    scanner.start()
    
    # Simuler des données de marché
    scanner._handle_market_data({
        "symbol": "BTC/USDT",
        "price": 48000,
        "open": 47500,
        "high": 48500,
        "low": 47000,
        "volume": 5000,
        "timestamp": time.time()
    })
    
    time.sleep(2)  # Attente pour traitement
    scanner.stop()