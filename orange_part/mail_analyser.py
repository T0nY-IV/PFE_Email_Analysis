import pandas as pd
import os
from api_methodes import get_last_json_uid, analyze

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
        return "UID: " + str(uid) + "\n" + email_content
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
                response = analyze(email_content)
                print(f"Réponse pour UID {uid}: {response}")
            except Exception as e:
                print(f"Erreur lors de l'envoi de la requête pour UID {uid}: {e}")