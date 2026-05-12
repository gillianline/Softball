import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Softball Performance Hub", layout="wide")

# --- LADY VOL STYLE CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #FF8200; }
    .athlete-header {
        background-color: #F8F9FA; padding: 20px; border-radius: 15px; border-left: 10px solid #FF8200; margin-bottom: 25px;
    }
    .player-photo { border-radius: 50%; width: 150px; height: 150px; object-fit: cover; border: 4px solid #4895DB; }
    .stTabs [role="tab"] { font-weight: 800; color: #4895DB; font-size: 18px; }
    .stTabs [aria-selected="true"] { color: #FF8200; border-bottom-color: #FF8200; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_all_data():
    ash_df = pd.read_csv(st.secrets["ASH_URL"])
    cmj_df = pd.read_csv(st.secrets["CMJ_URL"])
    roster_df = pd.read_csv(st.secrets["ROSTER_URL"])
    
    for df in [ash_df, cmj_df, roster_df]:
        df.columns = df.columns.str.strip()
        d_col = next((c for c in ['Date', 'Test Date', 'date'] if c in df.columns), None)
        if d_col:
            df['Date'] = pd.to_datetime(df[d_col], errors='coerce').dt.tz_localize(None)
    return ash_df, cmj_df, roster_df

ash_df, cmj_df, roster_df = load_all_data()

# --- MAIN PAGE FILTERS ---
st.title("🥎 Lady Vol Performance")
f1, f2 = st.columns(2)

with f1:
    athlete_list = sorted(ash_df['Player Name'].unique())
    selected = st.selectbox("Search Athlete", athlete_list)

with f2:
    years = sorted(ash_df['Date'].dt.year.dropna().unique().astype(int), reverse=True)
    sel_year = st.selectbox("Select Season", ["All Time"] + years)

# --- FILTERING ---
def apply_filters(df, athlete, year):
    temp = df[df['Player Name'] == athlete].copy()
    if year != "All Time":
        temp = temp[temp['Date'].dt.year == year]
    return temp.sort_values('Date')

ash_f = apply_filters(ash_df, selected, sel_year)
cmj_f = apply_filters(cmj_df, selected, sel_year)

# --- HEADER ---
pic_row = roster_df[roster_df['Player Name'] == selected]
photo = pic_row['Picture'].values[0] if not pic_row.empty else "https://www.w3schools.com/howto/img_avatar.png"
st.markdown(f'<div class="athlete-header"><div style="display: flex; align-items: center;"><img src="{photo}" class="player-photo"><div style="margin-left: 30px;"><h1 style="margin:0;">{selected}</h1><p style="color:#4895DB; font-weight:700; margin:0;">SOFTBALL PERFORMANCE HUB</p></div></div></div>', unsafe_allow_html=True)

tab_ash, tab_cmj = st.tabs(["⚡ ASH TEST", "🚀 CMJ RECOVERY"])

with tab_ash:
    if not ash_f.empty:
        st.metric("Peak Force", f"{int(ash_f.iloc[-1].get('Peak Vertical Force [N]', 0))} N")
        
        # ASH Figure (No update_layout)
        fig_ash = go.Figure(
            data=[go.Scatter(x=ash_f['Date'], y=ash_f['Peak Vertical Force [N]'], mode='lines+markers', line=dict(color="#FF8200"))],
            layout=go.Layout(template="plotly_white", margin=dict(l=20, r=20, t=20, b=20), xaxis=dict(showgrid=False))
        )
        st.plotly_chart(fig_ash, use_container_width=True)

with tab_cmj:
    h_col = next((c for c in cmj_f.columns if 'Height' in c), None)
    r_col = next((c for c in cmj_f.columns if 'RSI' in c), None)

    if not cmj_f.empty and h_col and r_col:
        # CMJ Figure (Directly defining layout inside the constructor to avoid ValueError)
        fig_cmj = go.Figure(
            data=[
                go.Scatter(x=cmj_f['Date'], y=cmj_f[h_col], name="Height (cm)", mode='lines+markers', line=dict(color='#4895DB', width=3)),
                go.Scatter(x=cmj_f['Date'], y=cmj_f[r_col], name="RSI-mod", mode='lines+markers', line=dict(color='#FF8200', dash='dot'), yaxis="y2")
            ],
            layout=go.Layout(
                template="plotly_white",
                yaxis=dict(title="Height (cm)", titlefont=dict(color="#4895DB"), tickfont=dict(color="#4895DB")),
                yaxis2=dict(title="RSI", titlefont=dict(color="#FF8200"), tickfont=dict(color="#FF8200"), overlaying="y", side="right", showgrid=False),
                legend=dict(orientation="h", y=1.1),
                margin=dict(l=50, r=50, t=30, b=20)
            )
        )
        # Add baseline logic
        base_val = float(cmj_f.iloc[0][h_col])
        fig_cmj.add_shape(type="line", x0=cmj_f['Date'].min(), x1=cmj_f['Date'].max(), y0=base_val, y1=base_val, line=dict(color="Red", dash="dash"))
        
        st.plotly_chart(fig_cmj, use_container_width=True)
    else:
        st.warning("Data columns for Height or RSI not found.")
