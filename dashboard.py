import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. Password check using the secret
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        pwd = st.sidebar.text_input("Password", type="password")
        if pwd == st.secrets["password"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            if pwd: st.sidebar.error("Access Denied")
            st.stop()

check_password()

# 2. Connection and Data Merging
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def get_master_data():
    # Calling the individual links hidden in secrets
    roster = conn.read(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet_roster"])
    ash    = conn.read(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet_ash"])
    cmj    = conn.read(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet_cmj"])
    throws = conn.read(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet_throws"])
    swings = conn.read(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet_swings"])

    # Merge everything on Player Name
    data = roster.merge(ash, on="Player Name", how="left") \
                 .merge(cmj, on="Player Name", how="left") \
                 .merge(throws, on="Player Name", how="left") \
                 .merge(swings, on="Player Name", how="left")
    return data

df = get_master_data()

# 3. Interactive Visuals
st.title("Softball Performance")

# Create two columns for your main correlations
col1, col2 = st.columns(2)

with col1:
    x_col = st.selectbox("Select Physical Metric (X)", 
                         ['Peak Vertical Force [N]', 'RFD - 200ms [N/s]', 'Jump Height (Imp-Mom) [cm]'])
    y_col = st.selectbox("Select On-Field Metric (Y)", 
                         ['Sum Swing Max Player Load', 'Total Throw Count', 'Swing Max Rotation Band 3 Count'])

    fig = px.scatter(df, x=x_col, y=y_col, color="Position", 
                     hover_name="Player Name", trendline="ols",
                     template="plotly_dark", title=f"{x_col} vs {y_col}")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Quick leaderboard for a chosen metric
    leader_metric = st.selectbox("Leaderboard Metric", df.columns[4:])
    leaderboard = df[['Player Name', leader_metric]].sort_values(by=leader_metric, ascending=False)
    st.dataframe(leaderboard, hide_index=True)

# 4. Hidden Admin View
with st.expander("View Full Master Sheet (Admin Only)"):
    st.dataframe(df)

# CSS to keep it clean
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)
