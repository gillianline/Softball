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
            # --- 1. BASELINE & RECOVERY LOGIC ---
            # Establish baseline from the first recorded test
            baseline_cmj = p_cmj.iloc[0]
            latest_cmj = p_cmj.iloc[-1]
        
            b_height = baseline_cmj['Jump Height (Imp-Mom) [cm]']
            l_height = latest_cmj['Jump Height (Imp-Mom) [cm]']
        
            b_rsi = baseline_cmj['RSI-modified (Imp-Mom) [m/s]']
            l_rsi = latest_cmj['RSI-modified (Imp-Mom) [m/s]']
        
            # Calculate Deltas
            height_diff = l_height - b_height
            height_perc = (height_diff / b_height) * 100
            rsi_perc = ((l_rsi - b_rsi) / b_rsi) * 100

            # --- 2. HEADER: CMJ BASELINE VS. RECOVERY ---
            st.subheader("CMJ Baseline vs. Post-Match Recovery")
            st.markdown(f"**Performance vs. Initial Baseline**")
        
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Baseline Height", f"{b_height:.1f} cm")
            m2.metric("Latest Jump", f"{l_height:.1f} cm", delta=f"{height_perc:+.1f}%")
            m3.metric("Current RSI", f"{l_rsi:.2f}", delta=f"{rsi_perc:+.1f}%")
        
            # Status logic: flagging fatigue if drop is > 5%
            status = "Recovered" if height_perc > -5 else "Fatigued"
            m4.metric("Status", status, delta_color="normal" if status == "Recovered" else "inverse")

            st.divider()

            # --- 3. DUAL AXIS CHART: HEIGHT VS RSI TREND ---
            st.subheader("Height vs. RSI Trend")
        
            fig_trend = go.Figure()

            # Primary Axis: Jump Height
            fig_trend.add_trace(go.Scatter(
                x=p_cmj['Date'], y=p_cmj['Jump Height (Imp-Mom) [cm]'],
                name="Jump Height (cm)", mode='lines+markers',
                line=dict(color='#FF8200', width=3),
                marker=dict(size=8, borderwidth=1, bordercolor="white")
            ))

            # Secondary Axis: RSI
            fig_trend.add_trace(go.Scatter(
                x=p_cmj['Date'], y=p_cmj['RSI-modified (Imp-Mom) [m/s]'],
                name="RSI-m", mode='lines+markers',
                line=dict(color='#4895DB', width=3, dash='dot'),
                marker=dict(size=8, borderwidth=1, bordercolor="white"),
                yaxis="y2"
            ))

            fig_trend.update_layout(
                template="plotly_white",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=False),
                yaxis=dict(
                    title="Jump Height (cm)",
                    titlefont=dict(color="#FF8200"),
                    tickfont=dict(color="#FF8200")
                ),
                yaxis2=dict(
                    title="RSI-m (m/s)",
                    titlefont=dict(color="#4895DB"),
                    tickfont=dict(color="#4895DB"),
                    anchor="x", overlaying="y", side="right",
                    showgrid=False
                ),
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig_trend, use_container_width=True)

            st.divider()

            # --- 4. MATCH CONTEXT TABLE ---
            st.subheader("Jump History & Match Context")
        
            # Prepare table data
            history = p_cmj.copy()
            history['Vs. Baseline'] = (history['Jump Height (Imp-Mom) [cm]'] - b_height).map('{:+.1f} cm'.format)
        
            # Rename for clean headers
            history = history.rename(columns={
                'Date': 'Jump Date',
                'Jump Height (Imp-Mom) [cm]': 'Jump Height',
                'RSI-modified (Imp-Mom) [m/s]': 'RSI'
            })
        
            # Ensure your CMJ Google Sheet has a 'Match Context' column to pull this in
            display_cols = ['Jump Date', 'Jump Height', 'Vs. Baseline', 'RSI']
            if 'Match Context' in history.columns:
                display_cols.insert(1, 'Match Context')
            else:
                # Fallback if the column doesn't exist yet
                history['Match Context'] = "N/A"
                display_cols.insert(1, 'Match Context')

            # Convert date for cleaner display
            history['Jump Date'] = history['Jump Date'].dt.strftime('%m/%d/%Y')

            # Rendering with the volleyball CSS class 'scout-table'
            st.write(history[display_cols].to_html(index=False, classes='scout-table', justify='center', escape=False), unsafe_allow_html=True)

        else:
            st.warning("No CMJ data available for the selected athlete.")
