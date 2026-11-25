# Suivi d'avancement — Locksmith Wars

## Fait
- Code complet du jeu dans Studio (minage, forge, crochetage, coffres, tutoriel, classements,
  boutique, effets et sons, animations du personnage en code).
- Coffres VLT_Lvl1–3 et serrures LCK_T1–3 construits en pièces Roblox (provisoires).
- Étape 0 : calibrage Blender → Roblox validé.
- Étape 1 : ORE_F1 modélisé, importé, normalisé, rangé dans Assets.ORE, aperçu dans Workspace.Preview_ORE.
- Étape 1 : ORE_F2, ORE_F3, ORE_F4, ORE_Rubble, ORE_Chunk, ING_Bar modélisés, exportés, contrôle
  qualité passé (planche `renders/lot1_ORE_ING.png`). Pas encore importés dans Studio.
- Étape 2 : TOOL_Pickaxe et TOOL_Hammer modélisés, exportés, contrôle qualité passé (planche
  `renders/lot2_TOOL.png`). Pas encore importés dans Studio.
- Interrupteurs `ReplicatedStorage.Config.Features` créés (MeshOres, MeshTools, MeshForge, MeshIngot).
- Gisements en mesh branchés dans `Services.MiningService` et `Controllers.MiningController`
  derrière `MeshOres` (actif pour F1 ; F2–F4 et Rubble pris en charge dès leur arrivée dans Assets.ORE).

- Sessions 3 et 4 (2026-11-13) : lots 3 (forge), 4a (coffres), 5 (effets), 6 (environnement)
  modélisés ; envoi automatique au nom du groupe (`scripts/upload_to_roblox.py`,
  `exports/uploads.json`) ; 20 assets insérés, normalisés, rangés, aperçus posés.
- Session 5 (2026-11-15/16) : tous les branchements E.1 à E.8 et E.10 faits et testés (gisements,
  éclats, lingot, pioche, marteau, forge, coffres mesh, effets). Interrupteurs : MeshOres, MeshTools,
  MeshForge, MeshIngot, MeshOreShake, MeshVaults, MeshFX. Lot 4b (serrures LCK_T1–T3) modélisé.

- Session 6 (2026-11-17) : serrures mesh (E.9, `MeshLocks`), tas d'or S/L, aperçus MIN/ENV (E.11)
  avec ENV_LB_Topper_Mask, lot « Ambiance » (`Ambiance`). Toute l'étape E du brief 4 est terminée.
- Session 7 (2026-11-17/18) : retours de la session 6 (LightingStyle conservé par le repli, ombres
  adoucies, écran du classement solide) ; ciel personnalisé SKY_Warm (derrière `Ambiance`) ; lot 9
  phase 1 : 3 blockouts de carte `MapDraft_A/B/C` mesurés et comparés.

- Session 8 (2026-11-18, reprise 2026-11-24/25) : lot 9 phase 2 — carte « Place du marché »
  (variante B, forge en alcôve est) construite à (-1800, 0, 0) derrière `NewMap`, falaises
  modulaires ENV_Cliff_A/B/Corner/Peak, habillage, ambiance propre à la carte, boucle complète
  testée ; `MapDraft_B`, `MapStudy_B` et `Preview_*` retirés. **Premier rendu complet atteint.**

## En cours
- Batterie de tests de l'utilisateur dans Studio (rien n'a encore été jugé à l'œil).
- Attente des retours sur la carte (premier rendu complet) et des 3 questions du rapport
  (rares au centre, classements dans le dos, validation de B).
- Rapport de la dernière session : `docs/rapports/2026-11-18_session8.md`.
- Prochain lot : 8 (visuels de lancement), après les retouches légères de la carte.

## À réimporter au nom du groupe avant la sortie
Liste vide : tout est envoyé au nom du groupe WingedSword Empire (33016933) depuis la session 4.
L'ancien ORE_F1 (à ton nom) est dans `Assets_Backup.ORE.ORE_F1_2026-11-13`.

## À faire avant la sortie (hors 3D)
- Team Test à deux (gameplay, équilibrage, visibilité des animations par les autres joueurs).
- Créer gamepasses et produit, reporter les Id dans Config.Monetization.
- Max 8 joueurs par serveur, NewPlayerProtection = 900, questionnaire de maturité, ProfileStore.

## Idées pour après le premier rendu
- Une fois tous les lots terminés et le premier rendu complet obtenu : exploration de style
  (matériaux personnalisés, autres directions graphiques). Ne pas commencer avant (demande du 2026-11-17).
- Wagonnet de minerai rare qui traverse la rue à intervalles réguliers et que les joueurs se
  disputent (inspiré du tapis roulant central de Steal a Brainrot). Demande du code : après le
  premier rendu.
- Verrouillage manuel gratuit du coffre avec temps de recharge (à étudier avec l'équilibrage).

## Journal
- 2026-11-25 : passage à un agent unique (sous-agents archivés dans docs/archives/agents/, règles dans docs/regles/) ; l'équipe passe à 3 personnes ; verrou de session docs/SESSION_EN_COURS.md.
- (le chef de projet ajoute ici une ligne datée par étape terminée)
- 2026-11-13 : fin de la modélisation du lot 1 (6 assets, contrôle qualité passé) ; branchement
  des gisements en mesh derrière `Features.MeshOres`, testé et enregistré (sans publication) ; modélisation du lot 2 (pioche, marteau).
- 2026-11-13 : envoi automatique au nom du groupe en service ; 20 assets intégrés (version 22 du lieu).
- 2026-11-16 : branchements E.3 à E.8 et E.10 vérifiés en jeu, lieu enregistré en version 35 ;
  serrures LCK_T2 et LCK_T3 modélisées, planche globale `renders/session3_global.png`.
- 2026-11-17 : 11 skills installées dans `.claude/skills/` (Apache-2.0), mentionnées dans CLAUDE.md et les agents.
- 2026-11-17 : E.9 serrures mesh (v38) ; tas d'or S/L (v40) ; E.11 aperçus MIN/ENV + Topper_Mask
  envoyé (v42) ; lot Ambiance (v44). Interrupteurs MeshLocks et Ambiance créés, tous testés.
- 2026-11-17/18 (session 7) : retours de la session 6 (v46) ; ciel SKY_Warm (v48) ; blockouts de carte
  A (v50), B + retouche A (v52), C (v55), présentation finale des 3 variantes ; arrêt pour le choix.
- 2026-11-18 (session 8) : étude de la forge, Opt1 alcôve est (v58) ; falaises modélisées, contrôlées,
  envoyées (4 Approved) ; session coupée pendant la construction.
- 2026-11-24/25 (reprise session 8) : inventaire (Terrain seul construit, démarrage OK) ; structure
  NewMap + MapSwitch + VaultPoint (v67) ; habillage, ambiance, boucle complète (v72) ; nettoyage (v73).
