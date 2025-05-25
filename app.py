import streamlit as st
import requests
import feedparser
from datetime import datetime
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from telegram import Bot
import json
import os

# --- Config ---
MOROCCO_CITIES = ["Rabat", "Casablanca", "Marrakech", "Fès", "Agadir", "Tanger", "Oujda"]
ALERT_KEYWORDS = [
    "manifestation", "protestation", "émeute", "sécurité", "attaque", "barricade",
    "météo", "tempête", "inondation", "tremblement", "séisme", "alerte", "catastrophe"
]

SEVERITY_KEYWORDS = {
    "Haute": ["attaque", "séisme", "tremblement", "catastrophe", "émeute"],
    "Moyenne": ["inondation", "tempête", "barricade", "manifestation"],
    "Basse": ["alerte", "sécurité", "protestation", "météo"]
}

RSS_FEEDS = {
    "Hespress": "https://www.hespress.com/feed",
    "Le360": "https://www.le360.ma/rss",
    "Media24": "https://medias24.com/feed",
    "ReliefWeb": "https://reliefweb.int/feeds/updates?country=127"
}

TELEGRAM_TOKEN = "7863887117:AAFc28s1TEvjHmBsBp_0OWFa1ZNqO906MZ0"
TELEGRAM_CHAT_ID = "5342551863"
HISTORY_FILE = "alert_history.json"

geolocator = Nominatim(user_agent="morocco_alerts")
bot = Bot(token=TELEGRAM_TOKEN)

# --- Helper Functions ---
def detect_severity(text):
    text = text.lower()
    for level, keywords in SEVERITY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return level
    return "Non classée"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as file:
            return json.load(file)
    return []

def save_to_history(alert):
    history = load_history()
    history.append(alert)
    with open(HISTORY_FILE, 'w') as file:
        json.dump(history, file, indent=2)

def fetch_articles():
    alerts = []
    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            published = entry.get("published", str(datetime.now()))
            location = None
            for city in MOROCCO_CITIES:
                if city.lower() in (title + summary).lower():
                    location = city
                    break
            if any(kw in title.lower() + summary.lower() for kw in ALERT_KEYWORDS):
                severity = detect_severity(title + " " + summary)
                alert = {
                    "Source": source,
                    "Title": title,
                    "Link": link,
                    "Published": published,
                    "Summary": summary,
                    "City": location,
                    "Severity": severity
                }
                alerts.append(alert)
                save_to_history(alert)
                if severity == "Haute":
                    send_telegram_alert(alert)
    return alerts

def send_telegram_alert(alert):
    message = f"🛑 *{alert['Source']}*\n*{alert['Title']}*\n📍 {alert['City'] or 'Ville inconnue'}\n🔴 Gravité : *{alert['Severity']}*\n🔗 [Voir l'article]({alert['Link']})"
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        print(f"Erreur d'envoi Telegram : {e}")

def get_coordinates(city_name):
    try:
        location = geolocator.geocode(f"{city_name}, Morocco")
        if location:
            return location.latitude, location.longitude
    except:
        return None, None
    return None, None

# --- Streamlit App ---
st.set_page_config(page_title="Morocco Alert System", layout="wide")
st.title("🛡️ Morocco Public Alert Dashboard")
st.markdown("Get live alerts about **protests**, **weather events**, **security breaches**, and **disasters** across Morocco.")

if st.button("📤 Envoyer une alerte test Telegram"):
    test_alert = {
        "Source": "TEST",
        "Title": "Alerte Test Fonctionnelle",
        "Link": "https://example.com",
        "Published": str(datetime.now()),
        "Summary": "Ceci est un test d'envoi de notification Telegram.",
        "City": "Rabat",
        "Severity": "Haute"
    }
    send_telegram_alert(test_alert)
    st.success("Alerte test envoyée sur Telegram ✅")

with st.spinner("Fetching alerts..."):
    data = fetch_articles()

if not data:
    st.warning("No alerts found at the moment.")
else:
    df = pd.DataFrame(data)
    df["Published"] = pd.to_datetime(df["Published"], errors='coerce')
    df = df.sort_values(by="Published", ascending=False)

    with st.expander("🔍 Filter alerts"):
        city_filter = st.multiselect("Filter by city:", MOROCCO_CITIES)
        severity_filter = st.multiselect("Filter by severity:", ["Haute", "Moyenne", "Basse", "Non classée"])
        if city_filter:
            df = df[df["Summary"].str.contains('|'.join(city_filter), case=False) | df["Title"].str.contains('|'.join(city_filter), case=False)]
        if severity_filter:
            df = df[df["Severity"].isin(severity_filter)]

    st.dataframe(df[["Published", "Severity", "Title", "Source", "Link"]], use_container_width=True)

    st.markdown("### 📊 Alert Statistics")
    stat_df = df.groupby(["City", "Severity"]).size().reset_index(name='Count')
    st.dataframe(stat_df)

    st.markdown("### 🗺️ Alerts Map")
    morocco_map = folium.Map(location=[31.7917, -7.0926], zoom_start=5.5)
    for _, row in df.iterrows():
        if row["City"]:
            lat, lon = get_coordinates(row["City"])
            if lat and lon:
                folium.Marker(
                    location=[lat, lon],
                    popup=f"{row['Title']}<br><a href='{row['Link']}' target='_blank'>View</a>",
                    tooltip=f"{row['City']} - {row['Severity']}"
                ).add_to(morocco_map)
    st_data = st_folium(morocco_map, width=800, height=500)

    st.markdown("---")
    st.caption("⚠️ This tool uses public RSS feeds and keyword matching. For official emergency alerts, always refer to government authorities.")
