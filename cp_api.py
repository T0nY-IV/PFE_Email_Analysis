#completed project api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ollama import chat
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import os
import json
import pandas as pd
from typing import Optional
from prompt import prompt_configlist
from orange_part.api_methodes import load_document, chunk_text, save_to_dataset, update_last_uids

app = FastAPI(title="RAG API", description="Retrieval-Augmented Generation API with Ollama")

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


@app.post("/initialize")
async def initialize():
    """Initialize the RAG system by loading document and creating embeddings"""
    global embedding_model, client, collection, document_text, chunks, embeddings
    
    try:
        # Load embedding model
        # Chargement du modèle de plongement (embedding) pour vectoriser le texte
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Load document
        # Chargement du corpus depuis le fichier JSON
        document_text = load_document("config-list-final.json")
        
        # Chunk the text
        # Découpage du texte en petits morceaux (chunks) de 500 caractères/mots
        chunks = chunk_text(document_text, 500)
        
        # Create embeddings
        # Conversion des morceaux de texte en vecteurs
        embeddings = embedding_model.encode(chunks)
        
        # Définition du répertoire pour la base de données Chroma locale
        persist_dir = "./chroma_db"
        
        # Store in Vector Database (Chroma)
        # Initialisation du client ChromaDB avec un stockage persistant
        client = chromadb.Client(
            Settings(
                persist_directory=persist_dir,
                anonymized_telemetry=False
            )
        )
        
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
            "document_path": "dataset_telecom.json",
            "last_excel_uid": last_excel_uid,
            "last_json_uid": last_json_uid
        }
    
    except FileNotFoundError as e:
        # Gestion de l'erreur si le fichier de données n'est pas trouvé
        raise HTTPException(status_code=404, detail=f"Document not found: dataset_telecom.json")
    except Exception as e:
        # Gestion des autres erreurs génériques lors de l'initialisation
        raise HTTPException(status_code=500, detail=f"Initialization error: {str(e)}")

@app.post("/query")
async def query(request: QueryRequest):
    """Query the RAG system and get response from Ollama"""
    global embedding_model, collection
    
    try:
        # Check if system is initialized
        if embedding_model is None or collection is None:
            raise HTTPException(status_code=400, detail="RAG system not initialized. Call /initialize first.")

        # Conversion de notre prompt spécifique en vecteur pour la recherche
        query_embedding = embedding_model.encode([prompt_configlist])[0]
        
        # Retrieve relevant context
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=5
        )
        
        documents = results.get("documents")
        if not documents or not documents[0]:
            raise HTTPException(status_code=404, detail="No documents retrieved from vector store.")
        retrieved_docs = documents[0]
        
        # Lecture du contenu de l'email à traiter
        email_content = str(request.email_content)
        
        # Create augmented prompt
        # Concaténation du prompt système avec le contenu de l'email
        full_prompt = prompt_configlist + "\n\n" + email_content
        
        # Jointure des documents retrouvés pour former le contexte
        context = "\n\n".join(retrieved_docs)
        
        # Construction du prompt final (Augmented Prompt) à envoyer au modèle LLM
        augmented_prompt = f"""
You are an assistant. Use the context below to answer the question.

Context:
{context}

Question:
{full_prompt}

Answer:
"""
        
        # Get response from Ollama
        # Génération de la réponse via le modèle LLM local (Ollama)
        response = chat(
            model="qwen3:1.7b",
            messages=[{"role": "user", "content": augmented_prompt}]
        )
        
        # Extraction et conversion de la réponse JSON retournée par le modèle
        data_json = json.loads(response["message"]["content"])
        
        # Sauvegarde du résultat dans le dataset (utile pour le RAG ou l'historique)
        save_to_dataset(email_content, data_json)
        
        # Affichage en console et retour de la réponse à l'utilisateur
        print(data_json)
        return data_json
        
        # Lignes commentées d'origine gardées intactes
        #return {
        #    #"status": "success",
        #    #"query": augmented_prompt,
        #    #"retrieved_context": retrieved_docs,
        #    "response": response["message"]["content"],
        #    #"email_content": request.email_content
        #}
    
    except HTTPException:
        # Propagation directe des exceptions HTTP déjà gérées
        raise
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
