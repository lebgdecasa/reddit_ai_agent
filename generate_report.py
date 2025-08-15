#!/usr/bin/env python3
"""
Script de génération de rapports pour le Mode Passive Conversational
"""

import sys
import os
from pathlib import Path

# Ajouter le dossier src au path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Changer le répertoire de travail vers le dossier du projet
os.chdir(current_dir)

from report_generator import main

if __name__ == "__main__":
    sys.exit(main())

