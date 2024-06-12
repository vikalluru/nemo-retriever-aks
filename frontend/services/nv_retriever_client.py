import json
import os

from typing import Dict
from nemo_retriever.retriever_client import RetrieverClient
from pprint import pprint


class NVRetriever:
    def __init__(self, base_url, collection_name="testCollection", pipeline="ranked_hybrid"):
        self.retriever_client =  RetrieverClient(base_url)
        self.collection_id = self.create_collection(collection_name, pipeline)
        self.config = self.load_config()

    def create_collection(self, collection_name, pipeline) -> int:
        # Delete existing collection with this name
        for collection in self.retriever_client.get_collections().collections:
            if collection.name == collection_name:
                return collection.id
        # Create new collection
        try:
            response = self.retriever_client.create_collection(pipeline, name=collection_name)
            return response.collection.id
        except Exception as e:
            print("An error occurred while creating a new collection:", e)

    def load_config(self) -> Dict:
        # Path to the JSON config file
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        with open(config_path, 'r') as file:
            config = json.load(file)
        return config            
        
    def add_to_collection(self, filepaths, callback=None) -> bool:
        assert self.collection_id is not None
        total_paths = len(filepaths)
        try:
            for i, filepath in enumerate(filepaths):
                response = self.retriever_client.add_document(collection_id=self.collection_id, filepath=filepath)
                percentage = int((i + 1) * 100 / total_paths)
                if callback:
                    callback(percentage, f"Processed PDF {filepath}")
                print(f"Added document {filepath} with id {response.documents[0].id}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False
        return True

    def delete_collection(self, collection_id):
        try:
            response = self.retriever_client.delete_collection(collection_id=collection_id)
            print(f"Deleted current collection with id {collection_id}")
        except Exception as e:
            print("An error occured while deleting collection:", e)

        
    def retrieve(self, query):
        context = ""
        try:
            response = self.retriever_client.search_collection(collection_id=self.collection_id, query=query, top_k=self.config["chunks_to_retrieve"])
            context =  "\n\n".join([f"Content with score-{chunk.score}: {chunk.content}" for chunk in response.chunks])
        except Exception as e:
            print("An error occurred while searching the collection:", e)
        return context

if __name__ == "__main__":
    breakpoint()
    ret = NVRetriever("http://51.124.97.12:1984", "br_data_test", "ranked_hybrid")
    ret.add_to_collection(["/home/azureuser/nim-demo-aks/test_data/2018-Annual-Report.pdf"])
    resp = ret.retrieve("What is thte total stock-based compensation expense incurred by Blackrcok in 2018?")
