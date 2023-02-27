import pandas as pd
import streamlit as st
import snowflake.connector
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

pd.options.mode.chained_assignment = None

st.set_page_config(
    page_title="Search Feature KPIs",
    page_icon="📊",
    layout="wide",
)

st.title("Search Feature KPIs")
st.write("This dashboard shows the most important KPIs for Search features.")
st.write("""---""")


# # Initialize connection.
# # Uses st.cache_resource to only run once.
# @st.cache_resource
# def init_connection():
#     return snowflake.connector.connect(**st.secrets["snowflake"], client_session_keep_alive=True)

# CONN = init_connection()

# # Perform query.
# # Uses st.cache_data to only rerun when the query changes or after 10 min.
# @st.cache_data(ttl=600)
# def run_query(query):
#     with CONN.cursor() as cur:
#         cur.execute(query)
#         return cur.fetchall()


tabs = st.tabs(["Search Platform Screens", "Search Configuration Features", "Search APIs"])

with tabs[0]:
    st.write("## Search Platform Screens")

with tabs[1]:
    st.write("## Search Configuration Features")

with tabs[2]:
    st.write("## Search APIs")
