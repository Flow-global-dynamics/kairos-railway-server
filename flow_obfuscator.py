#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowObfuscator.py - Module de protection contre l'espionnage IA/trading pour FlowGlobalDynamics™
"""

import logging
import time
import threading
import json
import random
import hashlib
import base64
import os
from typing import Dict, Any, List, Optional, Union, Callable

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

class FlowObfuscator:
    """
    Module de protection contre l'espionnage pour le cockpit FlowGlobalDynamics™
    """
    
    def __init__(self):
        """Initialisation du FlowObfuscator"""
        self.running = False
        self.threads = {}
        self.logger = self._setup_logger()
        self.event_bus = get_event_bus()
        self.config = self._load_configuration()
        self.obfuscation_keys = self._generate_obfuscation_keys()
        self.protection_active = True
        self.suspicious_activities = []
        self.detected_patterns = {}
        self.last_key_rotation = time.time()
        
    def _setup_logger(self):
        """Configuration du logger"""
        logger = logging.getLogger("FlowObfuscator")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Charge la configuration de l'obfuscateur
        
        Returns:
            Configuration de l'obfuscateur
        """
        # Configuration par défaut
        default_config = {
            "protection_levels": {
                "trade_data": "high",
                "market_analysis": "medium",
                "api_communication": "very_high",
                "signal_generation": "high",
                "performance_metrics": "medium"
            },
            "encryption": {
                "enabled": True,
                "algorithm": "AES-GCM",  # En réalité, utiliserait une bibliothèque de cryptographie
                "key_rotation_hours": 24
            },
            "obfuscation": {
                "order_sizes": True,
                "timing_randomization": True,
                "entry_price_offset": 0.1,  # Pourcentage de décalage
                "decoy_orders": True,
                "decoy_frequency": 0.2,  # 20% des ordres réels
                "parameter_noise": 0.05  # 5% de bruit sur les paramètres
            },
            "anti_pattern": {
                "enabled": True,
                "detection_sensitivity": 0.7,
                "countermeasures": ["timing_shift", "parameter_variation", "execution_paths"]
            },
            "monitoring": {
                "exchange_api_calls": True,
                "data_exfiltration": True,
                "unusual_patterns": True,
                "alert_threshold": 0.8
            }
        }
        
        try:
            # Tenter de charger depuis un fichier (désactivé pour l'exemple)
            # with open("obfuscator_config.json", "r") as f:
            #     return json.load(f)
            return default_config
        except Exception as e:
            self.logger.warning(f"Impossible de charger la configuration: {str(e)}. Utilisation des valeurs par défaut.")
            return default_config
    
    def _generate_obfuscation_keys(self) -> Dict[str, str]:
        """
        Génère des clés d'obfuscation pour différents modules
        
        Returns:
            Dictionnaire des clés d'obfuscation
        """
        keys = {}
        modules = [
            "trade_execution", "market_data", "risk_management", 
            "signal_generation", "position_sizing", "api_communication"
        ]
        
        for module in modules:
            # Générer une clé aléatoire pour chaque module
            # Dans un système réel, utiliser une vraie génération de clés cryptographiques
            random_bytes = os.urandom(32)
            key = base64.b64encode(random_bytes).decode('utf-8')
            keys[module] = key
        
        self.logger.debug("Nouvelles clés d'obfuscation générées")
        return keys
    
    def start(self):
        """Démarrage de l'obfuscateur"""
        if self.running:
            self.logger.warning("FlowObfuscator est déjà en cours d'exécution")
            return
            
        self.running = True
        
        # Démarrage des threads de protection
        self._start_protection_threads()
        
        self._register_events()
        self.logger.info("FlowObfuscator démarré - Protection contre l'espionnage activée")
        
    def stop(self):
        """Arrêt de l'obfuscateur"""
        if not self.running:
            self.logger.warning("FlowObfuscator n'est pas en cours d'exécution")
            return
            
        self.running = False
        
        # Arrêt des threads de protection
        for thread_name, thread in self.threads.items():
            if thread and thread.is_alive():
                thread.join(timeout=2.0)
                self.logger.debug(f"Thread {thread_name} arrêté")
        
        self._unregister_events()
        self.logger.info("FlowObfuscator arrêté")
    
    def _start_protection_threads(self):
        """Démarre les threads de protection"""
        # Thread de surveillance des activités
        self.threads["activity_monitor"] = threading.Thread(
            target=self._activity_monitor_loop, 
            daemon=True
        )
        self.threads["activity_monitor"].start()
        
        # Thread de rotation des clés
        self.threads["key_rotation"] = threading.Thread(
            target=self._key_rotation_loop, 
            daemon=True
        )
        self.threads["key_rotation"].start()
        
        # Thread de détection de patterns
        self.threads["pattern_detection"] = threading.Thread(
            target=self._pattern_detection_loop, 
            daemon=True
        )
        self.threads["pattern_detection"].start()
    
    def _register_events(self):
        """Enregistrement des abonnements aux événements"""
        self.event_bus.subscribe("outgoing_trade", self._handle_outgoing_trade)
        self.event_bus.subscribe("market_data_update", self._handle_market_data)
        self.event_bus.subscribe("api_call", self._handle_api_call)
        self.event_bus.subscribe("trade_signal", self._handle_trade_signal)
        self.event_bus.subscribe("obfuscation_config_update", self._handle_config_update)
    
    def _unregister_events(self):
        """Désenregistrement des abonnements aux événements"""
        self.event_bus.unsubscribe("outgoing_trade", self._handle_outgoing_trade)
        self.event_bus.unsubscribe("market_data_update", self._handle_market_data)
        self.event_bus.unsubscribe("api_call", self._handle_api_call)
        self.event_bus.unsubscribe("trade_signal", self._handle_trade_signal)
        self.event_bus.unsubscribe("obfuscation_config_update", self._handle_config_update)
    
    def _activity_monitor_loop(self):
        """Boucle de surveillance des activités"""
        while self.running:
            try:
                # Analyser les activités suspectes
                if self.suspicious_activities:
                    self._analyze_suspicious_activities()
                    
                    # Effacer les anciennes activités (plus de 1 heure)
                    current_time = time.time()
                    self.suspicious_activities = [
                        a for a in self.suspicious_activities 
                        if current_time - a.get("timestamp", 0) < 3600
                    ]
                
                time.sleep(10)  # Vérification toutes les 10 secondes
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de surveillance des activités: {str(e)}")
                time.sleep(30)
    
    def _key_rotation_loop(self):
        """Boucle de rotation des clés d'obfuscation"""
        while self.running:
            try:
                current_time = time.time()
                hours_since_rotation = (current_time - self.last_key_rotation) / 3600
                
                # Vérifier si une rotation de clés est nécessaire
                if hours_since_rotation >= self.config["encryption"]["key_rotation_hours"]:
                    self._rotate_obfuscation_keys()
                    self.last_key_rotation = current_time
                
                time.sleep(300)  # Vérification toutes les 5 minutes
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de rotation des clés: {str(e)}")
                time.sleep(300)
    
    def _pattern_detection_loop(self):
        """Boucle de détection de patterns"""
        while self.running:
            try:
                # Analyser les patterns détectés
                self._analyze_patterns()
                
                # Appliquer les contre-mesures si des patterns suspects sont détectés
                if self.detected_patterns:
                    self._apply_countermeasures()
                
                time.sleep(60)  # Vérification toutes les minutes
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de détection de patterns: {str(e)}")
                time.sleep(120)
    
    def _rotate_obfuscation_keys(self):
        """Effectue une rotation des clés d'obfuscation"""
        self.logger.info("Rotation des clés d'obfuscation en cours...")
        
        # Générer de nouvelles clés
        new_keys = self._generate_obfuscation_keys()
        
        # Remplacer les anciennes clés
        self.obfuscation_keys = new_keys
        
        # Notifier les modules de la rotation
        self.event_bus.publish("obfuscation_keys_rotated", {
            "timestamp": time.time()
        })
        
        self.logger.info("Rotation des clés d'obfuscation terminée")
    
    def _analyze_suspicious_activities(self):
        """Analyse les activités suspectes"""
        if not self.suspicious_activities:
            return
            
        # Regrouper les activités par type
        activities_by_type = {}
        
        for activity in self.suspicious_activities:
            activity_type = activity.get("type", "unknown")
            if activity_type not in activities_by_type:
                activities_by_type[activity_type] = []
            
            activities_by_type[activity_type].append(activity)
        
        # Analyser chaque type d'activité
        for activity_type, activities in activities_by_type.items():
            if len(activities) > 3:  # Seuil arbitraire
                # Calculer un score de risque
                risk_score = self._calculate_activity_risk(activity_type, activities)
                
                if risk_score > self.config["monitoring"]["alert_threshold"]:
                    self._trigger_protection_alert(activity_type, activities, risk_score)
    
    def _calculate_activity_risk(self, activity_type: str, activities: List[Dict[str, Any]]) -> float:
        """
        Calcule un score de risque pour un type d'activité
        
        Args:
            activity_type: Type d'activité
            activities: Liste des activités
            
        Returns:
            Score de risque (0-1)
        """
        # Calculer le score de risque en fonction du type d'activité
        if activity_type == "api_frequency":
            # Fréquence anormale d'appels API
            calls_per_minute = len(activities) / max(1, (activities[-1]["timestamp"] - activities[0]["timestamp"]) / 60)
            risk_score = min(1.0, calls_per_minute / 50)  # Seuil arbitraire: 50 appels/minute
        elif activity_type == "timing_pattern":
            # Patterns temporels répétitifs
            timestamps = [a["timestamp"] for a in activities]
            intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            
            # Calculer l'écart-type des intervalles (faible = régulier = suspect)
            if len(intervals) > 1:
                mean_interval = sum(intervals) / len(intervals)
                variance = sum((i - mean_interval) ** 2 for i in intervals) / len(intervals)
                std_dev = variance ** 0.5
                
                # Normaliser: plus l'écart-type est faible (régularité élevée), plus le risque est élevé
                regularity = 1 - min(1.0, std_dev / mean_interval)
                risk_score = regularity
            else:
                risk_score = 0.0
        elif activity_type == "data_exfiltration":
            # Tentatives d'exfiltration de données
            risk_score = 0.9  # Toujours considéré comme risqué
        else:
            # Type d'activité inconnu
            risk_score = 0.5  # Risque moyen par défaut
        
        return risk_score
    
    def _trigger_protection_alert(self, activity_type: str, activities: List[Dict[str, Any]], risk_score: float):
        """
        Déclenche une alerte de protection
        
        Args:
            activity_type: Type d'activité
            activities: Liste des activités
            risk_score: Score de risque
        """
        alert_data = {
            "type": activity_type,
            "risk_score": risk_score,
            "count": len(activities),
            "first_timestamp": activities[0]["timestamp"],
            "last_timestamp": activities[-1]["timestamp"],
            "details": activities[:5],  # Limiter aux 5 premières activités
            "timestamp": time.time()
        }
        
        self.logger.warning(f"Alerte de protection: {activity_type} - Score de risque: {risk_score:.2f}")
        
        # Publier l'alerte
        self.event_bus.publish("protection_alert", alert_data)
        
        # Augmenter automatiquement le niveau de protection
        if risk_score > 0.8:
            self._increase_protection_level()
    
    def _increase_protection_level(self):
        """
        Augmente le niveau de protection
        """
        self.logger.info("Augmentation du niveau de protection...")
        
        # Augmenter la protection des ordres
        if self.config["obfuscation"]["entry_price_offset"] < 0.2:
            self.config["obfuscation"]["entry_price_offset"] *= 1.5
        
        # Augmenter la fréquence des leurres
        if self.config["obfuscation"]["decoy_frequency"] < 0.5:
            self.config["obfuscation"]["decoy_frequency"] += 0.1
        
        # Augmenter le bruit sur les paramètres
        if self.config["obfuscation"]["parameter_noise"] < 0.1:
            self.config["obfuscation"]["parameter_noise"] *= 1.5
        
        # Publier la mise à jour de configuration
        self.event_bus.publish("obfuscation_level_increased", {
            "new_config": {
                "entry_price_offset": self.config["obfuscation"]["entry_price_offset"],
                "decoy_frequency": self.config["obfuscation"]["decoy_frequency"],
                "parameter_noise": self.config["obfuscation"]["parameter_noise"]
            },
            "timestamp": time.time()
        })
    
    def _analyze_patterns(self):
        """
        Analyse les patterns détectés
        """
        # Dans un système réel, implémenter des algorithmes de détection de patterns
        # comme l'analyse de séries temporelles, la détection d'anomalies, etc.
        
        # Pour l'exemple, nous simulons une détection simple
        # Cette fonction serait appelée après avoir accumulé suffisamment de données
        pass
    
    def _apply_countermeasures(self):
        """
        Applique des contre-mesures contre les patterns détectés
        """
        if not self.detected_patterns:
            return
            
        self.logger.info("Application de contre-mesures anti-pattern...")
        
        # Récupérer les contre-mesures configurées
        countermeasures = self.config["anti_pattern"]["countermeasures"]
        
        # Appliquer chaque contre-mesure
        for measure in countermeasures:
            if measure == "timing_shift":
                # Modifier les timing d'exécution
                self.event_bus.publish("countermeasure_applied", {
                    "type": "timing_shift",
                    "parameters": {
                        "min_delay_ms": 50,
                        "max_delay_ms": 200,
                        "random_seed": random.randint(1000, 9999)
                    },
                    "duration": 1800,  # 30 minutes
                    "timestamp": time.time()
                })
            elif measure == "parameter_variation":
                # Introduire des variations dans les paramètres
                self.event_bus.publish("countermeasure_applied", {
                    "type": "parameter_variation",
                    "parameters": {
                        "variation_factor": min(0.2, self.config["obfuscation"]["parameter_noise"] * 2),
                        "affected_modules": ["position_sizing", "entry_timing", "exit_rules"]
                    },
                    "duration": 3600,  # 1 heure
                    "timestamp": time.time()
                })
            elif measure == "execution_paths":
                # Modifier les chemins d'exécution
                self.event_bus.publish("countermeasure_applied", {
                    "type": "execution_paths",
                    "parameters": {
                        "reorder_operations": True,
                        "split_operations": True,
                        "conditional_execution": True
                    },
                    "duration": 7200,  # 2 heures
                    "timestamp": time.time()
                })
    
    def obfuscate_trade_data(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obfusque les données de trade
        
        Args:
            trade_data: Données du trade à obfusquer
            
        Returns:
            Données de trade obfusquées
        """
        if not self.protection_active or not self.config["obfuscation"]["order_sizes"]:
            return trade_data
            
        # Créer une copie pour ne pas modifier l'original
        obfuscated_data = trade_data.copy()
        
        # Obfusquer la taille de l'ordre
        if "size" in obfuscated_data:
            # Appliquer une variation à la taille
            noise_factor = self.config["obfuscation"]["parameter_noise"]
            size_variation = 1.0 + (random.random() * 2 - 1) * noise_factor
            obfuscated_data["size"] = obfuscated_data["size"] * size_variation
        
        # Obfusquer le prix d'entrée
        if "entry_price" in obfuscated_data:
            # Appliquer un décalage au prix
            price_offset = self.config["obfuscation"]["entry_price_offset"] / 100
            direction = 1 if random.random() > 0.5 else -1
            price_variation = 1.0 + direction * random.random() * price_offset
            obfuscated_data["entry_price"] = obfuscated_data["entry_price"] * price_variation
        
        # Ajouter des métadonnées aléatoires
        obfuscated_data["metadata"] = {
            "execution_id": self._generate_random_id(),
            "priority": random.randint(1, 5),
            "routing": random.choice(["direct", "smart", "algo"]),
            "timestamp_offset": random.randint(-500, 500)  # Milliseconds
        }
        
        return obfuscated_data
    
    def add_decoy_order(self, real_order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Crée un ordre leurre basé sur un ordre réel
        
        Args:
            real_order: Ordre réel
            
        Returns:
            Ordre leurre ou None si la fonctionnalité est désactivée
        """
        if not self.protection_active or not self.config["obfuscation"]["decoy_orders"]:
            return None
        
        # Vérifier si un leurre doit être généré (basé sur la fréquence configurée)
        if random.random() > self.config["obfuscation"]["decoy_frequency"]:
            return None
        
        # Créer un ordre leurre en inversant la direction et en modifiant les paramètres
        decoy = real_order.copy()
        
        # Inverser la direction
        if decoy.get("direction") == "long":
            decoy["direction"] = "short"
        else:
            decoy["direction"] = "long"
        
        # Modifier la taille (généralement plus petite)
        if "size" in decoy:
            decoy["size"] = decoy["size"] * random.uniform(0.1, 0.5)
        
        # Modifier le prix
        if "entry_price" in decoy:
            direction = 1 if random.random() > 0.5 else -1
            decoy["entry_price"] = decoy["entry_price"] * (1 + direction * random.uniform(0.01, 0.05))
        
        # Marquer comme un leurre (en interne seulement)
        decoy["_decoy"] = True
        decoy["_decoy_id"] = self._generate_random_id()
        
        # Générer un nouvel ID pour le leurre
        decoy["id"] = f"decoy_{int(time.time())}_{random.randint(1000, 9999)}"
        
        return decoy
    
    def randomize_execution_timing(self, base_delay: float = 0) -> float:
        """
        Randomise le timing d'exécution
        
        Args:
            base_delay: Délai de base en secondes
            
        Returns:
            Délai total en secondes
        """
        if not self.protection_active or not self.config["obfuscation"]["timing_randomization"]:
            return base_delay
        
        # Ajouter une variation aléatoire au délai
        timing_noise = random.uniform(0.05, 0.5)  # 50ms à 500ms
        return base_delay + timing_noise
    
    def _generate_random_id(self) -> str:
        """
        Génère un identifiant aléatoire
        
        Returns:
            Identifiant aléatoire
        """
        random_bytes = os.urandom(16)
        return hashlib.md5(random_bytes).hexdigest()
    
    def encrypt_sensitive_data(self, data: Union[Dict, List, str], context: str = "general") -> str:
        """
        Chiffre des données sensibles
        
        Args:
            data: Données à chiffrer
            context: Contexte d'utilisation pour sélectionner la clé
            
        Returns:
            Données chiffrées (Base64)
        """
        if not self.config["encryption"]["enabled"]:
            # Si le chiffrement est désactivé, retourner les données en JSON encodé en Base64
            json_data = json.dumps(data)
            return base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
        
        # Récupérer la clé à utiliser en fonction du contexte
        key = self.obfuscation_keys.get(context, self.obfuscation_keys.get("trade_execution", "default_key"))
        
        # Dans un système réel, utiliser une bibliothèque de cryptographie
        # comme cryptography.io pour un chiffrement sécurisé
        
        # Simuler un chiffrement pour l'exemple
        json_data = json.dumps(data)
        # XOR basique (NON SÉCURISÉ - uniquement pour la démonstration)
        key_bytes = key.encode('utf-8')
        data_bytes = json_data.encode('utf-8')
        xored = bytes(a ^ key_bytes[i % len(key_bytes)] for i, a in enumerate(data_bytes))
        
        return base64.b64encode(xored).decode('utf-8')
    
    def decrypt_sensitive_data(self, encrypted_data: str, context: str = "general") -> Any:
        """
        Déchiffre des données sensibles
        
        Args:
            encrypted_data: Données chiffrées (Base64)
            context: Contexte d'utilisation pour sélectionner la clé
            
        Returns:
            Données déchiffrées
        """
        if not self.config["encryption"]["enabled"]:
            # Si le chiffrement est désactivé, décoder le Base64 et parser le JSON
            try:
                json_data = base64.b64decode(encrypted_data).decode('utf-8')
                return json.loads(json_data)
            except Exception as e:
                self.logger.error(f"Erreur de déchiffrement: {str(e)}")
                return None
        
        # Récupérer la clé à utiliser en fonction du contexte
        key = self.obfuscation_keys.get(context, self.obfuscation_keys.get("trade_execution", "default_key"))
        
        # Dans un système réel, utiliser une bibliothèque de cryptographie
        
        # Simuler un déchiffrement pour l'exemple
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            key_bytes = key.encode('utf-8')
            # XOR inverse
            xored = bytes(a ^ key_bytes[i % len(key_bytes)] for i, a in enumerate(encrypted_bytes))
            json_data = xored.decode('utf-8')
            
            return json.loads(json_data)
        except Exception as e:
            self.logger.error(f"Erreur de déchiffrement: {str(e)}")
            return None
    
    def _handle_outgoing_trade(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les trades sortants
        
        Args:
            data: Données du trade
        """
        # Vérifier le niveau de protection requis
        protection_level = self.config["protection_levels"].get("trade_data", "medium")
        
        if protection_level == "high" or protection_level == "very_high":
            # Obfusquer les données du trade
            obfuscated_data = self.obfuscate_trade_data(data)
            
            # Créer un ordre leurre si nécessaire
            decoy_order = self.add_decoy_order(data)
            
            # Publier le trade obfusqué
            self.event_bus.publish("obfuscated_trade", obfuscated_data)
            
            # Publier l'ordre leurre si créé
            if decoy_order:
                self.event_bus.publish("outgoing_trade", decoy_order)
    
    def _handle_market_data(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les données de marché
        
        Args:
            data: Données de marché
        """
        # Les données de marché ne sont généralement pas obfusquées
        # car elles proviennent de sources externes
        pass
    
    def _handle_api_call(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les appels API
        
        Args:
            data: Données de l'appel API
        """
        # Vérifier le niveau de protection requis
        protection_level = self.config["protection_levels"].get("api_communication", "high")
        
        if protection_level == "high" or protection_level == "very_high":
            # Chiffrer les données sensibles
            if "payload" in data:
                data["payload"] = self.encrypt_sensitive_data(data["payload"], "api_communication")
            
            # Randomiser le timing
            delay = self.randomize_execution_timing()
            if delay > 0:
                time.sleep(delay)
            
            # Surveiller la fréquence des appels API
            if self.config["monitoring"]["exchange_api_calls"]:
                self._monitor_api_call(data)
    
    def _handle_trade_signal(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les signaux de trading
        
        Args:
            data: Données du signal
        """
        # Vérifier le niveau de protection requis
        protection_level = self.config["protection_levels"].get("signal_generation", "medium")
        
        if protection_level == "high" or protection_level == "very_high":
            # Obfusquer les paramètres du signal
            if "parameters" in data:
                noise_factor = self.config["obfuscation"]["parameter_noise"]
                
                for param, value in data["parameters"].items():
                    if isinstance(value, (int, float)):
                        variation = 1.0 + (random.random() * 2 - 1) * noise_factor
                        data["parameters"][param] = value * variation
    
    def _handle_config_update(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les mises à jour de configuration
        
        Args:
            data: Données de mise à jour de configuration
        """
        updates = data.get("updates", {})
        
        for section, section_updates in updates.items():
            if section in self.config:
                for key, value in section_updates.items():
                    if key in self.config[section]:
                        self.logger.info(f"Mise à jour de la configuration: {section}.{key} = {value}")
                        self.config[section][key] = value
    
    def _monitor_api_call(self, data: Dict[str, Any]):
        """
        Surveille les appels API pour détecter des patterns suspects
        
        Args:
            data: Données de l'appel API
        """
        # Enregistrer l'appel API
        api_call = {
            "endpoint": data.get("endpoint", "unknown"),
            "method": data.get("method", "GET"),
            "timestamp": time.time()
        }
        
        # Ajouter à la liste des activités suspectes pour analyse ultérieure
        self.suspicious_activities.append({
            "type": "api_frequency",
            "data": api_call,
            "timestamp": time.time()
        })

if __name__ == "__main__":
    # Test simple de l'obfuscateur
    obfuscator = FlowObfuscator()
    obfuscator.start()
    
    # Simuler un trade sortant
    test_trade = {
        "id": "trade123",
        "exchange": "bybit",
        "symbol": "BTC/USDT",
        "direction": "long",
        "size": 0.1,
        "entry_price": 48500,
        "timestamp": time.time()
    }
    
    obfuscator._handle_outgoing_trade(test_trade)
    
    # Tester l'obfuscation
    obfuscated = obfuscator.obfuscate_trade_data(test_trade)
    print(f"Original: {test_trade}")
    print(f"Obfuscated: {obfuscated}")
    
    time.sleep(2)  # Attente pour traitement
    obfuscator.stop()
