import json
with open("dataset_telecom.json", "r", encoding="utf-8") as f:
    dataset = json.load(f)
page = 2
page_size = 20
index = 0
reclamations = []
for item in dataset:
    if item.get("output", {}).get("workflow_type") == "Réclamation":
        index += 1
        if index <= (page * page_size) - 1 and index > ((page-1) * page_size) - 1:
            rec = {"input_email":item.get("input_email"), "output": item.get("output")}
            reclamations.append(rec)
            if index == 39:
                print(rec)
