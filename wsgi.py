"""
wsgi.py — Point d'entrée de PRODUCTION (deploiement)
=====================================================
Utilise par le serveur de production (gunicorn). Il importe l'application
ET tous les modules de pages, afin que l'ensemble des callbacks soient bien
enregistres (boutons, assistant, navigation), puis expose la variable `server`.

Commande de lancement en production :
    gunicorn wsgi:server

L'assistant IA necessite la variable d'environnement HF_TOKEN, a definir
dans les parametres de la plateforme d'hebergement (jamais dans le code).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, server  # noqa: F401  (server est utilise par gunicorn)

# Enregistrement des callbacks de TOUTES les pages
import pages.accueil      # noqa: F401
import pages.parametres   # noqa: F401
import pages.dashboard    # noqa: F401
import pages.resultats    # noqa: F401
import pages.simulation   # noqa: F401
