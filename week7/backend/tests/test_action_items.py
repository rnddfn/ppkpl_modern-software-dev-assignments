def test_create_complete_list_and_patch_action_item(client):
    payload = {"description": "Ship it"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["completed"] is False
    assert "created_at" in item and "updated_at" in item

    r = client.put(f"/action-items/{item['id']}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["completed"] is True

    r = client.get("/action-items/", params={"completed": True, "limit": 5, "sort": "-created_at"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get(f"/action-items/{item['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == item["id"]

    r = client.patch(f"/action-items/{item['id']}", json={"description": "Updated"})
    assert r.status_code == 200
    patched = r.json()
    assert patched["description"] == "Updated"

    r = client.put(f"/action-items/{item['id']}/reopen")
    assert r.status_code == 200
    reopened = r.json()
    assert reopened["completed"] is False

    r = client.delete(f"/action-items/{item['id']}")
    assert r.status_code == 204

    r = client.get(f"/action-items/{item['id']}")
    assert r.status_code == 404
    assert r.json() == {"detail": "Action item not found"}


def test_action_item_validation_and_query_errors(client):
    r = client.post("/action-items/", json={"description": "   "})
    assert r.status_code == 422

    r = client.post("/action-items/", json={"description": "Valid", "completed": True})
    assert r.status_code == 422

    r = client.patch("/action-items/999", json={})
    assert r.status_code == 422

    r = client.get("/action-items/", params={"sort": "unknown"})
    assert r.status_code == 400
    assert "Invalid sort field 'unknown'" in r.json()["detail"]


def test_action_items_sorting_and_pagination_with_filter(client):
    descriptions = ["Task C", "Task A", "Task B"]
    created = []
    for description in descriptions:
        r = client.post("/action-items/", json={"description": description})
        assert r.status_code == 201, r.text
        created.append(r.json())

    r = client.put(f"/action-items/{created[1]['id']}/complete")
    assert r.status_code == 200

    r = client.get("/action-items/", params={"sort": "description", "limit": 3})
    assert r.status_code == 200
    items = r.json()
    assert [item["description"] for item in items] == ["Task A", "Task B", "Task C"]

    r = client.get("/action-items/", params={"sort": "-description", "limit": 3})
    assert r.status_code == 200
    items = r.json()
    assert [item["description"] for item in items] == ["Task C", "Task B", "Task A"]

    r = client.get(
        "/action-items/",
        params={"completed": False, "sort": "id", "skip": 1, "limit": 1},
    )
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["description"] == "Task B"


def test_action_items_pagination_validation_errors(client):
    r = client.get("/action-items/", params={"skip": -1})
    assert r.status_code == 422

    r = client.get("/action-items/", params={"limit": 0})
    assert r.status_code == 422

    r = client.get("/action-items/", params={"limit": 201})
    assert r.status_code == 422


