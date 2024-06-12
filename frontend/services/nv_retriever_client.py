from nemo_retriever.retriever_client import RetrieverClient
from pprint import pprint
import os

class NVRetriever:
    """
    ret.retrieve("What is thte total stock-based compensation expense incurred by Blackrcok in 2018")
    """
    def __init__(self, base_url, collection_name="testCollection", pipeline="ranked_hybrid"):
        self.retriever_client =  RetrieverClient(base_url)
        self.collection_id = self.create_collection(collection_name, pipeline)

    def create_collection(self, collection_name, pipeline) -> int:
        # Delete existing collection with this name
        for collection in self.retriever_client.get_collections().collections:
            if collection.name == collection_name:
                self.delete_collection(collection.id)
        # Create new collection
        try:
            response = self.retriever_client.create_collection(pipeline, name=collection_name)
            return response.collection.id
        except Exception as e:
            print("An error occurred while creating a new collection:", e)
        
    def add_to_collection(self, filepaths, callback) -> bool:
        assert self.collection_id is not None
        total_paths = len(filepaths)
        try:
            for i, filepath in enumerate(filepaths):
                response = self.retriever_client.add_document(collection_id=self.collection_id, filepath=filepath)
                percentage = int((i + 1) * 100 / total_paths)
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

        
    def retrieve(self, query, top_k=3):
        try:
            response = self.retriever_client.search_collection(collection_id=self.collection_id, query=query, top_k=3)
            print(response)
        except Exception as e:
            print("An error occurred while searching the collection:", e)

if __name__ == "__main__":
    ret = NVRetriever("http://localhost:1984", "br_data_test", "ranked_hybrid")
    # ret.add_to_collection("/home/azureuser/nim-demo-aks/blackrock_data")
