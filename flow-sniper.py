#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowSniper.py - Module d'entrées précises sur niveaux clés pour FlowGlobalDynamics™
"""

import logging
import time
import threading
import json
import uuid
from typing import Dict, Any, List, Optional

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

class FlowSniper:
    """
    Module de trading précis sur niveaux clés (support/résistance)
    """
    
    def __init__(self):
        """Initialisation du FlowSniper"""
        self.running = False
        self.threads = {}
        self.logger = self._setup_logger()
        self.event_bus = get_event_bus()
        self.active_orders = {}  # ID -> Order data
        self.pending_orders = {}  # Ordres limites en attente
        self.filled_orders = {}  # Ordres exécutés
        self.key_levels = {}  # Niveaux clés par symbole
        self.config = self._load_configuration()
        
    def _setup_logger(self):
        """Configuration du logger"""
        logger = logging.getLogger("FlowSniper")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Charge la configuration du sniper
        
        Returns:
            Configuration du sniper
        """
        # Configuration par défaut
        default_config = {
            "default_timeframe": "1h",
            "max_active_orders": 3,
            "default_timeout_hours": 24,
            "default_slippage": 0.05,
            "risk_management": {
                "max_risk_per_trade": 0.02,  # 2% du capital
                "trailing_stop_enabled": True,
                "auto_adjust_entries": True
            },
            "level_detection": {
                "sensitivity": 0.8,
                "confirmation_candles": 3,
                "min_bounce_count": 2
            },
            "order_placement": {
                "default_reduce_only": False,
                "post_only": True,
                "immediate_or_cancel": False
            },
            "monitoring": {
                "check_interval_seconds": 5,
                "level_retest_tolerance": 0.002  # 0.2% tolérance
            }
        }
        
        try:
            # Tenter de charger depuis un fichier
            # with open("sniper_config.json", "r") as f:
            #     return json.load(f)
            return default_config
        except Exception as e:
            self.logger.warning(f"Impossible de charger la configuration: {str(e)}. Utilisation des valeurs par défaut.")
            return default_config
    
    def start(self):
        """Démarrage du sniper"""
        if self.running:
            self.logger.warning("FlowSniper est déjà en cours d'exécution")
            return
            
        self.running = True
        
        # Démarrage des threads de monitoring
        self._start_monitoring_threads()
        
        self._register_events()
        self.logger.info("FlowSniper démarré")
        
    def stop(self):
        """Arrêt du sniper"""
        if not self.running:
            self.logger.warning("FlowSniper n'est pas en cours d'exécution")
            return
            
        self.running = False
        
        # Annuler tous les ordres actifs
        self._cancel_all_orders()
        
        # Arrêt des threads de monitoring
        for thread_name, thread in self.threads.items():
            if thread and thread.is_alive():
                thread.join(timeout=2.0)
                self.logger.debug(f"Thread {thread_name} arrêté")
        
        self._unregister_events()
        self.logger.info("FlowSniper arrêté")
    
    def _start_monitoring_threads(self):
        """Démarre les threads de monitoring"""
        # Thread de monitoring des ordres
        self.threads["order_monitor"] = threading.Thread(
            target=self._order_monitor_loop, 
            daemon=True
        )
        self.threads["order_monitor"].start()
        
        # Thread de détection des niveaux
        self.threads["level_detector"] = threading.Thread(
            target=self._level_detector_loop, 
            daemon=True
        )
        self.threads["level_detector"].start()
        
        # Thread de gestion des expirations
        self.threads["expiration_manager"] = threading.Thread(
            target=self._expiration_manager_loop, 
            daemon=True
        )
        self.threads["expiration_manager"].start()
    
    def _register_events(self):
        """Enregistrement des abonnements aux événements"""
        self.event_bus.subscribe("market_data_update", self._handle_market_data)
        self.event_bus.subscribe("sniper_order_request", self._handle_order_request)
        self.event_bus.subscribe("order_fill", self._handle_order_fill)
        self.event_bus.subscribe("cancel_order", self._handle_cancel_order)
    
    def _unregister_events(self):
        """Désenregistrement des abonnements aux événements"""
        self.event_bus.unsubscribe("market_data_update", self._handle_market_data)
        self.event_bus.unsubscribe("sniper_order_request", self._handle_order_request)
        self.event_bus.unsubscribe("order_fill", self._handle_order_fill)
        self.event_bus.unsubscribe("cancel_order", self._handle_cancel_order)
    
    def _order_monitor_loop(self):
        """Boucle de monitoring des ordres"""
        while self.running:
            try:
                self._check_orders_status()
                time.sleep(self.config["monitoring"]["check_interval_seconds"])
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de monitoring des ordres: {str(e)}")
                time.sleep(10)
    
    def _level_detector_loop(self):
        """Boucle de détection des niveaux clés"""
        while self.running:
            try:
                self._detect_key_levels()
                time.sleep(30)  # Détection périodique des niveaux
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de détection des niveaux: {str(e)}")
                time.sleep(60)
    
    def _expiration_manager_loop(self):
        """Boucle de gestion des expirations"""
        while self.running:
            try:
                self._check_order_expirations()
                time.sleep(60)  # Vérification des expirations chaque minute
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de gestion des expirations: {str(e)}")
                time.sleep(60)
    
    def _check_orders_status(self):
        """Vérifie le statut de tous les ordres actifs"""
        current_time = time.time()
        orders_to_remove = []
        
        for order_id, order in self.active_orders.items():
            try:
                # Vérifier le statut de l'ordre
                status = self._get_order_status(order_id, order)
                
                if status == "filled":
                    # Ordre exécuté
                    self._handle_order_filled(order_id, order)
                    orders_to_remove.append(order_id)
                elif status == "cancelled":
                    # Ordre annulé
                    self._handle_order_cancelled(order_id, order)
                    orders_to_remove.append(order_id)
                elif status == "expired":
                    # Ordre expiré
                    self._handle_order_expired(order_id, order)
                    orders_to_remove.append(order_id)
                elif status == "partially_filled":
                    # Ordre partiellement exécuté
                    self._handle_order_partial_fill(order_id, order)
                    
                # Mettre à jour le timestamp de dernière vérification
                order["last_checked"] = current_time
                
                # Vérifier si le price action suggère un ajustement
                if self.config["risk_management"]["auto_adjust_entries"]:
                    self._consider_order_adjustment(order_id, order)
                    
            except Exception as e:
                self.logger.error(f"Erreur lors de la vérification de l'ordre {order_id}: {str(e)}")
        
        # Retirer les ordres traités
        for order_id in orders_to_remove:
            if order_id in self.active_orders:
                del self.active_orders[order_id]
    
    def _get_order_status(self, order_id: str, order: Dict[str, Any]) -> str:
        """
        Vérifie le statut d'un ordre
        
        Args:
            order_id: ID de l'ordre
            order: Données de l'ordre
            
        Returns:
            Statut de l'ordre
        """
        # Simuler la vérification du statut
        # Dans un système réel, vérifier via l'API de l'exchange
        
        # Si l'ordre a expiré
        current_time = time.time()
        if current_time > order.get("expires_at", float('inf')):
            return "expired"
        
        # Simuler une chance d'exécution basée sur le prix du marché
        symbol = order["symbol"]
        if symbol in self.key_levels and "market_data" in self.key_levels[symbol]:
            market_price = self.key_levels[symbol]["market_data"]["price"]
            order_price = order["entry_price"]
            direction = order["direction"]
            
            # Vérifier si le prix du marché a atteint le niveau d'ordre
            if direction == "long" and market_price <= order_price:
                return "filled" if current_time % 10 < 8 else "pending"  # 80% chance d'exécution
            elif direction == "short" and market_price >= order_price:
                return "filled" if current_time % 10 < 8 else "pending"
        
        return "pending"
    
    def _handle_order_filled(self, order_id: str, order: Dict[str, Any]):
        """
        Gère un ordre exécuté
        
        Args:
            order_id: ID de l'ordre
            order: Données de l'ordre
        """
        self.logger.info(f"Ordre {order_id} exécuté: {order['direction']} {order['size']} {order['symbol']} à {order['entry_price']}")
        
        # Mettre à jour le statut
        order["status"] = "filled"
        order["filled_at"] = time.time()
        
        # Déplacer vers les ordres remplis
        self.filled_orders[order_id] = order
        
        # Placer les ordres de stop-loss et take-profit
        if "stop_loss" in order:
            self._place_stop_loss(order_id, order)
        if "take_profit" in order:
            self._place_take_profit(order_id, order)
        
        # Publier l'événement d'ordre rempli
        self.event_bus.publish("order_filled", {
            "order_id": order_id,
            "symbol": order["symbol"],
            "direction": order["direction"],
            "size": order["size"],
            "fill_price": order["entry_price"],
            "timestamp": time.time()
        })
    
    def _handle_order_cancelled(self, order_id: str, order: Dict[str, Any]):
        """
        Gère un ordre annulé
        
        Args:
            order_id: ID de l'ordre
            order: Données de l'ordre
        """
        self.logger.info(f"Ordre {order_id} annulé: {order['symbol']} {order['direction']}")
        
        # Mettre à jour le statut
        order["status"] = "cancelled"
        order["cancelled_at"] = time.time()
        
        # Publier l'événement d'ordre annulé
        self.event_bus.publish("order_cancelled", {
            "order_id": order_id,
            "symbol": order["symbol"],
            "reason": order.get("cancel_reason", "Unknown"),
            "timestamp": time.time()
        })
    
    def _handle_order_expired(self, order_id: str, order: Dict[str, Any]):
        """
        Gère un ordre expiré
        
        Args:
            order_id: ID de l'ordre
            order: Données de l'ordre
        """
        self.logger.info(f"Ordre {order_id} expiré: {order['symbol']} {order['direction']}")
        
        # Mettre à jour le statut
        order["status"] = "expired"
        order["expired_at"] = time.time()
        
        # Publier l'événement d'ordre expiré
        self.event_bus.publish("order_expired", {
            "order_id": order_id,
            "symbol": order["symbol"],
            "timestamp": time.time()
        })
    
    def _handle_order_partial_fill(self, order_id: str, order: Dict[str, Any]):
        """
        Gère un ordre partiellement exécuté
        
        Args:
            order_id: ID de l'ordre
            order: Données de l'ordre
        """
        # Simuler l'exécution partielle
        if "filled_size" not in order:
            order["filled_size"] = 0
        
        partial_fill = order["size"] * 0.3  # 30% de remplissage
        order["filled_size"] += partial_fill
        order["remaining_size"] = order["size"] - order["filled_size"]
        
        self.logger.info(f"Ordre {order_id} partiellement exécuté: {order['filled_size']}/{order['size']} {order['symbol']}")
        
        # Si l'ordre est complètement rempli
        if order["filled_size"] >= order["size"]:
            self._handle_order_filled(order_id, order)
        else:
            # Publier l'événement de remplissage partiel
            self.event_bus.publish("order_partial_fill", {
                "order_id": order_id,
                "symbol": order["symbol"],
                "filled_size": order["filled_size"],
                "remaining_size": order["remaining_size"],
                "timestamp": time.time()
            })
    
    def _consider_order_adjustment(self, order_id: str, order: Dict[str, Any]):
        """
        Considère l'ajustement d'un ordre basé sur l'action des prix
        
        Args:
            order_id: ID de l'ordre
            order: Données de l'ordre
        """
        symbol = order["symbol"]
        
        if symbol not in self.key_levels or "market_data" not in self.key_levels[symbol]:
            return
        
        market_price = self.key_levels[symbol]["market_data"]["price"]
        order_price = order["entry_price"]
        direction = order["direction"]
        
        # Calculer la distance jusqu'à l'ordre
        distance_percent = abs(market_price - order_price) / order_price
        
        # Si le marché s'éloigne trop de l'ordre
        if distance_percent > 0.02:  # 2% de distance
            # Déterminer si l'ordre doit être ajusté ou annulé
            if direction == "long" and market_price > order_price:
                # Le marché est monté, ajuster l'ordre à la hausse
                new_entry_level = self._get_next_support_level(symbol, market_price)
                if new_entry_level and new_entry_level != order_price:
                    self._adjust_order_price(order_id, new_entry_level)
            elif direction == "short" and market_price < order_price:
                # Le marché est descendu, ajuster l'ordre à la baisse
                new_entry_level = self._get_next_resistance_level(symbol, market_price)
                if new_entry_level and new_entry_level != order_price:
                    self._adjust_order_price(order_id, new_entry_level)
    
    def _get_next_support_level(self, symbol: str, current_price: float) -> Optional[float]:
        """
        Obtient le prochain niveau de support
        
        Args:
            symbol: Symbole
            current_price: Prix actuel
            
        Returns:
            Niveau de support ou None
        """
        if symbol not in self.key_levels or "support_levels" not in self.key_levels[symbol]:
            return None
        
        support_levels = self.key_levels[symbol]["support_levels"]
        
        # Trouver le prochain support en dessous du prix actuel
        for level in sorted(support_levels, reverse=True):
            if level < current_price:
                return level
        
        return None
    
    def _get_next_resistance_level(self, symbol: str, current_price: float) -> Optional[float]:
        """
        Obtient le prochain niveau de résistance
        
        Args:
            symbol: Symbole
            current_price: Prix actuel
            
        Returns:
            Niveau de résistance ou None
        """
        if symbol not in self.key_levels or "resistance_levels" not in self.key_levels[symbol]:
            return None
        
        resistance_levels = self.key_levels[symbol]["resistance_levels"]
        
        # Trouver la prochaine résistance au-dessus du prix actuel
        for level in sorted(resistance_levels):
            if level > current_price:
                return level
        
        return None
    
    def _adjust_order_price(self, order_id: str, new_price: float):
        """
        Ajuste le prix d'un ordre
        
        Args:
            order_id: ID de l'ordre
            new_price: Nouveau prix
        """
        if order_id not in self.active_orders:
            return
        
        order = self.active_orders[order_id]
        old_price = order["entry_price"]
        
        # Mettre à jour le prix
        order["entry_price"] = new_price
        order["adjusted_at"] = time.time()
        order["previous_price"] = old_price
        
        self.logger.info(f"Ordre {order_id} ajusté: prix modifié de {old_price} à {new_price}")
        
        # Publier l'événement d'ajustement
        self.event_bus.publish("order_adjusted", {
            "order_id": order_id,
            "symbol": order["symbol"],
            "old_price": old_price,
            "new_price": new_price,
            "timestamp": time.time()
        })
    
    def _detect_key_levels(self):
        """Détecte les niveaux clés pour les différents symboles"""
        # Cette fonction serait normalement connectée à une source de données
        # Pour la démo, nous travaillons avec les niveaux existants
        
        for symbol in self.key_levels:
            # Mettre à jour les niveaux basés sur l'action des prix récente
            if "market_data" in self.key_levels[symbol]:
                self._update_levels_from_price_action(symbol)
    
    def _update_levels_from_price_action(self, symbol: str):
        """
        Met à jour les niveaux basés sur l'action des prix
        
        Args:
            symbol: Symbole à analyser
        """
        # Simuler la mise à jour des niveaux
        # Dans un système réel, utiliser l'analyse technique
        
        if "support_levels" in self.key_levels[symbol] and "resistance_levels" in self.key_levels[symbol]:
            # Simuler l'ajout/suppression de niveaux basé sur le prix
            current_price = self.key_levels[symbol]["market_data"]["price"]
            
            # Vérifier si des niveaux doivent être marqués comme cassés
            broken_supports = []
            for level in self.key_levels[symbol]["support_levels"]:
                if current_price < level * 0.998:  # 0.2% tolérance
                    broken_supports.append(level)
            
            # Retirer les supports cassés
            for level in broken_supports:
                self.key_levels[symbol]["support_levels"].remove(level)
                self.logger.debug(f"Support cassé pour {symbol}: {level}")
            
            broken_resistances = []
            for level in self.key_levels[symbol]["resistance_levels"]:
                if current_price > level * 1.002:  # 0.2% tolérance
                    broken_resistances.append(level)
            
            # Retirer les résistances cassées
            for level in broken_resistances:
                self.key_levels[symbol]["resistance_levels"].remove(level)
                self.logger.debug(f"Résistance cassée pour {symbol}: {level}")
    
    def _check_order_expirations(self):
        """Vérifie si des ordres ont expiré"""
        current_time = time.time()
        expired_orders = []
        
        for order_id, order in self.active_orders.items():
            if current_time > order.get("expires_at", float('inf')):
                expired_orders.append(order_id)
        
        # Annuler les ordres expirés
        for order_id in expired_orders:
            self._cancel_order(order_id, "expired")
    
    def _cancel_order(self, order_id: str, reason: str = "manual"):
        """
        Annule un ordre
        
        Args:
            order_id: ID de l'ordre
            reason: Raison de l'annulation
        """
        if order_id not in self.active_orders:
            return
        
        order = self.active_orders[order_id]
        order["cancel_reason"] = reason
        
        # Marquer pour annulation
        order["status"] = "cancelling"
        order["cancel_requested_at"] = time.time()
        
        self.logger.info(f"Annulation de l'ordre {order_id} demandée: {reason}")
    
    def _cancel_all_orders(self):
        """Annule tous les ordres actifs"""
        order_ids = list(self.active_orders.keys())
        
        for order_id in order_ids:
            self._cancel_order(order_id, "shutdown")
    
    def _place_stop_loss(self, parent_order_id: str, parent_order: Dict[str, Any]):
        """
        Place un ordre stop-loss pour un ordre rempli
        
        Args:
            parent_order_id: ID de l'ordre parent
            parent_order: Données de l'ordre parent
        """
        stop_loss_price = parent_order["stop_loss"]
        
        # Déterminer la direction opposée
        sl_direction = "sell" if parent_order["direction"] == "long" else "buy"
        
        # Créer l'ordre stop-loss
        sl_order = {
            "id": f"sl_{parent_order_id}",
            "parent_id": parent_order_id,
            "type": "stop_market",
            "symbol": parent_order["symbol"],
            "direction": sl_direction,
            "size": parent_order["size"],
            "trigger_price": stop_loss_price,
            "reduce_only": True,
            "created_at": time.time(),
            "status": "pending"
        }
        
        # Ajouter aux ordres actifs
        self.active_orders[sl_order["id"]] = sl_order
        
        self.logger.info(f"Stop-loss placé pour {parent_order_id}: {sl_direction} {sl_order['size']} {sl_order['symbol']} à {stop_loss_price}")
    
    def _place_take_profit(self, parent_order_id: str, parent_order: Dict[str, Any]):
        """
        Place un ordre take-profit pour un ordre rempli
        
        Args:
            parent_order_id: ID de l'ordre parent
            parent_order: Données de l'ordre parent
        """
        take_profit_price = parent_order["take_profit"]
        
        # Déterminer la direction opposée
        tp_direction = "sell" if parent_order["direction"] == "long" else "buy"
        
        # Créer l'ordre take-profit
        tp_order = {
            "id": f"tp_{parent_order_id}",
            "parent_id": parent_order_id,
            "type": "limit",
            "symbol": parent_order["symbol"],
            "direction": tp_direction,
            "size": parent_order["size"],
            "entry_price": take_profit_price,
            "reduce_only": True,
            "created_at": time.time(),
            "status": "pending"
        }
        
        # Ajouter aux ordres actifs
        self.active_orders[tp_order["id"]] = tp_order
        
        self.logger.info(f"Take-profit placé pour {parent_order_id}: {tp_direction} {tp_order['size']} {tp_order['symbol']} à {take_profit_price}")
    
    def create_sniper_order(self, symbol: str, exchange: str, direction: str, 
                          entry_price: float, stop_loss: float, take_profit: float,
                          size: float, timeout_hours: float = 24.0,
                          settings: Optional[Dict[str, Any]] = None) -> str:
        """
        Crée un ordre sniper
        
        Args:
            symbol: Symbole à trader
            exchange: Exchange
            direction: Direction (long/short)
            entry_price: Prix d'entrée ciblé
            stop_loss: Niveau de stop-loss
            take_profit: Niveau de take-profit
            size: Taille de la position
            timeout_hours: Délai d'expiration en heures
            settings: Paramètres supplémentaires
            
        Returns:
            ID de l'ordre créé
        """
        # Générer un ID unique
        order_id = f"sniper-{uuid.uuid4()}"
        
        # Créer l'ordre
        order = {
            "id": order_id,
            "type": "limit",
            "symbol": symbol,
            "exchange": exchange,
            "direction": direction,
            "size": size,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "status": "pending",
            "created_at": time.time(),
            "expires_at": time.time() + (timeout_hours * 3600),
            "settings": settings or {},
            "last_checked": time.time()
        }
        
        # Ajouter aux ordres actifs
        self.active_orders[order_id] = order
        
        self.logger.info(f"Ordre sniper créé: {direction} {size} {symbol} à {entry_price}")
        
        # Publier l'événement de création d'ordre
        self.event_bus.publish("sniper_order_created", {
            "order_id": order_id,
            "symbol": symbol,
            "direction": direction,
            "size": size,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "timestamp": time.time()
        })
        
        return order_id
    
    def update_key_levels(self, symbol: str, support_levels: List[float], 
                         resistance_levels: List[float], market_price: float):
        """
        Met à jour les niveaux clés pour un symbole
        
        Args:
            symbol: Symbole
            support_levels: Niveaux de support
            resistance_levels: Niveaux de résistance
            market_price: Prix actuel du marché
        """
        self.key_levels[symbol] = {
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
            "market_data": {
                "price": market_price,
                "last_update": time.time()
            }
        }
        
        self.logger.debug(f"Niveaux clés mis à jour pour {symbol}")
    
    def _handle_market_data(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les mises à jour de données de marché
        
        Args:
            data: Données de marché
        """
        symbol = data.get("symbol")
        if not symbol:
            return
        
        # Mettre à jour les données de marché
        if symbol not in self.key_levels:
            self.key_levels[symbol] = {
                "support_levels": [],
                "resistance_levels": [],
                "market_data": {}
            }
        
        self.key_levels[symbol]["market_data"] = {
            "price": data.get("price", 0),
            "bid": data.get("bid", 0),
            "ask": data.get("ask", 0),
            "volume": data.get("volume", 0),
            "volatility": data.get("volatility", 0),
            "last_update": time.time()
        }
        
        # Mettre à jour les niveaux de support/résistance s'ils sont fournis
        if "support_levels" in data:
            self.key_levels[symbol]["support_levels"] = data["support_levels"]
        if "resistance_levels" in data:
            self.key_levels[symbol]["resistance_levels"] = data["resistance_levels"]
    
    def _handle_order_request(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les demandes d'ordre
        
        Args:
            data: Données de la demande
        """
        request_id = data.get("request_id", str(uuid.uuid4()))
        
        try:
            symbol = data.get("symbol")
            exchange = data.get("exchange", "bybit")
            direction = data.get("direction")
            entry_price = data.get("entry_price")
            stop_loss = data.get("stop_loss")
            take_profit = data.get("take_profit")
            size = data.get("size")
            timeout_hours = data.get("timeout_hours", 24.0)
            settings = data.get("settings")
            
            # Vérifier les paramètres requis
            if not all([symbol, direction, entry_price, stop_loss, take_profit, size]):
                raise ValueError("Paramètres manquants pour créer l'ordre")
            
            # Créer l'ordre
            order_id = self.create_sniper_order(
                symbol, exchange, direction, entry_price,
                stop_loss, take_profit, size, timeout_hours, settings
            )
            
            # Publier la réponse
            self.event_bus.publish("sniper_order_response", {
                "request_id": request_id,
                "success": True,
                "order_id": order_id,
                "timestamp": time.time()
            })
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de l'ordre: {str(e)}")
            
            # Publier la réponse d'erreur
            self.event_bus.publish("sniper_order_response", {
                "request_id": request_id,
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            })
    
    def _handle_order_fill(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les remplissages d'ordre
        
        Args:
            data: Données du remplissage
        """
        order_id = data.get("order_id")
        if not order_id or order_id not in self.active_orders:
            return
        
        order = self.active_orders[order_id]
        
        # Mettre à jour le statut de l'ordre
        fill_price = data.get("fill_price", order["entry_price"])
        fill_size = data.get("fill_size", order["size"])
        
        order["status"] = "filled"
        order["filled_at"] = time.time()
        order["fill_price"] = fill_price
        order["fill_size"] = fill_size
        
        # Gérer l'ordre rempli
        self._handle_order_filled(order_id, order)
    
    def _handle_cancel_order(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les demandes d'annulation d'ordre
        
        Args:
            data: Données de la demande
        """
        order_id = data.get("order_id")
        reason = data.get("reason", "manual")
        
        if not order_id:
            return
        
        # Annuler l'ordre
        self._cancel_order(order_id, reason)

if __name__ == "__main__":
    # Test simple du sniper
    sniper = FlowSniper()
    sniper.start()
    
    # Créer un ordre de test
    test_order_id = sniper.create_sniper_order(
        symbol="BTC/USDT",
        exchange="bybit",
        direction="long",
        entry_price=47000,
        stop_loss=46500,
        take_profit=48000,
        size=0.01,
        timeout_hours=24
    )
    
    # Simuler des données de marché
    sniper._handle_market_data({
        "symbol": "BTC/USDT",
        "price": 47500,
        "bid": 47495,
        "ask": 47505,
        "volume": 5000,
        "support_levels": [47000, 46800, 46500],
        "resistance_levels": [48000, 48200, 48500]
    })
    
    time.sleep(2)  # Attente pour traitement
    sniper.stop()