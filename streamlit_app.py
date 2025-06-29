############################
# app.py – Streamlit demo  #
############################
import streamlit as st
import pandas as pd
import altair as alt
import us                                           # state look‑ups

st.markdown(
    "<h1 style='font-size: 60px; font-weight: bold; color: #4A90E2; text-align: center;'>University Donations Exploration</h1>",
    unsafe_allow_html=True
)

# ---------- CONFIG ----------
st.set_page_config(page_title="University Donor Dashboard", layout="wide")
alt.data_transformers.disable_max_rows()

# ---------- LOAD DATA ----------
@st.cache_data(show_spinner=False)
def load_data(path: str):
    df = pd.read_csv(path)

    # state abbrev ➜ FIPS
    abbr_to_fips = {s.abbr: int(s.fips) for s in us.states.STATES}
    df["state_fips"] = df["State"].map(abbr_to_fips).astype("Int64")

    # ensure Gift Year as string
    if "Gift Year" not in df.columns:
        df["Gift Year"] = pd.to_datetime(df["Gift Date"]).dt.year.astype(str)
    return df

df = load_data("university-donations.csv")

# Convert Gift Year to int for slider filtering
df["Gift Year Int"] = df["Gift Year"].astype(int)

# ---------- SIDEBAR FILTERS ----------

st.sidebar.header("Filter Data")

min_year = df["Gift Year Int"].min()
max_year = df["Gift Year Int"].max()
year_range = st.sidebar.slider(
    "Select Gift Year Range:",
    min_year,
    max_year,
    (min_year, max_year),
    step=1
)

min_gift = int(df["Gift Amount"].min())
max_gift = int(df["Gift Amount"].max())
gift_range = st.sidebar.slider(
    "Select Gift Amount Range:",
    min_gift,
    max_gift,
    (min_gift, max_gift),
    step=1000
)

# Apply filters to dataframe
df_filtered = df[
    (df["Gift Year Int"] >= year_range[0]) & (df["Gift Year Int"] <= year_range[1]) &
    (df["Gift Amount"] >= gift_range[0]) & (df["Gift Amount"] <= gift_range[1])
]

# ---------- SELECTIONS ----------
sel_alloc = alt.selection_point(fields=["Gift Allocation"])        # auto‑named
brush_yr  = alt.selection_interval(encodings=["x"])               # auto‑named

# ---------- CHARTS ----------

bar_alloc = (
    alt.Chart(df_filtered)
        .mark_bar()
        .encode(
            y=alt.Y("Gift Allocation:N", sort="-x", title=""),
            x=alt.X("sum(Gift Amount):Q", title="Total Gift Amount ($)"),
            color=alt.condition(sel_alloc, "Gift Allocation:N", alt.value("lightgray")),
            tooltip=["Gift Allocation:N",
                     alt.Tooltip("sum(Gift Amount):Q", format="$,.0f")],
        )
        .add_selection(sel_alloc)
        .properties(height=220, width=320, title="Gift Allocation")
)

line_yr = (
    alt.Chart(df_filtered)
        .mark_line(point=True)
        .encode(
            x=alt.X("Gift Year:O", sort="ascending", title="Year"),
            y=alt.Y("sum(Gift Amount):Q", title="Total Gift Amount ($)"),
            color="Gift Allocation:N",
            tooltip=[alt.Tooltip("Gift Year:O", title="Year"),
                     "Gift Allocation:N",
                     alt.Tooltip("sum(Gift Amount):Q", format="$,.0f")],
        )
        .add_selection(sel_alloc, brush_yr)
        .transform_filter(sel_alloc)
        .properties(height=220, width=480, title="Donations Over Time")
)

bar_subcat = (
    alt.Chart(df_filtered)
        .mark_bar()
        .encode(
            y=alt.Y("Allocation Subcategory:N", sort="-x"),
            x=alt.X("sum(Gift Amount):Q", title="Total Gift Amount ($)"),
            color="Gift Allocation:N",
            tooltip=["Allocation Subcategory:N",
                     alt.Tooltip("sum(Gift Amount):Q", format="$,.0f")],
        )
        .add_selection(sel_alloc, brush_yr)
        .transform_filter(sel_alloc)
        .transform_filter(brush_yr)
        .properties(height=300, width=820, title="Sub‑category Breakdown")
)

# ---------- LAYOUT ----------

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Gift Allocation")
    st.altair_chart(bar_alloc, use_container_width=True)

with col2:
    st.subheader("Donations over time")
    st.altair_chart(line_yr, use_container_width=True)

st.subheader("Gift Allocation by Subcategory")
st.altair_chart(bar_subcat, use_container_width=True)

# ---------- SIDEBAR INFO ----------

with st.sidebar:
    st.header("Interactions")
    st.markdown(
        """
        * **Click** a bar → filter by allocation  
        * **Drag** on the year axis → focus time window  
        * Charts update together.
        """
    )
    if st.checkbox("Show raw data"):
        st.dataframe(df_filtered)
