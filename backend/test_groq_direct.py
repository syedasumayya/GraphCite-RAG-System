import os
from dotenv import load_dotenv
from groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Load the API key from .env
load_dotenv()

print("1. Loading local HuggingFace Embedding model...")
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
print("   Embedding model loaded successfully!\n")

print("2. Connecting to Groq LLM...")
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

print("3. Asking Groq a question...")
try:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "What is a RAG system in AI? Explain in one sentence.",
            }
        ],
        model="openai/gpt-oss-120b",  # The working model from your list
    )
    print("\nResponse from Groq:")
    print(chat_completion.choices[0].message.content)

    # Test embedding
    text = "RAG is cool"
    embedding = embed_model.get_text_embedding(text)
    print(f"\n4. Embedding test successful! Vector size: {len(embedding)}")
    print("\n=== PHASE 1 COMPLETE ===")
    
except Exception as e:
    print("\nERROR CAUGHT:")
    print(e)