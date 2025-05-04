#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowVisionMarket.py - Module de surveillance intelligente du marché pour FlowGlobalDynamics™
"""

import logging
import time
import threading
import json
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

class FlowVisionMarket:
    """
    Surveillance intelligente du marché pour l'analyse et la détection d'opportunités
    """
    
    def __init__(self):
        """Initialisation du FlowVisionMarket"""
        self.running = False
        self.threads = {}
        self.logger = self._setup_logger()
        self.event_bus = get_event_bus()
        self.market_data = {}  # Données de marché par paire
        self.watched_symbols = []  # Symboles surveillés
        self.indicators = {}  # Indicateurs calculés par paire
        self.market_patterns = []  # Patterns détectés sur le marché
        self.last_analysis = {}  # Dernière analyse par paire
        
    def _setup_logger(self):
        """Configuration du logger"""
        logger = logging.getLogger("FlowVisionMarket")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def start(self):
        """Démarrage de la surveillance du marché"""
        if self.running:
            self.logger.warning("FlowVisionMarket est déjà en cours d'exécution")
            return
            
        self.running = True
        
        # Chargement des paires surveillées
        self._load_watched_symbols()
        
        # Démarrage des threads de surveillance
        self._start_market_threads()
        
        self._register_events()
        self.logger.info("FlowVisionMarket démarré")
        
    def stop(self):
        """Arrêt de la surveillance du marché"""
        if not self.running:
            self.logger.warning("FlowVisionMarket n'est pas en cours d'exécution")
            return
            
        self.running = False
        
        # Arrêt des threads de surveillance
        for thread_name, thread in self.threads.items():
            if thread and thread.is_alive():
                thread.join(timeout=2.0)
                self.logger.debug(f"Thread {thread_name} arrêté")
        
        self._unregister_events()
        self.logger.info("FlowVisionMarket arrêté")
    
    def _load_watched_symbols(self):
        """Charge la liste des symboles à surveiller"""
        # Liste par défaut
        default_symbols = [
            "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", 
            "ADA/USDT", "XRP/USDT", "DOT/USDT", "DOGE/USDT"
        ]
        
        try:
            # Tenter de charger depuis un fichier (désactivé pour l'exemple)
            # with open("watched_symbols.json", "r") as f:
            #     self.watched_symbols = json.load(f)
            self.watched_symbols = default_symbols
        except Exception as e:
            self.logger.warning(f"Impossible de charger les symboles surveillés: {str(e)}. Utilisation des valeurs par défaut.")
            self.watched_symbols = default_symbols
    
    def _start_market_threads(self):
        """Démarre les threads de surveillance du marché"""
        # Thread principal d'analyse
        self.threads["market_analysis"] = threading.Thread(
            target=self._market_analysis_loop, 
            daemon=True
        )
        self.threads["market_analysis"].start()
        
        # Thread de détection de patterns
        self.threads["pattern_detection"] = threading.Thread(
            target=self._pattern_detection_loop, 
            daemon=True
        )
        self.threads["pattern_detection"].start()
        
        # Thread de recherche d'opportunités
        self.threads["opportunity_scanning"] = threading.Thread(
            target=self._opportunity_scanning_loop, 
            daemon=True
        )
        self.threads["opportunity_scanning"].start()
    
    def _register_events(self):
        """Enregistrement des abonnements aux événements"""
        self.event_bus.subscribe("raw_market_data", self._handle_raw_market_data)
        self.event_bus.subscribe("market_insight_request", self._handle_market_insight_request)
        self.event_bus.subscribe("add_watched_symbol", self._handle_add_watched_symbol)
        self.event_bus.subscribe("remove_watched_symbol", self._handle_remove_watched_symbol)
    
    def _unregister_events(self):
        """Désenregistrement des abonnements aux événements"""
        self.event_bus.unsubscribe("raw_market_data", self._handle_raw_market_data)
        self.event_bus.unsubscribe("market_insight_request", self._handle_market_insight_request)
        self.event_bus.unsubscribe("add_watched_symbol", self._handle_add_watched_symbol)
        self.event_bus.unsubscribe("remove_watched_symbol", self._handle_remove_watched_symbol)
    
    def _market_analysis_loop(self):
        """Boucle principale d'analyse du marché"""
        while self.running:
            try:
                for symbol in self.watched_symbols:
                    if symbol in self.market_data:
                        self._analyze_market_data(symbol)
                        
                time.sleep(1)  # Analyse régulière
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle d'analyse du marché: {str(e)}")
    
    def _pattern_detection_loop(self):
        """Boucle de détection des patterns de marché"""
        while self.running:
            try:
                # Réinitialiser les patterns détectés
                self.market_patterns = []
                
                # Chercher des patterns pour chaque symbole avec suffisamment de données
                for symbol in self.watched_symbols:
                    if symbol in self.indicators and len(self.indicators[symbol].get("candles", [])) > 20:
                        patterns = self._detect_patterns(symbol)
                        if patterns:
                            for pattern in patterns:
                                self.market_patterns.append({
                                    "symbol": symbol,
                                    "pattern": pattern["name"],
                                    "strength": pattern["strength"],
                                    "direction": pattern["direction"],
                                    "timestamp": time.time()
                                })
                
                # Si des patterns ont été détectés, les publier
                if self.market_patterns:
                    self.event_bus.publish("market_patterns_detected", {
                        "patterns": self.market_patterns,
                        "timestamp": time.time()
                    })
                    self.logger.info(f"Détection de {len(self.market_patterns)} patterns de marché")
                
                time.sleep(5)  # Analyse moins fréquente pour les patterns
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de détection de patterns: {str(e)}")
    
    def _opportunity_scanning_loop(self):
        """Boucle de recherche d'opportunités de trading"""
        while self.running:
            try:
                opportunities = []
                
                # Analyser chaque symbole pour des opportunités
                for symbol in self.watched_symbols:
                    if symbol in self.indicators and symbol in self.market_data:
                        symbol_opportunities = self._scan_for_opportunities(symbol)
                        opportunities.extend(symbol_opportunities)
                
                # Si des opportunités ont été trouvées, les publier
                if opportunities:
                    self.event_bus.publish("market_opportunities", {
                        "opportunities": opportunities,
                        "timestamp": time.time()
                    })
                    self.logger.info(f"Détection de {len(opportunities)} opportunités de marché")
                
                time.sleep(3)  # Recherche régulière d'opportunités
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de recherche d'opportunités: {str(e)}")
    
    def _analyze_market_data(self, symbol: str):
        """
        Analyse les données de marché pour un symbole spécifique
        
        Args:
            symbol: Symbole à analyser
        """
        try:
            if symbol not in self.market_data:
                return
                
            # Initialiser ou récupérer les indicateurs existants
            if symbol not in self.indicators:
                self.indicators[symbol] = {
                    "candles": [],
                    "sma": {"fast": [], "medium": [], "slow": []},
                    "rsi": [],
                    "macd": {"line": [], "signal": [], "histogram": []},
                    "volatility": 0,
                    "trend": 0,
                    "support_levels": [],
                    "resistance_levels": []
                }
            
            # Mettre à jour les indicateurs avec les nouvelles données
            self._update_indicators(symbol)
            
            # Calculer la volatilité
            self.indicators[symbol]["volatility"] = self._calculate_volatility(symbol)
            
            # Détecter la tendance
            self.indicators[symbol]["trend"] = self._detect_trend(symbol)
            
            # Mettre à jour les niveaux de support/résistance
            self._update_support_resistance(symbol)
            
            # Enregistrer l'heure de la dernière analyse
            self.last_analysis[symbol] = time.time()
            
            # Publier les données de marché analysées
            self._publish_market_data(symbol)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse pour {symbol}: {str(e)}")
    
    def _update_indicators(self, symbol: str):
        """
        Met à jour les indicateurs techniques pour un symbole
        
        Args:
            symbol: Symbole pour lequel mettre à jour les indicateurs
        """
        # Simplification - dans un environnement réel, utiliser une bibliothèque comme TA-Lib
        # Ajout de la dernière bougie
        last_candle = {
            "open": self.market_data[symbol].get("open", 0),
            "high": self.market_data[symbol].get("high", 0),
            "low": self.market_data[symbol].get("low", 0),
            "close": self.market_data[symbol].get("price", 0),  # prix actuel = clôture
            "volume": self.market_data[symbol].get("volume", 0),
            "timestamp": self.market_data[symbol].get("timestamp", time.time())
        }
        
        # Ajouter la bougie aux données historiques (limité à 100 bougies)
        self.indicators[symbol]["candles"].append(last_candle)
        if len(self.indicators[symbol]["candles"]) > 100:
            self.indicators[symbol]["candles"] = self.indicators[symbol]["candles"][-100:]
        
        # Calcul des moyennes mobiles (SMA)
        closes = [candle["close"] for candle in self.indicators[symbol]["candles"]]
        self.indicators[symbol]["sma"]["fast"] = self._calculate_sma(closes, 10)
        self.indicators[symbol]["sma"]["medium"] = self._calculate_sma(closes, 25)
        self.indicators[symbol]["sma"]["slow"] = self._calculate_sma(closes, 50)
        
        # Calcul du RSI
        self.indicators[symbol]["rsi"] = self._calculate_rsi(closes, 14)
        
        # Calcul du MACD
        macd_line, macd_signal, macd_histogram = self._calculate_macd(closes)
        self.indicators[symbol]["macd"]["line"] = macd_line
        self.indicators[symbol]["macd"]["signal"] = macd_signal
        self.indicators[symbol]["macd"]["histogram"] = macd_histogram
    
    def _calculate_sma(self, data: List[float], period: int) -> List[float]:
        """
        Calcule la moyenne mobile simple (SMA)
        
        Args:
            data: Liste des prix de clôture
            period: Période de la moyenne mobile
            
        Returns:
            Liste des valeurs SMA
        """
        sma = []
        if len(data) < period:
            return sma
            
        for i in range(len(data)):
            if i < period - 1:
                sma.append(0)
            else:
                sma.append(sum(data[i-(period-1):i+1]) / period)
                
        return sma
    
    def _calculate_rsi(self, data: List[float], period: int) -> List[float]:
        """
        Calcule l'indicateur de force relative (RSI)
        
        Args:
            data: Liste des prix de clôture
            period: Période du RSI
            
        Returns:
            Liste des valeurs RSI
        """
        rsi = []
        if len(data) < period + 1:
            return rsi
            
        # Calcul des différences
        delta = []
        for i in range(1, len(data)):
            delta.append(data[i] - data[i-1])
        
        # Initialisation
        gain = [max(d, 0) for d in delta]
        loss = [max(-d, 0) for d in delta]
        
        # Calcul des moyennes
        avg_gain = sum(gain[:period]) / period
        avg_loss = sum(loss[:period]) / period
        
        # Premier RSI
        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))
        
        # Reste des RSI
        for i in range(period, len(delta)):
            avg_gain = (avg_gain * (period - 1) + gain[i]) / period
            avg_loss = (avg_loss * (period - 1) + loss[i]) / period
            
            if avg_loss == 0:
                rsi.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi.append(100 - (100 / (1 + rs)))
                
        # Padding pour que la taille corresponde aux données
        padding = [0] * period
        return padding + rsi
    
    def _calculate_macd(self, data: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[List[float], List[float], List[float]]:
        """
        Calcule la convergence/divergence des moyennes mobiles (MACD)
        
        Args:
            data: Liste des prix de clôture
            fast_period: Période de la moyenne rapide
            slow_period: Période de la moyenne lente
            signal_period: Période de la ligne de signal
            
        Returns:
            Tuple de (ligne MACD, ligne Signal, histogramme MACD)
        """
        # Calcul des EMA (Exponential Moving Average)
        ema_fast = self._calculate_ema(data, fast_period)
        ema_slow = self._calculate_ema(data, slow_period)
        
        # Calcul de la ligne MACD
        macd_line = []
        for i in range(len(data)):
            if i < slow_period - 1:
                macd_line.append(0)
            else:
                macd_line.append(ema_fast[i] - ema_slow[i])
        
        # Calcul de la ligne de signal
        signal_line = self._calculate_ema(macd_line, signal_period)
        
        # Calcul de l'histogramme
        histogram = []
        for i in range(len(macd_line)):
            if i < slow_period + signal_period - 2:
                histogram.append(0)
            else:
                histogram.append(macd_line[i] - signal_line[i])
        
        return macd_line, signal_line, histogram
    
    def _calculate_ema(self, data: List[float], period: int) -> List[float]:
        """
        Calcule la moyenne mobile exponentielle (EMA)
        
        Args:
            data: Liste des prix de clôture
            period: Période de l'EMA
            
        Returns:
            Liste des valeurs EMA
        """
        ema = []
        if len(data) < period:
            return ema
            
        # Calculer le facteur de multiplication
        multiplier = 2 / (period + 1)
        
        # La première EMA est une SMA
        sma = sum(data[:period]) / period
        ema.append(sma)
        
        # Calculer le reste des EMA
        for i in range(1, len(data) - period + 1):
            ema_value = (data[i+period-1] - ema[-1]) * multiplier + ema[-1]
            ema.append(ema_value)
            
        # Padding pour que la taille corresponde aux données
        padding = [0] * (period - 1)
        return padding + ema
    
    def _calculate_volatility(self, symbol: str) -> float:
        """
        Calcule la volatilité du marché pour un symbole
        
        Args:
            symbol: Symbole pour lequel calculer la volatilité
            
        Returns:
            Score de volatilité (0-1)
        """
        candles = self.indicators[symbol]["candles"]
        if len(candles) < 10:
            return 0.5  # Valeur par défaut
            
        # Calcul de l'ATR (Average True Range) sur 10 périodes
        tr_sum = 0
        for i in range(1, min(11, len(candles))):
            high = candles[-i]["high"]
            low = candles[-i]["low"]
            prev_close = candles[-i-1]["close"]
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_sum += tr
            
        atr = tr_sum / min(10, len(candles) - 1)
        
        # Normaliser l'ATR par rapport au prix
        current_price = candles[-1]["close"]
        normalized_atr = atr / current_price
        
        # Convertir en score de volatilité (0-1)
        # Supposons qu'un ATR normalisé de 5% = forte volatilité (score 1)
        volatility_score = min(1.0, normalized_atr * 20)
        
        return volatility_score
    
    def _detect_trend(self, symbol: str) -> float:
        """
        Détecte la tendance du marché pour un symbole
        
        Args:
            symbol: Symbole pour lequel détecter la tendance
            
        Returns:
            Score de tendance (-1 à +1, négatif = baissier, positif = haussier)
        """
        indicators = self.indicators[symbol]
        
        if len(indicators["sma"]["fast"]) < 5 or len(indicators["sma"]["slow"]) < 5:
            return 0  # Pas assez de données
        
        # Tendance basée sur les SMA
        fast_sma = indicators["sma"]["fast"][-1]
        medium_sma = indicators["sma"]["medium"][-1]
        slow_sma = indicators["sma"]["slow"][-1]
        
        sma_trend = 0
        if fast_sma > medium_sma > slow_sma:
            sma_trend = 1  # Forte tendance haussière
        elif fast_sma > medium_sma:
            sma_trend = 0.5  # Tendance haussière modérée
        elif fast_sma < medium_sma < slow_sma:
            sma_trend = -1  # Forte tendance baissière
        elif fast_sma < medium_sma:
            sma_trend = -0.5  # Tendance baissière modérée
            
        # Tendance basée sur le MACD
        macd_trend = 0
        if indicators["macd"]["histogram"] and len(indicators["macd"]["histogram"]) > 2:
            current_hist = indicators["macd"]["histogram"][-1]
            prev_hist = indicators["macd"]["histogram"][-2]
            
            if current_hist > 0 and prev_hist < current_hist:
                macd_trend = 1  # Forte tendance haussière
            elif current_hist > 0:
                macd_trend = 0.5  # Tendance haussière modérée
            elif current_hist < 0 and prev_hist > current_hist:
                macd_trend = -1  # Forte tendance baissière
            elif current_hist < 0:
                macd_trend = -0.5  # Tendance baissière modérée
                
        # Tendance basée sur le RSI
        rsi_trend = 0
        if indicators["rsi"] and len(indicators["rsi"]) > 1:
            current_rsi = indicators["rsi"][-1]
            
            if current_rsi > 70:
                rsi_trend = 0.8  # Survente (potentiel de baisse)
            elif current_rsi < 30:
                rsi_trend = -0.8  # Surachat (potentiel de hausse)
            elif current_rsi > 50:
                rsi_trend = 0.3  # Tendance haussière légère
            elif current_rsi < 50:
                rsi_trend = -0.3  # Tendance baissière légère
                
        # Combinaison des tendances (poids différents)
        overall_trend = (0.5 * sma_trend + 0.3 * macd_trend + 0.2 * rsi_trend)
        
        # Limiter entre -1 et +1
        return max(-1, min(1, overall_trend))
    
    def _update_support_resistance(self, symbol: str):
        """
        Met à jour les niveaux de support et résistance
        
        Args:
            symbol: Symbole pour lequel mettre à jour les niveaux
        """
        candles = self.indicators[symbol]["candles"]
        if len(candles) < 20:
            return
            
        # Simplification - dans un système réel, utiliser des algorithmes plus sophistiqués
        # comme la détection de pics locaux et l'analyse fractale
        
        # Recherche de pivots hauts et bas
        highs = [candle["high"] for candle in candles]
        lows = [candle["low"] for candle in candles]
        
        resistance_levels = []
        support_levels = []
        
        # Recherche simple des points pivots (simplifiée)
        for i in range(5, len(candles) - 5):
            # Pivot haut
            if all(highs[i] > highs[i-j] for j in range(1, 6)) and all(highs[i] > highs[i+j] for j in range(1, 6)):
                resistance_levels.append(highs[i])
                
            # Pivot bas
            if all(lows[i] < lows[i-j] for j in range(1, 6)) and all(lows[i] < lows[i+j] for j in range(1, 6)):
                support_levels.append(lows[i])
                
        # Regrouper les niveaux proches (tolérance de 0.5%)
        self.indicators[symbol]["resistance_levels"] = self._cluster_levels(resistance_levels, 0.005)
        self.indicators[symbol]["support_levels"] = self._cluster_levels(support_levels, 0.005)
    
    def _cluster_levels(self, levels: List[float], tolerance: float) -> List[float]:
        """
        Regroupe les niveaux proches en clusters
        
        Args:
            levels: Liste des niveaux
            tolerance: Tolérance pour le regroupement (en pourcentage)
            
        Returns:
            Liste des niveaux regroupés
        """
        if not levels:
            return []
            
        # Trier les niveaux
        sorted_levels = sorted(levels)
        
        # Initialiser les clusters
        clusters = []
        current_cluster = [sorted_levels[0]]
        
        # Parcourir les niveaux triés
        for i in range(1, len(sorted_levels)):
            # Si le niveau est proche du dernier niveau du cluster actuel
            if abs(sorted_levels[i] - current_cluster[-1]) / current_cluster[-1] <= tolerance:
                current_cluster.append(sorted_levels[i])
            else:
                # Ajouter la moyenne du cluster actuel aux clusters
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [sorted_levels[i]]
                
        # Ajouter le dernier cluster
        if current_cluster:
            clusters.append(sum(current_cluster) / len(current_cluster))
            
        return clusters
    
    def _detect_patterns(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Détecte les patterns de marché pour un symbole
        
        Args:
            symbol: Symbole pour lequel détecter les patterns
            
        Returns:
            Liste des patterns détectés
        """
        patterns = []
        candles = self.indicators[symbol]["candles"]
        
        if len(candles) < 20:
            return patterns
            
        # Exemple simple de détection de patterns
        # Dans un système réel, utiliser des algorithmes plus sophistiqués
        
        # Détection de divergences RSI
        if self._detect_rsi_divergence(symbol):
            patterns.append({
                "name": "RSI Divergence",
                "strength": 0.8,
                "direction": "bullish" if self.indicators[symbol]["rsi"][-1] < 40 else "bearish"
            })
            
        # Croisement des moyennes mobiles
        if self._detect_ma_crossover(symbol):
            patterns.append({
                "name": "MA Crossover",
                "strength": 0.7,
                "direction": "bullish" if self.indicators[symbol]["sma"]["fast"][-1] > self.indicators[symbol]["sma"]["slow"][-1] else "bearish"
            })
            
        # Croisement MACD
        if self._detect_macd_crossover(symbol):
            patterns.append({
                "name": "MACD Crossover",
                "strength": 0.65,
                "direction": "bullish" if self.indicators[symbol]["macd"]["line"][-1] > self.indicators[symbol]["macd"]["signal"][-1] else "bearish"
            })
            
        # Double bottom/top (très simplifié)
        double_pattern = self._detect_double_pattern(symbol)
        if double_pattern:
            patterns.append({
                "name": f"Double {double_pattern}",
                "strength": 0.75,
                "direction": "bullish" if double_pattern == "Bottom" else "bearish"
            })
            
        return patterns
    
    def _detect_rsi_divergence(self, symbol: str) -> bool:
        """
        Détecte les divergences RSI
        
        Args:
            symbol: Symbole à analyser
            
        Returns:
            True si une divergence est détectée, False sinon
        """
        candles = self.indicators[symbol]["candles"]
        rsi = self.indicators[symbol]["rsi"]
        
        if len(candles) < 20 or len(rsi) < 20:
            return False
            
        # Simplification - recherche de divergences basiques
        # Prix faisant des bas/hauts plus bas, mais RSI faisant des bas/hauts plus hauts
        price_downtrend = candles[-1]["close"] < candles[-10]["close"]
        rsi_uptrend = rsi[-1] > rsi[-10]
        
        price_uptrend = candles[-1]["close"] > candles[-10]["close"]
        rsi_downtrend = rsi[-1] < rsi[-10]
        
        return (price_downtrend and rsi_uptrend) or (price_uptrend and rsi_downtrend)
    
    def _detect_ma_crossover(self, symbol: str) -> bool:
        """
        Détecte les croisements de moyennes mobiles
        
        Args:
            symbol: Symbole à analyser
            
        Returns:
            True si un croisement est détecté, False sinon
        """
        fast_sma = self.indicators[symbol]["sma"]["fast"]
        slow_sma = self.indicators[symbol]["sma"]["slow"]
        
        if len(fast_sma) < 2 or len(slow_sma) < 2:
            return False
            
        # Détecter un croisement récent
        current_diff = fast_sma[-1] - slow_sma[-1]
        previous_diff = fast_sma[-2] - slow_sma[-2]
        
        return (current_diff > 0 and previous_diff < 0) or (current_diff < 0 and previous_diff > 0)
    
    def _detect_macd_crossover(self, symbol: str) -> bool:
        """
        Détecte les croisements MACD
        
        Args:
            symbol: Symbole à analyser
            
        Returns:
            True si un croisement est détecté, False sinon
        """
        macd_line = self.indicators[symbol]["macd"]["line"]
        signal_line = self.indicators[symbol]["macd"]["signal"]
        
        if len(macd_line) < 2 or len(signal_line) < 2:
            return False
            
        # Détecter un croisement récent
        current_diff = macd_line[-1] - signal_line[-1]
        previous_diff = macd_line[-2] - signal_line[-2]
        
        return (current_diff > 0 and previous_diff < 0) or (current_diff < 0 and previous_diff > 0)
    
    def _detect_double_pattern(self, symbol: str) -> Optional[str]:
        """
        Détecte les patterns double top/bottom
        
        Args:
            symbol: Symbole à analyser
            
        Returns:
            'Top', 'Bottom' ou None
        """
        candles = self.indicators[symbol]["candles"]
        
        if len(candles) < 20:
            return None
            
        # Simplification extrême - dans un système réel, utiliser des algorithmes plus sophistiqués
        lows = [candle["low"] for candle in candles[-20:]]
        highs = [candle["high"] for candle in candles[-20:]]
        
        # Rechercher deux bas similaires
        min_idx = [i for i in range(1, len(lows)-1) if lows[i] < lows[i-1] and lows[i] < lows[i+1]]
        if len(min_idx) >= 2:
            idx1, idx2 = min_idx[-2], min_idx[-1]
            if abs(lows[idx1] - lows[idx2]) / lows[idx1] < 0.02 and idx2 - idx1 >= 3:
                return "Bottom"
                
        # Rechercher deux hauts similaires
        max_idx = [i for i in range(1, len(highs)-1) if highs[i] > highs[i-1] and highs[i] > highs[i+1]]
        if len(max_idx) >= 2:
            idx1, idx2 = max_idx[-2], max_idx[-1]
            if abs(highs[idx1] - highs[idx2]) / highs[idx1] < 0.02 and idx2 - idx1 >= 3:
                return "Top"
                
        return None
    
    def _scan_for_opportunities(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Recherche des opportunités de trading pour un symbole
        
        Args:
            symbol: Symbole à analyser
            
        Returns:
            Liste des opportunités détectées
        """
        opportunities = []
        
        if symbol not in self.indicators:
            return opportunities
            
        # Données actuelles
        trend = self.indicators[symbol]["trend"]
        rsi = self.indicators[symbol]["rsi"][-1] if self.indicators[symbol]["rsi"] else 50
        macd_hist = self.indicators[symbol]["macd"]["histogram"][-1] if self.indicators[symbol]["macd"]["histogram"] else 0
        
        current_price = self.market_data[symbol]["price"] if "price" in self.market_data[symbol] else 0
        
        # Opportunité de tendance haussière
        if trend > 0.5 and rsi > 50 and rsi < 70 and macd_hist > 0:
            opportunities.append({
                "symbol": symbol,
                "type": "long",
                "strength": trend * 0.7 + 0.3,
                "entry_price": current_price,
                "stop_loss": current_price * 0.98,  # -2%
                "take_profit": current_price * 1.03,  # +3%
                "reason": "Forte tendance haussière avec confirmation MACD et RSI",
                "timestamp": time.time()
            })
        
        # Opportunité de tendance baissière
        elif trend < -0.5 and rsi < 50 and rsi > 30 and macd_hist < 0:
            opportunities.append({
                "symbol": symbol,
                "type": "short",
                "strength": abs(trend) * 0.7 + 0.3,
                "entry_price": current_price,
                "stop_loss": current_price * 1.02,  # +2%
                "take_profit": current_price * 0.97,  # -3%
                "reason": "Forte tendance baissière avec confirmation MACD et RSI",
                "timestamp": time.time()
            })
        
        # Opportunité de rebond (survente)
        elif rsi < 30 and trend > -0.3:
            opportunities.append({
                "symbol": symbol,
                "type": "long_reversal",
                "strength": (30 - rsi) / 30 * 0.8,
                "entry_price": current_price,
                "stop_loss": current_price * 0.985,  # -1.5%
                "take_profit": current_price * 1.02,  # +2%
                "reason": "Condition de survente avec potentiel de rebond",
                "timestamp": time.time()
            })
        
        # Opportunité de retournement (surachat)
        elif rsi > 70 and trend < 0.3:
            opportunities.append({
                "symbol": symbol,
                "type": "short_reversal",
                "strength": (rsi - 70) / 30 * 0.8,
                "entry_price": current_price,
                "stop_loss": current_price * 1.015,  # +1.5%
                "take_profit": current_price * 0.98,  # -2%
                "reason": "Condition de surachat avec potentiel de retournement",
                "timestamp": time.time()
            })
            
        return opportunities
    
    def _publish_market_data(self, symbol: str):
        """
        Publie les données de marché analysées
        
        Args:
            symbol: Symbole pour lequel publier les données
        """
        if symbol not in self.market_data or symbol not in self.indicators:
            return
            
        # Préparer les données de marché enrichies
        market_data = {
            "symbol": symbol,
            "price": self.market_data[symbol].get("price", 0),
            "volume": self.market_data[symbol].get("volume", 0),
            "timestamp": time.time(),
            "volatility": self.indicators[symbol]["volatility"],
            "trend": self.indicators[symbol]["trend"],
            "rsi": self.indicators[symbol]["rsi"][-1] if self.indicators[symbol]["rsi"] else None,
            "sma": {
                "fast": self.indicators[symbol]["sma"]["fast"][-1] if self.indicators[symbol]["sma"]["fast"] else None,
                "medium": self.indicators[symbol]["sma"]["medium"][-1] if self.indicators[symbol]["sma"]["medium"] else None,
                "slow": self.indicators[symbol]["sma"]["slow"][-1] if self.indicators[symbol]["sma"]["slow"] else None
            },
            "support_levels": self.indicators[symbol]["support_levels"],
            "resistance_levels": self.indicators[symbol]["resistance_levels"]
        }
        
        # Publier sur le bus d'événements
        self.event_bus.publish("market_data_update", market_data)
    
    def _handle_raw_market_data(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les données brutes de marché
        
        Args:
            data: Données brutes de marché
        """
        symbol = data.get("symbol")
        if not symbol or symbol not in self.watched_symbols:
            return
            
        # Mettre à jour les données de marché
        self.market_data[symbol] = data
    
    def _handle_market_insight_request(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les demandes d'analyse de marché
        
        Args:
            data: Données de la demande
        """
        request_id = data.get("request_id", "unknown")
        symbol = data.get("symbol")
        insight_type = data.get("insight_type", "general")
        
        if not symbol or symbol not in self.watched_symbols:
            self.event_bus.publish("market_insight_response", {
                "request_id": request_id,
                "error": f"Symbole {symbol} non surveillé",
                "timestamp": time.time()
            })
            return
        
        # Générer les informations demandées
        insights = self._generate_market_insights(symbol, insight_type)
        
        # Publier la réponse
        self.event_bus.publish("market_insight_response", {
            "request_id": request_id,
            "symbol": symbol,
            "insights": insights,
            "timestamp": time.time()
        })
    
    def _generate_market_insights(self, symbol: str, insight_type: str) -> Dict[str, Any]:
        """
        Génère des analyses de marché pour un symbole
        
        Args:
            symbol: Symbole à analyser
            insight_type: Type d'analyse demandée
            
        Returns:
            Dictionnaire contenant les analyses
        """
        if symbol not in self.indicators:
            return {"error": "Données insuffisantes pour l'analyse"}
            
        insights = {
            "symbol": symbol,
            "price": self.market_data[symbol].get("price", 0),
            "timestamp": time.time()
        }
        
        # Analyse générale du marché
        if insight_type == "general" or insight_type == "all":
            insights["general"] = {
                "trend": self._get_trend_description(symbol),
                "volatility": self._get_volatility_description(symbol),
                "momentum": self._get_momentum_description(symbol),
                "support_resistance": self._get_sr_description(symbol)
            }
            
        # Analyse technique détaillée
        if insight_type == "technical" or insight_type == "all":
            insights["technical"] = {
                "rsi": self._get_rsi_analysis(symbol),
                "macd": self._get_macd_analysis(symbol),
                "moving_averages": self._get_ma_analysis(symbol),
                "patterns": self._detect_patterns(symbol)
            }
            
        # Recommandations de trading
        if insight_type == "recommendations" or insight_type == "all":
            insights["recommendations"] = self._get_trading_recommendations(symbol)
            
        return insights
    
    def _get_trend_description(self, symbol: str) -> Dict[str, Any]:
        """
        Génère une description de la tendance
        
        Args:
            symbol: Symbole à analyser
            
        Returns:
            Description de la tendance
        """
        trend = self.indicators[symbol]["trend"]
        
        trend_strength = abs(trend)
        if trend_strength < 0.3:
            strength_desc = "faible"
        elif trend_strength < 0.6:
            strength_desc = "modérée"
        else:
            strength_desc = "forte"
            
        direction = "haussière" if trend > 0 else "baissière" if trend < 0 else "neutre"
        
        return {
            "direction": direction,
            "strength": strength_desc,
            "value": trend,
            "description": f"Tendance {direction} {strength_desc}"
        }
    
    def _get_volatility_description(self, symbol: str) -> Dict[str, Any]:
        """
        Génère une description de la volatilité
        
        Args:
            symbol: Symbole à analyser
            
        Returns:
            Description de la volatilité
        """
        volatility = self.indicators[symbol]["volatility"]
        
        if volatility < 0.3:
            desc = "faible"
        elif volatility < 0.6:
            desc = "modérée"
        else:
            desc = "élevée"
            
        return {
            "level": desc,
            "value": volatility,
            "description": f"Volatilité {desc}"
        }
    
    def _get_momentum_description(self, symbol: str) -> Dict[str, Any]:
        """
        Génère une description du momentum
        
        Args:
            symbol: Symbole à analyser
            
        Returns:
            Description du momentum
        """
        rsi = self.indicators[symbol]["rsi"][-1] if self.indicators[symbol]["rsi"] else 50
        macd_hist = self.indicators[symbol]["macd"]["histogram"][-1] if self.indicators[symbol]["macd"]["histogram"] else 0
        
        momentum_value = (rsi - 50) / 50 + (macd_hist * 10 if abs(macd_hist) < 0.1 else macd_hist)
        momentum_value = max(-1, min(1, momentum_value))
        
        if abs(momentum_value) < 0.3:
            strength = "faible"
        elif abs(momentum_value) < 0.6:
            strength = "modéré"
        else:
            strength = "fort"
            
        direction = "haussier" if momentum_value > 0 else "baissier" if momentum_value < 0 else "neutre"
        
        return {
            "direction": direction,
            "strength": strength,
            "value": momentum_value,
            "description": f"Momentum {direction} {strength}"
        }
    
    def _get_sr_description(self, symbol: str) -> Dict[str, Any]:
        """
        Génère une description des supports et résistances
        
        Args:
            symbol: Symbole à analyser
            
        Returns:
            Description des supports et résistances
        """
        supports = self.indicators[symbol]["support_levels"]
        resistances = self.indicators[symbol]["resistance_levels"]
        current_price = self.market_data[symbol].get("price", 0)
        
        # Trouver le support et la résistance les plus proches
        closest_support = max([s for s in supports if s < current_price], default=0)
        closest_resistance = min([r for r in resistances if r > current_price], default=float('inf'))
        
        return {
            "closest_support": closest_support,
            "closest_resistance": closest_resistance,
            "support_levels": supports,
            "resistance_levels": resistances,
            "support_distance": (current_price - closest_support) / current_price if closest_support > 0 else None,
            "resistance_distance": (closest_resistance - current_price) / current_price if closest_resistance < float('inf') else None
        }
    
    def _get_rsi_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Génère une analyse RSI
        
        Args:
            symbol: Symbole à analyser
            
        Returns:
            Analyse RSI
        """
        rsi = self.indicators[symbol]["rsi"][-1] if self.indicators[symbol]["rsi"] else 50
        
        if rsi > 70:
            condition = "surachat"
            signal = "potentiel de baisse"
        elif rsi < 30:
            condition = "survente"
            signal = "potentiel de hausse"
        elif rsi > 60:
            condition = "force"
            signal = "tendance haussière"
        elif rsi < 40:
            condition = "faiblesse"
            signal = "tendance baissière"
        else:
            condition = "neutre"
            signal = "pas de tendance claire"
            
        return {
            "value": rsi,
            "condition": condition,
            "signal": signal,
            "description": f"RSI à {rsi:.1f} indique une condition de {condition} - {signal}"
        }
    
    def _get_macd_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Génère une analyse MACD
        
        Args:
            symbol: Symbole à analyser
            
        Returns:
            Analyse MACD
        """
        macd = self.indicators[symbol]["macd"]
        if not macd["line"] or not macd["signal"] or not macd["histogram"]:
            return {"description": "Données MACD insuffisantes"}
            
        macd_line = macd["line"][-1]
        signal_line = macd["signal"][-1]
        histogram = macd["histogram"][-1]
        
        if macd_line > signal_line and histogram > 0 and histogram > macd["histogram"][-2]:
            signal = "bullish_strong"
            desc = "Signal d'achat fort (MACD au-dessus du signal et croissant)"
        elif macd_line > signal_line:
            signal = "bullish"
            desc = "Signal d'achat (MACD au-dessus du signal)"
        elif macd_line < signal_line and histogram < 0 and histogram < macd["histogram"][-2]:
            signal = "bearish_strong"
            desc = "Signal de vente fort (MACD en-dessous du signal et décroissant)"
        elif macd_line < signal_line:
            signal = "bearish"
            desc = "Signal de vente (MACD en-dessous du signal)"
        else:
            signal = "neutral"
            desc = "Pas de signal clair"
            
        return {
            "macd_line": macd_line,
            "signal_line": signal_line,
            "histogram": histogram,
            "signal": signal,
            "description": desc
        }
    
    def _get_ma_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Génère une analyse des moyennes mobiles
        
        Args:
            symbol: Symbole à analyser
            
        Returns:
            Analyse des moyennes mobiles
        """
        sma = self.indicators[symbol]["sma"]
        if not sma["fast"] or not sma["medium"] or not sma["slow"]:
            return {"description": "Données SMA insuffisantes"}
            
        fast = sma["fast"][-1]
        medium = sma["medium"][-1]
        slow = sma["slow"][-1]
        current_price = self.market_data[symbol].get("price", 0)
        
        ma_status = []
        signals = []
        
        if current_price > fast:
            ma_status.append("au-dessus de la MA rapide")
            signals.append("bullish")
        else:
            ma_status.append("en-dessous de la MA rapide")
            signals.append("bearish")
            
        if fast > medium > slow:
            structure = "structure haussière"
            signals.append("bullish_structure")
        elif fast < medium < slow:
            structure = "structure baissière"
            signals.append("bearish_structure")
        else:
            structure = "structure mixte"
            signals.append("mixed_structure")
            
        if abs(fast - medium) / medium < 0.005:
            signals.append("ma_squeeze")
            ma_status.append("convergence des MA (potentiel mouvement)")
            
        return {
            "fast": fast,
            "medium": medium,
            "slow": slow,
            "structure": structure,
            "status": " et ".join(ma_status),
            "signals": signals,
            "description": f"Prix {ma_status[0]}, {structure}{', ' + ma_status[1] if len(ma_status) > 1 else ''}"
        }
    
    def _get_trading_recommendations(self, symbol: str) -> Dict[str, Any]:
        """
        Génère des recommandations de trading
        
        Args:
            symbol: Symbole à analyser
            
        Returns:
            Recommandations de trading
        """
        opportunities = self._scan_for_opportunities(symbol)
        
        if not opportunities:
            action = "hold"
            confidence = 0.5
            reason = "Pas de signal fort détecté"
        else:
            # Prendre l'opportunité la plus forte
            best_opp = max(opportunities, key=lambda x: x["strength"])
            action = best_opp["type"]
            confidence = best_opp["strength"]
            reason = best_opp["reason"]
            
        return {
            "action": action,
            "confidence": confidence,
            "reason": reason,
            "entry": self.market_data[symbol].get("price", 0),
            "stop_loss": next((opp["stop_loss"] for opp in opportunities if opp["type"] == action), None),
            "take_profit": next((opp["take_profit"] for opp in opportunities if opp["type"] == action), None)
        }
    
    def _handle_add_watched_symbol(self, data: Dict[str, Any]):
        """
        Gestionnaire pour l'ajout d'un symbole à surveiller
        
        Args:
            data: Données du symbole à ajouter
        """
        symbol = data.get("symbol")
        if not symbol:
            return
            
        if symbol not in self.watched_symbols:
            self.watched_symbols.append(symbol)
            self.logger.info(f"Ajout du symbole à surveiller: {symbol}")
    
    def _handle_remove_watched_symbol(self, data: Dict[str, Any]):
        """
        Gestionnaire pour la suppression d'un symbole à surveiller
        
        Args:
            data: Données du symbole à supprimer
        """
        symbol = data.get("symbol")
        if not symbol:
            return
            
        if symbol in self.watched_symbols:
            self.watched_symbols.remove(symbol)
            self.logger.info(f"Suppression du symbole surveillé: {symbol}")
            
            # Nettoyage des données associées
            if symbol in self.market_data:
                del self.market_data[symbol]
            if symbol in self.indicators:
                del self.indicators[symbol]
            if symbol in self.last_analysis:
                del self.last_analysis[symbol]

if __name__ == "__main__":
    # Test simple de la surveillance de marché
    vision = FlowVisionMarket()
    vision.start()
    
    # Simuler des données de marché
    vision._handle_raw_market_data({
        "symbol": "BTC/USDT",
        "price": 48000,
        "high": 48500,
        "low": 47500,
        "open": 47800,
        "volume": 5000,
        "timestamp": time.time()
    })
    
    time.sleep(2)  # Attente pour traitement
    vision.stop()
