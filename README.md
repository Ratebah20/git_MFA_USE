# Guide d'utilisation du Simulateur SelfCare pour test OTP

Ce simulateur a été créé pour tester le flux complet de redirection OTP sans avoir à se soucier du reCAPTCHA et d'autres contraintes de l'environnement de production.

## Introduction

Le système OTP (One-Time Password) permet une redirection sécurisée des utilisateurs après validation MFA vers l'application SelfCare. Ce simulateur vous permet de tester ce flux de différentes manières.

## Contenu du simulateur

Le simulateur est composé d'une seule page HTML qui offre trois modes de test différents :

1. **Test manuel** : Testez directement la résolution d'un OTP spécifique
2. **Test flux complet** : Simulez le flux entier depuis la connexion jusqu'à la redirection
3. **Résoudre OTP** : Simulez la partie SelfCare qui résout un OTP reçu par redirection

## Comment utiliser le simulateur

### Mode 1 : Test manuel d'un OTP

Ce mode vous permet de tester directement la résolution d'un OTP existant :

1. Entrez un OTP valide dans le champ prévu
2. Cliquez sur "Vérifier l'OTP"
3. Le résultat de la validation s'affichera en dessous

### Mode 2 : Test du flux complet

Ce mode simule l'ensemble du flux depuis la connexion :

1. Entrez un nom d'utilisateur et mot de passe (simulés)
2. Choisissez une méthode MFA et entrez un code
3. Après validation, un OTP simulé sera généré
4. Utilisez le bouton "Rediriger vers SelfCare" pour tester la redirection

### Mode 3 : Résolution d'OTP (SelfCare)

Ce mode simule le comportement de SelfCare lorsqu'il reçoit un OTP par redirection :

1. Ce mode s'active automatiquement si vous arrivez sur la page avec un paramètre `otp_token` dans l'URL
2. L'OTP reçu est affiché
3. Cliquez sur "Valider l'OTP" pour simuler la résolution
4. Les informations d'authentification simulées s'afficheront

## Différences avec le système réel

Ce simulateur diffère du système réel sur ces points :

1. Il ne communique pas réellement avec le serveur pour les étapes d'authentification et MFA
2. Il génère des OTP simulés plutôt que d'utiliser l'API réelle
3. Il simule la résolution d'OTP sans appeler réellement le endpoint `/resolve-otp`

## Options de test avancées

Pour tester avec le système réel tout en évitant les problèmes de reCAPTCHA, vous pouvez :

1. Modifier le simulateur pour utiliser votre serveur local (changer `API_BASE_URL` dans le JavaScript)
2. Activer seulement certaines parties du flux (par exemple, uniquement la résolution OTP)
3. Créer manuellement des OTP dans la base de données pour les tester avec ce simulateur

## Problèmes connus

Le serveur d'authentification actuel nécessite un token reCAPTCHA, ce qui rend difficile l'automatisation des tests. Ce simulateur contourne cette limitation en simulant la partie authentification/MFA.

## Pour aller plus loin

Si vous souhaitez améliorer le simulateur :

1. Implémentez une communication réelle avec le backend pour la résolution d'OTP
2. Ajoutez la gestion des erreurs pour simuler des cas d'échec (OTP expiré, déjà utilisé, etc.)
3. Intégrez un mode de débogage pour afficher les requêtes/réponses complètes
