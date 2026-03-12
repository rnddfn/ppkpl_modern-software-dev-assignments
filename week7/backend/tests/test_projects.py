def test_create_project_and_link_related_entities(client):
    r = client.post("/projects/", json={"name": "Launch", "description": "Release prep"})
    assert r.status_code == 201, r.text
    project = r.json()

    r = client.post(
        "/notes/",
        json={
            "title": "Kickoff",
            "content": "Plan milestones",
            "project_id": project["id"],
        },
    )
    assert r.status_code == 201, r.text
    note = r.json()
    assert note["project_id"] == project["id"]

    r = client.post(
        "/action-items/",
        json={"description": "Prepare release checklist", "project_id": project["id"]},
    )
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["project_id"] == project["id"]

    r = client.get(f"/projects/{project['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == project["id"]
    assert len(data["notes"]) == 1
    assert len(data["action_items"]) == 1
    assert data["notes"][0]["id"] == note["id"]
    assert data["action_items"][0]["id"] == item["id"]


def test_project_filters_and_delete_detaches_relationships(client):
    r = client.post("/projects/", json={"name": "Alpha"})
    assert r.status_code == 201
    alpha = r.json()

    r = client.post("/projects/", json={"name": "Beta"})
    assert r.status_code == 201
    beta = r.json()

    r = client.post("/notes/", json={"title": "A", "content": "AA", "project_id": alpha["id"]})
    assert r.status_code == 201
    alpha_note = r.json()

    r = client.post("/notes/", json={"title": "B", "content": "BB", "project_id": beta["id"]})
    assert r.status_code == 201
    beta_note = r.json()

    r = client.post(
        "/action-items/",
        json={"description": "Alpha task", "project_id": alpha["id"]},
    )
    assert r.status_code == 201
    alpha_item = r.json()

    r = client.get("/notes/", params={"project_id": alpha["id"]})
    assert r.status_code == 200
    notes = r.json()
    assert [n["id"] for n in notes] == [alpha_note["id"]]

    r = client.get("/action-items/", params={"project_id": alpha["id"]})
    assert r.status_code == 200
    items = r.json()
    assert [i["id"] for i in items] == [alpha_item["id"]]

    r = client.delete(f"/projects/{alpha['id']}")
    assert r.status_code == 204

    r = client.get(f"/notes/{alpha_note['id']}")
    assert r.status_code == 200
    assert r.json()["project_id"] is None

    r = client.get(f"/action-items/{alpha_item['id']}")
    assert r.status_code == 200
    assert r.json()["project_id"] is None

    r = client.get(f"/notes/{beta_note['id']}")
    assert r.status_code == 200
    assert r.json()["project_id"] == beta["id"]


def test_project_validation_and_relationship_errors(client):
    r = client.post("/projects/", json={"name": "   "})
    assert r.status_code == 422

    r = client.post("/projects/", json={"name": "Roadmap"})
    assert r.status_code == 201

    r = client.post("/projects/", json={"name": "Roadmap"})
    assert r.status_code == 409
    assert r.json() == {"detail": "Project with this name already exists"}

    r = client.get("/projects/", params={"sort": "-nope"})
    assert r.status_code == 400
    assert "Invalid sort field 'nope'" in r.json()["detail"]

    r = client.patch("/projects/999", json={})
    assert r.status_code == 422

    r = client.post(
        "/notes/",
        json={"title": "Invalid link", "content": "No project", "project_id": 999},
    )
    assert r.status_code == 404
    assert r.json() == {"detail": "Project not found"}

    r = client.post("/action-items/", json={"description": "Missing project", "project_id": 999})
    assert r.status_code == 404
    assert r.json() == {"detail": "Project not found"}
