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


import sys
sys.stdout.reconfigure(encoding='utf-8')


# Assume other necessary imports and class definitions (like MonumentsSearch and CloseSearch) are done here

monuments_search = MonumentsSearch(
    data_file_path="../data/city.csv",
    landmark_column="city",
    wiki_content_column="wiki_content",
    landmarks_directory="../data/texts",
)

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
    searcher = CloseSearch(file="../data/data.csv", name="monuments", textual_var="wiki_content")
    results = searcher.search_similars(user_input, number=3)

    result_text = ""
    for landmark in results["landmark"]:
        response = monuments_search.query(f"What do you know about the landmark {landmark}?")
        result_text += f"\n\n### {landmark}\n{response}"

        filename = f'{landmark.replace(" ", "_")}_{1}.jpg'
        try:
            with open(f"../baiges/downloaded_images/{filename}", "rb") as img_file:
                encoded_img = base64.b64encode(img_file.read()).decode('utf-8')
            result_text += f"\n<br><div style='text-align: center'><img src='data:image/jpeg;base64,{encoded_img}' width='300'></div><br>"
        except Exception as exc:
            pass
    
    print(result_text)

if __name__ == "__main__":
    user_input = sys.argv[1]
    result = process_user_input(user_input)