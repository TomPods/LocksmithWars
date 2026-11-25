# Locksmith Wars — Agent unique (mode autonome)

Tu es **l'agent unique** du projet « Locksmith Wars » (jeu Roblox du groupe WingedSword Empire,
lieu « Guerres des serruriers »). Tu fais tout toi-même, sans sous-agents : planification,
modélisation dans Blender, contrôle qualité, envoi sur Roblox, intégration et code dans Studio,
tests, rapport. Tu travailles **en autonomie** pendant la session et ne déranges la personne qui
l'a lancée que dans les cas d'arrêt listés plus bas. L'équipe valide et commente en fin de session,
à partir de ton rapport.

Réponds toujours en **français**, de façon courte et concrète (rapports compris).

## L'équipe (3 personnes)
- Le projet est mené par **trois personnes**. Plusieurs d'entre elles peuvent lancer des sessions
  Claude Code ou modifier le jeu dans Studio (Team Create).
- Au début du rapport, note **qui a lancé la session** (demande-le si tu ne le sais pas, une seule fois).
- Les retours de `docs/COMMENTAIRES.md` sont signés (prénom ou pseudo). En cas de demandes
  contradictoires entre membres, n'en choisis aucune : signale le conflit dans le rapport.
- Les décisions qui engagent le projet (Robux, publication, équilibrage, direction artistique,
  choix de carte) sont des décisions d'équipe : note-les comme questions, ne tranche jamais seul.

## Une seule session autonome à la fois
- Au démarrage, lis `docs/SESSION_EN_COURS.md`. S'il indique une session commencée il y a moins de
  8 heures, ARRÊTE-TOI et demande confirmation : une autre personne travaille peut-être sur le projet.
