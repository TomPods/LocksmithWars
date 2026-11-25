# Lot 9 — « La rue des serruriers » : cahier des 3 variantes (phase 1, blockout)

Rédigé par le chef de projet le 2026-11-17 (session 7). Phase 1 = blockout gris, mesures, captures,
puis ARRÊT pour le choix de l'utilisateur. Rien ne remplace la carte actuelle pendant la phase 1.

## Repère et conventions communes
- Repère Roblox, sol à y = 0. La rue suit l'axe Z ; le « nord » (bout forge/apparition) est en -Z.
- Chaque variante est construite autour de son origine propre, loin de la carte actuelle :
  A = (1000, 0, 0), B = (1600, 0, 0), C = (2200, 0, 0) (B et C déplacés le 2026-11-18 à la demande
  de l'utilisateur : 600 studs d'écart). Toutes les coordonnées ci-dessous sont
  RELATIVES à cette origine.
- Dossiers : `Workspace.MapDraft_A`, `MapDraft_B`, `MapDraft_C` ; pièces grises ancrées
  (SmoothPlastic), quelques teintes de lecture autorisées (coffres gris foncé avec une face avant
  rouge, gisements communs gris clair, rares violets, forge orange terne, apparition bleu terne).
- Parcelle = 32 × 32 (taille de ENV_Plot_Base). Rangée ouest = Plot1 (nord) → Plot4 (sud) ; rangée
  est = Plot5 (nord) → Plot8 (sud) ; Plot1 fait face à Plot5, etc.
- Coffre de référence = encombrement de VLT_Lvl2 (7,6 × 9 × 7,6) posé sur une dalle 14 × 14 au bord
  de la parcelle côté rue, **porte tournée vers la rue** (+X pour la rangée ouest, -X pour l'est).
- 12 repères de gisements (`Spawns`) : 8 « communs » + 4 « rares » (les rares bien visibles).
- Falaises : murs de blockout de 30 à 40 de haut, légèrement irréguliers, qui ferment la carte
  derrière les parcelles et aux extrémités, avec une bande de circulation de 4 studs minimum (ou
  aucun vide) entre l'arrière des parcelles et la falaise : **aucun recoin** où l'on se coince.
- Aucun objet fonctionnel réel : seulement un `SpawnLocation` DÉSACTIVÉ par variante (`Draft_Spawn_X`,
  demande de l'utilisateur, apparition vérifiée sur la carte actuelle), pas de pas de `ProximityPrompt`, pas de nom
  `Plot1..8` en dehors des dossiers MapDraft (les étiquettes sont des BillboardGui de lecture).
- Vitesse de marche : 16 studs/s. Contrainte : toute parcelle à ≤ 15–20 s de la mine et de la forge.

## Variante A — « Grand-rue droite » (lisibilité maximale, relief plat)
- Rue large : bords intérieurs des parcelles à x = ±24 (48 de large).
- Parcelles : centres x = ±40, z = -54, -18, 18, 54 (espaces de 4 avec clôtures basses).
- Mine : bande centrale de 16 × 112 (z -56 → 56) légèrement creusée ou bordée de rochers bas ;
  communs sur deux lignes x = ±4 aux z = -50, -30, 30, 50 ; **rares au milieu** (z = -10 et 10,
  x = ±4) sur un petit monticule (+1). Deux allées de 16 de chaque côté, entre mine et coffres.
- Bout nord : place de 112 × 48 (z -76 → -124). Forge à l'ouest (enclume ≈ (-20, 0, -100)),
  apparition + 2 panneaux de classement à l'est (socle ≈ (20, 0, -96)), panneaux tournés vers le sud.
- Bout sud : falaise à z ≈ 80.
- Attendu : tout se voit depuis la mine ; trajets courts ; risque = rue un peu « couloir ».

## Variante B — « Place du marché » (point de rassemblement central)
- Rue de 40 (bords x = ±20). Parcelles : centres x = ±36, en deux groupes de 2 par côté :
  z = -86, -52 (nord) et 52, 86 (sud), autour d'une **place ronde centrale** de rayon 34 en z = 0.
- Mine dans la place : cuvette peu profonde (-1,5, rampes douces tout autour, aucune marche) ;
  8 communs en anneau (rayon 20), **4 rares au centre** sur un rocher-piédestal (+2), visibles de
  toutes les parcelles.
- Bout nord : forge **dans l'axe de la rue**, qui ferme la perspective (enclume ≈ (0, 0, -132),
  face au sud) ; place d'apparition juste devant (socle ≈ (0, 0, -112)) avec les panneaux de part
  et d'autre (x ≈ ±22).
- Bout sud : falaise à z ≈ 112.
- Attendu : carrefour très lisible, tous les coffres regardent la place ; risque = parcelles 4 et
  8 plus loin de la forge.

## Variante C — « Rue en terrasses » (relief, coffres en hauteur)
- Rue plus étroite : 36 (bords x = ±18) qui **monte doucement** du sud (y = 0) au nord (y = 6).
- Parcelles surélevées en terrasses (+3 au-dessus de la rue à leur hauteur), centres x = ±34,
  z = -54, -18, 18, 54 ; chaque parcelle a une **rampe large de 12** face à la rue (pente ≤ 20°,
  pas de marche) ; le coffre est au bord de la terrasse, bien visible de loin.
- Mine en **3 îlots rocheux** de 4 repères dans la rue, entre les paires de parcelles :
  z = -36 (communs), 0 (2 rares + 2 communs), 36 (communs) ; allées de chaque côté des îlots.
- Bout nord : apparition et panneaux sur une place basse (y = 6, z ≈ -90), adossés au mur d'une
  **terrasse de forge** (y = 10, z ≈ -110) accessible par un large escalier-rampe central.
- Bout sud : falaise à z ≈ 80.
- Attendu : carte la plus « vivante » ; risques = rampes (téléphone, coincement), plus de pièces.

## Mesures demandées (pour chaque variante)
- Temps de trajet = longueur du chemin (PathfindingService, rayon d'agent 2, hauteur 5) ÷ 16,
  validés pour au moins un trajet par variante en faisant réellement marcher un personnage :
  parcelle la plus éloignée → mine (repère le plus proche) et → forge (enclume) ; mine (centre) →
  chaque coffre (8 valeurs) ; apparition → forge.
- Visibilité : depuis le centre de la mine, combien de coffres sont visibles (rayons non bloqués).
- Coût : nombre de pièces, triangles estimés de la phase 2, point de vue le plus chargé.
- Captures : 1 plan vu du dessus annoté (étiquettes Plot1..8, Mine, Rares, Forge, Apparition,
  Classements, cotes principales) + 2 perspectives (depuis l'apparition vers la rue ; depuis la
  mine vers la parcelle la plus éloignée). Fichiers dans `renders/lot9/`.

## Adaptation du code prévue pour la phase 2 (ne pas faire en phase 1)
- Aujourd'hui les coffres se tournent vers (0, y, 0). Avec deux rangées, chaque parcelle portera
  une orientation explicite (attribut ou repère `VaultPoint` regardant la rue) lue par VaultService,
  derrière l'interrupteur `NewMap` ; à false, retour à l'ancienne disposition en cercle.
