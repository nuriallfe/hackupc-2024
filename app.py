import tkinter as tk
from sql_class import CloseSearch
from tkinter import messagebox
from gpt_class import MonumentsSearch
import textwrap

monuments_search = MonumentsSearch(
    data_file_path="./data/data.csv",
    landmark_column="landmark",
    wiki_content_column="wiki_content",
    landmarks_directory="./data/monuments",
)

# Function to process the text description
def process_description():
    result_file = ""
    description = description_entry.get()
    
    # Call your models here to process the description
    # For now, let's just display a simple message based on the description
    result_text = f"You want to go to: {description}"

    searcher = CloseSearch(file="./data/data.csv", name="monuments", textual_var = "wiki_content")
    
    results = searcher.search_similars(result_text, number=3)

    for land in results["landmark"]:
        response = monuments_search.query(f"Give me all you know about about the {land} landmark.")
        result_file += f"# {land}"
        result_file += "\n" + (str(response)) + "\n"
        print(textwrap.fill(str(response), 100))
    # Display the result in a message box
    messagebox.showinfo("Result", result_file)

# Create the main window
root = tk.Tk()
root.title("Where do you want to go?")

# Create a label and entry for the description
description_label = tk.Label(root, text="Enter a text description of where you want to go:")
description_label.pack()
description_entry = tk.Entry(root, width=50)
description_entry.pack()

# Create a button to process the description
process_button = tk.Button(root, text="Process", command=process_description)
process_button.pack()

# Run the application
root.mainloop()
