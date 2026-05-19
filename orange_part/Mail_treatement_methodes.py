import datetime
import os
import json
import pandas as pd
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ollama import chat
from sentence_transformers import SentenceTransformer
import chromadb
from shared.prompt import prompt_orange
from Ocr_methodes import Ocr_pdf, Ocr_pdf_Init, Ocr_picture
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

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
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder="./models")

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
        if len(email.split("/*MailSender*/")) > 1 and len(email.split("/*MailSub*/")) > 1:    
            email_contentb = email.split("/*MailSender*/")[0] + email.split("/*MailSender*/")[1] + email.split("/*MailSender*/")[2]
            email_contentb = email_contentb.split("/*MailSub*/")[0] + email_contentb.split("/*MailSub*/")[1] + email_contentb.split("/*MailSub*/")[2]
        else:
            email_contentb = email
        email_content = email_contentb.split("/cut/")[0]
        
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
                if att.upper().endswith((".PDF",".TXT")):
                    link_att_pdf = "emails_output/attachments/" + Uid + "/" + att
                    ocr_result = Ocr_pdf(link_att_pdf, layout)
                    email_content += "\n\n" + str(ocr_result)
                elif att.upper().endswith((".JPG", ".JPEG", ".PNG")):
                    link_att_img = "emails_output/images/" + Uid + "/" + att
                    ocr_result = Ocr_picture(link_att_img)
                    email_content += "\n\n" + str(ocr_result)
        else:
            email_content += "None"


        # Ensure email content is a string (in case it's not already)
        email_content = str(email_content)
        print(f"Email content :{email_content}") 
        
        # Create augmented prompt
        # Concaténation du prompt système avec le contenu de l'email
        full_prompt = prompt_orange + "\n\n" + email_content

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
        # Jointure des documents retrouvés pour former le contexte
        context = "\n\n".join(retrieved_docs)
       
        augmented_prompt = f"""
You are an assistant. Use the context below to answer the question.

Context:
{context}

Question:
{full_prompt}

Answer:
"""
        
        # Retry prediction up to 3 times, then fallback to "not analysed"
        max_attempts = 3
        retry_delay = 1
        data_json = "not analysed"
        for attempt in range(0, max_attempts):
            try:
                response = chat(
                    model="llama3.1:latest",
                    messages=[{"role": "user", "content": augmented_prompt}]
                )
                print(response["message"]["content"])
                data_json = json.loads(response["message"]["content"])
                break
            except Exception as retry_error:
                print(f"Prediction attempt {attempt} failed: {retry_error}.")
                if attempt < max_attempts:
                    print("Retrying...")
                    time.sleep(retry_delay)
                else:
                    print("Prediction failed after 3 attempts. Output set to 'not analysed'.")
        
        if len(email.split("/*MailSender*/")) > 1 and len(email.split("/*MailSub*/")) > 1 and data_json != "not analysed":
            sender = email.split("/*MailSender*/")[1]
            subject = email.split("/*MailSub*/")[1]
            try:
                sender_email = os.getenv("mail_@")
                sender_password = os.getenv("mail_code")
    
                if sender_email and sender_password:
                    # Extract and decode the email subject for use in the response
                    email_subject = subject
                    sender_name = sender
                
                    response_msg = MIMEMultipart()
                    response_msg['From'] = sender_email
                    response_msg['To'] = str(sender)
                    response_msg['Subject'] = f"Re: {email_subject}"
        
                    html_body = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <style>
                                .container {{
                                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                                    max-width: 600px;
                                    margin: 0 auto;
                                    background-color: #ffffff;
                                    border-radius: 16px;
                                    overflow: hidden;
                                    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
                                    border: 1px solid #e2e8f0;
                                }}
                                .header {{
                                    background: linear-gradient(135deg, #f97316, #8b5cf6);
                                    padding: 40px 20px;
                                    text-align: center;
                                    color: white;
                                }}
                                .content {{
                                    padding: 40px 30px;
                                    color: #1e293b;
                                    line-height: 1.6;
                                }}
                                .subject-card {{
                                    background-color: #f8fafc;
                                    border-radius: 12px;
                                    padding: 20px;
                                    margin: 24px 0;
                                    border-left: 4px solid #f97316;
                                }}
                                .subject-label {{
                                    color: #64748b;
                                    font-weight: 600;
                                    font-size: 0.75rem;
                                    text-transform: uppercase;
                                    letter-spacing: 0.05em;
                                    margin-bottom: 8px;
                                }}
                                .subject-text {{
                                    color: #0f172a;
                                    font-weight: 700;
                                    font-size: 1rem;
                                }}
                                .footer {{
                                    padding: 30px;
                                    text-align: center;
                                    color: #94a3b8;
                                    font-size: 0.8rem;
                                    background-color: #f8fafc;
                                    border-top: 1px solid #f1f5f9;
                                }}
                            </style>
                        </head>
                        <body style="background-color: #f8fafc; padding: 40px 20px; margin: 0;">
                            <div class="container">
                                <div class="header">
                                    <h1 style="margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.02em;">Orange Analytics</h1>
                                </div>
                                <div class="content">
                                    <h2 style="margin-top: 0; color: #0f172a; font-size: 20px;">Bonjour {sender_name},</h2>
                                    <p style="font-size: 16px; color: #475569;">Suite a votre {data_json['workflow_type']} envoyée par email le {datetime.datetime.now().strftime('%m/%d/%Y')} à {datetime.datetime.now().strftime('%H:%M')}, un ticket d'intervention a été créé et enregistré sous le numéro <b>UID{data_json['email_id']}.<b></p>
        
                                    <div class="subject-card">
                                        <div class="subject-label">Votre Message</div>
                                        <div class="subject-text">{email_subject}</div>
                                    </div>
                                    
                                    <p style="font-size: 14px; color: #64748b;">Notre équipe examine votre {data_json['workflow_type']} et vous répondra dans les meilleurs délais.</p>
                                </div>
                                <div class="footer">
                                    <p style="margin: 0;">&copy; 2026 Orange Analytics &bull; Suite de Sécurité & Analyse</p>
                                    <p style="margin: 4px 0 0 0;">Ceci est un message automatique, merci de ne pas y répondre.</p>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
        
                    response_msg.attach(MIMEText(html_body, 'html'))
        
                    # Using SMTP to send the email (IMAP is for reading/managing)
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                        server.login(sender_email, sender_password)
                        server.send_message(response_msg)
                        print(f"Message sent in response to: {email_subject}")
            except Exception as e:
                print(f"Error sending message email: {str(e)}")
                

        # Sauvegarde du résultat dans le dataset (utile pour le RAG ou l'historique)
        save_to_dataset(email_content, data_json)
        
        # Affichage en console et retour de la réponse à l'utilisateur
        print(data_json)
        return data_json
        
    except Exception as e:
        raise Exception(f"email content error: {str(e)}")
        

