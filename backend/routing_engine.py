import osmnx as ox
import networkx as nx
import logging
from typing import List, Tuple, Dict

# Setup logging for the engine
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriorityRoutingEngine:
    def __init__(self, place_name: str = "Salt Lake, Kolkata"):
        """
        Initializes the Engine Architect's core data structure.
        Converts the city into a MultiDiGraph G=(V,E).
        """
        self.place_name = place_name
        
        # Download the graph. Modern OSMnx versions automatically handle topological 
        # simplification during the fetch process, preventing memory overhead.
        self.graph = ox.graph_from_place(place_name, network_type='drive')
        
        # Initialize every edge with base 'length', 'flood_cost', and 'load'
        for u, v, k, data in self.graph.edges(keys=True, data=True):
            data['flood_cost'] = 1.0  # 1.0 = Dry (Baseline)
            data['current_load'] = 0  # Global Load Counter 
            data['capacity'] = 50     # Threshold for load balancing 

    def custom_weight_function(self, u, v, edge_data, priority_level) -> float:
        """
        The Multi-Objective Cost Function logic.
        Formula: W(e, u) = L(e) * C(e) * P(u, e).
        """
        length = edge_data.get('length', 1.0)
        flood_cost = edge_data.get('flood_cost', 1.0)
        current_load = edge_data.get('current_load', 0)
        capacity = edge_data.get('capacity', 50)
        
        # Base priority mapping for congestion
        priority_multiplier = 1000.0 / priority_level

        # --- THE FIX: PRIORITY-BASED FLOOD PENALTY ---
        # If the road is dry (1.0), it does nothing.
        # If the road is wet (>1.0), the penalty scales drastically based on who is asking.
        if flood_cost > 1.0:
            if priority_level >= 5000:
                # Emergency: Ignores 90% of the flood penalty to find the shortest physical path.
                effective_flood_cost = flood_cost * 0.1 
            elif priority_level <= 500:
                # Hangout/Leisure: Has ZERO tolerance for water. Multiplies penalty by 20x to force a detour.
                effective_flood_cost = flood_cost * 20.0 
            else:
                # Commuter: Standard penalty (tries to avoid, but will cross if detour is too long)
                effective_flood_cost = flood_cost * 2.0
        else:
            effective_flood_cost = 1.0

        # Load Balancing: Dynamic Exponential Scaling
        load_penalty = 1.0
        if current_load > capacity:
            # The Siren Override: Absolute immunity for Emergency vehicles
            if priority_level >= 5000:
                load_penalty = 1.0
            else:
                overload_ratio = current_load / capacity
                congestion_factor = overload_ratio ** 2 
                load_penalty = 1.0 + (congestion_factor * priority_multiplier)
            
        return length * effective_flood_cost * load_penalty

    def calculate_priority_route(self, start_coords: Tuple[float, float], 
                                  end_coords: Tuple[float, float], 
                                  priority_level: int) -> Dict:
        """
        Calculates the path using Dijkstra's algorithm with the 
        custom cost function.
        """
        # 1. Snap GPS coordinates to the nearest graph nodes
        start_node = ox.distance.nearest_nodes(self.graph, start_coords[1], start_coords[0])
        end_node = ox.distance.nearest_nodes(self.graph, end_coords[1], end_coords[0])

        # 2. Calculate path with custom edge weights
        try:
            route_nodes = nx.shortest_path(
                self.graph, 
                source=start_node, 
                target=end_node, 
                # Pass priority_level directly into the weight evaluation
                weight=lambda u, v, d: self.custom_weight_function(u, v, d, priority_level)
            )

            # 3. Transform Node IDs back to GPS coordinates and calculate physical metrics
            route_coords = []
            total_length_meters = 0
            total_cost_score = 0
            
            for i in range(len(route_nodes)):
                node = route_nodes[i]
                node_data = self.graph.nodes[node]
                route_coords.append([node_data['y'], node_data['x']])
                
                # Calculate real distance and cost for the edges between nodes
                if i < len(route_nodes) - 1:
                    next_node = route_nodes[i+1]
                    # Get edge data (using [0] as OSMnx MultiDiGraphs can have multiple parallel edges)
                    edge_data = self.graph[node][next_node][0]
                    total_length_meters += edge_data.get('length', 10.0)
                    total_cost_score += self.custom_weight_function(node, next_node, edge_data, priority_level)

            # Convert to kilometers
            distance_km = round(total_length_meters / 1000, 2)
            
            # Dynamic speed based on priority: Ambulance goes ~45km/h (750m/m), Commuter goes ~24km/h (400m/m)
            speed_meters_per_minute = 750 if priority_level >= 5000 else 400
            duration_min = max(1, round(total_length_meters / speed_meters_per_minute))

            return {
                "status": "success",
                "priority_used": priority_level,
                "coordinates": route_coords,
                "distance": distance_km,
                "duration": duration_min,
                "costScore": round(total_cost_score / 100) # Scaled down for UI readability
            }
        except nx.NetworkXNoPath:
            return {"status": "error", "message": "No safe route found."}

    def update_road_costs(self, flood_reports: List[Dict]):
        """
        Updates the graph edges based on validated flood data from Member 3.
        """
        for report in flood_reports:
            road_id = report['road_id']
            new_cost = report['cost'] 
            
            segments_flooded = 0
            for u, v, k, data in self.graph.edges(keys=True, data=True):
                osmids = data.get('osmid')
                
                # OSM IDs can sometimes be a list if roads merge, or a single integer
                is_match = False
                if isinstance(osmids, list) and road_id in osmids:
                    is_match = True
                elif osmids == road_id:
                    is_match = True
                    
                if is_match:
                    data['flood_cost'] = new_cost
                    segments_flooded += 1
                    
            print(f"🚨 ALERT: Successfully flooded {segments_flooded} road segments for OSM ID {road_id}!")

# Manual Test block
if __name__ == "__main__":
    engine = PriorityRoutingEngine()
    # Sample Test: Salt Lake Sector V to City Centre
    test_route = engine.calculate_priority_route(
        start_coords=(22.5735, 88.4331), 
        end_coords=(22.5857, 88.4147), 
        priority_level=5000 # Emergency
    )
    print(f"Calculated route with {len(test_route['coordinates'])} points.")