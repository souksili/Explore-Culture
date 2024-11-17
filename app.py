import os
from flask import Flask, jsonify, request, render_template
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager, create_access_token
from datetime import timedelta
from models import Utilisateur, db

app = Flask(__name__)

# Configuration de l'application
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

db.init_app(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
jwt = JWTManager(app)

app.config['BASE_URL'] = os.getenv('BASE_URL', 'http://localhost:5000')

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

    # Vérification si l'email est déjà utilisé
    utilisateur_existant = Utilisateur.query.filter_by(email=email).first()
    if utilisateur_existant:
        return jsonify({"message": "Email déjà utilisé"}), 400

    # Hachage du mot de passe
    mot_de_passe_hashé = bcrypt.generate_password_hash(mot_de_passe).decode('utf-8')

    # Création de l'utilisateur
    utilisateur = Utilisateur(email=email, mot_de_passe=mot_de_passe_hashé, nom_utilisateur=nom_utilisateur)
    db.session.add(utilisateur)
    db.session.commit()

    # Envoi d'un email de confirmation
    msg = Message(
        'Confirmation d\'inscription',
        recipients=[email]
    )
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

    # Recherche de l'utilisateur par email
    utilisateur = Utilisateur.query.filter_by(email=email).first()
    if not utilisateur:
        return jsonify({"message": "Utilisateur non trouvé"}), 404

    # Vérification du mot de passe
    if not bcrypt.check_password_hash(utilisateur.mot_de_passe, mot_de_passe):
        return jsonify({"message": "Mot de passe incorrect"}), 401

    # Génération du token JWT
    access_token = create_access_token(identity=utilisateur.id, expires_delta=timedelta(days=1))
    return jsonify(access_token=access_token), 200

@app.route('/recuperation_mdp', methods=['POST'])
def recuperation_mdp():
    data = request.get_json()
    email = data.get('email')

    # Recherche de l'utilisateur par email
    utilisateur = Utilisateur.query.filter_by(email=email).first()
    if not utilisateur:
        return jsonify({"message": "Utilisateur non trouvé"}), 404

    # Envoi d'un email de réinitialisation de mot de passe
    msg = Message(
        'Réinitialisation de votre mot de passe',
        recipients=[email]
    )
    base_url = app.config['BASE_URL']
    msg.body = f"Bonjour,\n\nCliquez sur ce lien pour réinitialiser votre mot de passe : http://{base_url}/reset_password/{email}"

    try:
        mail.send(msg)
        return jsonify({"message": "Lien de réinitialisation envoyé par email."}), 200
    except Exception as e:
        return jsonify({"message": f"Erreur d'envoi d'email : {str(e)}"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)