def test_seed_geladen(client, auth):
    rsos = client.get("/api/crm/organisaties?soort=RSO", headers=auth).json()
    vvts = client.get("/api/crm/organisaties?soort=VVT", headers=auth).json()
    assert len(rsos) == 17
    assert len(vvts) == 152


def test_contactpersonen_seed(client, auth):
    cps = client.get("/api/crm/contactpersonen", headers=auth).json()
    assert len(cps) >= 60


def test_voorbeeld_krachtenveld(client, auth):
    kvs = client.get("/api/crm/krachtenvelden", headers=auth).json()
    assert len(kvs) >= 1
    kv = client.get(f"/api/crm/krachtenvelden/{kvs[0]['id']}", headers=auth).json()
    assert len(kv["stakeholders"]) == 8
    # kwadrant-afleiding
    namen = {s["naam"]: s["kwadrant"] for s in kv["stakeholders"]}
    assert namen["Informatiemanager / CIO"] == "Actief betrekken"
    assert namen["Bestuurder / Directeur"] == "Tevreden houden"
    assert namen["Communicatie / Relatiemanager"] == "Informeren"


def test_crud_organisatie(client, auth):
    created = client.post("/api/crm/organisaties", headers=auth,
                          json={"soort": "VVT", "naam": "Testaanbieder", "provincies": "Utrecht"}).json()
    oid = created["id"]
    assert created["naam"] == "Testaanbieder"
    client.patch(f"/api/crm/organisaties/{oid}", headers=auth,
                 json={"soort": "VVT", "naam": "Testaanbieder BV", "provincies": "Utrecht"})
    got = client.get(f"/api/crm/organisaties/{oid}", headers=auth).json()
    assert got["naam"] == "Testaanbieder BV"
    assert client.delete(f"/api/crm/organisaties/{oid}", headers=auth).status_code == 204


def test_krachtenveld_met_stakeholder(client, auth):
    kv = client.post("/api/crm/krachtenvelden", headers=auth,
                     json={"titel": "Test KV"}).json()
    sh = client.post(f"/api/crm/krachtenvelden/{kv['id']}/stakeholders", headers=auth,
                     json={"naam": "Jan", "invloed": "Hoog", "betrokkenheid": "Hoog"}).json()
    assert sh["kwadrant"] == "Actief betrekken"
    client.patch(f"/api/crm/stakeholders/{sh['id']}", headers=auth,
                 json={"naam": "Jan", "invloed": "Hoog", "betrokkenheid": "Laag"})
    kv2 = client.get(f"/api/crm/krachtenvelden/{kv['id']}", headers=auth).json()
    assert kv2["stakeholders"][0]["kwadrant"] == "Tevreden houden"


def test_activiteit_opvolging(client, auth):
    a = client.post("/api/crm/activiteiten", headers=auth,
                    json={"titel": "Bellen", "soort": "taak", "status": "open"}).json()
    assert a["status"] == "open"
    open_items = client.get("/api/crm/activiteiten?status=open", headers=auth).json()
    assert any(x["id"] == a["id"] for x in open_items)


def test_dashboard(client, auth):
    d = client.get("/api/crm/dashboard", headers=auth).json()
    assert d["rso_count"] == 17
    assert d["aanbieder_count"] >= 152
    assert "kwadranten" in d and sum(d["kwadranten"].values()) >= 8
