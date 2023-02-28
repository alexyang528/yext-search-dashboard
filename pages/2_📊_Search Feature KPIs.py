from re import M
import pandas as pd
import streamlit as st

# import snowflake.connector
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statistics import mean

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


def read_data(file):
    return pd.read_csv(file)


##EXPERIENCE TRAINING
EXP_TRAINING = read_data("data/experience_training.csv")

# Convert dates to datetime
EXP_TRAINING["CALENDAR_DATE"] = pd.to_datetime(EXP_TRAINING["CALENDAR_DATE"])

# Calculate monthly ACV using ACV of last day of each month
EXP_TRAINING["MONTH"] = pd.to_datetime(EXP_TRAINING["CALENDAR_DATE"]).dt.strftime("%Y-%m")
MONTHLY_EXP = EXP_TRAINING.groupby("MONTH").last().reset_index()

######################################################################

##SEARCH MERCHANDISER
SEARCH_MERCH = read_data("data/search_merchandiser.csv")

# Convert dates to datetime
SEARCH_MERCH["CALENDAR_DATE"] = pd.to_datetime(SEARCH_MERCH["CALENDAR_DATE"])

# Calculate monthly ACV using ACV of last day of each month
SEARCH_MERCH["MONTH"] = pd.to_datetime(SEARCH_MERCH["CALENDAR_DATE"]).dt.strftime("%Y-%m")
MONTHLY_SM = SEARCH_MERCH.groupby("MONTH").last().reset_index()

######################################################################

##SEARCHABLE FIELDS
SEARCH_FIELDS = read_data("data/searchable_fields.csv")

# Convert dates to datetime
SEARCH_FIELDS["CALENDAR_DATE"] = pd.to_datetime(SEARCH_FIELDS["CALENDAR_DATE"])

# Calculate monthly ACV using ACV of last day of each month
# SEARCH_FIELDS["MONTH"] = pd.to_datetime(SEARCH_FIELDS["CALENDAR_DATE"]).dt.strftime("%Y-%m")
# might not use v
# MONTHLY_SF = SEARCH_FIELDS.groupby("MONTH").last().reset_index()

######################################################################

tabs = st.tabs(["Search Platform Screens", "Search Configuration Features", "Search APIs"])

with tabs[0]:

    st.info(
        f"""
        ## Summary
        #### As of February 2023, Experience Training has seen stagnant growth.
        It is still being used, with avg. monthly active user counts this year of {int(mean(MONTHLY_EXP["MAUS"].iloc[-6:]))} compared to a monthly active user count last year of {int(mean(MONTHLY_EXP["MAUS"].iloc[-12:-6]))}
        ##### We want to increase growth, as we still believe experience training plays a valuable role in the search ecosystem.
        To stir this growth we have an initiative to revamp our NLP Filter and Feature Snippet Training modules, currently being worked on by Backfire.

        """
    )

    ### Experience Training
    st.write("## Experience Training Adoption")

    st.write("## Daily Active Users Per Month")
    st.bar_chart(MONTHLY_EXP, x="MONTH", y="DAUS", height=500)

    st.write("## Monthly Active Users Per Month")
    st.bar_chart(MONTHLY_EXP, x="MONTH", y="MAUS", height=500)

    ### Search Merchandiser
    st.write("## Search Merchandiser Adoption")

    st.write("## Daily Active Users Per Month")
    st.bar_chart(MONTHLY_SM, x="MONTH", y="DAUS", height=500)

    st.write("## Monthly Active Users Per Month")
    st.bar_chart(MONTHLY_SM, x="MONTH", y="MAUS", height=500)


with tabs[1]:
    st.write("## Search Configuration Features")

    st.write("## Searchable Fields Usage")
    st.line_chart(
        SEARCH_FIELDS,
        x="CALENDAR_DATE",
        y=[
            "TEXT_SEARCH",
            "PHRASE_MATCH",
            "NLP_FILTER",
            "SEMANTIC_SEARCH",
            "DOCUMENT_SEARCH",
            "SORTABLE",
            "FACET",
            "STATICFILTER",
        ],
        height=500,
    )

with tabs[2]:
    st.write("## Search APIs")
