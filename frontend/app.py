"""Streamlit dashboard for Team Mood Tracker."""

from datetime import date, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

API_BASE = "http://localhost:8000"

MOOD_EMOJI: dict[str, str] = {
    "excited": "🤩",
    "happy": "😊",
    "neutral": "😐",
    "sad": "😢",
    "stressed": "😤",
}

MOOD_OPTIONS = list(MOOD_EMOJI.keys())


def submit_mood(user: str, mood: str, comment: str) -> bool:
    """POST a new mood entry to the API and return True on success."""
    resp = requests.post(
        f"{API_BASE}/moods/",
        json={"user": user, "mood": mood, "comment": comment},
        timeout=10,
    )
    return resp.status_code == 201


def fetch_daily_trends(days: int) -> pd.DataFrame:
    """Fetch per-day mood statistics from the API as a DataFrame."""
    resp = requests.get(f"{API_BASE}/stats/daily", params={"days": days}, timeout=10)
    if resp.status_code != 200:
        return pd.DataFrame()
    data = resp.json()
    return pd.DataFrame(data) if data else pd.DataFrame()


def fetch_aggregate_stats(start: date, end: date) -> dict | None:
    """Fetch aggregate mood stats for the given period; return None on error."""
    resp = requests.get(
        f"{API_BASE}/stats/aggregate",
        params={"start_date": start.isoformat(), "end_date": end.isoformat()},
        timeout=10,
    )
    if resp.status_code != 200:
        return None
    return resp.json()  # type: ignore[no-any-return]


def fetch_distribution(target_date: date | None) -> dict | None:
    """Fetch mood distribution data; return None on error."""
    params: dict[str, str] = {}
    if target_date:
        params["target_date"] = target_date.isoformat()
    resp = requests.get(
        f"{API_BASE}/stats/distribution", params=params, timeout=10
    )
    if resp.status_code != 200:
        return None
    return resp.json()  # type: ignore[no-any-return]


def fetch_entries(user: str | None, mood: str | None) -> pd.DataFrame:
    """Fetch raw mood entries from the API with optional filters."""
    params: dict[str, str] = {"limit": "200"}
    if user:
        params["user"] = user
    if mood:
        params["mood"] = mood
    resp = requests.get(f"{API_BASE}/moods/", params=params, timeout=10)
    if resp.status_code != 200:
        return pd.DataFrame()
    data = resp.json()
    return pd.DataFrame(data) if data else pd.DataFrame()


def render_submission_tab() -> None:
    """Render the mood submission form."""
    st.header("Submit Your Mood")
    user = st.text_input("Your name", max_chars=64)
    mood = st.selectbox(
        "How are you feeling?",
        MOOD_OPTIONS,
        format_func=lambda m: f"{MOOD_EMOJI[m]} {m.capitalize()}",
    )
    comment = st.text_area("Comment (optional)", max_chars=500)
    if st.button("Submit", type="primary"):
        if not user.strip():
            st.error("Please enter your name.")
        else:
            ok = submit_mood(user.strip(), str(mood), comment)
            if ok:
                st.success(f"Mood submitted! {MOOD_EMOJI[str(mood)]}")
            else:
                st.error("Failed to submit mood. Is the backend running?")


def render_history_tab() -> None:
    """Render the historical mood trend chart."""
    st.header("Historical Mood Trends")
    days = st.slider("Days to show", min_value=1, max_value=90, value=30)
    df = fetch_daily_trends(days)
    if df.empty:
        st.info("No data yet.")
        return
    df["date"] = pd.to_datetime(df["date"])
    st.line_chart(df.set_index("date")["average_rating"], use_container_width=True)
    st.caption("Average mood rating per day (1 = stressed → 5 = excited)")
    st.dataframe(df.rename(columns={"date": "Date", "average_rating": "Avg Rating", "entry_count": "Entries"}))


def render_stats_tab() -> None:
    """Render the aggregate statistics panel."""
    st.header("Aggregate Statistics")
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("From", value=date.today() - timedelta(days=7))
    with col2:
        end = st.date_input("To", value=date.today())
    stats = fetch_aggregate_stats(start, end)  # type: ignore[arg-type]
    if stats is None:
        st.error("Could not load statistics.")
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Rating", f"{stats['average_rating']:.2f} / 5")
    c2.metric("Total Entries", stats["entry_count"])
    period_days = (end - start).days + 1  # type: ignore[operator]
    c3.metric("Period (days)", period_days)
    st.subheader("Mood distribution for period")
    dist = stats.get("mood_distribution", {})
    if any(dist.values()):
        fig, ax = plt.subplots()
        labels = [f"{MOOD_EMOJI.get(k, '')} {k}" for k in dist]
        ax.bar(labels, list(dist.values()), color="steelblue")
        ax.set_ylabel("Count")
        ax.set_title("Mood Distribution")
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("No entries in this period.")


def render_barplots_tab() -> None:
    """Render barplot visualisations for mood distribution."""
    st.header("Mood Distribution Barplots")
    tab_day, tab_all = st.tabs(["By Day", "All Time"])
    with tab_day:
        target = st.date_input("Select date", value=date.today(), key="dist_day")
        data = fetch_distribution(target)  # type: ignore[arg-type]
        if data:
            _plot_distribution(data["distribution"], f"Mood on {target}")
        else:
            st.info("No data for selected date.")
    with tab_all:
        data = fetch_distribution(None)
        if data:
            _plot_distribution(data["distribution"], "All-Time Mood Distribution")
        else:
            st.info("No data yet.")


def _plot_distribution(distribution: dict[str, int], title: str) -> None:
    """Render a matplotlib bar chart for the given mood distribution dict."""
    labels = [f"{MOOD_EMOJI.get(k, '')} {k}" for k in distribution]
    values = list(distribution.values())
    fig, ax = plt.subplots()
    ax.bar(labels, values, color=["#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#F44336"])
    ax.set_ylabel("Number of entries")
    ax.set_title(title)
    st.pyplot(fig)
    plt.close(fig)


def render_entries_tab() -> None:
    """Render the raw entries browser with optional filters."""
    st.header("Browse Entries")
    col1, col2 = st.columns(2)
    with col1:
        user_filter = st.text_input("Filter by user", key="ef_user")
    with col2:
        mood_filter = st.selectbox("Filter by mood", ["(all)"] + MOOD_OPTIONS, key="ef_mood")
    mood_val = None if mood_filter == "(all)" else mood_filter
    df = fetch_entries(user_filter or None, mood_val)
    if df.empty:
        st.info("No entries found.")
    else:
        st.dataframe(df, use_container_width=True)


def main() -> None:
    """Entry point — configure Streamlit page and render all tabs."""
    st.set_page_config(page_title="Team Mood Tracker", page_icon="😊", layout="wide")
    st.title("Team Mood Tracker 😊")
    tabs = st.tabs(["Submit Mood", "History", "Statistics", "Barplots", "All Entries"])
    with tabs[0]:
        render_submission_tab()
    with tabs[1]:
        render_history_tab()
    with tabs[2]:
        render_stats_tab()
    with tabs[3]:
        render_barplots_tab()
    with tabs[4]:
        render_entries_tab()


if __name__ == "__main__":
    main()
