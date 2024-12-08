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
    group_id = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "description": self.description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "date_ajout": self.date_ajout.isoformat(),
            "group_id": self.group_id
        }

class Zone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    taille = db.Column(db.Integer, nullable=False)
    couleur = db.Column(db.String(7), nullable=False)
    date_ajout = db.Column(db.DateTime, default=datetime.utcnow)
    patrimoines = db.relationship('PatrimoineCulturel', backref='zone', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "description": self.description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "taille": self.taille,
            "couleur": self.couleur,
            "date_ajout": self.date_ajout.isoformat(),
            "patrimoines": [patrimoine.to_dict() for patrimoine in self.patrimoines]
        }

class PatrimoineCulturel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=False)
    type_patrimoine = db.Column(db.String(100), nullable=False)
    nom = db.Column(db.String(200), nullable=True)
    lieu = db.Column(db.String(200), nullable=True)
    importance = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(200), nullable=True)
    date_ajout = db.Column(db.DateTime, default=datetime.utcnow)

    cuisine = db.relationship('Cuisine', backref='patrimoine', lazy=True, uselist=False)
    histoire = db.relationship('Histoire', backref='patrimoine', lazy=True, uselist=False)
    personnalite = db.relationship('Personnalite', backref='patrimoine', lazy=True, uselist=False)
    musique = db.relationship('Musique', backref='patrimoine', lazy=True, uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "zone_id": self.zone_id,
            "type_patrimoine": self.type_patrimoine,
            "nom": self.nom,
            "lieu": self.lieu,
            "importance": self.importance,
            "description": self.description,
            "photo_url": self.photo_url,
            "date_ajout": self.date_ajout.isoformat(),
            "cuisine": self.cuisine.to_dict() if self.cuisine else None,
            "histoire": self.histoire.to_dict() if self.histoire else None,
            "personnalite": self.personnalite.to_dict() if self.personnalite else None,
            "musique": self.musique.to_dict() if self.musique else None,
        }

class Cuisine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patrimoine_id = db.Column(db.Integer, db.ForeignKey('patrimoine_culturel.id'), nullable=False)
    recette = db.Column(db.Text, nullable=True)
    ingredients = db.Column(db.Text, nullable=True)
    temps_preparation = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            "recette": self.recette,
            "ingredients": self.ingredients,
            "temps_preparation": self.temps_preparation,
        }

class Histoire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patrimoine_id = db.Column(db.Integer, db.ForeignKey('patrimoine_culturel.id'), nullable=False)
    evenement = db.Column(db.String(200), nullable=True)
    date_evenement = db.Column(db.String(50), nullable=True)
    personnages_cles = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "evenement": self.evenement,
            "date_evenement": self.date_evenement,
            "personnages_cles": self.personnages_cles,
        }

class Personnalite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patrimoine_id = db.Column(db.Integer, db.ForeignKey('patrimoine_culturel.id'), nullable=False)
    nom_personnalite = db.Column(db.String(200), nullable=True)
    biographie = db.Column(db.Text, nullable=True)
    contributions = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "nom_personnalite": self.nom_personnalite,
            "biographie": self.biographie,
            "contributions": self.contributions,
        }

class Musique(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patrimoine_id = db.Column(db.Integer, db.ForeignKey('patrimoine_culturel.id'), nullable=False)
    titre_musique = db.Column(db.String(200), nullable=True)
    artiste = db.Column(db.String(200), nullable=True)
    genre = db.Column(db.String(100), nullable=True)
    lien_musique = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            "titre_musique": self.titre_musique,
            "artiste": self.artiste,
            "genre": self.genre,
            "lien_musique": self.lien_musique,
        }

def send_email(recipient, subject, body):
    try:
        smtp_server = app.config['MAIL_SERVER']
        smtp_port = app.config['MAIL_PORT']
        smtp_username = app.config['MAIL_USERNAME']
        smtp_password = app.config['MAIL_PASSWORD']

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

@app.route('/editer_profil', methods=['GET'])
def editer_profil_page():
    logging.info("Route /editer_profil appelée")
    return render_template('editer_profil.html')

@app.route('/discover', methods=['GET'])
def discover_page():
    return render_template('discover.html')

