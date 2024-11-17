import os
import logging
from flask import Flask, jsonify, request, render_template
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager, create_access_token
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration de l'application
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('SMTP_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('SMTP_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('SMTP_USERNAME')

# Initialisation des extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
jwt = JWTManager(app)

# Modèles de base de données
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

# Fonction pour envoyer des emails
def send_email(recipient, subject, body):
    try:
        smtp_server = os.getenv('MAIL_SERVER')
        smtp_port = int(os.getenv('MAIL_PORT'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')

        if not smtp_password:
            logging.error("SMTP_PASSWORD is not set or is empty!")
            raise ValueError("SMTP_PASSWORD is required")

        msg = MIMEMultipart()
        msg['From'] = formataddr((str(Header('Explore Culture', 'utf-8')), smtp_username))
        msg['To'] = formataddr((str(Header(recipient, 'utf-8')), recipient))
        msg['Subject'] = Header(subject, 'utf-8')
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, recipient, msg.as_string())

        logging.info(f"Email envoyé avec succès à {recipient}.")
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi de l'email : {e}")
        raise

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

    subject = "Confirmation d'inscription"
    body = (
        f"Bonjour {nom_utilisateur},\n\n"
        f"Votre inscription a été réussie sur Explore Culture !\n\n"
        f"Merci pour votre inscription.\n\n"
        f"Cordialement,\nL'équipe Explore Culture."
    )

    try:
        send_email(recipient=email, subject=subject, body=body)
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

    subject = "Réinitialisation de votre mot de passe"
    reset_link = f"http://votreurl.com/reset_password/{email}"
    body = (
        f"Bonjour,\n\n"
        f"Cliquez sur ce lien pour réinitialiser votre mot de passe :\n{reset_link}\n\n"
        "Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet e-mail.\n\n"
        "Cordialement,\nL'équipe Explore Culture."
    )

    try:
        send_email(recipient=email, subject=subject, body=body)
        return jsonify({"message": "Lien de réinitialisation envoyé par email."}), 200
    except Exception as e:
        return jsonify({"message": f"Erreur d'envoi d'email : {str(e)}"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)