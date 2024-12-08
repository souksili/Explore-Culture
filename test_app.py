import pytest
from app import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://explore_culture_2o0u_user:6GccQd1C9t7lKaSS1MBK3adCwTB1vsZP@dpg-csujvsa3esus73cjoq2g-a.frankfurt-postgres.render.com/explore_culture_2o0u'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'mon_secret_key_unique'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sportapi97@gmail.com'
app.config['MAIL_PASSWORD'] = 'oycx qhfe kvlp ddcn'
app.config['MAIL_DEFAULT_SENDER'] = 'sportapi97@gmail.com'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)
jwt = JWTManager(app)

api_key = 'kqtn0dT4zqReaK70ZBpWiUhPxPMckCFN'
model = 'mistral-large-latest'

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_hello_world(client):
    """Teste la route principale '/'"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Hello, World!" in response.data

def test_api(client):
    """Teste la route '/api'"""
    response = client.get('/api')
    assert response.status_code == 200
    assert b"Bienvenue dans l'API de Explore Culture" in response.data