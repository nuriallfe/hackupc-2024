import tkinter as tk
import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import Point
from sql_class import CloseSearch
from gpt_class import MonumentsSearch
import matplotlib.pyplot as plt

# Initialize MonumentsSearch
monuments_search = MonumentsSearch(
    data_file_path="./data/data.csv",
    landmark_column="landmark",
    wiki_content_column="wiki_content",
    landmarks_directory="./data/monuments",
)

# Function to process the text description
def process_description():
    result_text = description_entry.get()
    if not result_text:
        result_text = "Por favor, ingrese una descripción."
    else:
        # Search for similar landmarks
        searcher = CloseSearch(file="./data/data.csv", name="monuments", textual_var="wiki_content")
        results = searcher.search_similars(result_text, number=3)

        # Plot the landmarks on a map
        geometry = [Point(xy) for xy in zip(results['longitude'], results['latitude'])]
        gdf = GeoDataFrame(results, geometry=geometry)   
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
        ax = world.plot(figsize=(10, 6))
        gdf.plot(ax=ax, marker='o', color='red', markersize=15)
        
        # Display information about the landmarks
        result_text = ""
        for landmark in results["landmark"]:
            response = monuments_search.query(f"¿Qué sabes sobre el monumento {landmark}?")
            result_text += f"\n\n#{landmark}\n{response}"

    result_display.config(state=tk.NORMAL)
    result_display.delete(1.0, tk.END)
    result_display.insert(tk.END, result_text)
    result_display.config(state=tk.DISABLED)

# Create the main window
root = tk.Tk()
root.title("¿Dónde quieres ir?")
root.geometry("800x600")

# Add some styling
root.configure(bg="#f0f0f0")
root.option_add("*Font", "Arial 12")

# Create a label and entry for the description
description_label = tk.Label(root, text="Ingresa una descripción del lugar que quieres visitar:", bg="#f0f0f0")
description_label.pack(pady=10)
description_entry = tk.Entry(root, width=70)
description_entry.pack(pady=5)

# Create a button to process the description
process_button = tk.Button(root, text="Procesar", command=process_description, bg="#4CAF50", fg="white")
process_button.pack(pady=10)

# Create an area to display the result
result_display = tk.Text(root, width=100, height=20, state=tk.DISABLED)
result_display.pack(pady=10)

# Run the application
root.mainloop()

