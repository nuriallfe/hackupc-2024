#extract cities

import pandas as pd
import os
from city import CreateCityDescriptions

path = './Data/1000Cities.csv'
data = pd.read_csv(path)

cities_txt_path = './Data/city_names.txt'

with open(cities_txt_path, 'w', encoding='utf-8') as file:
    for city in data['Name of City']:
        file.write(city + '\n')

dataset_save_dir = './data'  

if not os.path.exists(dataset_save_dir):
    os.makedirs(dataset_save_dir)

from_csv = "./data"

CreateCityDescriptions(cities_txt_path, dataset_save_dir) 