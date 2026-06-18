"""
run.py — Point d'entrée du dashboard
=====================================
Lancement :
    cd Dashboard_cgu_corrige
    python run.py

Puis ouvrir dans le navigateur : http://127.0.0.1:8050

Assistant IA :
    Pour activer l'assistant, definissez votre cle Hugging Face soit en
    variable d'environnement (export HF_TOKEN="hf_..."), soit en copiant
    le fichier .env.example en .env et en y mettant votre cle.
"""

import sys
import os

# Ajouter le dossier courant au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

# Enregistrement des callbacks de TOUTES les pages (import necessaire)
import pages.accueil      # noqa: F401
import pages.parametres   # noqa: F401
import pages.dashboard    # noqa: F401
import pages.resultats    # noqa: F401
import pages.simulation   # noqa: F401

if __name__ == '__main__':
    cle_ok = bool(os.environ.get('HF_TOKEN')) or os.path.exists(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
    print("=" * 55)
    print("  Dashboard CGU Social — Sénégal")
    print("  Ouvrir : http://127.0.0.1:8050")
    print("  Assistant IA :", "actif (cle detectee)" if cle_ok
          else "inactif (definir HF_TOKEN ou creer .env)")
    print("=" * 55)
    app.run(debug=False, host='127.0.0.1', port=8050)