@app.route('/api/zones', methods=['POST'])
@jwt_required()
def ajouter_zone():
    try:
        logging.info("Route /api/zones (POST) appelée")
        data = request.get_json()
        utilisateur_id = get_jwt_identity()
        nom = data.get('nom')
        description = data.get('description')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        taille = data.get('taille')
        couleur = data.get('couleur')

        zone = Zone(
            utilisateur_id=utilisateur_id,
            nom=nom,
            description=description,
            latitude=latitude,
            longitude=longitude,
            taille=taille,
            couleur=couleur
        )
        db.session.add(zone)
        db.session.commit()

        logging.info(f"Zone ajoutée pour l'utilisateur {utilisateur_id}")
        return jsonify({"message": "Zone ajoutée."}), 201
    except Exception as e:
        logging.error(f"Erreur lors de l'ajout de la zone : {e}")
        return jsonify({"message": "Une erreur est survenue."}), 500

@app.route('/api/user_role', methods=['GET'])
@jwt_required()
def get_user_role():
    try:
        logging.info("Route /api/user_role appelée")
        utilisateur_id = get_jwt_identity()
        utilisateur = Utilisateur.query.get(utilisateur_id)
        if utilisateur:
            return jsonify({"est_admin": utilisateur.est_admin}), 200
        else:
            return jsonify({"message": "Utilisateur non trouvé"}), 404
    except Exception as e:
        logging.error(f"Erreur lors de la vérification du rôle de l'utilisateur : {e}")
        return jsonify({"message": "Une erreur est survenue"}), 500

@app.route('/api/zones', methods=['GET'])
@jwt_required()
def recuperer_zones():
    try:
        logging.info("Route /api/zones (GET) appelée")

        zones = Zone.query.all()
        if not zones:
            logging.info("Aucune zone trouvée.")
            return jsonify([]), 200

        zones_dict = [zone.to_dict() for zone in zones]

        logging.info(f"Zones récupérées: {zones_dict}")
        return jsonify(zones_dict), 200
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des zones : {e}")
        return jsonify({"message": "Une erreur est survenue lors de la récupération des zones"}), 500

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
            f"Votre inscription a été réussie sur Explore Culture !\n\n"
            f"Merci pour votre inscription.\n\n"
            f"Cordialement,\nL'équipe Explore Culture."
        )

        send_email(recipient=email, subject=subject, body=body)
        logging.info(f"Inscription réussie pour {email}")
        return jsonify({"message": "Inscription réussie, email de confirmation envoyé."}), 201
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

        subject = "Réinitialisation de votre mot de passe"
        reset_link = f"http://votreurl.com/reset_password/{email}"
        body = (
            f"Bonjour,\n\n"
            f"Cliquez sur ce lien pour réinitialiser votre mot de passe :\n{reset_link}\n\n"
            "Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet e-mail.\n\n"
            "Cordialement,\nL'équipe Explore Culture."
        )

        send_email(recipient=email, subject=subject, body=body)
        logging.info(f"Lien de réinitialisation de mot de passe envoyé à {email}")
        return jsonify({"message": "Lien de réinitialisation envoyé par email."}), 200
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

        if user_id not in user_context:
            user_context[user_id] = {"stage": "start", "country": None, "preferences": None}

        context = user_context[user_id]

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
                        "addresses": addresses,
                        "redirect_url": "/dashboard"
                    })
                else:
                    response = jsonify({"response": "Aucune adresse valide trouvée."})
                user_context.pop(user_id, None)
            elif re.search(r'\bnon\b', user_input):
                response = jsonify({"response": "D'accord, si vous avez d'autres questions, n'hésitez pas!"})
                user_context.pop(user_id, None)
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

import uuid

