# Commentaires pour la prochaine session

Écris tes retours ici en fin de session (une ligne par point). Le chef de projet les traite en
priorité au début de la session suivante, les coche et y répond.

## À traiter
### Pour la session suivante


## Historique
### Retours sur la session 7 (2026-11-17/18), traités en session 8 (2026-11-18 → 2026-11-25)
- [x] **Ton choix de variante pour la carte** (A, B, C ou un mélange ; recommandation : B) :
  **Variante B « Place du marché » retenue, pour le moment** (choix révisable après le premier
  rendu complet). Précisions :
  - Pas de terrasses pour l'instant.
  - Étudie le rapprochement de la forge (par exemple sur un côté de la place plutôt qu'au bout de
    l'axe) pour réduire le trajet des parcelles du sud (13,8 s aujourd'hui), SEULEMENT si ça ne
    dégrade pas la place ni la lisibilité. Sinon, garde B tel quel. Explique ton choix dans le rapport.
  - Garde l'équilibre actuel du temps mine → coffre (3,6 à 5,7 s) : c'est ce qui laisse une vraie
    chance au voleur comme au propriétaire. Toute modification de la disposition doit le préserver.
  - Garde `MapDraft_A` et `MapDraft_C` (ne les supprime pas) jusqu'à ce que j'aie validé le premier
    rendu complet : je veux pouvoir revenir sur mon choix. Seuls `MapDraft_B` et les `Preview_*`
    peuvent être retirés une fois la vraie carte construite et vérifiée.
  → Fait (session 8) : B construite sans terrasses ; forge rapprochée dans une alcôve à l’est de la place (parcelle la plus loin 13,7 → 6,7 s, place intacte, justification dans le rapport) ; mine → coffre préservé (3,5–6,0 s calculés, 4,0–5,6 s en marche réelle) ; MapDraft_A et MapDraft_C gardés.
- [x] **LOT 9 — PHASE 2 — Construction (après ton choix)** (brief du 2026-11-17, recopié) :
  - Terrain Roblox (herbe, roche, chemins pavés, falaises), puis placement des assets ENV, MIN,
    FRG et des lanternes ; décor d'appoint cohérent avec la direction artistique.
  - Respecte les contrats du code (voir `CONTEXTE_PROJET.md`) : 8 parcelles BasePart nommées
    Plot1..Plot8 dans `Workspace.Plots` (orientation des coffres vers la rue à adapter) ;
    12 repères dans `Workspace.Mine.Spawns` ; pièce `Workspace.Forge.Anvil` avec son `ForgePrompt` ;
    panneaux `Workspace.Leaderboards.Gold` et `Steals` avec leur `BoardGui` ; `SpawnLocation` sur le
    socle d'apparition.
  - Interrupteur `NewMap` dans `Config.Features` : à false, l'ancienne disposition revient.
  - Ajuste l'ambiance à la nouvelle carte, puis supprime les dossiers `Preview_*` et `MapDraft_B`
    devenus inutiles (après avoir tout vérifié et sauvegardé). NE supprime PAS `MapDraft_A` ni
    `MapDraft_C`.
  - Captures avant / après de chaque zone, temps de trajet mesurés en jeu, test complet de la
    boucle (miner, forger, crocheter le Mannequin, revenir à son coffre), puis enregistrement du lieu.
  → Fait (session 8, versions 67 → 73) : Terrain + falaises modulaires, assets ENV/MIN/FRG, 16 lanternes, contrats respectés, interrupteur NewMap (false testé), ambiance propre à la carte, captures avant / après, boucle complète testée ; MapDraft_B, MapStudy_B et Preview_* retirés après enregistrement. Détail : docs/rapports/2026-11-18_session8.md.

