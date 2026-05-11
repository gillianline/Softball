import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance Profile", layout="centered")

# --- CUSTOM SCOUT CARD CSS ---
st.markdown("""
    <style>
    /* Main Background & Font */
    .stApp { background-color: #F5F5F7; color: #1D1D1F; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Center the metric text */
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: 800; color: #FF8200; }
    [data-testid="stMetricLabel"] { font-size: 14px; text-transform: uppercase; letter-spacing: 1px; color: #4895DB; }

    /* The Athlete Card Container */
    .athlete-card {
        background-color: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        text-align: center;
        margin-top: 20px;
    }
    
    /* Circular Photo Styling */
    .player-photo {
        border-radius: 50%;
        width: 180px;
        height: 180px;
        object-fit: cover;
        border: 4px solid #FF8200;
        margin-bottom: 20px;
    }

    /* Hide Streamlit Clutter */
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- PASSWORD GATE ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    _, col2, _ = st.columns([1,2,1])
    with col2:
        st.title("🔐 Access")
        pwd = st.text_input("Enter Key", type="password")
        if st.button("Login"):
            if pwd == st.secrets["PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
    st.stop()

# --- DATA LOADING (ASH ONLY) ---
@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(st.secrets["ASH_URL"])
    df.columns = df.columns.str.strip()
    # Simple clean: only the essentials
    for col in df.columns:
        if any(w in col.lower() for w in ['force', 'rfd', 'asym']):
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
    return df

df = load_data()

# --- UI: THE SCOUT CARD ---
athlete_list = sorted(df['Player Name'].unique())
selected = st.selectbox("Search Athlete", athlete_list)
p_data = df[df['Player Name'] == selected].iloc[-1]

# Display the "Card"
st.markdown(f"""
    <div class="athlete-card">
        <img src="{p_data.get('PhotoURL', 'https://www.w3schools.com/howto/img_avatar.png')}" class="player-photo">
        <h1 style="margin:0; color:#1D1D1F;">{selected}</h1>
        <p style="color:#8E8E93; font-weight:600; text-transform:uppercase;">{p_data.get('Position', 'Athlete')}</p>
    </div>
    """, unsafe_allow_html=True)

st.write("###") # Spacing

# Metric Grid
col1, col2 = st.columns(2)
with col1:
    st.metric("Peak Force", f"{int(p_data['Peak Vertical Force [N]'])} N")
    st.metric("Force Asym", f"{p_data.get('Peak Vertical Force [N] (Asym)(%)', 0)}%")

with col2:
    st.metric("RFD (200ms)", f"{int(p_data['RFD - 200ms [N/s]'])} N/s")
    st.metric("Explosive Efforts", p_data.get('Explosive Efforts', 'N/A'))

# Simple Rank Message (No tables/charts)
peak_force_rank = df['Peak Vertical Force [N]'].rank(ascending=False).loc[p_data.name]
st.info(f"💡 **Team Insight:** {selected} is currently ranked **#{int(peak_force_rank)}** in Peak Force production.")
