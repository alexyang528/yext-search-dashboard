import pandas as pd
import streamlit as st
import snowflake.connector
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

pd.options.mode.chained_assignment = None

st.set_page_config(
    page_title="State of Search Business",
    page_icon="📈",
    layout="wide",
)

st.title("State of Search Business")
st.write("This dashboard shows the state of the Search business at Yext.")
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


def deal_card(deal, color="#D3D3D3"):

    business = deal["NAME"]
    value = "${:,.0f}".format(deal["NET_TOTAL_USD"])
    tier = deal["TIER"]
    start_date = format_date(deal["START_DATE"])
    end_date = format_date(deal["END_DATE"])
    close_date = format_date(deal["CLOSE_DATE"])

    return f"""
    <div class="card" style="background-color: {color}; padding: 8px; margin:8px; width:300px; border-radius: 10px; display:flex;">
        <div class="card-body" style="display: flex; flex-direction: column; justify-content: space-between; justify-content: space-between;">
            <h5 class="card-title" style="color: black;">{business[:20] + "..." if len(business) > 20 else business}</h5>
            <div class="card-text">
                <p style="color: black;">
                    <span>{value} TCV</span>
                </p>
                <p style="color: black;">
                    <span>{tier if tier == tier else "Additional 2M Searches"}</span>
                </p>
                <p style="color: black;">
                    <span>{start_date}</span>
                    to
                    <span>{end_date}</span>
                </p>
                <p style="color: black;">
                    <span>Deal Closed {close_date}</span>
                </p>
            </div>
        </div>
    </div>
    """


def deal_grid(deals, color="#D3D3D3"):

    cards = [deal_card(deal, color) for deal in deals.to_dict("records")]

    return f"""
    <div style="display: flex; flex-wrap: wrap;">
        {''.join(cards)}
    </div>
    """


def format_date(date):
    return pd.to_datetime(date).strftime("%B, %Y")


QUOTELINES = read_data("data/search_quotelines.csv")
QUOTELINES = QUOTELINES[QUOTELINES["NET_TOTAL_USD"] > 0]
QUOTELINES["FIRST_CLOSE_DATE"] = QUOTELINES.groupby("BUSINESS_ID")["CLOSE_DATE"].transform("min")
QUOTELINES["CONTRACT_TYPE"] = QUOTELINES.apply(
    lambda row: "New Logo" if row["CLOSE_DATE"] == row["FIRST_CLOSE_DATE"] else "Renewal", axis=1
)
QUOTELINES["FIRST_CLOSE_YEAR"] = pd.to_datetime(QUOTELINES["FIRST_CLOSE_DATE"]).dt.strftime("%Y")
QUOTELINES["COUNTRY"] = QUOTELINES["CURRENCY"].map(
    {"USD": "NA", "CAD": "NA", "EUR": "EMEA", "GBP": "EMEA", "JPY": "Japan", "AUD": "Australia"}
)

DAILY_ACV = read_data("data/search_acv_by_date.csv")
DAILY_ACV["MONTH"] = pd.to_datetime(DAILY_ACV["CALENDAR_DATE"]).dt.strftime("%Y-%m")
MONTHLY_ACV = DAILY_ACV.groupby("MONTH").last().reset_index()
MONTHLY_ACV["MoM Growth"] = MONTHLY_ACV["ACTIVE_ACV"].pct_change()
MONTHLY_ACV["YoY Growth"] = MONTHLY_ACV["ACTIVE_ACV"].pct_change(periods=12)
MONTHLY_ACV["CMGR"] = (MONTHLY_ACV["ACTIVE_ACV"] / MONTHLY_ACV["ACTIVE_ACV"].iloc[0]) ** (
    1 / MONTHLY_ACV.index
) - 1
MONTHLY_ACV["CAGR"] = (MONTHLY_ACV["ACTIVE_ACV"] / MONTHLY_ACV["ACTIVE_ACV"].iloc[0]) ** (
    1 / (MONTHLY_ACV.index / 12)
) - 1

tabs = st.tabs(["Overall", "Customer Summary", "Deals", "Specific Business"])
with tabs[0]:

    st.write("## Search ACV per Month")
    st.bar_chart(MONTHLY_ACV, x="MONTH", y="ACTIVE_ACV", height=500)

    st.write("## MoM Growth")
    st.bar_chart(MONTHLY_ACV, x="MONTH", y="MoM Growth", height=500)

    st.write("## YoY Growth")
    st.bar_chart(MONTHLY_ACV, x="MONTH", y="YoY Growth", height=500)


