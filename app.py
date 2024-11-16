from flask import Flask, request, jsonify, render_template
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from models import db
from config import Config
from dotenv import load_dotenv
from flask_mail import Message
from models import Utilisateur
from flask_jwt_extended import create_access_token
from datetime import timedelta
import os

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

mail = Mail(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": "*"}})

db.init_app(app)

@app.route('/inscription', methods=['POST'])
def inscription():
    data = request.get_json()
    email = data.get('email')
    mot_de_passe = data.get('mot_de_passe')
    nom_utilisateur = data.get('nom_utilisateur')

    utilisateur_existant = Utilisateur.query.filter_by(email=email).first()
    if utilisateur_existant:
        return jsonify({"message": "Email déjà utilisé"}), 400

    mot_de_passe_hashé = bcrypt.generate_password_hash(mot_de_passe).decode('utf-8')

    utilisateur = Utilisateur(email=email, mot_de_passe=mot_de_passe_hashé, nom_utilisateur=nom_utilisateur)
    db.session.add(utilisateur)
    db.session.commit()

    msg = Message('Confirmation d\'inscription', recipients=[email])
    msg.body = f"Bonjour {nom_utilisateur},\n\nVotre inscription a été réussie sur Explore Culture !\n\nMerci pour votre inscription."
    
    try:
        mail.send(msg)
        return jsonify({"message": "Inscription réussie, email de confirmation envoyé."}), 201
    except Exception as e:
        return jsonify({"message": f"Erreur d'envoi d'email : {str(e)}"}), 500

@app.route('/connexion', methods=['POST'])
def connexion():
    data = request.get_json()
    email = data.get('email')
    mot_de_passe = data.get('mot_de_passe')

    utilisateur = Utilisateur.query.filter_by(email=email).first()
    if not utilisateur:
        return jsonify({"message": "Utilisateur non trouvé"}), 404

    if not bcrypt.check_password_hash(utilisateur.mot_de_passe, mot_de_passe):
        return jsonify({"message": "Mot de passe incorrect"}), 401

    access_token = create_access_token(identity=utilisateur.id, expires_delta=timedelta(days=1))
    return jsonify(access_token=access_token), 200

@app.route('/recuperation_mdp', methods=['POST'])
def recuperation_mdp():
    data = request.get_json()
    email = data.get('email')

    utilisateur = Utilisateur.query.filter_by(email=email).first()
    if not utilisateur:
        return jsonify({"message": "Utilisateur non trouvé"}), 404

    msg = Message('Réinitialisation de votre mot de passe', recipients=[email])
    msg.body = f"Bonjour,\n\nCliquez sur ce lien pour réinitialiser votre mot de passe : http://votreurl.com/reset_password/{email}"
    
    try:
        mail.send(msg)
        return jsonify({"message": "Lien de réinitialisation envoyé par email."}), 200
    except Exception as e:
        return jsonify({"message": f"Erreur d'envoi d'email : {str(e)}"}), 500

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/api')
def api():
    return jsonify(message="Bienvenue dans l'API de Explore Culture")

@app.route('/connexion', methods=['GET'])
def connexion_page():
    return render_template('connexion.html')

@app.route('/inscription', methods=['GET'])
def inscription_page():
    return render_template('inscription.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)