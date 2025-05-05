from flask import Flask, render_template, request, redirect, url_for, jsonify, session, make_response
import os
import secrets
import requests
import json
import re
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration de base
MFA_URL = "https://acc.portail.orange.lu"  # URL réelle du portail MFA
SELFCARE_SIMULATED_URL = "http://localhost:5000/selfcare"  # Notre simulateur SelfCare

# Désactiver la vérification SSL pour les environnements de développement
VERIFY_SSL = False

# Routes principales
@app.route('/')
def index():
    """Page d'accueil du simulateur SelfCare"""
    return render_template('index.html')

@app.route('/selfcare')
def selfcare():
    """Page principale du simulateur SelfCare"""
    # Récupérer l'OTP s'il est présent dans l'URL - essayer plusieurs formats possibles
    otp = request.args.get('otp_token') or request.args.get('otp') or ''
    
    # Journaliser les paramètres reçus pour le débogage
    app.logger.info(f"Reçu sur /selfcare avec params: {dict(request.args)}")
    
    # Si nous avons un OTP, tout va bien, sinon afficher un message d'erreur
    return render_template('selfcare.html', otp=otp, full_url=request.url, all_params=dict(request.args))

@app.route('/selfcare/login')
def selfcare_login():
    """Page de login de SelfCare qui redirige vers le MFA réel"""
    # URL de redirection vers notre simulateur après authentification MFA
    # S'assurer que l'URL est correctement encodée pour éviter les problèmes
    from urllib.parse import quote
    base_url = request.url_root.rstrip('/')
    redirect_uri = f"{base_url}/selfcare"
    
    app.logger.info(f"URL de redirection configurée: {redirect_uri}")
    
    # Construction de l'URL de redirection vers le MFA réel avec URL encodée
    auth_url = f"{MFA_URL}/login?redirect_uri={quote(redirect_uri)}"
    
    return render_template('selfcare_login.html', auth_url=auth_url, encoded_redirect=quote(redirect_uri))