with tabs[1]:
    # Display a tree map of customers by Industry
    st.write("## Customers by Industry")
    st.write("Search customers by industry. Size represents total contract value (TCV).")

    industry_quotelines = QUOTELINES[~QUOTELINES["INDUSTRY"].isnull()]
    fig = px.treemap(
        industry_quotelines,
        path=[px.Constant("All"), "INDUSTRY", "NAME"],
        values="NET_TOTAL_USD",
        color="INDUSTRY",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        height=1000,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display a tree map of customers by sign-up year
    st.write("## Customers by Sign-up Year")
    st.write("Search customers by sign-up year. Size represents total contract value (TCV).")

    year_quotelines = QUOTELINES[~QUOTELINES["FIRST_CLOSE_YEAR"].isnull()]
    fig = px.treemap(
        year_quotelines,
        path=[px.Constant("All"), "FIRST_CLOSE_YEAR", "NAME"],
        values="NET_TOTAL_USD",
        color="FIRST_CLOSE_YEAR",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        height=1000,
    )
    fig.update_layout(
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Display a tree map of customers by country
    st.write("## Customers by Country")
    st.write("Search customers by country. Size represents total contract value (TCV).")

    country_quotelines = QUOTELINES[~QUOTELINES["COUNTRY"].isnull()]
    fig = px.treemap(
        country_quotelines,
        path=[px.Constant("All"), "COUNTRY", "NAME"],
        values="NET_TOTAL_USD",
        color="COUNTRY",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        height=1000,
    )
    fig.update_layout(
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)


with tabs[2]:
    st.write("# Search Deals")
    st.write("The 20 most recent new logo deals for Search, sorted by contract start date.")

    # List the most recent 20 deals
    st.write("## Recent New Logo Deals")
    st.write(
        deal_grid(
            QUOTELINES[QUOTELINES["CONTRACT_TYPE"] == "New Logo"]
            .sort_values("CLOSE_DATE", ascending=False)
            .head(20),
            color="#d2f8d2",
        ),
        unsafe_allow_html=True,
    )

    # List the most recent 20 renewals
    st.write("## Recent Renewal Deals")
    st.write("The 20 most recent renewals for Search, sorted by contract start date.")
    st.write(
        deal_grid(
            QUOTELINES[QUOTELINES["CONTRACT_TYPE"] == "Renewal"]
            .sort_values("CLOSE_DATE", ascending=False)
            .head(20),
            color="#d2d2f8",
        ),
        unsafe_allow_html=True,
    )

    # List the biggest businesses by total contract value (Sum of net_total_usd) all time
    st.write("## All time biggest businesses")
    st.write("The 10 businesses with the most total contract value, sorted by contract value.")

    top_businesses = (
        QUOTELINES.groupby(["BUSINESS_ID", "NAME"])
        .agg(
            {
                "NET_TOTAL_USD": "sum",
                "START_DATE": "min",
                "END_DATE": "max",
                "CLOSE_DATE": "min",
                "TIER": "last",
            }
        )
        .sort_values("NET_TOTAL_USD", ascending=False)
        .head(10)
    )
    # Go from multi index to single index
    top_businesses = top_businesses.reset_index()

    # Render a grid of deal cards
    st.write(deal_grid(top_businesses, color="#f8e5d2"), unsafe_allow_html=True)

with tabs[3]:
    # Picker of business ID and name on quotelines table
    business_id = st.selectbox(
        "Select a business",
        QUOTELINES.groupby(["BUSINESS_ID", "NAME"])
        .agg({"NET_TOTAL_USD": "sum"})
        .reset_index()
        .sort_values("NET_TOTAL_USD", ascending=False)
        .drop_duplicates()
        .values.tolist(),
        format_func=lambda x: x[1],
    )

    # Filter the quotelines table to only include the selected business
    business_quotelines = QUOTELINES[QUOTELINES["BUSINESS_ID"] == business_id[0]]
    business_quotelines.sort_values("START_DATE", inplace=True)

    # Display the business name
    st.write(f"# {business_id[1]}")
    st.write(
        f"## {business_quotelines['ACCOUNT_TYPE'].iloc[0]} /"
        f" {business_quotelines['INDUSTRY'].iloc[0]}"
    )

    st.write(
        f"## Total Contract Value: {'${:,.0f}'.format(business_quotelines['NET_TOTAL_USD'].sum())}"
    )

    # Display some high level information about the business' contract history
    st.write("## Contract History")
    st.write(f"- Originally closed in **{format_date(business_quotelines['CLOSE_DATE'].min())}**")
    st.write(
        f"- Currently contracted until **{format_date(business_quotelines['END_DATE'].max())}**"
    )

    # Display deal grid
    st.write(deal_grid(business_quotelines, color="#f8e5d2"), unsafe_allow_html=True)

    # Display the total contract value
    st.write("""---""")
    with st.expander("Contract Details"):
        st.write(business_quotelines)
