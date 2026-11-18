import pytest
from app import app, load

@pytest.fixture
def client(tmp_path):
    app.config["DATA_FILE"] = str(tmp_path / "subs.json")
    app.config["TESTING"] = True
    return app.test_client()

GOOD = {"name": "Ali", "reg_no": "FA23-BCS-001", "title": "Lab 1",
        "url": "https://github.com/ali/lab1"}

def test_valid_submission_saved(client):
    r = client.post("/submit", data=GOOD)
    assert r.status_code == 200
    assert len(load()) == 1
    assert "FA23-BCS-001" in client.get("/").get_data(as_text=True)

def test_missing_registration_number_rejected(client):
    r = client.post("/submit", data={**GOOD, "reg_no": ""})
    assert r.status_code == 400
    assert "Registration number is required" in r.get_data(as_text=True)
    assert load() == []

def test_invalid_url_rejected(client):
    r = client.post("/submit", data={**GOOD, "url": "not a url"})
    assert r.status_code == 400
    assert load() == []