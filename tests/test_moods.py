"""Unit tests for the /moods CRUD endpoints."""

import pytest
from fastapi.testclient import TestClient


HAPPY_PAYLOAD = {"user": "alice", "mood": "happy", "comment": "Great day!"}
NEUTRAL_PAYLOAD = {"user": "bob", "mood": "neutral", "comment": ""}


class TestCreateMoodEntry:
    """Tests for POST /moods/."""

    def test_create_returns_201(self, client: TestClient) -> None:
        """Creating a valid entry must return HTTP 201."""
        resp = client.post("/moods/", json=HAPPY_PAYLOAD)
        assert resp.status_code == 201

    def test_create_response_fields(self, client: TestClient) -> None:
        """Response body must contain all expected fields with correct values."""
        resp = client.post("/moods/", json=HAPPY_PAYLOAD)
        body = resp.json()
        assert body["user"] == "alice"
        assert body["mood"] == "happy"
        assert body["rating"] == 4
        assert body["comment"] == "Great day!"
        assert "id" in body
        assert "created_at" in body

    def test_create_neutral_sets_rating_3(self, client: TestClient) -> None:
        """Neutral mood must result in rating=3."""
        resp = client.post("/moods/", json=NEUTRAL_PAYLOAD)
        assert resp.json()["rating"] == 3

    def test_create_stressed_sets_rating_1(self, client: TestClient) -> None:
        """Stressed mood must result in rating=1."""
        resp = client.post("/moods/", json={"user": "carol", "mood": "stressed", "comment": ""})
        assert resp.json()["rating"] == 1

    def test_create_excited_sets_rating_5(self, client: TestClient) -> None:
        """Excited mood must result in rating=5."""
        resp = client.post("/moods/", json={"user": "dan", "mood": "excited", "comment": ""})
        assert resp.json()["rating"] == 5

    def test_create_invalid_mood_returns_422(self, client: TestClient) -> None:
        """An invalid mood value must be rejected with HTTP 422."""
        resp = client.post("/moods/", json={"user": "alice", "mood": "furious", "comment": ""})
        assert resp.status_code == 422

    def test_create_empty_user_returns_422(self, client: TestClient) -> None:
        """An empty user string must be rejected with HTTP 422."""
        resp = client.post("/moods/", json={"user": "", "mood": "happy", "comment": ""})
        assert resp.status_code == 422


class TestGetMoodEntry:
    """Tests for GET /moods/{entry_id}."""

    def test_get_existing_entry(self, client: TestClient) -> None:
        """Getting an existing entry by id must return HTTP 200."""
        created = client.post("/moods/", json=HAPPY_PAYLOAD).json()
        resp = client.get(f"/moods/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_get_nonexistent_returns_404(self, client: TestClient) -> None:
        """Getting a non-existent entry must return HTTP 404."""
        resp = client.get("/moods/999999")
        assert resp.status_code == 404


class TestListMoodEntries:
    """Tests for GET /moods/."""

    def test_list_returns_200(self, client: TestClient) -> None:
        """Listing entries must return HTTP 200 and a list."""
        resp = client.get("/moods/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_contains_created_entry(self, client: TestClient) -> None:
        """A newly created entry must appear in the list."""
        client.post("/moods/", json=HAPPY_PAYLOAD)
        resp = client.get("/moods/")
        users = [e["user"] for e in resp.json()]
        assert "alice" in users

    def test_list_filter_by_user(self, client: TestClient) -> None:
        """User filter must restrict results to that user only."""
        client.post("/moods/", json=HAPPY_PAYLOAD)
        client.post("/moods/", json=NEUTRAL_PAYLOAD)
        resp = client.get("/moods/", params={"user": "alice"})
        entries = resp.json()
        assert all(e["user"] == "alice" for e in entries)

    def test_list_filter_by_mood(self, client: TestClient) -> None:
        """Mood filter must restrict results to that mood only."""
        client.post("/moods/", json=HAPPY_PAYLOAD)
        client.post("/moods/", json=NEUTRAL_PAYLOAD)
        resp = client.get("/moods/", params={"mood": "happy"})
        entries = resp.json()
        assert all(e["mood"] == "happy" for e in entries)

    def test_list_pagination(self, client: TestClient) -> None:
        """Limit and skip parameters must correctly paginate results."""
        for _ in range(5):
            client.post("/moods/", json=HAPPY_PAYLOAD)
        resp = client.get("/moods/", params={"limit": 2, "skip": 0})
        assert len(resp.json()) <= 2


class TestUpdateMoodEntry:
    """Tests for PUT /moods/{entry_id}."""

    def test_update_mood(self, client: TestClient) -> None:
        """Updating the mood field must reflect in the response."""
        created = client.post("/moods/", json=HAPPY_PAYLOAD).json()
        resp = client.put(f"/moods/{created['id']}", json={"mood": "stressed"})
        assert resp.status_code == 200
        assert resp.json()["mood"] == "stressed"
        assert resp.json()["rating"] == 1

    def test_update_comment(self, client: TestClient) -> None:
        """Updating only the comment must not change the mood."""
        created = client.post("/moods/", json=HAPPY_PAYLOAD).json()
        resp = client.put(f"/moods/{created['id']}", json={"comment": "Updated!"})
        assert resp.json()["comment"] == "Updated!"
        assert resp.json()["mood"] == "happy"

    def test_update_nonexistent_returns_404(self, client: TestClient) -> None:
        """Updating a non-existent entry must return HTTP 404."""
        resp = client.put("/moods/999999", json={"mood": "happy"})
        assert resp.status_code == 404


class TestDeleteMoodEntry:
    """Tests for DELETE /moods/{entry_id}."""

    def test_delete_existing_returns_204(self, client: TestClient) -> None:
        """Deleting an existing entry must return HTTP 204."""
        created = client.post("/moods/", json=HAPPY_PAYLOAD).json()
        resp = client.delete(f"/moods/{created['id']}")
        assert resp.status_code == 204

    def test_delete_removes_entry(self, client: TestClient) -> None:
        """After deletion, fetching the entry must return 404."""
        created = client.post("/moods/", json=HAPPY_PAYLOAD).json()
        client.delete(f"/moods/{created['id']}")
        resp = client.get(f"/moods/{created['id']}")
        assert resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, client: TestClient) -> None:
        """Deleting a non-existent entry must return HTTP 404."""
        resp = client.delete("/moods/999999")
        assert resp.status_code == 404
