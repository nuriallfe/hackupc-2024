import tkinter as tk
from tkinterweb import HtmlFrame  # This will handle the HTML rendering
import markdown2  # Convert Markdown to HTML
import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import Point
from sql_class import CloseSearch
from gpt_class import MonumentsSearch
import matplotlib.pyplot as plt
from threading import Thread
import time

# Assume other necessary imports and class definitions (like MonumentsSearch and CloseSearch) are done here

# Initialize MonumentsSearch
monuments_search = MonumentsSearch(
    data_file_path="./data/data.csv",
    landmark_column="landmark",
    wiki_content_column="wiki_content",
    landmarks_directory="./data/texts",
)

# Flag to control user input
can_send_message = True

def process_description():
    global can_send_message
    if not can_send_message:
        return

    user_input = description_entry.get()
    description_entry.delete(0, tk.END)  # Clear the input field after processing
    if not user_input:
        display_conversation("Please, enter a description.", "system")
        return

    display_conversation(f"You: {user_input}", "user")  # Display user input in the conversation
    can_send_message = False  # Prevent sending another message until the bot responds
    description_entry.config(state=tk.DISABLED)
    process_button.config(state=tk.DISABLED)

    # Search for similar landmarks in a separate thread
    thread = Thread(target=search_landmarks, args=(user_input,))
    thread.start()

def search_landmarks(user_input):
    searcher = CloseSearch(file="./data/data.csv", name="monuments", textual_var="wiki_content")
    results = searcher.search_similars(user_input, number=3)

    result_text = ""
    for landmark in results["landmark"]:
        response = monuments_search.query(f"What do you know about the landmark {landmark}?")
        result_text += f"\n\n### {landmark}\n{response}"
    
    display_conversation(result_text, "system")

def display_conversation(text, sender):
    formatted_text = markdown2.markdown(text) if sender == "system" else f"<div style='color: green;'>{text}</div>"
    animate_text(formatted_text, sender)

def animate_text(text, sender):
    global can_send_message
    if sender == "system":
        parts = text.split('\n')
        for part in parts:
            chat_display.html_text += part + "<br>"
            chat_display.load_html(chat_display.html_text)
            time.sleep(0.05)  # Adjust timing for realistic typing effect
        can_send_message = True  # Allow the user to send another message
        description_entry.config(state=tk.NORMAL)
        process_button.config(state=tk.NORMAL)
    else:
        chat_display.html_text += text + "<br>"
        chat_display.load_html(chat_display.html_text)

# Create the main window
root = tk.Tk()
root.title("Where would you like to go?")
root.geometry("800x600")

# Create a container for the chat display
chat_display = HtmlFrame(root, horizontal_scrollbar="auto", messages_enabled=False)
chat_display.html_text = ""  # Initialize an empty string to store HTML content
chat_display.pack(fill="both", expand=True, padx=10, pady=10)

# Frame for user input
input_frame = tk.Frame(root)
input_frame.pack(fill="x", side="bottom", padx=10, pady=10)

# Input area for descriptions
description_entry = tk.Entry(input_frame, font=("Helvetica", 16), width=50)
description_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

# Button to process the input
process_button = tk.Button(input_frame, text="Send", command=process_description, bg="green", fg="white", relief="raised", font=("Helvetica", 10))
process_button.pack(side="right")

root.mainloop()