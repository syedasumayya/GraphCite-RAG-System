# 📑 GraphCite: Advanced RAG System with Source Verification

An enterprise-grade Retrieval-Augmented Generation (RAG) system built for academic and enterprise knowledge management. GraphCite synthesizes information across complex sources, verifies claims with inline citations, and uses a Two-Stage Retrieval pipeline to reduce hallucinations.



## 🚀 Key Features

- **Two-Stage Retrieval:** Vector Search fetches 10 chunks, followed by a Cross-Encoder Re-ranker (`bge-reranker-base`) to select the best 3 chunks.
- **Conversation Memory:** Remembers previous questions for natural follow-up queries.
- **Multi-Document Support:** Upload multiple PDFs and switch between them using the Document History sidebar.
- **Strict Citation Generation:** Generates inline citations `[1]` linked directly to the source text.
- **Hallucination Control:** The system is instructed to respond with `"I don't know"` when the answer is not available in the retrieved context.

## 🛠️ Tech Stack

- **Orchestration:** LlamaIndex
- **LLM:** Groq (`gpt-oss-120b`)
- **Embeddings:** HuggingFace (`BAAI/bge-small-en-v1.5`)
- **Re-ranker:** Sentence-Transformers Cross-Encoder
- **Vector Database:** Qdrant (Local File Mode)
- **Backend:** FastAPI (Python)
- **Frontend:** Next.js, React, TypeScript, TailwindCSS

## 🏗️ System Architecture

**Ingestion:**

`PDF → PyMuPDF Parsing → Semantic Chunking (512 tokens) → Embedding → Qdrant Storage`

**Retrieval:**

`User Query → Vector Search (Top 10) → Cross-Encoder Re-ranking (Top 3)`

**Generation:**

`Context + System Prompt → Groq LLM → Markdown Response with Citations [1]`



