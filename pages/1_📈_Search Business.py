import pandas as pd
import streamlit as st
# import snowflake.connector
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


# Initialize connection.
# Uses st.cache_resource to only run once.
# @st.cache_resource
# def init_connection():
#     return snowflake.connector.connect(**st.secrets["snowflake"], client_session_keep_alive=True)


# CONN = init_connection()

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
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


def format_usd(value, round="M"):
    if round == "M":
        return "${:,.1f}M".format(value / 1000000)
    elif round == "K":
        return "${:,.1f}K".format(value / 1000)
    else:
        return "${:,.0f}".format(value)


def format_percentage(value):
    return "{:.1%}".format(value)


# Read quotelines file
QUOTELINES = read_data("data/search_quotelines.csv")

# Filter out deals with no TCV (unrelated upgrades, cancellations, etc.)
QUOTELINES = QUOTELINES[QUOTELINES["NET_TOTAL_USD"] > 0]

# Convert dates to datetime
QUOTELINES["CLOSE_DATE"] = pd.to_datetime(QUOTELINES["CLOSE_DATE"])
QUOTELINES["START_DATE"] = pd.to_datetime(QUOTELINES["START_DATE"])
QUOTELINES["END_DATE"] = pd.to_datetime(QUOTELINES["END_DATE"])
QUOTELINES["FIRST_CLOSE_DATE"] = QUOTELINES.groupby("BUSINESS_ID")["CLOSE_DATE"].transform("min")
QUOTELINES["COUNTRY"] = QUOTELINES["CURRENCY"].map(
    {"USD": "NA", "CAD": "NA", "EUR": "EMEA", "GBP": "EMEA", "JPY": "Japan"}
)

# Calculate additional contract details
QUOTELINES["CONTRACT_TYPE"] = QUOTELINES.apply(
    lambda row: "New Logo" if row["CLOSE_DATE"] == row["FIRST_CLOSE_DATE"] else "Renewal", axis=1
)

# Get businesses dataframe
BUSINESSES = (
    QUOTELINES.groupby(["BUSINESS_ID", "NAME", "INDUSTRY", "COUNTRY"])
    .agg(
        {
            "NET_TOTAL_USD": "sum",
            "CLOSE_DATE": "min",
            "START_DATE": "min",
            "END_DATE": "max",
        }
    )
    .reset_index()
)

BUSINESSES["ACV_USD"] = BUSINESSES["NET_TOTAL_USD"] / (
    (BUSINESSES["END_DATE"] - BUSINESSES["START_DATE"]).dt.days / 365
)
BUSINESSES["IS_ACTIVE"] = BUSINESSES["END_DATE"].apply(lambda x: x >= pd.to_datetime("today"))
BUSINESSES["CLOSE_YEAR"] = pd.to_datetime(BUSINESSES["CLOSE_DATE"]).dt.strftime("%Y")
BUSINESSES = BUSINESSES[
    (
        ~BUSINESSES["INDUSTRY"].isnull()
        & ~BUSINESSES["CLOSE_DATE"].isnull()
        & ~BUSINESSES["COUNTRY"].isnull()
    )
]
ACTIVE_BUSINESSES = BUSINESSES[BUSINESSES["IS_ACTIVE"]]

# Read daily ACV file
DAILY_ACV = read_data("data/search_acv_by_date.csv")

# Convert dates to datetime
DAILY_ACV["CALENDAR_DATE"] = pd.to_datetime(DAILY_ACV["CALENDAR_DATE"])

# Calculate monthly ACV using ACV of last day of each month
DAILY_ACV["MONTH"] = pd.to_datetime(DAILY_ACV["CALENDAR_DATE"]).dt.strftime("%Y-%m")
MONTHLY_ACV = DAILY_ACV.groupby("MONTH").last().reset_index()
MONTHLY_ACV["MoM Growth"] = MONTHLY_ACV["ACTIVE_ACV"].pct_change()
MONTHLY_ACV["YoY Growth"] = MONTHLY_ACV["ACTIVE_ACV"].pct_change(periods=12)

