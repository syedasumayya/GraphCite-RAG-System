import os
import uuid
import tempfile
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from llama_index.readers.file import PyMuPDFReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from groq import Groq
from sentence_transformers import CrossEncoder

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="GraphCite API")

# --- CORS SETUP ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---
class ChatRequest(BaseModel):
    question: str
    history: List[dict] = []
    filename: str = None

# --- INITIALIZE MODELS AND DB ---
print("Initializing models and database...")

# 1. Embedding Model
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# 2. Vector Database
qdrant = QdrantClient(path="qdrant_data")

# 3. LLM
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 4. Re-ranker Model
print("Loading Re-ranker Model...")
reranker = CrossEncoder('BAAI/bge-reranker-base')
print("Re-ranker loaded successfully!")

# Ensure Qdrant collection exists
if not qdrant.collection_exists("GraphCite"):
    qdrant.create_collection(
        collection_name="GraphCite",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )

# --- API ENDPOINTS ---

@app.get("/")
def read_root():
    return {"status": "GraphCite API is running!"}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # 1. Read PDF
    loader = PyMuPDFReader()
    documents = loader.load_data(file_path=tmp_path)
    
    # 2. Semantic Chunking
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    nodes = splitter.get_nodes_from_documents(documents)

    # 3. Embed and prepare for Qdrant
    points = []
    for node in nodes:
        embedding = embed_model.get_text_embedding(node.text)
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"text": node.text, "filename": file.filename}
        )
        points.append(point)

    # 4. Upload to Qdrant (We DO NOT delete old ones, so we can switch between them)
    qdrant.upsert(collection_name="GraphCite", points=points)
    os.remove(tmp_path)
    
    return {"message": f"Successfully ingested {len(points)} chunks from {file.filename}."}

@app.post("/ask")
async def ask_question(request: ChatRequest):
    question = request.question
    history = request.history

    # 1. Embed the user's question
    query_embedding = embed_model.get_text_embedding(question)
    
    # 2. Create a filter to ONLY search the active PDF
    query_filter = None
    if request.filename:
        query_filter = Filter(
            must=[FieldCondition(key="filename", match=MatchValue(value=request.filename))]
        )
    
    # 3. Search Qdrant with the filter
    search_results = qdrant.query_points(
        collection_name="GraphCite",
        query=query_embedding,
        query_filter=query_filter,
        limit=10
    ).points

    # 4. Extract text AND filename
    chunk_data = [{"text": res.payload['text'], "filename": res.payload.get('filename', 'Unknown')} for res in search_results]
    chunk_texts = [data["text"] for data in chunk_data]
    
    # 5. RE-RANKING STEP
    pairs = [[question, text] for text in chunk_texts]
    scores = reranker.predict(pairs)
    
    # 6. Sort chunks by their new scores
    scored_chunks = list(zip(chunk_data, scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    
    # 7. Build Context
    context = ""
    citations = []
    for i, (data, score) in enumerate(scored_chunks[:3]):
        context += f"[{i+1}] (Filename: {data['filename']}) {data['text']}\n\n"
        citations.append({
            "id": i+1,
            "text": data['text'],
            "filename": data['filename']
        })

    # 8. Construct Messages with Chat History
    messages = [
        {"role": "system", "content": f"""You are a helpful AI assistant. Use the following context to answer the user's question. 
        If you don't know the answer based on the context, just say you don't know. DO NOT make up an answer.
        
        CRITICAL INSTRUCTION: You MUST cite your sources by putting the bracket number at the very end of your sentence. Example: "The sky is blue [1]." Do NOT add extra characters.
        
        Context:
        {context}"""}
    ]
    
    for msg in history:
        if msg['role'] in ['user', 'assistant']:
            messages.append({"role": msg['role'], "content": msg['content']})
            
    messages.append({"role": "user", "content": question})
    
    # 9. Get LLM Response
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages
    )
    
    return {
        "answer": response.choices[0].message.content,
        "citations": citations
    }