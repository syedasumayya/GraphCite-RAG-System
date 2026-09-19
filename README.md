📑 GraphCite: Advanced RAG System with Source Verification
An enterprise-grade Retrieval-Augmented Generation (RAG) system built for academic and enterprise knowledge management. GraphCite doesn't just retrieve documents—it synthesizes information across complex sources, verifies its own claims with inline citations, and uses a Two-Stage Retrieval pipeline to eliminate hallucinations.

GraphCite Banner

🚀 Key Features
Two-Stage Retrieval: Uses Vector Search (Dense) to fetch 10 chunks, followed by a Cross-Encoder Re-ranker (bge-reranker-base) to score and select the absolute best 3 chunks.
Conversation Memory: Remembers previous questions for natural, follow-up queries.
Multi-Document Support: Upload multiple PDFs and switch between them using the Document History sidebar. The AI filters the database to only search the active document.
Strict Citation Generation: The LLM is forced to output answers with inline citations [1] that link directly to the source text in the UI.
Zero Hallucination: The system is strictly prompted to say "I don't know" if the answer is not in the retrieved context.
🛠️ Tech Stack
Orchestration: LlamaIndex
LLM: Groq (gpt-oss-120b)
Embeddings: HuggingFace (BAAI/bge-small-en-v1.5) - runs locally for free
Re-ranker: Sentence-Transformers Cross-Encoder
Vector Database: Qdrant (Local file mode)
Backend: FastAPI (Python)
Frontend: Next.js (React, TypeScript, TailwindCSS)
🏗️ System Architecture
Ingestion: PDF -> PyMuPDF Parsing -> Semantic Chunking (512 tokens) -> Embedding -> Qdrant Storage.
Retrieval: User Query -> Vector Search (Top 10) -> Cross-Encoder Re-ranking (Top 3).
Generation: Context + System Prompt -> Groq LLM -> Markdown Response with Citations [1].
⚙️ Setup and Installation
Backend
Navigate to the backend folder.
Create a virtual environment: python -m venv venv
Activate it: .\venv\Scripts\Activate.ps1 (Windows) or source venv/bin/activate (Mac/Linux)
Install dependencies: pip install fastapi uvicorn llama-index llama-index-readers-file pymupdf llama-index-embeddings-huggingface sentence-transformers qdrant-client groq python-dotenv python-multipart
Create a .env file and add your Groq API key: GROQ_API_KEY=your_key_here
Run the server: python -m uvicorn app.main:app --reload --port 8000
Frontend
Navigate to the frontend folder.
Install dependencies: npm install
Run the dev server: npm run dev
Open `http://localhost:3000
