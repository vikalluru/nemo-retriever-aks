import os
import json
import subprocess

from typing import List, Dict
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.schema import Document
from tika import parser

class OSSRetriever:
    def __init__(self):
        self.faiss_db = None
        self.config = self.load_config()
        self.embed_tool = OpenAIEmbeddings(model=self.config["openai_model"])

    def load_config(self) -> Dict:
        # Path to the JSON config file
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        with open(config_path, 'r') as file:
            config = json.load(file)
        return config

    def get_embedding_type(self) -> Embeddings:
        return self.embed_tool

    def ensure_tika_server_running(self):
        try:
            # Check if Java is installed
            java_version = subprocess.run(['java', '-version'], capture_output=True, text=True)
            if java_version.returncode != 0:
                raise EnvironmentError("Java is not installed or not found in PATH.")

            # Check if Tika server is running
            tika_server_url = "http://localhost:9998"
            response = subprocess.run(['curl', '-X', 'GET', tika_server_url], capture_output=True, text=True)
            if response.returncode != 0:
                # If Tika server is not running, start it
                tika_server_jar = "/tmp/tika-server.jar"
                if not os.path.exists(tika_server_jar):
                    # Download Tika server jar if not already present
                    subprocess.run([
                        'curl', '-o', tika_server_jar,
                        'http://search.maven.org/remotecontent?filepath=org/apache/tika/tika-server-standard/2.6.0/tika-server-standard-2.6.0.jar'
                    ], check=True)

                # Start Tika server
                subprocess.Popen(['java', '-jar', tika_server_jar], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("Started Tika server.")
            else:
                print("Tika server is already running.")
        except Exception as e:
            print(f"Failed to ensure Tika server is running: {e}")        

    def chunk_text(self, pdf_text: str) -> List[str]:
        text_splitter = CharacterTextSplitter(
            separator="\n",  # Split on newlines
            chunk_size=self.config["maximum_chunk_size"],  # Maximum chunk size
            chunk_overlap=self.config["chunk_overlap"],  # Overlap between chunks
        )
        chunks = text_splitter.split_text(pdf_text)
        return chunks

    def extract_text_from_pdf(self, pdf_path: str, use_tika: bool):
        if use_tika:
            self.ensure_tika_server_running()
            raw = parser.from_file(pdf_path)
            return raw['content']
        reader = PdfReader(pdf_path)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
        return text

    def generate_db(self, documents: List[Document]) -> None:
        if self.faiss_db is None:
            self.faiss_db = FAISS.from_documents(documents, self.embed_tool)
        else:
            self.faiss_db.add_documents(documents)

    def convert_query_to_embeddings(self, query: str) -> List[float]:
        return self.embed_tool.embed_query(query)

    def retrieve_context(self, query_embedded: List[float]) -> str:
        docs = self.faiss_db.similarity_search_by_vector(query_embedded, k=self.config["chunks_to_retrieve"])
        return "\n".join([f"{doc.page_content[:300]}" for doc in docs])

    def process_pdfs(self, pdf_paths: List[str], use_tika, callback) -> bool:
        total_paths = len(pdf_paths)
        try:
            for i, pdf_path in enumerate(pdf_paths):
                pdf_text = self.extract_text_from_pdf(pdf_path, use_tika)
                chunks = self.chunk_text(pdf_text)
                documents = [Document(page_content=chunk) for chunk in chunks]
                self.generate_db(documents)
                percentage = int((i + 1) * 100 / total_paths)
                callback(percentage, text=f"Processed PDF {pdf_path}")
            self.faiss_db.save_local("db")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False
        return True

    def retrieve(self, user_prompt: str) -> str:
        self.faiss_db = FAISS.load_local("db", self.get_embedding_type(), allow_dangerous_deserialization=True)
        query_embedding = self.convert_query_to_embeddings(user_prompt)
        context = self.retrieve_context(query_embedding)
        return context


if __name__ == "__main__":
    # Initialize the OSSRetriever with the embedding tool
    retriever = OSSRetriever()
    
    # List of PDF file paths to process
    data_dir = "/home/azureuser/nim-demo-aks/test_data/"
    pdf_paths = [os.path.join(data_dir, file) for file in os.listdir(data_dir)]

    example_lambda = lambda x,y: print(f"Status: {y} Completed: {x}")
    
    # Process the PDFs to extract text and generate the FAISS database
    success = retriever.process_pdfs(pdf_paths)
    if success:
        print("Successfully processed PDF files and created the FAISS database.")
    else:
        print("Failed to process PDF files.")

    # Example user query
    user_query = "Example query text to retrieve context from the database"
    
    # Retrieve context based on the user query
    context = retriever.retrieve(user_query)
    
    # Print the retrieved context
    print("Retrieved context:")
    print(context)
