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


def test_genereer_krachtenveld(client, auth):
    # kies een RSO (GERRIT heeft seed-contactpersonen)
    rsos = client.get("/api/crm/organisaties?soort=RSO", headers=auth).json()
    gerrit = next((o for o in rsos if o["naam"] == "GERRIT"), rsos[0])
    r = client.post(f"/api/crm/organisaties/{gerrit['id']}/genereer-krachtenveld", headers=auth)
    assert r.status_code == 201, r.text
    kv = r.json()
    # standaard 8 rollen + minimaal de gekoppelde contactpersonen
    assert kv["titel"].startswith("Krachtenveld GERRIT")
    assert len(kv["stakeholders"]) >= 8
    namen = [s["naam"] for s in kv["stakeholders"]]
    assert "Informatiemanager / CIO" in namen
    # canvas voorgevuld
    assert kv["kernopgave"] and kv["beslissingsdrivers"] and kv["kansen"]
    # kwadrant-afleiding werkt op gegenereerde stakeholders
    cio = next(s for s in kv["stakeholders"] if s["naam"] == "Informatiemanager / CIO")
    assert cio["kwadrant"] == "Actief betrekken"


def test_teamleden_en_accounthouder(client, auth):
    team = client.get("/api/crm/teamleden", headers=auth).json()
    assert team and team[0]["email"] == "admin@rhadix.nl"
    me_id = team[0]["id"]
    # organisatie met e-mail, linkedin én accounthouder
    org = client.post("/api/crm/organisaties", headers=auth, json={
        "soort": "RSO", "naam": "RSO Test", "email": "info@rsotest.nl",
        "linkedin": "https://linkedin.com/company/rsotest", "accounthouder_id": me_id,
    }).json()
    assert org["email"] == "info@rsotest.nl"
    assert org["linkedin"].endswith("rsotest")
    assert org["accounthouder"] and org["accounthouder"]["email"] == "admin@rhadix.nl"
    # accounthouder leeghalen mag ook
    upd = client.patch(f"/api/crm/organisaties/{org['id']}", headers=auth, json={
        "soort": "RSO", "naam": "RSO Test", "accounthouder_id": None,
    }).json()
    assert upd["accounthouder"] is None


def test_stakeholder_email_linkedin(client, auth):
    kv = client.post("/api/crm/krachtenvelden", headers=auth, json={"titel": "KV velden"}).json()
    sh = client.post(f"/api/crm/krachtenvelden/{kv['id']}/stakeholders", headers=auth, json={
        "naam": "Jan", "email": "jan@rso.nl", "linkedin": "https://linkedin.com/in/jan",
    }).json()
    assert sh["email"] == "jan@rso.nl" and sh["linkedin"].endswith("/jan")


def test_extra_accounthouders_org_en_contactpersoon(client, auth):
    """Meerdere Rhadix-collega's koppelbaar: primair + extra, op relatie én contactpersoon."""
    team = client.get("/api/crm/teamleden", headers=auth).json()
    me_id = team[0]["id"]

    # Relatie: primaire accounthouder + extra teamleden (M2M)
    org = client.post("/api/crm/organisaties", headers=auth, json={
        "soort": "RSO", "naam": "RSO Team", "accounthouder_id": me_id,
        "extra_accounthouder_ids": [me_id],
    }).json()
    assert org["accounthouder"]["id"] == me_id
    assert [u["id"] for u in org["extra_accounthouders"]] == [me_id]
    assert org["extra_accounthouder_ids"] == [me_id]

    # Extra leeghalen mag; primair blijft
    upd = client.patch(f"/api/crm/organisaties/{org['id']}", headers=auth, json={
        "soort": "RSO", "naam": "RSO Team", "accounthouder_id": me_id,
        "extra_accounthouder_ids": [],
    }).json()
    assert upd["extra_accounthouders"] == []
    assert upd["accounthouder"]["id"] == me_id

    # Contactpersoon: eigen primaire accounthouder + extra
    cp = client.post("/api/crm/contactpersonen", headers=auth, json={
        "naam": "Contact Test", "organisatie_id": org["id"],
        "accounthouder_id": me_id, "extra_accounthouder_ids": [me_id],
    }).json()
    assert cp["accounthouder"]["id"] == me_id
    assert [u["id"] for u in cp["extra_accounthouders"]] == [me_id]

    # Onbekende/niet-tenant-eigen ID's worden stil genegeerd
    cp2 = client.patch(f"/api/crm/contactpersonen/{cp['id']}", headers=auth, json={
        "naam": "Contact Test",
        "extra_accounthouder_ids": ["00000000-0000-0000-0000-000000000000"],
    }).json()
    assert cp2["extra_accounthouders"] == []
