# Guide des Outils — Projet G1-G2

Ce fichier explique les outils utilisés dans le projet, comment les installer, et ce que vous pouvez faire avec.
Voici une video qui explique le fonctionnement basique de Github : https://www.youtube.com/watch?v=bCOQl_CbER0

---

## 1. Warp — Le terminal moderne

### Qu'est-ce que Warp ?

Warp est un terminal nouvelle génération. Contrairement à un terminal classique (Terminal.app, iTerm2), Warp intègre des fonctionnalités modernes :

- **Éditeur intégré** : vous pouvez éditer une commande comme dans un bloc-notes (sélection, copier/coller, déplacement au clic)
- **Sélection par blocs** : sélectionnez une partie de la sortie d'une commande avec la souris
- **IA intégrée (Warp AI)** : posez des questions en langage naturel sur vos commandes
- **Workflows** : commandes pré-enregistrées pour les actions fréquentes
- **Division de l'écran** : plusieurs terminaux dans une même fenêtre

Dans warp vous pouvez soit ouvrir une fenêtre terminal classique, soit ouvrir une fenêtre avec l'agent IA de warp 
 
### Installation

1. Aller sur https://www.warp.dev/
2. Cliquer sur **Download for Mac** (ou windows)
3. Installer l'application et ouvrir Warp
4. Créer un compte Warp (gratuit)

### Commandes de base dans Warp

```bash
ls              # Lister les fichiers
cd dossier      # Changer de dossier
pwd             # Afficher le chemin actuel
clear           # Effacer le terminal
mkdir dossier   # Créer un dossier
```

### Agent Warp (Warp AI)

Warp dispose d'un assistant IA accessible avec `Ctrl+I` ou `Cmd+I`. Vous pouvez lui poser des questions comme :

- "Comment lister tous les fichiers Python ?"
- "Explique cette commande : git merge main"
- "Trouve les erreurs dans ce fichier"

Dans warp vous pouvez soit ouvrir une fenêtre terminal classique, soit ouvrir une fenêtre avec l'agent IA de warp, ATTENTIOn vous ne pouvez pas taper de 
Commandes dans une fenêtre agent warp, mais vous pouvez lui demander en langage naturel d'executer la commande à votre place

---

## 2. Git — Le gestionnaire de versions

### Qu'est-ce que Git ?

Git est un système qui permet de :

- **Sauvegarder l'historique** de chaque modification du code
- **Travailler à plusieurs** sur les mêmes fichiers sans écraser le travail des autres
- **Revenir en arrière** si une modification pose problème
- **Créer des branches** pour développer une fonctionnalité sans toucher au code principal

### Installation

Ouvir une fenestre warp "agent", lui demander de vous installer git, vous pouvez mettre en mode auto valid pour automatiser complètement l'installation

### Commandes Git essentielles

```bash
git clone <url>          # Télécharger le projet
git status               # Voir l'état des fichiers
git add <fichier>        # Préparer un fichier pour le commit
git commit -m "message"  # Sauvegarder les changements
git push                 # Envoyer sur GitHub
git pull                 # Récupérer les changements distants
git branch               # Lister les branches
git checkout -b <nom>    # Créer une nouvelle branche
```

---

## 3. GitHub — La plateforme collaborative

### Qu'est-ce que GitHub ?

GitHub est un service en ligne qui héberge des dépôts Git. C'est le "réseau social du code" où :

- **Notre projet** est stocké et accessible à toute l'équipe
- On peut **voir l'historique** des modifications
- On peut **commenter le code**, **signaler des bugs**, **proposer des améliorations**
- On peut **travailler en équipe** sans se marcher sur les pieds

### Créer un compte GitHub

1. Aller sur https://github.com
2. Cliquer sur **Sign up**
3. Entrer un nom d'utilisateur, une adresse email, un mot de passe
4. Vérifier l'email reçu
5. Optionnel : ajouter une photo de profil

### GitHub CLI (gh) — GitHub depuis le terminal

