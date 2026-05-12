import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance Hub", layout="wide")

# --- 2. CUSTOM LADY VOL CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1D1D1F; }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #FF8200; }
    .athlete-header {
        background-color: #F8F9FA; padding: 20px; border-radius: 15px;
        border-left: 10px solid #FF8200; margin-bottom: 25px;
    }
    .player-photo { border-radius: 50%; width: 150px; height: 150px; object-fit: cover; border: 4px solid #4895DB; }
    .metric-sub { font-size: 14px; font-weight: 700; margin-top: -15px; margin-bottom: 10px; }
    .red-text { color: #dc3545; }
    .green-text { color: #28a745; }
    #MainMenu, footer, header { visibility: hidden; }
    
    /* Simplified Login Styling */
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top: 15%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIMPLE LOGIN PAGE ---
if "auth" not in st.session_state: 
    st.session_state.auth = False

if not st.session_state.auth:
    # Minimalist center-aligned login
    _, col2, _ = st.columns([1, 0.8, 1])
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.title("Performance Access")
        pwd = st.text_input("Enter Password", type="password", label_visibility="collapsed", placeholder="Enter Password")
        if st.button("Login", use_container_width=True):
            if pwd == st.secrets["PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Invalid Access Key")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 4. DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    try:
        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        
        for df in [ash_df, cmj_df, roster_df]:
            df.columns = df.columns.str.strip()
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        ash_metrics = ['Peak Vertical Force [N]', 'RFD - 200ms [N/s]', 'Start Time to Peak Force [s]']
        cmj_metrics = ['Jump Height (Imp-Mom) [cm]', 'RSI-modified (Imp-Mom) [m/s]', 'Peak Power [W]']
        
        for df, metrics in [(ash_df, ash_metrics), (cmj_df, cmj_metrics)]:
            for col in df.columns:
                if any(m in col for m in metrics) or 'Asym' in col:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce').fillna(0)
        
        ash_df = ash_df.merge(roster_df[['Player Name', 'Picture']], on='Player Name', how='left')
        cmj_df = cmj_df.merge(roster_df[['Player Name', 'Picture']], on='Player Name', how='left')
        
        return ash_df, cmj_df
    except Exception as e:
        st.error(f"Data Sync Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

ash_df, cmj_df = load_all_data()

# --- 5. DASHBOARD UI ---
def quick_metric(col, label, best, current, unit):
    diff = ((current - best) / best * 100) if best != 0 else 0
    color = "red-text" if diff < -10 else "green-text"
    col.metric(label, f"{int(best)}{unit}")
    col.markdown(f'<p class="metric-sub {color}">Latest: {current:.1f}{unit} ({diff:+.1f}%)</p>', unsafe_allow_html=True)

if not ash_df.empty:
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        selected = st.selectbox("Search Athlete", sorted(ash_df['Player Name'].unique()))
    
    p_ash_all = ash_df[ash_df['Player Name'] == selected].sort_values('Date')
    
    with f_col2:
        years = sorted(p_ash_all['Date'].dt.year.dropna().unique().astype(int), reverse=True)
        selected_year = st.selectbox("Select Season", ["All Time"] + years)

    if selected_year == "All Time":
        ash_filt = p_ash_all
        cmj_filt = cmj_df[cmj_df['Player Name'] == selected].sort_values('Date')
        label = "All-Time"
    else:
        ash_filt = p_ash_all[p_ash_all['Date'].dt.year == selected_year]
        cmj_filt = cmj_df[(cmj_df['Player Name'] == selected) & (cmj_df['Date'].dt.year == selected_year)].sort_values('Date')
        label = str(selected_year)

    latest_ash = ash_filt.iloc[-1] if not ash_filt.empty else None
    if latest_ash is not None:
        st.markdown(f"""
            <div class="athlete-header">
                <div style="display: flex; align-items: center;">
                    <img src="{latest_ash.get('Picture', 'https://www.w3schools.com/howto/img_avatar.png')}" class="player-photo">
                    <div style="margin-left: 30px;">
                        <h1 style="margin:0;">{selected}</h1>
                        <p style="color:#4895DB; font-weight:700; margin:0;">PERFORMANCE HUB | {label}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    tab_ash, tab_cmj = st.tabs(["ASH TEST", "CMJ READINESS"])

    with tab_ash:
        if not ash_filt.empty:
            # ASH Metrics
            best_f = ash_filt['Peak Vertical Force [N]'].max()
            best_r = ash_filt['RFD - 200ms [N/s]'].max()
            
            m1, m2, m3 = st.columns(3)
            quick_metric(m1, "Best Force", best_f, latest_ash['Peak Vertical Force [N]'], " N")
            quick_metric(m2, "Best RFD", best_r, latest_ash['RFD - 200ms [N/s]'], " N/s")
            m3.metric("Latest Asymmetry", f"{latest_ash.get('Peak Vertical Force [N] (Asym)(%)', 0)}%")

            st.divider()
            
            # ASH Chart
            fig_ash = px.line(ash_filt, x='Date', y='Peak Vertical Force [N]', markers=True, 
                             template="plotly_white", color_discrete_sequence=["#FF8200"])
            fig_ash.update_xaxes(tickformat="%b %d, %y", tickangle=-45, nticks=12, title="")
            st.plotly_chart(fig_ash, use_container_width=True)
        else:
            st.info("No ASH records found.")

    with tab_cmj:
        if not cmj_filt.empty:
            c_lat = cmj_filt.iloc[-1]
            b_h = cmj_filt['Jump Height (Imp-Mom) [cm]'].max()
            b_rsi = cmj_filt['RSI-modified (Imp-Mom) [m/s]'].max()

            cm1, cm2, cm3 = st.columns(3)
            quick_metric(cm1, "Best Jump Height", b_h, c_lat['Jump Height (Imp-Mom) [cm]'], " cm")
            
            # RSI Logic with 2 Decimals
            rsi_curr = c_lat['RSI-modified (Imp-Mom) [m/s]']
            rsi_diff = ((rsi_curr - b_rsi) / b_rsi * 100) if b_rsi != 0 else 0
            rsi_col = "red-text" if rsi_diff < -10 else "green-text"
            cm2.metric("Best RSI-m", f"{b_rsi:.2f}")
            cm2.markdown(f'<p class="metric-sub {rsi_col}">Latest: {rsi_curr:.2f} ({rsi_diff:+.1f}%)</p>', unsafe_allow_html=True)
            
            cm3.metric("Current Weight", f"{c_lat.get('BW [KG]', 0):.1f}kg")

            st.write("")
            fig_cmj = px.line(cmj_filt, x='Date', y='Jump Height (Imp-Mom) [cm]', markers=True,
                             template="plotly_white", color_discrete_sequence=["#4895DB"])
            fig_cmj.update_xaxes(tickformat="%b %d, %y", tickangle=-45, nticks=12, title="")
            fig_cmj.update_layout(height=400, yaxis_title="Jump Height (cm)", margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_cmj, use_container_width=True)
        else:
            st.info("No CMJ records found.")
