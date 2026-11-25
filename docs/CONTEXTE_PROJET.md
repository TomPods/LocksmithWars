# Locksmith Wars — Contexte du projet (pour Claude Code)

Document de passation rédigé depuis la session claude.ai qui a écrit le code du jeu.
À tenir à jour par le chef de projet quand l'architecture ou les contrats changent.

## Le projet
- Jeu Roblox « Locksmith Wars », lieu « Guerres des serruriers », appartenant au groupe
  **WingedSword Empire**. Duo : l'utilisateur (scripting, débutant sur Studio) et un ami (3D).
- Boucle : miner des gisements (8 métaux, 4 raretés) → forger serrures/crochets à l'enclume
  (mini-jeu de timing) → protéger son coffre → crocheter le coffre des autres (mini-jeu, alarme
  chez le propriétaire, qui peut revenir attraper le voleur).
- Objectif : sortie publique vers mi-décembre 2026. Croissance 100 % organique (TikTok/Shorts).
- Les gameplay et code sont terminés et testés ; le chantier en cours est l'habillage 3D.

## Calibrage Blender → Roblox (validé)
- 1 unité Blender = 1 stud ; pas de rotation de 180° nécessaire, l'avant arrive en -Z Roblox.
- Blender X → Roblox -X, Blender Y → Roblox Z, Blender Z → Roblox Y (rotation propre).
- L'importeur Roblox enregistre un pivot interne tourné de 90° : chaque import doit être normalisé
  (procédure dans `docs/regles/INTEGRATION_STUDIO.md`).
- Import automatisé : `scripts/upload_to_roblox.py` envoie chaque FBX sur Roblox (Assets API d'Open
  Cloud, propriétaire = groupe 33016933) et note l'assetId dans `exports/uploads.json` ;
  l'agent insère ensuite l'asset dans Studio par son ID, puis le normalise.
- Import manuel (secours) : Fichier > Importer, Créateur = WingedSword Empire (jamais « Moi »),
  Ancré coché, pivot à l'origine de la scène.
- Interrupteurs : `ReplicatedStorage.Config.Features` permet de désactiver chaque nouveauté ;
  les anciennes versions d'assets sont gardées dans `ReplicatedStorage.Assets_Backup`.

## Architecture du code (Roblox Studio)
### ReplicatedStorage
- `Config/` : `Metals` (8 métaux : Name, Rarity, Family F1–F4, Weight, Multiplier, Color),
  `Locks` (T1–T3), `Picks` (T1–T3), `Vault` (niveaux, règles de vol, protections),
  `Monetization` (gamepasses/produits, Id = 0 tant que non créés).
- `Remotes/` : MineOre, MineHit, EquipLock, EquipPick, RecycleItem, StartHeist, SubmitPin,
  CancelHeist, GoldUpdated, Alarm, HeistResult, DataSync, OpenForge, UpgradeVault (RemoteEvents),
  Forge (RemoteFunction).
- `Assets/` : un dossier par catégorie (ENV, FRG, MIN, ORE, ING, VLT, LCK, PCK, TOOL, FX).
### ServerScriptService
- `Main` démarre dans l'ordre : DataService, MonetizationService, VaultService, MiningService,
  ForgeService, HeistService, LeaderboardService, DevTestService.
- `DataService` (sauvegarde DataStore simple, à remplacer par ProfileStore avant la sortie),
  `VaultService` (parcelles, coffres, or, amélioration, serrure visible, bouclier, alarme),
  `MiningService` (gisements, coups de pioche validés serveur), `ForgeService` (fabrication,
  équipement, recyclage), `HeistService` (sessions de crochetage validées serveur),
  `MonetizationService`, `LeaderboardService` (panneaux du hub), `DevTestService` (coffre du
  « Mannequin », Studio uniquement, pour tester le crochetage seul).
### StarterPlayerScripts
- `ClientMain` démarre : TweenFX (interface partagée, sons, particules, porte du coffre),
  CharacterAnim (animations du personnage EN CODE), HUDController, MiningController (pioche),
  ForgeUIController (forge + marteau + lingot locaux), LockpickController, AlarmController,
  ObjectiveController (tutoriel), ShopController.
