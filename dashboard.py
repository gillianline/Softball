import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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
        ash = pd.read_csv(st.secrets["ASH_URL"])
        cmj = pd.read_csv(st.secrets["CMJ_URL"])
        roster = pd.read_csv(st.secrets["ROSTER_URL"])
        
        for df in [ash, cmj, roster]:
            df.columns = df.columns.str.strip()
            # Clean names and dates
            n_col = find_col(df, ['Player Name', 'Athlete', 'Name', 'Player'])
            if n_col:
                df[n_col] = df[n_col].astype(str).str.strip().str.upper()
            d_col = find_col(df, ['Date', 'Test Date', 'date'])
            if d_col:
                df['Parsed_Date'] = pd.to_datetime(df[d_col], errors='coerce').dt.tz_localize(None)
                
        return ash, cmj, roster
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [pd.DataFrame()]*3

ash_df, cmj_df, roster_df = load_data()

# --- MAIN PAGE FILTERS ---
st.title("🥎 Performance Hub")
f1, f2 = st.columns(2)

with f1:
    n_col_main = find_col(ash_df, ['Player Name', 'Athlete', 'Name', 'Player'])
    # Only show athletes that actually have data
    athlete_list = sorted(ash_df[n_col_main].unique()) if n_col_main else []
    selected = st.selectbox("Search Athlete", athlete_list)

with f2:
    years = sorted(ash_df['Parsed_Date'].dt.year.dropna().unique().astype(int), reverse=True)
    sel_year = st.selectbox("Select Season", ["All Time"] + years)

# --- GLOBAL FILTERING ---
def get_filtered_data(df, athlete, year):
    n_col = find_col(df, ['Player Name', 'Athlete', 'Name', 'Player'])
    temp = df[df[n_col] == athlete].copy()
    if year != "All Time":
        temp = temp[temp['Parsed_Date'].dt.year == year]
    return temp.sort_values('Parsed_Date').dropna(subset=['Parsed_Date'])

ash_f = get_filtered_data(ash_df, selected, sel_year)
cmj_f = get_filtered_data(cmj_df, selected, sel_year)

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
                <p style="color:#4895DB; font-weight:700; font-size:18px; margin:0;">SOFTBALL PERFORMANCE | {sel_year}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

tab_ash, tab_cmj = st.tabs(["⚡ ASH TEST", "🚀 CMJ RECOVERY"])

# --- TAB 1: ASH ---
with tab_ash:
    if not ash_f.empty:
        latest = ash_f.iloc[-1]
        m1, m2 = st.columns(2)
        m1.metric("Peak Force", f"{int(latest.get('Peak Vertical Force [N]', 0))} N")
        m2.metric("RFD (200ms)", f"{int(latest.get('RFD - 200ms [N/s]', 0))} N/s")
        
        # Plotly Trace - Explicit and Robust
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ash_f['Parsed_Date'], 
            y=ash_f['Peak Vertical Force [N]'],
            mode='lines+markers',
            line=dict(color='#FF8200', width=4),
            marker=dict(size=8)
        ))
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=350,
            template="plotly_white",
            xaxis=dict(showgrid=False, title="Date"),
            yaxis=dict(title="Force (N)")
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No ASH data found.")

# --- TAB 2: CMJ ---
with tab_cmj:
    h_col = find_col(cmj_f, ['Jump Height (Imp-Mom) [cm]', 'Jump Height'])
    r_col = find_col(cmj_f, ['RSI-modified [m/s]', 'RSI-modified (Imp-Mom) [m/s]', 'RSI'])
    
    if not cmj_f.empty and h_col and r_col:
        # Dual-Axis Recovery Plot
        fig_cmj = go.Figure()
        
        fig_cmj.add_trace(go.Scatter(
            x=cmj_f['Parsed_Date'], y=cmj_f[h_col],
            name="Jump Height (cm)", mode='lines+markers',
            line=dict(color='#FF8200', width=3)
        ))
        
        fig_cmj.add_trace(go.Scatter(
            x=cmj_f['Parsed_Date'], y=cmj_f[r_col],
            name="RSI-mod", mode='lines+markers',
            line=dict(color='#4895DB', width=2, dash='dot'),
            yaxis="y2"
        ))
        
        fig_cmj.update_layout(
            height=400,
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(title="Height (cm)", titlefont=dict(color="#FF8200"), tickfont=dict(color="#FF8200")),
            yaxis2=dict(title="RSI", titlefont=dict(color="#4895DB"), tickfont=dict(color="#4895DB"), anchor="x", overlaying="y", side="right"),
            margin=dict(l=50, r=50, t=50, b=20)
        )
        
        st.plotly_chart(fig_cmj, use_container_width=True)
        
        # History List
        st.markdown("#### Season Sessions")
        history = cmj_f[['Parsed_Date', h_col, r_col]].copy()
        history['Display Date'] = history['Parsed_Date'].dt.strftime('%m/%d/%Y')
        st.dataframe(history[['Display Date', h_col, r_col]], use_container_width=True, hide_index=True)
    else:
        st.warning("No CMJ data found.")
