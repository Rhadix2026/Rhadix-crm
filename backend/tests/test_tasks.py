"""test_tasks.py — basistests voor de geporte taken-/workflowmodule in CRM."""


def test_summary_leeg(client, auth):
    s = client.get("/api/tasks/summary", headers=auth).json()
    assert s["mine_open"] == 0
    assert "tenant_open" in s  # admin ziet tenant-telling


def test_assignable_users_bevat_admin(client, auth):
    users = client.get("/api/tasks/assignable-users", headers=auth).json()
    assert any(u["email"] == "admin@rhadix.nl" for u in users)


def test_aanmaken_en_lijst(client, auth):
    me = client.get("/api/auth/me", headers=auth).json()
    created = client.post("/api/tasks", headers=auth, json={
        "title": "Bel bestuurder X",
        "priority": "HOOG",
        "assignee_id": me["id"],
        "source_type": "crm_organisatie",
        "source_label": "Zorgaanbieder X",
    })
    assert created.status_code == 201, created.text
    t = created.json()
    assert t["title"] == "Bel bestuurder X"
    assert t["priority"] == "HOOG"
    assert t["app_slug"] == "rhadix-crm"

    mine = client.get("/api/tasks?scope=mine", headers=auth).json()
    assert any(x["id"] == t["id"] for x in mine)

    s = client.get("/api/tasks/summary", headers=auth).json()
    assert s["mine_open"] >= 1


def test_status_en_verwijderen(client, auth):
    t = client.post("/api/tasks", headers=auth, json={"title": "Afronden dossier"}).json()
    upd = client.patch(f"/api/tasks/{t['id']}", headers=auth, json={"status": "KLAAR"}).json()
    assert upd["status"] == "KLAAR"
    assert upd["completed_at"] is not None
    assert client.delete(f"/api/tasks/{t['id']}", headers=auth).status_code == 204


def test_bulk_aanmaken(client, auth):
    me = client.get("/api/auth/me", headers=auth).json()
    res = client.post("/api/tasks/bulk", headers=auth, json={
        "assignee_id": me["id"],
        "source_type": "crm_actie",
        "items": [{"title": "Taak A"}, {"title": "Taak B", "priority": "HOOG"}],
    })
    assert res.status_code == 201, res.text
    assert res.json()["created"] == 2


def test_ongeldige_assignee_buiten_tenant(client, auth):
    import uuid
    r = client.post("/api/tasks", headers=auth, json={
        "title": "Mag niet", "assignee_id": str(uuid.uuid4())})
    assert r.status_code == 400
