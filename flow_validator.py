#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
flow_validator.py - Module de validation des composants pour FlowGlobalDynamics™
"""

import logging
import importlib
import os
import sys
from typing import Dict, List, Tuple, Any

# Configuration du logger
logger = logging.getLogger("FlowValidator")

# Liste des modules critiques
CRITICAL_MODULES = [
    "flow_eventbus",
    "flow_integrity_verifier",
    "flow_quantum_optimizer",
    "flow_risk_shield",
    "flow_vision_market",
    "flow_self_optimizer",
    "flow_bytebeat",
    "flow_obfuscator",
    "flow_vault",
    "kairos_shadowmode"
]

def validate_all_modules() -> Dict[str, bool]:
    """
    Valide l'intégrité et la disponibilité de tous les modules critiques
    
    Returns:
        Dictionnaire des résultats de validation par module
    """
    logger.info("Validation des modules FlowGlobalDynamics™...")
    
    results = {}
    
    # Vérifier chaque module critique
    for module_name in CRITICAL_MODULES:
        results[module_name] = validate_module(module_name)
    
    # Vérifier les routers
    router_results = validate_routers()
    results.update(router_results)
    
    # Compter les modules valides et invalides
    valid_count = sum(1 for result in results.values() if result)
    invalid_count = sum(1 for result in results.values() if not result)
    
    if invalid_count > 0:
        logger.warning(f"Validation terminée : {valid_count} modules valides, {invalid_count} modules invalides")
    else:
        logger.info(f"Validation réussie : {valid_count} modules valides")
    
    return results

def validate_module(module_name: str) -> bool:
    """
    Valide un module spécifique
    
    Args:
        module_name: Nom du module à valider
        
    Returns:
        True si le module est valide, False sinon
    """
    try:
        # Tenter d'importer le module
        module = importlib.import_module(module_name)
        
        # Vérifier la présence de classes ou fonctions clés
        if hasattr(module, module_name.split('_')[-1].capitalize()):
            logger.info(f"Module {module_name} validé avec succès")
            return True
        else:
            logger.warning(f"Module {module_name} importé mais semble incomplet")
            return False
            
    except ImportError as e:
        logger.error(f"Erreur d'importation du module {module_name}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de la validation du module {module_name}: {str(e)}")
        return False

def validate_routers() -> Dict[str, bool]:
    """
    Valide les modules de routage
    
    Returns:
        Dictionnaire des résultats de validation par router
    """
    router_results = {}
    
    # Liste des routers à valider
    routers = [
        "flowbytebeat_router",
        "flowsniper_router",
        "flowupspin_router"
    ]
    
    # Ajouter le dossier des routers au path si nécessaire
    if "routers" not in sys.path:
        sys.path.append("routers")
    
    # Vérifier chaque router
    for router_name in routers:
        try:
            # Tenter d'importer le router
            full_module_name = f"routers.{router_name}"
            router = importlib.import_module(full_module_name)
            
            # Vérifier si le router a un attribut "router"
            if hasattr(router, "router"):
                logger.info(f"Router {router_name} validé avec succès")
                router_results[router_name] = True
            else:
                logger.warning(f"Router {router_name} importé mais semble incomplet (attribut router manquant)")
                router_results[router_name] = False
                
        except ImportError as e:
            logger.error(f"Erreur d'importation du router {router_name}: {str(e)}")
            router_results[router_name] = False
        except Exception as e:
            logger.error(f"Erreur lors de la validation du router {router_name}: {str(e)}")
            router_results[router_name] = False
    
    return router_results

if __name__ == "__main__":
    # Configuration du logger pour les tests directs
    logging.basicConfig(level=logging.INFO)
    
    # Valider tous les modules
    results = validate_all_modules()
    
    # Afficher les résultats
    print("Résultats de validation :")
    for module, valid in results.items():
        status = "✅ VALIDE" if valid else "❌ INVALIDE"
        print(f"{module}: {status}")
