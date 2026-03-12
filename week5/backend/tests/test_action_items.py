from concurrent.futures import ThreadPoolExecutor

import pytest


def _create_action_item(client, description: str = "Ship it") -> dict:
    response = client.post("/action-items/", json={"description": description})
    assert response.status_code == 201, response.text
    return response.json()


def _post_bulk_complete(client, item_ids: list[int]):
    return client.post("/action-items/bulk-complete", json=item_ids)


def _require_bulk_endpoint(client) -> None:
    probe = _post_bulk_complete(client, [])
    if probe.status_code == 404:
        pytest.skip("bulk-complete endpoint is not implemented in this week5 codebase")


def test_create_and_complete_action_item(client):
    item = _create_action_item(client)
    assert item["completed"] is False

    response = client.put(f"/action-items/{item['id']}/complete")
    assert response.status_code == 200
    done = response.json()
    assert done["completed"] is True

    response = client.get("/action-items/")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["completed"] is True


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"description": None},
    ],
)
def test_create_action_item_rejects_invalid_payload(client, payload):
    response = client.post("/action-items/", json=payload)
    assert response.status_code in {400, 422}


def test_complete_action_item_returns_404_for_unknown_id(client):
    response = client.put("/action-items/999999/complete")
    assert response.status_code == 404
    assert response.json()["detail"] == "Action item not found"


def test_complete_action_item_rejects_non_integer_id(client):
    response = client.put("/action-items/not-an-int/complete")
    assert response.status_code in {400, 422}


def test_complete_action_item_handles_concurrent_retries(client):
    item = _create_action_item(client, description="concurrent retry")
    item_id = item["id"]

    def complete_once() -> int:
        return client.put(f"/action-items/{item_id}/complete").status_code

    with ThreadPoolExecutor(max_workers=6) as executor:
        statuses = list(executor.map(lambda _: complete_once(), range(12)))

    assert statuses
    assert all(status == 200 for status in statuses)

    response = client.get("/action-items/")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["completed"] is True


def test_bulk_complete_rolls_back_on_invalid_id(client):
    _require_bulk_endpoint(client)

    first = _create_action_item(client, description="first")
    second = _create_action_item(client, description="second")

    response = _post_bulk_complete(client, [first["id"], second["id"], 999999])
    assert response.status_code in {400, 404, 422}

    items_response = client.get("/action-items/")
    assert items_response.status_code == 200
    items_by_id = {item["id"]: item for item in items_response.json()}
    assert items_by_id[first["id"]]["completed"] is False
    assert items_by_id[second["id"]]["completed"] is False


def test_bulk_complete_is_stable_under_concurrent_requests(client):
    _require_bulk_endpoint(client)

    ids = [_create_action_item(client, description=f"bulk-{i}")["id"] for i in range(6)]
    batches = [
        ids[0:4],
        ids[2:6],
        ids[1:5],
    ]

    def complete_batch(batch: list[int]) -> int:
        return _post_bulk_complete(client, batch).status_code

    with ThreadPoolExecutor(max_workers=3) as executor:
        statuses = list(executor.map(complete_batch, batches))

    assert statuses
    assert all(200 <= status < 300 for status in statuses)

    items_response = client.get("/action-items/")
    assert items_response.status_code == 200
    items_by_id = {item["id"]: item for item in items_response.json()}
    for item_id in ids:
        assert items_by_id[item_id]["completed"] is True