### StarterPack
- Tool `Pioche` : pièces `Handle` (manche 0.3×0.3×3.6), `Head`, `Tip` ; `Tool.Grip = CFrame.new(0,0,1.2)`.
### Workspace
- `Plots` (8 parcelles en cercle, rayon 110), `Mine` (Spawns 12 repères + Nodes générés),
  `Forge` (Floor, **Anvil** avec ForgePrompt, Furnace, FurnaceGlow, Workbench), `Vaults` (générés),
  `Leaderboards` (Gold, Steals), `Preview_ORE` (aperçus à supprimer après validation).

## Pièges connus
- Les personnages utilisent des AnimationConstraint : `Motor6D.C0` est en lecture seule. Les
  animations par code passent par `joint.Transform` dans `RunService.PreSimulation` (CharacterAnim).
- Pour souder des pièces créées par script au personnage, utiliser `Weld` avec C0/C1 explicites,
  pas `WeldConstraint` (les décalages se calculent mal à l'activation).
- Les animations R15 importées devront être publiées sous le groupe, sinon elles ne se chargent pas.

## Contrats entre 3D et code, et plan de branchement
### Gisements (ORE) — ✅ ORE_F1 importé, normalisé, dans `Assets.ORE`
- ✅ Branchement fait le 2026-11-13 derrière `Config.Features.MeshOres` (chemins réels :
  `ServerScriptService.Services.MiningService`, `StarterPlayerScripts.Controllers.MiningController`).
  Les pièces du clone deviennent des enfants directs du gisement ; attributs `Mesh` et `MeshOrigin`.
  F2–F4 et `ORE_Rubble` sont pris en charge dès qu'ils existent dans `Assets.ORE` ; sinon repli en pièces.
  Reste à brancher : `ORE_Chunk` (éclat au coup de pioche). `Core`/`Shards` : origine à (0, 4.5, 0) Roblox.
- Modèle `ORE_F<n>` : `Rock` (fixe, Slate #6E6A66), `Crystals`, `Crystals_Broken` (recolorés selon
  le métal), F4 en plus : `Core` (cristal flottant), `Shards` (anneau). Origine = base centrée.
  `ORE_Rubble` (débris), `ORE_Chunk` (éclat Ø 0,8).
- Branchement (MiningService) : aujourd'hui `createNode` fabrique un bloc `Rock` + une pièce
  `Crystal`, et `placeCrystal` réduit le cristal selon les PV. À remplacer par : cloner
  `Assets.ORE.ORE_F<famille du métal>` (re-cloner si la famille change à la réapparition), recolorer
  `Crystals`/`Crystals_Broken` (matériau : F1–F2 Metal, F3 Glass, F4 Neon), afficher
  `Crystals_Broken` à la place de `Crystals` sous 50 % de PV, tout masquer et montrer `ORE_Rubble`
  à 0 PV. GARDER une pièce nommée `Rock` (le panneau d'info, `MineHit` et le client l'utilisent).
  Côté client (TweenFX ou MiningController) : `Core` flotte (±0,3 stud, 2 s) et `Shards` tourne (4 s/tour).
### Lingot (ING)
- `ING_Bar` 2×1×0,6, origine base centrée, recoloré. Branchement : `ForgeUIController.spawnIngot`
  crée aujourd'hui une pièce locale ; la remplacer par un clone posé sur le haut de l'enclume.
### Outils (TOOL)
- `TOOL_Pickaxe` : `Handle` (manche, origine au centre) + `Head` à l'avant. Remplacer les pièces du
  Tool `Pioche` en gardant le nom `Handle`, souder `Head` ; ajuster `Tool.Grip` pour que la tête soit
  devant le personnage (référence actuelle : tête ≈ 4,9 studs devant le torse en pose de repos).
- `TOOL_Hammer` : `Handle` + `Head`. Remplacer les pièces créées par `ForgeUIController.attachHammer`
  (soudure : `Weld`, C0 = RightGripAttachment.CFrame, C1 = CFrame.new(0, 0, 0.8) à ajuster).
### Forge (FRG)
- `FRG_Anvil` (repère `IngotPoint`), `FRG_Furnace` (`Body` + `Glow` Neon orange), `FRG_Workbench`
  (repère `DisplayPoint`). Branchement : remplacer la géométrie de `Workspace.Forge` en GARDANT une
  pièce nommée `Anvil` (même invisible) avec le `ForgePrompt`, car ForgeService et ForgeUI l'utilisent.
### Coffres (VLT) — déjà en place en pièces Roblox dans `Assets.VLT`
- `Body`, `DoorAssembly` (contient `Door` et tout ce qui bouge avec la porte), repères `LockSocket`
  et `BeaconPoint`. VaultService clone `Assets.VLT.VLT_Lvl<n>` ; la porte pivote autour du bord -X
  (Roblox) de `DoorAssembly`. La serrure est toujours à 3,5 studs du sol ; zone libre de 2,6 × 2,6
  studs autour de `LockSocket`. Coordonnées des repères (repère Roblox, base au sol, avant -Z) :
  Lvl1 LockSocket (0, 3.5, -2.9), BeaconPoint (0, 5.1, 0) ; Lvl2 (0, 3.5, -4.1) / (0, 9.0, 0) ;
  Lvl3 (0, 3.5, -5.25) / (0, 13.1, 0). Remplacer un modèle = même nom dans `Assets.VLT`, rien d'autre.
### Serrures (LCK) — déjà en place en pièces Roblox dans `Assets.LCK`
- Pivot au centre de la face arrière, avant -Z, pièce recolorée nommée `Tint`. Clonées par
  VaultService sur `LockSocket`, dans `DoorAssembly`.
### Effets (FX)
- Aujourd'hui créés en pièces par VaultService (`Shield` boule ForceField, `Beacon` bloc). Les
  versions 3D (FX_Shield_Dome, FX_AlarmBeacon_*, FX_GoldPile_S/M/L, FX_Coin) se brancheront en
  gardant les noms `Shield` et `Beacon` utilisés par le code.

## État des branchements au 2026-11-16 (version 35 du lieu) — fait foi sur les sections ci-dessus
### Interrupteurs (`ReplicatedStorage.Config.Features`, tous à true)
- `MeshOres` (MiningService, MiningController : gisements, débris, `animateOres` pour Core/Shards,
  `meshChunks` pour les éclats ORE_Chunk), `MeshOreShake` (MiningController).
- `MeshTools` (pioche mesh du StarterPack, `Grip = CFrame.new(0, 0, 1.06)` ; marteau dans
  `ForgeUIController.attachHammer`, C1 = CFrame.new(0, 0, 0.64)), `MeshIngot` (`spawnIngot`).
- `MeshForge` (modèles de `Workspace.Forge`, `ForgeUIController.anvilTop` lit `IngotPoint`).
- `MeshVaults` (`VaultService.makeVaultModel` ; à false, coffres en pièces de `Assets_Backup.VLT`).
- `MeshFX` (VaultService : `meshShield`, `meshBeacon`, `updateGoldPile` ; TweenFX : `coinBurst`,
  rotation du réflecteur).
- `MeshLocks` (2026-11-17, `VaultService.lockAsset` appelé par `updateLockVisual` ; à false, serrures
  en pièces de `Assets_Backup.LCK.LCK_T<n>_2026-11-17`). Serrures mesh : `PrimaryPart = Tint`, pièces
  T1 Keyhole/Shackle/Tint, T2 Cylinder/Keyway/Tint/Trim, T3 Bezel/Dial/Index/Lever/Tint.
- `Ambiance` (2026-11-17) : Lighting réglé dans le lieu (sauvegarde exacte dans
  `Assets_Backup.Lighting_2026-11-17`) ; objets ajoutés étiquetés `Ambiance` (`Workspace.Ambiance.*`,
  braises dans `FRG_Furnace.Glow`, scintillement dans `Assets.ORE.ORE_F4.Core`) ; objets existants
  modifiés étiquetés `AmbianceModified` avec `Legacy*` ; vacillation côté client par
  `StarterPlayerScripts.AmbianceFlicker` (étiquette `AmbianceFlicker`, attribut `FlickerAmount`).
  À false, `FeaturesApply.applyAmbiance` restaure tout au lancement (en jeu seulement).
  ⚠️ Dans la version actuelle de Studio, la propriété `Lighting.Technology` N'EXISTE PLUS : elle est
  remplacée par `Lighting.LightingStyle` (`Realistic` ≈ ancien Future, ombres nettes et lumières
  locales qui projettent des ombres ; `Soft` = rendu plus doux) et `Lighting.PrioritizeLightingQuality`
  (laisser coché). Le style a été réglé à la main par l'utilisateur le 2026-11-17 : lis sa valeur
  actuelle avant d'ajuster l'ambiance, et ne demande plus de « passer Technology en Future ».
- Session 7 (2026-11-17/18) : le repli `Ambiance` ignore `LightingStyle` et
  `PrioritizeLightingQuality` (table `AMBIANCE_USER_PROPS` de `FeaturesApply`) : ce sont des réglages
  manuels de l'utilisateur (actuellement `Realistic`, true). `ShadowSoftness` 0,35 et
  `EnvironmentDiffuseScale` 0,75 (valeurs d'origine dans la sauvegarde). Ciel **SKY_Warm** : le
  `Lighting.Sky` porte l'étiquette `Ambiance`, ses anciennes valeurs en `Legacy*`, StarCount 0 ; le
  repli remet le Sky d'origine depuis `Assets_Backup.Lighting_2026-11-17`. ⚠️ Dans Roblox,
  `SkyboxLf` regarde +X et `SkyboxRt` -X (inverse de la croix habituelle) ; une image envoyée en
  Decal a un ID d'image distinct (InsertService:LoadAsset(decalId) → Decal.Texture).
- `scripts/upload_to_roblox.py --type Decal` envoie un PNG en Decal au nom du groupe
  (`uploads.json` : `assetType`, `imageId`).
- Lot 9 phase 1 : blockouts `Workspace.MapDraft_A` et `MapDraft_C` (x = 1000 / 2200) gardés tant
  que l'utilisateur n'a pas validé le premier rendu (`MapDraft_B` retiré en session 8).
  Plans et mesures dans `renders/lot9/`, script `scripts/lot9_plan.py`.
### Carte (lot 9 phase 2, session 8, version 73) — interrupteur `Features.NewMap`
- Nouvelle carte « Place du marché » dans `Workspace.NewMap`, origine (-1800, 0, 0) ; ancienne carte
  dans `Workspace.LegacyMap` (avec son `Ambiance`). Le Terrain des deux cartes reste en place (pas de
  superposition).
- `ServerScriptService.MapSwitch` (ModuleScript, `Apply()` idempotent) est appelé en tête de `Main`
  et de `FeaturesApply` : il sort `Plots`, `Mine`, `Forge`, `Leaderboards`, `SpawnLocation` de la
  carte active vers `Workspace` (attribut `MapSource`), range l'autre carte dans
  `ServerStorage.MapStorage`, pose `Workspace.ActiveMap`. Les sections ci-dessous sur
  `Workspace.Forge` décrivent l'ancienne carte ; sur NewMap, la forge est en alcôve est (enclume à
  (45, 0, 0) relatif).
- Chaque parcelle de NewMap contient un Attachment `VaultPoint` (au bord côté rue, orienté vers la
  rue, attribut `FacingX` = ±1) : `VaultService.buildVault` pose le coffre dessus, porte (-Z) vers sa
  direction ; sans `VaultPoint`, comportement d'origine (porte vers (0, y, 0)).
- Repères `Mine.Spawns` : attribut `Zone` = `Commun` (Spawn1..8, anneau) ou `Centre` (Spawn9..12,
  piédestal) — non utilisé par le code (le métal reste tiré par `rollMetal`).
- Décor `NewMap.Decor` (lanternes, rochers, arches FORGE / MINE, fumée) hors étiquette `Ambiance` ;
  `NewMap.Ambiance` étiqueté. ENV_Cliff_Corner de la carte : collision par murs invisibles `Collision`.
- `ServerStorage.MapBackup.Terrain_NewMap_avant_decalage_2026-11-24` : Terrain avant l'abaissement.
- Les dossiers `Preview_*` ont été supprimés (session 8) : les assets sont dans `ReplicatedStorage.Assets`.
- `ServerScriptService.FeaturesApply` applique au démarrage les replis qui touchent des objets du
  lieu : ancienne pioche (`Assets_Backup.TOOL.Pioche_2026-11-13`) si `MeshTools = false` ; retrait des
  modèles de forge et réaffichage des anciens blocs si `MeshForge = false`.
### `Workspace.Forge` (dessus de `Floor` à y = 0,2)
- `FRG_Anvil` pivot (0, 0.2, 30), `IngotPoint` monde (0, 3.2, 30) ; `FRG_Furnace` pivot (9, 0.2, 38),
  bouche tournée vers l'enclume ; `FRG_Workbench` pivot (-9, 0.2, 36), `DisplayPoint` monde (-9, 3.7, 36).
- Anciens blocs `Anvil` (avec `ForgePrompt`), `Furnace`, `FurnaceGlow`, `Workbench` : gardés à leur
  place, invisibles, sans collision ; état d'origine dans des attributs `Legacy<Propriété>`.
  Les modèles mesh portent l'attribut `MeshForge = true`.
### Coffres et effets
- Coffre mesh : attribut `MeshVault = true`, pivot à la base, pivot de `DoorAssembly` sur l'axe des
  gonds (`TweenFX.animateDoor` s'en sert), repère `GoldPoint`, pièce `Interior`.
- Dans un coffre posé : `Shield` (dôme mesh, étiré selon la boîte englobante du coffre),
  `ShieldRing`, `Beacon` (socle du gyrophare, attribut `MeshFX`, enfants `Dome` / `Reflector` /
  `InfoGui`), `GoldPile` (Model, attribut `Asset`).
- Tas d'or : `FX_GoldPile_S/M/L` choisis par remplissage (tiers de la capacité, constantes locales de
  VaultService, pas dans `Config`), avec repli sur la taille présente dans `Assets.FX` et qui tient
  dans `Interior`.
- `Assets_Backup` : `ORE/ORE_F1_2026-11-13`, `TOOL/Pioche_2026-11-13`, `VLT/VLT_Lvl1..3_2026-11-15`,
  `LCK/LCK_T1..3_2026-11-17`, `Lighting_2026-11-17`.
- `ENV_Leaderboard.Screen` est solide (CanCollide true, session 7).
- `Assets.FX` contient FX_GoldPile_S/M/L ; `Assets.MIN` et `Assets.ENV` remplis (aperçus
  `Preview_MIN` ≈ (35, 0, -58), `Preview_ENV` ≈ (54, 0, 30) ; carte non modifiée). Aperçus aussi dans
  `Preview_LCK` (x ≈ 76).
- Les assets insérés par ID arrivent en package (`PackageLink` à retirer), tournés de 90° et non ancrés.
- Le lieu est en Team Create : un autre éditeur peut être connecté (vu le 2026-11-17).
- Défaut connu : les anciens coffres en pièces (pivot au centre de `Body`) sont à moitié enterrés.
### Piège de test
- Les modules ne sont pas partagés avec la console de commande : piloter les tests par entrées
  simulées et Remotes. L'identifiant de l'instance Studio change à chaque redémarrage.

## Consignes en vigueur de l'utilisateur (tant qu'il ne dit pas le contraire)
- Clé API installée (`ROBLOX_API_KEY`) et droits du groupe acquis : envoi automatique au nom du
  groupe, plus d'import manuel ni de liste « à réimporter ».
- Tout ce qui est modélisé est validé par défaut tant que l'utilisateur n'a pas fait ses retours.
- Animations R15 (lot 7) : repoussé après le Team Test.
