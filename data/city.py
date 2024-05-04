import geopy
import pandas as pd
import time
import os
import requests

class CreateCityDescriptions:
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

        self.landmarks_with_none = []
        
        self.landmarks: list = self.get_data_landmarks()

        if not from_csv:
            self.coordinates: dict = self.get_coordinates()
            self.wikipedia_data: dict = self.get_data_wikipedia()

            self.save_dataset()
        
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
            else:
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
        try:
            response = requests.get(self.URL, params=PARAMS)
            data = response.json()
            search_results = data['query']['search']
            if search_results:
                return search_results[0]['title']
            else:
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error searching Wikipedia for {landmark}: {e}")
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
        try:
            response = requests.get(self.URL, params=PARAMS)
            data = response.json()
            pages = data['query']['pages']
            for page in pages.values():
                if 'thumbnail' in page:
                    image_url = page['thumbnail']['source']
                    return image_url   
        except requests.exceptions.RequestException as e:
            print(f"Error getting Wikipedia image for {landmark}: {e}")
        return None
        
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
            print(f"Error getting Wikipedia content for {landmark}: {e}")
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
        for landmark in self.landmarks:
            searched_title = self.search_wikipedia(landmark)
            if searched_title:
                image_url = self.get_wikipedia_image(searched_title)
                content = self.get_wikipedia_content(searched_title)
                wikipedia_data[landmark] = {'image_url': image_url, 'content': content, 'title': searched_title}
            
            time.sleep(0.001) # Avoid hitting the API too hard

        return wikipedia_data

    def download_images(self):
        """
        Downloads each image from a list of image URLs into a specified directory.
        """
        dir_name = f"{self.save_dir}/images"
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)  # Create save directory if it doesn't exist

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Referer': 'https://www.google.com'
        }

        if self.from_csv:
            self.df = pd.read_csv(self.from_csv)
            image_urls = self.df['image_url'].tolist()
        else:
            image_urls = [self.wikipedia_data[landmark]['image_url'] for landmark in self.landmarks]

        error_count = 0
        for i, url in enumerate(image_urls):
            try:
                response = requests.get(url, stream=True, headers=headers)
                if response.status_code == 200:
                    # Construct a path to save the image
                    file_path = os.path.join(dir_name, self.landmarks[i].replace(' ', '_').replace('.', '').replace(',', '') + '.jpg')

                    # Write the image to a file
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                else:
                    error_count += 1
            except requests.RequestException as e:
                pass

        print(f"{error_count} images could not be downloaded.")

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
            texts = [self.wikipedia_data[landmark]['content'] for landmark in self.landmarks]

        for i, text in enumerate(texts):
            # Construct a path to save the text
            file_path = os.path.join(dir_name, self.landmarks[i].replace(' ', '_').replace('.', '').replace(',', '') + '.txt')

            # Write the text to a file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
    
    def save_dataset(self):
        """
        Save the simplified dataset to a csv file.
        """
        data = {
            'city': self.landmarks,
            'latitude': self.coordinates['latitude'],
            'longitude': self.coordinates['longitude'],
            'wiki_content': [self.wikipedia_data[landmark]['content'] for landmark in self.landmarks]
        }
        df = pd.DataFrame(data)
        df.to_csv(f"{self.save_dir}/cities_information.csv", index=False)




