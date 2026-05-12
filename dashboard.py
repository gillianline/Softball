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
def load_all_data():
    try:
        ash_df = pd.read_csv(st.secrets["ASH_URL"])
        cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
        roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
        swing_df = pd.read_csv(st.secrets["SWING_URL"])
        throw_df = pd.read_csv(st.secrets["THROW_URL"])
        
        # Clean white space and force date conversion
        for df in [ash_df, cmj_df, roster_df, swing_df, throw_df]:
            df.columns = df.columns.str.strip()
            d_col = next((c for c in ['Date', 'Test Date', 'date'] if c in df.columns), None)
            if d_col:
                df[d_col] = pd.to_datetime(df[d_col], errors='coerce')
        
        return ash_df, cmj_df, roster_df, swing_df, throw_df
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return [pd.DataFrame()]*5

ash_df, cmj_df, roster_df, swing_df, throw_df = load_all_data()

# --- MAIN PAGE FILTERS ---
st.title("Lady Vol Performance")
f1, f2 = st.columns(2)

with f1:
    athlete_list = sorted(ash_df['Player Name'].unique()) if 'Player Name' in ash_df.columns else []
    selected = st.selectbox("Search Athlete", athlete_list)

with f2:
    # Get years for filter
    all_dates = pd.concat([ash_df['Date'], cmj_df['Date']])
    unique_years = sorted(all_dates.dt.year.dropna().unique().astype(int), reverse=True)
    sel_year = st.selectbox("Select Season", ["All Time"] + unique_years)

# --- FILTERING LOGIC ---
def apply_filters(df, athlete, year):
    temp = df[df['Player Name'] == athlete].copy()
    if year != "All Time":
        temp = temp[temp['Date'].dt.year == year]
    return temp.sort_values('Date')

ash_f = apply_filters(ash_df, selected, sel_year)
cmj_f = apply_filters(cmj_df, selected, sel_year)
swing_f = apply_filters(swing_df, selected, sel_year)
throw_f = apply_filters(throw_df, selected, sel_year)

# --- ATHLETE HEADER ---
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

tab_ash, tab_cmj = st.tabs(["⚡ ASH TEST", "🚀 CMJ RECOVERY"])

# --- TAB 1: ASH ---
with tab_ash:
    if not ash_f.empty:
        latest = ash_f.iloc[-1]
        m1, m2 = st.columns(2)
        m1.metric("Peak Force", f"{int(latest.get('Peak Vertical Force [N]', 0))} N")
        m2.metric("RFD (200ms)", f"{int(latest.get('RFD - 200ms [N/s]', 0))} N/s")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ash_f['Date'], y=ash_f['Peak Vertical Force [N]'], mode='lines+markers', line=dict(color="#FF8200", width=3)))
        fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20), xaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: CMJ (VOLLEYBALL DUAL-AXIS LOGIC) ---
with tab_cmj:
    # Detect specific volleyball-style columns
    h_col = next((c for c in cmj_f.columns if 'Height' in c), 'Jump Height')
    r_col = next((c for c in cmj_f.columns if 'RSI' in c), 'RSI-modified [m/s]')

    if not cmj_f.empty:
        fig = go.Figure()
        
        # Primary Axis (Height)
        fig.add_trace(go.Scatter(x=cmj_f['Date'], y=cmj_f[h_col], name="Height (cm)", mode='lines+markers', line=dict(color='#4895DB', width=3)))
        
        # Secondary Axis (RSI)
        fig.add_trace(go.Scatter(x=cmj_f['Date'], y=cmj_f[r_col], name="RSI-mod", mode='lines+markers', line=dict(color='#FF8200', width=2, dash='dot'), yaxis="y2"))
        
        fig.update_layout(
            template="plotly_white",
            yaxis=dict(title="Height (cm)", titlefont=dict(color="#4895DB"), tickfont=dict(color="#4895DB")),
            yaxis2=dict(title="RSI-mod", titlefont=dict(color="#FF8200"), tickfont=dict(color="#FF8200"), overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            margin=dict(l=50, r=50, t=30, b=20)
        )
        
        # Add Baseline (Volleyball Logic)
        base_val = cmj_f.iloc[0][h_col]
        fig.add_hline(y=base_val, line_dash="dash", line_color="red", annotation_text="Baseline")
        
        st.plotly_chart(fig, use_container_width=True)

        # History Table
        st.markdown("#### Session History")
        history = cmj_f[['Date', h_col, r_col]].copy()
        history['Date'] = history['Date'].dt.strftime('%m/%d/%Y')
        st.dataframe(history, use_container_width=True, hide_index=True)
