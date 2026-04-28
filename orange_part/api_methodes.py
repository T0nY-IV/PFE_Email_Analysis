import os
import json
import pandas as pd
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ollama import chat
from sentence_transformers import SentenceTransformer
import chromadb
from shared.prompt import prompt_orange

def save_to_dataset(input_email, output_data):
    """Append new RAG result to dataset JSON file"""
    
    new_entry = {
        "input_email": input_email,
        "output": output_data
    }

    # If file exists → load existing data
    if os.path.exists("dataset_telecom.json"):
        with open("dataset_telecom.json", "r", encoding="utf-8") as f:
            try:
                dataset = json.load(f)
            except json.JSONDecodeError:
                dataset = []
    else:
        dataset = []

    # Append new entry
    dataset.append(new_entry)

    # Save updated dataset
    with open("dataset_telecom.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)


def load_document(path):
    """Load document from file"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def chunk_text(text, chunk_size=500):
    """Split text into chunks"""
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


def get_last_excel_uid():
    """Récupère le dernier UID depuis le fichier Excel"""
    try:
        excel_path = "emails_output/emails.xlsx"
        if not os.path.exists(excel_path):
            return None
        
        df = pd.read_excel(excel_path, engine="openpyxl")
        if 'UID' not in df.columns:
            return None
        
        last_excel_uid = int(df['UID'].max())
        return last_excel_uid
    except Exception as e:
        print(f"Erreur lors de la récupération du dernier UID Excel: {e}")
        return None

def get_last_json_uid():
    """Récupère le dernier UID depuis le fichier JSON"""
    try:
        json_path = "dataset_telecom.json"
        if not os.path.exists(json_path):
            return None
        
        with open(json_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)
        
        if not dataset:
            return None
        
        # Récupérer le dernier objet
        last_entry = dataset[-1]
        
        # Extraire l'email_id depuis l'output
        if "output" in last_entry and "email_id" in last_entry["output"]:
            last_json_uid = int(last_entry["output"]["email_id"])
            return last_json_uid
        
        return None
    except Exception as e:
        print(f"Erreur lors de la récupération du dernier UID JSON: {e}")
        return None

def update_last_uids():
    """Met à jour les variables globales des derniers UIDs"""
    last_excel_uid = get_last_excel_uid()
    last_json_uid = get_last_json_uid()
    return last_excel_uid, last_json_uid


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



def initialize():
    """Initialize the RAG system by loading document and creating embeddings"""
    global embedding_model, client, collection, document_text, chunks, embeddings
    
    try:
        # Load embedding model
        # Chargement du modèle de plongement (embedding) pour vectoriser le texte
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Load document
        # Chargement du corpus depuis le fichier JSON
        document_text = json.load(open("dataset_telecom.json", "r", encoding="utf-8"))
        
        # Chunk the text
        # Découpage du texte en petits morceaux (chunks) de 500 caractères/mots
        chunks = chunk_text(str(document_text), 500)
        
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
            "document_path": "dataset_telecom.json",
            "last_excel_uid": last_excel_uid,
            "last_json_uid": last_json_uid
        }
    
    except FileNotFoundError as e:
        # Gestion de l'erreur si le fichier de données n'est pas trouvé
        raise Exception("Dataset file not found")
    except Exception as e:
        # Gestion des autres erreurs génériques lors de l'initialisation
        print(f"Initialization error: {str(e)}")


def analyze(mail_content):
    """Query the RAG system and get response from Ollama"""
    global embedding_model, collection
    
    try:
        # Check if system is initialized
        if embedding_model is None or collection is None:
            raise Exception("RAG system not initialized. Call /initialize first.")

        # Conversion de notre prompt spécifique en vecteur pour la recherche
        query_embedding = embedding_model.encode([prompt_orange])[0]
        
        # Retrieve relevant context
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=5
        )
        
        documents = results.get("documents")
        if not documents or not documents[0]:
            raise Exception("No documents retrieved from vector store.")
            
        retrieved_docs = documents[0]
        
        # Lecture du contenu de l'email à traiter
        email_content = str(mail_content)
        
        # Create augmented prompt
        # Concaténation du prompt système avec le contenu de l'email
        full_prompt = prompt_orange + "\n\n" + email_content
        
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
        
    except Exception as e:
        # Transformation de toutes les autres erreurs en HTTP 500
        raise Exception(f"email content error: {str(e)}")
        

