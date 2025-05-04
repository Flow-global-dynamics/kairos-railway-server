#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowByteBeat.py - Module de scalping rapide Bybit / Kraken pour FlowGlobalDynamics™
"""

import logging
import time
import threading
import json
import random
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

class FlowByteBeat:
    """
    Module de scalping rapide pour Bybit et Kraken
    """
    
    def __init__(self):
        """Initialisation du FlowByteBeat"""
        self.running = False
        self.threads = {}
        self.logger = self._setup_logger()
        self.event_bus = get_event_bus()
        self.market_data = {}
        self.scalp_opportunities = []
        self.active_trades = {}
        self.config = self._load_configuration()
        self.exchange_status = {
            "bybit": {"connected": False, "last_update": 0},
            "kraken": {"connected": False, "last_update": 0}
        }
        self.performance_metrics = {
            "trades_executed": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_profit": 0.0,
            "avg_holding_time": 0.0
        }
        
    def _setup_logger(self):
        """Configuration du logger"""
        logger = logging.getLogger("FlowByteBeat")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Charge la configuration du module
        
        Returns:
            Configuration du module
        """
        # Configuration par défaut
        default_config = {
            "exchanges": {
                "bybit": {
                    "enabled": True,
                    "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
                    "max_positions": 3,
                    "position_size_usd": 100,
                    "max_leverage": 5
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
            },
            "execution": {
                "order_types": ["market", "limit"],
                "preferred_order_type": "limit",
                "max_retry_attempts": 3,
                "price_improvement_ticks": 1
            },
            "risk_management": {
                "max_daily_trades": 50,
                "max_concurrent_trades": 5,
                "max_daily_drawdown_percent": 5,
                "stop_after_consecutive_losses": 5
            },
            "technical_filters": {
                "moving_average_periods": [10, 20, 50],
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "min_volume": 100000
            }
        }
        
        try:
            # Tenter de charger depuis un fichier (désactivé pour l'exemple)
            # with open("byte_beat_config.json", "r") as f:
            #     return json.load(f)
            return default_config
        except Exception as e:
            self.logger.warning(f"Impossible de charger la configuration: {str(e)}. Utilisation des valeurs par défaut.")
            return default_config
    
    def start(self):
        """Démarrage du module de scalping"""
        if self.running:
            self.logger.warning("FlowByteBeat est déjà en cours d'exécution")
            return
            
        self.running = True
        
        # Démarrage des threads de scalping
        self._start_scalping_threads()
        
        self._register_events()
        self.logger.info("FlowByteBeat démarré")
        
    def stop(self):
        """Arrêt du module de scalping"""
        if not self.running:
            self.logger.warning("FlowByteBeat n'est pas en cours d'exécution")
            return
            
        self.running = False
        
        # Fermer les positions ouvertes
        self._close_all_positions("Module arrêté")
        
        # Arrêt des threads de scalping
        for thread_name, thread in self.threads.items():
            if thread and thread.is_alive():
                thread.join(timeout=2.0)
                self.logger.debug(f"Thread {thread_name} arrêté")
        
        self._unregister_events()
        self.logger.info("FlowByteBeat arrêté")
    
    def _start_scalping_threads(self):
        """Démarre les threads de scalping"""
        # Thread de surveillance du marché
        self.threads["market_watcher"] = threading.Thread(
            target=self._market_watcher_loop, 
            daemon=True
        )
        self.threads["market_watcher"].start()
        
        # Thread de détection d'opportunités
        self.threads["opportunity_detector"] = threading.Thread(
            target=self._opportunity_detector_loop, 
            daemon=True
        )
        self.threads["opportunity_detector"].start()
        
        # Thread d'exécution de trades
        self.threads["trade_executor"] = threading.Thread(
            target=self._trade_executor_loop, 
            daemon=True
        )
        self.threads["trade_executor"].start()
        
        # Thread de gestion des positions
        self.threads["position_manager"] = threading.Thread(
            target=self._position_manager_loop, 
            daemon=True
        )
        self.threads["position_manager"].start()
        
        # Thread de connexion aux échanges
        self.threads["exchange_connector"] = threading.Thread(
            target=self._exchange_connector_loop, 
            daemon=True
        )
        self.threads["exchange_connector"].start()
    
    def _register_events(self):
        """Enregistrement des abonnements aux événements"""
        self.event_bus.subscribe("market_data_update", self._handle_market_data)
        self.event_bus.subscribe("trade_signal", self._handle_trade_signal)
        self.event_bus.subscribe("risk_action", self._handle_risk_action)
        self.event_bus.subscribe("scalping_config_update", self._handle_config_update)
    
    def _unregister_events(self):
        """Désenregistrement des abonnements aux événements"""
        self.event_bus.unsubscribe("market_data_update", self._handle_market_data)
        self.event_bus.unsubscribe("trade_signal", self._handle_trade_signal)
        self.event_bus.unsubscribe("risk_action", self._handle_risk_action)
        self.event_bus.unsubscribe("scalping_config_update", self._handle_config_update)
    
    def _market_watcher_loop(self):
        """Boucle de surveillance du marché"""
        while self.running:
            try:
                # Surveiller les marchés actifs pour les deux échanges
                for exchange, config in self.config["exchanges"].items():
                    if config["enabled"] and self.exchange_status[exchange]["connected"]:
                        for symbol in config["symbols"]:
                            self._update_market_data(exchange, symbol)
                
                time.sleep(0.2)  # Mise à jour rapide pour le scalping
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de surveillance du marché: {str(e)}")
                time.sleep(1)
    
    def _opportunity_detector_loop(self):
        """Boucle de détection d'opportunités de scalping"""
        while self.running:
            try:
                # Réinitialiser les opportunités
                self.scalp_opportunities = []
                
                # Analyser chaque symbole pour des opportunités de scalping
                for exchange, config in self.config["exchanges"].items():
                    if config["enabled"] and self.exchange_status[exchange]["connected"]:
                        for symbol in config["symbols"]:
                            self._detect_scalping_opportunities(exchange, symbol)
                
                # Trier les opportunités par score
                if self.scalp_opportunities:
                    self.scalp_opportunities.sort(key=lambda x: x["score"], reverse=True)
                    
                    # Publier les meilleures opportunités
                    top_opportunities = self.scalp_opportunities[:3]
                    self.event_bus.publish("scalping_opportunities", {
                        "opportunities": top_opportunities,
                        "timestamp": time.time()
                    })
                
                time.sleep(0.5)  # Analyse fréquente mais pas trop intensive
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de détection d'opportunités: {str(e)}")
                time.sleep(1)
    
    def _trade_executor_loop(self):
        """Boucle d'exécution des trades"""
        while self.running:
            try:
                # Vérifier si nous pouvons exécuter de nouveaux trades
                if self._can_execute_new_trades():
                    # Exécuter les meilleures opportunités
                    for opportunity in self.scalp_opportunities[:2]:  # Limiter aux 2 meilleures
                        if self._validate_trading_conditions(opportunity):
                            self._execute_trade(opportunity)
                            break  # Exécuter un trade à la fois
                
                time.sleep(0.1)  # Vérification très fréquente
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle d'exécution des trades: {str(e)}")
                time.sleep(1)
    
    def _position_manager_loop(self):
        """Boucle de gestion des positions"""
        while self.running:
            try:
                # Gérer les positions actives
                trades_to_remove = []
                
                for trade_id, trade in self.active_trades.items():
                    # Vérifier si le trade a expiré (dépassé le temps de détention maximal)
                    current_time = time.time()
                    holding_time = current_time - trade["entry_time"]
                    
                    if holding_time > self.config["scalping"]["max_holding_time_seconds"]:
                        self._close_position(trade_id, "timeout")
                        trades_to_remove.append(trade_id)
                        continue
                    
                    # Vérifier si le trade a atteint l'objectif de profit
                    exchange = trade["exchange"]
                    symbol = trade["symbol"]
                    
                    if symbol in self.market_data.get(exchange, {}):
                        current_price = self.market_data[exchange][symbol].get("price", 0)
                        
                        # Calculer le profit actuel
                        if trade["direction"] == "long":
                            profit_percent = (current_price - trade["entry_price"]) / trade["entry_price"] * 100
                        else:  # short
                            profit_percent = (trade["entry_price"] - current_price) / trade["entry_price"] * 100
                        
                        # Vérifier si le profit cible est atteint
                        if profit_percent >= self.config["scalping"]["min_profit_percent"]:
                            self._close_position(trade_id, "take_profit")
                            trades_to_remove.append(trade_id)
                        
                        # Vérifier si la perte maximale est atteinte
                        elif profit_percent <= -self.config["scalping"]["max_loss_percent"]:
                            self._close_position(trade_id, "stop_loss")
                            trades_to_remove.append(trade_id)
                
                # Supprimer les trades fermés
                for trade_id in trades_to_remove:
                    if trade_id in self.active_trades:
                        del self.active_trades[trade_id]
                
                time.sleep(0.2)  # Vérification fréquente
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de gestion des positions: {str(e)}")
                time.sleep(1)
    
    def _exchange_connector_loop(self):
        """Boucle de connexion aux échanges"""
        while self.running:
            try:
                # Simuler les connexions aux échanges
                for exchange in self.exchange_status:
                    if self.config["exchanges"].get(exchange, {}).get("enabled", False):
                        if not self.exchange_status[exchange]["connected"]:
                            self._connect_to_exchange(exchange)
                        else:
                            # Vérifier si la connexion est toujours active
                            last_update = self.exchange_status[exchange]["last_update"]
                            if time.time() - last_update > 30:  # 30 secondes sans mise à jour
                                self.logger.warning(f"Connexion à {exchange} potentiellement perdue. Tentative de reconnexion.")
                                self._connect_to_exchange(exchange)
                
                time.sleep(5)  # Vérification périodique
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de connexion aux échanges: {str(e)}")
                time.sleep(10)
    
    def _connect_to_exchange(self, exchange: str):
        """
        Établit une connexion à un échange
        
        Args:
            exchange: Nom de l'échange
        """
        try:
            self.logger.info(f"Connexion à l'échange {exchange}...")
            
            # Simuler une connexion réussie
            # Dans un système réel, utiliser les API des échanges
            time.sleep(1)  # Simuler le délai de connexion
            
            # Marquer comme connecté
            self.exchange_status[exchange]["connected"] = True
            self.exchange_status[exchange]["last_update"] = time.time()
            
            self.logger.info(f"Connexion à {exchange} établie avec succès")
            
            # Publier l'état de la connexion
            self.event_bus.publish("exchange_connection", {
                "exchange": exchange,
                "status": "connected",
                "timestamp": time.time()
            })
        except Exception as e:
            self.logger.error(f"Erreur lors de la connexion à {exchange}: {str(e)}")
            
            # Marquer comme déconnecté
            self.exchange_status[exchange]["connected"] = False
            
            # Publier l'état de la connexion
            self.event_bus.publish("exchange_connection", {
                "exchange": exchange,
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            })
    
    def _update_market_data(self, exchange: str, symbol: str):
        """
        Met à jour les données de marché pour un symbole
        
        Args:
            exchange: Nom de l'échange
            symbol: Symbole à mettre à jour
        """
        # Dans un système réel, récupérer les données depuis l'API de l'échange
        # Ici, nous simulons des données pour l'exemple
        
        # Initialiser le dictionnaire d'échange si nécessaire
        if exchange not in self.market_data:
            self.market_data[exchange] = {}
        
        # Récupérer les données précédentes si disponibles
        prev_data = self.market_data[exchange].get(symbol, {})
        prev_price = prev_data.get("price", 1000 + random.random() * 100)
        
        # Simuler une petite variation de prix pour le scalping
        price_change = (random.random() - 0.5) * 2 * prev_price * 0.001  # Max ±0.1%
        new_price = prev_price + price_change
        
        # Créer de nouvelles données de marché
        self.market_data[exchange][symbol] = {
            "price": new_price,
            "bid": new_price - new_price * 0.0001,  # Simuler un petit spread
            "ask": new_price + new_price * 0.0001,
            "volume": 1000000 + random.random() * 500000,
            "timestamp": time.time()
        }
        
        # Mettre à jour le timestamp de la dernière mise à jour de l'échange
        self.exchange_status[exchange]["last_update"] = time.time()
    
    def _detect_scalping_opportunities(self, exchange: str, symbol: str):
        """
        Détecte les opportunités de scalping pour un symbole
        
        Args:
            exchange: Nom de l'échange
            symbol: Symbole à analyser
        """
        if exchange not in self.market_data or symbol not in self.market_data[exchange]:
            return
        
        market_data = self.market_data[exchange][symbol]
        
        # Calculer le spread en pourcentage
        bid = market_data.get("bid", 0)
        ask = market_data.get("ask", 0)
        
        if bid == 0 or ask == 0:
            return
        
        spread_percent = (ask - bid) / bid * 100
        
        # Vérifier si le spread est acceptable
        if spread_percent > self.config["scalping"]["max_spread_percent"]:
            return
        
        # Dans un système réel, calculer des indicateurs comme le RSI, MACD, etc.
        # Simuler des indicateurs pour l'exemple
        rsi = random.uniform(20, 80)
        volume_ok = market_data.get("volume", 0) > self.config["technical_filters"]["min_volume"]
        
        # Détecter les opportunités long et short
        long_opportunity = rsi < self.config["technical_filters"]["rsi_oversold"] and volume_ok
        short_opportunity = rsi > self.config["technical_filters"]["rsi_overbought"] and volume_ok
        
        # Calculer un score de qualité de l'opportunité
        if long_opportunity:
            score = (self.config["technical_filters"]["rsi_oversold"] - rsi) / 10
            
            # Ajouter l'opportunité
            self.scalp_opportunities.append({
                "exchange": exchange,
                "symbol": symbol,
                "direction": "long",
                "entry_price": ask,
                "score": score,
                "timestamp": time.time(),
                "indicators": {
                    "rsi": rsi,
                    "volume": market_data.get("volume", 0)
                }
            })
        
        if short_opportunity:
            score = (rsi - self.config["technical_filters"]["rsi_overbought"]) / 10
            
            # Ajouter l'opportunité
            self.scalp_opportunities.append({
                "exchange": exchange,
                "symbol": symbol,
                "direction": "short",
                "entry_price": bid,
                "score": score,
                "timestamp": time.time(),
                "indicators": {
                    "rsi": rsi,
                    "volume": market_data.get("volume", 0)
                }
            })
    
    def _can_execute_new_trades(self) -> bool:
        """
        Vérifie si de nouveaux trades peuvent être exécutés
        
        Returns:
            True si de nouveaux trades peuvent être exécutés, False sinon
        """
        # Vérifier le nombre de trades actifs
        if len(self.active_trades) >= self.config["risk_management"]["max_concurrent_trades"]:
            return False
        
        # Vérifier le nombre de trades quotidiens
        daily_trades = self.performance_metrics["trades_executed"]
        if daily_trades >= self.config["risk_management"]["max_daily_trades"]:
            return False
        
        # Vérifier les pertes consécutives
        consecutive_losses = 0
        
        # Si nous avons des métriques de performance
        if self.performance_metrics["trades_executed"] > 0:
            # On pourrait stocker un historique des trades pour calculer les pertes consécutives
            # Ici, on simule une valeur
            consecutive_losses = random.randint(0, 3)
            
        if consecutive_losses >= self.config["risk_management"]["stop_after_consecutive_losses"]:
            return False
        
        return True
    
    def _validate_trading_conditions(self, opportunity: Dict[str, Any]) -> bool:
        """
        Valide les conditions de trading pour une opportunité
        
        Args:
            opportunity: Opportunité de trading
            
        Returns:
            True si les conditions sont valides, False sinon
        """
        exchange = opportunity["exchange"]
        symbol = opportunity["symbol"]
        direction = opportunity["direction"]
        
        # Vérifier si nous avons déjà une position sur ce symbole
        for trade in self.active_trades.values():
            if trade["exchange"] == exchange and trade["symbol"] == symbol:
                return False
        
        # Vérifier si l'opportunité n'est pas trop ancienne (max 2 secondes)
        if time.time() - opportunity["timestamp"] > 2:
            return False
        
        # Vérifier si nous avons atteint le nombre maximum de positions pour cet échange
        exchange_positions = sum(1 for t in self.active_trades.values() if t["exchange"] == exchange)
        max_positions = self.config["exchanges"][exchange]["max_positions"]
        
        if exchange_positions >= max_positions:
            return False
        
        # Dans un système réel, effectuer d'autres validations comme:
        # - Vérifier les volumes disponibles
        # - Confirmer les signaux avec d'autres indicateurs
        # - Vérifier les tendances de plus long terme
        
        return True
    
    def _execute_trade(self, opportunity: Dict[str, Any]):
        """
        Exécute un trade à partir d'une opportunité
        
        Args:
            opportunity: Opportunité de trading
        """
        exchange = opportunity["exchange"]
        symbol = opportunity["symbol"]
        direction = opportunity["direction"]
        entry_price = opportunity["entry_price"]
        
        # Générer un ID de trade unique
        trade_id = f"scalp_{exchange}_{symbol}_{int(time.time())}_{random.randint(1000, 9999)}"
        
        self.logger.info(f"Exécution d'un trade {direction} sur {exchange} {symbol} à {entry_price}")
        
        # Calculer la taille de la position
        position_size_usd = self.config["exchanges"][exchange]["position_size_usd"]
        position_size = position_size_usd / entry_price
        
        # Dans un système réel, placer l'ordre via l'API de l'échange
        # Ici, nous simulons une exécution réussie
        
        # Créer un objet trade
        trade = {
            "id": trade_id,
            "exchange": exchange,
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "position_size": position_size,
            "position_size_usd": position_size_usd,
            "entry_time": time.time(),
            "status": "open"
        }
        
        # Ajouter aux trades actifs
        self.active_trades[trade_id] = trade
        
        # Mettre à jour les métriques
        self.performance_metrics["trades_executed"] += 1
        
        # Publier l'événement d'ouverture de position
        self.event_bus.publish("position_opened", {
            "position_id": trade_id,
            "exchange": exchange,
            "symbol": symbol,
            "direction": direction,
            "size": position_size,
            "size_usd": position_size_usd,
            "entry_price": entry_price,
            "timestamp": time.time()
        })
    
    def _close_position(self, trade_id: str, reason: str):
        """
        Ferme une position
        
        Args:
            trade_id: ID du trade à fermer
            reason: Raison de la fermeture
        """
        if trade_id not in self.active_trades:
            self.logger.warning(f"Tentative de fermer une position inexistante: {trade_id}")
            return
            
        trade = self.active_trades[trade_id]
        exchange = trade["exchange"]
        symbol = trade["symbol"]
        
        # Récupérer le prix de sortie actuel
        exit_price = 0
        if exchange in self.market_data and symbol in self.market_data[exchange]:
            if trade["direction"] == "long":
                exit_price = self.market_data[exchange][symbol].get("bid", 0)
            else:  # short
                exit_price = self.market_data[exchange][symbol].get("ask", 0)
        
        if exit_price == 0:
            # Prix de sortie non disponible, utiliser le dernier prix connu
            exit_price = self.market_data[exchange][symbol].get("price", trade["entry_price"])
        
        # Calculer le profit
        if trade["direction"] == "long":
            profit_percent = (exit_price - trade["entry_price"]) / trade["entry_price"] * 100
        else:  # short
            profit_percent = (trade["entry_price"] - exit_price) / trade["entry_price"] * 100
            
        profit_usd = trade["position_size_usd"] * profit_percent / 100
        
        self.logger.info(f"Fermeture de la position {trade_id} sur {exchange} {symbol}: {profit_percent:.2f}% ({profit_usd:.2f} USD) - Raison: {reason}")
        
        # Dans un système réel, fermer la position via l'API de l'échange
        
        # Mettre à jour les métriques
        self.performance_metrics["total_profit"] += profit_usd
        
        if profit_usd > 0:
            self.performance_metrics["winning_trades"] += 1
        else:
            self.performance_metrics["losing_trades"] += 1
            
        # Calculer le temps de détention
        holding_time = time.time() - trade["entry_time"]
        
        # Mettre à jour le temps de détention moyen
        total_trades = self.performance_metrics["winning_trades"] + self.performance_metrics["losing_trades"]
        current_avg = self.performance_metrics["avg_holding_time"]
        
        if total_trades > 1:
            self.performance_metrics["avg_holding_time"] = (current_avg * (total_trades - 1) + holding_time) / total_trades
        else:
            self.performance_metrics["avg_holding_time"] = holding_time
        
        # Publier l'événement de fermeture de position
        self.event_bus.publish("position_closed", {
            "position_id": trade_id,
            "exchange": exchange,
            "symbol": symbol,
            "direction": trade["direction"],
            "entry_price": trade["entry_price"],
            "exit_price": exit_price,
            "size": trade["position_size"],
            "size_usd": trade["position_size_usd"],
            "profit_percent": profit_percent,
            "profit_usd": profit_usd,
            "holding_time": holding_time,
            "reason": reason,
            "timestamp": time.time()
        })
        
        # Publier le résultat du trade
        self.event_bus.publish("trade_result", {
            "trade_id": trade_id,
            "exchange": exchange,
            "symbol": symbol,
            "direction": trade["direction"],
            "profit": profit_usd,
            "profit_percent": profit_percent,
            "strategy": "scalping",
            "timestamp": time.time()
        })
    
    def _close_all_positions(self, reason: str):
        """
        Ferme toutes les positions actives
        
        Args:
            reason: Raison de la fermeture
        """
        trade_ids = list(self.active_trades.keys())
        
        for trade_id in trade_ids:
            self._close_position(trade_id, reason)
    
    def _handle_market_data(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les mises à jour de données de marché
        
        Args:
            data: Données de marché
        """
        symbol = data.get("symbol")
        
        # Déterminer pour quel échange cette donnée est pertinente
        for exchange, config in self.config["exchanges"].items():
            if symbol in config["symbols"]:
                # Initialiser le dictionnaire d'échange si nécessaire
                if exchange not in self.market_data:
                    self.market_data[exchange] = {}
                
                # Mettre à jour les données
                self.market_data[exchange][symbol] = data
                
                # Mettre à jour le timestamp de la dernière mise à jour de l'échange
                self.exchange_status[exchange]["last_update"] = time.time()
    
    def _handle_trade_signal(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les signaux de trading
        
        Args:
            data: Données du signal
        """
        signal_type = data.get("type")
        symbol = data.get("symbol")
        direction = data.get("direction")
        exchange = data.get("exchange", "bybit")  # Par défaut
        
        if not symbol or not direction:
            return
            
        # Vérifier si le signal est pour un scalping
        if signal_type == "scalp" and exchange in self.config["exchanges"] and symbol in self.config["exchanges"][exchange]["symbols"]:
            # Créer une opportunité à partir du signal
            if exchange in self.market_data and symbol in self.market_data[exchange]:
                market_data = self.market_data[exchange][symbol]
                
                entry_price = 0
                if direction == "long":
                    entry_price = market_data.get("ask", 0)
                else:
                    entry_price = market_data.get("bid", 0)
                
                if entry_price > 0:
                    opportunity = {
                        "exchange": exchange,
                        "symbol": symbol,
                        "direction": direction,
                        "entry_price": entry_price,
                        "score": 0.9,  # Score élevé pour les signaux externes
                        "timestamp": time.time(),
                        "indicators": {
                            "source": "external_signal"
                        }
                    }
                    
                    # Ajouter l'opportunité en priorité
                    self.scalp_opportunities.insert(0, opportunity)
                    
                    self.logger.info(f"Signal de scalping reçu pour {exchange} {symbol} {direction}")
    
    def _handle_risk_action(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les actions de risque
        
        Args:
            data: Données de l'action de risque
        """
        action = data.get("action")
        reason = data.get("reason", "Action de risque")
        
        if action == "close_all":
            self.logger.warning(f"Action de risque demandée: {action} - {reason}")
            self._close_all_positions(reason)
        elif action == "reduce_positions":
            reduction_factor = data.get("reduction_factor", 0.5)
            self.logger.warning(f"Réduction des positions demandée: {reduction_factor} - {reason}")
            
            # Réduire les positions les moins rentables
            if self.active_trades:
                # Dans un système réel, calculer la rentabilité de chaque position
                # et fermer les moins rentables jusqu'à atteindre le facteur de réduction
                
                # Simplification: fermer 50% des positions
                trades_to_close = list(self.active_trades.keys())[:int(len(self.active_trades) * reduction_factor)]
                
                for trade_id in trades_to_close:
                    self._close_position(trade_id, f"Réduction de position - {reason}")
        elif action == "defensive_mode":
            self.logger.warning(f"Mode défensif activé: {reason}")
            
            # Ajuster temporairement les paramètres de risque
            self.config["scalping"]["min_profit_percent"] *= 0.8
            self.config["scalping"]["max_loss_percent"] *= 0.7
            self.config["risk_management"]["max_concurrent_trades"] = max(1, int(self.config["risk_management"]["max_concurrent_trades"] * 0.5))
    
    def _handle_config_update(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les mises à jour de configuration
        
        Args:
            data: Données de mise à jour de configuration
        """
        config_section = data.get("section")
        updates = data.get("updates", {})
        
        if not config_section or not updates:
            return
            
        # Mettre à jour la section de configuration
        if config_section in self.config:
            for key, value in updates.items():
                if key in self.config[config_section]:
                    self.logger.info(f"Mise à jour de la configuration: {config_section}.{key} = {value}")
                    self.config[config_section][key] = value
        
        # Si mise à jour de la liste des symboles
        if config_section == "exchanges":
            for exchange, exchange_updates in updates.items():
                if exchange in self.config["exchanges"] and "symbols" in exchange_updates:
                    self.config["exchanges"][exchange]["symbols"] = exchange_updates["symbols"]
                    self.logger.info(f"Symboles mis à jour pour {exchange}: {exchange_updates['symbols']}")

if __name__ == "__main__":
    # Test simple du module de scalping
    scalpeur = FlowByteBeat()
    scalpeur.start()
    
    # Simuler quelques données de marché
    scalpeur._handle_market_data({
        "symbol": "BTC/USDT",
        "price": 48500,
        "bid": 48495,
        "ask": 48505,
        "volume": 1500000,
        "timestamp": time.time()
    })
    
    # Simuler un signal de trading
    scalpeur._handle_trade_signal({
        "type": "scalp",
        "symbol": "BTC/USDT",
        "direction": "long",
        "exchange": "bybit",
        "timestamp": time.time()
    })
    
    time.sleep(5)  # Attente pour traitement
    scalpeur.stop()
