# Fix Windows-incompatible filenames before git push

Avant chaque `git push`, vérifie et corrige automatiquement tous les fichiers suivis par git dont le nom pose problème sur Windows.

## Problèmes détectés et corrigés

| Problème | Exemple | Corrigé en |
|----------|---------|------------|
| Deux-points `:` | `2026:06:04.docx` | `2026-06-04.docx` |
| Espace en fin de nom | `fichier .txt` | `fichier.txt` |
| Point en fin de nom | `fichier.txt.` | `fichier.txt` |
| Caractères `\ / : * ? " < > \|` | `data?final.xlsx` | `data_final.xlsx` |
| Espaces dans le chemin | `CR reunions/` | Conserver (Windows gère) |
| Accents `é è ê à ù` | `Compte-rendu.docx` | Conserver (NTFS OK) |

## Script de détection

```python
import os
import re
import subprocess
import sys

def check_and_fix():
    # Récupère la liste des fichiers trackés
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        capture_output=True, text=True
    )
    files = result.stdout.strip("\0").split("\0") if result.stdout else []
    
    fixes = []
    for path in files:
        old_path = path
        new_path = path
        
        # 1. Caractères interdits : \ / : * ? " < > |
        new_path = re.sub(r'[\:\*\?\"<>\|]', '_', new_path)
        
        # 2. Espaces en fin de nom (avant l'extension)
        parts = new_path.rsplit('/', 1)
        filename = parts[-1]
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            name = name.rstrip(' .')
            if not name:
                name = '_'
            parts[-1] = name + '.' + ext
        else:
            filename = filename.rstrip(' .')
            if not filename:
                filename = '_'
            parts[-1] = filename
        new_path = '/'.join(parts)
        
        if old_path != new_path:
            fixes.append((old_path, new_path))
    
    if not fixes:
        return
    
    print(f"🔧 Correction de {len(fixes)} fichier(s) incompatible(s) Windows...")
    for old, new in fixes:
        subprocess.run(["git", "mv", old, new])
        print(f"  {old} → {new}")
```

## Procédure avant chaque push

1. **Avant `git add`** : vérifier les nouveaux fichiers ajoutés
2. **Avant `git push`** : exécuter le script de détection
3. Si des fichiers sont renommés → commit séparé avec message :
   `"Renomme fichiers incompatibles Windows"`
4. Puis push normal

## Sauf si l'utilisateur dit explicitement "ne corrige pas les noms"
