#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KairosShadowMode.py - Module d'audit passif IA, stabilité, alertes pour FlowGlobalDynamics™
"""

import logging
import time
import threading
import json
import os
import uuid
import random
from typing import Dict, Any, List, Optional, Tuple, Callable, Set

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

class KairosShadowMode:
    """
    Module d'audit passif pour l'IA, la stabilité et les alertes
    """
    
    def __init__(self):
        """Initialisation du KairosShadowMode"""
        self.running = False
        self.threads = {}
        self.logger = self._setup_logger()
        self.event_bus = get_event_bus()
        self.config = self._load_configuration()
        
        # État interne
        self.module_states = {}
        self.event_history = []
        self.alerts = []
        self.anomalies = []
        self.stability_metrics = {}
        self.performance_metrics = {}
        self.monitored_events = set()
        self.last_audit_report = 0
        self.system_health_score = 1.0  # 0.0-1.0, 1.0 = parfaitement sain
        
        # Compteurs et statistiques
        self.event_counters = {}
        self.ai_decisions = []
        self.resource_usage = {}
        
    def _setup_logger(self):
        """Configuration du logger"""
        logger = logging.getLogger("KairosShadowMode")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Charge la configuration de l'auditeur
        
        Returns:
            Configuration de l'auditeur
        """
        # Configuration par défaut
        default_config = {
            "audit_intervals": {
                "system_health_seconds": 60,    # 1 minute
                "performance_report_seconds": 300,  # 5 minutes
                "stability_check_seconds": 180,  # 3 minutes
                "ai_audit_seconds": 600,    # 10 minutes
                "detailed_report_seconds": 3600  # 1 heure
            },
            "event_monitoring": {
                "max_history_size": 10000,
                "critical_events": [
                    "emergency_shutdown", 
                    "integrity_failure", 
                    "risk_action",
                    "protection_alert",
                    "deep_optimization_started"
                ],
                "performance_events": [
                    "trade_result",
                    "position_closed",
                    "market_opportunities",
                    "strategy_optimized"
                ]
            },
            "anomaly_detection": {
                "baseline_window_hours": 24,
                "detection_sensitivity": 0.7,  # 0.0-1.0
                "min_confidence_threshold": 0.6
            },
            "stability_thresholds": {
                "cpu_percent_max": 85,
                "memory_percent_max": 80,
                "resource_growth_percent_max": 10,  # Croissance max en % par heure
                "event_rate_change_max": 200,  # % max de changement du taux d'événements
                "error_rate_percent_max": 5
            },
            "ai_audit": {
                "decision_sampling_rate": 0.1,  # Échantillonner 10% des décisions
                "max_decisions_stored": 1000,
                "monitor_conflicting_signals": True,
                "monitor_strategy_consistency": True
            },
            "alert_settings": {
                "max_alerts_per_hour": 10,
                "alert_cooldown_seconds": 300,  # 5 minutes entre alertes similaires
                "alert_aggregation": True,
                "notification_levels": ["critical", "warning", "info"]
            },
            "report_settings": {
                "report_format": "json",
                "include_metrics": True,
                "include_anomalies": True,
                "include_alerts": True,
                "max_report_size": 1000,
                "reports_directory": "./reports"
            }
        }
        
        try:
            # Tenter de charger depuis un fichier (désactivé pour l'exemple)
            # with open("kairos_config.json", "r") as f:
            #     return json.load(f)
            return default_config
        except Exception as e:
            self.logger.warning(f"Impossible de charger la configuration: {str(e)}. Utilisation des valeurs par défaut.")
            return default_config
    
    def start(self):
        """Démarrage de l'auditeur"""
        if self.running:
            self.logger.warning("KairosShadowMode est déjà en cours d'exécution")
            return
            
        self.running = True
        
        # Initialiser les événements à surveiller
        self._initialize_monitored_events()
        
        # Démarrage des threads d'audit
        self._start_audit_threads()
        
        self._register_events()
        self.logger.info("KairosShadowMode démarré en mode audit passif")
        
    def stop(self):
        """Arrêt de l'auditeur"""
        if not self.running:
            self.logger.warning("KairosShadowMode n'est pas en cours d'exécution")
            return
            
        self.running = False
        
        # Générer un rapport final
        self._generate_detailed_report()
        
        # Arrêt des threads d'audit
        for thread_name, thread in self.threads.items():
            if thread and thread.is_alive():
                thread.join(timeout=2.0)
                self.logger.debug(f"Thread {thread_name} arrêté")
        
        self._unregister_events()
        self.logger.info("KairosShadowMode arrêté")
    
    def _initialize_monitored_events(self):
        """Initialise la liste des événements à surveiller"""
        # Événements critiques du système
        for event_type in self.config["event_monitoring"]["critical_events"]:
            self.monitored_events.add(event_type)
            self.event_counters[event_type] = 0
        
        # Événements de performance
        for event_type in self.config["event_monitoring"]["performance_events"]:
            self.monitored_events.add(event_type)
            self.event_counters[event_type] = 0
        
        # Ajouter d'autres événements d'intérêt
        additional_events = [
            "market_data_update", "strategy_optimization", "module_optimization",
            "resource_optimization_needed", "trading_optimization", "countermeasure_applied",
            "obfuscated_trade", "integrity_status", "vault_unlock"
        ]
        
        for event_type in additional_events:
            self.monitored_events.add(event_type)
            self.event_counters[event_type] = 0
    
    def _start_audit_threads(self):
        """Démarre les threads d'audit"""
        # Thread de surveillance système
        self.threads["system_health"] = threading.Thread(
            target=self._system_health_loop, 
            daemon=True
        )
        self.threads["system_health"].start()
        
        # Thread d'audit de performance
        self.threads["performance_audit"] = threading.Thread(
            target=self._performance_audit_loop, 
            daemon=True
        )
        self.threads["performance_audit"].start()
        
        # Thread de surveillance de stabilité
        self.threads["stability_check"] = threading.Thread(
            target=self._stability_check_loop, 
            daemon=True
        )
        self.threads["stability_check"].start()
        
        # Thread d'audit IA
        self.threads["ai_audit"] = threading.Thread(
            target=self._ai_audit_loop, 
            daemon=True
        )
        self.threads["ai_audit"].start()
        
        # Thread de génération de rapport
        self.threads["report_generator"] = threading.Thread(
            target=self._report_generator_loop, 
            daemon=True
        )
        self.threads["report_generator"].start()
    
    def _register_events(self):
        """Enregistrement des abonnements aux événements"""
        # Abonnement à tous les événements pour le mode audit passif
        # C'est intentionnellement générique pour capter toutes les interactions
        self.event_bus.subscribe("", self._handle_any_event)
        
        # Abonnements spécifiques pour les événements critiques
        for event_type in self.config["event_monitoring"]["critical_events"]:
            self.event_bus.subscribe(event_type, self._handle_critical_event)
        
        # Abonnements pour les événements de performance
        for event_type in self.config["event_monitoring"]["performance_events"]:
            self.event_bus.subscribe(event_type, self._handle_performance_event)
        
        # Abonnements particuliers
        self.event_bus.subscribe("module_performance", self._handle_module_performance)
        self.event_bus.subscribe("system_status", self._handle_system_status)
        self.event_bus.subscribe("trade_signal", self._handle_trade_signal)
        self.event_bus.subscribe("market_data_update", self._handle_market_data)
        self.event_bus.subscribe("audit_request", self._handle_audit_request)
    
    def _unregister_events(self):
        """Désenregistrement des abonnements aux événements"""
        # Désabonnement à tous les événements
        self.event_bus.unsubscribe("", self._handle_any_event)
        
        # Désabonnements spécifiques
        for event_type in self.config["event_monitoring"]["critical_events"]:
            self.event_bus.unsubscribe(event_type, self._handle_critical_event)
        
        for event_type in self.config["event_monitoring"]["performance_events"]:
            self.event_bus.unsubscribe(event_type, self._handle_performance_event)
        
        self.event_bus.unsubscribe("module_performance", self._handle_module_performance)
        self.event_bus.unsubscribe("system_status", self._handle_system_status)
        self.event_bus.unsubscribe("trade_signal", self._handle_trade_signal)
        self.event_bus.unsubscribe("market_data_update", self._handle_market_data)
        self.event_bus.unsubscribe("audit_request", self._handle_audit_request)
    
    def _system_health_loop(self):
        """Boucle de surveillance de la santé du système"""
        while self.running:
            try:
                # Collecter les métriques de santé du système
                system_metrics = self._collect_system_metrics()
                
                # Calculer le score de santé du système
                self.system_health_score = self._calculate_health_score(system_metrics)
                
                # Vérifier si des alertes sont nécessaires
                if self.system_health_score < 0.6:
                    self._trigger_health_alert(system_metrics)
                
                # Publier l'état de santé
                self.event_bus.publish("shadow_health_status", {
                    "health_score": self.system_health_score,
                    "metrics": system_metrics,
                    "timestamp": time.time()
                })
                
                # Attendre jusqu'à la prochaine vérification
                sleep_time = self.config["audit_intervals"]["system_health_seconds"]
                time.sleep(sleep_time)
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de santé du système: {str(e)}")
                time.sleep(30)
    
    def _performance_audit_loop(self):
        """Boucle d'audit de performance"""
        # Attendre un court moment avant de démarrer
        time.sleep(5)
        
        while self.running:
            try:
                # Analyser les métriques de performance
                performance_report = self._analyze_performance_metrics()
                
                # Sauvegarder le rapport
                self.performance_metrics = performance_report
                
                # Identifier les problèmes de performance
                if performance_report.get("issues"):
                    for issue in performance_report["issues"]:
                        self._add_alert("performance", issue["description"], issue["severity"], details=issue)
                
                # Publier le rapport de performance
                self.event_bus.publish("shadow_performance_report", {
                    "metrics": performance_report,
                    "timestamp": time.time()
                })
                
                # Attendre jusqu'à la prochaine vérification
                sleep_time = self.config["audit_intervals"]["performance_report_seconds"]
                time.sleep(sleep_time)
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle d'audit de performance: {str(e)}")
                time.sleep(60)
    
    def _stability_check_loop(self):
        """Boucle de vérification de stabilité"""
        # Attendre un court moment avant de démarrer
        time.sleep(10)
        
        while self.running:
            try:
                # Vérifier la stabilité du système
                stability_report = self._check_system_stability()
                
                # Sauvegarder le rapport
                self.stability_metrics = stability_report
                
                # Identifier les problèmes de stabilité
                if stability_report.get("instabilities"):
                    for instability in stability_report["instabilities"]:
                        self._add_alert("stability", instability["description"], instability["severity"], details=instability)
                
                # Publier le rapport de stabilité
                self.event_bus.publish("shadow_stability_report", {
                    "metrics": stability_report,
                    "timestamp": time.time()
                })
                
                # Attendre jusqu'à la prochaine vérification
                sleep_time = self.config["audit_intervals"]["stability_check_seconds"]
                time.sleep(sleep_time)
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de vérification de stabilité: {str(e)}")
                time.sleep(60)
    
    def _ai_audit_loop(self):
        """Boucle d'audit de l'IA"""
        # Attendre avant de démarrer pour accumuler des données
        time.sleep(30)
        
        while self.running:
            try:
                # Analyser les décisions de l'IA
                ai_audit_report = self._audit_ai_decisions()
                
                # Identifier les anomalies
                if ai_audit_report.get("anomalies"):
                    for anomaly in ai_audit_report["anomalies"]:
                        self._add_anomaly(anomaly)
                
                # Publier le rapport d'audit IA
                self.event_bus.publish("shadow_ai_audit", {
                    "report": ai_audit_report,
                    "timestamp": time.time()
                })
                
                # Attendre jusqu'à la prochaine vérification
                sleep_time = self.config["audit_intervals"]["ai_audit_seconds"]
                time.sleep(sleep_time)
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle d'audit IA: {str(e)}")
                time.sleep(120)
    
    def _report_generator_loop(self):
        """Boucle de génération de rapports détaillés"""
        # Attendre avant de démarrer pour accumuler des données
        time.sleep(60)
        
        while self.running:
            try:
                current_time = time.time()
                
                # Générer un rapport détaillé périodiquement
                if current_time - self.last_audit_report > self.config["audit_intervals"]["detailed_report_seconds"]:
                    self._generate_detailed_report()
                    self.last_audit_report = current_time
                
                # Attendre jusqu'à la prochaine vérification
                time.sleep(300)  # 5 minutes
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de génération de rapports: {str(e)}")
                time.sleep(300)
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """
        Collecte les métriques système
        
        Returns:
            Métriques système
        """
        # Simuler la collecte de métriques pour l'exemple
        # Dans un système réel, utiliser des bibliothèques comme psutil
        metrics = {
            "cpu": {
                "usage_percent": random.uniform(20, 70),
                "temperature": random.uniform(40, 70),
                "load_avg": [random.uniform(0.5, 2.0), random.uniform(0.5, 2.0), random.uniform(0.5, 2.0)]
            },
            "memory": {
                "usage_percent": random.uniform(30, 80),
                "available_mb": random.uniform(2000, 8000),
                "swap_usage_percent": random.uniform(10, 50)
            },
            "disk": {
                "usage_percent": random.uniform(40, 80),
                "io_wait_percent": random.uniform(0.1, 5.0),
                "write_rate_mb_s": random.uniform(0.5, 10.0),
                "read_rate_mb_s": random.uniform(0.5, 10.0)
            },
            "network": {
                "latency_ms": random.uniform(20, 100),
                "packet_loss_percent": random.uniform(0, 2.0),
                "bandwidth_usage_percent": random.uniform(10, 60)
            },
            "modules": {
                "active_count": len(self.module_states),
                "error_states": sum(1 for m in self.module_states.values() if m.get("state") == "error"),
                "warning_states": sum(1 for m in self.module_states.values() if m.get("state") == "warning")
            },
            "events": {
                "rate_per_second": sum(self.event_counters.values()) / max(1, self.config["audit_intervals"]["system_health_seconds"]),
                "critical_count": sum(self.event_counters.get(e, 0) for e in self.config["event_monitoring"]["critical_events"]),
                "total_count": sum(self.event_counters.values())
            },
            "errors": {
                "count_last_minute": random.randint(0, 10),
                "rate_per_hour": random.uniform(0, 50)
            },
            "timestamp": time.time()
        }
        
        # Réinitialiser les compteurs d'événements
        for event_type in self.event_counters:
            self.event_counters[event_type] = 0
        
        # Sauvegarder pour l'historique de ressources
        self.resource_usage[int(metrics["timestamp"])] = {
            "cpu": metrics["cpu"]["usage_percent"],
            "memory": metrics["memory"]["usage_percent"],
            "disk": metrics["disk"]["usage_percent"],
            "network": metrics["network"]["bandwidth_usage_percent"]
        }
        
        # Limiter la taille de l'historique
        max_entries = 24 * 60  # 24 heures à raison d'une entrée par minute
        if len(self.resource_usage) > max_entries:
            oldest_keys = sorted(self.resource_usage.keys())[:len(self.resource_usage) - max_entries]
            for key in oldest_keys:
                del self.resource_usage[key]
        
        return metrics
    
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """
        Calcule un score de santé du système
        
        Args:
            metrics: Métriques système
            
        Returns:
            Score de santé (0.0-1.0)
        """
        # Calculer des scores partiels
        cpu_score = 1.0 - (metrics["cpu"]["usage_percent"] / 100)
        memory_score = 1.0 - (metrics["memory"]["usage_percent"] / 100)
        disk_score = 1.0 - (metrics["disk"]["usage_percent"] / 100)
        network_score = 1.0 - (metrics["network"]["packet_loss_percent"] / 10)  # 10% de perte = score 0
        
        # Score modules
        total_modules = max(1, metrics["modules"]["active_count"])
        error_ratio = metrics["modules"]["error_states"] / total_modules
        warning_ratio = metrics["modules"]["warning_states"] / total_modules
        modules_score = 1.0 - (error_ratio * 0.7 + warning_ratio * 0.3)
        
        # Score erreurs (inverse de la fréquence des erreurs)
        error_rate = metrics["errors"]["rate_per_hour"]
        error_score = 1.0 - min(1.0, error_rate / 100)  # 100 erreurs/heure = score 0
        
        # Pondération des scores
        weights = {
            "cpu": 0.2,
            "memory": 0.2,
            "disk": 0.1,
            "network": 0.2,
            "modules": 0.2,
            "errors": 0.1
        }
        
        # Calcul du score global
        health_score = (
            weights["cpu"] * cpu_score +
            weights["memory"] * memory_score +
            weights["disk"] * disk_score +
            weights["network"] * network_score +
            weights["modules"] * modules_score +
            weights["errors"] * error_score
        )
        
        return max(0.0, min(1.0, health_score))
    
    def _trigger_health_alert(self, metrics: Dict[str, Any]):
        """
        Déclenche une alerte de santé système
        
        Args:
            metrics: Métriques système
        """
        # Déterminer la gravité de l'alerte
        if self.system_health_score < 0.3:
            severity = "critical"
            message = "Santé système critique"
        elif self.system_health_score < 0.5:
            severity = "high"
            message = "Santé système faible"
        else:
            severity = "medium"
            message = "Santé système dégradée"
        
        # Identifier les sous-systèmes problématiques
        issues = []
        
        if metrics["cpu"]["usage_percent"] > 85:
            issues.append("CPU surchargé")
        if metrics["memory"]["usage_percent"] > 90:
            issues.append("Mémoire presque épuisée")
        if metrics["disk"]["usage_percent"] > 95:
            issues.append("Espace disque presque épuisé")
        if metrics["network"]["packet_loss_percent"] > 5:
            issues.append("Perte de paquets réseau importante")
        if metrics["modules"]["error_states"] > 0:
            issues.append(f"{metrics['modules']['error_states']} module(s) en erreur")
        if metrics["errors"]["rate_per_hour"] > 50:
            issues.append("Taux d'erreurs élevé")
        
        # Ajouter l'alerte
        self._add_alert(
            "system_health", 
            f"{message}: {', '.join(issues)}",
            severity,
            details={
                "health_score": self.system_health_score,
                "issues": issues,
                "metrics": {k: v for k, v in metrics.items() if k != "timestamp"}
            }
        )
    
    def _analyze_performance_metrics(self) -> Dict[str, Any]:
        """
        Analyse les métriques de performance
        
        Returns:
            Rapport de performance
        """
        # Analyser les performances des modules
        module_performance = {}
        issues = []
        
        for module_name, state in self.module_states.items():
            if "performance" in state:
                module_performance[module_name] = {
                    "latency_ms": state["performance"].get("latency_ms", 0),
                    "throughput": state["performance"].get("throughput", 0),
                    "error_rate": state["performance"].get("error_rate", 0),
                    "cpu_percent": state["performance"].get("cpu_percent", 0),
                    "memory_percent": state["performance"].get("memory_percent", 0)
                }
                
                # Détecter les problèmes de performance
                if state["performance"].get("latency_ms", 0) > 500:
                    issues.append({
                        "module": module_name,
                        "type": "high_latency",
                        "description": f"Latence élevée dans {module_name}: {state['performance'].get('latency_ms')} ms",
                        "severity": "medium",
                        "value": state["performance"].get("latency_ms")
                    })
                
                if state["performance"].get("error_rate", 0) > 0.05:
                    issues.append({
                        "module": module_name,
                        "type": "high_error_rate",
                        "description": f"Taux d'erreur élevé dans {module_name}: {state['performance'].get('error_rate')*100:.1f}%",
                        "severity": "high",
                        "value": state["performance"].get("error_rate")
                    })
                
                if state["performance"].get("cpu_percent", 0) > 80:
                    issues.append({
                        "module": module_name,
                        "type": "high_cpu_usage",
                        "description": f"Utilisation CPU élevée par {module_name}: {state['performance'].get('cpu_percent')}%",
                        "severity": "medium",
                        "value": state["performance"].get("cpu_percent")
                    })
                
                if state["performance"].get("memory_percent", 0) > 80:
                    issues.append({
                        "module": module_name,
                        "type": "high_memory_usage",
                        "description": f"Utilisation mémoire élevée par {module_name}: {state['performance'].get('memory_percent')}%",
                        "severity": "medium",
                        "value": state["performance"].get("memory_percent")
                    })
        
        # Analyser les performances des trades
        trade_performance = self._analyze_trade_performance()
        
        # Compiler le rapport de performance
        performance_report = {
            "modules": module_performance,
            "trading": trade_performance,
            "issues": issues,
            "timestamp": time.time()
        }
        
        return performance_report
    
    def _analyze_trade_performance(self) -> Dict[str, Any]:
        """
        Analyse les performances des trades
        
        Returns:
            Métriques de performance des trades
        """
        # Rechercher les événements de résultats de trades dans l'historique
        trade_results = [
            event for event in self.event_history 
            if event["event_type"] == "trade_result"
        ]
        
        if not trade_results:
            return {
                "trades_count": 0,
                "win_rate": 0,
                "avg_profit": 0,
                "total_profit": 0
            }
        
        # Calculer les métriques
        wins = [t for t in trade_results if t["data"].get("profit", 0) > 0]
        losses = [t for t in trade_results if t["data"].get("profit", 0) <= 0]
        
        win_rate = len(wins) / len(trade_results) if trade_results else 0
        
        profits = [t["data"].get("profit", 0) for t in trade_results]
        avg_profit = sum(profits) / len(profits) if profits else 0
        total_profit = sum(profits)
        
        # Calculer par stratégie
        strategies = {}
        for trade in trade_results:
            strategy = trade["data"].get("strategy", "unknown")
            if strategy not in strategies:
                strategies[strategy] = {
                    "trades_count": 0,
                    "wins_count": 0,
                    "losses_count": 0,
                    "total_profit": 0
                }
            
            strategies[strategy]["trades_count"] += 1
            
            profit = trade["data"].get("profit", 0)
            strategies[strategy]["total_profit"] += profit
            
            if profit > 0:
                strategies[strategy]["wins_count"] += 1
            else:
                strategies[strategy]["losses_count"] += 1
        
        # Calculer les taux de réussite par stratégie
        for strategy, data in strategies.items():
            data["win_rate"] = data["wins_count"] / data["trades_count"] if data["trades_count"] > 0 else 0
            data["avg_profit"] = data["total_profit"] / data["trades_count"] if data["trades_count"] > 0 else 0
        
        return {
            "trades_count": len(trade_results),
            "win_rate": win_rate,
            "avg_profit": avg_profit,
            "total_profit": total_profit,
            "strategies": strategies
        }
    
    def _check_system_stability(self) -> Dict[str, Any]:
        """
        Vérifie la stabilité du système
        
        Returns:
            Rapport de stabilité
        """
        instabilities = []
        stability_scores = {}
        
        # Vérifier la stabilité des ressources (croissance anormale)
        resource_stability = self._check_resource_stability()
        
        if resource_stability["unstable_resources"]:
            for resource, data in resource_stability["unstable_resources"].items():
                instabilities.append({
                    "type": f"{resource}_growth",
                    "description": f"Croissance anormale de l'utilisation {resource}: {data['growth_percent']:.1f}%",
                    "severity": "high" if data["growth_percent"] > 20 else "medium",
                    "details": data
                })
            
            stability_scores["resources"] = resource_stability["stability_score"]
        else:
            stability_scores["resources"] = 1.0
        
        # Vérifier la stabilité des taux d'événements
        event_stability = self._check_event_rate_stability()
        
        if event_stability["unstable_events"]:
            for event_type, data in event_stability["unstable_events"].items():
                instabilities.append({
                    "type": f"{event_type}_rate_change",
                    "description": f"Changement anormal du taux d'événements {event_type}: {data['change_percent']:.1f}%",
                    "severity": "high" if data["change_percent"] > 300 else "medium",
                    "details": data
                })
            
            stability_scores["events"] = event_stability["stability_score"]
        else:
            stability_scores["events"] = 1.0
        
        # Vérifier la stabilité des erreurs
        error_stability = self._check_error_stability()
        
        if error_stability["high_error_modules"]:
            for module, data in error_stability["high_error_modules"].items():
                instabilities.append({
                    "type": f"{module}_high_errors",
                    "description": f"Taux d'erreur élevé dans {module}: {data['error_rate']*100:.1f}%",
                    "severity": "critical" if data["error_rate"] > 0.1 else "high",
                    "details": data
                })
            
            stability_scores["errors"] = error_stability["stability_score"]
        else:
            stability_scores["errors"] = 1.0
        
        # Calculer le score de stabilité global
        overall_stability = sum(stability_scores.values()) / len(stability_scores) if stability_scores else 1.0
        
        return {
            "overall_stability": overall_stability,
            "stability_scores": stability_scores,
            "instabilities": instabilities,
            "resource_stability": resource_stability,
            "event_stability": event_stability,
            "error_stability": error_stability,
            "timestamp": time.time()
        }
    
    def _check_resource_stability(self) -> Dict[str, Any]:
        """
        Vérifie la stabilité des ressources
        
        Returns:
            Rapport de stabilité des ressources
        """
        if len(self.resource_usage) < 10:
            return {"stable": True, "stability_score": 1.0, "unstable_resources": {}}
        
        # Calculer la croissance des ressources sur la dernière heure
        current_time = time.time()
        one_hour_ago = current_time - 3600
        
        recent_usage = {}
        old_usage = {}
        
        # Trouver l'utilisation récente et l'ancienne
        for timestamp, usage in self.resource_usage.items():
            if timestamp > current_time - 300:  # Dernières 5 minutes
                for resource, value in usage.items():
                    if resource not in recent_usage:
                        recent_usage[resource] = []
                    recent_usage[resource].append(value)
            elif one_hour_ago <= timestamp <= one_hour_ago + 300:  # 5 minutes autour d'il y a 1 heure
                for resource, value in usage.items():
                    if resource not in old_usage:
                        old_usage[resource] = []
                    old_usage[resource].append(value)
        
        # Calculer les moyennes et la croissance
        unstable_resources = {}
        stability_scores = {}
        
        for resource in ["cpu", "memory", "disk", "network"]:
            if resource in recent_usage and resource in old_usage and old_usage[resource]:
                recent_avg = sum(recent_usage[resource]) / len(recent_usage[resource])
                old_avg = sum(old_usage[resource]) / len(old_usage[resource])
                
                if old_avg > 0:
                    growth_percent = ((recent_avg - old_avg) / old_avg) * 100
                    
                    # Vérifier si la croissance est anormale
                    max_growth = self.config["stability_thresholds"]["resource_growth_percent_max"]
                    
                    if growth_percent > max_growth:
                        unstable_resources[resource] = {
                            "recent_avg": recent_avg,
                            "old_avg": old_avg,
                            "growth_percent": growth_percent,
                            "threshold": max_growth
                        }
                        
                        # Calculer un score de stabilité inversement proportionnel à la croissance
                        stability_scores[resource] = max(0.0, 1.0 - (growth_percent / (max_growth * 2)))
                    else:
                        stability_scores[resource] = 1.0
                else:
                    stability_scores[resource] = 1.0
            else:
                stability_scores[resource] = 1.0
        
        # Calculer le score de stabilité global
        overall_stability = sum(stability_scores.values()) / len(stability_scores) if stability_scores else 1.0
        
        return {
            "stability_score": overall_stability,
            "unstable_resources": unstable_resources
        }
    
    def _check_event_rate_stability(self) -> Dict[str, Any]:
        """
        Vérifie la stabilité des taux d'événements
        
        Returns:
            Rapport de stabilité des taux d'événements
        """
        # Regrouper les événements par type et par intervalle de temps
        current_time = time.time()
        recent_window = current_time - 600  # Dernières 10 minutes
        previous_window = recent_window - 600  # 10 minutes précédentes
        
        recent_counts = {}
        previous_counts = {}
        
        for event in self.event_history:
            event_type = event["event_type"]
            timestamp = event["timestamp"]
            
            if timestamp >= recent_window:
                recent_counts[event_type] = recent_counts.get(event_type, 0) + 1
            elif previous_window <= timestamp < recent_window:
                previous_counts[event_type] = previous_counts.get(event_type, 0) + 1
        
        # Calculer les changements de taux
        unstable_events = {}
        stability_scores = {}
        
        for event_type in set(recent_counts.keys()) | set(previous_counts.keys()):
            recent_count = recent_counts.get(event_type, 0)
            previous_count = previous_counts.get(event_type, 0)
            
            if previous_count > 5:  # Ignorer les événements rares
                change_percent = ((recent_count - previous_count) / previous_count) * 100
                
                # Vérifier si le changement est anormal
                max_change = self.config["stability_thresholds"]["event_rate_change_max"]
                
                if abs(change_percent) > max_change:
                    unstable_events[event_type] = {
                        "recent_count": recent_count,
                        "previous_count": previous_count,
                        "change_percent": change_percent,
                        "threshold": max_change
                    }
                    
                    # Calculer un score de stabilité inversement proportionnel au changement
                    stability_scores[event_type] = max(0.0, 1.0 - (abs(change_percent) / (max_change * 2)))
                else:
                    stability_scores[event_type] = 1.0
            else:
                stability_scores[event_type] = 1.0
        
        # Calculer le score de stabilité global
        overall_stability = sum(stability_scores.values()) / len(stability_scores) if stability_scores else 1.0
        
        return {
            "stability_score": overall_stability,
            "unstable_events": unstable_events
        }
    
    def _check_error_stability(self) -> Dict[str, Any]:
        """
        Vérifie la stabilité des taux d'erreurs
        
        Returns:
            Rapport de stabilité des erreurs
        """
        high_error_modules = {}
        stability_scores = {}
        
        for module_name, state in self.module_states.items():
            if "performance" in state:
                error_rate = state["performance"].get("error_rate", 0)
                
                # Vérifier si le taux d'erreur dépasse le seuil
                max_error_rate = self.config["stability_thresholds"]["error_rate_percent_max"] / 100
                
                if error_rate > max_error_rate:
                    high_error_modules[module_name] = {
                        "error_rate": error_rate,
                        "threshold": max_error_rate,
                        "error_count": state["performance"].get("error_count", 0),
                        "total_operations": state["performance"].get("total_operations", 0)
                    }
                    
                    # Calculer un score de stabilité inversement proportionnel au taux d'erreur
                    stability_scores[module_name] = max(0.0, 1.0 - (error_rate / (max_error_rate * 2)))
                else:
                    stability_scores[module_name] = 1.0
        
        # Calculer le score de stabilité global
        overall_stability = sum(stability_scores.values()) / len(stability_scores) if stability_scores else 1.0
        
        return {
            "stability_score": overall_stability,
            "high_error_modules": high_error_modules
        }
    
    def _audit_ai_decisions(self) -> Dict[str, Any]:
        """
        Audite les décisions de l'IA
        
        Returns:
            Rapport d'audit IA
        """
        # Filtrer pour ne conserver que les décisions récentes
        current_time = time.time()
        audit_window = 3600  # Dernière heure
        recent_decisions = [d for d in self.ai_decisions if current_time - d["timestamp"] < audit_window]
        
        if not recent_decisions:
            return {
                "decisions_count": 0,
                "anomalies": [],
                "decision_consistency": 1.0,
                "timestamp": current_time
            }
        
        # Analyser les décisions par type
        decisions_by_type = {}
        for decision in recent_decisions:
            decision_type = decision["type"]
            if decision_type not in decisions_by_type:
                decisions_by_type[decision_type] = []
            decisions_by_type[decision_type].append(decision)
        
        # Vérifier les anomalies
        anomalies = []
        
        # 1. Vérifier les signaux contradictoires
        if self.config["ai_audit"]["monitor_conflicting_signals"]:
            conflicting_signals = self._detect_conflicting_signals(recent_decisions)
            anomalies.extend(conflicting_signals)
        
        # 2. Vérifier la cohérence des stratégies
        if self.config["ai_audit"]["monitor_strategy_consistency"]:
            strategy_anomalies = self._check_strategy_consistency(decisions_by_type)
            anomalies.extend(strategy_anomalies)
        
        # Calculer un score de cohérence
        decision_consistency = 1.0 - (len(anomalies) / max(1, len(recent_decisions) / 10))
        
        return {
            "decisions_count": len(recent_decisions),
            "decision_types": {t: len(d) for t, d in decisions_by_type.items()},
            "anomalies": anomalies,
            "decision_consistency": max(0.0, min(1.0, decision_consistency)),
            "timestamp": current_time
        }
    
    def _detect_conflicting_signals(self, decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Détecte les signaux contradictoires
        
        Args:
            decisions: Liste des décisions à analyser
            
        Returns:
            Liste des anomalies détectées
        """
        # Regrouper les décisions par symbole et par fenêtre de temps (5 minutes)
        decisions_by_symbol = {}
        
        for decision in decisions:
            if decision["type"] not in ["trade_signal", "strategy_response"]:
                continue
                
            symbol = decision["data"].get("symbol")
            if not symbol:
                continue
                
            # Déterminer la fenêtre de temps (arrondir à 5 minutes)
            timestamp = decision["timestamp"]
            time_window = int(timestamp / 300) * 300  # 5 minutes
            
            if symbol not in decisions_by_symbol:
                decisions_by_symbol[symbol] = {}
                
            if time_window not in decisions_by_symbol[symbol]:
                decisions_by_symbol[symbol][time_window] = []
                
            decisions_by_symbol[symbol][time_window].append(decision)
        
        # Détecter les conflits dans chaque fenêtre de temps
        anomalies = []
        
        for symbol, windows in decisions_by_symbol.items():
            for time_window, window_decisions in windows.items():
                # Vérifier s'il y a des signaux longs et courts dans la même fenêtre
                long_signals = [d for d in window_decisions if d["data"].get("direction") == "long"]
                short_signals = [d for d in window_decisions if d["data"].get("direction") == "short"]
                
                if long_signals and short_signals:
                    anomalies.append({
                        "type": "conflicting_signals",
                        "description": f"Signaux contradictoires pour {symbol} dans la même fenêtre de temps",
                        "severity": "high",
                        "symbol": symbol,
                        "time_window": time_window,
                        "long_signals": len(long_signals),
                        "short_signals": len(short_signals)
                    })
        
        return anomalies
    
    def _check_strategy_consistency(self, decisions_by_type: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Vérifie la cohérence des stratégies
        
        Args:
            decisions_by_type: Décisions regroupées par type
            
        Returns:
            Liste des anomalies détectées
        """
        anomalies = []
        
        # Vérifier la cohérence des réponses de stratégie
        if "strategy_response" in decisions_by_type:
            strategy_responses = decisions_by_type["strategy_response"]
            
            # Compter les actions par stratégie
            actions_by_strategy = {}
            
            for response in strategy_responses:
                strategy = response["data"].get("strategy", "unknown")
                action = response["data"].get("action", "unknown")
                
                if strategy not in actions_by_strategy:
                    actions_by_strategy[strategy] = {}
                    
                if action not in actions_by_strategy[strategy]:
                    actions_by_strategy[strategy][action] = 0
                    
                actions_by_strategy[strategy][action] += 1
            
            # Vérifier si une stratégie change trop souvent d'action
            for strategy, actions in actions_by_strategy.items():
                total_responses = sum(actions.values())
                if total_responses >= 5:  # Ignorer les stratégies peu utilisées
                    most_common_action = max(actions.items(), key=lambda x: x[1])
                    most_common_ratio = most_common_action[1] / total_responses
                    
                    if most_common_ratio < 0.6:  # Si l'action la plus commune représente moins de 60% des réponses
                        anomalies.append({
                            "type": "strategy_inconsistency",
                            "description": f"La stratégie {strategy} change fréquemment d'action",
                            "severity": "medium",
                            "strategy": strategy,
                            "actions": actions,
                            "consistency_ratio": most_common_ratio
                        })
        
        return anomalies
    
    def _generate_detailed_report(self):
        """Génère un rapport d'audit détaillé"""
        report = {
            "timestamp": time.time(),
            "system_health": {
                "score": self.system_health_score,
                "status": "critical" if self.system_health_score < 0.3 else 
                          "warning" if self.system_health_score < 0.6 else 
                          "good"
            },
            "stability": {
                "metrics": self.stability_metrics
            },
            "performance": {
                "metrics": self.performance_metrics
            },
            "modules": {
                "count": len(self.module_states),
                "states": {m: s.get("state", "unknown") for m, s in self.module_states.items()}
            },
            "alerts": self._get_recent_alerts(24),  # Alertes des dernières 24h
            "anomalies": self._get_recent_anomalies(24),  # Anomalies des dernières 24h
            "events": {
                "count": len(self.event_history),
                "distribution": self._count_events_by_type(),
                "critical_events": self._get_critical_events(24)  # Événements critiques des dernières 24h
            }
        }
        
        # Sauvegarder le rapport
        if self.config["report_settings"]["include_metrics"]:
            reports_dir = self.config["report_settings"]["reports_directory"]
            
            try:
                os.makedirs(reports_dir, exist_ok=True)
                
                report_file = os.path.join(
                    reports_dir,
                    f"kairos_audit_{time.strftime('%Y%m%d_%H%M%S')}.json"
                )
                
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2)
                    
                self.logger.info(f"Rapport d'audit détaillé généré: {report_file}")
            except Exception as e:
                self.logger.error(f"Erreur lors de la génération du rapport: {str(e)}")
        
        # Publier le rapport
        self.event_bus.publish("shadow_audit_report", {
            "report": report,
            "timestamp": time.time()
        })
    
    def _count_events_by_type(self) -> Dict[str, int]:
        """
        Compte les événements par type
        
        Returns:
            Compteur d'événements par type
        """
        counts = {}
        
        for event in self.event_history:
            event_type = event["event_type"]
            counts[event_type] = counts.get(event_type, 0) + 1
            
        return counts
    
    def _get_critical_events(self, hours: int) -> List[Dict[str, Any]]:
        """
        Récupère les événements critiques sur une période
        
        Args:
            hours: Nombre d'heures à considérer
            
        Returns:
            Liste des événements critiques
        """
        current_time = time.time()
        time_threshold = current_time - (hours * 3600)
        
        critical_events = []
        
        for event in self.event_history:
            if event["timestamp"] >= time_threshold and event["event_type"] in self.config["event_monitoring"]["critical_events"]:
                critical_events.append(event)
                
        return critical_events
    
    def _get_recent_alerts(self, hours: int) -> List[Dict[str, Any]]:
        """
        Récupère les alertes récentes
        
        Args:
            hours: Nombre d'heures à considérer
            
        Returns:
            Liste des alertes récentes
        """
        current_time = time.time()
        time_threshold = current_time - (hours * 3600)
        
        return [a for a in self.alerts if a["timestamp"] >= time_threshold]
    
    def _get_recent_anomalies(self, hours: int) -> List[Dict[str, Any]]:
        """
        Récupère les anomalies récentes
        
        Args:
            hours: Nombre d'heures à considérer
            
        Returns:
            Liste des anomalies récentes
        """
        current_time = time.time()
        time_threshold = current_time - (hours * 3600)
        
        return [a for a in self.anomalies if a["timestamp"] >= time_threshold]
    
    def _add_alert(self, alert_type: str, message: str, severity: str, details: Dict[str, Any] = None):
        """
        Ajoute une alerte
        
        Args:
            alert_type: Type d'alerte
            message: Message d'alerte
            severity: Gravité de l'alerte
            details: Détails supplémentaires
        """
        # Vérifier si une alerte similaire a été émise récemment
        current_time = time.time()
        cooldown = self.config["alert_settings"]["alert_cooldown_seconds"]
        
        for alert in self.alerts:
            if (alert["type"] == alert_type and 
                current_time - alert["timestamp"] < cooldown):
                # Alerte similaire récente, ignorer
                return
        
        # Créer l'alerte
        alert = {
            "id": str(uuid.uuid4()),
            "type": alert_type,
            "message": message,
            "severity": severity,
            "details": details or {},
            "timestamp": current_time
        }
        
        # Ajouter l'alerte
        self.alerts.append(alert)
        
        # Limiter le nombre d'alertes
        max_alerts = 1000
        if len(self.alerts) > max_alerts:
            self.alerts = self.alerts[-max_alerts:]
        
        # Publier l'alerte
        self.event_bus.publish("shadow_alert", alert)
        
        # Logger l'alerte
        log_method = self.logger.warning if severity == "medium" else (
            self.logger.error if severity == "high" else 
            self.logger.critical if severity == "critical" else 
            self.logger.info
        )
        log_method(f"ALERTE {severity.upper()}: {message}")
    
    def _add_anomaly(self, anomaly: Dict[str, Any]):
        """
        Ajoute une anomalie
        
        Args:
            anomaly: Données de l'anomalie
        """
        # Ajouter un timestamp et un ID si non présents
        if "timestamp" not in anomaly:
            anomaly["timestamp"] = time.time()
            
        if "id" not in anomaly:
            anomaly["id"] = str(uuid.uuid4())
        
        # Ajouter l'anomalie
        self.anomalies.append(anomaly)
        
        # Limiter le nombre d'anomalies
        max_anomalies = 1000
        if len(self.anomalies) > max_anomalies:
            self.anomalies = self.anomalies[-max_anomalies:]
        
        # Publier l'anomalie
        self.event_bus.publish("shadow_anomaly", anomaly)
        
        # Logger l'anomalie
        severity = anomaly.get("severity", "medium")
        message = anomaly.get("description", "Anomalie détectée")
        
        log_method = self.logger.warning if severity == "medium" else (
            self.logger.error if severity == "high" else 
            self.logger.critical if severity == "critical" else 
            self.logger.info
        )
        log_method(f"ANOMALIE {severity.upper()}: {message}")
    
    def _handle_any_event(self, data: Dict[str, Any]):
        """
        Gestionnaire pour tous les événements
        
        Args:
            data: Données de l'événement
        """
        # Extraire les informations de l'événement
        event_type = self.event_bus.current_event_type
        
        # Ignorer certains événements pour éviter la surcharge
        ignore_types = ["shadow_", "module_performance"]
        if any(event_type.startswith(prefix) for prefix in ignore_types):
            return
        
        # Créer une entrée d'historique
        event_entry = {
            "event_type": event_type,
            "data": data,
            "timestamp": time.time()
        }
        
        # Ajouter à l'historique
        self.event_history.append(event_entry)
        
        # Limiter la taille de l'historique
        max_history = self.config["event_monitoring"]["max_history_size"]
        if len(self.event_history) > max_history:
            self.event_history = self.event_history[-max_history:]
        
        # Incrémenter le compteur d'événements
        if event_type in self.event_counters:
            self.event_counters[event_type] += 1
    
    def _handle_critical_event(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les événements critiques
        
        Args:
            data: Données de l'événement
        """
        event_type = self.event_bus.current_event_type
        
        # Créer une alerte pour l'événement critique
        message = f"Événement critique: {event_type}"
        details = {"event_type": event_type, "data": data}
        
        if event_type == "emergency_shutdown":
            message = f"Arrêt d'urgence demandé: {data.get('reason', 'Raison inconnue')}"
            severity = "critical"
        elif event_type == "integrity_failure":
            message = f"Défaillance d'intégrité: {data.get('details', 'Détails non disponibles')}"
            severity = "critical"
        elif event_type == "risk_action":
            action = data.get("action", "unknown")
            reason = data.get("reason", "Raison inconnue")
            message = f"Action de risque: {action} - {reason}"
            severity = "high" if action in ["close_all", "emergency_exit"] else "medium"
        elif event_type == "protection_alert":
            alert_type = data.get("type", "unknown")
            risk_score = data.get("risk_score", 0)
            message = f"Alerte de protection: {alert_type} - Score de risque: {risk_score:.2f}"
            severity = "critical" if risk_score > 0.8 else "high" if risk_score > 0.5 else "medium"
        elif event_type == "deep_optimization_started":
            message = "Optimisation profonde démarrée"
            severity = "medium"
        else:
            severity = "medium"
        
        self._add_alert(f"critical_event_{event_type}", message, severity, details)
    
    def _handle_performance_event(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les événements de performance
        
        Args:
            data: Données de l'événement
        """
        event_type = self.event_bus.current_event_type
        
        # Traiter les résultats de trades
        if event_type == "trade_result":
            # Ajouter aux décisions IA si l'échantillonnage est activé
            sampling_rate = self.config["ai_audit"]["decision_sampling_rate"]
            if random.random() < sampling_rate:
                self.ai_decisions.append({
                    "type": "trade_result",
                    "data": data,
                    "timestamp": time.time()
                })
                
                # Limiter le nombre de décisions stockées
                max_decisions = self.config["ai_audit"]["max_decisions_stored"]
                if len(self.ai_decisions) > max_decisions:
                    self.ai_decisions = self.ai_decisions[-max_decisions:]
        
        # Traiter les opportunités de marché
        elif event_type == "market_opportunities":
            opportunities = data.get("opportunities", [])
            
            # Échantillonner pour l'audit IA
            if opportunities and random.random() < self.config["ai_audit"]["decision_sampling_rate"]:
                self.ai_decisions.append({
                    "type": "market_opportunities",
                    "data": {
                        "count": len(opportunities),
                        "opportunities": opportunities[:3]  # Limiter aux 3 premières
                    },
                    "timestamp": time.time()
                })
    
    def _handle_module_performance(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les performances des modules
        
        Args:
            data: Données de performance
        """
        module_name = data.get("module")
        if not module_name:
            return
            
        # Mettre à jour l'état du module
        if module_name not in self.module_states:
            self.module_states[module_name] = {}
            
        self.module_states[module_name]["performance"] = data
        self.module_states[module_name]["last_update"] = time.time()
        
        # Déterminer l'état du module
        state = "normal"
        
        if data.get("error_rate", 0) > 0.1:
            state = "error"
        elif data.get("latency_ms", 0) > 500 or data.get("error_rate", 0) > 0.05:
            state = "warning"
            
        self.module_states[module_name]["state"] = state
    
    def _handle_system_status(self, data: Dict[str, Any]):
        """
        Gestionnaire pour le statut système
        
        Args:
            data: Données de statut
        """
        status_type = data.get("type")
        
        if status_type == "error":
            # Créer une alerte pour l'erreur système
            message = data.get("message", "Erreur système non spécifiée")
            self._add_alert("system_error", f"Erreur système: {message}", "high", data)
        elif status_type == "warning":
            # Créer une alerte pour l'avertissement système
            message = data.get("message", "Avertissement système non spécifié")
            self._add_alert("system_warning", f"Avertissement système: {message}", "medium", data)
    
    def _handle_trade_signal(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les signaux de trading
        
        Args:
            data: Données du signal
        """
        # Ajouter aux décisions IA si l'échantillonnage est activé
        sampling_rate = self.config["ai_audit"]["decision_sampling_rate"]
        if random.random() < sampling_rate:
            self.ai_decisions.append({
                "type": "trade_signal",
                "data": data,
                "timestamp": time.time()
            })
            
            # Limiter le nombre de décisions stockées
            max_decisions = self.config["ai_audit"]["max_decisions_stored"]
            if len(self.ai_decisions) > max_decisions:
                self.ai_decisions = self.ai_decisions[-max_decisions:]
    
    def _handle_market_data(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les données de marché
        
        Args:
            data: Données de marché
        """
        # Ne pas stocker toutes les mises à jour de marché (trop nombreuses)
        # Mais pourrait mettre à jour un état interne du marché
        pass
    
    def _handle_audit_request(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les demandes d'audit
        
        Args:
            data: Données de la demande
        """
        request_type = data.get("type", "general")
        request_id = data.get("request_id", str(uuid.uuid4()))
        
        # Générer le rapport demandé
        if request_type == "detailed":
            # Générer un rapport détaillé
            self._generate_detailed_report()
            
            self.event_bus.publish("audit_response", {
                "request_id": request_id,
                "type": "detailed",
                "status": "completed",
                "timestamp": time.time()
            })
        elif request_type == "system_health":
            # Générer un rapport de santé du système
            system_metrics = self._collect_system_metrics()
            health_score = self._calculate_health_score(system_metrics)
            
            self.event_bus.publish("audit_response", {
                "request_id": request_id,
                "type": "system_health",
                "health_score": health_score,
                "metrics": system_metrics,
                "timestamp": time.time()
            })
        elif request_type == "performance":
            # Générer un rapport de performance
            performance_report = self._analyze_performance_metrics()
            
            self.event_bus.publish("audit_response", {
                "request_id": request_id,
                "type": "performance",
                "metrics": performance_report,
                "timestamp": time.time()
            })
        elif request_type == "ai_audit":
            # Générer un rapport d'audit IA
            ai_audit_report = self._audit_ai_decisions()
            
            self.event_bus.publish("audit_response", {
                "request_id": request_id,
                "type": "ai_audit",
                "report": ai_audit_report,
                "timestamp": time.time()
            })
        elif request_type == "alerts":
            # Récupérer les alertes récentes
            hours = data.get("hours", 24)
            alerts = self._get_recent_alerts(hours)
            
            self.event_bus.publish("audit_response", {
                "request_id": request_id,
                "type": "alerts",
                "alerts": alerts,
                "timestamp": time.time()
            })
        elif request_type == "anomalies":
            # Récupérer les anomalies récentes
            hours = data.get("hours", 24)
            anomalies = self._get_recent_anomalies(hours)
            
            self.event_bus.publish("audit_response", {
                "request_id": request_id,
                "type": "anomalies",
                "anomalies": anomalies,
                "timestamp": time.time()
            })
        else:
            # Type de rapport inconnu
            self.event_bus.publish("audit_response", {
                "request_id": request_id,
                "type": request_type,
                "status": "error",
                "error": "Type de rapport inconnu",
                "timestamp": time.time()
            })

if __name__ == "__main__":
    # Test simple de l'auditeur
    kairos = KairosShadowMode()
    kairos.start()
    
    # Simuler quelques événements
    kairos._handle_any_event({
        "symbol": "BTC/USDT",
        "price": 48000,
        "volume": 1500,
        "timestamp": time.time()
    })
    
    kairos._handle_module_performance({
        "module": "FlowQuantumOptimizer",
        "latency_ms": 120,
        "error_rate": 0.02,
        "cpu_percent": 35,
        "memory_percent": 45,
        "timestamp": time.time()
    })
    
    time.sleep(2)  # Attente pour traitement
    kairos.stop()
