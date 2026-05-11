import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance Hub", layout="wide")

# --- VOLLEYBALL STYLE CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #FF8200; }
    .athlete-header {
        background-color: #F8F9FA;
        padding: 20px;
        border-radius: 15px;
        border-left: 10px solid #FF8200;
        margin-bottom: 25px;
    }
    .player-photo {
        border-radius: 50%;
        width: 150px;
        height: 150px;
        object-fit: cover;
        border: 4px solid #4895DB;
    }
    .stTabs [role="tab"] { font-weight: 800; color: #4895DB; font-size: 18px; }
    .stTabs [aria-selected="true"] { color: #FF8200; border-bottom-color: #FF8200; }
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- PASSWORD GATE ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    _, col2, _ = st.columns([1,1,1])
    with col2:
        st.title("🔐 Access Key")
        pwd = st.text_input("Password", type="password")
        if st.button("Unlock Dashboard"):
            if pwd == st.secrets["PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
    st.stop()

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    try:
        # Load sheets
        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        
        # Clean headers
        for df in [ash_df, cmj_df, roster_df]:
            df.columns = df.columns.str.strip()
        
        # Nuclear Sanitizer for numeric columns
        def sanitize(df):
            for col in df.columns:
                if any(word in col.lower() for word in ['force', 'rfd', 'height', 'power', 'velocity', 'impulse', 'rsi', 'stiffness']):
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            return df

        ash_df = sanitize(ash_df)
        cmj_df = sanitize(cmj_df)
        
        return ash_df, cmj_df, roster_df
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

ash_df, cmj_df, roster_df = load_all_data()

# --- UI LOGIC ---
if not ash_df.empty and not cmj_df.empty:
    # Athlete Search
    athlete_list = sorted(list(set(ash_df['Player Name'].unique()) | set(cmj_df['Player Name'].unique())))
    selected = st.selectbox("Search Athlete", athlete_list)
    
    # Get Picture from Roster
    photo_url = roster_df[roster_df['Player Name'] == selected]['Picture'].values
    photo = photo_url[0] if len(photo_url) > 0 else "https://www.w3schools.com/howto/img_avatar.png"

    # Header
    st.markdown(f"""
        <div class="athlete-header">
            <div style="display: flex; align-items: center;">
                <img src="{photo}" class="player-photo">
                <div style="margin-left: 30px;">
                    <h1 style="margin:0;">{selected}</h1>
                    <p style="color:#4895DB; font-weight:700; font-size:18px; margin:0;">PERFORMANCE MASTER DASHBOARD</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- TABS ---
    tab_ash, tab_cmj = st.tabs(["⚡ ASH TEST (Force/RFD)", "🚀 CMJ TEST (Jump/Power)"])

    with tab_ash:
        p_ash = ash_df[ash_df['Player Name'] == selected].sort_values('Date')
        if not p_ash.empty:
            latest_ash = p_ash.iloc[-1]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Peak Force", f"{int(latest_ash['Peak Vertical Force [N]'])} N")
            m2.metric("RFD (200ms)", f"{int(latest_ash['RFD - 200ms [N/s]'])} N/s")
            m3.metric("Force Asym", f"{latest_ash.get('Peak Vertical Force [N] (Asym)(%)', 0)}%")
            m4.metric("Time to Peak", f"{latest_ash.get('Start Time to Peak Force [s]', 0)}s")
            
            st.plotly_chart(px.line(p_ash, x='Date', y='Peak Vertical Force [N]', title="Force History", markers=True, color_discrete_sequence=["#FF8200"]), use_container_width=True)
        else:
            st.warning("No ASH data found for this athlete.")

    with tab_cmj:
        p_cmj = cmj_df[cmj_df['Player Name'] == selected].sort_values('Date')
        if not p_cmj.empty:
            latest_cmj = p_cmj.iloc[-1]
            
            # --- TOP ROW: THE BIG 4 ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Jump Height", f"{latest_cmj['Jump Height (Imp-Mom) [cm]']} cm")
            c2.metric("RSI-Modified", f"{latest_cmj['RSI-modified (Imp-Mom) [m/s]']}")
            c3.metric("Peak Power", f"{int(latest_cmj['Peak Power [W]'])} W")
            c4.metric("Stiffness", f"{int(latest_cmj['CMJ Stiffness [N/m]'])} N/m")

            st.divider()

            # --- MIDDLE ROW: STRATEGY & TRENDS ---
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("Braking vs. Deceleration RFD")
                # This shows if the athlete is 'sharp' or 'mushy' in the bottom of the jump
                rfd_data = pd.DataFrame({
                    'Metric': ['Eccentric Braking', 'Eccentric Deceleration'],
                    'Value': [latest_cmj['Eccentric Braking RFD [N/s]'], latest_cmj['Eccentric Deceleration RFD [N/s]']]
                })
                fig_rfd = px.bar(rfd_data, x='Metric', y='Value', 
                                 color='Metric', 
                                 color_discrete_map={'Eccentric Braking': '#4895DB', 'Eccentric Deceleration': '#FF8200'},
                                 template="plotly_white")
                fig_rfd.update_layout(showlegend=False)
                st.plotly_chart(fig_rfd, use_container_width=True)
            
            with col_right:
                st.subheader("Jump Height Trend")
                fig_trend = px.line(p_cmj, x='Date', y='Jump Height (Imp-Mom) [cm]', 
                                    markers=True, 
                                    color_discrete_sequence=["#FF8200"],
                                    template="plotly_white")
                st.plotly_chart(fig_trend, use_container_width=True)

            # --- BOTTOM ROW: ASYMMETRY CHECK ---
            st.subheader("CMJ Symmetry Analysis")
            asym_cols = st.columns(3)
            # Highlighting specific asymmetries in the jump strategy
            asym_cols[0].metric("Concentric Mean Force Asym", f"{latest_cmj.get('Concentric Mean Force % (Asym) (%)', 0)}%")
            asym_cols[1].metric("Eccentric Braking Asym", f"{latest_cmj.get('Eccentric Braking RFD % (Asym) (%)', 0)}%")
            asym_cols[2].metric("Takeoff Peak Force Asym", f"{latest_cmj.get('Takeoff Peak Force % (Asym) (%)', 0)}%")
        else:
            st.warning("No CMJ data found for this athlete.")
