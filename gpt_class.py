import pandas as pd
from llama_index import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    OpenAIEmbedding,
    ServiceContext,
    StorageContext,
)

from llama_index.llms.ollama import Ollama
from llama_index.llms import OpenAI
from llama_index.text_splitter import SentenceSplitter
from llama_iris import IRISVectorStore
from dotenv import load_dotenv
import os
import getpass
import textwrap

import getpass
import os
from dotenv import load_dotenv

load_dotenv(override=True)

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("OpenAI API Key:")


class MonumentsSearch:
    def __init__(
        self,
        data_file_path,
        landmark_column,
        wiki_content_column,
        landmarks_directory,
        iris_hostname="localhost",
        iris_port="1972",
        iris_namespace="USER",
        openai_api_key=None,
        llama_model="gpt-3.5-turbo",
        openai_embedding_model="BAAI/bge-base-en-v1.5",
        vector_table_name="apunts",
        vector_embed_dim=1536,
    ):
        self.data_file_path = data_file_path
        self.landmark_column = landmark_column
        self.wiki_content_column = wiki_content_column
        self.landmarks_directory = landmarks_directory
        self.iris_hostname = iris_hostname
        self.iris_port = iris_port
        self.iris_namespace = iris_namespace
        self.openai_api_key = openai_api_key
        self.llama_model = llama_model
        self.openai_embedding_model = openai_embedding_model
        self.vector_table_name = vector_table_name
        self.vector_embed_dim = vector_embed_dim

    def read_data(self):
        df = pd.read_csv(self.data_file_path)
        for i, e in df.iterrows():
            with open(
                f"{self.landmarks_directory}/{e[self.landmark_column]}.txt",
                "w",
                encoding="utf8",
            ) as w:
                w.write(e[self.wiki_content_column])

    def setup_iris_connection(self):
        global CONNECTION_STRING
        username = 'demo'
        password = 'demo' 
        hostname = os.getenv('IRIS_HOSTNAME', 'localhost')
        print(hostname)
        port = '1972' 
        namespace = 'USER'
        CONNECTION_STRING = f"iris://{username}:{password}@{hostname}:{port}/{namespace}"

        return CONNECTION_STRING

    def setup_openai(self):
        if not self.openai_api_key:
            self.openai_api_key = getpass.getpass("OpenAI API Key:")
        os.environ["OPENAI_API_KEY"] = self.openai_api_key
        llm = OpenAI(model=self.llama_model, temperature=0.01)
        embed_model = OpenAIEmbedding()
        service_context = ServiceContext.from_defaults(llm=llm, embed_model=embed_model)
        return service_context

    def build_index(self):
        documents = SimpleDirectoryReader(self.landmarks_directory).load_data()
        connection_string = self.setup_iris_connection()
        service_context = self.setup_openai()
        vector_store = IRISVectorStore.from_params(
            connection_string=CONNECTION_STRING,
            table_name=self.vector_table_name,
            embed_dim=self.vector_embed_dim,
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True,
            service_context=service_context,
        )
        return index.as_query_engine()

    def query(self, query_text):
        query_engine = self.build_index()
        response = query_engine.query(query_text)
        return response


# Example usage:
monuments_search = MonumentsSearch(
    data_file_path="./data/data.csv",
    landmark_column="landmark",
    wiki_content_column="wiki_content",
    landmarks_directory="./data/monuments",
)
monuments_search.read_data()

response = monuments_search.query("All the monuments that are in Amsterdam")
print(textwrap.fill(str(response), 100))

response = monuments_search.query("What happened in the mid 1980s?")
print(textwrap.fill(str(response), 100))

response = monuments_search.query("Create questions, and answers, based on the info you know")
print(textwrap.fill(str(response), 100))
