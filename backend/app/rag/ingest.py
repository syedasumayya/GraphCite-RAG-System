import os
import uuid
from dotenv import load_dotenv
from llama_index.readers.file import PyMuPDFReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# Load environment variables
load_dotenv()

def process_and_store_document(file_path):
    print(f"1. Loading PDF from: {file_path}")
    loader = PyMuPDFReader()
    documents = loader.load_data(file_path=file_path)
    print(f"   Loaded {len(documents)} page(s) from the PDF.\n")

    print("2. Performing Semantic Chunking...")
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    nodes = splitter.get_nodes_from_documents(documents)
    print(f"   Document split into {len(nodes)} chunks (nodes).\n")

    print("3. Initializing Embedding Model...")
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

    print("4. Connecting to Local Qdrant Vector Database...")
    # This will create a folder called 'qdrant_data' to store your vectors locally
    qdrant = QdrantClient(path="qdrant_data")
    
    collection_name = "GraphCite"
    
    # Create a collection if it doesn't exist
    if not qdrant.collection_exists(collection_name):
        qdrant.create_collection(
            collection_name=collection_name,
            # Vector size must match the embedding model (BGE-small is 384)
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"   Created new collection: {collection_name}")
    else:
        print(f"   Collection '{collection_name}' already exists. Adding to it.")

    print("5. Embedding and Storing chunks into Qdrant...")
    points = []
    for i, node in enumerate(nodes):
        # Embed the chunk
        embedding = embed_model.get_text_embedding(node.text)
        
        # Create a point for Qdrant
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "text": node.text,
                "metadata": node.metadata
            }
        )
        points.append(point)

    # Upload all chunks to Qdrant
    qdrant.upsert(collection_name=collection_name, points=points)
    
    print(f"\n=== SUCCESS! Stored {len(points)} chunks into Qdrant. ===")
    print("You can now query this database in Phase 3.")

if __name__ == "__main__":
    pdf_path = "data/sample.pdf"
    if os.path.exists(pdf_path):
        process_and_store_document(pdf_path)
    else:
        print(f"ERROR: Could not find {pdf_path}. Please put a PDF in the data folder.")