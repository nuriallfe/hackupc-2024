import requests
import geopy
import pandas as pd
import time

class CreateDataLandmarks:
	def __init__(self, landmarks_file: str, to_file: str):
		"""
		Parameters
		----------
		landmarks_file : str
			The path to the file containing the landmarks.

		to_file : str
			The path to the file to save the dataset.
		"""
		self.landmarks_file: str = landmarks_file
		self.to_file: str = to_file
		self.URL: str = "https://en.wikipedia.org/w/api.php"

		self.landmarks_with_none = []
		
		self.landmarks: list = self.get_data_landmarks()
		self.coordinates: dict = self.get_coordinates()
		self.wikipedia_data: dict = self.get_data_wikipedia()

		self.save_dataset()

	def get_data_landmarks(self):
		"""
		Get the data from the file containing the landmarks.

		Returns
		-------
		list
			The list of landmarks.
		"""
		with open(self.landmarks_file, 'r', encoding='utf-8') as file:
			landmarks = file.read().splitlines()
			landmarks = [landmark.strip() for landmark in landmarks if landmark.strip()]
		return landmarks
	
	def get_coordinates(self):
		"""
		Get the coordinates of the landmarks.

		Returns
		-------
		dict
			The dictionary of the locations.
		"""
		geolocator = geopy.Nominatim(user_agent="landmarks")
		coordinates = {'latitude': [], 'longitude': []}
		for landmark in self.landmarks:
			location = geolocator.geocode(landmark)
			if location is None:
				print(f"Location not found for {landmark}.")
				coordinates['latitude'].append(None)
				coordinates['longitude'].append(None)
				self.landmarks_with_none.append(landmark)
				continue
			coordinates['latitude'].append(location.latitude)
			coordinates['longitude'].append(location.longitude)
		return coordinates

	def search_wikipedia(self, landmark: str):
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
			'srsearch': landmark,
			'srlimit': 1  # Adjust if more results are needed for selection
		}
		response = requests.get(self.URL, params=PARAMS)
		data = response.json()
		search_results = data['query']['search']
		if search_results:
			return search_results[0]['title']
		else:
			return None

	def get_wikipedia_image(self, landmark: str):
		"""
		Get the main image from a Wikipedia page by title.

		Parameters
		----------
		landmark : str
			The landmark to search for.

		Returns
		-------
		str
			The URL of the image.
		"""
		PARAMS = {
			'action': "query",
			'format': "json",
			'titles': landmark,
			'prop': 'pageimages',
			'pithumbsize': 500
		}
		response = requests.get(self.URL, params=PARAMS)
		data = response.json()
		pages = data['query']['pages']
		image_url = "No image found"
		for page in pages.values():
			if 'thumbnail' in page:
				image_url = page['thumbnail']['source']
				break
		return image_url

	def get_wikipedia_content(self, landmark: str):
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
			'titles': landmark,
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
		return "No content found"

	def get_data_wikipedia(self):
		"""
		Get all the data from Wikipedia for the landmarks.

		Returns
		-------
		dict
			The dictionary of the Wikipedia data.
		"""
		wikipedia_data = {}
		for landmark in self.landmarks:
			searched_title = self.search_wikipedia(landmark)
			if searched_title:
				image_url = self.get_wikipedia_image(searched_title)
				content = self.get_wikipedia_content(searched_title)
				wikipedia_data[landmark] = {'image_url': image_url, 'content': content, 'title': searched_title}
			
			time.sleep(0.1) # Avoid hitting the API too hard

		return wikipedia_data
	
	def save_dataset(self):
		"""
		Save the dataset to a csv file.
		"""
		data = {
			'landmark': [landmark for landmark in self.landmarks if landmark not in self.landmarks_with_none],
			'latitude': [self.coordinates['latitude'][i] for i, landmark in enumerate(self.landmarks) if landmark not in self.landmarks_with_none],
			'longitude': [self.coordinates['longitude'][i] for i, landmark in enumerate(self.landmarks) if landmark not in self.landmarks_with_none],
			'wiki_title': [self.wikipedia_data[landmark]['title'] for landmark in self.landmarks if landmark not in self.landmarks_with_none],
			'image_url': [self.wikipedia_data[landmark]['image_url'] for landmark in self.landmarks if landmark not in self.landmarks_with_none],
			'wiki_content': [self.wikipedia_data[landmark]['content'] for landmark in self.landmarks if landmark not in self.landmarks_with_none]
		}

		print(f"{len(self.landmarks_with_none)} landmarks not found and were removed from the dataset.")

		df = pd.DataFrame(data)
		df.to_csv(self.to_file, index=False)