#### Qu'est-ce que GitHub CLI ?

C'est un outil en ligne de commande qui permet d'interagir avec GitHub sans quitter le terminal.
En general on ne modifie pas directement le code sur GitHub mais en local puis en l'exportant sur GitHub

#### Installation

Utiliser l'agent warp, demander lui de vous installer "GitHub CLI"


#### Configuration

Ensuite il faut vous connecter à votre compte GitHub:

Taper dans une fenêtre terminal (et non agent) "gh auth login"
```
Suivre les instructions : choisir "GitHub.com" → "HTTPS" → "Login with a web browser".

#### Commandes utiles

```bash
gh repo clone Louison-code/Projet-G1-G2    # Cloner le projet
gh repo view Louison-code/Projet-G1-G2      # Voir le dépôt
gh issue list                                # Voir les tâches
gh pr list                                   # Voir les pull requests
```

---




## 4. OpenCode — L'assistant IA dans le terminal

### Qu'est-ce qu'OpenCode ?

OpenCode est un outil en ligne de commande (CLI) qui intègre une IA directement dans votre terminal. (Comme Claude Code) Il permet de :

- **Discuter avec l'IA** pour coder plus vite
- **Modifier des fichiers** automatiquement
- **Expliquer du code** existant
- **Debugger** des erreurs
- **Écrire des tests**
- **Automatiser des tâches** répétitives

OpenCode est conçu pour fonctionner avec Warp (mais fonctionne aussi dans d'autres terminaux).

### Installation

Demander à l'agent Warp de vous installer Opencode


### Configuration


Creer un fichier "Opencode_workspace" dans votre ordinateur idéalement dans votre dossier utilisateur
En lançant opencode dans ce fichier et non dans tout votre ordinateur cela permet de ne lui donner accès que au dossier que vous avez mit dans ce workspace

Dans une fenêtre du terminal, tapez "cd opencode_workspcace" (on s'est placer dans le dossier) et ensuite tapez "opencode" (on lance opencode)

Pour l'instant on va utiliser un LLM gratuit, faite dans OPENCODE "/model" et choisissez une modele gratuit



Il faudra une fois ça fait me donner votre nom d'utilisateur GitHub ( et non votre adresse mail) pour que je puisse vous ajouter au dossier projet sur Github. 
Une fois que je vous ai ajouté faites dans votre terminal "gh repo clone Louison-code/Projet-G1-G2" ou demander à Opencode de cloner dans le workspace "Louison-code/Projet-G1-G2", le fichier projet est maintenant dans votre ordinateur et vous pouvez travailler dessus.
Une fois vos modifs faites il faut commit et push vos modifs demander à opencode de le faire pour vous, (vos modifs seront actualisées sur GitHub)




### Exemples de demandes à OpenCode

- "Ajoute les collaborateurs "non d'utilisateur GitHub" au dépôt GitHub"
- "Explique ce que fait cette fonction"
- "Crée un fichier README pour le dossier 03_IA"
- "Trouve les erreurs dans le fichier scraper.py"
- "Ajoute des commentaires à ce code"

---


## Résumé : Ce que vous pouvez faire avec ces outils

| Outil | Utilité principale |
|-------|-------------------|
| **Warp** | Terminal moderne + IA intégrée pour poser des questions |
| **Git** | Sauvegarder et versionner le code localement |
| **GitHub** | Stocker le code en ligne, travailler en équipe |
| **GitHub CLI** | Gérer GitHub depuis le terminal |
| **OpenCode** | Assistant IA pour coder, modifier, expliquer, débugger |

### Workflow typique

```bash
# 1. Ouvrir Warp
# 2. Cloner le projet (une seule fois)
gh repo clone Louison-code/Projet-G1-G2

# 3. Lancer OpenCode
cd Projet-G1-G2 ou cd Opencode_workspace
opencode

# 4. Travailler avec Git
git add .
git commit -m "Ajout de la fonctionnalité X"
git push
```

---

BAUDOUIN Louison
