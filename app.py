import os
import json
import time
import folium
import datetime
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from streamlit_folium import folium_static


@st.cache(max_entries=None, suppress_st_warning=True)
def load_data():
    url_cases = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data" \
                "/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv "
    url_deaths = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data" \
                 "/csse_covid_19_time_series/time_series_covid19_deaths_global.csv "
    url_recoveries = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data" \
                     "/csse_covid_19_time_series/time_series_covid19_recovered_global.csv "

    cases = pd.read_csv(url_cases)
    deaths = pd.read_csv(url_deaths)
    recoveries = pd.read_csv(url_recoveries)

    cases.rename(columns={'Korea, South': 'South Korea',
                          'US': 'United States',
                          'Czechia': 'Czech Republic'},
                 inplace=True)
    recoveries.rename(columns={'Korea, South': 'South Korea',
                               'US': 'United States',
                               'Czechia': 'Czech Republic'},
                      inplace=True)
    deaths.rename(columns={'Korea, South': 'South Korea',
                           'US': 'United States',
                           'Czechia': 'Czech Republic'},
                  inplace=True)

    cases = cases.transpose()
    cases.columns = cases.iloc[1]
    cases = cases.iloc[4:]
    cases['Date'] = cases.index
    cases = cases.reset_index(drop=True)
    cases = cases.rename(columns={'Country/Region': 'Date'})

    recoveries = recoveries.transpose()
    recoveries.columns = recoveries.iloc[1]
    recoveries = recoveries.iloc[4:]
    recoveries['Date'] = recoveries.index
    recoveries = recoveries.reset_index(drop=True)
    recoveries = recoveries.rename(columns={'Country/Region': 'Date'})

    deaths = deaths.transpose()
    deaths.columns = deaths.iloc[1]
    deaths = deaths.iloc[4:]
    deaths['Date'] = deaths.index
    deaths = deaths.reset_index(drop=True)
    deaths = deaths.rename(columns={'Country/Region': 'Date'})

    return cases, deaths, recoveries


@st.cache
def load_pop_data():
    pop_data = pd.read_csv('data/countries.csv', index_col='country')
    return pop_data


@st.cache(allow_output_mutation=True)
def processing(countries, cases, deaths, recoveries):
    """
    Function to combine data files and calculate active cases

    """
    datalist = []
    for country in countries:
        d = deaths[['Date', country]]
        c = cases[['Date', country]]
        r = recoveries[['Date', country]]
        df = c.merge(left_on='Date', right_on='Date', right=r)
        df = df.merge(left_on='Date', right_on='Date', right=d)
        df['Date'] = pd.to_datetime(df['Date'], infer_datetime_format=True)
        df.set_index('Date', inplace=True)
        df.columns = ['cases', 'recoveries', 'deaths']
        df['active'] = df['cases'] - (df['deaths'] + df['recoveries'])
        df = df[['active']]
        df.columns = [f'{country}']
        datalist.append(df)
    if len(datalist) > 1:
        merged = pd.concat(datalist, axis=1)
        return merged
    elif len(datalist) == 1:
        return df
    else:
        df = []
        return df


@st.cache(allow_output_mutation=True)
def wrangle_data(countries, pop_data, countries_pop_data, cases, deaths, recoveries):
    datetime = cases['Date']
    data = pd.DataFrame(index=datetime)
    for country in countries:
        d = deaths[['Date', country]]
        c = cases[['Date', country]]
        r = recoveries[['Date', country]]
        df = c.merge(left_on='Date', right_on='Date', right=r)
        df = df.merge(left_on='Date', right_on='Date', right=d)
        df['Date'] = pd.to_datetime(df['Date'], infer_datetime_format=True)
        df.set_index('Date', inplace=True)
        df.columns = ['cases', 'recoveries', 'deaths']
        df['active'] = df['cases'] - (df['deaths'] + df['recoveries'])
        data[f'{country}'] = df[['active']]

    data = data.transpose().reset_index()
    data = pd.melt(data, id_vars='index')
    data.rename(columns={'index': 'country', 'Date': 'date', 'value': 'active'}, inplace=True)
    data = data[data['country'].isin(countries_pop_data)]
    data['active_capita'] = data.apply(lambda x: x.active / pop_data.at[f"{x.country}", "population"] * 100000, axis=1)
    with pd.option_context('mode.use_inf_as_na', True):
        data = data.dropna(subset=['active', 'active_capita'], how='all')

    # # per week
    # df['new_date'] = pd.to_datetime(df['date'])
    # df['Year-Week'] = df['new_date'].dt.strftime('%Y-%U')

    return data


