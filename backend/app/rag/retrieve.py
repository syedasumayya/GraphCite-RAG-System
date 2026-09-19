import os
from dotenv import load_dotenv
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from qdrant_client import QdrantClient
from groq import Groq

# Load environment variables
load_dotenv()

print("Initializing models and database...")
# 1. Initialize Embedding Model (must match the one used in ingestion)
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# 2. Connect to Local Qdrant Database
qdrant = QdrantClient(path="qdrant_data")

# 3. Connect to Groq LLM
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def ask_question(question):
    print(f"\n{'='*50}")
    print(f"❓ Question: {question}")
    print('='*50)
    
    # STEP A: Embed the user's question
    query_embedding = embed_model.get_text_embedding(question)
    
    # STEP B: Search Qdrant for the top 3 most relevant chunks
    search_results = qdrant.query_points(
        collection_name="GraphCite",
        query=query_embedding,
        limit=3
    ).points
    
    # STEP C: Extract the text from the results
    context = ""
    for i, result in enumerate(search_results):
        context += f"Chunk {i+1}:\n{result.payload['text']}\n\n"
        
    print("\n[Retrieved Context from PDF]")
    print(context[:500] + "...\n") # Print a small preview of what we found
    
    # STEP D: Construct the RAG Prompt
    # This forces the LLM to ONLY use the provided context.
    prompt = f"""You are a helpful AI assistant. Use the following pieces of context to answer the question at the end. 
    If you don't know the answer, just say you don't know. DO NOT try to make up an answer.
    
    Context:
    {context}
    
    Question: {question}
    Answer:"""
    
    # STEP E: Send to Groq LLM
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )
    
    print("[🤖 AI Answer]")
    print(response.choices[0].message.content)

if __name__ == "__main__":
    # Let's test it with questions based on the document you uploaded!
    ask_question("What is the main topic of this document?")
    ask_question("What is the submission date and file name mentioned?")