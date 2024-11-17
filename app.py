import os
import smtplib
import logging
import qrcode
from flask import Flask, jsonify, request, render_template
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token
from datetime import timedelta, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Initialisation de l'application et des extensions
app = Flask(__name__)
db = SQLAlchemy()
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Configuration de l'application
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv(app.config['MAIL_USERNAME'])

# Initialisation de la base de données
db.init_app(app)

# Modèles
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

# Fonction pour envoyer un email avec QR code
def send_email_with_qr_code(subject, recipient_email, body, qr_content=None, qr_filename="qr_code.png"):
    try:
        # Générer un QR code si nécessaire
        qr_code_path = None
        if qr_content:
            qr = qrcode.make(qr_content)
            qr_code_path = os.path.join('temp', qr_filename)
            os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
            qr.save(qr_code_path)

        # Création de l'email
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Ajouter le QR code en pièce jointe
        if qr_code_path:
            with open(qr_code_path, "rb") as image_file:
                img = MIMEImage(image_file.read())
                img.add_header('Content-Disposition', 'attachment', filename=qr_filename)
                msg.attach(img)

        # Envoi de l'email via SMTP
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.sendmail(app.config['MAIL_USERNAME'], recipient_email, msg.as_string())

        # Nettoyer le fichier QR code temporaire
        if qr_code_path:
            os.remove(qr_code_path)
        return True

    except Exception as e:
        logging.error(f"Erreur lors de l'envoi de l'email : {e}")
        return False

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

    confirmation_link = f"{request.host_url.rstrip('/')}/confirm/{utilisateur.id}"
    body = f"Bonjour {nom_utilisateur},\n\nVotre inscription a été réussie sur Explore Culture !\nCliquez ici pour confirmer : {confirmation_link}\n\nMerci !"

    if send_email_with_qr_code(
        subject="Confirmation d'inscription",
        recipient_email=email,
        body=body,
        qr_content=confirmation_link
    ):
        return jsonify({"message": "Inscription réussie, email de confirmation envoyé."}), 201
    else:
        return jsonify({"message": "Inscription réussie, mais échec de l'envoi de l'email."}), 500

@app.route('/recuperation_mdp', methods=['POST'])
def recuperation_mdp():
    data = request.get_json()
    email = data.get('email')

    utilisateur = Utilisateur.query.filter_by(email=email).first()
    if not utilisateur:
        return jsonify({"message": "Utilisateur non trouvé"}), 404

    reset_link = f"{request.host_url.rstrip('/')}/reset_password/{utilisateur.id}"
    body = f"Bonjour,\n\nCliquez sur ce lien pour réinitialiser votre mot de passe : {reset_link}\n\nMerci."

    if send_email_with_qr_code(
        subject="Réinitialisation de votre mot de passe",
        recipient_email=email,
        body=body,
        qr_content=reset_link
    ):
        return jsonify({"message": "Lien de réinitialisation envoyé par email."}), 200
    else:
        return jsonify({"message": "Erreur lors de l'envoi de l'email."}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)