# python_script.py
import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import Point
from sql_class import CloseSearch
from gpt_class import MonumentsSearch
import matplotlib.pyplot as plt
from threading import Thread
import time
import base64
from images_class import ImageSearch

import sys
sys.stdout.reconfigure(encoding='utf-8')
import osmnx

# Assume other necessary imports and class definitions (like MonumentsSearch and CloseSearch) are done here


cities_search = MonumentsSearch(
    data_file_path="../data/city.csv",
    landmark_column="city",
    wiki_content_column="wiki_content",
    landmarks_directory="../data/city_texts"
)
import sys

def process_user_input(user_input):
    if not user_input:
        return "Please, enter a description."

    #print(f"You: {user_input}") 
    # Search for similar landmarks in a separate thread
    thread = Thread(target=search_image, args=(user_input,))
    thread.start()

def search_image(user_input):
    image_search = ImageSearch(folder='../data/city_images/*.jpg', name="cities")
    result = image_search.search_similars(str(user_input))
    ciutat = result["monument_name"][0]
    text = f"# {ciutat} \n\n "
    result_text = text

    result_text += str(cities_search.query(f"Create a brew (2-3 lines) description about the city of {ciutat}")) + "\n"

    result_text += f"\n**Other similar cities are {result['monument_name'][1]} and {result['monument_name'][2]}**"

    figure, ax = plt.subplots(figsize=(12, 8))
    # Retrieve the area as a GeoDataFrame
    area = osmnx.geocode_to_gdf(ciutat)

    # Plot the area on the specified axis
    area.plot(ax=ax, facecolor="black")
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    # Turn off the axis
    ax.axis('off')

    # Save the plot as an image file
    plt.savefig("../data/generatedmap.png")
    
    print(result_text)


if __name__ == "__main__":
    user_input = sys.argv[1]
    result = process_user_input(user_input)