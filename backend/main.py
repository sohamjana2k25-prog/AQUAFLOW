from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Tuple, Dict
from routing_engine import PriorityRoutingEngine
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastAPI App
app = FastAPI(
    title="Priority Routing API",
    description="Engine Architect API for dynamic flood-aware routing.",
    version="1.0.0"
)

# CRITICAL HACKATHON ADDITION: CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# Initialize the Routing Engine
logger.info("Initializing the Priority Routing Engine. Downloading graph data...")
engine = PriorityRoutingEngine(place_name="Salt Lake, Kolkata")
logger.info("Graph loaded successfully. Engine is ready.")

# --- Pydantic Data Models ---

class RouteRequest(BaseModel):
    start: Tuple[float, float]  # [latitude, longitude]
    end: Tuple[float, float]    # [latitude, longitude]
    priority: int               # e.g., 5000 (Ambulance), 1000 (Commuter)

class FloodReport(BaseModel):
    road_id: int
    cost: int                   # 1 (Dry) to 1000 (Impassable)

class FloodUpdateRequest(BaseModel):
    reports: List[FloodReport]


# --- API Endpoints ---

@app.get("/")
def health_check():
    """Simple check to verify the server is running."""
    return {
        "status": "online", 
        "message": "Priority Routing Engine API is active.",
        "nodes": len(engine.graph.nodes),
        "edges": len(engine.graph.edges)
    }

@app.get("/active-floods")
def get_active_floods():
    """
    State Discovery: Scans the Graph for edges with a flood_cost > 1.0.
    This ensures the Live Feed UI matches the Engine's internal math.
    """
    flooded_roads = []
    # Loop through all edges and find those with a cost > 1
    # We use a set to avoid showing the same road multiple times if it has multiple segments
    seen_roads = set()
    
    for u, v, k, data in engine.graph.edges(keys=True, data=True):
        cost = data.get('flood_cost', 1.0)
        osmid = data.get('osmid')
        
        # Handle OSMIDs that might be lists
        primary_id = osmid[0] if isinstance(osmid, list) else osmid
        
        if cost > 1.0 and primary_id not in seen_roads:
            flooded_roads.append({
                "road_id": primary_id,
                "severity": "Impassable" if cost > 500 else "Ankle Deep",
                "cost": cost,
                "location": data.get('name', "Main Road Sector V"),
                "timestamp": "Live" 
            })
            seen_roads.add(primary_id)
            
    return flooded_roads

@app.post("/calculate-route")
def calculate_route(request: RouteRequest):
    """
    Endpoint for Member 1 (Frontend) to request a path.
    """
    logger.info(f"Route requested: Priority {request.priority} from {request.start} to {request.end}")
    
    result = engine.calculate_priority_route(
        start_coords=request.start,
        end_coords=request.end,
        priority_level=request.priority
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
        
    return result

@app.post("/update-flood-data")
def update_flood_data(request: FloodUpdateRequest):
    """
    Endpoint for Member 3 (Nexus) to push new flood data.
    """
    reports_dict = [{"road_id": r.road_id, "cost": r.cost} for r in request.reports]
    engine.update_road_costs(reports_dict)
    
    logger.info(f"Updated dynamic costs for {len(reports_dict)} road segments.")
    return {"status": "success", "message": "Graph weights updated successfully."}