from app import __version__
from starlette.testclient import TestClient
from main import app


client = TestClient(app)

def test_version():
    assert __version__ == '0.1.0'

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}

def test_new_game():
    response = client.post("/game/new-game",json={"customer_id":2},)
    assert response.status_code == 200
    assert response.json() ==  {'data': {'customer_game_state': 'x,x,x,x,x,x,x,x,x,x,x,x',
    'customer_name': 'Sasaluck',
    'global_best': 17,
    'my_best': 0},
    'status': {'code': 1000, 'description': 'Success', 'header': ''}}



