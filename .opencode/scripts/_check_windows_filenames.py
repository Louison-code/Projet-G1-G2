#!/usr/bin/env python3
"""
Vérifie et corrige les noms de fichiers incompatibles Windows dans le repo git.

Problèmes détectés :
  • Caractères interdits : \ / : * ? " < > |
  • Espace ou point en fin de nom (avant extension)
  • Noms réservés : CON, PRN, AUX, NUL, COM1..COM9, LPT1..LPT9
"""

import os
import re
import subprocess
import sys
from pathlib import Path

RESERVED = {"CON", "PRN", "AUX", "NUL", "NUL."} | {
    f"COM{i}" for i in range(1, 10)
} | {f"LPT{i}" for i in range(1, 10)}

def normalize_name(name: str) -> str:
    if "." in name:
        stem, ext = name.rsplit(".", 1)
        stem = stem.rstrip(" .")
        if not stem:
            stem = "_"
        result = stem + "." + ext
    else:
        result = name.rstrip(" .")
        if not result:
            result = "_"
    # Caractères interdits Windows
    result = re.sub(r'[\:\*\?"<>\|]', "_", result)
    result = re.sub(r"\\", "_", result)
    result = re.sub(r"/", "_", result)
    # Noms réservés (insensibles à la casse)
    stem = result.split(".")[0]
    if stem.upper() in RESERVED:
        stem = "_" + stem
        if "." in result:
            result = stem + "." + result.split(".", 1)[1]
        else:
            result = stem
    return result

def main():
    # Récupère tous les fichiers trackés
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("❌ Erreur git ls-files")
        sys.exit(1)

    files = result.stdout.strip("\0").split("\0") if result.stdout else []
    fixes = []

    for old_path in files:
        parts = old_path.split("/")
        new_parts = []
        changed = False
        for part in parts:
            new = normalize_name(part)
            new_parts.append(new)
            if new != part:
                changed = True

        if changed:
            new_path = "/".join(new_parts)
            fixes.append((old_path, new_path))

    if not fixes:
        print("✅ Aucun fichier incompatible Windows détecté.")
        return

    print(f"🔧 {len(fixes)} fichier(s) incompatible(s) Windows détecté(s) :\n")
    for old, new in fixes:
        subprocess.run(["git", "mv", old, new])
        print(f"  {old}")
        print(f"    → {new}\n")

    print("📦 Crée un commit séparé avec ces renommages.")

if __name__ == "__main__":
    main()
