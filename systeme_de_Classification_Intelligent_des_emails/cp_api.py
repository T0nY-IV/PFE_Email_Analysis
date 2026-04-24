#completed project api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ollama import chat
from sentence_transformers import SentenceTransformer
import chromadb
import json
import os
import sys
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Optional
from shared.prompt import get_prompt_configlist, get_json_config
from cp_api_methodes import load_document, chunk_text, save_to_dataset, update_last_uids
from Ocr_methodes import Ocr_pdf_Init, Ocr_pdf, Ocr_picture

app = FastAPI(title="RAG API", description="Retrieval-Augmented Generation API with Ollama")
layout = Ocr_pdf_Init()

# Add CORS middleware 
# Configuration CORS pour autoriser les requêtes provenant de n'importe quelle origine ("*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
# Variables globales pour stocker l'état du système RAG en mémoire
embedding_model = None
client = None
collection = None
document_text = None
chunks = None
embeddings = None
# Variables pour les derniers IDs
last_excel_uid = None
last_json_uid = None



# Modèle de requête pour récupérer le chemin du fichier email
class QueryRequest(BaseModel):
    email_content: Optional[str]


def chunk_json_dataset(data, chunk_size=5):
    """Chunk JSON dataset by grouping entries together for semantic retrieval.

    Each chunk contains a small group of complete JSON entries (input_email + output),
    preserving the JSON structure and meaning.
    """
    chunks = []
    if not isinstance(data, list):
        data = [data]

    for i in range(0, len(data), chunk_size):
        chunk_entries = data[i:i+chunk_size]
        # Create a meaningful text representation for each chunk
        chunk_text = ""
        for entry in chunk_entries:
            if isinstance(entry, dict) and "input_email" in entry and "output" in entry:
                output = entry.get("output", {})
                workflow_label = output.get("workflow_label", output.get("label", "unknown"))
                # Create a semantic representation
                chunk_text += f"Workflow: {workflow_label}\n"
                chunk_text += f"Email sample: {entry['input_email'][:300]}\n"
                chunk_text += "---\n"
        if chunk_text:
            chunks.append(chunk_text)

    return chunks


@app.post("/initialize")
async def initialize():
    """Initialize the RAG system by loading document and creating embeddings"""
    global embedding_model, client, collection, document_text, chunks, embeddings, last_excel_uid, last_json_uid

    try:
        # Load embedding model
        # Chargement du modèle de plongement (embedding) pour vectoriser le texte
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        # Load document
        # Chargement du corpus depuis le fichier JSON
        document_text = json.load(open("full_dataset.json", "r", encoding="utf-8"))

        # Chunk the text - use JSON-aware chunking that preserves structure
        # Découpage du texte en groupes d'entrées JSON complètes (5 entrées par chunk)
        chunks = chunk_json_dataset(document_text, chunk_size=5)

        # Create embeddings
        # Conversion des morceaux de texte en vecteurs
        embeddings = embedding_model.encode(chunks)

        # Définition du répertoire pour la base de données Chroma locale
        persist_dir = "./chroma_db"

        # Store in Vector Database (Chroma)
        # Initialisation du client ChromaDB avec un stockage persistant
        client = chromadb.PersistentClient(path=persist_dir)

        # Delete existing collection if it exists
        # Suppression de l'ancienne collection pour éviter les doublons lors de la réinitialisation
        try:
            client.delete_collection("my_docs")
        except:
            pass

        # Création d'une nouvelle collection vierge
        collection = client.create_collection("my_docs")

        # Ajout des documents, de leurs vecteurs et d'identifiants uniques dans la collection
        for i, chunk in enumerate(chunks):
            collection.add(
                documents=[chunk],
                embeddings=[embeddings[i].tolist()],
                ids=[str(i)]
            )


        # Mettre à jour les derniers UIDs
        last_excel_uid, last_json_uid = update_last_uids()

        # Retourne un message de succès avec des statistiques sur les données chargées
        return {
            "status": "success",
            "message": f"RAG system initialized with {len(chunks)} chunks",
            "chunks_count": len(chunks),
            "document_path": "full_dataset.json",
            "last_excel_uid": last_excel_uid,
            "last_json_uid": last_json_uid
        }

    except FileNotFoundError as e:
        # Gestion de l'erreur si le fichier de données n'est pas trouvé
        raise HTTPException(status_code=404, detail=f"Document not found: full_dataset.json")
    except Exception as e:
        # Gestion des autres erreurs génériques lors de l'initialisation
        raise HTTPException(status_code=500, detail=f"Initialization error: {str(e)}")

