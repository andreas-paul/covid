import pandas as pd
import streamlit as st


@st.cache(max_entries=None, suppress_st_warning=True, show_spinner=False)
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


@st.cache(suppress_st_warning=True, show_spinner=False, allow_output_mutation=True)
def load_vaccine_data():
    url = 'https://raw.githubusercontent.com/govex/COVID-19/master/data_tables/vaccine_data/' \
          'global_data/time_series_covid19_vaccine_global.csv'
    df = pd.read_csv(url)
    df = df.drop(['UID', 'Report_Date_String'], axis=1)
    df['Date'] = pd.to_datetime(df['Date'], infer_datetime_format=True)

    df_doses = df.reset_index().pivot_table(index='Country_Region', columns='Date', values='Doses_admin')
    df_parti = df.reset_index().pivot_table(index='Country_Region', columns='Date', values='People_partially_vaccinated')
    df_fully = df.reset_index().pivot_table(index='Country_Region', columns='Date', values='People_fully_vaccinated')

    df_doses = df_doses.transpose()
    df_parti = df_parti.transpose()
    df_fully = df_fully.transpose()

    return df_doses, df_parti, df_fully


@st.cache
def load_pop_data():
    pop_data = pd.read_csv('data/countries.csv', index_col='country')
    return pop_data


@st.cache(allow_output_mutation=True, show_spinner=False)
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


@st.cache(allow_output_mutation=True, show_spinner=False)
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


@st.cache(allow_output_mutation=True, show_spinner=False)
def create_daily(data):
    df = pd.DataFrame()
    for country in data.columns:
        if country != 'Date':
            df[f"{country}"] = data[f"{country}"].diff()
    df['Date'] = data['Date']
    return df


@st.cache(allow_output_mutation=True, show_spinner=False, suppress_st_warning=True)
def process_daily(countries, data):
    """
    Function to combine data files

    """
    countries = countries + ['Date']
    data = data[countries]
    data['Date'] = pd.to_datetime(data['Date'], infer_datetime_format=True)
    data.index = data['Date']
    return data



