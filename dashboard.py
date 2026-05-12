import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Added for dual-axis support

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
        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        
        for df in [ash_df, cmj_df, roster_df]:
            df.columns = df.columns.str.strip()
        
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
    athlete_list = sorted(list(set(ash_df['Player Name'].unique()) | set(cmj_df['Player Name'].unique())))
    selected = st.selectbox("Search Athlete", athlete_list)
    
    photo_url = roster_df[roster_df['Player Name'] == selected]['Picture'].values
    photo = photo_url[0] if len(photo_url) > 0 else "https://www.w3schools.com/howto/img_avatar.png"

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
            c1, c2, c3, c4 = st.columns(4)
            
            # Helper Variables for column names
            h_col = 'Jump Height (Imp-Mom) [cm]'
            rsi_col = 'RSI-modified (Imp-Mom) [m/s]'

            c1.metric("Jump Height", f"{latest_cmj[h_col]} cm")
            c2.metric("RSI-Modified", f"{latest_cmj[rsi_col]}")
            c3.metric("Peak Power", f"{int(latest_cmj['Peak Power [W]'])} W")
            c4.metric("Stiffness", f"{int(latest_cmj['CMJ Stiffness [N/m]'])} N/m")

            # --- DUAL AXIS CHART: Jump Height vs RSI ---
            st.subheader("Performance Trend: Jump Height & Explosiveness")
            
            fig = go.Figure()

            # Add Jump Height (Left Axis)
            fig.add_trace(go.Scatter(
                x=p_cmj['Date'], 
                y=p_cmj[h_col],
                name="Jump Height (cm)",
                mode='lines+markers',
                line=dict(color='#FF8200', width=3)
            ))

            # Add RSI (Right Axis)
            fig.add_trace(go.Scatter(
                x=p_cmj['Date'], 
                y=p_cmj[rsi_col],
                name="RSI-Modified",
                mode='lines+markers',
                line=dict(color='#4895DB', width=3, dash='dot'),
                yaxis="y2" # This links it to the secondary axis
            ))

            # Update layout to support secondary axis
            fig.update_layout(
                template="plotly_white",
                xaxis=dict(title="Date", showgrid=False),
                yaxis=dict(
                    title="Jump Height (cm)",
                    titlefont=dict(color="#FF8200"),
                    tickfont=dict(color="#FF8200")
                ),
                yaxis2=dict(
                    title="RSI-Modified",
                    titlefont=dict(color="#4895DB"),
                    tickfont=dict(color="#4895DB"),
                    anchor="x",
                    overlaying="y",
                    side="right",
                    showgrid=False
                ),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=50, b=20)
            )

            st.plotly_chart(fig, use_container_width=True)

            # --- Braking Strategy Section ---
            st.subheader("Braking Strategy")
            
            # Impulse Comparison
            impulse_data = pd.DataFrame({
                'Metric': ['P1 Concentric', 'P2 Concentric'],
                'Value': [latest_cmj['P1 Concentric Impulse [N s]'], latest_cmj['P2 Concentric Impulse [N s]']]
            })
            st.plotly_chart(px.bar(impulse_data, x='Metric', y='Value', color='Metric', title="Concentric Impulse Phases", color_discrete_sequence=["#4895DB", "#FF8200"]), use_container_width=True)
            
        else:
            st.warning("No CMJ data found for this athlete.")