@app.route('/resolve-otp', methods=['POST'])
def resolve_otp():
    """Endpoint pour résoudre un OTP en appelant l'API réelle"""
    data = request.get_json()
    otp_token = data.get('otp_token')
    
    if not otp_token:
        return jsonify({"success": False, "message": "OTP manquant"}), 400
    
    app.logger.info(f"Tentative de résolution de l'OTP: {otp_token}")
    
    try:
        # Nous devons d'abord obtenir un token CSRF valide du serveur MFA
        app.logger.info("Récupération d'un token CSRF depuis le serveur MFA...")
        
        # On crée une session pour conserver les cookies entre les requêtes
        session_req = requests.Session()
        session_req.verify = VERIFY_SSL
        
        # Configuration pour maintenir les cookies et suivre les redirections
        session_req.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SelfCareSimulator/1.0"
        })
        # Désactiver l'escape automatique des redirections pour garder les cookies
        session_req.max_redirects = 5
        
        # Appel à la page d'accueil pour récupérer un token CSRF
        try:
            # On récupère la page d'accueil pour obtenir un token CSRF
            home_resp = session_req.get(f"{MFA_URL}/")
            app.logger.info(f"Status réponse page d'accueil: {home_resp.status_code}")
            
            # Extraction du token CSRF depuis la balise meta
            html_content = home_resp.text
            csrf_token = None
            csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', html_content)
            
            if csrf_match:
                csrf_token = csrf_match.group(1)
                app.logger.info(f"Token CSRF récupéré: {csrf_token[:10]}...")
            else:
                app.logger.warning("Impossible de trouver le token CSRF dans la page HTML")
            
            # Maintenant, on peut faire l'appel au endpoint resolve-otp avec le token CSRF
            resolve_url = f"{MFA_URL}/resolve-otp"
            app.logger.info(f"Appel à l'API avec CSRF: {resolve_url}")
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Referer": f"{MFA_URL}/"
            }
            
            # Ajouter le token CSRF dans l'en-tête attendu par Flask-WTF
            if csrf_token:
                # Flask-WTF attend par défaut le token dans cet en-tête
                headers["X-CSRFToken"] = csrf_token
            
            # Création du payload incluant le token CSRF si disponible
            payload = {"otp_token": otp_token}
            if csrf_token:
                payload["csrf_token"] = csrf_token
            
            app.logger.info(f"Payload envoyé: {payload}")
            
            # Appel à l'API réelle pour résoudre l'OTP
            response = session_req.post(
                resolve_url,
                headers=headers,
                json=payload
            )
            
            # Détails de la réponse pour le débogage
            app.logger.info(f"Réponse du serveur: Status {response.status_code}")
            app.logger.info(f"Headers: {response.headers}")
            
            # Essayer de récupérer la réponse JSON
            try:
                api_response = response.json()
                app.logger.info(f"Contenu de la réponse: {api_response}")
            except ValueError as json_err:
                app.logger.error(f"Erreur lors de la conversion de la réponse en JSON: {str(json_err)}")
                app.logger.error(f"Contenu brut: {response.text[:500]}")
                return jsonify({
                    "success": False,
                    "message": f"La réponse du serveur n'est pas au format JSON valide",
                    "status_code": response.status_code,
                    "raw_content": response.text[:200]  # Tronquer pour éviter une réponse trop longue
                }), 500
            
            # Retourner la réponse
            return jsonify(api_response), response.status_code
            
        except requests.RequestException as req_err:
            app.logger.error(f"Erreur lors de la récupération du token CSRF: {str(req_err)}")
            return jsonify({
                "success": False,
                "message": f"Erreur lors de la récupération du token CSRF: {str(req_err)}"
            }), 500
            
    except requests.RequestException as req_err:
        app.logger.error(f"Erreur de requête HTTP: {str(req_err)}")
        return jsonify({
            "success": False,
            "message": f"Erreur de communication avec le serveur MFA: {str(req_err)}"
        }), 500
    except Exception as e:
        app.logger.error(f"Erreur inattendue lors de la validation de l'OTP: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Erreur inattendue lors de la validation de l'OTP: {str(e)}",
            "trace": traceback.format_exc()
        }), 500

@app.route('/otp-test')
def otp_test():
    """Page de test spécifique pour la résolution d'OTP"""
    return render_template('otp_test.html')

@app.route('/mfa-redirect')
def mfa_redirect():
    """Page qui redirige vers le portail MFA réel"""
    redirect_uri = f"{request.url_root.rstrip('/')}/selfcare"
    auth_url = f"{MFA_URL}/login?redirect_uri={redirect_uri}"
    return redirect(auth_url)

# Route de débogage pour voir tous les paramètres reçus
@app.route('/debug')
def debug():
    """Page de débogage pour afficher les paramètres reçus"""
    output = {
        'args': dict(request.args),
        'headers': dict(request.headers),
        'cookies': dict(request.cookies),
        'url': request.url,
        'base_url': request.base_url,
        'path': request.path,
        'method': request.method
    }
    return jsonify(output)

# Route spéciale pour tester une redirection manuelle vers selfcare avec OTP
@app.route('/test-redirect/<otp>')
def test_redirect(otp):
    """Test de redirection manuelle"""
    return redirect(f"/selfcare?otp_token={otp}")

@app.before_request
def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)

if __name__ == '__main__':
    # Configurer la journalisation
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
    )
    
    # Créer le dossier templates s'il n'existe pas
    os.makedirs('templates', exist_ok=True)
    
    # Le simulateur n'a pas besoin de nettoyer les OTP expirés
    # car ce travail est fait par l'application MFA réelle
    
    # Désactiver les warnings d'HTTPS non vérifié
    import urllib3
    urllib3.disable_warnings()
    
    # Démarrer l'application avec hôte configuré pour être accessible depuis d'autres machines
    app.run(debug=False, host='0.0.0.0')
