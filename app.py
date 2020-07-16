import os
import time
import datetime
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


st.markdown(
        f"""
<style>
    .reportview-container .main .block-container{{
        max-width: 900px;        
    }}
</style>
""",
        unsafe_allow_html=True,
    )


@st.cache
def load_data():	
	url_cases = "http://www.dkriesel.com/_media/corona-cases.csv"
	url_deaths = "http://www.dkriesel.com/_media/corona-deaths.csv"
	url_recoveries = "http://www.dkriesel.com/_media/corona-recoveries.csv"
	cases = pd.read_csv(url_cases, sep='\t')
	deaths = pd.read_csv(url_deaths, sep='\t')
	recoveries = pd.read_csv(url_recoveries, sep='\t')
	cases.rename(columns={'Korea, South': 'South Korea'}, inplace=True)
	recoveries.rename(columns={'Korea, South': 'South Korea'}, inplace=True)
	deaths.rename(columns={'Korea, South': 'South Korea'}, inplace=True)
	return cases, deaths, recoveries


@st.cache
def load_pop_data():
	pop_data = pd.read_csv('countries.csv', index_col='country')
	return pop_data


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
		df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %H:%M:%S.%f')
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
	

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def remote_css(url):
    st.markdown(f'<link href="{url}" rel="stylesheet">', unsafe_allow_html=True)    


def icon(icon_name):
    st.markdown(f'<i class="material-icons">{icon_name}</i>', unsafe_allow_html=True)


def main():

	# Load some potential styling options
	local_css("style.css")
	remote_css('https://fonts.googleapis.com/icon?family=Material+Icons')	
	## Set radio widget to horizontal:
	st.write('<style>div.Widget.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
	# icon("alarm")
	
	st.write("""	
	# 🦠 Covid-19 data exploration

	This is an experimental app to explore data related to Covid-19. I'm in no way an expert 
	in epidemiology so please take the few attempts at interpreting the data here with a grain of salt. 
	Fortunately (or unfortunately 😷), it speaks for itself.
	""")

	cases, deaths, recoveries = load_data()
	pop_data = load_pop_data()

	st.write("""\
	## Active cases

	The first chart shows active cases of Covid-19 as reported by individual countries. Active cases are calculated in the following way:
	
	$$ 
	active = cases - (deaths + recoveries) 
	$$
	
	Some countries do not report recoveries (e.g., in The Netherlands), but most report deaths. This results 
	in the number of active	cases sometimes being equal or similar to _cases_ - _deaths_ only, 
	while at the same time also showing a steady increase in the total case count.
	""")


	countries = tuple(cases.columns[1:])
	
	countries = st.multiselect('Choose one or multiple countries', countries, ['Germany', 'US'])
	if not countries:
		st.warning("Please select at least one country.")

	merged = processing(countries, cases, deaths, recoveries)

	enrich = st.radio("Select enrichment", ('none', 'per capita (100k)'), 1)
	
	if enrich == 'none':
		pass
	elif enrich == 'per capita (100k)':
		for item in countries:
			merged[f'{item}'] = merged[f'{item}'] / pop_data.at[f"{item}",f"population"] * 100000		

	if len(merged) >= 1:
		st.line_chart(merged)
	else:
		pass
	
	if len(countries) > 0:
		df_list = []
		for item in countries:
			x = pop_data.loc[[f'{item}']]
			df_list.append(x)		
		pop_data_sel = pd.concat(df_list).sort_values(by='country')
	else:
		st.warning("No country selected above, so there's no data to show here.")
		return


	last = cases['Date'].iloc[-1]
	last = datetime.datetime.strptime(last, '%Y-%m-%d')
	status = f'Latest data from {last.strftime("%d %B %Y")}.'
	st.info(f"{status} Data sources: [dkriesel](https://www.dkriesel.com/corona/) | [worldometer](https://worldometers.info)  ")


if __name__ == "__main__":
    main()
