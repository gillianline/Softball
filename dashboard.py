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
def find_col(df, options):
    return next((c for c in options if c in df.columns), None)

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_data():
    try:
        urls = [st.secrets["ASH_URL"], st.secrets["CMJ_URL"], st.secrets["ROSTER_URL"], st.secrets["SWING_URL"], st.secrets["THROW_URL"]]
        dfs = [pd.read_csv(url) for url in urls]
        
        for df in dfs:
            df.columns = df.columns.str.strip()
            # Clean Athlete Names to ensure matches
            n_col = find_col(df, ['Player Name', 'Athlete', 'Name', 'Player'])
            if n_col:
                df[n_col] = df[n_col].astype(str).str.strip().str.upper()
                
        return dfs
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [pd.DataFrame()]*5

ash_df, cmj_df, roster_df, swing_df, throw_df = load_data()

# --- MAIN PAGE FILTERS ---
st.title("🥎 Performance Hub")
f1, f2 = st.columns(2)

with f1:
    name_col = find_col(ash_df, ['Player Name', 'Athlete', 'Name', 'Player'])
    athlete_list = sorted(ash_df[name_col].unique()) if name_col else []
    selected = st.selectbox("Search Athlete", athlete_list)

with f2:
    def get_years(df):
        d_col = find_col(df, ['Date', 'Test Date', 'date'])
        if d_col: return pd.to_datetime(df[d_col], errors='coerce').dt.year
        return pd.Series(dtype='int')
    all_years = pd.concat([get_years(ash_df), get_years(cmj_df)])
    years = sorted(all_years.dropna().unique().astype(int), reverse=True)
    sel_year = st.selectbox("Select Season", ["All Time"] + years)

# --- FILTERING ---
def clean_and_filter(df, year, athlete):
    d_col = find_col(df, ['Date', 'Test Date', 'date'])
    n_col = find_col(df, ['Player Name', 'Athlete', 'Name', 'Player'])
    if not n_col or not d_col: return pd.DataFrame()
    
    temp = df[df[n_col] == athlete].copy()
    temp['Date_Parsed'] = pd.to_datetime(temp[d_col], errors='coerce').dt.tz_localize(None)
    if year != "All Time":
        temp = temp[temp['Date_Parsed'].dt.year == year]
    return temp.sort_values('Date_Parsed')

ash_f = clean_and_filter(ash_df, sel_year, selected)
cmj_f = clean_and_filter(cmj_df, sel_year, selected)

# --- HEADER ---
r_name = find_col(roster_df, ['Player Name', 'Athlete', 'Name', 'Player'])
pic_row = roster_df[roster_df[r_name] == selected] if r_name else pd.DataFrame()
photo = pic_row['Picture'].values[0] if not pic_row.empty and 'Picture' in pic_row.columns else "https://www.w3schools.com/howto/img_avatar.png"

st.markdown(f"""
    <div class="athlete-header">
        <div style="display: flex; align-items: center;">
            <img src="{photo}" class="player-photo">
            <div style="margin-left: 30px;">
                <h1 style="margin:0;">{selected}</h1>
                <p style="color:#4895DB; font-weight:700; font-size:18px; margin:0;">LADY VOL PERFORMANCE DASHBOARD</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

tab_ash, tab_cmj = st.tabs(["⚡ ASH TEST", "🚀 CMJ RECOVERY"])

with tab_ash:
    if not ash_f.empty:
        latest = ash_f.iloc[-1]
        m1, m2, m3 = st.columns(3)
        m1.metric("Peak Force", f"{int(latest.get('Peak Vertical Force [N]', 0))} N")
        m2.metric("RFD (200ms)", f"{int(latest.get('RFD - 200ms [N/s]', 0))} N/s")
        m3.metric("Time to Peak", f"{latest.get('Start Time to Peak Force [s]', 0)}s")
        
        chart_ash = alt.Chart(ash_f).mark_line(color='#FF8200', size=3, point=True).encode(
            x=alt.X('Date_Parsed:T', title='Date'),
            y=alt.Y('Peak Vertical Force [N]:Q', scale=alt.Scale(zero=False))
        ).properties(height=350)
        st.altair_chart(chart_ash, use_container_width=True)
    else:
        st.warning("No ASH data found for selection.")

with tab_cmj:
    h_col = find_col(cmj_f, ['Jump Height (Imp-Mom) [cm]', 'Jump Height'])
    r_col = find_col(cmj_f, ['RSI-modified [m/s]', 'RSI-modified (Imp-Mom) [m/s]', 'RSI'])
    
    if not cmj_f.empty and h_col and r_col:
        base = alt.Chart(cmj_f).encode(alt.X('Date_Parsed:T', title='Date'))
        
        line_h = base.mark_line(color='#FF8200', size=3).encode(y=alt.Y(f'{h_col}:Q', title='Height (cm)'))
        point_h = base.mark_point(color='#FF8200', filled=True).encode(y=alt.Y(f'{h_col}:Q'))
        
        line_r = base.mark_line(color='#4895DB', strokeDash=[5,5], size=2).encode(y=alt.Y(f'{r_col}:Q', title='RSI'))
        point_r = base.mark_point(color='#4895DB').encode(y=alt.Y(f'{r_col}:Q'))
        
        combined = alt.layer(line_h + point_h, line_r + point_r).resolve_scale(y='independent').properties(height=400)
        st.altair_chart(combined.configure_axisLeft(titleColor='#FF8200').configure_axisRight(titleColor='#4895DB'), use_container_width=True)
        
        # Table
        base_val = float(cmj_f.iloc[0][h_col])
        comp_list = []
        for _, row in cmj_f.iterrows():
            diff = float(row[h_col]) - base_val
            comp_list.append({"Date": row['Date_Parsed'].strftime('%m/%d'), "Height": f"{row[h_col]:.1f}", "Diff": diff, "RSI": f"{row[r_col]:.2f}"})
        
        st.markdown("#### History")
        st.table(pd.DataFrame(comp_list))
    else:
        st.warning("No CMJ data found for selection.")
