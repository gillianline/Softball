import streamlit as st
import pandas as pd
import plotly.express as px

# 1. IMMEDIATE PAGE CONFIG
st.set_page_config(page_title="Softball Performance", layout="wide")

# 2. HIDE BRANDING (Matches your VB style)
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# 3. SIMPLEST PASSWORD GATE
# This ensures the app stays "alive" while waiting for input
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🥎 Softball Access")
    # Using a simple input without a lot of logic around it first
    pwd = st.text_input("Password", type="password")
    if st.button("Unlock"):
        if pwd == st.secrets["PASSWORD"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid")
    st.stop()

# 4. DATA LOADING (Only runs AFTER successful login)
@st.cache_data(ttl=600)
def load_softball_data():
    def clean(df):
        df.columns = df.columns.str.strip()
        # Mango Type 1 numeric cleaning
        for col in df.columns:
            if any(w in col.lower() for w in ['force', 'rfd', 'height', 'load', 'count']):
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        return df

    try:
        # Loading logic
        roster = clean(pd.read_csv(st.secrets["ROSTER_URL"]))
        ash    = clean(pd.read_csv(st.secrets["ASH_URL"]))
        cmj    = clean(pd.read_csv(st.secrets["CMJ_URL"]))
        throws = clean(pd.read_csv(st.secrets["THROWS_URL"]))
        swings = clean(pd.read_csv(st.secrets["SWINGS_URL"]))

        # Progressive Merge
        df = roster.merge(ash, on="Player Name", how="left")
        df = df.merge(cmj, on="Player Name", how="left")
        df = df.merge(throws, on="Player Name", how="left")
        df = df.merge(swings, on="Player Name", how="left")
        return df
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return pd.DataFrame()

# 5. DASHBOARD EXECUTION
df = load_softball_data()

if not df.empty:
    st.success("✅ Systems Online")
    
    # Simple Selector to verify it works
    athlete = st.selectbox("Athlete", df["Player Name"].unique())
    st.dataframe(df[df["Player Name"] == athlete])
    
    # Correlation Plot
    st.subheader("Physical vs. Skill Correlation")
    nums = df.select_dtypes(include=['number']).columns.tolist()
    if len(nums) >= 2:
        fig = px.scatter(df, x=nums[0], y=nums[1], hover_name="Player Name", trendline="ols")
        st.plotly_chart(fig)
else:
    st.warning("Connected to server, but data is missing. Check your ROSTER_URL and ASH_URL.")
