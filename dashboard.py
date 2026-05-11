import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import math

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
        
        # We also need the session/practice data for match context
        # (Assuming your master session data is in a secret named SESSION_URL)
        session_df = pd.read_csv(st.secrets["SESSION_URL"])
        
        def sanitize(df):
            df.columns = df.columns.str.strip()
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            if 'Test Date' in df.columns:
                df['Test Date'] = pd.to_datetime(df['Test Date'], errors='coerce')
            return df

        return sanitize(ash_df), sanitize(cmj_df), sanitize(roster_df), sanitize(session_df)
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

ash_df, cmj_df, roster_df, session_df = load_all_data()

if not ash_df.empty and not cmj_df.empty:
    athlete_list = sorted(list(set(ash_df['Player Name'].unique()) | set(cmj_df['Player Name'].unique())))
    selected = st.selectbox("Search Athlete", athlete_list)
    
    # Get Picture
    pic_row = roster_df[roster_df['Player Name'] == selected]
    photo = pic_row['Picture'].values[0] if not pic_row.empty and 'Picture' in roster_df.columns else "https://www.w3schools.com/howto/img_avatar.png"

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

    tab_ash, tab_cmj = st.tabs(["⚡ ASH TEST", "🚀 CMJ RECOVERY"])

    # --- TAB 1: ASH TEST ---
    with tab_ash:
        p_ash = ash_df[ash_df['Player Name'] == selected].sort_values('Date')
        if not p_ash.empty:
            latest = p_ash.iloc[-1]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Peak Force", f"{int(latest['Peak Vertical Force [N]'])} N")
            m2.metric("RFD (200ms)", f"{int(latest['RFD - 200ms [N/s]'])} N/s")
            asym = latest.get('Peak Vertical Force [N] (Asym)(%)', 0)
            m3.metric("Force Asym", f"{asym}%", delta="- Risk" if asym > 10 else None, delta_color="inverse")
            m4.metric("Time to Peak", f"{latest.get('Start Time to Peak Force [s]', 0)}s")
            st.plotly_chart(px.line(p_ash, x='Date', y='Peak Vertical Force [N]', markers=True, color_discrete_sequence=["#FF8200"], template="plotly_white"), use_container_width=True)

    # --- TAB 2: CMJ RECOVERY (INTEGRATED) ---
    with tab_cmj:
        st.markdown("### CMJ Baseline vs. Post-Match Recovery")
        
        # Syncing Athlete Name columns
        c_sync = cmj_df.rename(columns={'Athlete': 'Player Name'}) if 'Athlete' in cmj_df.columns else cmj_df.copy()
        ath_cmj_data = c_sync[c_sync['Player Name'] == selected].sort_values('Test Date')
        
        # Logic: Baseline = Wk 4, Comparison = Wk > 4
        baseline_cmj = ath_cmj_data[ath_cmj_data['Week'] == 4]
        post_match_cmj = ath_cmj_data[ath_cmj_data['Week'] > 4]

        if not baseline_cmj.empty:
            base_row = baseline_cmj.iloc[-1]
            h_col = 'Jump Height (Imp-Mom) [cm]'
            r_col = 'RSI-modified [m/s]'
            
            # 1. Summary Metrics
            st.markdown("#### Performance vs. Week 4 Baseline")
            latest_post = post_match_cmj.iloc[-1] if not post_match_cmj.empty else None
            
            if latest_post is not None:
                h_diff = ((latest_post[h_col] - base_row[h_col]) / (base_row[h_col] if base_row[h_col] > 0 else 1)) * 100
                rsi_diff = ((latest_post[r_col] - base_row[r_col]) / (base_row[r_col] if base_row[r_col] > 0 else 1)) * 100
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Baseline", f"{base_row[h_col]:.1f} cm")
                c2.metric("Latest Jump", f"{latest_post[h_col]:.1f} cm", f"{h_diff:+.1f}%")
                c3.metric("RSI", f"{latest_post[r_col]:.2f}", f"{rsi_diff:+.1f}%")

            # 2. History Table with Match Context
            st.markdown("#### Jump History & Match Context")
            comparison_list = []
            for _, row in post_match_cmj.iterrows():
                jump_date = pd.to_datetime(row['Test Date'])
                
                try:
                    # Look for matches using your double-column search logic
                    prev_matches = session_df[
                        (session_df['Player Name'] == selected) & 
                        (session_df['Date'] < jump_date) & 
                        ((session_df['Session_Name'].str.contains('Match|Game', case=False, na=False)) | 
                         (session_df['Session Type'].str.contains('Match|Game', case=False, na=False)))
                    ]
                    prev_match_name = prev_matches.sort_values('Date', ascending=False).iloc[0]['Session_Name']
                except:
                    prev_match_name = "N/A"

                raw_diff = float(row[h_col]) - float(base_row[h_col])
                comparison_list.append({
                    "Date": jump_date.strftime('%m/%d/%Y'),
                    "Prev Match": prev_match_name,
                    "Height": f"{row[h_col]:.1f} cm",
                    "Diff": raw_diff,
                    "Display": f"{raw_diff:+.1f} cm",
                    "RSI": f"{row[r_col]:.2f}"
                })

            # Render Table
            table_html = """<table class="scout-table">
                <tr><th>Jump Date</th><th>Previous Match</th><th>Jump Height</th><th>Vs. Baseline</th><th>RSI</th></tr>"""
            for item in comparison_list:
                color = "#28a745" if item['Diff'] >= 0 else "#dc3545"
                table_html += f"""<tr>
                    <td>{item['Date']}</td><td>{item['Prev Match']}</td><td>{item['Height']}</td>
                    <td style="font-weight:bold; color:{color};">{item['Display']}</td><td>{item['RSI']}</td>
                </tr>"""
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

            # 3. Dual-Axis Recovery Chart
            st.markdown("#### Height vs. RSI Trend")
            fig_cmj = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])
            
            fig_cmj.add_trace(go.Scatter(x=ath_cmj_data['Test Date'], y=ath_cmj_data[h_col], 
                                         name="Height (cm)", mode='lines+markers', line=dict(color='#4895DB', width=3)), secondary_y=False)
            fig_cmj.add_trace(go.Scatter(x=ath_cmj_data['Test Date'], y=ath_cmj_data[r_col], 
                                         name="RSI-mod", mode='lines+markers', line=dict(color='#FF8200', width=2, dash='dot')), secondary_y=True)
            
            fig_cmj.add_hline(y=base_row[h_col], line_dash="dash", line_color="red", annotation_text="Baseline")
            
            fig_cmj.update_layout(height=400, template="simple_white", margin=dict(l=50, r=50, t=30, b=10),
                                  legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"))
            fig_cmj.update_yaxes(title_text="Height (cm)", secondary_y=False)
            fig_cmj.update_yaxes(title_text="RSI-mod", secondary_y=True)
            st.plotly_chart(fig_cmj, use_container_width=True, key=f"cmj_final_{selected}")
        else:
            st.info("No Week 4 Baseline data found for this athlete.")
