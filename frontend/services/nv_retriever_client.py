from nemo_retriever.retriever_client import RetrieverClient
from pprint import pprint
import os

class NVRetriever:
    """
    ret.retrieve("What is thte total stock-based compensation expense incurred by Blackrcok in 2018")
    """
    def __init__(self, base_url, collection_name="testCollection", pipeline="ranked_hybrid"):
        self.retriever_client =  RetrieverClient(base_url)
        self.collection_id = self.get_or_create_collection(collection_name, pipeline)

    def get_or_create_collection(self, collection_name, pipeline) -> int:
        for collection in self.retriever_client.get_collections().collections:
            if collection.name == collection_name:
                return collection.id
        try:
            response = self.retriever_client.create_collection(pipeline, name=collection_name)
            return response.collection.id
        except Exception as e:
            print("An error occurred while creating a new collection:", e)
        
    def add_to_collection(self, file_paths, callback) -> bool:
        assert self.collection_id is not None
        total_files = len(file_paths)
        for i, file_path in enumerate(file_paths):
            response = self.retriever_client.add_document(collection_id=self.collection_id, filepath=filepath)
            callback((i+1)/(total_files) * 100, f"Processed PDF {pdf_path}")
            print(f"Added document {file_name} with id {response.documents[0].id}")
        return True

    def delete_collection(self):
        try:
            response = self.retriever_client.delete_collection(collection_id=self.collection_id)
            print(f"Deleted current collection with id {self.collection_id}")
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
