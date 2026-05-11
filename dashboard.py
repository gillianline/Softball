import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. UI Setup & Branding
st.set_page_config(page_title="Softball Performance", layout="wide")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

# 2. Secret-Based Password Protection
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if not st.session_state["authenticated"]:
        # Centering the login box
        _, col2, _ = st.columns([1,1,1])
        with col2:
            st.title("🔐 Login")
            pwd = st.text_input("Enter Access Key", type="password")
            if st.button("Access Dashboard"):
                if pwd == st.secrets["password"]:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Invalid Key")
        st.stop()

check_password()

# 3. Data Connection (Links hidden in Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def load_and_sync_data():
    # This version looks for the keys directly in st.secrets
    # Use this if your secrets are NOT nested under [connections.gsheets]
    roster = conn.read(spreadsheet=st.secrets["spreadsheet_roster"])
    ash    = conn.read(spreadsheet=st.secrets["spreadsheet_ash"])
    cmj    = conn.read(spreadsheet=st.secrets["spreadsheet_cmj"])
    throws = conn.read(spreadsheet=st.secrets["spreadsheet_throws"])
    swings = conn.read(spreadsheet=st.secrets["spreadsheet_swings"])

    # Clean column names (remove whitespace)
    for data_frame in [roster, ash, cmj, throws, swings]:
        data_frame.columns = data_frame.columns.str.strip()

    # Merging logic (ensure 'Player Name' is the exact column name in all 5 sheets)
    master = roster.merge(ash, on="Player Name", how="left") \
                   .merge(cmj, on="Player Name", how="left") \
                   .merge(throws, on="Player Name", how="left") \
                   .merge(swings, on="Player Name", how="left")
    return master

df = load_and_sync_data()

# 4. Dashboard Logic
st.title("🥎 Softball Analytics Dashboard")

# Top Metrics Row
cols = st.columns(4)
cols[0].metric("Roster Size", len(df))
cols[1].metric("Avg Peak Power", f"{int(df['Peak Power [W]'].mean())}W")
cols[2].metric("High Load Swings", df['Swing Max Rotation Band 3 Count'].sum())
cols[3].metric("Throw Volume", df['Total Throw Count'].sum())

st.divider()

# Correlation Section
st.subheader("Performance Correlations")
c1, c2 = st.columns([2, 1])

with c1:
    # Selectors for X and Y axis
    x_axis = st.selectbox("Choose Physical Metric", 
                          ['Peak Vertical Force [N]', 'RFD - 200ms [N/s]', 'Jump Height (Imp-Mom) [cm]', 'Peak Power [W]'])
    y_axis = st.selectbox("Choose Skill Metric", 
                          ['Sum Swing Max Player Load', 'Swing Max Rotation Band 3 Count', 'Total Throw Player Load'])

    fig = px.scatter(df, x=x_axis, y=y_axis, color="Position", 
                     hover_name="Player Name", trendline="ols",
                     template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.write("### Position Rankings")
    rank_metric = st.selectbox("Rank by:", [x_axis, y_axis])
    ranking = df[['Player Name', rank_metric, 'Position']].sort_values(by=rank_metric, ascending=False)
    st.dataframe(ranking, hide_index=True, use_container_width=True)

# 5. Hidden Data View
with st.expander("Admin: View Master Sheet"):
    st.dataframe(df)