### Retours sur la session 6 (2026-11-17), traités en session 7 (2026-11-17/18)
- [x] Éclairage : la propriété `Lighting.Technology` n'existe plus dans ma version de Studio. J'ai
  réglé `LightingStyle` à la main (`PrioritizeLightingQuality` coché). Lis la valeur actuelle,
  vérifie que l'ambiance rend bien avec ce réglage et ajuste si besoin (ombres près des parcelles,
  budgets). Mets à jour le rapport et la batterie de tests en conséquence.
  → Fait (session 7) : `Realistic` + `PrioritizeLightingQuality` lus et conservés ; le repli `Ambiance` ne les touche plus (il aurait remis Soft) ; ombres adoucies (ShadowSoftness 0,35, EnvironmentDiffuseScale 0,75), budgets mesurés et respectés.
- [x] Lanternes de la mine : à garder ; elles seront intégrées à la vraie carte (lot 9).
  → Noté : gardées, placées sur la vraie carte en phase 2.
- [x] Heure 16 h 30 : OK. Remplace le ciel par défaut par un ciel personnalisé chaud et stylisé,
  cohérent avec la direction artistique, derrière l'interrupteur `Ambiance`.
  → Fait : ciel SKY_Warm peint dans Blender, envoyé au nom du groupe, posé dans `Lighting.Sky` derrière `Ambiance` (repli testé).
- [x] Panneau de classement : ajoute une collision sur l'écran (on ne doit plus pouvoir le traverser).
  → Fait : `Screen` solide (Assets.ENV et Preview_ENV), testé (le personnage est bloqué).
- [x] Ma batterie de tests n'est pas encore faite : ce n'est pas bloquant, continue.
  → Noté ; batterie mise à jour dans le rapport de la session 7.
- [x] Versions 39 et 41 du lieu : probablement mon ami (Team Create) ; rien à faire.
  → Noté, rien à faire.

- [x] **LOT 9 — PHASE 1 — LA CARTE (objectif : le premier rendu complet du jeu).** Aujourd'hui il n'y a pas
  de vraie carte : plaque grise, blocs provisoires, assets en aperçu.

  **Phase 1 — Concept, puis ARRÊT pour mon choix.**
  - Disposition inspirée de Steal a Brainrot, sans copier ses visuels : « la rue des serruriers ».
    8 parcelles en deux rangées de 4, face à face, de part et d'autre d'une rue centrale ; chaque
    coffre regarde la rue. Les gisements de la mine occupent le centre de la rue (point de
    rassemblement, comme le tapis roulant de SaB), les rares bien visibles. La forge et la place
    d'apparition (classements) à une extrémité. Carte compacte : depuis la mine on voit son coffre
    et on peut y revenir en quelques secondes quand l'alarme sonne.
  - Univers : petite rue d'artisans serruriers-forgerons fermée par des falaises / montagnes, dans
    la direction artistique actuelle (low-poly chunky, couleurs unies) avec l'ambiance actuelle.
  - Propose 3 variantes de cette disposition (largeur de la rue, place de la forge, organisation
    des gisements, relief) : pour chacune, un plan vu du dessus annoté et 2 captures en perspective
    (blockout en pièces grises dans `Workspace.MapDraft_<A/B/C>`), avec les temps de trajet mesurés
    (vitesse de marche 16 studs/s) : parcelle la plus éloignée → mine et → forge ; mine → chaque
    coffre. Points forts, points faibles, impact sur les téléphones.
  - Contraintes gameplay : toute parcelle à 15–20 s maximum de la mine et de la forge ; le voleur
    et le propriétaire doivent pouvoir se croiser ; coffres visibles de loin ; pas de recoins où
    l'on se coince ; carte compacte pour les téléphones.
  - Attention au code : les coffres se tournent aujourd'hui vers le point (0, y, 0). Avec deux
    rangées, ils devront regarder la rue : prévois cette adaptation pour la phase 2.
  - Présentation pour que je puisse comparer facilement :
    - les 3 maquettes côte à côte, espacées d'au moins 600 studs sur l'axe X (A à x = 1000,
      B à x = 1600, C à x = 2200), loin de la carte actuelle, chacune avec un grand panneau
      « VARIANTE A / B / C » visible de loin et un `SpawnLocation` désactivé à son entrée ;
    - une planche de synthèse `renders/lot9_variantes.png` : les 3 plans vus du dessus côte à
      côte, à la même échelle, avec une légende de couleurs identique (parcelles, rue, gisements,
      forge, apparition, classements) ;
    - un tableau comparatif unique dans le rapport (une ligne par variante : temps de trajet,
      taille de la carte, points forts, points faibles, ta recommandation argumentée) ;
    - comment aller voir chaque variante dans Studio (où se placer, quoi regarder).
  - **ARRÊTE-TOI et attends mon choix.** Ne supprime pas les blockouts avant ma réponse. Je
    répondrai dans `docs/COMMENTAIRES.md` (par exemple « Variante B, avec la forge de la A »).

  → Phase 1 faite (session 7) : blockouts `MapDraft_A/B/C`, plans annotés `renders/lot9/*_plan_annote.png`, captures, temps mesurés ; comparaison et recommandation (B) dans `docs/rapports/2026-11-17_session7.md`. Présentation faite comme demandé : A x = 1000, B x = 1600, C x = 2200, panneau « VARIANTE X » au-dessus de l'entrée, `Draft_Spawn_X` désactivé, planche `renders/lot9_variantes.png` (même échelle, légende unique), tableau comparatif et points de vue dans le rapport. Blockouts gardés. **En attente de ton choix.**

