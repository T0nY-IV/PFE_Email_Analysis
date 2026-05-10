import json
import asyncio
import re
from datetime import datetime
from typing import List, Any
from email_refresher import start_email_poller, stop_auto_refresh, get_poller_status, auto_refresh
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine, SessionLocal, get_db
from auth.router import router as auth_router
from auth.dependencies import require_role, get_current_user
from auth.models import User, UserRole, ReclamationResolution, DemandeResolution

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
    q: str = ""


class CooldownRequest(BaseModel):
    cooldown_seconds: int = 60


class EmailUIDRequest(BaseModel):
    email_uid: str


class ResolutionCheckResponse(BaseModel):
    email_uid: str
    is_resolved: bool


@app.on_event("startup")
async def startup_event():
    """Start email poller automatically when API starts"""
    start_email_poller()
    print("Email poller started in background thread")


@app.post("/refresh/start")
async def start_email_poller_endpoint(request: CooldownRequest):
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
        q = request.q.lower().strip() if request.q else ""
        
        index = 0
        reclamations = []
        for item in reversed(dataset):
            if item.get("output", {}).get("workflow_type") == "Réclamation":
                # Apply search filter
                if q:
                    output = item.get("output", {})
                    email_content = item.get("input_email", "").lower()
                    attrs = " ".join([str(v) for v in output.get("attributes", {}).values() if v]).lower()
                    combined = f"{output.get('email_id', '')} {email_content} {attrs}"
                    if q not in combined:
                        continue
                
                index += 1
                if index <= (page * page_size) and index > (page - 1) * page_size:
                    rec = {"input_email": item.get("input_email"), "output": item.get("output")}
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
        q = request.q.lower().strip() if request.q else ""
        
        index = 0
        demandes = []
        for item in reversed(dataset):
            if item.get("output", {}).get("workflow_type") == "Demande":
                # Apply search filter
                if q:
                    output = item.get("output", {})
                    email_content = item.get("input_email", "").lower()
                    attrs = " ".join([str(v) for v in output.get("attributes", {}).values() if v]).lower()
                    combined = f"{output.get('email_id', '')} {email_content} {attrs}"
                    if q not in combined:
                        continue
                
                index += 1
                if index <= (page * page_size) and index > (page - 1) * page_size:
                    dem = {"input_email": item.get("input_email"), "output": item.get("output")}
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
        q = request.q.lower().strip() if request.q else ""
        
        filtered_dataset = []
        if q:
            for item in reversed(dataset):
                output = item.get("output", {})
                email_content = item.get("input_email", "").lower()
                attrs = " ".join([str(v) for v in output.get("attributes", {}).values() if v]).lower()
                combined = f"{output.get('email_id', '')} {email_content} {attrs}"
                if q in combined:
                    filtered_dataset.append(item)
        else:
            filtered_dataset = dataset[::-1]

        items = filtered_dataset[(page-1)*page_size : page*page_size]

        return {
            "status": "success",
            "count": len(filtered_dataset),
            "current_page": page,
            "data": items
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving all items: {str(e)}")


@app.get("/stats/monthly", dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.RESPONSABLE_RECLAMATIONS, UserRole.RESPONSABLE_DEMANDES))])
async def get_monthly_stats():
    """Get monthly counts for reclamations and demandes in the current year"""
    try:
        # Load the dataset
        with open("dataset_telecom.json", "r", encoding="utf-8") as f:
            dataset = json.load(f)
        
        current_year = datetime.now().year
        # Group by month (1-12)
        # Result structure: {month: {"reclamation": count, "demande": count}}
        stats = {month: {"reclamation": 0, "demande": 0} for month in range(1, 13)}
        
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        # Regex to extract Date from input_email string
        # Format expected: "Date: Tue, 03 Feb 2026 13:01:13 +0100"
        date_pattern = re.compile(r"Date:\s+.*,\s+(\d{2})\s+(\w{3})\s+(\d{4})")
        
        for item in dataset:
            input_email = item.get("input_email", "")
            workflow_type = item.get("output", {}).get("workflow_type")
            
            if not workflow_type:
                continue
                
            match = date_pattern.search(input_email)
            if match:
                _, mon_str, year = match.groups()
                year = int(year)
                if year == current_year:
                    month = month_map.get(mon_str)
                    if month:
                        if workflow_type == "Réclamation":
                            stats[month]["reclamation"] += 1
                        elif workflow_type == "Demande":
                            stats[month]["demande"] += 1
        
        # Format for frontend: [{month: "Jan", reclamations: X, demandes: Y}, ...]
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        formatted_stats = []
        for m in range(1, 13):
            formatted_stats.append({
                "name": month_names[m-1],
                "Reclamations": stats[m]["reclamation"],
                "Demandes": stats[m]["demande"]
            })
            
        return {
            "status": "success",
            "year": current_year,
            "data": formatted_stats
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating monthly stats: {str(e)}")


# ===================== RECLAMATIONS RESOLUTION ENDPOINTS =====================

@app.post("/reclamations/mark-resolved", dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.RESPONSABLE_RECLAMATIONS))])
async def mark_reclamation_resolved(request: EmailUIDRequest, db = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Mark a reclamation as resolved by storing its UID and the resolver's username"""
    try:
        # Check if already exists
        existing = db.query(ReclamationResolution).filter(
            ReclamationResolution.email_uid == request.email_uid
        ).first()
        
        if existing:
            return {
                "status": "success",
                "message": "Reclamation already marked as resolved",
                "email_uid": request.email_uid,
                "resolved_by": existing.resolved_by
            }
        
        # Create new resolution record
        resolution = ReclamationResolution(email_uid=request.email_uid, resolved_by=current_user.username)
        db.add(resolution)
        db.commit()
        db.refresh(resolution)
        
        return {
            "status": "success",
            "message": "Reclamation marked as resolved",
            "email_uid": request.email_uid,
            "resolved_at": resolution.resolved_at,
            "resolved_by": resolution.resolved_by
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error marking reclamation as resolved: {str(e)}")


@app.delete("/reclamations/mark-unresolved/{email_uid}", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def mark_reclamation_unresolved(email_uid: str, db = Depends(get_db)):
    """Remove a reclamation from resolved list (mark as unresolved)"""
    try:
        resolution = db.query(ReclamationResolution).filter(
            ReclamationResolution.email_uid == email_uid
        ).first()
        
        if not resolution:
            raise HTTPException(status_code=404, detail="Reclamation resolution record not found")
        
        db.delete(resolution)
        db.commit()
        
        return {
            "status": "success",
            "message": "Reclamation marked as unresolved",
            "email_uid": email_uid
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error marking reclamation as unresolved: {str(e)}")


@app.get("/reclamations/is-resolved/{email_uid}")
async def check_reclamation_resolved(email_uid: str, db = Depends(get_db)):
    """Check if a reclamation is resolved"""
    try:
        resolution = db.query(ReclamationResolution).filter(
            ReclamationResolution.email_uid == email_uid
        ).first()
        
        is_resolved = resolution is not None
        
        return {
            "status": "success",
            "email_uid": email_uid,
            "is_resolved": is_resolved,
            "resolved_at": resolution.resolved_at if is_resolved else None,
            "resolved_by": resolution.resolved_by if is_resolved else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking reclamation resolution: {str(e)}")


@app.get("/reclamations/resolved-list")
async def get_resolved_reclamations(db = Depends(get_db)):
    """Get all resolved reclamation data including UIDs and resolvers"""
    try:
        resolutions = db.query(ReclamationResolution).all()
        
        resolved_data = [
            {"email_uid": r.email_uid, "resolved_by": r.resolved_by, "resolved_at": r.resolved_at} 
            for r in resolutions
        ]
        
        return {
            "status": "success",
            "count": len(resolved_data),
            "resolved_list": resolved_data,
            "resolved_uids": [r.email_uid for r in resolutions] # Keep for backward compatibility if needed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving resolved reclamations: {str(e)}")


# ===================== DEMANDES RESOLUTION ENDPOINTS =====================

@app.post("/demandes/mark-resolved", dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.RESPONSABLE_DEMANDES))])
async def mark_demande_resolved(request: EmailUIDRequest, db = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Mark a demande as resolved by storing its UID and the resolver's username"""
    try:
        # Check if already exists
        existing = db.query(DemandeResolution).filter(
            DemandeResolution.email_uid == request.email_uid
        ).first()
        
        if existing:
            return {
                "status": "success",
                "message": "Demande already marked as resolved",
                "email_uid": request.email_uid,
                "resolved_by": existing.resolved_by
            }
        
        # Create new resolution record
        resolution = DemandeResolution(email_uid=request.email_uid, resolved_by=current_user.username)
        db.add(resolution)
        db.commit()
        db.refresh(resolution)
        
        return {
            "status": "success",
            "message": "Demande marked as resolved",
            "email_uid": request.email_uid,
            "resolved_at": resolution.resolved_at,
            "resolved_by": resolution.resolved_by
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error marking demande as resolved: {str(e)}")


@app.delete("/demandes/mark-unresolved/{email_uid}", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def mark_demande_unresolved(email_uid: str, db = Depends(get_db)):
    """Remove a demande from resolved list (mark as unresolved)"""
    try:
        resolution = db.query(DemandeResolution).filter(
            DemandeResolution.email_uid == email_uid
        ).first()
        
        if not resolution:
            raise HTTPException(status_code=404, detail="Demande resolution record not found")
        
        db.delete(resolution)
        db.commit()
        
        return {
            "status": "success",
            "message": "Demande marked as unresolved",
            "email_uid": email_uid
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error marking demande as unresolved: {str(e)}")


@app.get("/demandes/is-resolved/{email_uid}")
async def check_demande_resolved(email_uid: str, db = Depends(get_db)):
    """Check if a demande is resolved"""
    try:
        resolution = db.query(DemandeResolution).filter(
            DemandeResolution.email_uid == email_uid
        ).first()
        
        is_resolved = resolution is not None
        
        return {
            "status": "success",
            "email_uid": email_uid,
            "is_resolved": is_resolved,
            "resolved_at": resolution.resolved_at if is_resolved else None,
            "resolved_by": resolution.resolved_by if is_resolved else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking demande resolution: {str(e)}")


@app.get("/demandes/resolved-list")
async def get_resolved_demandes(db = Depends(get_db)):
    """Get all resolved demande data including UIDs and resolvers"""
    try:
        resolutions = db.query(DemandeResolution).all()
        
        resolved_data = [
            {"email_uid": r.email_uid, "resolved_by": r.resolved_by, "resolved_at": r.resolved_at} 
            for r in resolutions
        ]
        
        return {
            "status": "success",
            "count": len(resolved_data),
            "resolved_list": resolved_data,
            "resolved_uids": [r.email_uid for r in resolutions] # Keep for backward compatibility if needed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving resolved demandes: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8086)
