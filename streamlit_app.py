import streamlit as st

st.title("🎈 University Donor Dashboard")
st.write(
    "The First App I Ever Deployed"
)
import pandas as pd
import altair as alt
from vega_datasets import data

import us

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
reset_click     = alt.selection_point(on='click', clear='mouseup', name='ResetClick')


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

# State dropdown (kept from the original)
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

# 4-D  Choropleth Map of States
us_states       = alt.topo_feature(data.us_10m.url, 'states')
state_map_select = alt.selection_multi(fields=['state_fips'], name='StateMapSelect', empty='all')

base_map = (
    alt.Chart(us_states)
        .mark_geoshape(stroke='white', strokeWidth=0.5)
        .encode(
            color=alt.condition(
                state_map_select,
                alt.Color('Total Donations:Q', scale=alt.Scale(scheme='greens')),
                alt.value('lightgray')
            ),
            tooltip=[
                alt.Tooltip('State Name:N', title='State'),
                alt.Tooltip('Total Donations:Q', format='$,.0f'),
                alt.Tooltip('Unique Donors:Q')
            ]
        )
        .transform_lookup(
            lookup='id',
            from_=alt.LookupData(
                state_agg,
                'state_fips',
                ['State Name', 'Total Donations', 'Unique Donors']
            )
        )
        .add_selection(state_map_select)
        .transform_filter(reset_click)
        .project(type='albersUsa')
        .properties(width=700, height=400, title='Hover to See State Data')
)

#
reset_text = (
    alt.Chart(pd.DataFrame({'text': ['Click to Reset State Selection']}))
        .mark_text(align='left', fontSize=13, fontWeight='bold', color='steelblue')
        .encode(text='text:N')
        .add_selection(reset_click)
        .properties(width=300, height=30)
)


controls = (
    alt.Chart(pd.DataFrame({'x': [0]}))
        .mark_point(opacity=0)
        .add_selection(college_select, state_select)
        .properties(height=0)
)


dashboard = (
    alt.vconcat(
        controls,
        alt.hconcat(base_map, reset_text),
        alt.hconcat(bar_alloc, line_year),
        bar_subcat
    )
    .configure_title(anchor='start')
)

dashboard