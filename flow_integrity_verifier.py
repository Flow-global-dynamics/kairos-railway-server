#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowIntegrityVerifier.py - Module de vérification d'intégrité des fichiers critiques pour FlowGlobalDynamics™
"""

import logging
import time
import threading
import hashlib
import os
import json
from typing import Dict, Any, List, Optional, Set, Tuple

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

class FlowIntegrityVerifier:
    """
    Module de vérification d'intégrité des fichiers critiques
    """
    
    def __init__(self):
        """Initialisation du FlowIntegrityVerifier"""
        self.running = False
        self.threads = {}
        self.logger = self._setup_logger()
        self.event_bus = get_event_bus()
        self.config = self._load_configuration()
        self.file_hashes = {}
        self.last_full_scan = 0
        self.last_quick_scan = 0
        self.integrity_status = {
            "status": "unknown",
            "last_check": 0,
            "issues": []
        }
        self.known_modules = self._get_known_modules()
        
    def _setup_logger(self):
        """Configuration du logger"""
        logger = logging.getLogger("FlowIntegrityVerifier")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Charge la configuration du vérificateur d'intégrité
        
        Returns:
            Configuration du vérificateur
        """
        # Configuration par défaut
        default_config = {
            "scan_intervals": {
                "quick_scan_seconds": 300,  # 5 minutes
                "full_scan_seconds": 3600   # 1 heure
            },
            "critical_files": [
                "flow_launcher.py",
                "flow_eventbus.py",
                "flow_quantumoptimizer.py",
                "flow_riskshield.py",
                "flow_visionmarket.py",
                "flow_selfoptimizer.py",
                "flow_bytebeat.py",
                "flow_obfuscator.py",
                "flow_integrityverifier.py",
                "flow_vault.py",
                "kairos_shadowmode.py"
            ],
            "monitored_directories": [
                "./",  # Répertoire courant
                "./modules",
                "./config"
            ],
            "file_extensions": [".py", ".json", ".yml", ".yaml"],
            "excluded_patterns": [
                "__pycache__",
                ".git",
                "*.pyc",
                "*.log",
                "temp_*"
            ],
            "actions": {
                "on_integrity_failure": "alert",  # alert, restore, shutdown
                "backup_enabled": True,
                "backup_directory": "./backups"
            },
            "verification": {
                "check_permissions": True,
                "check_timestamps": True,
                "hash_algorithm": "sha256"  # md5, sha1, sha256, sha512
            }
        }
        
        try:
            # Tenter de charger depuis un fichier (désactivé pour l'exemple)
            # with open("integrity_config.json", "r") as f:
            #     return json.load(f)
            return default_config
        except Exception as e:
            self.logger.warning(f"Impossible de charger la configuration: {str(e)}. Utilisation des valeurs par défaut.")
            return default_config
    
    def _get_known_modules(self) -> Dict[str, Dict[str, Any]]:
        """
        Récupère la liste des modules connus avec leurs informations
        
        Returns:
            Dictionnaire des modules connus
        """
        # Dans un système réel, charger depuis un fichier sécurisé
        return {
            "flow_launcher.py": {
                "description": "Démarrage global cockpit",
                "required": True,
                "dependencies": ["flow_eventbus.py"]
            },
            "flow_eventbus.py": {
                "description": "Communication entre modules IA",
                "required": True,
                "dependencies": []
            },
            "flow_quantumoptimizer.py": {
                "description": "Optimisation gains et stratégies",
                "required": True,
                "dependencies": ["flow_eventbus.py"]
            },
            "flow_riskshield.py": {
                "description": "Protection et réduction des risques",
                "required": True,
                "dependencies": ["flow_eventbus.py"]
            },
            "flow_visionmarket.py": {
                "description": "Surveillance intelligente du marché",
                "required": True,
                "dependencies": ["flow_eventbus.py"]
            },
            "flow_selfoptimizer.py": {
                "description": "Auto-ajustement cockpit / IA",
                "required": True,
                "dependencies": ["flow_eventbus.py"]
            },
            "flow_bytebeat.py": {
                "description": "Scalping rapide Bybit / Kraken",
                "required": True,
                "dependencies": ["flow_eventbus.py"]
            },
            "flow_obfuscator.py": {
                "description": "Protection contre l'espionnage IA/trading",
                "required": True,
                "dependencies": ["flow_eventbus.py"]
            },
            "flow_integrityverifier.py": {
                "description": "Vérification d'intégrité fichiers critiques",
                "required": True,
                "dependencies": ["flow_eventbus.py"]
            },
            "flow_vault.py": {
                "description": "Stockage sécurisé (clés, data cockpit)",
                "required": True,
                "dependencies": ["flow_eventbus.py"]
            },
            "kairos_shadowmode.py": {
                "description": "Audit passif IA, stabilité, alertes",
                "required": True,
                "dependencies": ["flow_eventbus.py"]
            }
        }
    
    def start(self):
        """Démarrage du vérificateur d'intégrité"""
        if self.running:
            self.logger.warning("FlowIntegrityVerifier est déjà en cours d'exécution")
            return
            
        self.running = True
        
        # Démarrage des threads de vérification
        self._start_verification_threads()
        
        self._register_events()
        self.logger.info("FlowIntegrityVerifier démarré")
        
        # Effectuer une vérification initiale
        self._perform_full_scan()
        
    def stop(self):
        """Arrêt du vérificateur d'intégrité"""
        if not self.running:
            self.logger.warning("FlowIntegrityVerifier n'est pas en cours d'exécution")
            return
            
        self.running = False
        
        # Arrêt des threads de vérification
        for thread_name, thread in self.threads.items():
            if thread and thread.is_alive():
                thread.join(timeout=2.0)
                self.logger.debug(f"Thread {thread_name} arrêté")
        
        self._unregister_events()
        self.logger.info("FlowIntegrityVerifier arrêté")
    
    def _start_verification_threads(self):
        """Démarre les threads de vérification"""
        # Thread de vérification périodique
        self.threads["periodic_scanner"] = threading.Thread(
            target=self._periodic_scanner_loop, 
            daemon=True
        )
        self.threads["periodic_scanner"].start()
        
        # Thread de surveillance des modifications en temps réel
        self.threads["realtime_monitor"] = threading.Thread(
            target=self._realtime_monitor_loop, 
            daemon=True
        )
        self.threads["realtime_monitor"].start()
    
    def _register_events(self):
        """Enregistrement des abonnements aux événements"""
        self.event_bus.subscribe("file_modified", self._handle_file_modified)
        self.event_bus.subscribe("integrity_check_request", self._handle_integrity_check_request)
        self.event_bus.subscribe("restore_file_request", self._handle_restore_file_request)
    
    def _unregister_events(self):
        """Désenregistrement des abonnements aux événements"""
        self.event_bus.unsubscribe("file_modified", self._handle_file_modified)
        self.event_bus.unsubscribe("integrity_check_request", self._handle_integrity_check_request)
        self.event_bus.unsubscribe("restore_file_request", self._handle_restore_file_request)
    
    def _periodic_scanner_loop(self):
        """Boucle de vérification périodique"""
        while self.running:
            try:
                current_time = time.time()
                
                # Vérifier si un scan rapide est nécessaire
                if current_time - self.last_quick_scan > self.config["scan_intervals"]["quick_scan_seconds"]:
                    self._perform_quick_scan()
                    self.last_quick_scan = current_time
                
                # Vérifier si un scan complet est nécessaire
                if current_time - self.last_full_scan > self.config["scan_intervals"]["full_scan_seconds"]:
                    self._perform_full_scan()
                    self.last_full_scan = current_time
                
                time.sleep(10)  # Vérification toutes les 10 secondes
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de vérification périodique: {str(e)}")
                time.sleep(30)
    
    def _realtime_monitor_loop(self):
        """Boucle de surveillance en temps réel"""
        # Dans un système réel, utiliser inotify (Linux) ou watchdog (multiplateforme)
        # Pour cet exemple, nous simulons une vérification périodique à haute fréquence
        
        last_check_files = {}
        
        while self.running:
            try:
                # Vérifier uniquement les fichiers critiques
                for file_path in self._get_critical_file_paths():
                    if os.path.exists(file_path):
                        mtime = os.path.getmtime(file_path)
                        
                        # Si le fichier a été modifié depuis la dernière vérification
                        if file_path in last_check_files and mtime > last_check_files[file_path]:
                            self._handle_file_modified({
                                "file_path": file_path,
                                "timestamp": time.time()
                            })
                        
                        last_check_files[file_path] = mtime
                
                time.sleep(1)  # Vérification à haute fréquence
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de surveillance en temps réel: {str(e)}")
                time.sleep(5)
    
    def _perform_quick_scan(self):
        """Effectue un scan rapide des fichiers critiques"""
        self.logger.debug("Exécution d'un scan rapide...")
        
        issues = []
        critical_files = self._get_critical_file_paths()
        
        for file_path in critical_files:
            try:
                # Vérifier si le fichier existe
                if not os.path.exists(file_path):
                    issues.append({
                        "file": file_path,
                        "issue": "missing",
                        "severity": "critical",
                        "timestamp": time.time()
                    })
                    continue
                
                # Vérifier l'intégrité du fichier
                if file_path in self.file_hashes:
                    current_hash = self._calculate_file_hash(file_path)
                    stored_hash = self.file_hashes.get(file_path)
                    
                    if current_hash != stored_hash:
                        issues.append({
                            "file": file_path,
                            "issue": "modified",
                            "severity": "critical",
                            "stored_hash": stored_hash,
                            "current_hash": current_hash,
                            "timestamp": time.time()
                        })
                
                # Vérifier les permissions si configuré
                if self.config["verification"]["check_permissions"]:
                    self._check_file_permissions(file_path, issues)
            except Exception as e:
                self.logger.error(f"Erreur lors de la vérification de {file_path}: {str(e)}")
                issues.append({
                    "file": file_path,
                    "issue": "error",
                    "severity": "high",
                    "error": str(e),
                    "timestamp": time.time()
                })
        
        # Mettre à jour le statut d'intégrité
        self._update_integrity_status(issues, scan_type="quick")
    
    def _perform_full_scan(self):
        """Effectue un scan complet de tous les fichiers surveillés"""
        self.logger.info("Exécution d'un scan complet...")
        
        issues = []
        
        # Récupérer tous les fichiers à surveiller
        monitored_files = self._get_all_monitored_files()
        
        # Vérifier chaque fichier
        for file_path in monitored_files:
            try:
                # Vérifier si le fichier est exclu
                if self._is_file_excluded(file_path):
                    continue
                
                # Vérifier si le fichier existe
                if not os.path.exists(file_path):
                    # Ajouter une issue uniquement si c'est un fichier critique ou si nous avons déjà un hash pour ce fichier
                    if file_path in self._get_critical_file_paths() or file_path in self.file_hashes:
                        issues.append({
                            "file": file_path,
                            "issue": "missing",
                            "severity": "critical" if file_path in self._get_critical_file_paths() else "high",
                            "timestamp": time.time()
                        })
                    continue
                
                # Calculer le hash du fichier
                current_hash = self._calculate_file_hash(file_path)
                
                # Si nous avons déjà un hash pour ce fichier, vérifier l'intégrité
                if file_path in self.file_hashes:
                    stored_hash = self.file_hashes.get(file_path)
                    
                    if current_hash != stored_hash:
                        issues.append({
                            "file": file_path,
                            "issue": "modified",
                            "severity": "critical" if file_path in self._get_critical_file_paths() else "medium",
                            "stored_hash": stored_hash,
                            "current_hash": current_hash,
                            "timestamp": time.time()
                        })
                
                # Stocker ou mettre à jour le hash du fichier
                self.file_hashes[file_path] = current_hash
                
                # Vérifier les permissions si configuré
                if self.config["verification"]["check_permissions"]:
                    self._check_file_permissions(file_path, issues)
                
                # Vérifier les timestamps si configuré
                if self.config["verification"]["check_timestamps"]:
                    self._check_file_timestamps(file_path, issues)
            except Exception as e:
                self.logger.error(f"Erreur lors de la vérification de {file_path}: {str(e)}")
                issues.append({
                    "file": file_path,
                    "issue": "error",
                    "severity": "high",
                    "error": str(e),
                    "timestamp": time.time()
                })
        
        # Vérifier les dépendances des modules
        self._check_module_dependencies(issues)
        
        # Mettre à jour le statut d'intégrité
        self._update_integrity_status(issues, scan_type="full")
        
        # Sauvegarder les hashes de référence
        self._save_reference_hashes()
    
    def _get_critical_file_paths(self) -> List[str]:
        """
        Récupère les chemins des fichiers critiques
        
        Returns:
            Liste des chemins de fichiers critiques
        """
        critical_files = []
        
        for file_name in self.config["critical_files"]:
            # Vérifier dans chaque répertoire surveillé
            for directory in self.config["monitored_directories"]:
                file_path = os.path.join(directory, file_name)
                if os.path.exists(file_path):
                    critical_files.append(file_path)
                    break  # Passer au fichier suivant une fois trouvé
        
        return critical_files
    
    def _get_all_monitored_files(self) -> List[str]:
        """
        Récupère tous les fichiers surveillés
        
        Returns:
            Liste de tous les fichiers surveillés
        """
        monitored_files = []
        
        # Parcourir tous les répertoires surveillés
        for directory in self.config["monitored_directories"]:
            if os.path.exists(directory) and os.path.isdir(directory):
                for root, dirs, files in os.walk(directory):
                    # Filtrer les répertoires exclus
                    dirs[:] = [d for d in dirs if not self._is_path_excluded(os.path.join(root, d))]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # Vérifier si le fichier a une extension surveillée
                        _, ext = os.path.splitext(file)
                        if ext in self.config["file_extensions"] and not self._is_file_excluded(file_path):
                            monitored_files.append(file_path)
        
        return monitored_files
    
    def _is_file_excluded(self, file_path: str) -> bool:
        """
        Vérifie si un fichier est exclu de la surveillance
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            True si le fichier est exclu, False sinon
        """
        # Vérifier si le chemin correspond à un motif exclu
        return self._is_path_excluded(file_path)
    
    def _is_path_excluded(self, path: str) -> bool:
        """
        Vérifie si un chemin est exclu de la surveillance
        
        Args:
            path: Chemin à vérifier
            
        Returns:
            True si le chemin est exclu, False sinon
        """
        for pattern in self.config["excluded_patterns"]:
            if pattern.startswith("*"):
                # Motif d'extension/suffixe
                if path.endswith(pattern[1:]):
                    return True
            elif pattern.endswith("*"):
                # Motif de préfixe/début
                if os.path.basename(path).startswith(pattern[:-1]):
                    return True
            else:
                # Motif exact ou sous-chaîne
                if pattern in path:
                    return True
        
        return False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calcule le hash d'un fichier
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Hash du fichier
        """
        if not os.path.exists(file_path):
            return ""
            
        algorithm = self.config["verification"]["hash_algorithm"].lower()
        
        hash_func = None
        if algorithm == "md5":
            hash_func = hashlib.md5()
        elif algorithm == "sha1":
            hash_func = hashlib.sha1()
        elif algorithm == "sha256":
            hash_func = hashlib.sha256()
        elif algorithm == "sha512":
            hash_func = hashlib.sha512()
        else:
            # Par défaut, utiliser SHA-256
            hash_func = hashlib.sha256()
        
        # Calculer le hash
        with open(file_path, 'rb') as f:
            # Lire par blocs pour économiser la mémoire
            for block in iter(lambda: f.read(4096), b''):
                hash_func.update(block)
        
        return hash_func.hexdigest()
    
    def _check_file_permissions(self, file_path: str, issues: List[Dict[str, Any]]):
        """
        Vérifie les permissions d'un fichier
        
        Args:
            file_path: Chemin du fichier
            issues: Liste des problèmes détectés
        """
        try:
            # Cette fonction dépend du système d'exploitation
            # Sous Unix, nous pourrions vérifier les permissions avec os.stat
            
            # Exemple simplifié pour tous les OS
            if not os.access(file_path, os.R_OK):
                issues.append({
                    "file": file_path,
                    "issue": "permissions",
                    "severity": "high",
                    "details": "Le fichier n'est pas lisible",
                    "timestamp": time.time()
                })
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des permissions de {file_path}: {str(e)}")
    
    def _check_file_timestamps(self, file_path: str, issues: List[Dict[str, Any]]):
        """
        Vérifie les timestamps d'un fichier
        
        Args:
            file_path: Chemin du fichier
            issues: Liste des problèmes détectés
        """
        try:
            # Vérifier si le fichier a été modifié dans le futur (potentielle manipulation)
            mtime = os.path.getmtime(file_path)
            current_time = time.time()
            
            if mtime > current_time + 60:  # 1 minute dans le futur (marge pour les horloges désynchronisées)
                issues.append({
                    "file": file_path,
                    "issue": "future_timestamp",
                    "severity": "high",
                    "details": f"Timestamp du fichier dans le futur: {time.ctime(mtime)}",
                    "timestamp": current_time
                })
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification des timestamps de {file_path}: {str(e)}")
    
    def _check_module_dependencies(self, issues: List[Dict[str, Any]]):
        """
        Vérifie les dépendances entre les modules
        
        Args:
            issues: Liste des problèmes détectés
        """
        # Vérifier si tous les modules requis sont présents
        for module_name, module_info in self.known_modules.items():
            if module_info.get("required", False):
                # Vérifier si le module est présent
                module_found = False
                for directory in self.config["monitored_directories"]:
                    if os.path.exists(os.path.join(directory, module_name)):
                        module_found = True
                        break
                
                if not module_found:
                    issues.append({
                        "file": module_name,
                        "issue": "missing_required_module",
                        "severity": "critical",
                        "details": f"Module requis manquant: {module_name} - {module_info.get('description', '')}",
                        "timestamp": time.time()
                    })
        
        # Vérifier les dépendances
        for module_name, module_info in self.known_modules.items():
            dependencies = module_info.get("dependencies", [])
            
            for dependency in dependencies:
                dependency_found = False
                for directory in self.config["monitored_directories"]:
                    if os.path.exists(os.path.join(directory, dependency)):
                        dependency_found = True
                        break
                
                if not dependency_found:
                    issues.append({
                        "file": module_name,
                        "issue": "missing_dependency",
                        "severity": "high",
                        "details": f"Dépendance manquante: {dependency} pour {module_name}",
                        "timestamp": time.time()
                    })
    
    def _update_integrity_status(self, issues: List[Dict[str, Any]], scan_type: str):
        """
        Met à jour le statut d'intégrité
        
        Args:
            issues: Liste des problèmes détectés
            scan_type: Type de scan (quick ou full)
        """
        # Filtrer les problèmes critiques et importants
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        high_issues = [i for i in issues if i.get("severity") == "high"]
        
        # Déterminer le statut global
        if critical_issues:
            status = "critical"
        elif high_issues:
            status = "warning"
        else:
            status = "ok"
        
        # Mettre à jour le statut
        self.integrity_status = {
            "status": status,
            "last_check": time.time(),
            "scan_type": scan_type,
            "issues": issues,
            "critical_count": len(critical_issues),
            "high_count": len(high_issues),
            "total_count": len(issues)
        }
        
        # Publier le statut d'intégrité
        self.event_bus.publish("integrity_status", {
            "status": status,
            "scan_type": scan_type,
            "critical_count": len(critical_issues),
            "high_count": len(high_issues),
            "total_count": len(issues),
            "timestamp": time.time()
        })
        
        # Logger le résultat
        if status == "critical":
            self.logger.critical(f"Problèmes d'intégrité critiques détectés ({len(critical_issues)}) - Action requise!")
        elif status == "warning":
            self.logger.warning(f"Avertissements d'intégrité détectés ({len(high_issues)}) - Vérification recommandée.")
        else:
            self.logger.info(f"Vérification d'intégrité réussie - Aucun problème critique détecté.")
        
        # Prendre des actions automatiques si configuré
        if status == "critical" and self.config["actions"]["on_integrity_failure"] != "alert":
            self._handle_integrity_failure(critical_issues)
    
    def _handle_integrity_failure(self, issues: List[Dict[str, Any]]):
        """
        Gère une défaillance d'intégrité
        
        Args:
            issues: Liste des problèmes critiques
        """
        action = self.config["actions"]["on_integrity_failure"]
        
        if action == "restore":
            # Restaurer les fichiers modifiés
            for issue in issues:
                if issue.get("issue") == "modified":
                    file_path = issue.get("file")
                    self._restore_file(file_path)
        elif action == "shutdown":
            # Arrêt d'urgence
            self.logger.critical("Arrêt d'urgence demandé suite à une défaillance d'intégrité critique!")
            
            # Publier un événement d'arrêt d'urgence
            self.event_bus.publish("emergency_shutdown", {
                "reason": "integrity_failure",
                "details": "Défaillance d'intégrité critique détectée",
                "issues": issues,
                "timestamp": time.time()
            })
    
    def _restore_file(self, file_path: str) -> bool:
        """
        Restaure un fichier à partir d'une sauvegarde
        
        Args:
            file_path: Chemin du fichier à restaurer
            
        Returns:
            True si la restauration a réussi, False sinon
        """
        if not self.config["actions"]["backup_enabled"]:
            self.logger.warning(f"Impossible de restaurer {file_path} - Les sauvegardes ne sont pas activées.")
            return False
            
        try:
            # Déterminer le chemin de la sauvegarde
            backup_dir = self.config["actions"]["backup_directory"]
            file_name = os.path.basename(file_path)
            backup_path = os.path.join(backup_dir, file_name + '.backup')
            
            if not os.path.exists(backup_path):
                self.logger.error(f"Aucune sauvegarde trouvée pour {file_path}")
                return False
                
            # Restaurer le fichier
            with open(backup_path, 'rb') as src, open(file_path, 'wb') as dst:
                dst.write(src.read())
                
            self.logger.info(f"Fichier restauré avec succès: {file_path}")
            
            # Mettre à jour le hash
            self.file_hashes[file_path] = self._calculate_file_hash(file_path)
            
            # Publier un événement de restauration
            self.event_bus.publish("file_restored", {
                "file": file_path,
                "timestamp": time.time()
            })
            
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la restauration de {file_path}: {str(e)}")
            return False
    
    def _save_reference_hashes(self):
        """Sauvegarde les hashes de référence"""
        try:
            # Dans un système réel, sauvegarder dans un fichier sécurisé
            # with open("reference_hashes.json", "w") as f:
            #     json.dump(self.file_hashes, f, indent=2)
            
            # Simuler une sauvegarde
            self.logger.debug(f"Hashes de référence sauvegardés pour {len(self.file_hashes)} fichiers")
            
            # Créer des sauvegardes si configuré
            if self.config["actions"]["backup_enabled"]:
                self._backup_critical_files()
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des hashes de référence: {str(e)}")
    
    def _backup_critical_files(self):
        """Crée des sauvegardes des fichiers critiques"""
        try:
            backup_dir = self.config["actions"]["backup_directory"]
            
            # Créer le répertoire de sauvegarde s'il n'existe pas
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Sauvegarder chaque fichier critique
            for file_path in self._get_critical_file_paths():
                if os.path.exists(file_path):
                    file_name = os.path.basename(file_path)
                    backup_path = os.path.join(backup_dir, file_name + '.backup')
                    
                    with open(file_path, 'rb') as src, open(backup_path, 'wb') as dst:
                        dst.write(src.read())
            
            self.logger.debug("Sauvegarde des fichiers critiques terminée")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des fichiers critiques: {str(e)}")
    
    def _handle_file_modified(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les modifications de fichiers
        
        Args:
            data: Données de la modification
        """
        file_path = data.get("file_path")
        
        if not file_path or not os.path.exists(file_path):
            return
            
        # Vérifier si le fichier est surveillé
        if self._is_file_excluded(file_path):
            return
            
        # Vérifier si le fichier est dans notre liste de hashes
        if file_path in self.file_hashes:
            current_hash = self._calculate_file_hash(file_path)
            stored_hash = self.file_hashes.get(file_path)
            
            if current_hash != stored_hash:
                self.logger.warning(f"Modification détectée pour {file_path}")
                
                # Déterminer si c'est un fichier critique
                is_critical = False
                for critical_file in self._get_critical_file_paths():
                    if os.path.samefile(file_path, critical_file):
                        is_critical = True
                        break
                
                # Créer un rapport de modification
                modification_report = {
                    "file": file_path,
                    "issue": "modified",
                    "severity": "critical" if is_critical else "medium",
                    "stored_hash": stored_hash,
                    "current_hash": current_hash,
                    "timestamp": time.time()
                }
                
                # Mettre à jour le statut d'intégrité
                current_issues = self.integrity_status.get("issues", [])
                current_issues.append(modification_report)
                
                # Mettre à jour le statut
                self._update_integrity_status(current_issues, scan_type="realtime")
                
                # Vérifier si des actions automatiques sont nécessaires
                if is_critical and self.config["actions"]["on_integrity_failure"] == "restore":
                    self._restore_file(file_path)
    
    def _handle_integrity_check_request(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les demandes de vérification d'intégrité
        
        Args:
            data: Données de la demande
        """
        check_type = data.get("type", "quick")
        file_path = data.get("file_path")
        
        if file_path:
            # Vérification d'un fichier spécifique
            self.logger.info(f"Vérification d'intégrité demandée pour {file_path}")
            
            if os.path.exists(file_path):
                issues = []
                
                # Vérifier le hash
                if file_path in self.file_hashes:
                    current_hash = self._calculate_file_hash(file_path)
                    stored_hash = self.file_hashes.get(file_path)
                    
                    if current_hash != stored_hash:
                        issues.append({
                            "file": file_path,
                            "issue": "modified",
                            "severity": "critical" if file_path in self._get_critical_file_paths() else "medium",
                            "stored_hash": stored_hash,
                            "current_hash": current_hash,
                            "timestamp": time.time()
                        })
                
                # Vérifier les permissions si configuré
                if self.config["verification"]["check_permissions"]:
                    self._check_file_permissions(file_path, issues)
                
                # Vérifier les timestamps si configuré
                if self.config["verification"]["check_timestamps"]:
                    self._check_file_timestamps(file_path, issues)
                
                # Publier le résultat
                self.event_bus.publish("integrity_check_result", {
                    "file": file_path,
                    "status": "modified" if issues else "ok",
                    "issues": issues,
                    "timestamp": time.time()
                })
            else:
                # Fichier introuvable
                self.event_bus.publish("integrity_check_result", {
                    "file": file_path,
                    "status": "missing",
                    "issues": [{
                        "file": file_path,
                        "issue": "missing",
                        "severity": "critical" if file_path in self._get_critical_file_paths() else "high",
                        "timestamp": time.time()
                    }],
                    "timestamp": time.time()
                })
        else:
            # Vérification complète
            self.logger.info(f"Vérification d'intégrité {check_type} demandée")
            
            if check_type == "full":
                self._perform_full_scan()
            else:
                self._perform_quick_scan()
    
    def _handle_restore_file_request(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les demandes de restauration de fichiers
        
        Args:
            data: Données de la demande
        """
        file_path = data.get("file_path")
        
        if not file_path:
            return
            
        self.logger.info(f"Restauration demandée pour {file_path}")
        
        # Tenter de restaurer le fichier
        success = self._restore_file(file_path)
        
        # Publier le résultat
        self.event_bus.publish("restore_file_result", {
            "file": file_path,
            "success": success,
            "timestamp": time.time()
        })
        
        # Si la restauration a réussi, mettre à jour le statut d'intégrité
        if success:
            # Effectuer un scan rapide pour mettre à jour le statut
            self._perform_quick_scan()

if __name__ == "__main__":
    # Test simple du vérificateur d'intégrité
    verifier = FlowIntegrityVerifier()
    verifier.start()
    
    # Simuler une demande de vérification d'intégrité
    verifier._handle_integrity_check_request({
        "type": "quick"
    })
    
    time.sleep(2)  # Attente pour traitement
    verifier.stop()
