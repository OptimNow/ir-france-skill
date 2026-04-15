# ir-france-skill

Skill pour agents IA (Claude Code, Claude Desktop, Cursor, Windsurf, Cline) qui guide le remplissage de la **déclaration d'impôt sur le revenu en France** (formulaire 2042 et annexes).

## Ce que fait cette skill

- **Parcours guidé** : accompagne étape par étape le remplissage de la déclaration, de la collecte des documents jusqu'à la validation finale
- **Mapping des cases** : correspondance entre chaque type de revenu et les cases exactes des formulaires (2042, 2042-C-PRO, 2042-RICI, 2044, 2047, 2086...)
- **Simulation d'IR** : calcul estimatif du montant d'impôt avec comparaison PFU vs option barème
- **Cas courants et spéciaux** : salaires, BNC/BIC, micro-entreprise, revenus fonciers, dividendes, intérêts, plus-values mobilières et immobilières, crypto-actifs, stock-options, AGA, BSPCE, revenus de source étrangère, régime d'impatriation
- **Checklist documentaire** personnalisée selon le profil du contribuable
- **Erreurs fréquentes** et points de vigilance

## Ce que cette skill ne fait PAS

> **Avertissement important**
>
> Cette skill est un **outil d'aide au remplissage**. Elle ne remplace pas un conseil fiscal professionnel.
>
> - Elle ne télédéclare rien sur impots.gouv.fr
> - Elle ne garantit pas l'exactitude des calculs (les barèmes sont indicatifs et doivent être vérifiés)
> - Elle ne constitue pas un avis fiscal ou juridique
> - La responsabilité du contenu de la déclaration reste celle du contribuable
>
> Pour les situations complexes (optimisation patrimoniale, contrôle fiscal, montages internationaux), consultez un expert-comptable ou un avocat fiscaliste.

## Année fiscale

| Version | Revenus | Déclaration | Statut |
|---------|---------|-------------|--------|
| 1.0.x   | 2025    | Printemps 2026 | En cours -- barèmes à confirmer avec la LFI 2026 |

Les barèmes et seuils sont dans `references/bareme-et-seuils.md`. Ce fichier doit être mis à jour chaque année après publication de la loi de finances au Journal Officiel.

## Installation

### Claude Code

```bash
# Installation globale (disponible dans tous les projets)
cd ~/.claude/skills
git clone https://github.com/OptimNow/ir-france-skill.git ir-france

# OU installation par projet
cd /chemin/vers/votre/projet
mkdir -p .claude/skills
cd .claude/skills
git clone https://github.com/OptimNow/ir-france-skill.git ir-france
```

### Autres agents (Cursor, Windsurf, Cline...)

Clonez le repo et pointez votre agent vers le fichier `SKILL.md`. La skill est en Markdown pur avec un script Python, elle fonctionne avec tout agent capable de lire des fichiers et d'exécuter du code.

### Claude Desktop / Claude.ai

Téléchargez le fichier `.skill` depuis les [Releases](../../releases) et installez-le via l'interface.

## Structure

```
ir-france-skill/
├── SKILL.md                              # Point d'entrée (workflow et routage)
├── references/
│   ├── bareme-et-seuils.md               # Barème IR, décote, seuils (MAJ annuelle)
│   ├── revenus-activite.md               # Salaires, BNC, BIC, auto-entrepreneur
│   ├── revenus-capitaux.md               # Dividendes, intérêts, PFU vs barème, AV
│   ├── plus-values.md                    # Mobilières, immobilières, crypto
│   ├── revenus-fonciers.md               # Micro-foncier, réel, SCPI, Pinel
│   ├── revenus-etrangers.md              # Conventions, 2047, comptes étrangers
│   ├── cas-speciaux.md                   # Stock-options, AGA, BSPCE, impatriation
│   ├── reductions-credits.md             # Réductions, crédits, charges déductibles
│   ├── prelevements-sociaux.md           # CSG, CRDS, prélèvements sociaux
│   ├── formulaires-mapping.md            # Correspondance revenus -> cases
│   └── erreurs-frequentes.md             # Pièges courants, checklist, correction
├── scripts/
│   └── simulateur-ir.py                  # Calcul IR, décote, QF, PFU vs barème
├── LICENSE
└── README.md
```

### Architecture

Le SKILL.md sert de **routeur** : il guide le workflow et pointe vers le fichier de référence pertinent selon la situation. L'agent ne charge que ce dont il a besoin, ce qui évite de saturer le contexte.

## Utilisation

Dites simplement à votre agent :

- *"Aide-moi à remplir ma déclaration d'impôts"*
- *"Je suis freelance en micro-BNC avec des dividendes, quelles cases je remplis ?"*
- *"Compare PFU et option barème pour mon cas"*
- *"Qu'est-ce que je dois déclarer pour mes crypto ?"*
- *"Checklist des documents pour ma déclaration"*

La skill s'active automatiquement quand votre question concerne la fiscalité des revenus en France.

## Simulateur

Le script `scripts/simulateur-ir.py` calcule :

- IR au barème progressif avec quotient familial
- Décote
- Réductions et crédits d'impôt (avec plafonnement des niches)
- PFU sur les revenus de capitaux
- Prélèvements sociaux
- CEHR (contribution exceptionnelle sur les hauts revenus)
- Comparaison PFU vs option barème avec recommandation

Le simulateur est un outil d'estimation. Pour le calcul officiel, utilisez le [simulateur de la DGFiP](https://www.impots.gouv.fr/simulateurs).

## Contribuer

Les contributions sont bienvenues, notamment :

- **Mise à jour annuelle** des barèmes et seuils après publication de la loi de finances
- **Cas manquants** : si un type de revenu ou une situation n'est pas couvert
- **Corrections** : erreurs dans les numéros de cases, les taux, les seuils
- **Amélioration du simulateur** : cas croisés, interactions entre dispositifs
- **Tests** : ajout de cas de test avec des résultats vérifiés

Merci d'ouvrir une issue avant de soumettre une PR significative.

### Convention de versioning

- `1.x.x` : revenus 2025
- `2.x.x` : revenus 2026
- etc.

Le numéro majeur suit l'année de revenus.

## Limites connues

1. Les barèmes sont indicatifs et basés sur des projections. Ils doivent être vérifiés avec les montants officiels publiés au Journal Officiel.
2. Le simulateur ne gère pas toutes les interactions croisées (plafonnement QF combiné avec déficits, impatriation, taux effectif pour revenus étrangers).
3. Certains dispositifs anciens (plans de stock-options pré-2012, anciens PERP) sont mentionnés mais pas détaillés.
4. La skill ne couvre pas l'IFI (Impôt sur la Fortune Immobilière), qui fait l'objet d'une déclaration séparée.

## Liens utiles

- [impots.gouv.fr -- Simulateur officiel](https://www.impots.gouv.fr/simulateurs)
- [Service Public -- Déclaration de revenus](https://www.service-public.gouv.fr/particuliers/vosdroits/F358)
- [BOFiP -- Bulletin Officiel des Finances Publiques](https://bofip.impots.gouv.fr/)
- [Formulaire 2042](https://www.impots.gouv.fr/formulaire/2042/declaration-des-revenus)
- [Brochure pratique IR](https://www.impots.gouv.fr/www2/fichiers/documentation/brochure/ir_2026/accueil.htm)

## Projets liés

- [Paperasse](https://github.com/romainsimon/paperasse) -- Skills IA pour la comptabilité et fiscalité des entreprises françaises (IS, liasse fiscale, FEC, notariat)

## Licence

[MIT](LICENSE)
