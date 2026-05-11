import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Config
st.set_page_config(page_title="Softball Performance", layout="wide")

# 2. Sidebar Maintenance
if st.sidebar.button("🔄 Clear App Cache & Reboot"):
    st.cache_data.clear()
    st.rerun()

# 3. Password Gate (VB Style)
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    pwd = st.sidebar.text_input("Access Key", type="password")
    if st.sidebar.button("Unlock"):
        if pwd == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.sidebar.error("Incorrect Password")
    st.stop()

# 4. Safe-Sync Data Loading
@st.cache_data(ttl=300)
def load_and_merge_safe():
    def clean(df):
        df.columns = df.columns.str.strip()
        # Mango Type 1 logic: Force numeric, remove non-numbers
        for col in df.columns:
            if any(w in col.lower() for w in ['force', 'rfd', 'height', 'load', 'count', 'power']):
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        return df

    try:
        # Load Roster first to establish the baseline
        master = clean(pd.read_csv(st.secrets["ROSTER_URL"]))
        
        # Merge others one by one to save memory
        sheets = ["ASH_URL", "CMJ_URL", "THROWS_URL", "SWINGS_URL"]
        for key in sheets:
            temp_df = clean(pd.read_csv(st.secrets[key]))
            # Only merge if 'Player Name' exists, otherwise skip to prevent crash
            if "Player Name" in temp_df.columns:
                master = master.merge(temp_df, on="Player Name", how="left")
            
        return master
    except Exception as e:
        st.error(f"Merge Error: {e}")
        return pd.DataFrame()

# 5. Dashboard UI
df = load_and_merge_safe()

if not df.empty:
    st.title("🥎 Softball Performance Hub")
    
    # Athlete Selector
    athlete = st.selectbox("Select Athlete", df["Player Name"].unique())
    p_data = df[df["Player Name"] == athlete].iloc[0]

    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("ASH Force", f"{p_data.get('Peak Vertical Force [N]', 0)} N")
    c2.metric("CMJ Height", f"{p_data.get('Jump Height (Imp-Mom) [cm]', 0)} cm")
    c3.metric("Total Swings", p_data.get('Swing Count', 0))

    # Correlation Analysis
    st.divider()
    nums = df.select_dtypes(include=['number']).columns.tolist()
    if len(nums) >= 2:
        fig = px.scatter(df, x=nums[0], y=nums[1], color="Position", 
                         hover_name="Player Name", trendline="ols",
                         template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Data is empty. Check your Google Sheet URL permissions.")
