import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import requests
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Flood Alert System - Role 3 Backend")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Weather API credentials
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

# City sectors with average elevation (example for Kolkata area)
# You can expand this with more sectors
CITY_SECTORS = {
    "salt_lake": {"lat": 22.5726, "lng": 88.4041, "elevation": 5, "name": "Salt Lake"},
    "new_town": {"lat": 22.5850, "lng": 88.4150, "elevation": 7, "name": "New Town"},
    "south_kolkata": {"lat": 22.5283, "lng": 88.3617, "elevation": 4, "name": "South Kolkata"},
    "north_kolkata": {"lat": 22.6345, "lng": 88.3639, "elevation": 6, "name": "North Kolkata"},
    "central": {"lat": 22.5669, "lng": 88.3704, "elevation": 5, "name": "Central"},
}

# Risk level thresholds
RISK_THRESHOLDS = {
    "low": 0.5,
    "moderate": 1.5,
    "high": 3.0
}

# ============================================================
# PHASE 1: PREDICTIVE RAINFALL ENGINE
# ============================================================

async def get_rainfall_data(lat: float, lng: float) -> dict:
    """
    Fetch rainfall data from OpenWeatherMap One Call API
    Returns: rainfall intensity in mm/hr
    """
    try:
        url = f"https://api.openweathermap.org/data/3.0/onecall"
        params = {
            "lat": lat,
            "lon": lng,
            "appid": OPENWEATHERMAP_API_KEY,
            "exclude": "alerts"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            data = response.json()
            
            # Extract rainfall data
            rainfall_mm_hr = 0
            
            # Check for rain in current conditions
            if "current" in data and "rain" in data["current"]:
                rainfall_mm_hr = data["current"]["rain"].get("1h", 0)
            
            # Check minutely data for more precise prediction
            if "minutely" in data and len(data["minutely"]) > 0:
                next_hour_rainfall = data["minutely"][0].get("precipitation", 0)
                rainfall_mm_hr = max(rainfall_mm_hr, next_hour_rainfall)
            
            return {
                "rainfall_mm_hr": rainfall_mm_hr,
                "timestamp": datetime.utcnow().isoformat(),
                "conditions": data.get("current", {}).get("weather", [{}])[0].get("main", "Unknown")
            }
    except Exception as e:
        logger.error(f"Error fetching rainfall data: {e}")
        return {"rainfall_mm_hr": 0, "timestamp": datetime.utcnow().isoformat(), "error": str(e)}

def calculate_risk_level(rainfall_mm_hr: float, elevation: int) -> dict:
    """
    Calculate predicted risk level using the formula:
    Rp = Rainfall Intensity (mm/hr) / Sector Elevation (m)
    """
    if elevation == 0:
        elevation = 1  # Avoid division by zero
    
    risk_percentage = (rainfall_mm_hr / elevation)
    
    # Determine risk level
    if risk_percentage > RISK_THRESHOLDS["high"]:
        risk_level = "high"
        risk_score = 3
    elif risk_percentage > RISK_THRESHOLDS["moderate"]:
        risk_level = "moderate"
        risk_score = 2
    elif risk_percentage > RISK_THRESHOLDS["low"]:
        risk_level = "low"
        risk_score = 1
    else:
        risk_level = "safe"
        risk_score = 0
    
    return {
        "risk_percentage": round(risk_percentage, 2),
        "risk_level": risk_level,
        "risk_score": risk_score
    }

async def update_sector_risks():
    """
    Background task: Poll weather data and update sector risk levels
    Runs every 5 minutes
    """
    while True:
        try:
            logger.info("Starting sector risk update...")
            
            for sector_id, sector_data in CITY_SECTORS.items():
                # Get rainfall data
                rainfall_info = await get_rainfall_data(sector_data["lat"], sector_data["lng"])
                rainfall_mm_hr = rainfall_info.get("rainfall_mm_hr", 0)
                
                # Calculate risk
                risk_info = calculate_risk_level(rainfall_mm_hr, sector_data["elevation"])
                
                # Update Supabase
                supabase.table("city_sectors").update({
                    "rainfall_mm_hr": rainfall_mm_hr,
                    "risk_level": risk_info["risk_level"],
                    "risk_score": risk_info["risk_score"],
                    "risk_percentage": risk_info["risk_percentage"],
                    "last_updated": datetime.utcnow().isoformat()
                }).eq("sector_id", sector_id).execute()
                
                logger.info(f"Updated {sector_data['name']}: {risk_info['risk_level']} risk (Score: {risk_info['risk_score']})")
            
            # Wait 5 minutes before next update
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Error in sector risk update: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on app startup"""
    logger.info("Starting background tasks...")
    asyncio.create_task(update_sector_risks())

@app.get("/sectors/risk")
async def get_sector_risks():
    """
    GET endpoint to retrieve all sector risk levels
    Used by Member 1 for the heatmap visualization
    """
    try:
        response = supabase.table("city_sectors").select("*").execute()
        sectors = response.data if response.data else []
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "sectors": sectors
        }
    except Exception as e:
        logger.error(f"Error fetching sector risks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# PHASE 2: CROWDSOURCED VALIDATION API
# ============================================================

@app.post("/report")
async def submit_flood_report(
    latitude: float = Form(...),
    longitude: float = Form(...),
    water_depth: int = Form(...),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    POST endpoint to receive flood reports from users
    Accepts: GPS coordinates, water depth (1-5), optional photo
    """
    try:
        image_url = None
        
        # Upload image to Supabase Storage if provided
        if file:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/{timestamp}_{file.filename}"
            
            file_content = await file.read()
            supabase.storage.from_("flood-reports").upload(
                filename,
                file_content,
                {"content-type": file.content_type}
            )
            
            # Get public URL
            image_url = supabase.storage.from_("flood-reports").get_public_url(filename)
        
        # Insert report into database
        report_data = {
            "latitude": latitude,
            "longitude": longitude,
            "water_depth": water_depth,
            "description": description,
            "image_url": image_url,
            "timestamp": datetime.utcnow().isoformat(),
            "verified": False
        }
        
        result = supabase.table("user_reports").insert(report_data).execute()
        report_id = result.data[0]["id"] if result.data else None
        
        # Trigger consensus algorithm
        await check_consensus_and_update_roads(latitude, longitude)
        
        return {
            "status": "success",
            "message": "Report submitted successfully",
            "report_id": report_id,
            "image_url": image_url
        }
    except Exception as e:
        logger.error(f"Error submitting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def check_consensus_and_update_roads(latitude: float, longitude: float):
    """
    Consensus Algorithm:
    - A road segment's cost only increases if there are ≥3 reports 
      within a 100-meter radius in the last 60 minutes
    """
    try:
        # Query for nearby reports in the last 60 minutes
        time_threshold = (datetime.utcnow() - timedelta(minutes=60)).isoformat()
        
        # Use PostGIS ST_DWithin function to find nearby reports
        nearby_reports = supabase.rpc(
            "get_nearby_reports",
            {
                "lat": latitude,
                "lng": longitude,
                "radius_m": 100,
                "time_threshold": time_threshold
            }
        ).execute()
        
        report_count = len(nearby_reports.data) if nearby_reports.data else 0
        
        logger.info(f"Found {report_count} reports within 100m radius")
        
        # If threshold met, update road segments
        if report_count >= 3:
            # Find the nearest road segment
            nearest_road = supabase.rpc(
                "get_nearest_road",
                {"lat": latitude, "lng": longitude}
            ).execute()
            
            if nearest_road.data and len(nearest_road.data) > 0:
                road_id = nearest_road.data[0]["id"]
                
                # Update road cost (multiply by flood factor)
                supabase.table("road_segments").update({
                    "current_cost": 500,  # High cost for flooded road
                    "is_flooded": True,
                    "last_flooded": datetime.utcnow().isoformat()
                }).eq("id", road_id).execute()
                
                logger.info(f"Road {road_id} marked as flooded (consensus reached)")
    except Exception as e:
        logger.error(f"Error in consensus check: {e}")

# ============================================================
# SERVE LIVE COSTS TO MEMBER 2 (ROUTING ENGINE)
# ============================================================

@app.get("/live-costs")
async def get_live_road_costs():
    """
    GET endpoint that returns current road costs
    Used by Member 2's routing algorithm
    Format: [{"road_id": 101, "cost": 500}, ...]
    """
    try:
        response = supabase.table("road_segments").select("id, current_cost").execute()
        
        costs = [
            {"road_id": road["id"], "cost": road["current_cost"]}
            for road in (response.data or [])
        ]
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "roads": costs
        }
    except Exception as e:
        logger.error(f"Error fetching live costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ADMIN GALLERY ENDPOINT (FOR DEMO)
# ============================================================

@app.get("/admin/gallery")
async def get_report_gallery(limit: int = 10):
    """
    Admin endpoint to view recent flood reports
    Shows: photo URL, timestamp, GPS location, water depth
    Perfect for the hackathon demo/pitch
    """
    try:
        response = supabase.table("user_reports")\
            .select("*")\
            .order("timestamp", desc=True)\
            .limit(limit)\
            .execute()
        
        reports = response.data or []
        
        return {
            "status": "success",
            "count": len(reports),
            "reports": [
                {
                    "id": r["id"],
                    "image_url": r.get("image_url"),
                    "timestamp": r.get("timestamp"),
                    "latitude": r.get("latitude"),
                    "longitude": r.get("longitude"),
                    "water_depth": r.get("water_depth"),
                    "description": r.get("description")
                }
                for r in reports if r.get("image_url")
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching gallery: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# HEALTH CHECK & DEBUG ENDPOINTS
# ============================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/debug/sectors")
async def debug_sectors():
    """Debug endpoint to see all configured sectors"""
    return {
        "sectors": CITY_SECTORS,
        "thresholds": RISK_THRESHOLDS
    }

@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "service": "Flood Alert System - Role 3 Backend",
        "version": "1.0.0",
        "endpoints": {
            "POST /report": "Submit a flood report with optional photo",
            "GET /live-costs": "Get current road costs (for Member 2)",
            "GET /sectors/risk": "Get all sector risk levels (for Member 1)",
            "GET /admin/gallery": "View recent flood reports with photos",
            "GET /health": "Health check",
            "GET /debug/sectors": "Debug sector configuration"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
