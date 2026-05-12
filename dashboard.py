import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
        swing_df = pd.read_csv(st.secrets["SWING_URL"])
        throw_df = pd.read_csv(st.secrets["THROW_URL"])
        
        def sanitize(df):
            df.columns = df.columns.str.strip()
            # Dynamic date detection
            d_col = next((c for c in ['Date', 'Test Date', 'date'] if c in df.columns), None)
            if d_col:
                df[d_col] = pd.to_datetime(df[d_col], errors='coerce')
            return df

        return sanitize(ash_df), sanitize(cmj_df), sanitize(roster_df), sanitize(swing_df), sanitize(throw_df)
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

ash_df, cmj_df, roster_df, swing_df, throw_df = load_all_data()

# --- UI LOGIC ---
if not ash_df.empty:
    athlete_list = sorted(ash_df['Player Name'].unique())
    selected = st.selectbox("Search Athlete", athlete_list)
    
    pic_row = roster_df[roster_df['Player Name'] == selected]
    photo = pic_row['Picture'].values[0] if not pic_row.empty else "https://www.w3schools.com/howto/img_avatar.png"

    st.markdown(f"""
        <div class="athlete-header">
            <div style="display: flex; align-items: center;">
                <img src="{photo}" class="player-photo">
                <div style="margin-left: 30px;">
                    <h1 style="margin:0;">{selected}</h1>
                    <p style="color:#4895DB; font-weight:700; font-size:18px; margin:0;">SOFTBALL PERFORMANCE HUB</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    tab_ash, tab_cmj = st.tabs(["⚡ ASH PROFILE", "🚀 CMJ RECOVERY"])

    with tab_ash:
        d_col_ash = next((c for c in ['Date', 'Test Date', 'date'] if c in ash_df.columns), 'Date')
        p_ash = ash_df[ash_df['Player Name'] == selected].sort_values(d_col_ash)
        if not p_ash.empty:
            latest = p_ash.iloc[-1]
            # Safe numeric conversion for Asym
            try:
                asym = float(str(latest.get('Peak Vertical Force [N] (Asym)(%)', 0)).replace('%', '').strip())
            except:
                asym = 0.0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Peak Force", f"{int(latest.get('Peak Vertical Force [N]', 0))} N")
            m2.metric("RFD (200ms)", f"{int(latest.get('RFD - 200ms [N/s]', 0))} N/s")
            m3.metric("Force Asym", f"{asym}%", delta="- Risk" if asym > 10 else None, delta_color="inverse")
            m4.metric("Time to Peak", f"{latest.get('Start Time to Peak Force [s]', 0)}s")
            st.plotly_chart(px.line(p_ash, x=d_col_ash, y='Peak Vertical Force [N]', markers=True, color_discrete_sequence=["#FF8200"], template="plotly_white"), use_container_width=True)

    with tab_cmj:
        st.markdown("### CMJ Baseline vs. Post-Match Recovery")
        c_sync = cmj_df.rename(columns={'Athlete': 'Player Name'}) if 'Athlete' in cmj_df.columns else cmj_df.copy()
        
        d_col_cmj = next((c for c in ['Test Date', 'Date', 'date'] if c in c_sync.columns), 'Date')
        h_col = next((c for c in ['Jump Height (Imp-Mom) [cm]', 'Jump Height'] if c in c_sync.columns), 'Jump Height')
        r_col = next((c for c in ['RSI-modified [m/s]', 'RSI-modified (Imp-Mom) [m/s]', 'RSI'] if c in c_sync.columns), 'RSI')
        
        ath_cmj_data = c_sync[c_sync['Player Name'] == selected].sort_values(d_col_cmj)
        
        if not ath_cmj_data.empty:
            base_val = float(ath_cmj_data.iloc[0][h_col])
            
            # --- BYPASSING PLOTLY VALIDATORS USING RAW DICT ---
            chart_data = {
                "data": [
                    {
                        "x": ath_cmj_data[d_col_cmj].dt.strftime('%Y-%m-%d').tolist(),
                        "y": ath_cmj_data[h_col].tolist(),
                        "name": "Height (cm)",
                        "type": "scatter",
                        "mode": "lines+markers",
                        "line": {"color": "#4895DB", "width": 3}
                    },
                    {
                        "x": ath_cmj_data[d_col_cmj].dt.strftime('%Y-%m-%d').tolist(),
                        "y": ath_cmj_data[r_col].tolist(),
                        "name": "RSI-mod",
                        "type": "scatter",
                        "mode": "lines+markers",
                        "yaxis": "y2",
                        "line": {"color": "#FF8200", "width": 2, "dash": "dot"}
                    }
                ],
                "layout": {
                    "template": "plotly_white",
                    "xaxis": {"title": "Date", "showgrid": False},
                    "yaxis": {"title": "Height (cm)", "titlefont": {"color": "#4895DB"}, "tickfont": {"color": "#4895DB"}},
                    "yaxis2": {
                        "title": "RSI-mod",
                        "titlefont": {"color": "#FF8200"},
                        "tickfont": {"color": "#FF8200"},
                        "overlaying": "y",
                        "side": "right",
                        "showgrid": False
                    },
                    "legend": {"orientation": "h", "y": -0.3, "x": 0.5, "xanchor": "center"},
                    "margin": {"l": 50, "r": 50, "t": 30, "b": 10},
                    "shapes": [{
                        "type": "line",
                        "xref": "paper", "x0": 0, "x1": 1,
                        "yref": "y", "y0": base_val, "y1": base_val,
                        "line": {"color": "red", "width": 2, "dash": "dash"}
                    }]
                }
            }
            
            # This bypasses all the go.Layout code that was crashing
            st.plotly_chart(chart_data, use_container_width=True)

            # --- TABLE LOGIC REMAINS THE SAME ---
            st.markdown("#### Jump History")
            combined_skills = pd.concat([swing_df, throw_df], ignore_index=True)
            comp_list = []
            for _, row in ath_cmj_data.iloc[1:].iterrows():
                j_date = pd.to_datetime(row[d_col_cmj])
                try:
                    prev_m = combined_skills[(combined_skills['Player Name'] == selected) & (pd.to_datetime(combined_skills['Date']) < j_date) & (combined_skills['Session Type'].str.contains('Game|Match', case=False, na=False))]
                    pm_row = prev_m.sort_values('Date', ascending=False).iloc[0]
                    m_info = f"{pm_row['Session Type']} ({pd.to_datetime(pm_row['Date']).strftime('%m/%d')})"
                except: m_info = "N/A"
                
                diff = float(row[h_col]) - base_val
                comp_list.append({"Date": j_date.strftime('%m/%d/%Y'), "Match": m_info, "Height": f"{row[h_col]:.1f} cm", "Diff": diff, "RSI": f"{row[r_col]:.2f}"})

            html = """<table class="scout-table"><tr><th>Date</th><th>Prev Match</th><th>Height</th><th>Vs Baseline</th><th>RSI</th></tr>"""
            for i in comp_list:
                clr = "#28a745" if i['Diff'] >= 0 else "#dc3545"
                html += f"<tr><td>{i['Date']}</td><td>{i['Match']}</td><td>{i['Height']}</td><td style='color:{clr}; font-weight:bold;'>{i['Diff']:+.1f} cm</td><td>{i['RSI']}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)