@app.route('/api/historique', methods=['POST'])
@jwt_required()
def ajouter_historique():
    try:
        logging.info("Route /api/historique (POST) appelée")
        data = request.get_json()
        utilisateur_id = get_jwt_identity()
        addresses = data.get('addresses', [])

        group_id = str(uuid.uuid4())

        for address in addresses:
            historique = Historique(
                utilisateur_id=utilisateur_id,
                nom=address['nom'],
                description=address.get('description'),
                latitude=address['latitude'],
                longitude=address['longitude'],
                group_id=group_id
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

@app.route('/api/historique/<group_id>', methods=['DELETE'])
@jwt_required()
def supprimer_historique(group_id):
    try:
        logging.info(f"Route /api/historique/{group_id} (DELETE) appelée")
        utilisateur_id = get_jwt_identity()

        Historique.query.filter_by(utilisateur_id=utilisateur_id, group_id=group_id).delete()
        db.session.commit()

        logging.info(f"Itinéraire {group_id} supprimé pour l'utilisateur {utilisateur_id}")
        return jsonify({"message": "Itinéraire supprimé."}), 200
    except Exception as e:
        logging.error(f"Erreur lors de la suppression de l'itinéraire : {e}")
        return jsonify({"message": "Une erreur est survenue."}), 500

@app.route('/editer_profil', methods=['POST'])
@jwt_required()
def editer_profil():
    try:
        logging.info("Route /editer_profil (POST) appelée")
        utilisateur_id = get_jwt_identity()
        data = request.get_json()

        prenom = data.get('prenom')
        nom_complet = data.get('nom_complet')
        photo_url = data.get('photo_url')
        langue = data.get('langue')
        localisation = data.get('localisation')
        bio = data.get('bio')

        profil = Profil.query.filter_by(utilisateur_id=utilisateur_id).first()
        if not profil:
            profil = Profil(utilisateur_id=utilisateur_id)

        if prenom:
            profil.prenom = prenom
        if nom_complet:
            profil.nom_complet = nom_complet
        if photo_url:
            profil.photo_url = photo_url
        if langue:
            profil.langue = langue
        if localisation:
            profil.localisation = localisation
        if bio:
            profil.bio = bio

        db.session.add(profil)
        db.session.commit()

        logging.info(f"Profil mis à jour pour l'utilisateur {utilisateur_id}")
        return jsonify({"message": "Profil mis à jour."}), 200
    except Exception as e:
        logging.error(f"Erreur lors de la mise à jour du profil : {e}")
        return jsonify({"message": "Une erreur est survenue lors de la mise à jour du profil"}), 500

@app.route('/api/zones/<int:zone_id>/patrimoines', methods=['POST'])
@jwt_required()
def ajouter_patrimoine(zone_id):
    try:
        logging.info(f"Route /api/zones/{zone_id}/patrimoines (POST) appelée")
        data = request.get_json()
        type_patrimoine = data.get('type_patrimoine')
        nom = data.get('nom')
        lieu = data.get('lieu')
        importance = data.get('importance')
        description = data.get('description')
        photo_url = data.get('photo_url')

        valid_types = ["cuisine", "histoire", "personnalité", "musique"]
        if type_patrimoine not in valid_types:
            logging.error(f"Type de patrimoine invalide : {type_patrimoine}")
            return jsonify({"message": "Type de patrimoine invalide"}), 400

        patrimoine = PatrimoineCulturel(
            zone_id=zone_id,
            type_patrimoine=type_patrimoine,
            nom=nom,
            lieu=lieu,
            importance=importance,
            description=description,
            photo_url=photo_url
        )
        db.session.add(patrimoine)
        db.session.commit()

        if type_patrimoine == "cuisine":
            recette = data.get('recette')
            ingredients = data.get('ingredients')
            temps_preparation = data.get('temps_preparation')
            cuisine = Cuisine(
                patrimoine_id=patrimoine.id,
                recette=recette,
                ingredients=ingredients,
                temps_preparation=temps_preparation
            )
            db.session.add(cuisine)
        elif type_patrimoine == "histoire":
            evenement = data.get('evenement')
            date_evenement = data.get('date_evenement')
            personnages_cles = data.get('personnages_cles')
            histoire = Histoire(
                patrimoine_id=patrimoine.id,
                evenement=evenement,
                date_evenement=date_evenement,
                personnages_cles=personnages_cles
            )
            db.session.add(histoire)
        elif type_patrimoine == "personnalité":
            nom_personnalite = data.get('nom_personnalite')
            biographie = data.get('biographie')
            contributions = data.get('contributions')
            personnalite = Personnalite(
                patrimoine_id=patrimoine.id,
                nom_personnalite=nom_personnalite,
                biographie=biographie,
                contributions=contributions
            )
            db.session.add(personnalite)
        elif type_patrimoine == "musique":
            titre_musique = data.get('titre_musique')
            artiste = data.get('artiste')
            genre = data.get('genre')
            lien_musique = data.get('lien_musique')
            musique = Musique(
                patrimoine_id=patrimoine.id,
                titre_musique=titre_musique,
                artiste=artiste,
                genre=genre,
                lien_musique=lien_musique
            )
            db.session.add(musique)

        db.session.commit()

        logging.info(f"Patrimoine culturel ajouté pour la zone {zone_id}")
        return jsonify({"message": "Patrimoine culturel ajouté."}), 201
    except Exception as e:
        logging.error(f"Erreur lors de l'ajout du patrimoine culturel : {e}")
        return jsonify({"message": "Une erreur est survenue."}), 500

@app.route('/api/zones/<int:zone_id>/patrimoines', methods=['GET'])
@jwt_required()
def recuperer_patrimoines(zone_id):
    try:
        logging.info(f"Route /api/zones/{zone_id}/patrimoines (GET) appelée")
        patrimoines = PatrimoineCulturel.query.filter_by(zone_id=zone_id).all()
        if not patrimoines:
            logging.info("Aucun patrimoine culturel trouvé pour cette zone.")
            return jsonify([]), 200

        patrimoines_dict = [patrimoine.to_dict() for patrimoine in patrimoines]

        logging.info(f"Patrimoines culturels récupérés: {patrimoines_dict}")
        return jsonify(patrimoines_dict), 200
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des patrimoines culturels : {e}")
        return jsonify({"message": "Une erreur est survenue lors de la récupération des patrimoines culturels"}), 500

@app.route('/api/zones/<int:zone_id>/patrimoines/<int:patrimoine_id>', methods=['DELETE'])
@jwt_required()
def supprimer_patrimoine(zone_id, patrimoine_id):
    try:
        logging.info(f"Route /api/zones/{zone_id}/patrimoines/{patrimoine_id} (DELETE) appelée")
        patrimoine = PatrimoineCulturel.query.get(patrimoine_id)
        if not patrimoine or patrimoine.zone_id != zone_id:
            logging.warning(f"Patrimoine culturel non trouvé ou ne correspond pas à la zone {zone_id}")
            return jsonify({"message": "Patrimoine culturel non trouvé"}), 404

        db.session.delete(patrimoine)
        db.session.commit()

        logging.info(f"Patrimoine culturel {patrimoine_id} supprimé pour la zone {zone_id}")
        return jsonify({"message": "Patrimoine culturel supprimé."}), 200
    except Exception as e:
        logging.error(f"Erreur lors de la suppression du patrimoine culturel : {e}")
        return jsonify({"message": "Une erreur est survenue."}), 500

@app.route('/api/zones/<int:zone_id>/all', methods=['GET'])
@jwt_required()
def recuperer_toutes_donnees_par_zone(zone_id):
    try:
        logging.info(f"Route /api/zones/{zone_id}/all (GET) appelée")

        zone = Zone.query.get(zone_id)
        if not zone:
            logging.warning(f"Zone {zone_id} non trouvée")
            return jsonify({"message": "Zone non trouvée"}), 404

        histoires = Histoire.query.join(PatrimoineCulturel).filter(PatrimoineCulturel.zone_id == zone_id).all()
        musiques = Musique.query.join(PatrimoineCulturel).filter(PatrimoineCulturel.zone_id == zone_id).all()
        cuisines = Cuisine.query.join(PatrimoineCulturel).filter(PatrimoineCulturel.zone_id == zone_id).all()
        personnalites = Personnalite.query.join(PatrimoineCulturel).filter(PatrimoineCulturel.zone_id == zone_id).all()

        data = {
            "histoire": [histoire.to_dict() for histoire in histoires],
            "musique": [musique.to_dict() for musique in musiques],
            "cuisine": [cuisine.to_dict() for cuisine in cuisines],
            "personnalite": [personnalite.to_dict() for personnalite in personnalites]
        }

        print(f"Données récupérées pour la zone {zone_id}: {data}")
        return jsonify(data), 200
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des données pour la zone {zone_id} : {e}")
        return jsonify({"message": "Une erreur est survenue lors de la récupération des données"}), 500

@app.route('/api/qcm/<int:zone_id>', methods=['GET'])
@jwt_required()
def recuperer_qcm(zone_id):
    try:
        logging.info(f"Route /api/qcm/{zone_id} (GET) appelée")

        zone = Zone.query.get(zone_id)
        if not zone:
            logging.warning(f"Zone {zone_id} non trouvée")
            return jsonify({"message": "Zone non trouvée"}), 404

        patrimoines = PatrimoineCulturel.query.filter_by(zone_id=zone_id).all()

        data = {
            "histoire": [],
            "musique": [],
            "cuisine": [],
            "personnalite": []
        }

        for patrimoine in patrimoines:
            if patrimoine.histoire:
                data["histoire"].append(patrimoine.histoire.to_dict())
            if patrimoine.musique:
                data["musique"].append(patrimoine.musique.to_dict())
            if patrimoine.cuisine:
                data["cuisine"].append(patrimoine.cuisine.to_dict())
            if patrimoine.personnalite:
                data["personnalite"].append(patrimoine.personnalite.to_dict())

        qcm_data = generate_qcm_with_mistral(data)

        logging.info(f"QCM généré pour la zone {zone_id}: {qcm_data}")
        return jsonify(qcm_data), 200
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des QCM pour la zone {zone_id} : {e}")
        return jsonify({"message": "Une erreur est survenue lors de la récupération des QCM"}), 500

def generate_qcm_with_mistral(data):
    try:
        logging.info(f"Génération de QCM avec Mistral pour les données : {data}")

        instructions = []
        if data["histoire"]:
            instructions.append("Générez une question sur les événements historique. La réponse correcte doit être placée de manière aléatoire parmi les options.")
        else:
            instructions.append("ne Générez pas")

        if data["cuisine"]:
            instructions.append("Générez une question sur le plats traditionnels. La réponse correcte doit être placée de manière aléatoire parmi les options.")
        else:
            instructions.append("ne Générez pas")

        if data["musique"]:
            instructions.append("Générez moi une question sur les musiciens. La réponse correcte doit être placée de manière aléatoire parmi les options.")
        else:
            instructions.append("ne Générez pas")

        if data["personnalite"]:
            instructions.append("Générez une question sur les personnalités. La réponse correcte doit être placée de manière aléatoire parmi les options.")
        else:
            instructions.append("ne Générez pas")

        messages = [
            {
                "role": "user",
                "content": (
                    f"Bonjour, générez un QCM basé sur les données suivantes : {json.dumps(data)}. "
                    f"Le format du QCM doit être le suivant : {json.dumps(QCM_FORMAT)}. "
                    f"Pour chaque question, générez des options de réponse concrètes basées sur les données fournies. "
                    f"Assurez-vous que chaque question a une réponse correcte et trois réponses incorrectes. "
                    f"Instructions spécifiques : {' '.join(instructions)}"
                )
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
        logging.error(f"Erreur lors de la génération de QCM avec Mistral : {e}")
        return []

QCM_FORMAT = {
    "questions": [
        {
            "question": ".....?",
            "options": [
                {"text": "Option 1", "correct": False},
                {"text": "Option 2", "correct": False},
                {"text": "Option 3", "correct": True},
                {"text": "Option 4", "correct": False}
            ]
        },
        {
            "question": "...?",
            "options": [
                {"text": "Option 1", "correct": False},
                {"text": "Option 2", "correct": False},
                {"text": "Option 3", "correct": True},
                {"text": "Option 4", "correct": False}
            ]
        },
        {
            "question": "....?",
            "options": [
                {"text": "Option 1", "correct": False},
                {"text": "Option 2", "correct": False},
                {"text": "Option 3", "correct": True},
                {"text": "Option 4", "correct": False}
            ]
        },
        {
            "question": ".....?",
            "options": [
                {"text": "Option 1", "correct": False},
                {"text": "Option 2", "correct": False},
                {"text": "Option 3", "correct": True},
                {"text": "Option 4", "correct": False}
            ]
        }
    ]
}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)