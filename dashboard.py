import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance Hub", layout="wide")

# --- VOLLEYBALL STYLE CSS (Clean & Hidden Headers) ---
st.markdown("""
    <style>
    th, td {text-align: center !important;}
    [data-testid="stMetricValue"] {font-size: 26px; color: #FF8200; font-weight: 800;}
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    /* Hide the 'View Fullscreen' and other Streamlit UI clutter */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- PASSWORD GATE ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    _, col2, _ = st.columns([1,1,1])
    with col2:
        st.title("🥎 Access Key")
        pwd = st.text_input("Password", type="password")
        if st.button("Unlock Dashboard"):
            if pwd == st.secrets["PASSWORD"]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Invalid Credentials")
    st.stop()

# --- DATA LOADING (Optimized for Large Sheets) ---
@st.cache_data(ttl=300)
def load_ash_data():
    try:
        # Pull only necessary columns if the sheet is huge
        df = pd.read_csv(st.secrets["ASH_URL"])
        df.columns = df.columns.str.strip()
        
        # 'Nuclear Sanitizer' for numeric columns
        target_metrics = ['Peak Vertical Force [N]', 'RFD - 200ms [N/s]', 'Start Time to Peak Force [s]']
        for col in df.columns:
            if any(m in col for m in target_metrics) or 'Asym' in col:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Syncing Error: {e}")
        return pd.DataFrame()

df = load_ash_data()

# --- DASHBOARD UI ---
if not df.empty:
    # 1. ATHLETE SELECTION
    athlete_list = sorted(df['Player Name'].unique())
    selected_athlete = st.selectbox("Select Athlete", athlete_list)
    
    # Filter for selected athlete (taking the most recent test)
    # If your sheet has multiple dates, this pulls the last row
    p_data = df[df['Player Name'] == selected_athlete].iloc[-1]

    # 2. KEY PERFORMANCE INDICATORS (KPIs)
    st.subheader(f"Latest ASH Profile: {selected_athlete}")
    m1, m2, m3, m4 = st.columns(4)
    
    m1.metric("Peak Force", f"{int(p_data['Peak Vertical Force [N]'])} N")
    m2.metric("RFD (200ms)", f"{int(p_data['RFD - 200ms [N/s]'])} N/s")
    
    # Highlight Asymmetry in Red if > 10%
    asym_val = p_data.get('Peak Vertical Force [N] (Asym)(%)', 0)
    asym_color = "normal" if asym_val < 10 else "inverse"
    m3.metric("Force Asymmetry", f"{asym_val}%", delta_color=asym_color)
    
    m4.metric("Time to Peak", f"{p_data.get('Start Time to Peak Force [s]', 0)} s")

    st.divider()

    # 3. TEAM CORRELATION (No Raw Data Shown)
    st.subheader("Team-Wide Force Trends")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        # Scatter plot to see where athlete sits vs the team
        fig = px.scatter(df, x='Peak Vertical Force [N]', y='RFD - 200ms [N/s]',
                         hover_name='Player Name', 
                         title="Force Production vs. Explosiveness",
                         template="plotly_white",
                         color_discrete_sequence=["#4895DB"])
        
        # Add a special gold dot for the selected athlete
        fig.add_scatter(x=[p_data['Peak Vertical Force [N]']], 
                        y=[p_data['RFD - 200ms [N/s]']],
                        mode='markers', marker=dict(size=15, color='#FF8200', symbol='star'),
                        name=selected_athlete)
        
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.info("📊 **Insight:** The gold star represents the selected athlete's current standing relative to the team's average force and RFD output.")
        # Top 5 Ranking for Peak Force
        st.write("**Top 5: Peak Force**")
        top_5 = df.nlargest(5, 'Peak Vertical Force [N]')[['Player Name', 'Peak Vertical Force [N]']]
        st.table(top_5.assign(Force=top_5['Peak Vertical Force [N]'].astype(int)).drop(columns='Peak Vertical Force [N]'))

else:
    st.warning("Data connection established, but no records found. Check Sheet GID.")
