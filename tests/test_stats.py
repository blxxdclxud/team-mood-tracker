"""Unit tests for the /stats analytics endpoints."""

from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient


HAPPY = {"user": "alice", "mood": "happy", "comment": ""}
STRESSED = {"user": "bob", "mood": "stressed", "comment": ""}
NEUTRAL = {"user": "carol", "mood": "neutral", "comment": ""}


def _seed(client: TestClient) -> None:
    """Create a small set of mood entries for statistics tests."""
    for payload in [HAPPY, STRESSED, NEUTRAL, HAPPY]:
        client.post("/moods/", json=payload)


def _utc_today_iso() -> str:
    """Return current date in UTC as ISO string."""
    return datetime.now(timezone.utc).date().isoformat()


class TestDailyTrends:
    """Tests for GET /stats/daily."""

    def test_returns_200(self, client: TestClient) -> None:
        """Daily trends endpoint must return HTTP 200."""
        resp = client.get("/stats/daily")
        assert resp.status_code == 200

    def test_returns_list(self, client: TestClient) -> None:
        """Response must be a JSON list."""
        resp = client.get("/stats/daily")
        assert isinstance(resp.json(), list)

    def test_data_appears_after_seeding(self, client: TestClient) -> None:
        """After seeding entries, daily stats must be non-empty."""
        _seed(client)
        resp = client.get("/stats/daily", params={"days": 30})
        assert len(resp.json()) >= 1

    def test_stat_fields_present(self, client: TestClient) -> None:
        """Each daily stat item must contain date, average_rating, entry_count."""
        _seed(client)
        items = client.get("/stats/daily").json()
        for item in items:
            assert "date" in item
            assert "average_rating" in item
            assert "entry_count" in item

    def test_days_param_accepted(self, client: TestClient) -> None:
        """The days query parameter must be accepted without error."""
        resp = client.get("/stats/daily", params={"days": 7})
        assert resp.status_code == 200

    def test_days_param_validation(self, client: TestClient) -> None:
        """A days value of 0 must be rejected with HTTP 422."""
        resp = client.get("/stats/daily", params={"days": 0})
        assert resp.status_code == 422


class TestAggregateStats:
    """Tests for GET /stats/aggregate."""

    def test_returns_200(self, client: TestClient) -> None:
        """Aggregate stats endpoint must return HTTP 200 for a valid date range."""
        today = _utc_today_iso()
        resp = client.get("/stats/aggregate", params={"start_date": today, "end_date": today})
        assert resp.status_code == 200

    def test_response_fields(self, client: TestClient) -> None:
        """Response must contain all required aggregate fields."""
        today = _utc_today_iso()
        body = client.get(
            "/stats/aggregate", params={"start_date": today, "end_date": today}
        ).json()
        assert "average_rating" in body
        assert "entry_count" in body
        assert "mood_distribution" in body
        assert "start_date" in body
        assert "end_date" in body

    def test_average_rating_with_entries(self, client: TestClient) -> None:
        """Average rating must be a positive float after seeding entries."""
        _seed(client)
        today = _utc_today_iso()
        body = client.get(
            "/stats/aggregate", params={"start_date": today, "end_date": today}
        ).json()
        # happy=4, stressed=1, neutral=3, happy=4 → mean=3.0
        assert body["average_rating"] == 3.0

    def test_empty_period_returns_zero_average(self, client: TestClient) -> None:
        """A period with no entries must return average_rating=0 and entry_count=0."""
        past = (date.today() - timedelta(days=365)).isoformat()
        body = client.get(
            "/stats/aggregate", params={"start_date": past, "end_date": past}
        ).json()
        assert body["entry_count"] == 0
        assert body["average_rating"] == 0.0

    def test_missing_start_date_returns_422(self, client: TestClient) -> None:
        """Omitting start_date must return HTTP 422."""
        resp = client.get("/stats/aggregate", params={"end_date": date.today().isoformat()})
        assert resp.status_code == 422

    def test_mood_distribution_keys(self, client: TestClient) -> None:
        """Mood distribution must contain all five mood keys."""
        today = _utc_today_iso()
        body = client.get(
            "/stats/aggregate", params={"start_date": today, "end_date": today}
        ).json()
        expected_keys = {"happy", "neutral", "stressed", "sad", "excited"}
        assert expected_keys == set(body["mood_distribution"].keys())


class TestMoodDistribution:
    """Tests for GET /stats/distribution."""

    def test_returns_200(self, client: TestClient) -> None:
        """Distribution endpoint must return HTTP 200."""
        resp = client.get("/stats/distribution")
        assert resp.status_code == 200

    def test_all_time_scope(self, client: TestClient) -> None:
        """Without a date filter, scope must be 'all-time'."""
        body = client.get("/stats/distribution").json()
        assert body["scope"] == "all-time"

    def test_day_scope(self, client: TestClient) -> None:
        """With a date filter, scope must equal that date's ISO string."""
        today = _utc_today_iso()
        body = client.get("/stats/distribution", params={"target_date": today}).json()
        assert body["scope"] == today

    def test_distribution_contains_all_moods(self, client: TestClient) -> None:
        """Distribution dict must contain all five mood keys."""
        body = client.get("/stats/distribution").json()
        expected = {"happy", "neutral", "stressed", "sad", "excited"}
        assert expected == set(body["distribution"].keys())

    def test_distribution_counts_after_seeding(self, client: TestClient) -> None:
        """Submitted entries must be reflected in the all-time distribution."""
        _seed(client)
        body = client.get("/stats/distribution").json()
        dist = body["distribution"]
        assert dist["happy"] >= 2
        assert dist["stressed"] >= 1
        assert dist["neutral"] >= 1


class TestHealthCheck:
    """Tests for GET /health."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        """Health endpoint must return {status: ok}."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

