import streamlit as st

st.title("🎈 University Donor Dashboard")
st.write(
    "The First App I Ever Deployed"
)
import pandas as pd
import altair as alt
from vega_datasets import data
import us

# Directly load the CSV file from the workspace
csv_path = "university-donations.csv"
df = pd.read_csv(csv_path)

state_id_map   = {state.abbr: int(state.fips)  for state in us.states.STATES}
state_name_map = {int(state.fips): state.name  for state in us.states.STATES}

df['state_fips'] = (
    df['State']
      .map(state_id_map)
      .dropna()
      .astype(int)
)


state_agg = (
    df.groupby('state_fips')
      .agg(
          **{
              'Total Donations': ('Gift Amount', 'sum'),
              'Unique Donors' : ('Prospect ID', 'nunique')
          }
      )
      .reset_index()
)

state_agg['State Name'] = state_agg['state_fips'].map(state_name_map)

selection_alloc = alt.selection_point(fields=['Gift Allocation'], name='SelectAlloc')
brush_year      = alt.selection_interval(encodings=['x'], name='BrushYear')


college_dropdown = alt.binding_select(
    options=sorted(df['College'].dropna().unique()),
    name='Select College:'
)
college_select = alt.selection_single(
    fields=['College'],
    bind=college_dropdown,
    name='CollegeSelect',
    empty='all'
)

state_dropdown = alt.binding_select(
    options=sorted(df['State'].dropna().unique()),
    name='Select State:'
)
state_select = alt.selection_multi(
    fields=['State'],
    bind=state_dropdown,
    name='StateSelect',
    empty='all'
)


bar_alloc = (
    alt.Chart(df)
        .mark_bar()
        .encode(
            y=alt.Y('Gift Allocation:N', sort='-x'),
            x=alt.X('sum(Gift Amount):Q', title='Total Gift Amount ($)'),
            color=alt.condition(selection_alloc, 'Gift Allocation:N', alt.value('lightgray')),
            tooltip=[
                'Gift Allocation:N',
                alt.Tooltip('sum(Gift Amount):Q', format='$,.0f')
            ]
        )
        .add_selection(selection_alloc, college_select, state_select)
        .transform_filter(college_select)
        .transform_filter(state_select)
        .properties(width=400, height=200, title='Total Gift Amount by Allocation')
)

if 'Gift Year' not in df.columns:
    df['Gift Year'] = pd.to_datetime(df['Gift Date']).dt.year
df['Gift Year'] = df['Gift Year'].astype(str)
line_year = (
    alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X('Gift Year:O', title='Year', sort='ascending'),
            y=alt.Y('sum(Gift Amount):Q', title='Total Gift Amount ($)'),
            color='Gift Allocation:N',
            tooltip=[
                alt.Tooltip('Gift Year:O', title='Year'),
                'Gift Allocation:N',
                alt.Tooltip('sum(Gift Amount):Q', format='$,.0f',
                            title='Total Gift Amount')
            ]
        )
        .add_selection(brush_year, selection_alloc, college_select, state_select)
        .transform_filter(selection_alloc)
        .transform_filter(college_select)
        .transform_filter(state_select)
        .properties(width=600, height=200, title='Donations Over Time by Allocation')
)


bar_subcat = (
    alt.Chart(df)
        .mark_bar()
        .encode(
            y=alt.Y('Allocation Subcategory:N', sort='-x'),
            x=alt.X('sum(Gift Amount):Q', title='Total Gift Amount ($)'),
            color='Gift Allocation:N',
            tooltip=[
                'Allocation Subcategory:N',
                alt.Tooltip('sum(Gift Amount):Q', format='$,.0f')
            ]
        )
        .add_selection(selection_alloc, brush_year, college_select, state_select)
        .transform_filter(selection_alloc)
        .transform_filter(brush_year)
        .transform_filter(college_select)
        .transform_filter(state_select)
        .properties(width=600, height=300, title='Breakdown by Allocation Subcategory')
)

controls = (
    alt.Chart(pd.DataFrame({'x': [0]}))
        .mark_point(opacity=0)
        .add_selection(college_select, state_select)
        .properties(height=0)
)

# Only the linked charts, no map

dashboard = (
    alt.vconcat(
        controls,
        alt.hconcat(bar_alloc, line_year),
        bar_subcat
    )
    .configure_title(anchor='start')
)

st.altair_chart(dashboard, use_container_width=True)