# Calculate CAGR and CMGR for last 12 months
LAST_12_ACV = MONTHLY_ACV.tail(13).reset_index()
LAST_12_ACV.drop(["index", "CALENDAR_DATE"], axis=1, inplace=True)
LAST_12_ACV["CMGR"] = (LAST_12_ACV["ACTIVE_ACV"] / LAST_12_ACV["ACTIVE_ACV"].iloc[0]) ** (
    1 / LAST_12_ACV.index
) - 1
LAST_12_ACV["CAGR"] = (LAST_12_ACV["ACTIVE_ACV"] / LAST_12_ACV["ACTIVE_ACV"].iloc[0]) ** (
    1 / (LAST_12_ACV.index / 12)
) - 1
LAST_12_ACV = LAST_12_ACV.tail(12)

tabs = st.tabs(["Overall", "Customer Summary", "Deals", "Specific Business"])
with tabs[0]:

    st.info(
        f"""
        ## Summary
        #### As of February 2023, Yext Search has {format_usd(MONTHLY_ACV['ACTIVE_ACV'].iloc[-1])} in annual contract value (ACV).
        This compares to **\{format_usd(MONTHLY_ACV['ACTIVE_ACV'].iloc[-2])} in January 2023**, or 
        {format_percentage(MONTHLY_ACV['MoM Growth'].iloc[-1])} growth month-over-month (MoM); 
        or, **\{format_usd(MONTHLY_ACV['ACTIVE_ACV'].iloc[-12])} in February 2022**, and 
        {format_percentage(MONTHLY_ACV['YoY Growth'].iloc[-1])} growth year-over-year (YoY).
        
        [Coveo](https://ir.coveo.com/en/news-events/press-releases/detail/241/coveo-reports-fourth-quarter-and-fiscal-year-2022-financial) 
        reported **\$77.9M** in SaaS subscription revenue in FY22 with a growth rate of 41% YoY, and 
        [Algolia](https://getlatka.com/companies/algolia) reportedly has an annual revenue of **\$75M**.

        #### Yext Search has captured \{format_usd(QUOTELINES['NET_TOTAL_USD'].sum())} in total contract value (TCV) since inception.
        In the same ballpark timeframe, Reviews (Response, Monitoring, and Generation) captured 
        approximately **\$50-60M**, Pages captured about **\$80-100M**, and Listings captured **\$300M+**. 
        _Note this only includes contracts in Zuora, which was first implemented in 2020 and probably 
        disproportionally excludes other products._

        #### Over the past 12 months, Yext Search has grown at a compound monthly growth rate (CMGR) of {format_percentage(LAST_12_ACV['CMGR'].iloc[-1])}, and a compound annual growth rate (CAGR) of {format_percentage(LAST_12_ACV['CAGR'].iloc[-1])}.
        This compares favorably to industry averages [published by SaaS Capital](https://www.saas-capital.com/research/2020-private-saas-company-growth-rate-benchmarks/), 
        which states that **startups between \$10M and \$20M in revenue average a growth rate of 43%**.

        #### Last month, Yext Search closed \{format_usd(QUOTELINES[QUOTELINES['CLOSE_DATE'].dt.strftime('%Y-%m') == '2023-01']['NET_TOTAL_USD'].sum())} in TCV, compared to \{format_usd(QUOTELINES[QUOTELINES['CLOSE_DATE'].dt.strftime('%Y-%m') == '2022-12']['NET_TOTAL_USD'].sum())} in the previous month, or \{format_usd(QUOTELINES[QUOTELINES['CLOSE_DATE'].dt.strftime('%Y-%m') == '2022-01']['NET_TOTAL_USD'].sum())} a year ago.
        Incremental TCV (new contracts closed, including new logos and renewals) is largely flat month-over-month.
        """
    )
    st.write("""---""")

    st.write("## Last 12 Months")

    st.write("### Annual Contract Value (ACV)")
    st.write("The ACV of active Search contracts each month over the past 12 months.")
    st.bar_chart(LAST_12_ACV, x="MONTH", y="ACTIVE_ACV", height=500)

    st.write("### Compound Monthly Growth Rate (CMGR)")
    st.write("The average monthly growth rate of Yext Search over the past 12 months.")
    st.line_chart(LAST_12_ACV, x="MONTH", y="CMGR", height=500)

    st.write("### Compound Annual Growth Rate (CAGR)")
    st.write("The average annual growth rate of Yext Search over the past 12 months.")
    st.line_chart(LAST_12_ACV, x="MONTH", y="CAGR", height=500)

    with st.expander("Show Raw Data"):
        st.dataframe(LAST_12_ACV)


