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
        required_keys = ["ASH_URL", "CMJ_URL", "ROSTER_URL", "SWING_URL", "THROW_URL"]
        for key in required_keys:
            if key not in st.secrets:
                st.error(f"Missing Secret Key: {key}")
                st.stop()

        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        swing_df = pd.read_csv(st.secrets["SWING_URL"])
        throw_df = pd.read_csv(st.secrets["THROW_URL"])
        
        def sanitize(df):
            df.columns = df.columns.str.strip()
            # Handle Date variations
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
    # Athlete Selection
    athlete_list = sorted(ash_df['Player Name'].unique())
    selected = st.selectbox("Search Athlete", athlete_list)
    
    # Photo Logic
    pic_row = roster_df[roster_df['Player Name'] == selected]
    photo = pic_row['Picture'].values[0] if not pic_row.empty and 'Picture' in roster_df.columns else "https://www.w3schools.com/howto/img_avatar.png"

    # Profile Header
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
            
            # --- SAFETY WRAP: Force asym to a float ---
            try:
                asym = float(str(latest.get('Peak Vertical Force [N] (Asym)(%)', 0)).replace('%', ''))
            except:
                asym = 0.0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Peak Force", f"{int(latest['Peak Vertical Force [N]'])} N")
            m2.metric("RFD (200ms)", f"{int(latest['RFD - 200ms [N/s]'])} N/s")
            
            # Now the comparison (asym > 10) will work perfectly
            m3.metric("Force Asym", f"{asym}%", 
                      delta="- Risk" if asym > 10 else None, 
                      delta_color="inverse")
            
            m4.metric("Time to Peak", f"{latest.get('Start Time to Peak Force [s]', 0)}s")
            
    # --- TAB 2: CMJ RECOVERY (NO WEEK COLUMN VERSION) ---
    with tab_cmj:
        st.markdown("### CMJ Baseline vs. Post-Match Recovery")
        
        # 1. Sync names and identify the Date column
        c_sync = cmj_df.rename(columns={'Athlete': 'Player Name'}) if 'Athlete' in cmj_df.columns else cmj_df.copy()
        
        # Find Date Column dynamically
        date_col = next((c for c in ['Test Date', 'Date', 'date', 'test date'] if c in c_sync.columns), None)
        
        if not date_col:
            st.error("⚠️ Data Error: Could not find a date column in the CMJ sheet.")
            st.stop()

        # 2. SORT & FILTER
        c_sync[date_col] = pd.to_datetime(c_sync[date_col], errors='coerce')
        ath_cmj_data = c_sync[c_sync['Player Name'] == selected].sort_values(date_col)
        
        if not ath_cmj_data.empty:
            # 3. BASELINE LOGIC: Use the first row as Baseline
            base_row = ath_cmj_data.iloc[0] 
            # Comparison: Everything after the first row
            post_baseline_data = ath_cmj_data.iloc[1:] if len(ath_cmj_data) > 1 else pd.DataFrame()

            h_col = 'Jump Height (Imp-Mom) [cm]'
            r_col = 'RSI-modified [m/s]'
            
            # KPI Metrics
            latest_row = ath_cmj_data.iloc[-1]
            if len(ath_cmj_data) > 1:
                h_base = base_row[h_col] if base_row[h_col] > 0 else 1
                h_diff = ((latest_row[h_col] - base_row[h_col]) / h_base) * 100
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Initial Baseline", f"{base_row[h_col]:.1f} cm")
                c2.metric("Latest Jump", f"{latest_row[h_col]:.1f} cm", f"{h_diff:+.1f}%")
                c3.metric("RSI Status", f"{latest_row[r_col]:.2f}", 
                          delta="Recovered" if h_diff > -5 else "Fatigued",
                          delta_color="normal" if h_diff > -5 else "inverse")

            # 4. HISTORY TABLE (with Swing/Throw Match Context)
            st.markdown("#### Jump History & Match Context")
            comparison_list = []
            
            # Combine skills sheets for match searching
            combined_skills = pd.concat([swing_df, throw_df], ignore_index=True)
            combined_skills['Date'] = pd.to_datetime(combined_skills['Date'], errors='coerce')
            
            # Show all jumps except the very first one (baseline) in the table
            for _, row in post_baseline_data.iterrows():
                jump_date = pd.to_datetime(row[date_col])
                try:
                    prev_matches = combined_skills[
                        (combined_skills['Player Name'] == selected) & 
                        (combined_skills['Date'] < jump_date) & 
                        (combined_skills['Session Type'].str.contains('Game|Match', case=False, na=False))
                    ]
                    prev_match_row = prev_matches.sort_values('Date', ascending=False).iloc[0]
                    prev_match_info = f"{prev_match_row['Session Type']} ({prev_match_row['Date'].strftime('%m/%d')})"
                except:
                    prev_match_info = "N/A"

                diff = float(row[h_col]) - float(base_row[h_col])
                comparison_list.append({
                    "Date": jump_date.strftime('%m/%d/%Y'),
                    "Match": prev_match_info,
                    "Height": f"{row[h_col]:.1f} cm",
                    "Diff": diff,
                    "RSI": f"{row[r_col]:.2f}"
                })

            table_html = """<table class="scout-table">
                <tr><th>Jump Date</th><th>Previous Match</th><th>Height</th><th>Vs. Baseline</th><th>RSI</th></tr>"""
            for item in comparison_list:
                color = "#28a745" if item['Diff'] >= 0 else "#dc3545"
                table_html += f"""<tr>
                    <td>{item['Date']}</td><td>{item['Match']}</td><td>{item['Height']}</td>
                    <td style="color:{color}; font-weight:bold;">{item['Diff']:+.1f} cm</td><td>{item['RSI']}</td>
                </tr>"""
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

            # 5. CHART
            fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Scatter(x=ath_cmj_data[date_col], y=ath_cmj_data[h_col], name="Height (cm)", line=dict(color='#4895DB', width=3)), secondary_y=False)
            fig.add_trace(go.Scatter(x=ath_cmj_data[date_col], y=ath_cmj_data[rsi_col], name="RSI", line=dict(color='#FF8200', width=2, dash='dot')), secondary_y=True)
            
            # Red Line at the Baseline Height
            fig.add_hline(y=base_row[h_col], line_dash="dash", line_color="red", annotation_text="Baseline")
            
            fig.update_layout(height=400, template="simple_white", margin=dict(l=50, r=50, t=30, b=10), legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center"))
            st.plotly_chart(fig, use_container_width=True, key=f"cmj_final_{selected}")
        else:
            st.info(f"No CMJ data found for {selected}.")
