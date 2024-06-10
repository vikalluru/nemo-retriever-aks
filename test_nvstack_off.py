import requests
from bs4 import BeautifulSoup
from tika import parser
import openai
import cohere
from pymilvus import (
    connections,
    FieldSchema, CollectionSchema, DataType,
    Collection, utility
)

RESULTS_DIR = "data"
# # Define Milvus connection and collection details
# connections.connect("default", host="localhost", port="19530")

# # Define collection schema
# fields = [
#     FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
#     FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
#     FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536)  # Adjust dimension based on OpenAI model used
# ]
# schema = CollectionSchema(fields, "Document embeddings collection")

# # Create or load collection
# collection_name = "pdf_documents"
# if utility.has_collection(collection_name):
#     collection = Collection(collection_name)
# else:
#     collection = Collection(collection_name, schema)

# # Function to extract text from PDF using Apache Tika
# def extract_text_from_pdf(pdf_path):
#     raw = parser.from_file(pdf_path)
#     return raw['content']

# # Function to get OpenAI embeddings
# def get_openai_embeddings(text, api_key):
#     openai.api_key = api_key
#     response = openai.Embedding.create(
#         input=text,
#         model="text-embedding-ada-002"
#     )
#     return response['data'][0]['embedding']

# # Function to store results in Milvus
# def store_in_milvus(collection, text, embedding):
#     ids = [collection.num_entities]
#     collection.insert([ids, [text], [embedding]])

# Main function to demonstrate the workflow
def main(url, openai_api_key):
    # Get list of PDF URLs
    pdf_urls = get_pdf_urls(url)
    print(pdf_urls)
    
    for i, pdf_url in enumerate(pdf_urls):
        # Download PDF
        pdf_path = f"report_{i}.pdf"
        print(f"Download {pdf_path} from {pdf_url}")
        download_pdf(pdf_url, pdf_path)
        
        # Extract text from PDF
        # text = extract_text_from_pdf(pdf_path)
        # print(f"Extracted Text from {pdf_url[:30]}: {text[:100]}")  # Print first 100 characters of the extracted text
        
        # # Generate OpenAI embeddings
        # embedding = get_openai_embeddings(text, openai_api_key)
        # print(f"Generated Embedding for {pdf_url[:30]}: {embedding[:10]}")  # Print first 10 dimensions of the embedding
        
        # # Store results in Milvus
        # store_in_milvus(collection, text, embedding)

# # Define your API key and webpage URL
openai_api_key = "sk-proj-xDGHifSN2zgIcSGWZRVRT3BlbkFJjjgSx275xvsJtYVC4g3d"
webpage_url = "https://ir.blackrock.com/financials/annual-reports-and-proxy/default.aspx"

# # Run the main function
main(webpage_url, openai_api_key)
