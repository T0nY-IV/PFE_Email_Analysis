import json
import asyncio
from typing import List, Any
from email_refresher import start_email_poller, stop_auto_refresh, get_poller_status, auto_refresh
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
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


class CooldownRequest(BaseModel):
    cooldown_seconds: int = 60


@app.on_event("startup")
async def startup_event():
    """Start email poller automatically when API starts"""
    start_email_poller()
    print("Email poller started in background thread")


@app.post("/refresh/start")
async def start_email_poller_endpoint(request: CooldownRequest = None):
    """Start or restart the email poller with optional new cooldown time"""
    try:
        cooldown = request.cooldown_seconds if request else None
        start_email_poller(cooldown)
        return {
            "status": "success",
            "message": "Email poller started",
            "poll_interval_seconds": cooldown
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting poller: {str(e)}")


@app.post("/refresh/stop")
async def stop_email_poller_endpoint():
    """Stop the email poller gracefully"""
    try:
        stop_auto_refresh()
        return {"status": "success", "message": "Email poller stopping..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping poller: {str(e)}")


@app.get("/refresh/status")
async def get_poller_status_endpoint():
    """Get the current status of the email poller"""
    try:
        status = get_poller_status()
        return {"status": "success", **status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@app.post("/refresh/once")
async def fetch_emails_once():
    """Fetch emails once immediately (non-blocking, runs in background thread)"""
    try:
        await asyncio.to_thread(auto_refresh, cooldown_seconds=None)
        return {"status": "success", "message": "Emails fetched successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching emails: {str(e)}")

@app.get("/get_reclamations", dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.RESPONSABLE_RECLAMATIONS))])
async def api_get_reclamations(request: PageRequest = Depends()):
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
async def api_get_demandes(request: PageRequest = Depends()):
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
async def api_get_all(request: PageRequest = Depends()):
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
    uvicorn.run(app, host="127.0.0.1", port=8086)
