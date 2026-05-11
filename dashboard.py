import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Setup
st.set_page_config(page_title="Softball Performance", layout="wide")

# 2. Volleyball-Style Formatting
st.markdown("""
    <style>
    th, td {text-align: center !important;}
    [data-testid="stMetricValue"] {font-size: 24px;}
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    .player-photo-large { border-radius: 50%; width: 200px; height: 200px; object-fit: contain; border: 6px solid #FF8200; }
    @media print { [data-testid="stSidebar"], [data-testid="stHeader"] { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

# 3. Password Check (Matches VB)
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    pwd = st.text_input("Enter Access Key", type="password")
    if st.button("Unlock"):
        if pwd == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Incorrect Password")
    st.stop()

# 4. Data Loading (Matches VB "Nuclear Sanitizer")
@st.cache_data(ttl=600)
def get_data():
    def sanitize(df):
        df.columns = df.columns.str.strip()
        # Ensure we find the Name column
        for col in df.columns:
            if col.lower() in ['player name', 'name', 'athlete']:
                df.rename(columns={col: 'Player Name'}, inplace=True)
        # Convert performance metrics to numbers
        for col in df.columns:
            if any(w in col.lower() for w in ['force', 'rfd', 'height', 'load', 'count']):
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        return df

    try:
        r = sanitize(pd.read_csv(st.secrets["ROSTER_URL"]))
        a = sanitize(pd.read_csv(st.secrets["ASH_URL"]))
        c = sanitize(pd.read_csv(st.secrets["CMJ_URL"]))
        t = sanitize(pd.read_csv(st.secrets["THROWS_URL"]))
        s = sanitize(pd.read_csv(st.secrets["SWINGS_URL"]))

        df = r.merge(a, on="Player Name", how="left") \
              .merge(c, on="Player Name", how="left") \
              .merge(t, on="Player Name", how="left") \
              .merge(s, on="Player Name", how="left")
        return df
    except Exception as e:
        st.error(f"Syncing Error: {e}")
        return pd.DataFrame()

# 5. Dashboard Output
df = get_data()

if not df.empty:
    st.title("🥎 Softball Performance Analytics")
    athlete = st.selectbox("Select Athlete", df["Player Name"].unique())
    p_data = df[df["Player Name"] == athlete].iloc[0]

    # Visualizing Data
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        img = p_data.get('PhotoURL', "https://www.w3schools.com/howto/img_avatar.png")
        st.markdown(f'<img src="{img}" class="player-photo-large">', unsafe_allow_html=True)
    with col2:
        st.metric("ASH Peak Force", f"{p_data.get('Peak Vertical Force [N]', 0)} N")
        st.metric("CMJ Height", f"{p_data.get('Jump Height (Imp-Mom) [cm]', 0)} cm")
    with col3:
        st.metric("Swing Load", p_data.get('Sum Swing Max Player Load', 0))
        st.metric("Throw Count", p_data.get('Total Throw Count', 0))

    # Correlation Analysis
    st.divider()
    st.subheader("Performance Correlations")
    nums = df.select_dtypes(include=['number']).columns.tolist()
    if len(nums) >= 2:
        fig = px.scatter(df, x=nums[0], y=nums[1], color="Position", hover_name="Player Name", trendline="ols")
        st.plotly_chart(fig, use_container_width=True)
