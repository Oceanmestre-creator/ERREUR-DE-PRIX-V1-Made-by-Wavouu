# Alertes erreurs de prix → Discord

Surveille les nouveaux deals Dealabs toutes les 10 minutes et t'envoie une alerte Discord pour :
- **tous les deals à -70 % ou plus**, toutes catégories (la tech est mise en avant) ;
- tout deal où quelqu'un parle d'**erreur de prix**.

100 % gratuit : tourne sur GitHub Actions, rien à laisser allumé.

## L'appli

Une appli web (dossier `docs/`) affiche les alertes et les 300 derniers deals, avec des filtres (erreurs, tech, -50/-70/-90 %, catégories).
Elle est publiée par GitHub Pages : https://oceanmestre-creator.github.io/ERREUR-DE-PRIX-V1-Made-by-Wavouu/

Pour l'installer sur ton téléphone :
- **iPhone** : ouvre le lien dans Safari → Partager → « Sur l'écran d'accueil » ;
- **Android** : ouvre le lien dans Chrome → menu ⋮ → « Installer l'application ».

Les notifications instantanées restent celles de Discord. L'appli affiche un badge et une alerte quand de nouveaux deals sont arrivés depuis ta dernière visite.

## Installation (faisable depuis le téléphone, sur github.com)

1. **Crée un dépôt public** : github.com → « + » → New repository → nom `alertes-erreurs-de-prix` → **Public** → Create.
2. **Envoie les fichiers** : « Add file » → « Upload files » → glisse le contenu du zip (`alerte.py`, `README.md` et le dossier `.github`). 
   Si le dossier `.github` ne passe pas depuis le téléphone : « Add file » → « Create new file », nomme-le `.github/workflows/alertes.yml` et colle le contenu du fichier.
3. **Ajoute le webhook en secret** : Settings → Secrets and variables → Actions → New repository secret 
   - Name : `DISCORD_WEBHOOK` 
   - Secret : l'URL de ton webhook Discord
4. **Lance un premier test** : onglet Actions → « Alertes erreurs de prix » → Run workflow. 
   Le 1er passage mémorise les deals existants sans alerter (pour ne pas te spammer). Ensuite, seuls les nouveaux deals déclenchent des alertes.

## Réglages

En haut de `alerte.py` :
- `REDUCTION_MIN` : seuil de réduction (70 par défaut) ;
- `TOUTES_CATEGORIES` : `False` pour revenir à la tech seule ;
- `MOTS_TECH` : mots-clés à surveiller ;
- `MOTS_ERREUR` : mots qui déclenchent une alerte même sans pourcentage.

## Limites

- Les erreurs de prix partent vite : une vérification toutes les 10 min peut arriver après la bataille.
- La réduction est détectée dans le texte du deal (« -75 % », « au lieu de 999 € »…). Si l'auteur ne l'indique pas, le deal n'est alerté que s'il parle d'erreur.
- Un vendeur peut annuler une commande passée à un prix manifestement dérisoire.
