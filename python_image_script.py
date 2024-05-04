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


# Assume other necessary imports and class definitions (like MonumentsSearch and CloseSearch) are done here

# Initialize MonumentsSearch

import sys

def process_user_input(user_input):
    if not user_input:
        return "Please, enter a description."

    #print(f"You: {user_input}") 
    # Search for similar landmarks in a separate thread
    thread = Thread(target=search_image, args=(user_input,))
    thread.start()

def search_image(user_input):
    image_search = ImageSearch(folder='../baiges/downloaded_images/*.jpg')
    result = image_search.search_similars(str(user_input))["monument_name"]

    print(f"The landmark from the image is {result}")

if __name__ == "__main__":
    user_input = sys.argv[1]
    result = process_user_input(user_input)