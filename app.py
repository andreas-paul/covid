import streamlit as st
from scripts.data import *
from scripts.figures import *


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
    the sidebar (left side) to select an analysis or visualisation.
    """)

    # Load and wrangle data
    cases, deaths, recoveries = load_data()
    pop_data = load_pop_data()
    country_list = tuple(cases.columns[1:])
    vac_doses, vac_partial, vac_fully = load_vaccine_data()
    vac_doses_pop = vac_doses.copy(deep=True)
    vac_partial_pop = vac_partial.copy(deep=True)
    vac_fully_pop = vac_fully.copy(deep=True)

    for country in list(vac_doses.columns):
        try:
            pop = pop_data.at[country, "population"]
        except KeyError:
            continue
        vac_doses_pop[f"{country}"] = vac_doses_pop[f"{country}"].apply(lambda x: x / pop * 100000)

    for country in list(vac_partial.columns):
        try:
            pop = pop_data.at[country, "population"]
        except KeyError:
            continue
        vac_partial_pop[f"{country}"] = vac_partial_pop[f"{country}"].apply(lambda x: x / pop * 100000)

    for country in list(vac_fully.columns):
        try:
            pop = pop_data.at[country, "population"]
        except KeyError:
            continue
        vac_fully_pop[f"{country}"] = vac_fully_pop[f"{country}"].apply(lambda x: x / pop * 100000)

    feature = st.sidebar.radio("Choose feature to display", ['🤒 Active cases',
                                                             '💉 Vaccines',
                                                             '✔️ Data exploration'])

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
            bokeh_plot(merged_new, 'Number of cases', 'linear')
        else:
            bokeh_plot(merged, 'Number of cases', 'linear')

    elif feature == '💉 Vaccines':
        st.write("""\
                ## Vaccines

                This chart shows doses of vaccines given, as reported by individual countries (_vertical axis, y_). 
                A number of options can be chosen, including comparison with active cases.  
                
                """)

        topic = st.selectbox('Select data comparison', ['Vaccine doses (time-series)'])
        country_list = list(vac_doses.columns)

        if topic == 'Vaccine doses (time-series)':
            countries = st.multiselect('Choose one or multiple countries', country_list,
                                       ['Israel', 'United Arab Emirates', 'United Kingdom', 'Germany'])

            if not countries:
                st.warning("Please select at least one country.")

            left, center, right = st.beta_columns(3)
            with left:
                enrich = st.checkbox("Per capita (100k)", value=True)
            with center:
                compar = st.checkbox("Compare to active", value=False)
            with right:
                log = st.checkbox("Log-scale", value=False)

            scale = 'linear'
            if log:
                scale = 'log'

            if enrich:
                bokeh_plot_vaccines(vac_doses_pop[countries], per_capita=True)
            else:
                bokeh_plot_vaccines(vac_doses[countries], per_capita=False)

    elif feature == '✔️ Data exploration':
        st.write("""\
                  ## Data exploration

                  This area offers a variety of graphs that compare various types of data, something that is very
                  difficulty to find elsewhere. In particular, the focus is on showing the connection between the
                  incidence-number (cases per 100k people) as used in Germany, number of PCR tests conducted, 
                  implementation of movement and other restrictions and vaccine doses.
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
                        * [Centers for Civic Impact](https://github.com/govex/COVID-19)
                        """)
    
    st.sidebar.markdown(f" {status}")

    st.sidebar.warning("If you're having difficulties to see the text on the right, "
                       "please switch to the light theme by clicking on the menu button in the upper right, "
                       "and then go to Settings > Theme.")
    

if __name__ == "__main__":
    main()
