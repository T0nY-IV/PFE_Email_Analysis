import os
import json
import pandas as pd
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ollama import chat
from sentence_transformers import SentenceTransformer
import chromadb
from shared.prompt import prompt_orange
from Ocr_methodes import Ocr_pdf, Ocr_pdf_Init, Ocr_picture

layout = Ocr_pdf_Init()

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
    global embedding_model, client, collection, chunks, embeddings

    try:
        # Load embedding model
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        # Load JSON dataset
        with open("dataset_telecom.json", "r", encoding="utf-8") as f:
            dataset = json.load(f)

        # Extract only email content (input_email field) for chunking
        chunks = [entry["input_email"] for entry in dataset if "input_email" in entry]

        if not chunks:
            raise Exception("No email content found in dataset")

        # Create embeddings from email content
        embeddings = embedding_model.encode(chunks)

        # Setup ChromaDB persistent storage
        persist_dir = "./chroma_db"
        client = chromadb.PersistentClient(path=persist_dir)

        # Delete existing collection if it exists
        try:
            client.delete_collection("my_docs")
        except:
            pass

        # Create new collection
        collection = client.create_collection("my_docs")

        # Add documents with their embeddings and unique IDs
        for i, chunk in enumerate(chunks):
            collection.add(
                documents=[chunk],
                embeddings=[embeddings[i].tolist()],
                ids=[str(i)]
            )

        # Update last UIDs
        last_excel_uid, last_json_uid = update_last_uids()

        return {
            "status": "success",
            "message": f"RAG system initialized with {len(chunks)} email chunks",
            "chunks_count": len(chunks),
            "last_excel_uid": last_excel_uid,
            "last_json_uid": last_json_uid
        }

    except FileNotFoundError:
        raise Exception("Dataset file not found")
    except Exception as e:
        print(f"Initialization error: {str(e)}")
        raise


def analyze(email):
    """Query the RAG system and get response from Ollama"""
    global embedding_model, collection

    try:

        email_content = email.split("/cut/")[0]
        # Check if system is initialized
        if embedding_model is None or collection is None:
            raise Exception("RAG system not initialized. Call /initialize first.")

        # Encode the actual mail content for query (not the prompt template)
        query_embedding = embedding_model.encode([str(email_content)])[0]
        
        # Retrieve relevant context
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=5
        )
        
        documents = results.get("documents")
        if not documents or not documents[0]:
            raise Exception("No documents retrieved from vector store.")
            
        retrieved_docs = documents[0]
        
        #separation of the attachments from the email content
        email_attachments = email.split("/cut/")[1]
        if email_attachments == "":
            attachements = []
        else:
            attachements = email_attachments.split(";")
        email_content += "\n\nAttachments:\n"
        Uid = email_content.split("UID:")[1].split("\n")[0].strip()

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


        # Lecture du contenu de l'email à traiter
        email_content = str(email_content)
        
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
        

