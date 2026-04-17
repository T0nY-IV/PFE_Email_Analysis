import os
import json
import pandas as pd

def save_to_dataset(input_email, output_data):
    """Append new RAG result to dataset JSON file"""
    
    new_entry = {
        "output": output_data,
        "input_email": input_email
    }

    # If file exists → load existing data
    if os.path.exists("full_dataset.json"):
        with open("full_dataset.json", "r", encoding="utf-8") as f:
            try:
                dataset = json.load(f)
            except json.JSONDecodeError:
                dataset = []
    else:
        dataset = []

    # Append new entry
    dataset.append(new_entry)

    # Save updated dataset
    with open("full_dataset.json", "w", encoding="utf-8") as f:
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
        json_path = "full_dataset.json"
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
