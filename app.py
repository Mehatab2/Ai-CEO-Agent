import json
from pathlib import Path

import pandas as pd
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

st.set_page_config(page_title="SAP Strategic Intelligence Dashboard", layout="wide")

COMPANY_NAME = "SAP"
INDUSTRY = "Enterprise Software / Cloud ERP"

DATA_DIR = Path(__file__).parent / "notebook" / "data"


def load_json(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


@st.cache_data
def load_clean_data():
    df = pd.read_json(DATA_DIR / "clean_data.json")
    df["published"] = pd.to_datetime(df["published"], errors="coerce", utc=True, format="mixed")
    return df


@st.cache_data
def score_sentiment(df):
    analyzer = SentimentIntensityAnalyzer()
    texts = (df["title"].fillna("") + ". " + df["clean_text"].fillna("").str.slice(0, 500))
    scores = [analyzer.polarity_scores(t)["compound"] for t in texts]

    df = df.copy()
    df["sentiment_score"] = scores
    df["sentiment_label"] = pd.cut(
        df["sentiment_score"],
        bins=[-1, -0.05, 0.05, 1],
        labels=["Negative", "Neutral", "Positive"],
    )
    return df


clean_df = load_clean_data()
opportunities = load_json("opportunities.json")
risks = load_json("risks.json")
trends = load_json("trends.json")
competitors = load_json("competitor_activity.json")
recommendations = load_json("recommendations.json")
briefing = load_json("ceo_briefing.json")

st.title(f"{COMPANY_NAME} — AI CEO Strategic Intelligence Dashboard")
st.caption('"If you were the CEO today, what would you do next and why?"')

# ============================================================
# Section 1: Company Overview
# ============================================================
st.header("1. Company Overview")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Company", COMPANY_NAME)
col2.metric("Industry", INDUSTRY)
col3.metric("Documents Collected", len(clean_df))

n_sources = clean_df["source"].nunique()
col4.metric("Data Sources", n_sources)
col4.caption("16 outlets across 3 collection channels: SAP News RSS, GNews API, Hacker News API")

last_update = clean_df["published"].max()
last_update_str = last_update.strftime("%Y-%m-%d") if pd.notna(last_update) else "Unknown"
col5.metric("Last Update", last_update_str)

st.divider()

# ============================================================
# Section 2: Market Intelligence
# ============================================================
st.header("2. Market Intelligence")

tab1, tab2, tab3, tab4 = st.tabs(["Recent News", "Competitor Activity", "Emerging Tech", "SAP Announcements"])

with tab1:
    recent = clean_df.sort_values("published", ascending=False, na_position="last").head(10)
    for _, row in recent.iterrows():
        date_str = row["published"].strftime("%Y-%m-%d") if pd.notna(row["published"]) else "date unknown"
        st.markdown(f"**{row['title']}**")
        st.caption(f"{row['source']} · {date_str}")

with tab2:
    if not competitors:
        st.info("No competitor data yet - run agents/04_competitor_monitor.ipynb")
    else:
        for c in competitors:
            if c.get("mention_count", 0) > 0:
                st.markdown(f"**{c['competitor']}** ({c['mention_count']} mentions)")
                st.write(c.get("summary", ""))
                st.write("")
        zero_hit = [c["competitor"] for c in competitors if c.get("mention_count", 0) == 0]
        if zero_hit:
            st.caption(f"No recent activity detected for: {', '.join(zero_hit)}")

with tab3:
    if not trends:
        st.info("No trend data yet - run agents/03_trend_agent.ipynb")
    else:
        for t in trends:
            st.markdown(f"**{t.get('title')}** _{t.get('category')}_")
            st.write(t.get("description", ""))
            st.write("")

with tab4:
    announcements = clean_df[clean_df["source"] == "SAP News"].sort_values(
        "published", ascending=False, na_position="last"
    ).head(5)
    for _, row in announcements.iterrows():
        st.write(f"- {row['title']}")

st.divider()

# ============================================================
# Section 3: Opportunity Monitor
# ============================================================
st.header("3. Opportunity Monitor")

if not opportunities:
    st.info("No opportunity data yet - run agents/01_opportunity_agent.ipynb")
else:
    for o in opportunities:
        with st.container(border=True):
            st.subheader(o.get("title"))
            col1, col2 = st.columns(2)
            col1.write(f"**Impact Level:** {o.get('impact_level')}")
            col2.write(f"**Confidence Score:** {o.get('confidence_score')}")
            st.write(f"**Evidence:** {o.get('evidence')}")

st.divider()

# ============================================================
# Section 4: Risk Monitor
# ============================================================
st.header("4. Risk Monitor")

if not risks:
    st.info("No risk data yet - run agents/02_risk_agent.ipynb")
else:
    for r in risks:
        with st.container(border=True):
            st.subheader(r.get("title"))
            col1, col2, col3 = st.columns(3)
            col1.write(f"**Risk Category:** {r.get('risk_category')}")
            col2.write(f"**Severity Level:** {r.get('severity_level')}")
            col3.write(f"**Confidence Score:** {r.get('confidence_score')}")
            st.write(f"**Evidence:** {r.get('evidence')}")

st.divider()

# ============================================================
# Section 5: Sentiment Analysis
# ============================================================
st.header("5. Sentiment Analysis")
st.caption(
    "News sentiment = SAP News + press coverage. "
    "Public sentiment = Hacker News community discussion."
)

sentiment_df = score_sentiment(clean_df)
news_df = sentiment_df[sentiment_df["source"] != "Hacker News"]
public_df = sentiment_df[sentiment_df["source"] == "Hacker News"]

col1, col2 = st.columns(2)
with col1:
    st.subheader("News Sentiment")
    if len(news_df) > 0:
        st.metric("Average Score", f"{news_df['sentiment_score'].mean():.2f}")
        st.bar_chart(news_df["sentiment_label"].value_counts())
    else:
        st.write("No news articles found.")

with col2:
    st.subheader("Public Sentiment (Hacker News)")
    if len(public_df) > 0:
        st.metric("Average Score", f"{public_df['sentiment_score'].mean():.2f}")
        st.bar_chart(public_df["sentiment_label"].value_counts())
    else:
        st.write("No Hacker News articles found.")

st.subheader("Sentiment Trend Over Time")
trend_df = sentiment_df.dropna(subset=["published"]).copy()
if len(trend_df) > 0:
    trend_df["week"] = trend_df["published"].dt.tz_localize(None).dt.to_period("W").dt.start_time
    weekly_sentiment = trend_df.groupby("week")["sentiment_score"].mean()
    st.line_chart(weekly_sentiment)
else:
    st.write("Not enough dated articles to show a trend.")

st.divider()

# ============================================================
# Section 6: Strategic Recommendations
# ============================================================
st.header("6. Strategic Recommendations")

if not recommendations:
    st.info("No recommendations yet - run agents/05_ceo_agent.ipynb")
else:
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    sorted_recs = sorted(recommendations, key=lambda r: priority_order.get(r.get("priority"), 3))

    for r in sorted_recs:
        with st.container(border=True):
            st.subheader(r.get("recommendation"))
            col1, col2 = st.columns(2)
            col1.write(f"**Priority:** {r.get('priority')}")
            col2.write(f"**Risk Level:** {r.get('risk_level')}")
            st.write(f"**Expected Impact:** {r.get('expected_impact')}")
            st.write("**Supporting Evidence:**")
            for e in r.get("supporting_evidence", []):
                st.write(f"- {e}")

st.divider()

# ============================================================
# Section 7: CEO Briefing
# ============================================================
st.header("7. CEO Briefing")

if not briefing:
    st.info("No CEO briefing yet - run agents/05_ceo_agent.ipynb")
else:
    st.subheader("What happened?")
    st.write(briefing.get("what_happened", ""))

    st.subheader("Why does it matter?")
    st.write(briefing.get("why_it_matters", ""))

    st.subheader("What should management do next?")
    st.write(briefing.get("what_to_do_next", ""))
