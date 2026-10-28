# Alertes erreurs de prix → Discord

Surveille les nouveaux deals Dealabs toutes les 10 minutes et t'envoie une alerte Discord pour :
- la **tech** (téléphones, ordinateurs, cartes graphiques…) à **-70 % ou plus** ;
- tout deal tech où quelqu'un parle d'**erreur de prix**.

100 % gratuit : tourne sur GitHub Actions, rien à laisser allumé.

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
- `MOTS_TECH` : mots-clés à surveiller ;
- `MOTS_ERREUR` : mots qui déclenchent une alerte même sans pourcentage.

## Limites

- Les erreurs de prix partent vite : une vérification toutes les 10 min peut arriver après la bataille.
- La réduction est détectée dans le texte du deal (« -75 % », « au lieu de 999 € »…). Si l'auteur ne l'indique pas, le deal n'est alerté que s'il parle d'erreur.
- Un vendeur peut annuler une commande passée à un prix manifestement dérisoire.
