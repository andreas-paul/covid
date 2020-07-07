import os
import time
import datetime
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# with open("style.css") as f:
	# st.markdown('<style>{}</style>'.format(f.read()), unsafe_allow_html=True)


def load_data():
	if os.path.exists('corona-cases.csv'):
		cases = pd.read_csv('corona-cases.csv')
		recoveries = pd.read_csv('corona-recoveries.csv')
		deaths = pd.read_csv('corona-deaths.csv')
		last = cases['Date'].iloc[-1]
		last = datetime.datetime.strptime(last, '%Y-%m-%d')
		status = f'Loaded data files. Latest data from {last.strftime("%d %B %Y")}.'
		return cases, recoveries, deaths, status
	else:
		pd.read_csv('http://www.dkriesel.com/_media/corona-cases.csv', sep='\t').to_csv('corona-cases.csv', index=False)
		pd.read_csv('http://www.dkriesel.com/_media/corona-recoveries.csv',sep='\t').to_csv('corona-recoveries.csv', index=False)
		pd.read_csv('http://www.dkriesel.com/_media/corona-deaths.csv', sep='\t').to_csv('corona-deaths.csv', index=False)
		cases = pd.read_csv('corona-cases.csv')
		recoveries = pd.read_csv('corona-recoveries.csv')
		deaths = pd.read_csv('corona-deaths.csv')
		last = cases['Date'].iloc[-1]
		last = datetime.datetime.strptime(last, '%Y-%m-%d')
		status = f'Downloaded files and saved to disk. Latest data from {last.strftime("%d %B %Y")}.'
		return cases, recoveries, deaths, status


def update_data():
	pd.read_csv('http://www.dkriesel.com/_media/corona-cases.csv', sep='\t').to_csv('corona-cases.csv', index=False)
	pd.read_csv('http://www.dkriesel.com/_media/corona-recoveries.csv',sep='\t').to_csv('corona-recoveries.csv', index=False)
	pd.read_csv('http://www.dkriesel.com/_media/corona-deaths.csv', sep='\t').to_csv('corona-deaths.csv', index=False)
	cases, recoveries, deaths, status = load_data()
	return cases, recoveries, deaths, status 


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


# st.write('<style>div.Widget.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)


st.write("""	
# Data exploration

A simple app to explore data related to Covid-19. Data source: [dkriesel.com](http://www.dkriesel.com/corona)
""")

st.write("""
## Data Loading

""")

cases, recoveries, deaths, status = load_data()
st.write(status)

update = st.button("Update data")
if update:
	cases, recoveries, deaths, status = update_data()
	st.write(status)

st.write("""
## Stats by country

In this section, the data of individual countries can be explored. 

""")

countries = tuple(cases.columns[1:])
country = st.selectbox('Select country:', countries, 66)

coordinates = pd.DataFrame({'lat': [24], 'lon': [54]})

# st.map(coordinates, zoom=4)

data = wrangleData(country=country, cases=cases, recoveries=recoveries, deaths=deaths)

st.write("")
days = st.number_input("Enter number of days", min_value=1, max_value=31, value=7)
st.write(f"Most recent data (last {days} days):")
st.write(data[['cases', 'deaths', 'recoveries', 'active']].tail(days))

st.write("""
## Graph data by type

""")
datatype = ('cases', 'active', 'recoveries', 'deaths', 'change_active')
datatype = st.selectbox("Select data type:", datatype, 1)

txt = str(datatype).title()
st.write(f'Covid-19 cases in {country}: {txt}')

st.line_chart(data[f'{datatype}'])
st.text("(This is an interactive chart. Zoom with your mousewheel, double-click to reset!)")

