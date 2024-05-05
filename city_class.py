import geopy
import pandas as pd
import time
import os
import numpy as np
import requests

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
        
        self.cities, self.countries = self.get_data_cities()

        if not from_csv:
            self.coordinates: dict = self.get_coordinates()
            self.wikipedia_data: dict = self.get_data_wikipedia()

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
        coordinates = {'latitude': [], 'longitude': []}
        for city, country in zip(self.cities, self.countries):
            location = geolocator.geocode(f"{city}, {country}")
            if location is None:
                print(f"Location not found for {city}.")
                coordinates['latitude'].append(None)
                coordinates['longitude'].append(None)
            else:
                coordinates['latitude'].append(location.latitude)
                coordinates['longitude'].append(location.longitude)
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
            'action': "query",
            'prop': 'extracts',
            'format': "json",
            'titles': city,
            'exlimit': 1,
            'explaintext': True,
            'exintro': False  # Change to True if you only want the intro part
        }
        try:
            response = requests.get(self.URL, params=PARAMS)
            data = response.json()
            pages = data['query']['pages']
            for page in pages.values():
                if 'extract' in page:
                    return page['extract']
            else:
                return None
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
            searched_title = self.search_wikipedia(city)
            if searched_title:
                content = self.get_wikipedia_content(searched_title)
                wikipedia_data[city] = {'content': content, 'title': searched_title}
            
            time.sleep(0.001) # Avoid hitting the API too hard

        return wikipedia_data

    def save_texts(self):
        """
        Save the content of the Wikipedia pages to text files.
        """
        dir_name = f"{self.save_dir}/city_texts"
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)  # Create save directory if it doesn't exist

        if self.from_csv:
            self.df = pd.read_csv(self.from_csv)
            texts = self.df['wiki_content'].tolist()
        else:
            texts = [self.wikipedia_data[city]['content'] for city in self.cities]

        for i, text in enumerate(texts):
            # Construct a path to save the text
            file_path = os.path.join(dir_name, self.cities[i].replace(' ', '_').replace('.', '').replace(',', '') + '.txt')

            # Write the text to a file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
    
    def save_dataset(self):
        """
        Save the simplified dataset to a csv file.
        """
        data = {
            'city': self.cities,
            'country': self.countries,
            'latitude': self.coordinates['latitude'],
            'longitude': self.coordinates['longitude'],
            'wiki_title': [self.wikipedia_data[city]['title'] for city in self.cities],
            'wiki_content': [self.wikipedia_data[city]['content'] for city in self.cities]
        }
        df = pd.DataFrame(data)
        df.dropna(inplace=True)

        self.cities = df['city'].tolist()
        self.countries = df['country'].tolist()
        self.coordinates = {'latitude': df['latitude'].tolist(), 'longitude': df['longitude'].tolist()}
        self.wikipedia_data = {city: {'content': df[df['city'] == city]['wiki_content'].values[0],
                                      'title': df[df['city'] == city]['wiki_title'].values[0]}
                              for city in self.cities}


        df.to_csv(f"{self.save_dir}/city.csv", index=False)