- [x] Idées notées pour après le premier rendu (ne pas faire maintenant) : wagonnet de minerai rare
  dans la rue, verrouillage manuel du coffre. Déjà ajoutées dans `docs/SUIVI.md`.
  → Noté (déjà dans SUIVI.md).

### Session 4 du 2026-11-13 (traitée en sessions 5 et 6, 2026-11-15 → 2026-11-17)
_Brief de la session 4 (intégré le 2026-11-13 depuis COMMENTAIRES_NOUVEAUX_v2.md). Tous les points sont traités._

#### A. Changements depuis la dernière session
- [x] Droits du groupe et clé API installée. → Anciens points « Pas de clé API » et « Créateur = Moi » cochés RÉGLÉS ; plus aucune liste d'import manuel.
- [x] Planches et tests pas encore regardés, tout est validé par défaut. → Noté ; batterie de tests fournie dans le rapport du 2026-11-17.
- [x] Animations R15 repoussées après le Team Test. → Lot 7 hors plan.

#### B. Règles de cette session
- [x] Rapport au fil de l'eau avec « Point de reprise ». → Appliqué (sessions 5 et 6).
- [x] Un seul agent dans Studio, mode Édition. → Respecté.
- [x] Interrupteur + repli + Assets_Backup pour toute intégration. → Respecté (9 interrupteurs, sauvegardes LCK et Lighting ajoutées).
- [x] Partie de test, console, vérification, arrêt, enregistrement ; jamais de publication. → Respecté (versions 38, 40, 42, 44).
- [x] Aucune valeur d'équilibrage modifiée, aucune fonctionnalité supprimée. → Respecté.
- [x] Ordre de priorité. → Suivi jusqu'au bout.

#### C. Étape 1 — Envoi automatique
- [x] Test d'envoi de CAL_Cube_1x1x1. → 73335461523854, Approved (session 4).
- [x] Cas d'arrêt 401/403. → Ne s'est pas produit.
- [x] Asset au nom du groupe. → Vérifié (WingedSword Empire, 33016933).

#### D. Étape 2 — Envoi et préparation
- [x] 1-2. Envoi au nom du groupe de tous les FBX. → Fait ; dernier : ENV_LB_Topper_Mask (71981959915048) le 2026-11-17.
- [x] 3. Insertion, normalisation, manifest, rangement, anciennes versions dans Assets_Backup. → Fait, y compris LCK (2026-11-17).
- [x] 4. Aperçus Preview_<CAT>. → ORE, FRG, ING, TOOL, FX, VLT, LCK, MIN, ENV.
- [x] 5. Liste « À réimporter » vidée. → Fait.

