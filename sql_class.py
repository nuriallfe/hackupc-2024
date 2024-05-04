import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text

class MonumentSearch:
    def __init__(self, file='./data/data.csv', name = "monuments", textual_var = "wiki_content", username = 'demo', password = 'demo', hostname='localhost', port='1972', namespace='USER'):
        self.name = name
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.namespace = namespace
        self.engine = None
        self.model = None
        self.data = pd.read_csv(file)
        self.columns = self.data.columns
        self.types = self.data.dtypes
        self.textual_var = textual_var
        self.connect_to_database()
        self.create_monuments_table()
        self.load_sentence_transformer_model()
        self.generate_embeddings()
        self.insert_data_into_database()

    def connect_to_database(self):
        CONNECTION_STRING = f"iris://{self.username}:{self.password}@{self.hostname}:{self.port}/{self.namespace}"
        self.engine = create_engine(CONNECTION_STRING)

    def create_monuments_table(self):
        s_values = {
            "float64": "DOUBLE",
            "object": "VARCHAR(20000)",
            "O": "VARCHAR(20000)",
            "int32": "INT"
        }
        with self.engine.connect() as conn:
            with conn.begin():
                try:
                    sql = f"CREATE TABLE {self.name} (\n"
                    sql += ",\n".join(f'{e} {s_values[str(t)]}' for e, t in zip(self.columns, self.types))
                    sql += ", \n description_vector VECTOR(DOUBLE, 384)\n)"
                    conn.execute(text(sql))
                except:
                    sql = f"""
                        DROP TABLE {self.name}
                    """
                    conn.execute(text(sql))
                    sql = f"CREATE TABLE {self.name} ("
                    sql += ",\n".join(f'{e} {s_values[str(t)]}' for e, t in zip(self.columns, self.types))
                    sql += ", \n description_vector VECTOR(DOUBLE, 384))"
                    conn.execute(text(sql))

    def load_sentence_transformer_model(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def generate_embeddings(self):
        self.data["description_vector"] = self.model.encode(self.data[self.textual_var].tolist(), normalize_embeddings=True).tolist()

    def insert_data_into_database(self):
        with self.engine.connect() as conn:
            with conn.begin():
                for index, row in self.data.iterrows():
                    sql = text(f"""
                        INSERT INTO {self.name} 
                        ({",".join(e for e in self.columns)}, description_vector) 
                        VALUES ({",".join(':'+e for e in self.columns)}, TO_VECTOR(:description_vector))
                    """)

                    to_execute = {k: row[k] for k in self.columns}
                    to_execute['description_vector'] = str(row['description_vector'])
                    conn.execute(sql, to_execute)

    def search_monuments(self, description_search, condition = "", number= 10):
        search_vector = self.model.encode(description_search, normalize_embeddings=True).tolist()
        with self.engine.connect() as conn:
            with conn.begin():
                sql = text(f"""
                    SELECT TOP {number} * FROM {self.name} 
                    {condition}
                    ORDER BY VECTOR_COSINE(description_vector, TO_VECTOR(:search_vector)) DESC
                """)
                results = conn.execute(sql, {'search_vector': str(search_vector)}).fetchall()
        results_df = pd.DataFrame(results, columns=list(self.columns) + ["description_vector"])
        pd.set_option('display.max_colwidth', None)  # Easier to read description
        return results_df

