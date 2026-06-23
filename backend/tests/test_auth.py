def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_meta(client):
    m = client.get("/api/meta").json()
    assert m["name"] == "Rhadix CRM"
    assert {mod["key"] for mod in m["modules"]} >= {"relaties", "krachtenveld"}


def test_login_en_me(client, auth):
    me = client.get("/api/auth/me", headers=auth).json()
    assert me["email"] == "admin@rhadix.nl"
    assert me["role"] == "PLATFORM_ADMIN"


def test_login_fout_wachtwoord(client):
    r = client.post("/api/auth/login", json={"email": "admin@rhadix.nl", "password": "fout"})
    assert r.status_code == 401


def test_zonder_token_geweigerd(client):
    assert client.get("/api/crm/organisaties").status_code == 401
