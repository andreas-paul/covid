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



# st.markdown(
#         f"""
# <style>
#     .reportview-container .main .block-container{{
#         max-width: 900px;        
#     }}
# </style>
# """,
#         unsafe_allow_html=True,
#     )


@st.cache(max_entries=None)
def load_data():	
	url_cases = "http://www.dkriesel.com/_media/corona-cases.csv"
	url_deaths = "http://www.dkriesel.com/_media/corona-deaths.csv"
	url_recoveries = "http://www.dkriesel.com/_media/corona-recoveries.csv"
	cases = pd.read_csv(url_cases, sep='\t', decimal=',')
	deaths = pd.read_csv(url_deaths, sep='\t', decimal=',')
	recoveries = pd.read_csv(url_recoveries, sep='\t', decimal=',')
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
	cases.drop(['Diamond Princess', 'MS Zaandam'], inplace=True, axis=1)
	recoveries.drop(['Diamond Princess', 'MS Zaandam'], inplace=True, axis=1)
	deaths.drop(['Diamond Princess', 'MS Zaandam'], inplace=True, axis=1)
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
		df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %H:%M:%S.%f')
		df.set_index('Date', inplace=True)
		df.columns = ['cases', 'recoveries', 'deaths']
		df['active'] = df['cases'] - (df['deaths'] + df['recoveries'])
		data[f'{country}'] = df[['active']]
	
	data = data.transpose().reset_index()
	data = pd.melt(data, id_vars='index')
	data.rename(columns={'index': 'country', 'Date': 'date', 'value': 'active'}, inplace=True)
	data = data[data['country'].isin(countries_pop_data)]
	data['active_capita'] = data.apply(lambda x: x.active / pop_data.at[f"{x.country}","population"] * 100000, axis=1)
	with pd.option_context('mode.use_inf_as_na', True):
		data = data.dropna(subset=['active', 'active_capita'], how='all')

	# # per week
	# df['new_date'] = pd.to_datetime(df['date'])
	# df['Year-Week'] = df['new_date'].dt.strftime('%Y-%U')

	return data



def main():
	

	# Set radio widget to horizontal:
	st.write('<style>div.Widget.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)

	st.write("""	
	# 🦠 Covid-19 data exploration

	This is an experimental app to explore data related to Covid-19. I'm in no way an expert 
	in epidemiology so please take the few attempts at interpreting the data here with a grain of salt. 
	Fortunately (or unfortunately 😷), it speaks for itself.
	""")


	# Load and wrangle data
	cases, deaths, recoveries = load_data()
	pop_data = load_pop_data()
	countries_pop_data = pop_data.index.to_list()
	country_list = tuple(cases.columns[1:])	
	map_data = wrangle_data(country_list, pop_data, countries_pop_data, cases, deaths, recoveries) 	
	# map_data.to_csv('map_data.csv', index=False)
	exclude = map_data.sort_values(by=['date','active']).tail(5)
	exclude = exclude['country'].to_list()
	exclude_from_map = map_data[~map_data['country'].isin(exclude)]
	
	feature = st.radio("Choose feature to display", ['Active cases', 'Per-capita map'])

	if feature == 'Active cases':

		st.write("""\
		## Active cases

		This chart shows active cases of Covid-19 as reported by individual countries. Active cases 
		are calculated in the following way:
		
		$$ 
		active = cases - (deaths + recoveries) 
		$$
		
		Some countries do not report recoveries (e.g., in The Netherlands), but most report deaths. This results 
		in the number of active	cases sometimes being equal or similar to _cases_ - _deaths_ only, 
		while at the same time also showing a steady increase in the total case count.
		""")
		
		countries = st.multiselect('Choose one or multiple countries', country_list, ['Germany', 'Japan', 'United Arab Emirates'])
		if not countries:
			st.warning("Please select at least one country.")

		merged = processing(countries, cases, deaths, recoveries)

		merged_new = merged.copy()	
		for item in countries:
			merged_new[f'{item}'] = merged_new[f'{item}'] / pop_data.at[f"{item}","population"] * 100000

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

		map_data['date'] = pd.to_datetime(map_data['date'], format='%Y-%m-%d').dt.date
		
		
		min_date = map_data['date'].min()
		max_date = map_data['date'].max()

		day = st.slider('Move the slider to change time on the map', min_date, max_date, value=max_date)
		df = map_data.loc[map_data['date'] == day]

		geo = f'data/world.geojson' # geojson file

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
			highlight = False,
			nan_fill_color='white',
			nan_fill_opacity=0.2,
		
		)

		
		# folium.TileLayer('Stamen Terrain').add_to(m)
		# folium.TileLayer('Stamen Water Color').add_to(m)
		folium.map.LayerControl('bottomleft', collapsed=True).add_to(m)
		folium_static(m, width=700, height=400)

		st.write('')
		st.write("""**Top 3 countries by active cases per capita (100k):**""")

		df = df[['country', 'active', 'active_capita']].sort_values(by='active_capita', ascending=False).head(3).reset_index(drop=True)
		st.text(f"1. {df.at[0, 'country']}: {df.at[0, 'active_capita']:.0f}")
		st.text(f"2. {df.at[1, 'country']}: {df.at[1, 'active_capita']:.0f}")
		st.text(f"3. {df.at[2, 'country']}: {df.at[2, 'active_capita']:.0f}")

	# -----------------------------------------------------------------------------------------------------------

	# Bottom line (credits)
	last = cases['Date'].iloc[-1]
	last = datetime.datetime.strptime(last, '%Y-%m-%d')
	status = f'Latest data from {last.strftime("%d %B %Y")}.'
	st.info(f"{status} Data sources: [dkriesel](https://www.dkriesel.com/corona/)"
			f" | [worldometer](https://worldometers.info)")


if __name__ == "__main__":
    main()


# TODO Implement download from S3 