with tabs[1]:

    st.info(
        f"""
        ## Summary
        #### Finance and Healthcare represent the largest industries for Yext Search, with \{format_usd(ACTIVE_BUSINESSES[ACTIVE_BUSINESSES['INDUSTRY'] == 'Financial Services']['NET_TOTAL_USD'].sum())} ({format_percentage(ACTIVE_BUSINESSES[ACTIVE_BUSINESSES['INDUSTRY'] == 'Financial Services']['NET_TOTAL_USD'].sum() / ACTIVE_BUSINESSES['NET_TOTAL_USD'].sum())} of TCV) and \{format_usd(ACTIVE_BUSINESSES[ACTIVE_BUSINESSES['INDUSTRY'] == 'Healthcare']['NET_TOTAL_USD'].sum())} ({format_percentage(ACTIVE_BUSINESSES[ACTIVE_BUSINESSES['INDUSTRY'] == 'Healthcare']['NET_TOTAL_USD'].sum() / ACTIVE_BUSINESSES['NET_TOTAL_USD'].sum())} of TCV), respectively.
        However, Yext Search has sizeable customers across all industries.

        #### Overall, customer retention is {format_percentage(BUSINESSES["IS_ACTIVE"].mean())} (i.e. {BUSINESSES["IS_ACTIVE"].sum()} of {BUSINESSES["BUSINESS_ID"].count()} customers are active).
        This is below [industry averages](https://userpilot.com/blog/good-retention-rates-in-saas/#:~:text=The%20monthly%20average%20churn%20rate,range%20of%2092%2D97%20%25.) of 92-97%. Particular weak spots include in Retail and EMEA.

        #### Most TCV today was acquired in 2021, not 2022. \{format_usd(BUSINESSES[BUSINESSES["CLOSE_YEAR"] == '2021']['NET_TOTAL_USD'].sum())} TCV was acquired in 2021, compared to \{format_usd(BUSINESSES[BUSINESSES["CLOSE_YEAR"] == '2022']['NET_TOTAL_USD'].sum())} in 2022.
        This slowdown does align with strategic decisions to re-focus on core products like Listings, instead of viewing Search as the primary growth engine of the business.
    """
    )

    # Customer metrics by Industry
    st.write("## Industry")
    st.write("### All Industries by TCV")

    retention_i = (
        BUSINESSES.groupby(["INDUSTRY"])
        .agg({"BUSINESS_ID": "count", "NET_TOTAL_USD": "sum", "IS_ACTIVE": "mean"})
        .reset_index()
    )

    fig = px.treemap(
        BUSINESSES,
        path=[px.Constant("All"), "INDUSTRY", "NAME"],
        values="NET_TOTAL_USD",
        color="INDUSTRY",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        height=1000,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.write("### Industries with \$2M+ in TCV")
    industries = BUSINESSES.groupby(["INDUSTRY"]).agg({"NET_TOTAL_USD": "sum"}).reset_index()
    industries.sort_values("NET_TOTAL_USD", ascending=False, inplace=True)
    bar = px.bar(industries.head(6), x="INDUSTRY", y="NET_TOTAL_USD", height=500)
    st.plotly_chart(bar, use_container_width=True)

    st.write("### Retention by Industry")
    retention_i.sort_values("NET_TOTAL_USD", ascending=False, inplace=True)
    retention_i.rename({"IS_ACTIVE": "CUSTOMER_RETENTION"}, axis=1, inplace=True)
    retention_bar = px.bar(retention_i.head(6), x="INDUSTRY", y="CUSTOMER_RETENTION", height=500)
    st.plotly_chart(retention_bar, use_container_width=True)

    st.write("### Change in TCV by Industry (% YoY, 2021 to 2022)")
    change = (
        BUSINESSES.groupby(["INDUSTRY", "CLOSE_YEAR"]).agg({"NET_TOTAL_USD": "sum"}).reset_index()
    )
    change["Cumulative TCV"] = change.groupby("INDUSTRY")["NET_TOTAL_USD"].cumsum()
    change["YoY Change"] = change.groupby("INDUSTRY")["Cumulative TCV"].pct_change()
    change = change[change["CLOSE_YEAR"] == "2022"]
    # Sort into Healthcare, Financial Services, Manufacturing, Information, Retail, Food & Hospitality
    change["INDUSTRY"] = pd.Categorical(
        change["INDUSTRY"],
        [
            "Healthcare",
            "Financial Services",
            "Manufacturing",
            "Information",
            "Retail",
            "Food & Hospitality",
        ],
    )
    change.sort_values("INDUSTRY", inplace=True)
    bar = px.bar(change, x="INDUSTRY", y="YoY Change", height=500)
    st.plotly_chart(bar, use_container_width=True)

    # Customer metrics by Sign-up Year
    st.write("## Sign-up Year")
    st.write("### All Customers by Sign-up Year")
    fig = px.treemap(
        BUSINESSES,
        path=[px.Constant("All"), "CLOSE_YEAR", "NAME"],
        values="NET_TOTAL_USD",
        color="CLOSE_YEAR",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        height=1000,
    )
    fig.update_layout(
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.bar_chart(BUSINESSES, x="CLOSE_YEAR", y="NET_TOTAL_USD", height=500)

    st.write("### Retention by Sign-up Year")
    retention_y = (
        BUSINESSES.groupby(["CLOSE_YEAR"])
        .agg({"BUSINESS_ID": "count", "NET_TOTAL_USD": "sum", "IS_ACTIVE": "mean"})
        .reset_index()
    )
    retention_y.sort_values("NET_TOTAL_USD", ascending=False, inplace=True)
    retention_y.rename({"IS_ACTIVE": "CUSTOMER_RETENTION"}, axis=1, inplace=True)
    retention_bar = px.bar(retention_y, x="CLOSE_YEAR", y="CUSTOMER_RETENTION", height=500)
    st.plotly_chart(retention_bar, use_container_width=True)

    # Customer metrics by Region
    st.write("## Region")
    st.write("### All Regions by TCV")
    fig = px.treemap(
        BUSINESSES,
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
    st.bar_chart(BUSINESSES, x="COUNTRY", y="NET_TOTAL_USD", height=500)

    st.write("### Retention by Region")
    retention_r = (
        BUSINESSES.groupby(["COUNTRY"])
        .agg({"BUSINESS_ID": "count", "NET_TOTAL_USD": "sum", "IS_ACTIVE": "mean"})
        .reset_index()
    )
    retention_r.sort_values("NET_TOTAL_USD", ascending=False, inplace=True)
    retention_r.rename({"IS_ACTIVE": "CUSTOMER_RETENTION"}, axis=1, inplace=True)
    retention_bar = px.bar(retention_r, x="COUNTRY", y="CUSTOMER_RETENTION", height=500)
    st.plotly_chart(retention_bar, use_container_width=True)

    st.write("### Change in TCV (YoY %, 2021 to 2022)")
    change = (
        BUSINESSES.groupby(["COUNTRY", "CLOSE_YEAR"]).agg({"NET_TOTAL_USD": "sum"}).reset_index()
    )
    change["Cumulative TCV"] = change.groupby("COUNTRY")["NET_TOTAL_USD"].cumsum()
    change["YoY Change"] = change.groupby("COUNTRY")["Cumulative TCV"].pct_change()
    change = change[change["CLOSE_YEAR"] == "2022"]

    bar = px.bar(change, x="COUNTRY", y="YoY Change", height=500)
    st.plotly_chart(bar, use_container_width=True)


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
        BUSINESSES.sort_values("NET_TOTAL_USD", ascending=False).drop_duplicates().values.tolist(),
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
