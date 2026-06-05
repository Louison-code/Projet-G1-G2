# Fichiers à déplacer sur Google Drive

Ces fichiers sont des **livrables/fichiers binaires** qui ne devraient pas être versionnés dans Git. Déplacez-les sur Google Drive (ou autre cloud) puis supprimez-les du dépôt.

---

## 📁 docs/gestion_projet/

### Présentations (.pptx)
| Fichier | Taille |
|---------|--------|
| `docs/gestion_projet/00_Presentations/AUDIT_FINAL_TousPoles_CentraleLille (1).pptx` | |
| `docs/gestion_projet/00_Presentations/Architecture RAG_N8N_Agent Open Claw.pptx` | |
| `docs/gestion_projet/00_Presentations/Presentation_Client_G1G2.pptx` | |
| `docs/gestion_projet/00_Presentations/Reunion P Yim 23 Mars 2026_.pptx` | |
| `docs/gestion_projet/00_Presentations/presentation ds.pptx` | |
| `docs/gestion_projet/00_Présentations/Architecture_Application.pptx` | |
| `docs/gestion_projet/99_ARCHIVES/Audit GdP.pptx` | |
| `docs/gestion_projet/99_ARCHIVES/WBS V2.pptx` | |
| `docs/gestion_projet/99_ARCHIVES/WBS.pptx` | |

### Tableurs (.xlsx, .ods)
| Fichier | Taille |
|---------|--------|
| `docs/gestion_projet/00_Presentations/Bareme audit technique.xlsx` | |
| `docs/gestion_projet/01_Cadrage/Matrice RACI.xlsx` | |
| `docs/gestion_projet/01_Cadrage/Matrice competences.xlsx` | |
| `docs/gestion_projet/02_Planning/TO DO LIST.xlsx` | |
| `docs/gestion_projet/03_Suivi_Equipe/Suivi horaire/Comptabilité des heures.xlsx` | |
| `docs/gestion_projet/04_Risques_et_Qualité/Fiche éval risques version finale-1 (1).xlsx` | |
| `docs/gestion_projet/99_ARCHIVES/BUDGET.xlsx` | |
| `docs/gestion_projet/99_ARCHIVES/Copie de Gant.xlsx` | |
| `docs/gestion_projet/99_ARCHIVES/RACI.xlsx` | |
| `docs/gestion_projet/99_ARCHIVES/RACI_1.xlsx` | |
| `docs/gestion_projet/99_ARCHIVES/RACI_1.ods` | |

### Documents (.docx)
| Fichier | Taille |
|---------|--------|
| `docs/gestion_projet/01_Cadrage/WBS.docx` | |
| `docs/gestion_projet/01_Cadrage/cahier des charges.docx` | |
| `docs/gestion_projet/03_Suivi_Equipe/02-06-2026.docx` | |
| (tous les CR réunions dans `docs/gestion_projet/03_Suivi_Equipe/CR reunions/*.docx`) | |
| `docs/gestion_projet/99_ARCHIVES/Cahier des charges V1.docx` | |
| `docs/gestion_projet/99_ARCHIVES/TO DO LIST.docx` | |
| `docs/gestion_projet/99_ARCHIVES/WBS texte.docx` | |
| `docs/gestion_projet/99_ARCHIVES/intro_audit_GdP.docx` | |

### PDFs
| Fichier | Taille |
|---------|--------|
| `docs/gestion_projet/01_Cadrage/charte du projet.pdf` | |
| `docs/gestion_projet/03_Suivi_Equipe/fiche projet.pdf` | |
| `docs/gestion_projet/99_ARCHIVES/Gestion des risques.pdf` | |
| `docs/gestion_projet/99_ARCHIVES/Ressources Utiles.pdf` | |
| `docs/gestion_projet/99_ARCHIVES/roles.pdf` | |

### Images (.jpg, .png)
| Fichier | Taille |
|---------|--------|
| `docs/gestion_projet/03_Suivi_Equipe/photos equipe/IMG_1382.PNG` | |
| `docs/gestion_projet/03_Suivi_Equipe/photos equipe/IMG_3068.jpeg` | |
| `docs/gestion_projet/03_Suivi_Equipe/photos equipe/PrevauxIsidorePortrait.jpg` | |
| `docs/gestion_projet/03_Suivi_Equipe/photos equipe/rana.jpg` | |
| `docs/gestion_projet/99_ARCHIVES/matrice de compétences V1.PNG` | |
| `docs/gestion_projet/99_ARCHIVES/Tableau des risuqes.jpg` | |

### Autres
| Fichier | Taille |
|---------|--------|
| `docs/gestion_projet/02_Planning/gantt.gan` | (fichier GanttProject) |
| `docs/gestion_projet/99_ARCHIVES/intro_audit_GdP.odt` | |

---

## 📁 docs/ia/

| Fichier | Taille |
|---------|--------|
| `docs/ia/00_Documentations/Synthese_NLP_IA.pdf` | |

---

## 📁 docs/archives/scraping/

Tout le dossier `docs/archives/scraping/` contient des fichiers binaires et des archives d'anciennes versions. **À déplacer entièrement sur Drive.**

Fichiers notables :
- `liste URL_KOMPASS.xlsx` (plusieurs copies)
- `Livrable_Final_PowerBI.xlsx` (plusieurs versions)
- `Livrable_IA_Nettoye.json`
- `rapport_T1_T3_scraping.pdf`
- `scrypt SQL.docx`
- `EXPLICATION scraping.docx`
- Anciens scripts Python (archives)

---

## 📁 data/

| Fichier | Taille |
|---------|--------|
| `data/base_reindustrialisation.db` | Base SQLite (déjà dans .gitignore) |

La base est déjà exclue de Git via `.gitignore`. **Ne pas l'ajouter**, elle reste sur le Drive.

---

## Organisation suggérée sur Google Drive

```
📁 Projet-G1-G2_Livrables/
├── 📁 Presentations/
├── 📁 Documents_Projet/        (CDC, WBS, RACI, CR réunions)
├── 📁 Planning_Suivi/          (Gantt, TO DO, comptabilité heures)
├── 📁 Conformite_Juridique/    (si fichiers binaires)
├── 📁 Scraping_Archives/       (anciens scripts, exports)
├── 📁 Base_Donnees/            (base_reindustrialisation.db)
├── 📁 Photos_Equipe/
└── 📁 IA/                      (Synthèse NLP, datasets)
```
