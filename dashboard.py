import streamlit as st
import pandas as pd
import altair as alt

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance Hub", layout="wide")

# --- LADY VOL STYLE CSS ---
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
    st.stop()

# --- DATA LOADING & INITIAL CLEANING ---
@st.cache_data(ttl=300)
def load_data():
    try:
        ash = pd.read_csv(st.secrets["ASH_URL"])
        cmj = pd.read_csv(st.secrets["CMJ_URL"])
        roster = pd.read_csv(st.secrets["ROSTER_URL"])
        swing = pd.read_csv(st.secrets["SWING_URL"])
        throw = pd.read_csv(st.secrets["THROW_URL"])
        
        def sanitize(df):
            df.columns = df.columns.str.strip()
            # Standardize date column naming for the filter
            d_col = next((c for c in ['Date', 'Test Date', 'date'] if c in df.columns), 'Date')
            df['Date'] = pd.to_datetime(df[d_col], errors='coerce').dt.tz_localize(None)
            return df

        return sanitize(ash), sanitize(cmj), sanitize(roster), sanitize(swing), sanitize(throw)
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [pd.DataFrame()]*5

ash_df, cmj_df, roster_df, swing_df, throw_df = load_data()

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e4/Tennessee_Volunteers_logo.svg", width=100)
    st.header("Global Filters")
    
    # 1. Dynamic Year Detection (Fixed for KeyError)
    def get_years(df):
        # Look for any variation of a date column
        d_col = next((c for c in ['Date', 'Test Date', 'date', 'test date'] if c in df.columns), None)
        if d_col is not None:
            return pd.to_datetime(df[d_col], errors='coerce').dt.year
        return pd.Series(dtype='int')

    all_years_series = pd.concat([get_years(ash_df), get_years(cmj_df)])
    years = sorted(all_years_series.dropna().unique().astype(int), reverse=True)
    sel_year = st.selectbox("Select Season", ["All Time"] + years)
    
    # 2. Athlete Search
    all_athletes = sorted(ash_df['Player Name'].unique()) if 'Player Name' in ash_df.columns else []
    selected = st.selectbox("Search Athlete", all_athletes)

# --- GLOBAL FILTERING LOGIC ---
def apply_year_filter(df, year):
    if year == "All Time": 
        return df
    # Find the date column again to filter specifically for this df
    d_col = next((c for c in ['Date', 'Test Date', 'date', 'test date'] if c in df.columns), None)
    if d_col:
        # Convert to datetime temporarily to check the year
        temp_date = pd.to_datetime(df[d_col], errors='coerce')
        return df[temp_date.dt.year == year]
    return df

ash_f = apply_year_filter(ash_df, sel_year)
cmj_f = apply_year_filter(cmj_df, sel_year)
swing_f = apply_year_filter(swing_df, sel_year)
throw_f = apply_year_filter(throw_df, sel_year)


# --- ATHLETE HEADER ---
pic_row = roster_df[roster_df['Player Name'] == selected]
photo = pic_row['Picture'].values[0] if not pic_row.empty else "https://www.w3schools.com/howto/img_avatar.png"

