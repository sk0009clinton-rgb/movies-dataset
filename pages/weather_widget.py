import requests
from datetime import datetime, timezone

import streamlit as st

st.set_page_config(
    page_title="Weather Widget",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# WMO weather-code → (label, emoji)
# ---------------------------------------------------------------------------
WMO_CODES = {
    0: ("Clear Sky", "☀️"),
    1: ("Mainly Clear", "🌤️"),
    2: ("Partly Cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Foggy", "🌫️"),
    48: ("Icy Fog", "🌫️"),
    51: ("Light Drizzle", "🌦️"),
    53: ("Drizzle", "🌦️"),
    55: ("Heavy Drizzle", "🌧️"),
    61: ("Light Rain", "🌧️"),
    63: ("Rain", "🌧️"),
    65: ("Heavy Rain", "🌧️"),
    71: ("Light Snow", "🌨️"),
    73: ("Snow", "❄️"),
    75: ("Heavy Snow", "❄️"),
    77: ("Snow Grains", "🌨️"),
    80: ("Light Showers", "🌦️"),
    81: ("Showers", "🌧️"),
    82: ("Heavy Showers", "⛈️"),
    85: ("Snow Showers", "🌨️"),
    86: ("Heavy Snow Showers", "❄️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm w/ Hail", "⛈️"),
    99: ("Thunderstorm w/ Heavy Hail", "⛈️"),
}

WIND_DIRS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def wind_direction_label(degrees: float) -> str:
    return WIND_DIRS[round(degrees / 45) % 8]


def wmo(code: int):
    return WMO_CODES.get(code, ("Unknown", "🌡️"))


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------
@st.cache_data(ttl=600)
def geocode(city: str):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    r = requests.get(url, params={"name": city, "count": 5, "language": "en", "format": "json"}, timeout=10)
    r.raise_for_status()
    return r.json().get("results", [])


@st.cache_data(ttl=600)
def fetch_weather(lat: float, lon: float, unit: str = "celsius"):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join([
            "temperature_2m", "relative_humidity_2m", "apparent_temperature",
            "is_day", "precipitation", "weather_code",
            "wind_speed_10m", "wind_direction_10m",
        ]),
        "daily": ",".join([
            "weather_code", "temperature_2m_max", "temperature_2m_min",
            "precipitation_sum", "wind_speed_10m_max",
        ]),
        "temperature_unit": unit,
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
        "timezone": "auto",
        "forecast_days": 7,
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Custom CSS — large TV-friendly dark theme
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
/* ---- TV dark base ---- */
html, body, [data-testid="stAppViewContainer"] {
    background: #0d1117 !important;
    color: #e6edf3 !important;
    font-family: 'Segoe UI', system-ui, sans-serif;
}
[data-testid="stSidebar"] { display: none; }
[data-testid="collapsedControl"] { display: none; }

/* ---- Main weather card ---- */
.weather-card {
    background: linear-gradient(135deg, #161b22 0%, #1c2634 100%);
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 2.5rem 3rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}
.city-name   { font-size: 2.4rem; font-weight: 700; color: #58a6ff; margin:0; }
.local-time  { font-size: 1.1rem; color: #8b949e; margin: 0.3rem 0 1.5rem; }
.temp-main   { font-size: 6rem; font-weight: 800; line-height: 1; color: #e6edf3; }
.temp-unit   { font-size: 2.5rem; vertical-align: super; color: #8b949e; }
.condition   { font-size: 1.8rem; margin-top: 0.3rem; color: #c9d1d9; }
.feels-like  { font-size: 1.1rem; color: #8b949e; margin-top: 0.4rem; }

/* ---- Stat tiles ---- */
.stat-grid { display: flex; gap: 1rem; margin-top: 2rem; flex-wrap: wrap; }
.stat-tile {
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 14px;
    padding: 1.2rem 1.6rem;
    min-width: 150px;
    flex: 1;
    text-align: center;
}
.stat-label { font-size: 0.85rem; color: #8b949e; text-transform: uppercase; letter-spacing: .06em; }
.stat-value { font-size: 1.8rem; font-weight: 700; color: #e6edf3; margin-top: 0.3rem; }
.stat-icon  { font-size: 1.6rem; }

/* ---- Forecast row ---- */
.forecast-row { display: flex; gap: 0.8rem; margin-top: 1rem; flex-wrap: wrap; }
.fc-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 14px;
    padding: 1rem;
    text-align: center;
    flex: 1;
    min-width: 100px;
}
.fc-day  { font-size: 0.85rem; color: #8b949e; font-weight: 600; }
.fc-icon { font-size: 2rem; margin: 0.5rem 0; }
.fc-hi   { font-size: 1.2rem; font-weight: 700; color: #e6edf3; }
.fc-lo   { font-size: 1rem; color: #8b949e; }

/* ---- Search input ---- */
.stTextInput input {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 10px !important;
    font-size: 1.2rem !important;
    padding: 0.6rem 1rem !important;
}
.stButton button {
    background: #1f6feb !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 1.1rem !important;
    padding: 0.5rem 1.5rem !important;
    font-weight: 600 !important;
}
.stSelectbox div[data-baseweb="select"] > div {
    background: #21262d !important;
    border-color: #30363d !important;
    color: #e6edf3 !important;
}
.stRadio label { color: #c9d1d9 !important; font-size: 1.05rem; }
div[data-testid="stHorizontalBlock"] { align-items: flex-end; }

/* ---- Refresh note ---- */
.refresh-note { font-size: 0.8rem; color: #484f58; text-align: right; margin-top: 0.5rem; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session-state defaults
# ---------------------------------------------------------------------------
if "city_query" not in st.session_state:
    st.session_state.city_query = "London"
if "selected_location" not in st.session_state:
    st.session_state.selected_location = None
if "unit" not in st.session_state:
    st.session_state.unit = "celsius"

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("## 🌤️ Live Weather Widget &nbsp;&nbsp;<small style='font-size:1rem;color:#8b949e;'>Clean OS TV</small>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Controls row
# ---------------------------------------------------------------------------
col_search, col_btn, col_unit = st.columns([4, 1, 2])

with col_search:
    city_input = st.text_input(
        "City",
        value=st.session_state.city_query,
        label_visibility="collapsed",
        placeholder="Search city…",
        key="city_input_field",
    )

with col_btn:
    search_clicked = st.button("Search")

with col_unit:
    unit_choice = st.radio(
        "Unit",
        ["°C", "°F"],
        index=0 if st.session_state.unit == "celsius" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.unit = "celsius" if unit_choice == "°C" else "fahrenheit"
    unit_sym = unit_choice

# ---------------------------------------------------------------------------
# Geocode & location picker
# ---------------------------------------------------------------------------
if search_clicked and city_input.strip():
    st.session_state.city_query = city_input.strip()
    st.session_state.selected_location = None
    st.cache_data.clear()

try:
    results = geocode(st.session_state.city_query)
except Exception as e:
    st.error(f"Geocoding failed: {e}")
    st.stop()

if not results:
    st.warning(f"No results found for **{st.session_state.city_query}**. Try a different spelling.")
    st.stop()

location_labels = [
    f"{r['name']}{', ' + r.get('admin1','') if r.get('admin1') else ''}, {r.get('country','')}"
    for r in results
]

if len(results) > 1 and st.session_state.selected_location is None:
    choice = st.selectbox("Select location", location_labels, label_visibility="collapsed")
    idx = location_labels.index(choice)
else:
    idx = 0

loc = results[idx]

# ---------------------------------------------------------------------------
# Fetch weather
# ---------------------------------------------------------------------------
try:
    data = fetch_weather(loc["latitude"], loc["longitude"], st.session_state.unit)
except Exception as e:
    st.error(f"Weather fetch failed: {e}")
    st.stop()

cur = data["current"]
daily = data["daily"]
tz_offset = data.get("utc_offset_seconds", 0)

now_local = datetime.now(timezone.utc).timestamp() + tz_offset
now_dt = datetime.utcfromtimestamp(now_local)
time_str = now_dt.strftime("%A, %d %b %Y  •  %H:%M")

label, emoji = wmo(cur["weather_code"])
temp = round(cur["temperature_2m"])
feels = round(cur["apparent_temperature"])
humidity = cur["relative_humidity_2m"]
precip = cur["precipitation"]
wind_spd = round(cur["wind_speed_10m"])
wind_dir = wind_direction_label(cur["wind_direction_10m"])
city_label = location_labels[idx]

# ---------------------------------------------------------------------------
# Main weather card
# ---------------------------------------------------------------------------
st.markdown(
    f"""
<div class="weather-card">
  <p class="city-name">📍 {city_label}</p>
  <p class="local-time">🕐 {time_str}</p>
  <div style="display:flex;align-items:flex-end;gap:1.5rem;flex-wrap:wrap;">
    <div>
      <span class="temp-main">{temp}</span><span class="temp-unit">{unit_sym}</span>
      <p class="condition">{emoji} {label}</p>
      <p class="feels-like">Feels like {feels}{unit_sym}</p>
    </div>
  </div>
  <div class="stat-grid">
    <div class="stat-tile">
      <div class="stat-icon">💧</div>
      <div class="stat-label">Humidity</div>
      <div class="stat-value">{humidity}%</div>
    </div>
    <div class="stat-tile">
      <div class="stat-icon">💨</div>
      <div class="stat-label">Wind</div>
      <div class="stat-value">{wind_spd} km/h {wind_dir}</div>
    </div>
    <div class="stat-tile">
      <div class="stat-icon">🌧️</div>
      <div class="stat-label">Precip</div>
      <div class="stat-value">{precip} mm</div>
    </div>
    <div class="stat-tile">
      <div class="stat-icon">{"☀️" if cur["is_day"] else "🌙"}</div>
      <div class="stat-label">Period</div>
      <div class="stat-value">{"Day" if cur["is_day"] else "Night"}</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 7-day forecast
# ---------------------------------------------------------------------------
st.markdown("### 7-Day Forecast")

day_cards = ""
for i in range(7):
    date_str = daily["time"][i]
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    day_name = "Today" if i == 0 else dt.strftime("%a")
    fc_label, fc_emoji = wmo(daily["weather_code"][i])
    hi = round(daily["temperature_2m_max"][i])
    lo = round(daily["temperature_2m_min"][i])
    day_cards += f"""
<div class="fc-card">
  <div class="fc-day">{day_name}<br><small style="font-weight:400">{dt.strftime('%d %b')}</small></div>
  <div class="fc-icon">{fc_emoji}</div>
  <div class="fc-hi">{hi}{unit_sym}</div>
  <div class="fc-lo">{lo}{unit_sym}</div>
</div>"""

st.markdown(f'<div class="forecast-row">{day_cards}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Auto-refresh note + rerun trigger
# ---------------------------------------------------------------------------
st.markdown(
    '<p class="refresh-note">Data from Open-Meteo • Refreshes every 10 min</p>',
    unsafe_allow_html=True,
)

# Auto-refresh every 10 minutes using Streamlit's built-in rerun
st.markdown(
    """
<script>
setTimeout(function(){ window.location.reload(); }, 600000);
</script>
""",
    unsafe_allow_html=True,
)