def extract_json_from_response(response_text: str) -> dict:
    """Extract valid JSON from LLM response, handling thought blocks and markdown.

    Qwen3 models may output <think>...</think> thought blocks before the actual response.
    This function strips those and extracts the JSON using regex.
    """
    # Step 1: Remove <think>...</think> thought blocks (Qwen3 specific)
    response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL | re.IGNORECASE)

    # Step 2: Remove markdown code blocks if present
    response_text = re.sub(r'```json\s*', '', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'```\s*', '', response_text)

    # Step 3: Find JSON object using regex (handles nested braces)
    # Look for the first { and match to the last }
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Step 4: Try direct parsing as fallback
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from response: {str(e)[:200]}")


@app.post("/query")
async def query(request: QueryRequest):
    """Query the RAG system and get response from Ollama"""
    global embedding_model, collection

    try:
        # Check if system is initialized
        if embedding_model is None or collection is None:
            raise HTTPException(status_code=400, detail="RAG system not initialized. Call /initialize first.")

        # Lecture du contenu de l'email à traiter
        req_content = str(request.email_content)
        email_content = req_content.split("/cut/")[0]
        #separation of the attachments from the email content
        email_attachments = req_content.split("/cut/")[1] if "/cut/" in req_content else ""
        if email_attachments == "":
            attachements = []
        else:
            attachements = email_attachments.split(";")
        email_content += "\n\nAttachments:\n"
        Uid = email_content.split("UID:")[1].split("\n")[0].strip() if "UID:" in email_content else "unknown"

        #attachement processing with OCR if necessary
        if attachements:
            for att in attachements:
                if att.endswith(".pdf"):
                    link_att_pdf = "emails_output/attachments/" + Uid + "/" + att
                    ocr_result = Ocr_pdf(link_att_pdf, layout)
                    email_content += "\n\n" + str(ocr_result)
                elif att.endswith((".jpg", ".jpeg", ".png")):
                    link_att_img = "emails_output/images/" + Uid + "/" + att
                    ocr_result = Ocr_picture(link_att_img)
                    email_content += "\n\n" + str(ocr_result)
        else:
            email_content += "None"

        # Retrieve relevant context using EMAIL CONTENT as query (not the prompt!)
        # This finds similar emails from the dataset to use as few-shot examples
        query_embedding = embedding_model.encode([email_content])[0]

        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=3  # Reduced from 5 to 3 for less noise
        )

        documents = results.get("documents")
        retrieved_docs = documents[0] if documents and documents[0] else []

        # Build the prompt dynamically
        prompt_template = get_prompt_configlist()

        # Create augmented prompt with retrieved context as few-shot examples
        if retrieved_docs:
            context = "\n\n".join(retrieved_docs)
            augmented_prompt = f"""{prompt_template}

Reference examples from similar emails:
{context}

Email to analyze:
{email_content}
"""
        else:
            augmented_prompt = f"{prompt_template}\n\n{email_content}"

        # Get response from Ollama with temperature control for deterministic output
        # Temperature 0.1 for more deterministic JSON output
        # num_predict set high enough for full JSON response
        response = chat(
            model="qwen3:1.7b",
            messages=[{"role": "user", "content": augmented_prompt}],
            options={
                "temperature": 0.1,  # Low temperature for consistent JSON
                "top_p": 0.9,
                "num_predict": 500,  # Max tokens for response
                "stop": ["</s>", "Email:", "Reference"]  # Stop tokens to prevent extra text
            }
        )

        # Extract and parse JSON from response (handles <think> blocks)
        response_content = response["message"]["content"]
        data_json = extract_json_from_response(response_content)

        # Sauvegarde du résultat dans le dataset (utile pour le RAG ou l'historique)
        save_to_dataset(email_content, data_json)

        # Affichage en console et retour de la réponse à l'utilisateur
        print(data_json)
        return data_json

    except HTTPException:
        # Propagation directe des exceptions HTTP déjà gérées
        raise
    except (json.JSONDecodeError, ValueError) as e:
        # Gestion de l'erreur si la réponse du modèle n'est pas un JSON valide
        raise HTTPException(status_code=500, detail=f"Invalid JSON response from model: {str(e)[:200]}")
    except Exception as e:
        # Transformation de toutes les autres erreurs en HTTP 500
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")

@app.get("/health")
async def health():
    """Health check endpoint"""
    # Endpoint utilisé pour vérifier si l'API est en ligne et son état d'initialisation
    return {
        "status": "ok",
        "system_initialized": embedding_model is not None and collection is not None
    }

@app.get("/status")
async def status():
    """Get current system status"""
    # Endpoint de diagnostic pour récupérer les détails de l'état actuel du système
    return {
        "embedding_model_loaded": embedding_model is not None,
        "database_initialized": collection is not None,
        "chunks_count": len(chunks) if chunks else 0,
        "document_loaded": document_text is not None
    }

if __name__ == "__main__":
    import uvicorn
    # Démarrage du serveur Uvicorn en local (127.0.0.1) sur le port 8086
    uvicorn.run(app, host="127.0.0.1", port=8086)
