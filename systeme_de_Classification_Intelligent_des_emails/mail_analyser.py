import requests
import pandas as pd
import os
from cp_api_methodes import get_last_json_uid

def send_request_to_api(email_content: str):
    url = "http://localhost:8086/query"
    payload = {
        "email_content": email_content,
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
    
def initialize_rag_system():
    url = "http://localhost:8086/initialize"
    try:
        last_json_uid = get_last_json_uid()
        last_excel_uid = 0  # Placeholder, can be updated to get the actual last Excel UID if needed
        
        response = requests.post(url, json={})
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Initialization failed with status code {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error during initialization: {e}")
        return None


def get_mailContent_from_exel_by_uid(uid):
    """Récupère le contenu d'un email depuis le fichier Excel en utilisant l'UID"""
    try:
        excel_path = "emails_output/emails.xlsx"
        if not os.path.exists(excel_path):
            raise FileNotFoundError("Le fichier Excel n'existe pas.")
        
        df = pd.read_excel(excel_path)
        if 'UID' not in df.columns:
            raise ValueError("La colonne 'UID' est manquante dans le fichier Excel.")
        
        # Rechercher la ligne correspondant à l'UID
        email_row = df[df['UID'] == uid]
        if email_row.empty:
            raise ValueError(f"Aucun email trouvé avec l'UID: {uid}")
        
        # Extraire le contenu de l'email
        email_content = email_row.iloc[0]['Email Content']  # Utiliser la colonne 'Email Content'
        email_attachements = email_row.iloc[0]['Attachments']  # Utiliser la colonne 'Attachments' si nécessaire
        return "UID: " + str(uid) + "\n" + email_content + "/cut/" + str(email_attachements)
    except Exception as e:
        print(f"Erreur lors de la récupération du contenu de l'email: {e}")
        return None
    
def loop_through_emails_and_send_requests():
    """Boucle à travers les emails et envoie des requêtes à l'API pour chaque email"""
    excel_path = "emails_output/emails.xlsx"
    if not os.path.exists(excel_path):
        print("Le fichier Excel n'existe pas.")
        return
    
    last_json_uid = get_last_json_uid()

    df = pd.read_excel(excel_path)
    if 'UID' not in df.columns:
        print("La colonne 'UID' est manquante dans le fichier Excel.")
        return
    
    for uid in df['UID'][df['UID'] > last_json_uid]:
        email_content = get_mailContent_from_exel_by_uid(uid)
        if email_content:
            try:
                response = send_request_to_api(email_content)
                print(f"Réponse pour UID {uid}: {response}")
            except Exception as e:
                print(f"Erreur lors de l'envoi de la requête pour UID {uid}: {e}")