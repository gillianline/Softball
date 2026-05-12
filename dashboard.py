import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance Hub", layout="wide")

# --- CUSTOM CSS ---
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
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; margin-top: 10px;}
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
        st.title("🔐 Performance Access")
        pwd = st.text_input("Enter Key", type="password")
        if st.button("Unlock Dashboard"):
            if pwd == st.secrets["PASSWORD"]:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Invalid Credentials")
    st.stop()

# --- DATA LOADING & CLEANING ---
@st.cache_data(ttl=300)
def load_all_softball_data():
    try:
        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        swing_df = pd.read_csv(st.secrets["SWING_URL"])
        throw_df = pd.read_csv(st.secrets["THROW_URL"])
        
        def sanitize(df):
            df.columns = df.columns.str.strip()
            for col in ['Date', 'Test Date', 'date']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            return df

        return sanitize(ash_df), sanitize(cmj_df), sanitize(roster_df), sanitize(swing_df), sanitize(throw_df)
    except Exception as e:
        st.error(f"Data Connection Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

ash_df, cmj_df, roster_df, swing_df, throw_df = load_all_softball_data()

# --- DASHBOARD UI ---
if not ash_df.empty:
    athlete_list = sorted(ash_df['Player Name'].unique())
    selected = st.selectbox("Search Athlete", athlete_list)
    
    pic_row = roster_df[roster_df['Player Name'] == selected]
    photo = pic_row['Picture'].values[0] if not pic_row.empty and 'Picture' in roster_df.columns else "https://www.w3schools.com/howto/img_avatar.png"

    st.markdown(f"""
        <div class="athlete-header">
            <div style="display: flex; align-items: center;">
                <img src="{photo}" class="player-photo">
                <div style="margin-left: 30px;">
                    <h1 style="margin:0;">{selected}</h1>
                    <p style="color:#4895DB; font-weight:700; font-size:18px; margin:0;">SOFTBALL HIGH PERFORMANCE HUB</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    tab_ash, tab_cmj = st.tabs(["⚡ ASH PROFILE", "🚀 CMJ RECOVERY"])

    # --- TAB 1: ASH TEST ---
    with tab_ash:
        p_ash = ash_df[ash_df['Player Name'] == selected].sort_values('Date')
        if not p_ash.empty:
            latest = p_ash.iloc[-1]
            try:
                asym_val = float(str(latest.get('Peak Vertical Force [N] (Asym)(%)', 0)).replace('%', ''))
            except:
                asym_val = 0.0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Peak Force", f"{int(latest['Peak Vertical Force [N]'])} N")
            m2.metric("RFD (200ms)", f"{int(latest['RFD - 200ms [N/s]'])} N/s")
            m3.metric("Force Asym", f"{asym_val}%", delta="- Risk" if asym_val > 10 else None, delta_color="inverse")
            m4.metric("Time to Peak", f"{latest.get('Start Time to Peak Force [s]', 0)}s")
            
            st.plotly_chart(px.line(p_ash, x='Date', y='Peak Vertical Force [N]', markers=True, color_discrete_sequence=["#FF8200"], template="plotly_white"), use_container_width=True)

    # --- TAB 2: CMJ RECOVERY ---
    with tab_cmj:
        st.markdown("### CMJ Baseline vs. Post-Match Recovery")
        
        c_sync = cmj_df.rename(columns={'Athlete': 'Player Name'}) if 'Athlete' in cmj_df.columns else cmj_df.copy()
        
        # DYNAMIC DETECTION
        date_col = next((c for c in ['Test Date', 'Date', 'date', 'test date'] if c in c_sync.columns), None)
        h_col = next((c for c in ['Jump Height (Imp-Mom) [cm]', 'Jump Height', 'Height'] if c in c_sync.columns), None)
        r_col = next((c for c in ['RSI-modified [m/s]', 'RSI-modified (Imp-Mom) [m/s]', 'RSI', 'RSI-mod'] if c in c_sync.columns), None)
        
        if not all([date_col, h_col, r_col]):
            st.error(f"Missing Columns: Date ({date_col}), Height ({h_col}), RSI ({r_col})")
            st.stop()

        c_sync[date_col] = pd.to_datetime(c_sync[date_col], errors='coerce')
        ath_cmj_data = c_sync[c_sync['Player Name'] == selected].sort_values(date_col)
        
        if not ath_cmj_data.empty:
            base_row = ath_cmj_data.iloc[0] 
            latest_row = ath_cmj_data.iloc[-1]
            post_baseline = ath_cmj_data.iloc[1:] if len(ath_cmj_data) > 1 else pd.DataFrame()

            # KPI
            h_base = base_row[h_col] if base_row[h_col] > 0 else 1
            h_diff = ((latest_row[h_col] - base_row[h_col]) / h_base) * 100
            
            k1, k2, k3 = st.columns(3)
            k1.metric("Initial Baseline", f"{base_row[h_col]:.1f} cm")
            k2.metric("Latest Jump", f"{latest_row[h_col]:.1f} cm", f"{h_diff:+.1f}%")
            k3.metric("RSI Status", f"{float(latest_row[r_col]):.2f}", delta="Fatigued" if h_diff < -5 else "Recovered", delta_color="inverse" if h_diff < -5 else "normal")

            # MATCH CONTEXT
            st.markdown("#### Jump History & Match Context")
            combined_skills = pd.concat([swing_df, throw_df], ignore_index=True)
            combined_skills['Date'] = pd.to_datetime(combined_skills['Date'], errors='coerce')
            
            comp_list = []
            for _, row in post_baseline.iterrows():
                j_date = pd.to_datetime(row[date_col])
                try:
                    prev_matches = combined_skills[(combined_skills['Player Name'] == selected) & (combined_skills['Date'] < j_date) & (combined_skills['Session Type'].str.contains('Game|Match', case=False, na=False))]
                    pm_row = prev_matches.sort_values('Date', ascending=False).iloc[0]
                    m_info = f"{pm_row['Session Type']} ({pm_row['Date'].strftime('%m/%d')})"
                except:
                    m_info = "N/A"

                diff = float(row[h_col]) - float(base_row[h_col])
                comp_list.append({"Date": j_date.strftime('%m/%d/%Y'), "Match": m_info, "Height": f"{row[h_col]:.1f} cm", "Diff": diff, "RSI": f"{row[r_col]:.2f}"})

            table_html = """<table class="scout-table"><tr><th>Jump Date</th><th>Previous Match</th><th>Height</th><th>Vs. Baseline</th><th>RSI</th></tr>"""
            for i in comp_list:
                clr = "#28a745" if i['Diff'] >= 0 else "#dc3545"
                table_html += f"<tr><td>{i['Date']}</td><td>{i['Match']}</td><td>{i['Height']}</td><td style='color:{clr}; font-weight:bold;'>{i['Diff']:+.1f} cm</td><td>{i['RSI']}</td></tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

            # --- DUAL AXIS GRAPH (STABLE VERSION) ---
            st.markdown("#### Height vs. RSI Trend")
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Scatter(x=ath_cmj_data[date_col], y=ath_cmj_data[h_col], name="Height (cm)", line=dict(color='#4895DB', width=3)), secondary_y=False)
            fig.add_trace(go.Scatter(x=ath_cmj_data[date_col], y=ath_cmj_data[r_col], name="RSI", line=dict(color='#FF8200', width=2, dash='dot')), secondary_y=True)
            fig.add_hline(y=base_row[h_col], line_dash="dash", line_color="red", annotation_text="Baseline")
            fig.update_layout(height=400, template="simple_white", margin=dict(l=50, r=50, t=30, b=10), legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"))
            fig.update_yaxes(title_text="Height (cm)", secondary_y=False)
            fig.update_yaxes(title_text="RSI-mod", secondary_y=True)
            st.plotly_chart(fig, use_container_width=True, key=f"cmj_final_{selected}")
