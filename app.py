import os
import time
import datetime
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
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


@st.cache
def wrangle_data(countries, cases, deaths, recoveries):
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

	# # per week
	# df['new_date'] = pd.to_datetime(df['date'])
	# df['Year-Week'] = df['new_date'].dt.strftime('%Y-%U')

	return data


def map(map_data):
	fig = px.choropleth(map_data, locationmode='country names',
						locations='country',
		                color='active', 
						animation_frame='date',
						title = "Active cases",							                
		                color_continuous_scale=px.colors.sequential.PuRd)
	fig.update_layout(margin={"r":0,"t":0,"l":50,"b":0})
	fig.update_layout(coloraxis=dict(colorbar_x=1, 
                                 colorbar_y=0.5, 
                                 colorbar_len=0.80, 
								 colorbar_title='',
                                 colorbar_thickness=20,
								 colorbar_tickfont=dict(size=11, color='grey')))
	# fig.update_layout(coloraxis_showscale=False)

	fig["layout"].pop("updatemenus")
	return fig


def main():

	## Set radio widget to horizontal:
	st.write('<style>div.Widget.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)

	
	st.write("""	
	# 🦠 Covid-19 data exploration

	This is an experimental app to explore data related to Covid-19. I'm in no way an expert 
	in epidemiology so please take the few attempts at interpreting the data here with a grain of salt. 
	Fortunately (or unfortunately 😷), it speaks for itself.
	""")

	cases, deaths, recoveries = load_data()
	pop_data = load_pop_data()
	countries = tuple(cases.columns[1:])
	map_data = wrangle_data(countries, cases, deaths, recoveries)
	
	feature = st.sidebar.selectbox("Choose feature", ['Active cases', 'Per-capita map'])

	if feature == 'Active cases':

		st.write("""\
		## Active cases

		This first chart shows active cases of Covid-19 as reported by individual countries. Active cases are calculated in the following way:
		
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

	elif feature == 'Per-capita map':

		st.write("""\
		## Active cases per capita

		This map shows the number of active cases through time and space. 
		
		""")

		fig = map(map_data)
		st.write(fig)



	last = cases['Date'].iloc[-1]
	last = datetime.datetime.strptime(last, '%Y-%m-%d')
	status = f'Latest data from {last.strftime("%d %B %Y")}.'
	st.info(f"{status} Data sources: [dkriesel](https://www.dkriesel.com/corona/) | [worldometer](https://worldometers.info)  ")


if __name__ == "__main__":
    main()


# TODO Implement download from S3 
# TODO Implement per capita calc for map