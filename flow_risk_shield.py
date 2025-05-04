#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowRiskShield.py - Module de protection et réduction des risques pour FlowGlobalDynamics™
"""

import logging
import time
import threading
import json
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

class FlowRiskShield:
    """
    Bouclier de risque pour la protection et la réduction des risques de trading
    """
    
    def __init__(self):
        """Initialisation du FlowRiskShield"""
        self.running = False
        self.thread = None
        self.logger = self._setup_logger()
        self.event_bus = get_event_bus()
        self.current_risk_level = 0  # 0-10, 0=faible, 10=élevé
        self.market_conditions = {}
        self.active_positions = []
        self.risk_thresholds = self._load_risk_thresholds()
        
    def _setup_logger(self):
        """Configuration du logger"""
        logger = logging.getLogger("FlowRiskShield")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_risk_thresholds(self) -> Dict[str, Any]:
        """
        Charge les seuils de risque depuis la configuration
        
        Returns:
            Dictionnaire des seuils de risque
        """
        # Valeurs par défaut
        default_thresholds = {
            "max_position_size": 0.05,    # Max 5% du capital par position
            "max_total_exposure": 0.3,    # Max 30% du capital total exposé
            "volatility_multiplier": 0.8, # Réduction de taille en forte volatilité
            "correlation_limit": 0.7,     # Limite de corrélation entre actifs
            "drawdown_exit": 0.15,        # Sortie à 15% de drawdown du portefeuille
            "market_stress_levels": [
                {"name": "Normal", "threshold": 0.3, "action": "normal_operation"},
                {"name": "Elevated", "threshold": 0.6, "action": "reduce_position_size"},
                {"name": "High", "threshold": 0.8, "action": "defensive_mode"},
                {"name": "Extreme", "threshold": 0.9, "action": "emergency_exit"}
            ]
        }
        
        try:
            # Tenter de charger depuis un fichier (désactivé pour l'exemple)
            # with open("risk_thresholds.json", "r") as f:
            #     return json.load(f)
            return default_thresholds
        except Exception as e:
            self.logger.warning(f"Impossible de charger les seuils de risque: {str(e)}. Utilisation des valeurs par défaut.")
            return default_thresholds
    
    def start(self):
        """Démarrage du bouclier de risque"""
        if self.running:
            self.logger.warning("FlowRiskShield est déjà en cours d'exécution")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._risk_assessment_loop, daemon=True)
        self.thread.start()
        self._register_events()
        self.logger.info("FlowRiskShield démarré")
        
    def stop(self):
        """Arrêt du bouclier de risque"""
        if not self.running:
            self.logger.warning("FlowRiskShield n'est pas en cours d'exécution")
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        self._unregister_events()
        self.logger.info("FlowRiskShield arrêté")
    
    def _register_events(self):
        """Enregistrement des abonnements aux événements"""
        self.event_bus.subscribe("market_data_update", self._handle_market_data)
        self.event_bus.subscribe("position_opened", self._handle_position_opened)
        self.event_bus.subscribe("position_closed", self._handle_position_closed)
        self.event_bus.subscribe("risk_check_request", self._handle_risk_check_request)
    
    def _unregister_events(self):
        """Désenregistrement des abonnements aux événements"""
        self.event_bus.unsubscribe("market_data_update", self._handle_market_data)
        self.event_bus.unsubscribe("position_opened", self._handle_position_opened)
        self.event_bus.unsubscribe("position_closed", self._handle_position_closed)
        self.event_bus.unsubscribe("risk_check_request", self._handle_risk_check_request)
    
    def _risk_assessment_loop(self):
        """Boucle principale d'évaluation des risques"""
        while self.running:
            try:
                self._evaluate_overall_risk()
                time.sleep(5)  # Évaluation régulière toutes les 5 secondes
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle d'évaluation des risques: {str(e)}")
    
    def _evaluate_overall_risk(self):
        """Évalue le niveau de risque global"""
        try:
            if not self.market_conditions:
                return
                
            # Calcul simple du risque basé sur plusieurs facteurs
            volatility_risk = self._calculate_volatility_risk()
            exposure_risk = self._calculate_exposure_risk()
            market_trend_risk = self._calculate_market_trend_risk()
            
            # Pondération des facteurs de risque
            new_risk_level = (
                0.4 * volatility_risk +
                0.4 * exposure_risk +
                0.2 * market_trend_risk
            )
            
            # Normaliser entre 0 et 10
            new_risk_level = min(10, max(0, new_risk_level * 10))
            
            # Si le niveau de risque a changé significativement
            if abs(new_risk_level - self.current_risk_level) > 0.5:
                self.current_risk_level = new_risk_level
                self._publish_risk_assessment()
                
                # Vérifier si des actions de protection sont nécessaires
                self._check_protection_actions()
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'évaluation du risque: {str(e)}")
    
    def _calculate_volatility_risk(self) -> float:
        """
        Calcule le risque lié à la volatilité du marché
        
        Returns:
            Score de risque de volatilité (0-1)
        """
        # Exemple simple, à adapter avec des calculs réels
        if not self.market_conditions.get("volatility"):
            return 0.5
            
        volatility = self.market_conditions.get("volatility", 0.5)
        return min(1.0, max(0.0, volatility))
    
    def _calculate_exposure_risk(self) -> float:
        """
        Calcule le risque lié à l'exposition actuelle du portefeuille
        
        Returns:
            Score de risque d'exposition (0-1)
        """
        if not self.active_positions:
            return 0.0
            
        # Calculer l'exposition totale (somme des tailles des positions)
        total_exposure = sum(position.get("size", 0) for position in self.active_positions)
        
        # Normaliser par rapport au seuil maximal
        max_exposure = self.risk_thresholds.get("max_total_exposure", 0.3)
        exposure_risk = total_exposure / max_exposure
        
        return min(1.0, max(0.0, exposure_risk))
    
    def _calculate_market_trend_risk(self) -> float:
        """
        Calcule le risque lié à la tendance actuelle du marché
        
        Returns:
            Score de risque de tendance (0-1)
        """
        # Simplification - utilise la tendance du marché si disponible
        market_trend = self.market_conditions.get("trend", 0)
        
        # Conversion en score de risque (tendance baissière = risque plus élevé)
        trend_risk = 0.5 - market_trend  # -1 (baisse) à +1 (hausse)
        
        return min(1.0, max(0.0, trend_risk))
    
    def _publish_risk_assessment(self):
        """Publie l'évaluation de risque actuelle"""
        risk_data = {
            "risk_level": self.current_risk_level,
            "risk_category": self._get_risk_category(),
            "risk_factors": {
                "volatility": self._calculate_volatility_risk(),
                "exposure": self._calculate_exposure_risk(),
                "market_trend": self._calculate_market_trend_risk()
            },
            "timestamp": time.time()
        }
        
        self.logger.info(f"Niveau de risque actuel: {self.current_risk_level:.1f}/10 - {risk_data['risk_category']}")
        self.event_bus.publish("risk_assessment", risk_data)
    
    def _get_risk_category(self) -> str:
        """
        Obtient la catégorie de risque basée sur le niveau actuel
        
        Returns:
            Catégorie de risque sous forme de chaîne
        """
        if self.current_risk_level < 3:
            return "Faible"
        elif self.current_risk_level < 5:
            return "Modéré"
        elif self.current_risk_level < 7:
            return "Élevé"
        else:
            return "Critique"
    
    def _check_protection_actions(self):
        """Vérifie si des actions de protection sont nécessaires"""
        if not self.active_positions:
            return
            
        # Déterminer le niveau de stress du marché
        for level in reversed(self.risk_thresholds.get("market_stress_levels", [])):
            if self.current_risk_level / 10 >= level["threshold"]:
                action = level["action"]
                self.logger.info(f"Niveau de stress {level['name']} détecté. Action: {action}")
                
                # Exécuter l'action de protection appropriée
                if action == "reduce_position_size":
                    self._request_position_reduction()
                elif action == "defensive_mode":
                    self._request_defensive_mode()
                elif action == "emergency_exit":
                    self._request_emergency_exit()
                
                break
    
    def _request_position_reduction(self):
        """Demande une réduction des positions"""
        self.event_bus.publish("risk_action", {
            "action": "reduce_positions",
            "reduction_factor": 0.5,  # Réduire de 50%
            "reason": f"Niveau de risque élevé: {self.current_risk_level:.1f}/10"
        })
    
    def _request_defensive_mode(self):
        """Demande le passage en mode défensif"""
        self.event_bus.publish("risk_action", {
            "action": "defensive_mode",
            "stop_loss_tightening": 0.3,  # Resserrer les stop loss de 30%
            "take_profit_reduction": 0.3,  # Réduire les take profit de 30%
            "new_entries_allowed": False,
            "reason": f"Niveau de risque très élevé: {self.current_risk_level:.1f}/10"
        })
    
    def _request_emergency_exit(self):
        """Demande une sortie d'urgence de toutes les positions"""
        self.event_bus.publish("risk_action", {
            "action": "emergency_exit",
            "close_all": True,
            "reason": f"Niveau de risque critique: {self.current_risk_level:.1f}/10"
        })
        
        # Log critique
        self.logger.critical(f"ALERTE RISQUE CRITIQUE: Sortie d'urgence demandée. Niveau de risque: {self.current_risk_level:.1f}/10")
    
    def _handle_market_data(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les mises à jour de données de marché
        
        Args:
            data: Données de marché
        """
        symbol = data.get("symbol", "unknown")
        
        # Mise à jour des conditions de marché
        self.market_conditions[symbol] = {
            "price": data.get("price", 0),
            "volatility": data.get("volatility", 0),
            "volume": data.get("volume", 0),
            "trend": data.get("trend", 0),
            "timestamp": data.get("timestamp", time.time())
        }
    
    def _handle_position_opened(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les ouvertures de position
        
        Args:
            data: Données de la position ouverte
        """
        position_id = data.get("position_id")
        self.active_positions.append(data)
        self.logger.info(f"Nouvelle position suivie: {position_id} - {data.get('symbol')}")
    
    def _handle_position_closed(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les fermetures de position
        
        Args:
            data: Données de la position fermée
        """
        position_id = data.get("position_id")
        
        # Retirer la position de la liste active
        self.active_positions = [p for p in self.active_positions if p.get("position_id") != position_id]
        self.logger.info(f"Position fermée et retirée du suivi: {position_id}")
    
    def _handle_risk_check_request(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les demandes de vérification de risque
        
        Args:
            data: Données de la demande
        """
        request_id = data.get("request_id", "unknown")
        trade_params = data.get("trade_params", {})
        
        # Effectuer la vérification de risque pour le trade proposé
        risk_result = self._evaluate_trade_risk(trade_params)
        
        # Publier le résultat
        self.event_bus.publish("risk_check_response", {
            "request_id": request_id,
            "approved": risk_result["approved"],
            "risk_score": risk_result["risk_score"],
            "position_size_modifier": risk_result["position_size_modifier"],
            "message": risk_result["message"],
            "timestamp": time.time()
        })
    
    def _evaluate_trade_risk(self, trade_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Évalue le risque d'un trade proposé
        
        Args:
            trade_params: Paramètres du trade proposé
            
        Returns:
            Résultat de l'évaluation du risque
        """
        symbol = trade_params.get("symbol", "unknown")
        position_size = trade_params.get("position_size", 0)
        direction = trade_params.get("direction", "long")
        
        # Vérifications de base
        if self.current_risk_level >= 8:
            return {
                "approved": False,
                "risk_score": 1.0,
                "position_size_modifier": 0,
                "message": "Risque de marché trop élevé pour ouvrir de nouvelles positions"
            }
        
        # Vérifier la taille de position par rapport au maximum autorisé
        max_position_size = self.risk_thresholds.get("max_position_size", 0.05)
        if position_size > max_position_size:
            position_size_modifier = max_position_size / position_size
            return {
                "approved": True,
                "risk_score": 0.7,
                "position_size_modifier": position_size_modifier,
                "message": f"Taille de position réduite à {position_size_modifier:.2%} de la demande initiale"
            }
        
        # Trade approuvé avec ajustements basés sur le niveau de risque actuel
        risk_adjustment = 1.0 - (self.current_risk_level / 20)  # Ajustement linéaire
        
        return {
            "approved": True,
            "risk_score": self.current_risk_level / 10,
            "position_size_modifier": risk_adjustment,
            "message": "Trade approuvé avec ajustement de la taille basé sur le risque actuel"
        }

if __name__ == "__main__":
    # Test simple du bouclier de risque
    risk_shield = FlowRiskShield()
    risk_shield.start()
    
    # Simuler des données de marché
    risk_shield._handle_market_data({
        "symbol": "BTC/USDT",
        "price": 48000,
        "volatility": 0.8,  # Élevée
        "volume": 5000,
        "trend": -0.7       # Forte baisse
    })
    
    # Position fictive pour test
    risk_shield._handle_position_opened({
        "position_id": "test-position-1",
        "symbol": "BTC/USDT",
        "direction": "long",
        "size": 0.1,
        "entry_price": 47500
    })
    
    time.sleep(2)  # Attente pour traitement
    risk_shield.stop()