#### E. Étape 3 — Branchements
- [x] 1. Gisements F2–F4, Rubble. → Session 5.
- [x] 2. Cristaux qui tremblent. → Session 3 (MeshOreShake).
- [x] 3. ORE_Chunk. → Session 5.
- [x] 4. ING_Bar. → Session 5.
- [x] 5. Pioche. → Session 5 (Grip 1,06, ancienne pioche en repli).
- [x] 6. Marteau. → Session 5.
- [x] 7. Forge. → Session 5 (Anvil invisible gardé avec ForgePrompt).
- [x] 8. Coffres. → Session 5, 3 niveaux testés.
- [x] 9. Serrures. → 2026-11-17, interrupteur MeshLocks, teinte Fer/Or/Aetherite testée.
- [x] 10. Effets. → Session 5 ; tas d'or S et L ajoutés le 2026-11-17.
- [x] 11. Environnement en aperçu seulement. → 2026-11-17 (Preview_MIN, Preview_ENV), carte inchangée.

#### F. Étape 4 — Modélisation
- [x] Reprise du point de reprise de la session 3. → Lots 6 et 4b terminés, planche globale faite, Topper_Mask corrigé et contrôlé.

#### G. Rapport de fin de session
- [x] « État des interrupteurs ». → Dans le rapport du 2026-11-17.
- [x] « Batterie de tests pour toi ». → Dans le rapport du 2026-11-17 (11 étapes).
- [x] « Assets ». → Dans le rapport du 2026-11-17.
- [x] SUIVI.md et CONTEXTE_PROJET.md à jour. → Fait.

### Session 3 du 2026-11-13
_Brief de la session 3 (modélisation). Session coupée par la limite d'utilisation : lots 3, 4a et 5 modélisés, point E fait ; restent le contrôle qualité du lot 5, les lots 6 et 4b et la planche globale (repris au point F du brief de la session 4). Les cases non cochées ci-dessous sont dans cet état._

#### A. Décisions sur la session précédente
- [x] Lot 1 (F2, F3, F4, Rubble, Chunk, ING_Bar) et lot 2 (pioche, marteau) : validés par défaut.
  Je n'ai pas encore regardé les planches ; mes retours éventuels viendront plus tard.
  → Noté : lots 1 et 2 considérés validés, ils servent de référence de style avec ORE_F1. Retouches possibles plus tard.
- [x] Hauteurs de F3 (6,13) et F4 (6,50) : garder telles quelles. Piédestal F4 : ne pas toucher.
  → Noté : aucune retouche de F3/F4.
- [x] ORE_Rubble sans collision : d'accord.
  → Noté : manifest inchangé (canCollide = false).
- [x] Droits du groupe : pas de date. Continuer avec Créateur = Moi et tenir à jour la liste
  « À réimporter au nom du groupe avant la sortie » dans `docs/SUIVI.md`.
  → Noté : consigne maintenue ; la liste de SUIVI.md est complétée en fin de session (point F).
- [x] Animations R15 (lot 7) : repoussé après le Team Test. Ne pas le bloquer, ne pas le relancer.
  → Noté : lot 7 sorti du plan jusqu'au Team Test ; plus de question à ce sujet dans les rapports.

#### B. Règles de cette session
- [ ] Les 8 FBX de la session précédente ne sont PAS importés, et la batterie de tests en jeu se
  fera plus tard. Cette session est consacrée à la MODÉLISATION : pas d'intégration ni de test en
  jeu, sauf exception du point E.
- [ ] Rédige le rapport AU FIL DE L'EAU : crée `docs/rapports/AAAA-MM-JJ.md` dès le début et
  complète-le après chaque asset terminé, avec une section « Point de reprise » (dernier asset
  terminé, prochain asset). La session précédente a été coupée par la limite d'utilisation : si ça
  se reproduit, la suivante doit pouvoir reprendre exactement là.
