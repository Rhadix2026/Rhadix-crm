def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_meta(client):
    m = client.get("/api/meta").json()
    assert m["name"] == "Rhadix CRM"
    assert {mod["key"] for mod in m["modules"]} >= {"relaties", "krachtenveld"}


def test_sso_en_me(client, auth):
    """Authenticatie verloopt via SSO; /auth/me toont de JIT-gebruiker."""
    from tests.conftest import SSO_ADMIN_EMAIL

    me = client.get("/api/auth/me", headers=auth).json()
    assert me["email"] == SSO_ADMIN_EMAIL
    assert me["role"] == "PLATFORM_ADMIN"


def test_lokale_login_geblokkeerd(client):
    """Lokale wachtwoord-login is afgesloten — ongeacht of het wachtwoord klopt."""
    r = client.post("/api/auth/login", json={"email": "admin@rhadix.nl", "password": "fout"})
    assert r.status_code == 403


def test_zonder_token_geweigerd(client):
    assert client.get("/api/crm/organisaties").status_code == 401
