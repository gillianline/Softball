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
            # --- BASELINE LOGIC ---
            # We assume the first test or a specific 'Week 1' test is the baseline
            baseline_val = p_cmj.iloc[0]['Jump Height (Imp-Mom) [cm]']
            latest_cmj = p_cmj.iloc[-1]
            latest_val = latest_cmj['Jump Height (Imp-Mom) [cm]']
            
            # Calculate % Change
            perc_change = ((latest_val - baseline_val) / baseline_val) * 100
            
            # --- TOP ROW: RECOVERY VS BASELINE ---
            st.subheader("CMJ Baseline vs. Latest Recovery")
            b1, b2, b3, b4 = st.columns(4)
            
            b1.metric("Baseline Height", f"{baseline_val:.1f} cm")
            b2.metric("Latest Jump", f"{latest_val:.1f} cm", delta=f"{perc_change:+.1f}%")
            
            # RSI Comparison
            baseline_rsi = p_cmj.iloc[0]['RSI-modified (Imp-Mom) [m/s]']
            latest_rsi = latest_cmj['RSI-modified (Imp-Mom) [m/s]']
            rsi_delta = ((latest_rsi - baseline_rsi) / baseline_rsi) * 100
            
            b3.metric("Current RSI", f"{latest_rsi:.2f}", delta=f"{rsi_delta:+.1f}%")
            b4.metric("Jump Status", "Recovered" if perc_change > -5 else "Fatigued", 
                      delta_color="normal" if perc_change > -5 else "inverse")

            st.divider()

            # --- MIDDLE ROW: THE VOLLEYBALL-STYLE TREND ---
            st.subheader("Height vs. RSI Trend")
            # Create a dual-axis style chart
            fig_trend = px.line(p_cmj, x='Date', y=['Jump Height (Imp-Mom) [cm]', 'RSI-modified (Imp-Mom) [m/s]'],
                                markers=True, 
                                labels={"value": "Performance Value", "variable": "Metric"},
                                color_discrete_map={
                                    "Jump Height (Imp-Mom) [cm]": "#FF8200", 
                                    "RSI-modified (Imp-Mom) [m/s]": "#4895DB"
                                },
                                template="plotly_white")
            st.plotly_chart(fig_trend, use_container_width=True)

            # --- BOTTOM ROW: MATCH CONTEXT TABLE ---
            st.subheader("Jump History & Match Context")
            
            # Create the summary table
            history_table = p_cmj.copy()
            history_table['Vs. Baseline'] = history_table['Jump Height (Imp-Mom) [cm]'] - baseline_val
            history_table['Vs. Baseline'] = history_table['Vs. Baseline'].map('{:+.1f} cm'.format)
            
            # Rename columns to match your preferred look
            display_cols = {
                'Date': 'Jump Date',
                'Jump Height (Imp-Mom) [cm]': 'Jump Height',
                'RSI-modified (Imp-Mom) [m/s]': 'RSI'
            }
            
            # Formatting for display
            final_table = history_table[list(display_cols.keys()) + ['Vs. Baseline']]
            final_table = final_table.rename(columns=display_cols)
            final_table['Jump Date'] = final_table['Jump Date'].dt.strftime('%m/%d/%Y')
            
            # Apply the style
            st.write(final_table.to_html(index=False, classes='scout-table', escape=False), unsafe_allow_html=True)
            
        else:
            st.warning("No CMJ data found for this athlete.")