st.markdown(f"""
    <div class="athlete-header">
        <div style="display: flex; align-items: center;">
            <img src="{photo}" class="player-photo">
            <div style="margin-left: 30px;">
                <h1 style="margin:0;">{selected}</h1>
                <p style="color:#4895DB; font-weight:700; font-size:18px; margin:0;">SOFTBALL PERFORMANCE | {sel_year}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

tab_ash, tab_cmj = st.tabs(["⚡ ASH PROFILE", "🚀 CMJ RECOVERY"])

# --- TAB 1: ASH PROFILE ---
with tab_ash:
    p_ash = ash_f[ash_f['Player Name'] == selected].sort_values('Date')
    if not p_ash.empty:
        latest = p_ash.iloc[-1]
        
        # Robust conversion for Asym
        try:
            asym_val = float(str(latest.get('Peak Vertical Force [N] (Asym)(%)', 0)).replace('%', '').strip())
        except:
            asym_val = 0.0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Peak Force", f"{int(latest.get('Peak Vertical Force [N]', 0))} N")
        m2.metric("RFD (200ms)", f"{int(latest.get('RFD - 200ms [N/s]', 0))} N/s")
        m3.metric("Force Asym", f"{asym_val}%", delta="- Risk" if asym_val > 10 else None, delta_color="inverse")
        m4.metric("Time to Peak", f"{latest.get('Start Time to Peak Force [s]', 0)}s")
        
        # Simple Line for ASH
        st.altair_chart(
            alt.Chart(p_ash).mark_line(color='#FF8200', size=3, interpolate='linear').encode(
                x=alt.X('Date:T', title='Date'),
                y=alt.Y('Peak Vertical Force [N]:Q', title='Force (N)', scale=alt.Scale(zero=False))
            ).properties(height=350), use_container_width=True
        )
    else:
        st.warning(f"No ASH data for {selected} in {sel_year}")

# --- TAB 2: CMJ RECOVERY (ALTAIR DUAL-AXIS) ---
with tab_cmj:
    st.markdown("### CMJ Baseline vs. Post-Match Recovery")
    
    # Sync name and identify columns
    c_sync = cmj_f.rename(columns={'Athlete': 'Player Name'}) if 'Athlete' in cmj_f.columns else cmj_f.copy()
    h_col = next((c for c in ['Jump Height (Imp-Mom) [cm]', 'Jump Height'] if c in c_sync.columns), 'Jump Height')
    r_col = next((c for c in ['RSI-modified [m/s]', 'RSI-modified (Imp-Mom) [m/s]', 'RSI'] if c in c_sync.columns), 'RSI')
    
    # Clean and force numeric for Altair stability
    chart_df = c_sync[c_sync['Player Name'] == selected].copy()
    chart_df[h_col] = pd.to_numeric(chart_df[h_col], errors='coerce')
    chart_df[r_col] = pd.to_numeric(chart_df[r_col], errors='coerce')
    chart_df = chart_df.dropna(subset=['Date', h_col, r_col]).sort_values('Date')
    
    if not chart_df.empty:
        # --- ALTAIR DUAL-AXIS ---
        base = alt.Chart(chart_df).encode(alt.X('Date:T', axis=alt.Axis(title='Date', format='%m/%d')))

        # Height (Orange - Left)
        line_h = base.mark_line(color='#FF8200', size=3, interpolate='linear').encode(
            y=alt.Y(f'{h_col}:Q', title='Jump Height (cm)', scale=alt.Scale(zero=False))
        )
        points_h = base.mark_point(color='#FF8200', filled=True, size=60).encode(y=alt.Y(f'{h_col}:Q'))

        # RSI (Blue - Right)
        line_r = base.mark_line(color='#4895DB', strokeDash=[5,5], size=2, interpolate='linear').encode(
            y=alt.Y(f'{r_col}:Q', title='RSI-mod', scale=alt.Scale(zero=False))
        )
        points_r = base.mark_point(color='#4895DB', size=60).encode(y=alt.Y(f'{r_col}:Q'))

        st.altair_chart(
            alt.layer((line_h + points_h), (line_r + points_r))
            .resolve_scale(y='independent')
            .properties(width='container', height=400)
            .configure_axisLeft(titleColor='#FF8200', labelColor='#FF8200')
            .configure_axisRight(titleColor='#4895DB', labelColor='#4895DB'),
            use_container_width=True
        )

        # --- MATCH HISTORY TABLE ---
        st.markdown("#### Season History & Match Context")
        comp_list = []
        base_val = float(chart_df.iloc[0][h_col])
        combined_skills = pd.concat([swing_f, throw_f], ignore_index=True)
        
        for _, row in chart_df.iloc[1:].iterrows():
            j_date = row['Date']
            try:
                prev_m = combined_skills[
                    (combined_skills['Player Name'] == selected) & 
                    (combined_skills['Date'] < j_date) & 
                    (combined_skills['Session Type'].str.contains('Game|Match', case=False, na=False))
                ]
                pm_row = prev_m.sort_values('Date', ascending=False).iloc[0]
                m_info = f"{pm_row['Session Type']} ({pm_row['Date'].strftime('%m/%d')})"
            except: m_info = "N/A"
            
            diff = float(row[h_col]) - base_val
            comp_list.append({"Date": j_date.strftime('%m/%d/%Y'), "Match": m_info, "Height": f"{row[h_col]:.1f} cm", "Diff": diff, "RSI": f"{row[r_col]:.2f}"})

        html = """<table class="scout-table"><tr><th>Date</th><th>Prev Match</th><th>Height</th><th>Vs Baseline</th><th>RSI</th></tr>"""
        for i in comp_list:
            clr = "#28a745" if i['Diff'] >= 0 else "#dc3545"
            html += f"<tr><td>{i['Date']}</td><td>{i['Match']}</td><td>{i['Height']}</td><td style='color:{clr}; font-weight:bold;'>{i['Diff']:+.1f} cm</td><td>{i['RSI']}</td></tr>"
        st.markdown(html + "</table>", unsafe_allow_html=True)
    else:
        st.info(f"No CMJ test data recorded for {selected} in {sel_year}.")
