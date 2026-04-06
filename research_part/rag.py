from ollama import chat
from sentence_transformers import SentenceTransformer
import chromadb
from prompt import prompt_1, prompt_2, murged_prompt, prompt_orange
#Choose an Embedding Model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def load_document(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

document_text = load_document("dataset_telecom.txt")
#Chunk the Text
def chunk_text(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

chunks = chunk_text(document_text)
#Create Embeddings
embeddings = embedding_model.encode(chunks)

#Store in Vector Database (Chroma)
client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory="./chroma_db",
        anonymized_telemetry=False
    )
)
collection = client.create_collection("my_docs")

for i, chunk in enumerate(chunks):
    collection.add(
        documents=[chunk],
        embeddings=[embeddings[i].tolist()],
        ids=[str(i)]
    )

#Retrieve Relevant Context
query = prompt_orange
query_embedding = embedding_model.encode([query])[0]

results = collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=3
)

retrieved_docs = results["documents"][0]

#Send Context to LLaMA
try:
    with open("emails_output/email_9599.txt", "r", encoding="utf-8") as f: #normal email: 9589, complex email: 9590
        email_content = f.read()
except FileNotFoundError:
    print("emails_output/email_9599.txt not found - please provide an email file.")
    raise

full_prompt = query + "\n\n" + email_content

context = "\n\n".join(retrieved_docs)

augmented_prompt = f"""
You are an assistant. Use the context below to answer the question.

Context:
{context}

Question:
{full_prompt}

Answer:
"""

response = chat(
    model="qwen3:1.7b",
    messages=[{"role": "user", "content": augmented_prompt}]
)

print(response["message"]["content"])