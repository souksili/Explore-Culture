import os
from flask import Flask, jsonify, request, render_template
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager, create_access_token
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

app = Flask(__name__)

# Configuration de l'application
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# Initialisation des extensions
db.init_app(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
jwt = JWTManager(app)

class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(200), nullable=False)
    nom_utilisateur = db.Column(db.String(100), nullable=False)
    token_auth = db.Column(db.String(200))
    est_admin = db.Column(db.Boolean, default=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, onupdate=datetime.utcnow)
    date_derniere_connexion = db.Column(db.DateTime)

    profil = db.relationship('Profil', backref='utilisateur', lazy=True)

class Profil(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    prenom = db.Column(db.String(100))
    nom_complet = db.Column(db.String(200))
    photo_url = db.Column(db.String(200))
    langue = db.Column(db.String(50))
    localisation = db.Column(db.String(100))
    bio = db.Column(db.String(500))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, onupdate=datetime.utcnow)

# Routes
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)