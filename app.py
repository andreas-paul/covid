import os
import json
import time
import folium
import datetime
import itertools
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from streamlit_folium import folium_static
from bokeh.plotting import figure
from bokeh.events import DoubleTap
from bokeh.models import WheelZoomTool, CustomJS, DatetimeTickFormatter
from bokeh.palettes import Dark2_5 as palette


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

    cases = cases.drop(['Province/State', 'Lat', 'Long'], axis=1)
    deaths = deaths.drop(['Province/State', 'Lat', 'Long'], axis=1)
    recoveries = recoveries.drop(['Province/State', 'Lat', 'Long'], axis=1)
    
    cases = cases.groupby('Country/Region').sum().reset_index()    
    deaths = deaths.groupby('Country/Region').sum().reset_index()
    recoveries = recoveries.groupby('Country/Region').sum().reset_index()
    
    cases = cases.transpose()
    cases.columns = cases.iloc[0]
    cases['Date'] = cases.index
    cases = cases.iloc[1:]
    cases = cases.reset_index(drop=True)

    recoveries = recoveries.transpose()
    recoveries.columns = recoveries.iloc[0]
    recoveries['Date'] = recoveries.index
    recoveries = recoveries.iloc[1:]
    recoveries = recoveries.reset_index(drop=True)

    deaths = deaths.transpose()
    deaths.columns = deaths.iloc[0]
    deaths['Date'] = deaths.index
    deaths = deaths.iloc[1:]
    deaths = deaths.reset_index(drop=True)

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


def bokeh_plot(data):
    p = figure(title='Active cases',
               x_axis_type='datetime',
               x_axis_label='Time',
               y_axis_label='Number of cases',
               toolbar_location=None,
               plot_height=400
               )
    x = data.index

    colors = itertools.cycle(palette)

    for column in data.columns:
        df = list(data[column])
        p.line(x, df, legend_label=column, line_width=2, color=next(colors))

    p.xaxis.formatter = DatetimeTickFormatter(months=['%B %Y'])
    p.toolbar.active_scroll = p.select_one(WheelZoomTool)
    p.js_on_event(DoubleTap, CustomJS(args=dict(p=p), code='p.reset.emit()'))
    st.bokeh_chart(p, use_container_width=True)


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

    This is an experimental app developed in Python with the fabulous [streamlit](https://streamlit.io/) package, 
    to help explore and understand data related to the Covid-19 pandemic (2019 - present). Please use the options in 
    the sidebar (left side) to select an analysis/visualisation.
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
    feature = st.sidebar.radio("Choose feature to display", ['🤒 Active cases', '💉 Vaccines'])

    if feature == '🤒 Active cases':

        st.write("""\
        ## Active cases

        This chart shows active cases of Covid-19 as reported by individual countries (_vertical axis, y_). Active cases 
        are calculated in the following way:
        
        $$ 
        active = cases - (deaths + recoveries) 
        $$
        
        Some countries do not report recoveries but most report deaths. This will result
        in an ever increasing number of active cases and should thus be interpreted with care (e.g., _The Netherlands_).
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
            bokeh_plot(merged_new)
        else:
            bokeh_plot(merged)

    elif feature == '💉 Vaccines':
        st.write("""\
                ## Vaccines

                This chart shows doses of vaccines given, as reported by individual countries (_vertical axis, y_). 
                A number of options can be chosen, including comparison with active cases.  
                
                https://raw.githubusercontent.com/govex/COVID-19/master/data_tables/vaccine_data/global_data/time_series_covid19_vaccine_global.csv
                """)
    # -----------------------------------------------------------------------------------------------------------

    # Bottom line (credits)

    last = pd.DataFrame({'date': [cases['Date'].iloc[-1]]})
    last['date'] = pd.to_datetime(last['date'], infer_datetime_format=True)
    last = last.at[0, 'date']
    status = f'🚀 Latest data from: {last.strftime("%d %B %Y")}'
    st.sidebar.markdown("""
                        🛠️ Developer: A. Paul                        
                        🌱 Last update: 24 March 2021     
                                           
                        ℹ️ Data sources:
                        * [Johns Hopkins University](https://github.com/CSSEGISandData/COVID-19)   
                        * [Worldometers](https://worldometers.info)
                        """)
    
    st.sidebar.markdown(f" {status}")

    st.sidebar.warning("If you're having difficulties to see the text on the right, "
                       "please switch to the light theme by clicking on the menu button in the upper right, "
                       "and then go to Settings > Theme.")
    

if __name__ == "__main__":
    main()
