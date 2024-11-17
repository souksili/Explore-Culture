import os
import logging
from flask import Flask, jsonify, request, render_template
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager, create_access_token
from itsdangerous import URLSafeTimedSerializer
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import unicodedata

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('SMTP_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('SMTP_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('SMTP_USERNAME')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
jwt = JWTManager(app)
serializer = URLSafeTimedSerializer(app.config['JWT_SECRET_KEY'])

def remove_accents(input_str):
    return ''.join(
        c for c in unicodedata.normalize('NFD', input_str) if unicodedata.category(c) != 'Mn'
    )

def get_base_url():
    """Récupère l'URL de base de l'application à partir des variables d'environnement."""
    return os.getenv('APP_BASE_URL', 'http://localhost:5000')

class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(200), nullable=False)
    nom_utilisateur = db.Column(db.String(100), nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, onupdate=datetime.utcnow)
    date_derniere_connexion = db.Column(db.DateTime)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/api')
def api():
    return jsonify(message="Bienvenue dans l'API de Explore Culture")

@app.route('/inscription', methods=['POST'])
def inscription():
    try:
        data = request.get_json()
        email = data.get('email')
        mot_de_passe = data.get('mot_de_passe')
        nom_utilisateur = data.get('nom_utilisateur')

        if Utilisateur.query.filter_by(email=email).first():
            return jsonify({"message": "Email déjà utilisé"}), 400

        mot_de_passe_hashé = bcrypt.generate_password_hash(mot_de_passe).decode('utf-8')
        utilisateur = Utilisateur(email=email, mot_de_passe=mot_de_passe_hashé, nom_utilisateur=nom_utilisateur)
        db.session.add(utilisateur)
        db.session.commit()

        subject = "Confirmation d'inscription"
        body = (
            f"Bonjour {nom_utilisateur},\n\n"
            f"Votre inscription a été réussie sur Explore Culture !\n\n"
            f"Cordialement,\nL'équipe Explore Culture."
        )

        send_email(recipient=email, subject=subject, body=body)
        return jsonify({"message": "Inscription réussie, email de confirmation envoyé."}), 201
    except Exception as e:
        logging.error(f"Erreur lors de l'inscription : {e}")
        return jsonify({"message": "Une erreur est survenue lors de l'inscription"}), 500

@app.route('/connexion', methods=['POST'])
def connexion():
    try:
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
    except Exception as e:
        logging.error(f"Erreur lors de la connexion : {e}")
        return jsonify({"message": "Une erreur est survenue lors de la connexion"}), 500

@app.route('/recuperation_mdp', methods=['POST'])
def recuperation_mdp():
    try:
        data = request.get_json()
        email = data.get('email')

        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur:
            return jsonify({"message": "Utilisateur non trouvé"}), 404

        token = serializer.dumps(email, salt='password-recovery-salt')
        reset_link = f"{get_base_url()}/reset_password/{token}"

        subject = "Réinitialisation de votre mot de passe"
        body = (
            f"Bonjour,\n\n"
            f"Cliquez sur ce lien pour réinitialiser votre mot de passe :\n{reset_link}\n\n"
            "Ce lien expirera dans 30 minutes.\n\n"
            "Cordialement,\nL'équipe Explore Culture."
        )

        send_email(recipient=email, subject=subject, body=body)
        return jsonify({"message": "Lien de réinitialisation envoyé par email."}), 200
    except Exception as e:
        logging.error(f"Erreur lors de la récupération de mot de passe : {e}")
        return jsonify({"message": "Une erreur est survenue"}), 500

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-recovery-salt', max_age=1800)
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur:
            return jsonify({"message": "Utilisateur non trouvé"}), 404

        if request.method == 'POST':
            data = request.get_json()
            new_password = data.get('new_password')

            if not new_password or len(new_password) < 6:
                return jsonify({"message": "Le mot de passe doit contenir au moins 6 caractères."}), 400

            utilisateur.mot_de_passe = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()

            return jsonify({"message": "Mot de passe réinitialisé avec succès."}), 200

        return jsonify({"message": "Lien valide. Envoyez un nouveau mot de passe via POST."}), 200
    except Exception as e:
        logging.error(f"Erreur lors de la réinitialisation : {e}")
        return jsonify({"message": "Le lien est invalide ou expiré."}), 400

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Erreur non capturée : {e}")
    return jsonify({"message": "Une erreur est survenue"}), 500

def send_email(recipient, subject, body):
    try:
        msg = Message(subject, recipients=[recipient])
        msg.body = remove_accents(body)
        mail.send(msg)
        logging.info(f"Email envoyé avec succès à {recipient}.")
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi de l'email : {e}")
        raise

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)