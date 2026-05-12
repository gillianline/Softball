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

# --- UTILITY: DYNAMIC COLUMN FINDER ---
def find_col(df, options, default=None):
    return next((c for c in options if c in df.columns), default)

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

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_data():
    try:
        ash = pd.read_csv(st.secrets["ASH_URL"])
        cmj = pd.read_csv(st.secrets["CMJ_URL"])
        roster = pd.read_csv(st.secrets["ROSTER_URL"])
        swing = pd.read_csv(st.secrets["SWING_URL"])
        throw = pd.read_csv(st.secrets["THROW_URL"])
        
        # Strip whitespace from headers immediately
        for df in [ash, cmj, roster, swing, throw]:
            df.columns = df.columns.str.strip()
            
        return ash, cmj, roster, swing, throw
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [pd.DataFrame()]*5

ash_df, cmj_df, roster_df, swing_df, throw_df = load_data()

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e4/Tennessee_Volunteers_logo.svg", width=100)
    st.header("Global Filters")
    
    # Identify Athlete Name Column (e.g., 'Player Name' or 'Athlete')
    name_col = find_col(ash_df, ['Player Name', 'Athlete', 'Name', 'Player'])
    
    # Identify Date Column & Extract Years
    def get_year_series(df):
        d_col = find_col(df, ['Date', 'Test Date', 'date', 'test date'])
        if d_col: return pd.to_datetime(df[d_col], errors='coerce').dt.year
        return pd.Series(dtype='int')

    all_years = pd.concat([get_year_series(ash_df), get_year_series(cmj_df)])
    years = sorted(all_years.dropna().unique().astype(int), reverse=True)
    sel_year = st.selectbox("Select Season", ["All Time"] + years)
    
    # Athlete Selection
    athlete_list = sorted(ash_df[name_col].unique()) if name_col else []
    selected = st.selectbox("Search Athlete", athlete_list)

# --- GLOBAL FILTERING ---
def filter_data(df, year, athlete):
    d_col = find_col(df, ['Date', 'Test Date', 'date', 'test date'])
    n_col = find_col(df, ['Player Name', 'Athlete', 'Name', 'Player'])
    
    temp_df = df.copy()
    if n_col:
        temp_df = temp_df[temp_df[n_col] == athlete]
    if d_col:
        temp_df['Date_Parsed'] = pd.to_datetime(temp_df[d_col], errors='coerce').dt.tz_localize(None)
        if year != "All Time":
            temp_df = temp_df[temp_df['Date_Parsed'].dt.year == year]
    return temp_df

ash_f = filter_data(ash_df, sel_year, selected)
cmj_f = filter_data(cmj_df, sel_year, selected)
swing_f = filter_data(swing_df, sel_year, selected)
throw_f = filter_data(throw_df, sel_year, selected)

# --- HEADER ---
r_name_col = find_col(roster_df, ['Player Name', 'Athlete', 'Name', 'Player'])
pic_row = roster_df[roster_df[r_name_col] == selected] if r_name_col else pd.DataFrame()
photo = pic_row['Picture'].values[0] if not pic_row.empty and 'Picture' in pic_row.columns else "https://www.w3schools.com/howto/img_avatar.png"

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

# --- TAB 1: ASH ---
with tab_ash:
    if not ash_f.empty:
        latest = ash_f.iloc[-1]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Peak Force", f"{int(latest.get('Peak Vertical Force [N]', 0))} N")
        m2.metric("RFD (200ms)", f"{int(latest.get('RFD - 200ms [N/s]', 0))} N/s")
        m4.metric("Time to Peak", f"{latest.get('Start Time to Peak Force [s]', 0)}s")
        
        st.altair_chart(
            alt.Chart(ash_f).mark_line(color='#FF8200', size=3).encode(
                x='Date_Parsed:T', y=alt.Y('Peak Vertical Force [N]:Q', scale=alt.Scale(zero=False))
            ).properties(height=350), use_container_width=True
        )
    else:
        st.warning("No ASH data found for selection.")

# --- TAB 2: CMJ (ALTAIR DUAL-AXIS) ---
with tab_cmj:
    h_col = find_col(cmj_f, ['Jump Height (Imp-Mom) [cm]', 'Jump Height', 'Height'])
    r_col = find_col(cmj_f, ['RSI-modified [m/s]', 'RSI-modified (Imp-Mom) [m/s]', 'RSI'])
    
    if not cmj_f.empty and h_col and r_col:
        # Dual Axis Graph
        base = alt.Chart(cmj_f).encode(alt.X('Date_Parsed:T', axis=alt.Axis(title='Date')))
        line_h = base.mark_line(color='#FF8200', size=3).encode(y=alt.Y(f'{h_col}:Q', title='Height (cm)'))
        line_r = base.mark_line(color='#4895DB', strokeDash=[5,5], size=2).encode(y=alt.Y(f'{r_col}:Q', title='RSI'))
        
        st.altair_chart(
            alt.layer(line_h, line_r).resolve_scale(y='independent')
            .properties(width='container', height=400)
            .configure_axisLeft(titleColor='#FF8200', labelColor='#FF8200')
            .configure_axisRight(titleColor='#4895DB', labelColor='#4895DB'),
            use_container_width=True
        )

        # Table
        st.markdown("#### Season History")
        base_val = float(cmj_f.iloc[0][h_col])
        combined_skills = pd.concat([swing_f, throw_f], ignore_index=True)
        
        comp_list = []
        for _, row in cmj_f.iloc[1:].iterrows():
            diff = float(row[h_col]) - base_val
            comp_list.append({"Date": row['Date_Parsed'].strftime('%m/%d/%Y'), "Height": f"{row[h_col]:.1f} cm", "Diff": diff, "RSI": f"{row[r_col]:.2f}"})

        html = """<table class="scout-table"><tr><th>Date</th><th>Height</th><th>Vs Baseline</th><th>RSI</th></tr>"""
        for i in comp_list:
            clr = "#28a745" if i['Diff'] >= 0 else "#dc3545"
            html += f"<tr><td>{i['Date']}</td><td>{i['Height']}</td><td style='color:{clr}; font-weight:bold;'>{i['Diff']:+.1f} cm</td><td>{i['RSI']}</td></tr>"
        st.markdown(html + "</table>", unsafe_allow_html=True)
