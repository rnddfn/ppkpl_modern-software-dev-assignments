def test_create_list_and_patch_notes(client):
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"
    assert "created_at" in data and "updated_at" in data

    r = client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get("/notes/", params={"q": "Hello", "limit": 10, "sort": "-created_at"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get(f"/notes/{data['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == data["id"]

    note_id = data["id"]
    r = client.patch(f"/notes/{note_id}", json={"title": "Updated"})
    assert r.status_code == 200
    patched = r.json()
    assert patched["title"] == "Updated"

    r = client.delete(f"/notes/{note_id}")
    assert r.status_code == 204

    r = client.get(f"/notes/{note_id}")
    assert r.status_code == 404
    assert r.json() == {"detail": "Note not found"}


def test_note_validation_and_query_errors(client):
    r = client.post("/notes/", json={"title": "   ", "content": "Hello world"})
    assert r.status_code == 422

    r = client.post("/notes/", json={"title": "Valid", "content": "Hello", "extra": "nope"})
    assert r.status_code == 422

    r = client.patch("/notes/999", json={})
    assert r.status_code == 422

    r = client.get("/notes/", params={"sort": "-nope"})
    assert r.status_code == 400
    assert "Invalid sort field 'nope'" in r.json()["detail"]


