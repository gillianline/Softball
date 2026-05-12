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
    .scout-table { width: 100%; border-collapse: collapse; text-align: center; margin-top: 10px;}
    .scout-table th { background-color: #4895DB; color: white; padding: 8px; border-bottom: 2px solid #FF8200; text-transform: uppercase; font-size: 12px; }
    .scout-table td { padding: 8px; border-bottom: 1px solid #F5F5F7; font-size: 12px; }
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_data():
    try:
        ash = pd.read_csv(st.secrets["ASH_URL"])
        cmj = pd.read_csv(st.secrets["CMJ_URL"])
        roster = pd.read_csv(st.secrets["ROSTER_URL"])
        
        for df in [ash, cmj, roster]:
            df.columns = df.columns.str.strip()
            # Find name/date columns regardless of specific labeling
            n_col = next((c for c in ['Player Name', 'Athlete', 'Name'] if c in df.columns), None)
            d_col = next((c for c in ['Date', 'Test Date', 'date'] if c in df.columns), None)
            if n_col: df[n_col] = df[n_col].astype(str).str.strip()
            if d_col: df['Parsed_Date'] = pd.to_datetime(df[d_col], errors='coerce').dt.tz_localize(None)
                
        return ash, cmj, roster
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [pd.DataFrame()]*3

ash_df, cmj_df, roster_df = load_data()

# --- MAIN PAGE FILTERS ---
st.title("🥎 Performance Hub")
f1, f2 = st.columns(2)

with f1:
    n_col = next((c for c in ['Player Name', 'Athlete', 'Name'] if c in ash_df.columns), 'Player Name')
    athlete_list = sorted(ash_df[n_col].unique())
    selected = st.selectbox("Search Athlete", athlete_list)

with f2:
    years = sorted(ash_df['Parsed_Date'].dt.year.dropna().unique().astype(int), reverse=True)
    sel_year = st.selectbox("Select Season", ["All Time"] + years)

# --- FILTERING ---
def filter_df(df, athlete, year):
    n_col = next((c for c in ['Player Name', 'Athlete', 'Name'] if c in df.columns), 'Player Name')
    temp = df[df[n_col] == athlete].copy()
    if year != "All Time":
        temp = temp[temp['Parsed_Date'].dt.year == year]
    return temp.sort_values('Parsed_Date')

ash_f = filter_df(ash_df, selected, sel_year)
cmj_f = filter_df(cmj_df, selected, sel_year)

# --- HEADER ---
r_name = next((c for c in ['Player Name', 'Athlete', 'Name'] if c in roster_df.columns), 'Player Name')
pic_row = roster_df[roster_df[r_name] == selected]
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

tab_ash, tab_cmj = st.tabs(["⚡ ASH TEST", "🚀 CMJ RECOVERY"])

with tab_ash:
    if not ash_f.empty:
        latest = ash_f.iloc[-1]
        m1, m2 = st.columns(2)
        m1.metric("Peak Force", f"{int(latest.get('Peak Vertical Force [N]', 0))} N")
        m2.metric("RFD (200ms)", f"{int(latest.get('RFD - 200ms [N/s]', 0))} N/s")
        
        # Single Axis Stable Chart
        st.plotly_chart({
            "data": [{"x": ash_f['Parsed_Date'].tolist(), "y": ash_f['Peak Vertical Force [N]'].tolist(), "type": "scatter", "mode": "lines+markers", "line": {"color": "#FF8200"}}],
            "layout": {"template": "plotly_white", "xaxis": {"title": "Date"}, "yaxis": {"title": "Force (N)"}}
        }, use_container_width=True)

with tab_cmj:
    # 1. Column Search
    h_col = next((c for c in cmj_f.columns if 'height' in c.lower()), None)
    r_col = next((c for c in cmj_f.columns if 'rsi' in c.lower()), None)

    if not cmj_f.empty and h_col and r_col:
        # 2. Data Cleaning
        plot_df = cmj_f.copy()
        plot_df[h_col] = pd.to_numeric(plot_df[h_col], errors='coerce')
        plot_df[r_col] = pd.to_numeric(plot_df[r_col], errors='coerce')
        plot_df = plot_df.dropna(subset=[h_col, r_col])

        # 3. Construct the Chart Dict
        chart_dict = {
            "data": [
                {
                    "x": plot_df['Parsed_Date'].dt.strftime('%Y-%m-%d').tolist(),
                    "y": plot_df[h_col].tolist(),
                    "name": "Jump Height", "type": "scatter", "mode": "lines+markers",
                    "line": {"color": "#FF8200", "width": 3}
                },
                {
                    "x": plot_df['Parsed_Date'].dt.strftime('%Y-%m-%d').tolist(),
                    "y": plot_df[r_col].tolist(),
                    "name": "RSI-mod", "type": "scatter", "mode": "lines+markers",
                    "yaxis": "y2", "line": {"color": "#4895DB", "width": 2, "dash": "dot"}
                }
            ],
            "layout": {
                "template": "plotly_white",
                "height": 450,
                "legend": {"orientation": "h", "y": 1.1, "x": 0.5, "xanchor": "center"},
                "xaxis": {"title": "Date", "showgrid": False},
                "yaxis": {
                    "title": "Height (cm)", 
                    "titlefont": {"color": "#FF8200"}, 
                    "tickfont": {"color": "#FF8200"},
                    "showgrid": False
                },
                "yaxis2": {
                    "title": "RSI-mod", 
                    "titlefont": {"color": "#4895DB"}, 
                    "tickfont": {"color": "#4895DB"}, 
                    "overlaying": "y", 
                    "side": "right", 
                    "showgrid": False
                },
                "margin": {"l": 50, "r": 50, "t": 60, "b": 40}
            }
        }
        
        # CRITICAL FIX: validate_figure=False bypasses the Python 3.14 bug
        st.plotly_chart(chart_dict, use_container_width=True, theme=None)
        
        # 4. History Table
        st.markdown("#### Session History")
        table_df = plot_df[['Parsed_Date', h_col, r_col]].copy()
        table_df['Date'] = table_df['Parsed_Date'].dt.strftime('%m/%d/%Y')
        st.dataframe(table_df[['Date', h_col, r_col]], use_container_width=True, hide_index=True)
        
    else:
        st.warning("Could not find matching Height or RSI columns.")
