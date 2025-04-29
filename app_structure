#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour créer la structure de l'application
Ce script crée les répertoires nécessaires pour l'application FlowGlobalApp
"""

import os
import sys

def create_app_structure():
    """Crée la structure de base de l'application"""
    
    # Répertoires à créer
    directories = [
        'utils',
        'routers',
        'logs'
    ]
    
    # Création des répertoires
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Répertoire '{directory}' créé")
        else:
            print(f"Répertoire '{directory}' existe déjà")
    
    # Création des fichiers __init__.py dans chaque répertoire
    for directory in directories:
        init_file = os.path.join(directory, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write('# Ce fichier est nécessaire pour que Python traite ce répertoire comme un package')
            print(f"Fichier '{init_file}' créé")
        else:
            print(f"Fichier '{init_file}' existe déjà")
    
    print("\nStructure de l'application créée avec succès!")
    print("Vous pouvez maintenant déployer l'application sur Railway")

if __name__ == "__main__":
    create_app_structure()
