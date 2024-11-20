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
import unicodedata
import re
import json
from flask_jwt_extended import jwt_required, get_jwt_identity
from mistralai import Mistral

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('SMTP_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('SMTP_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('SMTP_USERNAME')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
jwt = JWTManager(app)

api_key = os.getenv('API_KEY')
model = os.getenv('MODEL')

client = Mistral(api_key=api_key)

def remove_accents(input_str):
    return ''.join(
        c for c in unicodedata.normalize('NFD', input_str) if unicodedata.category(c) != 'Mn'
    )

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

class Historique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    date_ajout = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "description": self.description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "date_ajout": self.date_ajout.isoformat()
        }

def send_email(recipient, subject, body):
    try:
        smtp_server = os.getenv('MAIL_SERVER')
        smtp_port = int(os.getenv('MAIL_PORT'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')

        if not smtp_password:
            logging.error("SMTP_PASSWORD is not set or is empty!")
            raise ValueError("SMTP_PASSWORD is required")

        subject = remove_accents(subject)
        body = remove_accents(body)

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
    logging.info("Route /test appelée")
    return 'Hello, World!'

@app.route('/api')
def api():
    logging.info("Route /api appelée")
    return jsonify(message="Bienvenue dans l'API de Explore Culture")

@app.route('/connexion', methods=['GET'])
def connexion_page():
    logging.info("Route /connexion (GET) appelée")
    return render_template('connexion.html')

@app.route('/inscription', methods=['GET'])
def inscription_page():
    logging.info("Route /inscription (GET) appelée")
    return render_template('inscription.html')

@app.route('/dashboard', methods=['GET'])
def dashboard_page():
    logging.info("Route /dashboard appelée")
    return render_template('map.html')

@app.route('/inscription', methods=['POST'])
def inscription():
    try:
        logging.info("Route /inscription (POST) appelée")
        data = request.get_json()
        email = data.get('email')
        mot_de_passe = data.get('mot_de_passe')
        nom_utilisateur = data.get('nom_utilisateur')

        utilisateur_existant = Utilisateur.query.filter_by(email=email).first()
        if utilisateur_existant:
            logging.warning(f"Email déjà utilisé : {email}")
            return jsonify({"message": "Email déjà utilisé"}), 400

        mot_de_passe_hashé = bcrypt.generate_password_hash(mot_de_passe).decode('utf-8')
        utilisateur = Utilisateur(email=email, mot_de_passe=mot_de_passe_hashé, nom_utilisateur=nom_utilisateur)
        db.session.add(utilisateur)
        db.session.commit()

        subject = "Confirmation d'inscription"
        body = (
            f"Bonjour {nom_utilisateur},\n\n"
            f"Votre inscription a ete reussie sur Explore Culture !\n\n"
            f"Merci pour votre inscription.\n\n"
            f"Cordialement,\nL'equipe Explore Culture."
        )

        send_email(recipient=email, subject=subject, body=body)
        logging.info(f"Inscription réussie pour {email}")
        return jsonify({"message": "Inscription reussie, email de confirmation envoye."}), 201
    except Exception as e:
        logging.error(f"Erreur lors de l'inscription : {e}")
        return jsonify({"message": "Une erreur est survenue lors de l'inscription"}), 500

@app.route('/connexion', methods=['POST'])
def connexion():
    try:
        logging.info("Route /connexion (POST) appelée")
        data = request.get_json()
        email = data.get('email')
        mot_de_passe = data.get('mot_de_passe')

        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur:
            logging.warning(f"Utilisateur non trouvé : {email}")
            return jsonify({"message": "Utilisateur non trouvé"}), 404

        if not bcrypt.check_password_hash(utilisateur.mot_de_passe, mot_de_passe):
            logging.warning(f"Mot de passe incorrect pour : {email}")
            return jsonify({"message": "Mot de passe incorrect"}), 401

        access_token = create_access_token(identity=str(utilisateur.id), expires_delta=timedelta(days=1))
        logging.info(f"Connexion réussie pour {email}")
        return jsonify(access_token=access_token), 200
    except Exception as e:
        logging.error(f"Erreur lors de la connexion : {e}")
        return jsonify({"message": "Une erreur est survenue lors de la connexion"}), 500

@app.route('/deconnexion', methods=['POST'])
def deconnexion():
    try:
        logging.info("Route /deconnexion appelée")
        response = jsonify({"message": "Déconnexion réussie"})
        return response, 200
    except Exception as e:
        logging.error(f"Erreur lors de la déconnexion : {e}")
        return jsonify({"message": "Une erreur est survenue lors de la déconnexion"}), 500

@app.route('/recuperation_mdp', methods=['POST'])
def recuperation_mdp():
    try:
        logging.info("Route /recuperation_mdp appelée")
        data = request.get_json()
        email = data.get('email')

        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur:
            logging.warning(f"Utilisateur non trouvé pour la récupération de mot de passe : {email}")
            return jsonify({"message": "Utilisateur non trouvé"}), 404

        subject = "Reinitialisation de votre mot de passe"
        reset_link = f"http://votreurl.com/reset_password/{email}"
        body = (
            f"Bonjour,\n\n"
            f"Cliquez sur ce lien pour reinitialiser votre mot de passe :\n{reset_link}\n\n"
            "Si vous n'avez pas demande cette reinitialisation, veuillez ignorer cet e-mail.\n\n"
            "Cordialement,\nL'equipe Explore Culture."
        )

        send_email(recipient=email, subject=subject, body=body)
        logging.info(f"Lien de réinitialisation de mot de passe envoyé à {email}")
        return jsonify({"message": "Lien de reinitialisation envoye par email."}), 200
    except Exception as e:
        logging.error(f"Erreur lors de la récupération de mot de passe : {e}")
        return jsonify({"message": "Une erreur est survenue"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Erreur non capturée : {e}")
    return jsonify({"message": "Une erreur est survenue"}), 500

user_context = {}

@app.route('/chat', methods=['POST'])
def chat():
    try:
        logging.info("Route /chat appelée")
        req = request.get_json(silent=True, force=True)
        user_input = req.get('message').lower()
        user_id = req.get('user_id', 'default')

        # Initialisation du contexte si utilisateur non reconnu
        if user_id not in user_context:
            user_context[user_id] = {"stage": "start", "country": None, "preferences": None}

        # Obtenir le contexte actuel de l'utilisateur
        context = user_context[user_id]

        # Gestion des réponses en fonction du contexte actuel
        if context["stage"] == "start":
            if re.search(r'\bbonjour|salut\b', user_input):
                response = welcome_response()
                context["stage"] = "awaiting_country"
            else:
                response = fallback_response()

        elif context["stage"] == "awaiting_country":
            if "pays" in user_input:
                response = ask_country_response()
                context["stage"] = "awaiting_country_input"
            else:
                response = fallback_response()

        elif context["stage"] == "awaiting_country_input":
            context["country"] = user_input
            response = jsonify({"response": f"Vous avez choisi le pays : {user_input}. Avez-vous des préférences spécifiques (par exemple, plats traditionnels kabyles)?"})
            context["stage"] = "awaiting_preferences"

        elif context["stage"] == "awaiting_preferences":
            context["preferences"] = user_input
            response = jsonify({"response": f"Vous avez indiqué les préférences : {user_input}. Souhaitez-vous obtenir un itinéraire?"})
            context["stage"] = "country_confirmed"

        elif context["stage"] == "country_confirmed":
            if re.search(r'\boui\b', user_input):
                addresses = get_cultural_heritage_addresses(context["country"], context["preferences"])
                if isinstance(addresses, list):
                    response = jsonify({
                        "response": "Chargement des adresses sur la carte...",
                        "addresses": addresses,  # Transmettez les adresses au client
                        "redirect_url": "/dashboard"
                    })
                else:
                    response = jsonify({"response": "Aucune adresse valide trouvée."})
                user_context.pop(user_id, None)  # Réinitialiser le contexte
            elif re.search(r'\bnon\b', user_input):
                response = jsonify({"response": "D'accord, si vous avez d'autres questions, n'hésitez pas!"})
                user_context.pop(user_id, None)  # Réinitialiser le contexte
            else:
                response = fallback_response()
        else:
            response = fallback_response()

    except Exception as e:
        logging.error(f"Erreur dans la route /chat : {e}")
        response = jsonify({"response": f"Une erreur est survenue: {str(e)}"})

    return response

def welcome_response():
    logging.info("Réponse de bienvenue envoyée")
    return jsonify({"response": "Bonjour! Où aimeriez-vous voyager? (Par exemple : indiquez un pays)"})

def ask_country_response():
    logging.info("Demande de pays envoyée")
    return jsonify({"response": "Quel pays souhaitez-vous visiter?"})

def fallback_response():
    logging.info("Réponse de repli envoyée")
    return jsonify({"response": "Désolé, je n'ai pas compris. Pouvez-vous reformuler?"})

def get_cultural_heritage_addresses(country, preferences):
    try:
        logging.info(f"Récupération des adresses de patrimoine culturel pour {country} avec préférences {preferences}")
        messages = [
            {
                "role": "user",
                "content": f"Bonjour, Recommandez des adresses de patrimoine culturel pour {country} en sachant que le user aime {preferences}. Chaque objet dans la liste contient les champs nom, description, latitude, longitude."
            }
        ]
        chat_response = client.chat.complete(
            model=model,
            messages=messages,
            response_format={"type": "json_object"}
        )
        if chat_response.choices and chat_response.choices[0].message.content:
            return json.loads(chat_response.choices[0].message.content)
        else:
            return []
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des adresses de patrimoine culturel : {e}")
        return []

@app.route('/api/historique', methods=['POST'])
@jwt_required()
def ajouter_historique():
    try:
        logging.info("Route /api/historique (POST) appelée")
        data = request.get_json()
        utilisateur_id = get_jwt_identity()
        addresses = data.get('addresses', [])

        for address in addresses:
            historique = Historique(
                utilisateur_id=utilisateur_id,
                nom=address['nom'],
                description=address.get('description'),
                latitude=address['latitude'],
                longitude=address['longitude']
            )
            db.session.add(historique)

        db.session.commit()
        logging.info(f"Historique mis à jour pour l'utilisateur {utilisateur_id}")
        return jsonify({"message": "Historique mis à jour."}), 201
    except Exception as e:
        logging.error(f"Erreur lors de l'ajout à l'historique : {e}")
        return jsonify({"message": "Une erreur est survenue."}), 500

@app.route('/api/historique', methods=['GET'])
@jwt_required()
def recuperer_historique():
    try:
        logging.info("Route /api/historique (GET) appelée")
        utilisateur_id = str(get_jwt_identity())
        logging.info(f"Utilisateur ID: {utilisateur_id}")

        historique = Historique.query.filter_by(utilisateur_id=utilisateur_id).order_by(Historique.date_ajout.desc()).all()
        if not historique:
            logging.info("Aucun historique trouvé pour cet utilisateur.")
            return jsonify([]), 200

        historique_dict = []
        for item in historique:
            item_dict = item.to_dict()
            if not isinstance(item_dict.get('nom'), str):
                logging.error("Le nom doit être une chaîne de caractères")
                return jsonify({"message": "Le nom doit être une chaîne de caractères"}), 400
            if not isinstance(item_dict.get('latitude'), (int, float)):
                logging.error("La latitude doit être un nombre")
                return jsonify({"message": "La latitude doit être un nombre"}), 400
            if not isinstance(item_dict.get('longitude'), (int, float)):
                logging.error("La longitude doit être un nombre")
                return jsonify({"message": "La longitude doit être un nombre"}), 400
            historique_dict.append(item_dict)

        logging.info(f"Historique converti en dictionnaire: {historique_dict}")

        return jsonify(historique_dict), 200
    except Exception as e:
        logging.error(f"Erreur lors de la récupération de l'historique : {e}")
        return jsonify({"message": "Une erreur est survenue lors de la récupération de l'historique"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)