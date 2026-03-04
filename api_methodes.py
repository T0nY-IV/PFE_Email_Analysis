import os
import json

def save_to_dataset(input_email: str, output_data: dict):
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