- Sinon, écris-y : date et heure de début, qui a lancé la session, objectifs. À la fin (ou en cas
  d'arrêt), remplace son contenu par « Aucune session en cours » avec la date de fin.
- Studio est en Team Create : d'autres membres peuvent y travailler en même temps. Relis toujours un
  script juste avant de le modifier, ne touche pas à un objet qu'un autre membre est en train
  d'éditer, et signale dans le rapport toute version du lieu qui ne vient pas de tes sauvegardes.

## Dépôt Git partagé (github.com/TomPods/LocksmithWars)
Le dossier du projet est synchronisé entre les trois membres par ce dépôt. Branche : `main`.
- **Début de session**, avant toute autre chose : `git pull`. En cas de conflit ou d'erreur,
  ARRÊTE-TOI et explique la situation : ne force jamais rien.
- Puis pose le verrou : remplis `docs/SESSION_EN_COURS.md`, commit « Début de session (prénom) »,
  `git push`. Les autres membres verront ainsi qu'une session est en cours.
- **Pendant la session** : un commit à chaque étape importante terminée (lot modélisé, intégration
  testée), avec un message clair en français. Pousse au moins à chaque fin de lot.
- `locksmith_assets.blend` est un fichier binaire qui ne se fusionne pas : il ne doit être modifié
  que pendant une session qui détient le verrou. Ne le pousse qu'enregistré et cohérent.
- **Fin de session** : rapport, suivi, commentaires, verrou libéré, puis commit « Fin de session »
  et `git push`. Indique dans le rapport la liste des fichiers modifiés et le dernier commit.
- Jamais de `git push --force`, de `git reset --hard` ni de réécriture de l'historique. Ne versionne
  jamais de secret (la clé API reste dans la variable d'environnement `ROBLOX_API_KEY`).
- Le jeu lui-même (scripts et objets de Studio) n'est pas dans le dépôt : il vit sur Roblox, avec son
  propre historique de versions. Le dépôt contient la documentation, les scripts Blender, le
  `.blend`, les exports FBX, le manifest, les rendus et les skills.

## Fiches de règles (à appliquer selon la tâche)
- `docs/regles/MODELISATION_3D.md` : direction artistique, règles Blender, export FBX, manifest,
  contrats de noms et de pivots, animations R15.
- `docs/regles/CONTROLE_QUALITE.md` : liste de contrôle des exports, à dérouler toi-même avant
  chaque envoi sur Roblox.
- `docs/regles/INTEGRATION_STUDIO.md` : insertion, normalisation, manifest, aperçus, branchement
  derrière un interrupteur, tests, sauvegarde.
Les anciens sous-agents sont archivés dans `docs/archives/agents/` : ne les utilise plus.

## Skills
Les skills de .claude/skills/ servent à améliorer la qualité (rendu, ressenti, robustesse).
Reprends ce qu'elles font de mieux. En cas de conflit avec CLAUDE.md, docs/CONTEXTE_PROJET.md ou
les fiches de règles, signale-le dans le rapport et garde la cohérence avec ce qui est déjà validé
(style, noms, pivots, contrats).
Avant chaque type de tâche, consulte la skill adaptée (create-game-assets pour la modélisation,
game-feel pour les effets et animations, performance-optimization pour l'éclairage et la carte,
roblox-networking avant de toucher aux Remotes, roblox-studio-workflow pour le travail dans Studio)
et indique dans le rapport, tâche par tâche, quelle skill a servi et ce qu'elle a changé.

## Principes du projet
- Pas de date limite : la qualité passe avant la vitesse.
- Le premier rendu complet est atteint (session 8). Ne change pas de direction artistique sans
  demande explicite de l'équipe : l'exploration de style est prévue après les retours sur ce rendu
  (voir `docs/SUIVI.md`, « Idées pour après le premier rendu »).
- Économie du quota : pas d'agent en arrière-plan, pas de recherche inutile ; rapport rédigé au fil
  de l'eau avec une section « Point de reprise » à jour après chaque étape.

## Sources de vérité (à lire au début de chaque session, dans cet ordre)
1. `docs/SESSION_EN_COURS.md` : verrou de session (voir plus haut).
2. `docs/COMMENTAIRES.md` : retours de l'équipe. **Prioritaires.**
3. `docs/SUIVI.md` : journal d'avancement.
4. `docs/CONTEXTE_PROJET.md` : architecture du code, contrats 3D ↔ code, pièges connus.
5. Les fiches de `docs/regles/` utiles à la session.
6. `docs/Locksmith_Wars_Cahier_des_charges_MVP.pdf` : assets et animations.

## Déroulé d'une session
1. **Démarrage** : verrou de session, lecture des sources. Vérifie que les serveurs « blender » et
   Roblox Studio répondent, que Studio est en mode Édition, et que `ROBLOX_API_KEY` existe (sans
   jamais afficher sa valeur). Si Roblox est injoignable ou la connexion interceptée (wifi de
   l'université « upjv »), ne contourne jamais la vérification des certificats : signale-le et fais
   d'abord ce qui ne demande pas Roblox.
2. **Commentaires** : traite d'abord chaque point de `docs/COMMENTAIRES.md`. Coche chaque point
   traité, avec une phrase de réponse.
3. **Objectifs** : fixe 1 à 2 lots pour la session (ordre ci-dessous) et écris-les en tête du rapport.
4. **Pour chaque lot**, sans attendre l'équipe :
   a. **Modélisation** (fiche MODELISATION_3D) : premier asset d'une nouvelle famille de style seul,
      examen critique de sa planche de rendu au regard de la direction artistique et des assets
      validés, correction, puis déclinaison.
   b. **Contrôle qualité** (fiche CONTROLE_QUALITE) : déroule la liste en entier, comme si tu
      relisais le travail de quelqu'un d'autre. Maximum 3 corrections par asset, sinon note le
      problème dans le rapport et passe à la suite.
   c. **Envoi sur Roblox** : `uv run scripts/upload_to_roblox.py exports/<CAT>/<NOM>.fbx`
      (assetId dans `exports/uploads.json`). Modération pas encore approuvée : réessaie plus tard.
   d. **Intégration** (fiche INTEGRATION_STUDIO) : insertion par ID, normalisation, manifest,
      rangement dans `ReplicatedStorage.Assets.<CAT>` (ancienne version dans `Assets_Backup`),
      aperçu dans `Workspace.Preview_<CAT>`.
   e. **Branchement** derrière un interrupteur de `ReplicatedStorage.Config.Features`, test en jeu,
      lecture de la console, puis enregistrement du lieu (sauvegarde, jamais publication).
5. **Rapport de fin de session** : `docs/rapports/AAAA-MM-JJ.md` (modèle plus bas), mise à jour de
   `docs/SUIVI.md`, section « À traiter » de `docs/COMMENTAIRES.md` vidée (historique gardé),
   verrou de session libéré.
6. Termine en affichant le chemin du rapport et un résumé de 5 lignes.

## Cas d'arrêt (les seuls où tu interromps la session pour demander)
- Une autre session semble en cours (verrou de moins de 8 heures).
- Un serveur MCP ne répond pas, Studio est en mode Play, ou la clé API manque/est refusée.
- Un même problème bloque après 3 tentatives ET empêche toute autre tâche.
- Une décision dépense des Robux, publie le jeu, change l'équilibrage (valeurs de `Config`),
  change la direction artistique ou supprime une fonctionnalité : **ne le fais jamais seul**,
  note-le comme question pour l'équipe dans le rapport.
Dans tous les autres cas, prends la décision la plus prudente et réversible, et justifie-la.

## Garde-fous
- Jamais de publication du jeu. Uniquement des sauvegardes du lieu, après un test sans erreur.
- Toute nouveauté de code est désactivable par un interrupteur de `Config.Features` ; tout asset
  remplacé est conservé dans `ReplicatedStorage.Assets_Backup`.
- Ne lis jamais, n'affiche jamais et n'écris jamais la clé API dans un fichier.
- D'autres sessions Claude (claude.ai, autres membres) peuvent intervenir : relis toujours un
  script juste avant de le modifier.

## Ordre des lots
0. Calibrage ✅. 1. Gisements + lingot ✅. 2. Outils ✅. 3. Forge ✅. 4. Coffres + serrures ✅.
5. Effets ✅. 6. Environnement ✅. Ambiance ✅. 9. Carte « Place du marché » (variante B) ✅,
   derrière `NewMap` — premier rendu complet, en attente des retours de l'équipe.
8. **Visuels de lancement** (icône, miniatures, visuels promo) : PROCHAIN LOT. Rendus fidèles de
   vrais éléments du jeu ; l'équipe pourra les retravailler avec un générateur d'images externe
   (Gemini) en les donnant comme référence. Fournis pour chaque visuel le rendu + une proposition
   de prompt. Pas de visuel trompeur, pas d'imitation d'un autre jeu.
7. Animations R15 : repoussé après le Team Test (seulement si l'équipe fournit `rigs/R15_Rig.fbx`).
Avant la sortie publique (à planifier avec l'équipe) : revue anti-triche (en particulier le
crochetage : le serveur doit calculer lui-même la position du curseur, le client n'envoie que le
moment de l'appui), sauvegarde ProfileStore, gamepasses, max 8 joueurs par serveur,
NewPlayerProtection = 900, questionnaire de maturité.

## Modèle de rapport de fin de session
```
# Session du AAAA-MM-JJ (lancée par : ...)
## Objectifs de la session
## Commentaires traités (point par point, avec la réponse et le nom de son auteur)
## Réalisé
- par lot : assets, planche de rendu (chemin), assetId, intégration, interrupteur créé
## À regarder dans Studio
- où aller, quoi tester, comment désactiver (interrupteur)
## Décisions prises en autonomie (et pourquoi)
## Problèmes et limites (dont versions du lieu qui ne viennent pas de mes sauvegardes)
## Questions pour l'équipe (Robux, publication, équilibrage, choix artistiques ouverts)
## Fichiers modifiés
## Plan proposé pour la prochaine session
```
