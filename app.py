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
	

def wrangleData(country, cases, recoveries, deaths):
	uae_d = deaths[['Date', country]]
	uae_c = cases[['Date', country]]
	uae_r = recoveries[['Date', country]]
	uae_d.columns = ['Date_d', 'deaths']
	uae_c.columns = ['Date_c', 'cases']
	uae_r.columns = ['Date_r', 'recoveries']
	data = [uae_c, uae_d, uae_r]
	df = pd.concat(data, axis=1)
	df.drop(['Date_d', 'Date_r'], axis=1, inplace=True)   
	df.rename(columns={'Date_c': 'date'})          
	df['Date_c'] = pd.to_datetime(df['Date_c'], format='%Y-%m-%d %H:%M:%S.%f')
	df.set_index('Date_c', inplace=True)    
	# df = df.loc[datetime.date(year=2020,month=month,day=1):]
	df['active'] = df['cases'] - (df['deaths'] + df['recoveries'])
	df['change_active'] = df['active'].pct_change()
	df['change_active'] = df['change_active'] * 100
	df['change_active'] = df['change_active'].round(2)
	df['change_cases'] = df['cases'].pct_change()
	df['change_cases'] = df['change_cases'] * 100  
	df['change_cases'] = df['change_cases'].round(2)
	df[df['change_cases'] == np.inf] = np.nan

	return df


def plotData(data):
	fig, ax = plt.subplots(figsize=(13,8))
	plt.xticks(rotation=70)
	ax.plot(df['change_active'], label='Change active cases', color='darkblue', linewidth=1)
	ax.plot(df['change_cases'], label='Change total cases', color='orange', linewidth=0.5)
	#     ax.set_xlim([datetime.date(2020, 4, 1), datetime.date(2020, 4, 28)])
	bottom = np.nanmin(df['change_active']) - 5
	top = np.nanmax(df['change_active']) + 5
	ax.set_ylim(bottom=bottom,top=top)
	ax.set_title(f'Daily change in active cases of COVID-19 ({country})', fontsize=14)
	ax.legend()
	ax.grid(color='grey', linestyle='--', linewidth=0.5)
	ax.axhline(0, color='black', lw=1)
	plt.show()


def per_capita(x):
	return x + 100


def main():
	
	st.write("""	
	# 🦠 Covid-19 data exploration

	This is an experimental app to explore data related to Covid-19. I'm in no way an expert 
	in epidemiology so please take the few attempts at interpreting the data with a grain of salt. 
	Fortunately (or unfortunately 😷), the data speaks for itself.
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
	
	countries = st.multiselect('Choose countries', countries, ['US', 'Germany'])
	if not countries:
		st.warning("Please select at least one country.")

	merged = processing(countries, cases, deaths, recoveries)

	enrich = st.radio("Select enrichment", ('none', 'per capita', 'density', 
						'median age', 'urban population'))
	
	if enrich == 'none':
		pass
	elif enrich == 'per capita':
		for item in countries:
			merged[f'{item}'] = merged[f'{item}'] / pop_data.at[f"{item}",f"population"] * 100000
	elif enrich == 'density':
		for item in countries:
			merged[f'{item}'] = merged[f'{item}'] / pop_data.at[f"{item}",f"density"]
	elif enrich == 'median age':
		for item in countries:
			merged[f'{item}'] = merged[f'{item}'] / pop_data.at[f"{item}",f"median_age"]	
	elif enrich == 'urban population':
		for item in countries:
			merged[f'{item}'] = merged[f'{item}'] / pop_data.at[f"{item}",f"urban_pop"]			
	

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
		st.write("Relevant population data:")
		st.write(pop_data_sel)
	else:
		st.warning("No country selected above, so there's no data to show here.")
		return

	last = cases['Date'].iloc[-1]
	last = datetime.datetime.strptime(last, '%Y-%m-%d')
	status = f'Latest data from {last.strftime("%d %B %Y")}.'
	st.info(f"{status} Data sources: [dkriesel](www.dkriesel.com/corona/) | [worldometer](worldometers.info)  ")


if __name__ == "__main__":
    main()


## Set radio widget to horizontal
st.write('<style>div.Widget.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