def main():
    st.set_page_config(
        page_title="Explore Covid-19 data",
        page_icon="🧊",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        f"""
    <style>
        .reportview-container .main .block-container{{
            max-width: {1000}px;
            padding-top: {0}rem;
            padding-right: {2}rem;
            padding-left: {2}rem;
            padding-bottom: {0}rem;
        }}
        .reportview-container .main {{
            color: {'black'};
            background-color: {'white'};
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )
    # Set radio widget to horizontal:
    st.write('<style>div.Widget.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)

    st.write("""	
    # 🦠 Covid-19 data exploration

    This is an experimental app developed in Python and the fabulous streamlit package, 
    to explore data related to the Covid-19 pandemic (2019 - present). Select features on the sidebar to the left. 
    """)

    # Load and wrangle data
    cases, deaths, recoveries = load_data()

    pop_data = load_pop_data()
    # countries_pop_data = pop_data.index.to_list()
    country_list = tuple(cases.columns[1:])
    # map_data = wrangle_data(country_list, pop_data, countries_pop_data, cases, deaths, recoveries)
    # map_data.to_csv('map_data.csv', index=False)
    # exclude = map_data.sort_values(by=['date', 'active']).tail(5)
    # exclude = exclude['country'].to_list()
    # exclude_from_map = map_data[~map_data['country'].isin(exclude)]

    # feature = st.radio("Choose feature to display", ['Active cases', 'Per-capita map'])
    feature = st.sidebar.radio("Choose feature to display", ['Active cases'])

    if feature == 'Active cases':

        st.write("""\
        ## Active cases

        This chart shows active cases of Covid-19 as reported by individual countries. Active cases 
        are calculated in the following way:
        
        $$ 
        active = cases - (deaths + recoveries) 
        $$
        
        Some countries do not report recoveries but most report deaths. This will result
        in an ever increasing number of active cases and thus should be interpreted with care (e.g., _The Netherlands_).
        """)

        countries = st.multiselect('Choose one or multiple countries', country_list,
                                   ['Germany', 'Japan', 'United Arab Emirates'])
        if not countries:
            st.warning("Please select at least one country.")

        merged = processing(countries, cases, deaths, recoveries)

        merged_new = merged.copy()
        for item in countries:
            merged_new[f'{item}'] = merged_new[f'{item}'] / pop_data.at[f"{item}", "population"] * 100000

        enrich = st.checkbox("Per capita (100k)", value=True)
        if enrich:
            st.line_chart(merged_new)
        else:
            st.line_chart(merged)

    elif feature == 'Per-capita map':

        st.write("""\
        ## Active cases 

        This map shows the number of active cases through space and time, based on a country's population. This means,
        if a country has e.g. an active case count of 700 per capita, 700 of 100,000 will theoretically be having a 
        Covid-19 infection. Going a step further, this would mean that the probability of coming accross someone who is 
        infected, is equal to:

        """)

        st.latex(r'''\frac{700}{100,000} * 100 = 0.7\%''')

        st.write("""
        This back-on-the-envelope percentage seems low, but compared to other diseases, such as e.g. 
        tuberculosis, which has a worldwide occurrence of approximately 0.13\% according to data of 
        the World Health Organisation (2018), this is pretty damn high.
        """)

        map_data['date'] = pd.to_datetime(map_data['date'], infer_datetime_format=True).dt.date

        min_date = map_data['date'].min()
        max_date = map_data['date'].max()

        day = st.slider('Move the slider to change time on the map', min_date, max_date, value=max_date)
        df = map_data.loc[map_data['date'] == day]

        geo = f'data/world.geojson'  # geojson file

        m = folium.Map(location=[50, 10],
                       name='Active cases',
                       zoom_start=1.0,
                       width='100%',
                       height='100%',
                       tiles=None,
                       min_zoom=1,
                       max_zoom=4
                       )

        # add chloropleth
        m.choropleth(
            name='Active cases',
            geo_data=geo,
            data=df,
            columns=['country', 'active_capita'],
            key_on='feature.properties.name',
            fill_color='YlOrRd',
            fill_opacity=0.9,
            line_opacity=0.2,
            highlight=False,
            nan_fill_color='white',
            nan_fill_opacity=0.2,

        )

        # folium.TileLayer('Stamen Terrain').add_to(m)
        # folium.TileLayer('Stamen Water Color').add_to(m)
        folium.map.LayerControl('bottomleft', collapsed=True).add_to(m)
        folium_static(m, width=700, height=400)

        st.write('')
        st.write("""**Top 3 countries by active cases per capita (100k):**""")

        df = df[['country', 'active', 'active_capita']].sort_values(by='active_capita', ascending=False).head(
            3).reset_index(drop=True)
        st.text(f"1. {df.at[0, 'country']}: {df.at[0, 'active_capita']:.0f}")
        st.text(f"2. {df.at[1, 'country']}: {df.at[1, 'active_capita']:.0f}")
        st.text(f"3. {df.at[2, 'country']}: {df.at[2, 'active_capita']:.0f}")

    # -----------------------------------------------------------------------------------------------------------

    # Bottom line (credits)
    st.sidebar.warning("If you're unable to see the text on the right, "
                    "please switch to the light theme using the menu button in the upper right (Settings)")
    last = pd.DataFrame({'date': [cases['Date'].iloc[-1]]})
    last['date'] = pd.to_datetime(last['date'], infer_datetime_format=True)
    last = last.at[0, 'date']
    status = f'Latest data from {last.strftime("%d %B %Y")}.'
    st.sidebar.info(f"{status} Data sources: [Johns Hopkins University](https://github.com/CSSEGISandData/COVID-19)"
            f" | [worldometer](https://worldometers.info)")


if __name__ == "__main__":
    main()

# TODO Implement download from S3
