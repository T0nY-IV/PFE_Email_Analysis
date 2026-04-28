import json
from typing import List, Any
from mail_analyser import initialize_rag_system, loop_through_emails_and_send_requests
from email_refresher import run_once
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from auth.router import router as auth_router
from auth.dependencies import require_role
from auth.models import User, UserRole

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Backend Methods API", description="API for backend methods and email processing")

# Include auth router
app.include_router(auth_router)

def paginate_list(items: List[Any], page: int, page_size: int) -> dict:
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be positive integers")
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "page": page,
        "page_size": page_size,
        "total": len(items),
        "pages": (len(items) + page_size - 1) // page_size,
        "items": items[start:end],
    }


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PageRequest(BaseModel):
    page: int
    page_size: int = 10



# To initialize, use the base API: http://127.0.0.1:8086/initialize

@app.post("/process-emails")
async def api_process_emails():
    """API endpoint to process emails and send requests to the API"""
    try:
        loop_through_emails_and_send_requests()
        return {"status": "success", "message": "Emails processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing emails: {str(e)}")

@app.post("/fetch-emails")
async def api_fetch_emails():
    """API endpoint to fetch new emails from Gmail"""
    try:
        run_once()
        return {"status": "success", "message": "Emails fetched successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching emails: {str(e)}")

@app.get("/get_reclamations", dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.RESPONSABLE_RECLAMATIONS))])
async def api_get_reclamations(request: PageRequest):
    """API endpoint to get all reclamations"""
    try:
        # Load the dataset
        with open("dataset_telecom.json", "r", encoding="utf-8") as f:
            dataset = json.load(f)
        page = request.page
        page_size = request.page_size
        index = 0
        reclamations = []
        for item in dataset:
            if item.get("output", {}).get("workflow_type") == "Réclamation":
                index += 1
                if index <= (page * page_size) - 1 and index > ((page-1) * page_size) - 1:
                    rec = {"input_email":item.get("input_email"), "output": item.get("output")}
                    reclamations.append(rec)
        
        return {
            "status": "success",
            "count": index,
            "current_page": page,
            "data": reclamations
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving reclamations: {str(e)}")

@app.get("/get_demandes", dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.RESPONSABLE_DEMANDES))])
async def api_get_demandes(request: PageRequest):
    """API endpoint to get all demandes"""
    try:
        # Load the dataset
        with open("dataset_telecom.json", "r", encoding="utf-8") as f:
            dataset = json.load(f)
        
        page = request.page
        page_size = request.page_size
        index = 0
        demandes = []
        for item in dataset:
            if item.get("output", {}).get("workflow_type") == "Demande":
                index += 1
                if index <= (page * page_size) - 1 and index > ((page-1) * page_size) - 1:
                    dem = {"input_email":item.get("input_email"), "output": item.get("output")}
                    demandes.append(dem)
        
        return {
            "status": "success",
            "count": index,
            "current_page": page,
            "data": demandes
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving demandes: {str(e)}")

@app.get("/get_all", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def api_get_all(request: PageRequest):
    """API endpoint to get all items"""
    try:
        # Load the dataset
        with open("dataset_telecom.json", "r", encoding="utf-8") as f:
            dataset = json.load(f)
        
        page = request.page
        page_size = request.page_size
        items = dataset[(page-1)*page_size : page*page_size] if page*page_size < len(dataset) else dataset[(page-1)*page_size:]

        return {
            "status": "success",
            "count": len(dataset),
            "current_page": page,
            "data": items
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving all items: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8087)
