import geopy
import pandas as pd
import time
import os
import numpy as np
import requests
from bs4 import BeautifulSoup
from meteostat import Monthly, Point
import re

class CreateDataCities:
	def __init__(self, cities_file: str, save_dir: str, from_csv: str = ''):
		"""
		Parameters
		----------
		cities_file : str
			The path to the file containing the cities.

		save_dir : str
			The directory to save the dataset.

		from_csv : str
			The path to the csv file containing the precalculated dataset.
		"""
		self.cities_file: str = cities_file
		self.from_csv: str = from_csv
		self.save_dir: str = save_dir.removesuffix('/')
		self.URL: str = "https://en.wikipedia.org/w/api.php"

		if not from_csv:
			self.cities, self.countries = self.get_data_cities()
			self.coordinates: dict = self.get_coordinates()
			self.wikipedia_data: dict = self.get_data_wikipedia()
		else:
			self.df = pd.read_csv(from_csv)
			self.cities = self.df['city'].tolist()
			self.countries = self.df['country'].tolist()
			self.coordinates = {'latitude': self.df['latitude'].tolist(), 'longitude': self.df['longitude'].tolist(), 'altitude': self.df['altitude'].tolist()}
			self.wikipedia_data = {city: {'content': self.df[self.df['city'] == city]['wiki_content'].values[0],
										  'title': self.df[self.df['city'] == city]['wiki_title'].values[0]}
								   for city in self.cities}
			
			
		self.get_anual_weather_data()

		self.save_dataset()
		
		self.save_texts()

	def get_data_cities(self):
		"""
		Get the data from the file containing the cities.

		Returns
		-------
		list
			The list of cities.
		"""
		if self.from_csv:
			df = pd.read_csv(self.from_csv)
			cities = df['city'].tolist()
			countries = df['country'].tolist()
		else:
			with open(self.cities_file, 'r', encoding='utf-8') as file:
				tuples = file.read().splitlines()
				cities = [city.split(',')[0].strip() for city in tuples]
				countries = [city.split(',')[1].strip() for city in tuples]
		
		pairs = [(ci, co) for ci, co in zip(cities, countries)]
		pairs = set(pairs)
		pairs = list(pairs)

		cities = [t[0] for t in pairs]
		countries = [t[1] for t in pairs]

		return cities, countries

	def get_coordinates(self):
		"""
		Get the coordinates of the cities.

		Returns
		-------
		dict
			The dictionary of the locations.
		"""
		geolocator = geopy.Nominatim(user_agent="cities", timeout=10)
		coordinates = {'latitude': [], 'longitude': [], 'altitude': []}
		for city, country in zip(self.cities, self.countries):
			print(f"Getting coordinates for {city}...")
			location = geolocator.geocode(f"{city}, {country}")
			if location is None:
				print(f"Location not found for {city}.")
				coordinates['latitude'].append(None)
				coordinates['longitude'].append(None)
				coordinates['altitude'].append(None)
			else:
				longitude = location.longitude
				latitude = location.latitude
				coordinates['latitude'].append(latitude)
				coordinates['longitude'].append(longitude)
				
				query = ('https://api.open-elevation.com/api/v1/lookup'
						f'?locations={latitude},{longitude}')
				r = requests.get(query).json()  # json object, various ways you can extract value
				# one approach is to use pandas json functionality:
				altitude = r['results'][0]['elevation']

				coordinates['altitude'].append(altitude)

		return coordinates

	def search_wikipedia(self, city: str):
		"""
		Search for a Wikipedia page by title and return the best match.

		Parameters
		----------
		city : str
			The city to search for.

		Returns
		-------
		str
			The title of the best match.
		"""
		PARAMS = {
			'action': "query",
			'format': "json",
			'list': "search",
			'srsearch': city,
			'srlimit': 1  # Adjust if more results are needed for selection
		}
		try:
			response = requests.get(self.URL, params=PARAMS)
			data = response.json()
			search_results = data['query']['search']
			if search_results:
				return search_results[0]['title']
			else:
				return None
		except requests.exceptions.RequestException as e:
			print(f"Error searching Wikipedia for {city}: {e}")
			return None
		
	def html_to_text(self, html_content):
		soup = BeautifulSoup(html_content, 'html.parser')
		text = ''
		for section in soup.find_all(['h2', 'p']):
			if section.name == 'h2':
				text += '\n\n' + section.get_text() + '\n\n'  # Add extra newlines for headers
			else:
				text += section.get_text() + ' '

		# Remove references in square brackets
		text = re.sub(r'\[.*?\]', '', text)

		# Remove multiple spaces
		text = re.sub(r'\s+', ' ', text)

		# Remove triple or larger newlines and replace with double newlines
		text = re.sub(r'\n{3,}', '\n\n', text)

		# Remove leading and trailing spaces
		text = text.strip()

		# Remove ⓘ symbol
		text = text.replace('ⓘ', '')

		return text
		
	def get_wikipedia_content(self, city: str):
		"""
		Get the main content of a Wikipedia page by title.

		Parameters
		----------
		city : str
			The city to search for.

		Returns
		-------
		str
			The content of the Wikipedia page.
		"""
		PARAMS = {
			'action': "parse",
			'page': city,
			'format': "json",
			'prop': 'text',  # Get the content of the page
			'disabletoc': True,  # Disable the table of contents to keep the text clean
			'wrapoutputclass': ''  # This minimizes the amount of HTML wrapping in output
		}	
		try:
			response = requests.get(self.URL, params=PARAMS)
			data = response.json()
			# Parse text from the HTML if needed
			if 'parse' in data and 'text' in data['parse']:
				html_content = data['parse']['text']['*']
				# Optionally process HTML to plain text or structured text here
				return self.html_to_text(html_content)
			else:
				return "Content not found."
		except requests.exceptions.RequestException as e:
			print(f"Error getting Wikipedia content for {city}: {e}")
			return None

	def get_data_wikipedia(self):
		"""
		Get all the data from Wikipedia for the cities.

		Returns
		-------
		dict
			The dictionary of the Wikipedia data.
		"""
		wikipedia_data = {}
		for city in self.cities:
			print(f"Getting Wikipedia data for {city}...")
			searched_title = self.search_wikipedia(city)
			if searched_title:
				content = self.get_wikipedia_content(searched_title)
				wikipedia_data[city] = {'content': content, 'title': searched_title}
			
			time.sleep(0.001) # Avoid hitting the API too hard

		return wikipedia_data
	
	def get_anual_weather_data(self):
		self.weather_data = []

		for i, city in enumerate(self.cities):
			print(f"Getting weather data for {city}...")

			longitude = self.coordinates['longitude'][i]
			latitude = self.coordinates['latitude'][i]
			altitude = self.coordinates['altitude'][i]

			# Create Point
			point = Point(latitude, longitude, altitude)

			start = pd.Timestamp.now() - pd.DateOffset(years=1)
			start = pd.to_datetime(start.date(), format='%Y-%m-%d')
			# End today
			end = pd.Timestamp.now()
			end = pd.to_datetime(end.date(), format='%Y-%m-%d')

			# Get monthly data
			data = Monthly(point, start, end)
			data = data.fetch()

			# Ensure the index is a DatetimeIndex
			if not isinstance(data.index, pd.DatetimeIndex):
				data.index = pd.to_datetime(data.index, format='%Y-%m-%d')

			months_data = {
				'January': data[data.index.month == 1],
				'February': data[data.index.month == 2],
				'March': data[data.index.month == 3],
				'April': data[data.index.month == 4],
				'May': data[data.index.month == 5],
				'June': data[data.index.month == 6],
				'July': data[data.index.month == 7],
				'August': data[data.index.month == 8],
				'September': data[data.index.month == 9],
				'October': data[data.index.month == 10],
				'November': data[data.index.month == 11],
				'December': data[data.index.month == 12],
				'summer': data[data.index.month.isin([6, 7, 8])],
				'winter': data[data.index.month.isin([12, 1, 2])],
				'autumn': data[data.index.month.isin([9, 10, 11])],
				'spring': data[data.index.month.isin([3, 4, 5])],
				'the past year': data
			}

			keywords_mapping = {
				'tavg': 'Average temperature (°C)',
				'prcp': 'Total precipitation (rainfall) (mm)',
				'wspd': 'Average wind speed (km/h)',
			}

			aggreation = {
				'tavg': np.mean,
				'prcp': np.sum,
				'wspd': np.mean
			}

			keywords_texts = {keyword: '' for keyword in keywords_mapping.keys()}

			for keyword in keywords_texts.keys():
				for month in months_data.keys():
					keywords_texts[keyword] += f'{keywords_mapping[keyword]} in {month}: {aggreation[keyword](months_data[month][keyword]):.2f}. '

			total_text = '\n'.join(list(keywords_texts.values()))

			self.weather_data.append(total_text)

	def save_texts(self):
		"""
		Save the content of the Wikipedia pages to text files.
		"""
		dir_name = f"{self.save_dir}/city_texts"
		if not os.path.exists(dir_name):
			os.makedirs(dir_name)  # Create save directory if it doesn't exist

		texts = [self.wikipedia_data[city]['content'] for city in self.cities]
		texts_weather = self.weather_data

		for i, text in enumerate(texts):
			# Construct a path to save the text
			file_path = os.path.join(dir_name, self.cities[i].replace(' ', '_').replace('.', '').replace(',', '') + '.txt')

			# Write the text to a file
			with open(file_path, 'w', encoding='utf-8') as f:
				f.write(f'Wikipedia information about {self.cities[i]}:\n{text.strip()}')
				f.write('\n\n')
				f.write(f'Weather information about {self.cities[i]}: {texts_weather[i].strip()}')
	
	def save_dataset(self):
		"""
		Save the simplified dataset to a csv file.
		"""
		data = {
			'city': self.cities,
			'country': self.countries,
			'latitude': self.coordinates['latitude'],
			'longitude': self.coordinates['longitude'],
			'altitude': self.coordinates['altitude'], 
			'wiki_title': [self.wikipedia_data[city]['title'] for city in self.cities],
			'wiki_content': [self.wikipedia_data[city]['content'] for city in self.cities],
			'weather_data': self.weather_data
		}
		df = pd.DataFrame(data)
		df.dropna(inplace=True)

		self.cities = df['city'].tolist()
		self.countries = df['country'].tolist()
		self.coordinates = {'latitude': df['latitude'].tolist(), 'longitude': df['longitude'].tolist(), 'altitude': df['altitude'].tolist()}
		self.wikipedia_data = {city: {'content': df[df['city'] == city]['wiki_content'].values[0],
									  'title': df[df['city'] == city]['wiki_title'].values[0]}
							  for city in self.cities}
		self.weather_data = df['weather_data'].tolist()

		df.to_csv(f"{self.save_dir}/city.csv", index=False)