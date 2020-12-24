from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import Base
from main import app, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_create_customer():
    response = client.post(
        "/customer",
        json={
            "first_name": "Sasaluck",
            "last_name": "C.",
            "phone_number": "0958634627"
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"]["code"] == 1000
    assert data["data"]["first_name"] == "Sasaluck"
    assert data["data"]["last_name"] == "C."
    assert data["data"]["phone_number"] == "0958634627"

    response = client.get("/customers")
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["status"]["code"] == 1000
    assert data["data"]["first_name"] == "Sasaluck"
    assert data["data"]["last_name"] == "C."
    assert data["data"]["phone_number"] == "0958634627"


def test_create_global_game():
    response = client.post(
        "/game/global-game",
        json={
            "state": "1,1,4,6,4,5,2,3,2,3,5,6",
            "global_best": 0
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"]["code"] == 1000
    assert data["data"]["state"] == "1,1,4,6,4,5,2,3,2,3,5,6"
    assert data["data"]["global_best"] == 0


def test_new_game_failed_invalid_customer():
    response = client.post("/game/new-game",json={"customer_id":-1},)
    assert response.status_code == 200
    assert response.json() ==  {
    "status": {
        "code": 1999,
        "header": "",
        "description": "Fail. Customer does not exist."
    },
    "data": {}
}


def test_open_card_invalid_card_number():
    response = client.post("/game/card-open",json={
        "customer_id":2,
        "card_no": -1,
        "prev_card_no":11
        })

    assert response.status_code == 200
    assert response.json() ==  {
        "status": {
            "code": 1999,
            "header": "",
            "description": "Fail. Card no is not valid."
        },
        "data": {}
    }


def test_open_card_invalid_customer():
    response = client.post("/game/card-open",json={
        "customer_id":100,
        "card_no": 1,
        "prev_card_no":11
        })

    assert response.status_code == 200
    assert response.json() ==  {
        "status": {
            "code": 1999,
            "header": "",
            "description": "Fail. User does not exist."
        },
        "data": {}
    }
