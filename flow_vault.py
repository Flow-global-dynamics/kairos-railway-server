#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowVault.py - Module de stockage sécurisé (clés, data cockpit) pour FlowGlobalDynamics™
"""

import logging
import time
import threading
import json
import os
import base64
import hashlib
import getpass
import uuid
from typing import Dict, Any, List, Optional, Union, Callable

# Import pour le chiffrement (dans un environnement réel)
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

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

class FlowVault:
    """
    Module de stockage sécurisé pour les données sensibles
    """
    
    def __init__(self):
        """Initialisation du FlowVault"""
        self.running = False
        self.threads = {}
        self.logger = self._setup_logger()
        self.event_bus = get_event_bus()
        self.config = self._load_configuration()
        self.vault = {}
        self.cached_data = {}
        self.encryption_key = None
        self.is_unlocked = False
        self.last_save = 0
        self.last_auto_lock = 0
        self.access_log = []
        
    def _setup_logger(self):
        """Configuration du logger"""
        logger = logging.getLogger("FlowVault")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Charge la configuration du coffre-fort
        
        Returns:
            Configuration du coffre-fort
        """
        # Configuration par défaut
        default_config = {
            "vault_file": "flow_vault.dat",
            "security": {
                "auto_lock_minutes": 30,
                "max_failed_attempts": 5,
                "pbkdf2_iterations": 100000,
                "encryption_algorithm": "Fernet"  # AES-128 en mode CBC avec HMAC-SHA256
            },
            "categories": {
                "api_keys": {
                    "description": "Clés API pour les échanges",
                    "sensitive": True,
                    "cache_enabled": False
                },
                "trading_parameters": {
                    "description": "Paramètres de trading",
                    "sensitive": False,
                    "cache_enabled": True
                },
                "user_preferences": {
                    "description": "Préférences utilisateur",
                    "sensitive": False,
                    "cache_enabled": True
                },
                "system_state": {
                    "description": "État du système",
                    "sensitive": False,
                    "cache_enabled": True
                }
            },
            "backup": {
                "enabled": True,
                "interval_hours": 24,
                "max_backups": 5,
                "backup_dir": "./backups"
            }
        }
        
        try:
            # Tenter de charger depuis un fichier (désactivé pour l'exemple)
            # with open("vault_config.json", "r") as f:
            #     return json.load(f)
            return default_config
        except Exception as e:
            self.logger.warning(f"Impossible de charger la configuration: {str(e)}. Utilisation des valeurs par défaut.")
            return default_config
    
    def start(self):
        """Démarrage du coffre-fort"""
        if self.running:
            self.logger.warning("FlowVault est déjà en cours d'exécution")
            return
            
        self.running = True
        
        # Vérifier si le coffre-fort existe déjà
        if not os.path.exists(self.config["vault_file"]):
            self.logger.info("Aucun coffre-fort trouvé. Un nouveau coffre-fort sera créé.")
        else:
            self.logger.info("Coffre-fort existant détecté.")
        
        # Démarrage des threads de gestion
        self._start_vault_threads()
        
        self._register_events()
        self.logger.info("FlowVault démarré")
        
    def stop(self):
        """Arrêt du coffre-fort"""
        if not self.running:
            self.logger.warning("FlowVault n'est pas en cours d'exécution")
            return
            
        self.running = False
        
        # Verrouiller le coffre-fort
        self.lock_vault()
        
        # Sauvegarder le coffre-fort si nécessaire
        if self.last_save < time.time() - 60:  # Si la dernière sauvegarde date de plus d'une minute
            self._save_vault()
        
        # Arrêt des threads de gestion
        for thread_name, thread in self.threads.items():
            if thread and thread.is_alive():
                thread.join(timeout=2.0)
                self.logger.debug(f"Thread {thread_name} arrêté")
        
        self._unregister_events()
        self.logger.info("FlowVault arrêté")
    
    def _start_vault_threads(self):
        """Démarre les threads de gestion du coffre-fort"""
        # Thread de gestion automatique
        self.threads["auto_manager"] = threading.Thread(
            target=self._auto_manager_loop, 
            daemon=True
        )
        self.threads["auto_manager"].start()
        
        # Thread de sauvegarde périodique
        self.threads["periodic_backup"] = threading.Thread(
            target=self._periodic_backup_loop, 
            daemon=True
        )
        self.threads["periodic_backup"].start()
    
    def _register_events(self):
        """Enregistrement des abonnements aux événements"""
        self.event_bus.subscribe("vault_store", self._handle_vault_store)
        self.event_bus.subscribe("vault_retrieve", self._handle_vault_retrieve)
        self.event_bus.subscribe("vault_delete", self._handle_vault_delete)
        self.event_bus.subscribe("vault_unlock", self._handle_vault_unlock)
        self.event_bus.subscribe("vault_lock", self._handle_vault_lock)
    
    def _unregister_events(self):
        """Désenregistrement des abonnements aux événements"""
        self.event_bus.unsubscribe("vault_store", self._handle_vault_store)
        self.event_bus.unsubscribe("vault_retrieve", self._handle_vault_retrieve)
        self.event_bus.unsubscribe("vault_delete", self._handle_vault_delete)
        self.event_bus.unsubscribe("vault_unlock", self._handle_vault_unlock)
        self.event_bus.unsubscribe("vault_lock", self._handle_vault_lock)
    
    def _auto_manager_loop(self):
        """Boucle de gestion automatique du coffre-fort"""
        while self.running:
            try:
                # Vérifier si le verrouillage automatique est nécessaire
                current_time = time.time()
                auto_lock_minutes = self.config["security"]["auto_lock_minutes"]
                
                if self.is_unlocked and auto_lock_minutes > 0:
                    if current_time - self.last_auto_lock > auto_lock_minutes * 60:
                        self.logger.info("Verrouillage automatique du coffre-fort")
                        self.lock_vault()
                        self.last_auto_lock = current_time
                
                # Vérifier si une sauvegarde est nécessaire
                if self.is_unlocked and current_time - self.last_save > 300:  # 5 minutes
                    self._save_vault()
                
                time.sleep(30)  # Vérification toutes les 30 secondes
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de gestion automatique: {str(e)}")
                time.sleep(60)
    
    def _periodic_backup_loop(self):
        """Boucle de sauvegarde périodique du coffre-fort"""
        while self.running:
            try:
                if self.config["backup"]["enabled"] and self.is_unlocked:
                    # Vérifier si une sauvegarde est nécessaire
                    backup_interval_seconds = self.config["backup"]["interval_hours"] * 3600
                    
                    # Vérifier si une sauvegarde a déjà été effectuée récemment
                    backup_dir = self.config["backup"]["backup_dir"]
                    if os.path.exists(backup_dir):
                        backup_files = [f for f in os.listdir(backup_dir) if f.startswith("flow_vault_backup_")]
                        if backup_files:
                            # Trier par date de modification
                            backup_files.sort(key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)), reverse=True)
                            last_backup_time = os.path.getmtime(os.path.join(backup_dir, backup_files[0]))
                            
                            if time.time() - last_backup_time > backup_interval_seconds:
                                self._create_backup()
                        else:
                            # Aucune sauvegarde trouvée, en créer une
                            self._create_backup()
                    else:
                        # Créer le répertoire de sauvegarde
                        os.makedirs(backup_dir, exist_ok=True)
                        self._create_backup()
                
                # Attendre jusqu'à la prochaine vérification
                sleep_time = 3600  # 1 heure
                time.sleep(sleep_time)
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle de sauvegarde périodique: {str(e)}")
                time.sleep(3600)
    
    def unlock_vault(self, password: str) -> bool:
        """
        Déverrouille le coffre-fort
        
        Args:
            password: Mot de passe pour déverrouiller le coffre-fort
            
        Returns:
            True si le déverrouillage a réussi, False sinon
        """
        if self.is_unlocked:
            self.logger.warning("Le coffre-fort est déjà déverrouillé")
            return True
            
        try:
            # Vérifier si le coffre-fort existe
            if not os.path.exists(self.config["vault_file"]):
                # Premier déverrouillage, initialiser le coffre-fort
                self.encryption_key = self._derive_key(password)
                self.is_unlocked = True
                self.last_auto_lock = time.time()
                
                # Initialiser un coffre-fort vide
                self._init_empty_vault()
                
                # Sauvegarder le coffre-fort
                self._save_vault()
                
                self.logger.info("Nouveau coffre-fort créé et déverrouillé")
                return True
            
            # Déverrouiller un coffre-fort existant
            self.encryption_key = self._derive_key(password)
            
            # Essayer de charger le coffre-fort
            try:
                self._load_vault()
                self.is_unlocked = True
                self.last_auto_lock = time.time()
                self.logger.info("Coffre-fort déverrouillé avec succès")
                return True
            except Exception as e:
                self.logger.error(f"Erreur lors du déverrouillage du coffre-fort: {str(e)}")
                self.encryption_key = None
                return False
            
        except Exception as e:
            self.logger.error(f"Erreur lors du déverrouillage du coffre-fort: {str(e)}")
            return False
    
    def lock_vault(self):
        """Verrouille le coffre-fort"""
        if not self.is_unlocked:
            self.logger.warning("Le coffre-fort est déjà verrouillé")
            return
            
        # Sauvegarder le coffre-fort avant de le verrouiller
        if self.last_save < time.time() - 60:  # Si la dernière sauvegarde date de plus d'une minute
            self._save_vault()
        
        # Effacer les données sensibles
        self.encryption_key = None
        self.cached_data = {}
        self.is_unlocked = False
        
        # Effacer partiellement le coffre-fort en mémoire
        # Ne supprimez pas complètement pour éviter de recharger les métadonnées
        # mais supprimez les valeurs sensibles
        for category in self.vault:
            for key in self.vault[category]:
                if isinstance(self.vault[category][key], dict) and "value" in self.vault[category][key]:
                    self.vault[category][key]["value"] = None
        
        self.logger.info("Coffre-fort verrouillé")
    
    def store(self, category: str, key: str, value: Any, metadata: Dict[str, Any] = None) -> bool:
        """
        Stocke une valeur dans le coffre-fort
        
        Args:
            category: Catégorie de données
            key: Clé de la donnée
            value: Valeur à stocker
            metadata: Métadonnées additionnelles
            
        Returns:
            True si le stockage a réussi, False sinon
        """
        if not self.is_unlocked:
            self.logger.error("Impossible de stocker des données - Le coffre-fort est verrouillé")
            return False
            
        # Vérifier si la catégorie existe
        if category not in self.config["categories"]:
            self.logger.warning(f"La catégorie '{category}' n'existe pas. Création d'une nouvelle catégorie.")
            self.config["categories"][category] = {
                "description": "Catégorie créée automatiquement",
                "sensitive": True,
                "cache_enabled": False
            }
        
        # Vérifier si la catégorie existe dans le coffre-fort
        if category not in self.vault:
            self.vault[category] = {}
        
        # Préparer les métadonnées
        if metadata is None:
            metadata = {}
            
        metadata["last_modified"] = time.time()
        metadata["version"] = metadata.get("version", 0) + 1
        
        # Déterminer si la donnée est sensible
        is_sensitive = self.config["categories"][category].get("sensitive", True)
        
        # Créer l'entrée
        self.vault[category][key] = {
            "value": value,
            "metadata": metadata,
            "sensitive": is_sensitive,
            "last_access": time.time()
        }
        
        # Ajouter au cache si le cache est activé pour cette catégorie
        if self.config["categories"][category].get("cache_enabled", False):
            if category not in self.cached_data:
                self.cached_data[category] = {}
            self.cached_data[category][key] = value
        
        # Journal d'accès
        self._log_access("store", category, key)
        
        # Planifier une sauvegarde
        self._schedule_save()
        
        return True
    
    def retrieve(self, category: str, key: str) -> Optional[Any]:
        """
        Récupère une valeur depuis le coffre-fort
        
        Args:
            category: Catégorie de données
            key: Clé de la donnée
            
        Returns:
            Valeur stockée ou None si non trouvée
        """
        # Vérifier dans le cache si disponible
        if (category in self.cached_data and 
            key in self.cached_data[category] and 
            self.config["categories"].get(category, {}).get("cache_enabled", False)):
            
            # Journal d'accès
            self._log_access("retrieve_cached", category, key)
            
            return self.cached_data[category][key]
        
        # Sinon, le coffre-fort doit être déverrouillé
        if not self.is_unlocked:
            self.logger.error("Impossible de récupérer des données - Le coffre-fort est verrouillé")
            return None
            
        # Vérifier si la catégorie et la clé existent
        if category not in self.vault or key not in self.vault[category]:
            self.logger.warning(f"Donnée non trouvée: {category}.{key}")
            return None
        
        # Récupérer la valeur
        data = self.vault[category][key]
        value = data.get("value")
        
        # Mettre à jour le timestamp d'accès
        data["last_access"] = time.time()
        
        # Journal d'accès
        self._log_access("retrieve", category, key)
        
        return value
    
    def delete(self, category: str, key: str) -> bool:
        """
        Supprime une valeur du coffre-fort
        
        Args:
            category: Catégorie de données
            key: Clé de la donnée
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        if not self.is_unlocked:
            self.logger.error("Impossible de supprimer des données - Le coffre-fort est verrouillé")
            return False
            
        # Vérifier si la catégorie et la clé existent
        if category not in self.vault or key not in self.vault[category]:
            self.logger.warning(f"Donnée non trouvée pour suppression: {category}.{key}")
            return False
        
        # Supprimer du coffre-fort
        del self.vault[category][key]
        
        # Supprimer du cache si présent
        if category in self.cached_data and key in self.cached_data[category]:
            del self.cached_data[category][key]
        
        # Journal d'accès
        self._log_access("delete", category, key)
        
        # Planifier une sauvegarde
        self._schedule_save()
        
        return True
    
    def list_keys(self, category: str) -> List[str]:
        """
        Liste les clés disponibles dans une catégorie
        
        Args:
            category: Catégorie de données
            
        Returns:
            Liste des clés
        """
        if not self.is_unlocked:
            self.logger.error("Impossible de lister les clés - Le coffre-fort est verrouillé")
            return []
            
        if category not in self.vault:
            return []
            
        return list(self.vault[category].keys())
    
    def get_metadata(self, category: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les métadonnées d'une entrée
        
        Args:
            category: Catégorie de données
            key: Clé de la donnée
            
        Returns:
            Métadonnées ou None si non trouvées
        """
        if not self.is_unlocked:
            self.logger.error("Impossible de récupérer les métadonnées - Le coffre-fort est verrouillé")
            return None
            
        if category not in self.vault or key not in self.vault[category]:
            return None
            
        return self.vault[category][key].get("metadata", {})
    
    def _derive_key(self, password: str) -> bytes:
        """
        Dérive une clé de chiffrement à partir du mot de passe
        
        Args:
            password: Mot de passe
            
        Returns:
            Clé de chiffrement
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            # Mode de compatibilité simple (moins sécurisé)
            return hashlib.sha256(password.encode()).digest()
        
        # Utiliser PBKDF2 pour dériver une clé
        salt = b'FlowGlobalDynamics'  # Dans un environnement réel, utiliser un sel aléatoire stocké
        iterations = self.config["security"]["pbkdf2_iterations"]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations
        )
        
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _init_empty_vault(self):
        """Initialise un coffre-fort vide"""
        self.vault = {}
        
        for category in self.config["categories"]:
            self.vault[category] = {}
        
        # Ajouter des informations système
        self.vault["system"] = {
            "vault_info": {
                "value": {
                    "created_at": time.time(),
                    "version": "1.0"
                },
                "metadata": {
                    "description": "Informations sur le coffre-fort"
                },
                "sensitive": False,
                "last_access": time.time()
            }
        }
    
    def _save_vault(self):
        """Sauvegarde le coffre-fort sur disque"""
        if not self.is_unlocked or not self.encryption_key:
            self.logger.error("Impossible de sauvegarder - Le coffre-fort est verrouillé")
            return
            
        try:
            # Préparer les données à sauvegarder
            vault_data = {}
            
            for category in self.vault:
                vault_data[category] = {}
                for key, data in self.vault[category].items():
                    # Copier l'entrée
                    entry = data.copy()
                    
                    # Si la valeur est None, ne pas la sauvegarder
                    if entry.get("value") is None:
                        continue
                    
                    vault_data[category][key] = entry
            
            # Sérialiser les données
            serialized_data = json.dumps(vault_data, default=self._json_serializer)
            
            # Chiffrer les données
            encrypted_data = self._encrypt_data(serialized_data)
            
            # Sauvegarder sur disque
            with open(self.config["vault_file"], 'wb') as f:
                f.write(encrypted_data)
            
            self.last_save = time.time()
            self.logger.debug("Coffre-fort sauvegardé avec succès")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde du coffre-fort: {str(e)}")
    
    def _load_vault(self):
        """Charge le coffre-fort depuis le disque"""
        if not self.encryption_key:
            self.logger.error("Impossible de charger - Clé de chiffrement manquante")
            return
            
        try:
            # Vérifier si le fichier existe
            if not os.path.exists(self.config["vault_file"]):
                self.logger.warning("Fichier de coffre-fort introuvable")
                self._init_empty_vault()
                return
            
            # Lire les données chiffrées
            with open(self.config["vault_file"], 'rb') as f:
                encrypted_data = f.read()
            
            # Déchiffrer les données
            serialized_data = self._decrypt_data(encrypted_data)
            
            # Désérialiser les données
            vault_data = json.loads(serialized_data)
            
            # Charger dans le coffre-fort
            self.vault = vault_data
            
            # Initialiser le cache
            self.cached_data = {}
            for category, items in self.vault.items():
                if self.config["categories"].get(category, {}).get("cache_enabled", False):
                    self.cached_data[category] = {}
                    for key, data in items.items():
                        if not data.get("sensitive", True):
                            self.cached_data[category][key] = data.get("value")
            
            self.logger.info(f"Coffre-fort chargé avec succès ({len(vault_data)} catégories)")
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du coffre-fort: {str(e)}")
            raise
    
    def _encrypt_data(self, data: str) -> bytes:
        """
        Chiffre des données
        
        Args:
            data: Données à chiffrer
            
        Returns:
            Données chiffrées
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            # Mode de compatibilité simple (moins sécurisé)
            key = self.encryption_key[:16]  # Utiliser les 16 premiers octets comme clé AES
            # Simuler un chiffrement (ceci n'est PAS sécurisé)
            return base64.b64encode(data.encode())
        
        # Utiliser Fernet (AES-128-CBC avec HMAC pour l'intégrité)
        f = Fernet(self.encryption_key)
        return f.encrypt(data.encode())
    
    def _decrypt_data(self, encrypted_data: bytes) -> str:
        """
        Déchiffre des données
        
        Args:
            encrypted_data: Données chiffrées
            
        Returns:
            Données déchiffrées
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            # Mode de compatibilité simple (moins sécurisé)
            # Simuler un déchiffrement (ceci n'est PAS sécurisé)
            return base64.b64decode(encrypted_data).decode()
        
        # Utiliser Fernet (AES-128-CBC avec HMAC pour l'intégrité)
        f = Fernet(self.encryption_key)
        return f.decrypt(encrypted_data).decode()
    
    def _json_serializer(self, obj):
        """Sérialise des objets personnalisés pour JSON"""
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        raise TypeError(f"Type non sérialisable: {type(obj)}")
    
    def _create_backup(self):
        """Crée une sauvegarde du coffre-fort"""
        if not self.is_unlocked or not os.path.exists(self.config["vault_file"]):
            return
            
        try:
            # Créer le répertoire de sauvegarde si nécessaire
            backup_dir = self.config["backup"]["backup_dir"]
            os.makedirs(backup_dir, exist_ok=True)
            
            # Générer un nom de fichier pour la sauvegarde
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"flow_vault_backup_{timestamp}.dat")
            
            # Copier le fichier du coffre-fort
            with open(self.config["vault_file"], 'rb') as src, open(backup_file, 'wb') as dst:
                dst.write(src.read())
            
            self.logger.info(f"Sauvegarde du coffre-fort créée: {backup_file}")
            
            # Nettoyer les anciennes sauvegardes
            self._cleanup_old_backups()
        except Exception as e:
            self.logger.error(f"Erreur lors de la création d'une sauvegarde: {str(e)}")
    
    def _cleanup_old_backups(self):
        """Nettoie les anciennes sauvegardes"""
        try:
            backup_dir = self.config["backup"]["backup_dir"]
            max_backups = self.config["backup"]["max_backups"]
            
            # Lister les fichiers de sauvegarde
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith("flow_vault_backup_")]
            
            # Si le nombre de sauvegardes dépasse le maximum
            if len(backup_files) > max_backups:
                # Trier par date de modification (plus ancienne en premier)
                backup_files.sort(key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)))
                
                # Supprimer les sauvegardes excédentaires
                for i in range(len(backup_files) - max_backups):
                    file_to_delete = os.path.join(backup_dir, backup_files[i])
                    os.remove(file_to_delete)
                    self.logger.debug(f"Ancienne sauvegarde supprimée: {file_to_delete}")
        except Exception as e:
            self.logger.error(f"Erreur lors du nettoyage des anciennes sauvegardes: {str(e)}")
    
    def _schedule_save(self):
        """Planifie une sauvegarde du coffre-fort"""
        # Si la dernière sauvegarde date de plus de 5 minutes, sauvegarder immédiatement
        if time.time() - self.last_save > 300:
            self._save_vault()
    
    def _log_access(self, action: str, category: str, key: str):
        """
        Enregistre un accès au coffre-fort
        
        Args:
            action: Type d'action (store, retrieve, delete)
            category: Catégorie de données
            key: Clé de la donnée
        """
        log_entry = {
            "action": action,
            "category": category,
            "key": key,
            "timestamp": time.time(),
            "access_id": str(uuid.uuid4())
        }
        
        # Ajouter à l'historique d'accès
        self.access_log.append(log_entry)
        
        # Limiter la taille du journal d'accès
        if len(self.access_log) > 1000:
            self.access_log = self.access_log[-1000:]
    
    def get_access_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère le journal d'accès
        
        Args:
            limit: Nombre maximum d'entrées à récupérer
            
        Returns:
            Journal d'accès
        """
        if not self.is_unlocked:
            self.logger.error("Impossible de récupérer le journal d'accès - Le coffre-fort est verrouillé")
            return []
            
        # Retourner les N dernières entrées
        return self.access_log[-limit:]
    
    def _handle_vault_store(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les demandes de stockage
        
        Args:
            data: Données de la demande
        """
        category = data.get("category")
        key = data.get("key")
        value = data.get("value")
        metadata = data.get("metadata")
        request_id = data.get("request_id", str(uuid.uuid4()))
        
        if not category or not key or value is None:
            self.event_bus.publish("vault_store_response", {
                "request_id": request_id,
                "success": False,
                "error": "Paramètres incomplets",
                "timestamp": time.time()
            })
            return
        
        # Stocker la valeur
        success = self.store(category, key, value, metadata)
        
        # Publier la réponse
        self.event_bus.publish("vault_store_response", {
            "request_id": request_id,
            "success": success,
            "category": category,
            "key": key,
            "timestamp": time.time()
        })
    
    def _handle_vault_retrieve(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les demandes de récupération
        
        Args:
            data: Données de la demande
        """
        category = data.get("category")
        key = data.get("key")
        request_id = data.get("request_id", str(uuid.uuid4()))
        
        if not category or not key:
            self.event_bus.publish("vault_retrieve_response", {
                "request_id": request_id,
                "success": False,
                "error": "Paramètres incomplets",
                "timestamp": time.time()
            })
            return
        
        # Récupérer la valeur
        value = self.retrieve(category, key)
        
        # Publier la réponse
        self.event_bus.publish("vault_retrieve_response", {
            "request_id": request_id,
            "success": value is not None,
            "category": category,
            "key": key,
            "value": value,
            "timestamp": time.time()
        })
    
    def _handle_vault_delete(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les demandes de suppression
        
        Args:
            data: Données de la demande
        """
        category = data.get("category")
        key = data.get("key")
        request_id = data.get("request_id", str(uuid.uuid4()))
        
        if not category or not key:
            self.event_bus.publish("vault_delete_response", {
                "request_id": request_id,
                "success": False,
                "error": "Paramètres incomplets",
                "timestamp": time.time()
            })
            return
        
        # Supprimer la valeur
        success = self.delete(category, key)
        
        # Publier la réponse
        self.event_bus.publish("vault_delete_response", {
            "request_id": request_id,
            "success": success,
            "category": category,
            "key": key,
            "timestamp": time.time()
        })
    
    def _handle_vault_unlock(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les demandes de déverrouillage
        
        Args:
            data: Données de la demande
        """
        password = data.get("password")
        request_id = data.get("request_id", str(uuid.uuid4()))
        
        if not password:
            self.event_bus.publish("vault_unlock_response", {
                "request_id": request_id,
                "success": False,
                "error": "Mot de passe manquant",
                "timestamp": time.time()
            })
            return
        
        # Déverrouiller le coffre-fort
        success = self.unlock_vault(password)
        
        # Publier la réponse
        self.event_bus.publish("vault_unlock_response", {
            "request_id": request_id,
            "success": success,
            "timestamp": time.time()
        })
    
    def _handle_vault_lock(self, data: Dict[str, Any]):
        """
        Gestionnaire pour les demandes de verrouillage
        
        Args:
            data: Données de la demande
        """
        request_id = data.get("request_id", str(uuid.uuid4()))
        
        # Verrouiller le coffre-fort
        self.lock_vault()
        
        # Publier la réponse
        self.event_bus.publish("vault_lock_response", {
            "request_id": request_id,
            "success": True,
            "timestamp": time.time()
        })

if __name__ == "__main__":
    # Test simple du coffre-fort
    vault = FlowVault()
    vault.start()
    
    # Déverrouiller le coffre-fort (avec un mot de passe par défaut)
    if vault.unlock_vault("test_password"):
        # Stocker des données
        vault.store("api_keys", "binance", {
            "api_key": "test_api_key",
            "api_secret": "test_api_secret"
        })
        
        # Récupérer des données
        api_keys = vault.retrieve("api_keys", "binance")
        print(f"API Keys: {api_keys}")
        
        # Verrouiller le coffre-fort
        vault.lock_vault()
    
    time.sleep(2)  # Attente pour traitement
    vault.stop()
