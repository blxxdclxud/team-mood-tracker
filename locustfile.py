import random

from locust import HttpUser, between, task


MOODS = ["happy", "neutral", "stressed", "sad", "excited"]
USERS = ["alice", "bob", "carol", "dan", "eve"]


class MoodTrackerUser(HttpUser):
    """Simulates a team member interacting with the Mood Tracker API."""

    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        """Seed one entry so read endpoints have data from the first request."""
        self.client.post(
            "/moods/",
            json={
                "user": random.choice(USERS),
                "mood": random.choice(MOODS),
                "comment": "load test seed",
            },
        )

    @task(3)
    def get_moods(self) -> None:
        """Fetch the mood entries list — highest weight as most common operation."""
        self.client.get("/moods/", params={"limit": 50})

    @task(2)
    def submit_mood(self) -> None:
        """Submit a new mood entry."""
        self.client.post(
            "/moods/",
            json={
                "user": random.choice(USERS),
                "mood": random.choice(MOODS),
                "comment": "Automated load test entry",
            },
        )

    @task(2)
    def daily_trends(self) -> None:
        """Fetch the daily mood trend statistics."""
        self.client.get("/stats/daily", params={"days": 30})

    @task(1)
    def distribution(self) -> None:
        """Fetch all-time mood distribution data."""
        self.client.get("/stats/distribution")

    @task(1)
    def health(self) -> None:
        """Ping the health endpoint."""
        self.client.get("/health")
