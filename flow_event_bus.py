#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowEventBus.py - Module de communication entre les modules IA du cockpit FlowGlobalDynamics™
"""

import time
import queue
import threading
import logging
from typing import Dict, Any, Callable, List

class FlowEventBus:
    """
    Classe principale du bus d'événements pour la communication entre les modules IA
    """
    
    def __init__(self):
        """Initialisation du FlowEventBus"""
        self.event_queue = queue.Queue()
        self.subscribers = {}
        self.running = False
        self.thread = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Configuration du logger"""
        logger = logging.getLogger("FlowEventBus")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def start(self):
        """Démarrage du bus d'événements"""
        if self.running:
            self.logger.warning("FlowEventBus est déjà en cours d'exécution")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._process_events, daemon=True)
        self.thread.start()
        self.logger.info("FlowEventBus démarré")
        
    def stop(self):
        """Arrêt du bus d'événements"""
        if not self.running:
            self.logger.warning("FlowEventBus n'est pas en cours d'exécution")
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        self.logger.info("FlowEventBus arrêté")
        
    def _process_events(self):
        """Traitement des événements dans la file d'attente"""
        while self.running:
            try:
                event_type, event_data = self.event_queue.get(timeout=0.1)
                self._dispatch_event(event_type, event_data)
                self.event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement d'un événement: {str(e)}")
    
    def publish(self, event_type: str, event_data: Dict[str, Any] = None):
        """
        Publication d'un événement dans le bus
        
        Args:
            event_type: Type d'événement
            event_data: Données associées à l'événement
        """
        if event_data is None:
            event_data = {}
            
        try:
            self.event_queue.put((event_type, event_data))
            self.logger.debug(f"Événement publié: {event_type}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la publication d'un événement: {str(e)}")
    
    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Abonnement à un type d'événement
        
        Args:
            event_type: Type d'événement à écouter
            callback: Fonction à appeler lors de la réception d'un événement
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
            
        self.subscribers[event_type].append(callback)
        self.logger.debug(f"Nouvel abonnement pour l'événement: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Désabonnement d'un type d'événement
        
        Args:
            event_type: Type d'événement
            callback: Fonction à désabonner
        """
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            self.logger.debug(f"Désabonnement pour l'événement: {event_type}")
    
    def _dispatch_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        Dispatch d'un événement aux abonnés
        
        Args:
            event_type: Type d'événement
            event_data: Données de l'événement
        """
        if event_type not in self.subscribers:
            return
            
        for callback in self.subscribers[event_type]:
            try:
                callback(event_data)
            except Exception as e:
                self.logger.error(f"Erreur dans le callback d'un événement: {str(e)}")

# Instance globale du bus d'événements
event_bus = FlowEventBus()

# Fonction d'accès à l'instance globale
def get_event_bus():
    """Récupère l'instance globale du FlowEventBus"""
    return event_bus

if __name__ == "__main__":
    # Test simple du bus d'événements
    bus = FlowEventBus()
    bus.start()
    
    def test_handler(data):
        print(f"Événement reçu: {data}")
    
    bus.subscribe("test_event", test_handler)
    bus.publish("test_event", {"message": "Test du bus d'événements"})
    
    time.sleep(1)  # Attente pour le traitement de l'événement
    bus.stop()
