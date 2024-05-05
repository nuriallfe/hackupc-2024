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
import matplotlib.pyplot as plt


import sys
sys.stdout.reconfigure(encoding='utf-8')

import osmnx

# Assume other necessary imports and class definitions (like MonumentsSearch and CloseSearch) are done here

# Initialize MonumentsSearch
monuments_search = MonumentsSearch(
    data_file_path="../data/data.csv",
    landmark_column="landmark",
    wiki_content_column="wiki_content",
    landmarks_directory="../data/texts",
)

import sys

def process_user_input(user_input):
    if not user_input:
        return "Please, enter a description."

    #print(f"You: {user_input}") 
    # Search for similar landmarks in a separate thread
    thread = Thread(target=search_landmarks, args=(user_input,))
    thread.start()

def search_landmarks(user_input):

    city_searcher = CloseSearch(file="../data/city.csv", name="cities", textual_var="wiki_content")

    results = city_searcher.search_similars(user_input, number=1)
    ciutat = results["city"][0]
    latitud = results["latitude"][0]
    longitud = results["longitude"][0]
    text = f"# {ciutat} \n\n "
    result_text = text

    monu_searcher = CloseSearch(file="../data/data.csv", name="monuments", textual_var="wiki_content",add_distances=True, lat1= latitud, long1 =longitud,  recalculate=True)


    where = f"WHERE distance < {1000}"
    results = monu_searcher.search_similars(user_input, number=3, condition=where)

    lons = [e for e in results["longitude"]]
    lats = [e for e in results["latitude"]]
    for landmark in results["landmark"]:
        response = monuments_search.query(f"What do you know about the landmark {landmark}?")
        result_text += f"\n\n### {landmark}\n{response}"

        filename = f'{landmark.replace(" ", "_")}_{1}.jpg'
        try:
            with open(f"../data/downloaded_images/{filename}", "rb") as img_file:
                encoded_img = base64.b64encode(img_file.read()).decode('utf-8')
            result_text += f"\n<br><div style='text-align: center'><img src='data:image/jpeg;base64,{encoded_img}' width='300'></div><br>"
        except Exception as exc:
            pass


    figure, ax = plt.subplots(figsize=(12, 8))
    # Retrieve the area as a GeoDataFrame
    area = osmnx.geocode_to_gdf(ciutat)

    # Plot the area on the specified axis
    area.plot(ax=ax, facecolor="black")
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    ax.scatter(lons, lats, color='red', label='Points')

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    # Turn off the axis
    ax.axis('off')

    # Save the plot as an image file
    plt.savefig("../data/generatedmap.png")
    
    print(result_text)

if __name__ == "__main__":
    user_input = sys.argv[1]
    result = process_user_input(user_input)