- [ ] Enregistre `locksmith_assets.blend` après chaque asset ; mets le manifest à jour à chaque export.
- [ ] Pour chaque NOUVELLE famille de style (forge, coffres, serrures, effets, environnement), fais
  le premier asset seul, examine sa planche au regard de la direction artistique et des lots
  validés (ORE_F1 = référence de style), corrige, puis décline le reste.
- [ ] `qa-reviewer` contrôle chaque lot avant de passer au suivant (3 allers-retours maximum).
- [ ] Ordre de priorité : lot 3 → lot 4a → lot 5 → lot 6 → lot 4b. Si la session s'arrête avant la
  fin, ce n'est pas grave : la priorité est la qualité de ce qui est terminé.

#### C. Cahier détaillé des lots (coordonnées en repère BLENDER : X droite, Y profondeur, Z haut,
#### avant = -Y ; rappel : ce qui doit être en -X dans Roblox se place en +X dans Blender)

##### Lot 3 — Forge (ambiance chaude : bois, brique, orange, laiton)
1. **FRG_Anvil** (premier asset de la famille, à faire seul) — encombrement ≈ 4 × 2 × 3.
   - `Body` : enclume en acier sombre #2E2E33 (Metal), corps évasé vers le haut, corne conique à
     l'avant-gauche, talon carré, biseaux marqués. Table plate et bien lisible.
   - `Stump` : billot de bois #8B5A2B (WoodPlanks) sous l'enclume, cerclé d'un anneau de fer
     (pièce `Band`, #5A5F66, Metal).
   - **Le dessus de la table doit être à 3,0 studs du sol** : le code pose le lingot à cette hauteur.
   - Repère `IngotPoint` au centre de la table (z = 3,0).
2. **FRG_Furnace** — encombrement ≈ 8 × 8 × 10, bouche face à l'avant (-Y).
   - `Body` : fourneau en briques #6B3A2A (Brick) sur socle de pierre (pièce `Base`, #5B5650, Slate).
   - `Hood` : hotte et cheminée en métal sombre (#3B3F45, Metal), légèrement trapue.
   - `Glow` : plan au fond de la bouche, rôle `fixed`, matériau Neon, #FF7A1A (deviendra lumineux).
   - Option si le style le permet : 2 ou 3 braises en saillie dans la bouche (pièce `Embers`, Neon #FFB347).
3. **FRG_Workbench** — encombrement ≈ 8 × 4 × 4.
   - `Top` : plateau épais en bois (WoodPlanks #8B5A2B) ; `Legs` : pieds plus sombres (#5C3A1E).
   - `Vise` : étau en acier (#5A5F66) sur un coin du plateau.
   - `Props` : quelques objets de serrurier posés dessus (une serrure en cours, une pince, une boîte
     de goupilles), fusionnés, laiton #C9A14A et acier ; rien au centre du plateau.
   - Repère `DisplayPoint` au centre du plateau, juste au-dessus (là où le jeu fait apparaître
     l'objet fabriqué).
4. **Retouche TOOL_Hammer** : écarter le bout du manche de la tête (scintillement), réexporter.

##### Lot 4a — Coffres (ambiance froide, accents dorés ; contrats de `CONTEXTE_PROJET.md`)
Remplacent les versions en pièces Roblox actuelles. Rien ne doit changer côté code : mêmes noms,
mêmes repères, même hauteur de serrure.
- Structure de chaque coffre : `Body` (corps, collision), Collection enfant `DoorAssembly` contenant
  `Door` et tout ce qui bouge avec la porte (volant, poignée, cadres, anneaux, pènes), repères
  `LockSocket` et `BeaconPoint`. Charnières visibles côté +X Blender (= -X Roblox, côté où pivote
  la porte dans le jeu). Rien de `DoorAssembly` ne dépasse au-delà du bord des charnières.
- Ajoute à chaque coffre une **cavité intérieure** derrière la porte (fond sombre #2A2A2A, pièce
  `Interior`, fixe) et un repère `GoldPoint` au sol de la cavité : quand la porte s'ouvre pendant
  un vol, on doit voir l'intérieur (le tas d'or y sera posé plus tard).
- Zone libre de 2,6 × 2,6 studs autour de `LockSocket` (aucune pièce de la porte n'y empiète).
- Coordonnées Blender :
  | Coffre | Encombrement (X × Y × Z) | Porte | LockSocket | BeaconPoint |
  |---|---|---|---|---|
  | VLT_Lvl1 | 5 × 5 × 5 | centre (0, -2.7, 2.5), 3.6 × 0.4 × 3.6 | (0, -2.9, 3.5) | (0, 0, 5.1) |
  | VLT_Lvl2 | 7.6 × 7.6 × 9 | centre (0, -3.8, 4.6), 5 × 0.6 × 6.6 | (0, -4.1, 3.5) | (0, 0, 9.0) |
  | VLT_Lvl3 | 12 × 8 × 13 | ronde Ø 9, centre (0, -4.5, 6.5), ép. 1 | (0, -5.25, 3.5) | (0, 0, 13.1) |
- **VLT_Lvl1** (premier de la famille, seul) : coffre trapu en bois #8B5A2B cerclé d'acier #5A5F66,
  coins renforcés #3B3F45, porte en tôle striée (DiamondPlate) avec levier et pommeau laiton.
- **VLT_Lvl2** : coffre-fort vert #2F4A3A sur socle #1F2E26, finitions et charnières laiton
  #C9A14A, porte encadrée de laiton, volant à poignées au-dessus de la zone de la serrure.
- **VLT_Lvl3** : chambre forte gris canon #3B3F45 (DiamondPlate), porte ronde massive à anneaux
  concentriques, grand volant à 5 branches et poignées jaunes, cercle de bandes de danger
  jaune #F2C12E / noir #1E1E1E autour de l'ouverture, gonds massifs. Doit impressionner.
- Progression : chaque niveau doit paraître nettement plus imposant et plus précieux que le précédent.

##### Lot 5 — Effets (section A5 du cahier)
- **FX_Shield_Dome** : demi-sphère Ø 10 × 5 (icosphère subdivisée, coupée à l'équateur, normales
  vers l'extérieur), ForceField #4FC3FF, sans collision. Le jeu la redimensionne selon le coffre.
- **FX_Shield_Ring** : anneau plat Ø 10 au sol, Neon #4FC3FF.
- **FX_AlarmBeacon** : `Base` (cylindre gris foncé Ø 1,2 × 0,4), `Dome` (demi-sphère Ø 1, Glass
  rouge #FF2A2A), `Reflector` (demi-cylindre miroir + ampoule, Neon rouge, origine sur l'axe vertical
  central : il tournera).
- **FX_GoldPile_S / M / L** (2 × 2 × 0,6 ; 3 × 3 × 1,2 ; 4 × 4 × 2) : monticule de pièces d'or
  #F2C12E (Metal) avec quelques lingots, généreux et appétissant (c'est la récompense filmée).
- **FX_Coin** : pièce Ø 0,6 × 0,1, 12 côtés, symbole en relief, #F2C12E.

##### Lot 6 — Environnement (section A1 du cahier)
- ENV_Plot_Base (32 × 32 × 1, bordure d'une autre couleur), ENV_Plot_VaultPad (14 × 14 × 0,4,
  rivets aux coins), ENV_Plot_Sign (`Frame` + `Board`, face avant plate pour le texte),
  ENV_Plot_Fence (module 8 × 0,4 × 2), ENV_SpawnPad (`Base` + `Ring` Neon), ENV_Zone_Sign (arche
  8 × 0,6 × 9 : `Frame` + `Board`), MIN_Rock_Deco_A/B/C (3, 5, 8 de diamètre, dans le style de la
  roche d'ORE_F1), MIN_Lantern_Post (`Post` + `Light` Neon jaune), ENV_Leaderboard (12 × 1 × 10 :
  `Frame` + `Screen`, écran plat à l'avant), ENV_LB_Topper_Crown et ENV_LB_Topper_Mask.
- Cohérence : même palette que les lots validés ; la mine reprend les tons de la roche d'ORE_F1.

##### Lot 4b — Serrures (si le temps le permet, après le lot 6)
- LCK_T1 (cadenas : `Tint` + anse acier), LCK_T2 (`Tint` plaque + barillet + vis), LCK_T3 (`Tint`
  plaque + cadran gradué + levier). Origine au centre de la face ARRIÈRE, avant vers -Y, pièce
  recolorée `Tint` en gris neutre #D0D0D0. Dimensions : T1 ≈ 1,4 × 0,6 × 1,2 (+ anse) ;
  T2 ≈ 1,8 × 0,3 × 2,2 ; T3 ≈ 2,4 × 0,3 × 2,4. Chaque niveau plus imposant et plus « high-tech ».

#### D. Planches de rendu
- [ ] Une planche par lot dans `renders/` (assets côte à côte + mannequin de 5 studs).
- [ ] En fin de session, une **planche globale** `renders/session3_global.png` réunissant TOUS les
  assets modélisés depuis le début (gisements, outils, forge, coffres, effets, environnement), pour
  vérifier la cohérence d'ensemble du style et des échelles.

#### E. Petites corrections de code (seule exception à « pas de test en jeu »)
- [x] Faire trembler les cristaux avec la roche à l'impact pour les gisements en mesh
  (`MiningController`, la secousse ne vise que `Rock`). Seulement si c'est rapide : modification
  chirurgicale, une courte partie de test pour vérifier la console, puis enregistrement du lieu.
  Sinon, reporter à la session d'intégration.
  → Fait : `shakeRock` (MiningController) fait trembler `Crystals` et `Crystals_Broken` avec `Rock` en mesh, derrière `Features.MeshOreShake` ; testé en jeu (retour exact en place), console sans erreur nouvelle, lieu enregistré sans publication.

#### F. Rapport de fin de session
- [ ] Ajoute une section **« Liste cumulée des FBX à importer »** : tous les FBX non encore importés
  (session précédente + celle-ci), regroupés par catégorie, dans l'ordre d'import conseillé, avec
  les réglages (Ancré coché, pivot à l'origine de la scène, modèle groupé, Créateur = Moi), et la
  consigne de les laisser dans le Workspace sans les renommer.
- [ ] Ajoute ces assets à la liste « À réimporter au nom du groupe » de `docs/SUIVI.md`.
- [ ] Termine par le plan de la session d'intégration (ordre de branchement et tests à faire ensemble).

### Session 2 du 2026-11-13
- [x] Je n'ai pas les droits du groupe : les imports se font pour l'instant avec Créateur = Moi.
  Tenir à jour dans docs/SUIVI.md une section « À réimporter au nom du groupe avant la sortie »
  listant chaque asset importé ainsi (en commençant par ORE_F1). Ne pas bloquer le travail pour ça.
  → Fait : section créée dans docs/SUIVI.md, ORE_F1 en première ligne ; consigne conservée pour les sessions suivantes.
  → RÉGLÉ (session 4, 2026-11-13) : l'utilisateur a les droits du groupe ; les imports se font au nom de WingedSword Empire.
- [x] Pas de clé API pour l'instant. Après le contrôle qualité, ne pas envoyer les FBX sur Roblox :
  lister dans le rapport les fichiers à importer à la main (Fichier > Importer, Créateur =
  WingedSword Empire, Ancré coché, pivot à l'origine de la scène). Au début de la session suivante,
  roblox-integrator récupère les modèles importés dans le Workspace et fait la suite (normalisation,
  manifest, aperçu, branchement).
  → Fait : aucun envoi ; 8 FBX à importer à la main listés dans docs/rapports/2026-11-13.md. Consigne conservée tant que la clé manque.
  → RÉGLÉ (session 4, 2026-11-13) : `ROBLOX_API_KEY` installée ; envoi automatique, plus d'import manuel.
