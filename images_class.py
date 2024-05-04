import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
import torch
from torchvision import models, transforms
from torch.nn.functional import cosine_similarity
from PIL import Image
import glob
import re

class ImageSearch:
    def __init__(self, folder='../data/downloaded_images/*.jpg', name = "images", username = 'demo', password = 'demo', hostname='localhost', port='1972', namespace='USER', recalculate=False):
        self.name = name
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.recalculate = recalculate
        self.namespace = namespace
        self.engine = None
        self.model = models.resnet18(pretrained=True)
        self.model.eval()
        self.paths = glob.glob(folder)
        self.embeddings = False
        self.connect_to_database()
        self.create_images_table()
        if self.embeddings == False:
            self.generate_embeddings()
            self.insert_data_into_database()

    def connect_to_database(self):
        CONNECTION_STRING = f"iris://{self.username}:{self.password}@{self.hostname}:{self.port}/{self.namespace}"
        self.engine = create_engine(CONNECTION_STRING)

    def create_images_table(self):
        s_values = {
            "float64": "DOUBLE",
            "object": "VARCHAR(20000)",
            "O": "VARCHAR(20000)",
            "int32": "INT",
            "int64": "INT"
        }
        with self.engine.connect() as conn:
            with conn.begin():
                try:
                    sql = f"CREATE TABLE {self.name} (\n"
                    sql += " monument_name VARCHAR(20000), \n description_vector VECTOR(DOUBLE, 1000)\n)"
                    conn.execute(text(sql))
                except:
                    if self.recalculate:
                        sql = f"DROP TABLE {self.name}"
                        conn.execute(text(sql))
                        sql = f"CREATE TABLE {self.name} (\n"
                        sql += " monument_name VARCHAR(20000), \n description_vector VECTOR(DOUBLE, 1000)\n)"
                        conn.execute(text(sql))
                    else:
                        self.embeddings = True
                
    def load_image(self, image_path):
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
        image = Image.open(image_path).convert('RGB')  # Convertir la imagen a RGB
        image = transform(image).unsqueeze(0)  # Añade una dimensión al principio
        return image
    def clean_image_name(self, file_path):
        base_name = os.path.basename(file_path).replace('.jpg', '')
        
        # Delete any numbers and underscores at the end of the file name
        clean_name = re.sub(r'_[0-9]+$', '', base_name)
        
        # Replace any remaining underscores with spaces
        clean_name = clean_name.replace('_', ' ')
        
        return clean_name

    def get_embedding(self, image_tensor):
        with torch.no_grad():
            embedding = self.model(image_tensor)
        return embedding
    def generate_embeddings(self):
        self.image_embeddings = [self.get_embedding(self.load_image(img_path)) for img_path in self.paths]

    def insert_data_into_database(self):
        with self.engine.connect() as conn:
            with conn.begin():
                for index, row in enumerate(self.paths):
                    sql = text(f"""
                        INSERT INTO {self.name} 
                        (monument_name, description_vector) 
                        VALUES (:monument_name, TO_VECTOR(:description_vector))
                    """)
                    to_execute = {}
                    to_execute["monument_name"] = row
                    to_execute['description_vector'] = str(self.image_embeddings[index].tolist()[0])
                    conn.execute(sql, to_execute)

    def search_similars(self, image_path, condition = "", number= 10):
        search_vector = self.get_embedding(self.load_image(image_path)).tolist()[0]
        with self.engine.connect() as conn:
            with conn.begin():
                sql = text(f"""
                    SELECT TOP {number} * FROM {self.name} 
                    {condition}
                    ORDER BY VECTOR_COSINE(description_vector, TO_VECTOR(:search_vector)) DESC
                """)
                results = conn.execute(sql, {'search_vector': str(search_vector)}).fetchall()
        results_df = pd.DataFrame(results, columns=["monument_name", "description_vector"])

        results_df["monument_name"] = [self.clean_image_name(e) for e in results_df["monument_name"]]
        pd.set_option('display.max_colwidth', None)  # Easier to read description
        return results_df

#image_search = ImageSearch()
#print(image_search.search_similars("../data/test_images/uni.jpg")["monument_name"])