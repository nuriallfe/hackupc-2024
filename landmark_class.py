import requests
import geopy
import pandas as pd
import time
import os
import numpy as np
from dotenv import load_dotenv

class CreateDataLandmarks:
	def __init__(self, landmarks_file: str, save_dir: str, from_csv: str = ''):
		"""
		Parameters
		----------
		landmarks_file : str
			The path to the file containing the landmarks.

		save_dir : str
			The directory to save the dataset.

		from_csv : str
			The path to the csv file containing the precalculated dataset.
		"""
		self.landmarks_file: str = landmarks_file
		self.from_csv: str = from_csv
		self.save_dir: str = save_dir.removesuffix('/')
		self.URL: str = "https://en.wikipedia.org/w/api.php"

		if not from_csv:
			self.landmarks, self.cities, self.countries, self.totals = self.get_data_landmarks()
			self.wikipedia_data: dict = self.get_data_wikipedia()
			self.coordinates: dict = self.get_coordinates()

			self.save_dataset()
		
		self.download_images()
		self.save_texts()

	def get_data_landmarks(self):
		"""
		Get the data from the file containing the landmarks.

		Returns
		-------
		list
			The list of landmarks.
		"""
		if self.from_csv:
			df = pd.read_csv(self.from_csv)
			landmarks = df['landmark'].tolist()
		else:
			with open(self.landmarks_file, 'r', encoding='utf-8') as file:
				names = file.read().splitlines()
				landmarks = [n.split(',')[0].strip() for n in names]
				cities = [n.split(',')[1].strip() for n in names]
				countries = [n.split(',')[2].strip() for n in names]

		return landmarks, cities, countries, names
	
	def get_coordinates(self):
		"""
		Get the coordinates of the landmarks.

		Returns
		-------
		dict
			The dictionary of the locations.
		"""
		geolocator = geopy.Nominatim(user_agent="landmarks", timeout=10)
		coordinates = {'latitude': [], 'longitude': []}
		for total in self.totals:
			location = geolocator.geocode(total)
			if location is None:
				# Try getting the location from the Wikipedia data
				new_landmark = self.wikipedia_data[total]['title']
				if new_landmark is not None:
					location = geolocator.geocode(new_landmark)
				
				if location is None:
					print(f"Location not found for {total}.")
					coordinates['latitude'].append(None)
					coordinates['longitude'].append(None)
				else:
					coordinates['latitude'].append(location.latitude)
					coordinates['longitude'].append(location.longitude)
			else:
				coordinates['latitude'].append(location.latitude)
				coordinates['longitude'].append(location.longitude)
		return coordinates

	def search_wikipedia(self, total: str):
		"""
		Search for a Wikipedia page by title and return the best match.

		Parameters
		----------
		landmark : str
			The landmark to search for.

		Returns
		-------
		str
			The title of the best match.
		"""
		PARAMS = {
			'action': "query",
			'format': "json",
			'list': "search",
			'srsearch': total,
			'srlimit': 1  # Adjust if more results are needed for selection
		}
		response = requests.get(self.URL, params=PARAMS)
		data = response.json()
		search_results = data['query']['search']
		if search_results:
			return search_results[0]['title']
		else:
			return None

	def get_wikipedia_content(self, title: str):
		"""
		Get the main content of a Wikipedia page by title.

		Parameters
		----------
		landmark : str
			The landmark to search for.

		Returns
		-------
		str
			The content of the Wikipedia page.
		"""
		PARAMS = {
			'action': "query",
			'prop': 'extracts',
			'format': "json",
			'titles': title,
			'exlimit': 1,
			'explaintext': True,
			'exintro': False  # Change to True if you only want the intro part
		}
		response = requests.get(self.URL, params=PARAMS)
		data = response.json()
		pages = data['query']['pages']
		for page in pages.values():
			if 'extract' in page:
				return page['extract']
		else:
			return None

	def get_data_wikipedia(self):
		"""
		Get all the data from Wikipedia for the landmarks.

		Returns
		-------
		dict
			The dictionary of the Wikipedia data.
		"""
		wikipedia_data = {}
		for i, total in enumerate(self.totals):
			print(f"Getting Wikipedia data for {total} ({i}/{len(self.landmarks)})")
			searched_title = self.search_wikipedia(total)
			content = self.get_wikipedia_content(searched_title) if searched_title is not None else None
			
			wikipedia_data[total] = {'content': content, 'title': searched_title}
			
		return wikipedia_data

	def download_images(self):
		"""
		Download images from Flickr API based on the landmarks.
		"""

		if self.from_csv:
			self.df = pd.read_csv(self.from_csv)
			self.landmarks = self.df['landmark'].tolist()
			self.cities = self.df['city'].tolist()
			self.countries = self.df['country'].tolist()
			self.totals = [f"{landmark}, {city}, {country}" for landmark, city, country in zip(self.landmarks, self.cities, self.countries)]

		def fetch_images(text_search, num_images=10):
			"""
			Fetches images from Flickr API based on a text search, ensuring it gathers a specified number of valid image URLs.

			Args:
				text_search (str): Text to search for
				num_images (int): Desired number of images to fetch

			Returns:
				list: List of image URLs
			"""
			url = 'https://api.flickr.com/services/rest/'
			images = []
			page = 1

			while len(images) < num_images:
				params = {
					'method': 'flickr.photos.search',
					'api_key': self.flickr_api_key,
					'text': text_search,
					'sort': 'relevance',
					'media': 'photos',
					'safe_search': 1,
					'extras': 'url_l',  # 'url_l' is more likely to be available
					'format': 'json',
					'nojsoncallback': 1,
					'per_page': 100,  # Fetch more photos per request
					'page': page
				}

				try:
					response = requests.get(url, params=params)
					response.raise_for_status()
					photos = response.json()['photos']['photo']
					for photo in photos:
						if 'url_l' in photo and len(images) < num_images:
							images.append(photo['url_l'])
					page += 1
				except requests.RequestException as e:
					print(f"Error fetching data: {e}")
					break

			return images
		
		# Fetch images for each landmark

		# Load the API key from .env
		load_dotenv()

		self.flickr_api_key = os.environ.get('FLICKR_API_KEY')

		directory = f"{self.save_dir}/downloaded_images"

		if not os.path.exists(directory):
					os.makedirs(directory)

		for i, landmark in enumerate(self.landmarks):
			print(f"Downloading images for {landmark} ({i+1}/{len(self.landmarks)})")
			images = fetch_images(landmark, num_images=3)
			
			for j, image_url in enumerate(images):
				filename = f'{self.totals[i].replace(" ", "_").replace(".", "").replace(",", "")}_{j+1}.jpg'  # Replace spaces with underscores and append the index
				try:
					response = requests.get(image_url)
					response.raise_for_status()
					with open(os.path.join(directory, filename), 'wb') as f:
						f.write(response.content)
				except requests.RequestException as e:
					print(f"Error downloading image {filename}: {e}")

	def save_texts(self):
		"""
		Save the content of the Wikipedia pages to text files.
		"""
		dir_name = f"{self.save_dir}/texts"
		if not os.path.exists(dir_name):
			os.makedirs(dir_name)  # Create save directory if it doesn't exist

		if self.from_csv:
			self.df = pd.read_csv(self.from_csv)
			texts = self.df['wiki_content'].tolist()
		else:
			texts = [self.wikipedia_data[total]['content'] for total in self.totals]

		for i, text in enumerate(texts):
			# Construct a path to save the text
			file_path = os.path.join(dir_name, self.totals[i].replace(' ', '_').replace('.', '').replace(',', '') + '.txt')

			# Write the text to a file
			with open(file_path, 'w', encoding='utf-8') as f:
				f.write(text)
	
	def save_dataset(self):
		"""
		Save the dataset to a csv file.
		"""
		data = {
			'landmark': self.landmarks,
			'city': self.cities,
			'country': self.countries,
			'latitude': self.coordinates['latitude'],
			'longitude': self.coordinates['longitude'],
			'wiki_title': [self.wikipedia_data[total]['title'] for total in self.totals],
			'wiki_content': [self.wikipedia_data[total]['content'] for total in self.totals]
		}

		self.df = pd.DataFrame(data)

		rows1 = self.df.shape[0]

		# Remove lines with python None values
		self.df.dropna(inplace=True)

		rows2 = self.df.shape[0]
		print(f"Removed {rows1 - rows2} rows with missing data.")

		self.landmarks = self.df['landmark'].tolist()
		self.cities = self.df['city'].tolist()
		self.countries = self.df['country'].tolist()
		self.totals = [f"{landmark}, {city}, {country}" for landmark, city, country in zip(self.landmarks, self.cities, self.countries)]
		self.coordinates = {'latitude': self.df['latitude'].tolist(), 'longitude': self.df['longitude'].tolist()}
		self.wikipedia_data = {total: {'title': title, 'content': content} for total, title, content in zip(self.totals, self.df['wiki_title'].tolist(), self.df['wiki_content'].tolist())}
	

		self.df.to_csv(f"{self.save_dir}/data.csv", index=False)
