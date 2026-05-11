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
        background-color: #F8F9FA; padding: 20px; border-radius: 15px; border-left: 10px solid #FF8200; margin-bottom: 25px;
    }
    .player-photo { border-radius: 50%; width: 150px; height: 150px; object-fit: cover; border: 4px solid #4895DB; }
    .stTabs [role="tab"] { font-weight: 800; color: #4895DB; font-size: 18px; }
    .stTabs [aria-selected="true"] { color: #FF8200; border-bottom-color: #FF8200; }
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; }
    .scout-table th { background-color: #4895DB; color: white; padding: 8px; border-bottom: 2px solid #FF8200; text-transform: uppercase; font-size: 12px; }
    .scout-table td { padding: 8px; border-bottom: 1px solid #F5F5F7; font-size: 12px; }
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
            else:
                st.error("Invalid Password")
    st.stop()

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    try:
        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        
        def sanitize(df):
            df.columns = df.columns.str.strip()
            # Clean names for stability
            if 'Jump Height (Imp-Mom) [cm]' in df.columns:
                df.rename(columns={'Jump Height (Imp-Mom) [cm]': 'JumpHeight'}, inplace=True)
            if 'RSI-modified (Imp-Mom) [m/s]' in df.columns:
                df.rename(columns={'RSI-modified (Imp-Mom) [m/s]': 'RSI'}, inplace=True)
            
            for col in df.columns:
                if any(w in col.lower() for w in ['force', 'rfd', 'height', 'power', 'rsi']):
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0.0)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            return df

        return sanitize(ash_df), sanitize(cmj_df), roster_df
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

ash_df, cmj_df, roster_df = load_all_data()

if not ash_df.empty and not cmj_df.empty:
    athlete_list = sorted(list(set(ash_df['Player Name'].unique()) | set(cmj_df['Player Name'].unique())))
    selected = st.selectbox("Search Athlete", athlete_list)
    
    pic_row = roster_df[roster_df['Player Name'] == selected]
    photo = pic_row['Picture'].values[0] if not pic_row.empty and 'Picture' in roster_df.columns else "https://www.w3schools.com/howto/img_avatar.png"

    st.markdown(f"""
        <div class="athlete-header">
            <div style="display: flex; align-items: center;">
                <img src="{photo}" class="player-photo">
                <div style="margin-left: 30px;">
                    <h1 style="margin:0;">{selected}</h1>
                    <p style="color:#4895DB; font-weight:700; font-size:18px; margin:0;">SOFTBALL PERFORMANCE Hub</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    tab_ash, tab_cmj = st.tabs(["⚡ ASH TEST", "🚀 CMJ RECOVERY"])

    with tab_ash:
        p_ash = ash_df[ash_df['Player Name'] == selected].sort_values('Date')
        if not p_ash.empty:
            latest = p_ash.iloc[-1]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Peak Force", f"{int(latest['Peak Vertical Force [N]'])} N")
            m2.metric("RFD (200ms)", f"{int(latest['RFD - 200ms [N/s]'])} N/s")
            m3.metric("Force Asym", f"{latest.get('Peak Vertical Force [N] (Asym)(%)', 0)}%")
            m4.metric("Time to Peak", f"{latest.get('Start Time to Peak Force [s]', 0)}s")
            st.plotly_chart(px.line(p_ash, x='Date', y='Peak Vertical Force [N]', markers=True, color_discrete_sequence=["#FF8200"], template="plotly_white"), use_container_width=True)

    with tab_cmj:
        p_cmj = cmj_df[cmj_df['Player Name'] == selected].sort_values('Date')
        if not p_cmj.empty:
            b_cmj = p_cmj.iloc[0]
            l_cmj = p_cmj.iloc[-1]
            h_perc = ((l_cmj['JumpHeight'] - b_cmj['JumpHeight']) / b_cmj['JumpHeight']) * 100 if b_cmj['JumpHeight'] != 0 else 0
            
            st.subheader("CMJ Baseline vs. Post-Match Recovery")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Baseline Height", f"{b_cmj['JumpHeight']:.1f} cm")
            c2.metric("Latest Jump", f"{l_cmj['JumpHeight']:.1f} cm", delta=f"{h_perc:+.1f}%")
            c3.metric("Current RSI", f"{l_cmj['RSI']:.2f}")
            c4.metric("Status", "Recovered" if h_perc > -5 else "Fatigued", delta_color="normal" if h_perc > -5 else "inverse")

            st.divider()

            # --- STACKED CHARTS (BROKEN DUAL-AXIS BYPASSED) ---
            st.subheader("Performance Trends")
            
            # Chart 1: Jump Height
            fig_h = px.line(p_cmj, x='Date', y='JumpHeight', markers=True, 
                            title="Jump Height (cm)", color_discrete_sequence=["#FF8200"], template="plotly_white")
            fig_h.update_layout(xaxis_title=None, margin=dict(l=20, r=20, t=40, b=0))
            st.plotly_chart(fig_h, use_container_width=True)

            # Chart 2: RSI
            fig_r = px.line(p_cmj, x='Date', y='RSI', markers=True, 
                            title="Explosiveness (RSI)", color_discrete_sequence=["#4895DB"], template="plotly_white")
            fig_r.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_r, use_container_width=True)

            st.divider()

            # --- HISTORY TABLE ---
            st.subheader("Jump History")
            hist = p_cmj.copy()
            hist['Vs. Baseline'] = (hist['JumpHeight'] - b_cmj['JumpHeight']).map('{:+.1f} cm'.format)
            hist['Jump Date'] = hist['Date'].dt.strftime('%m/%d/%Y')
            st.write(hist[['Jump Date', 'JumpHeight', 'Vs. Baseline', 'RSI']].to_html(index=False, classes='scout-table', escape=False), unsafe_allow_html=True)
