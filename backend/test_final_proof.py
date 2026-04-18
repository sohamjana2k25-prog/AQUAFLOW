from routing_engine import PriorityRoutingEngine
import osmnx as ox

def run_final_proof():
    print("Initializing Engine... (Loading Salt Lake Sector V Grid)")
    engine = PriorityRoutingEngine(place_name="Salt Lake, Kolkata")
    G = engine.graph

    # We need two points with ACTUAL parallel roads
    start = (22.5815, 88.4348) # Technopolis
    end = (22.5740, 88.4335)   # Wipro

    print("\n--- PHASE 1: THE SUNNY DAY ---")
    baseline = engine.calculate_priority_route(start, end, 1000)
    print(f"Normal path: {len(baseline['coordinates'])} steps.")

    print("\n--- PHASE 2: THE FLASH FLOOD ---")
    mid_idx = len(baseline['coordinates']) // 2
    mid_point = baseline['coordinates'][mid_idx]

    u, v, key = ox.distance.nearest_edges(G, mid_point[1], mid_point[0])
    G[u][v][key]['flood_cost'] = 800

    flood_route = engine.calculate_priority_route(start, end, 1000)
    print(f"Detour path length: {len(flood_route['coordinates'])} steps.")

    print("\n--- PHASE 3: THE HERD EFFECT ---")
    detour_nodes = [ox.distance.nearest_nodes(G, lon, lat) for lat, lon in flood_route['coordinates']]
    for i in range(len(detour_nodes)-1):
        n1, n2 = detour_nodes[i], detour_nodes[i+1]
        if G.has_edge(n1, n2):
            for k in G[n1][n2]:
                G[n1][n2][k]['current_load'] = 200  # Massive gridlock

    print("\n--- PHASE 4: SYSTEM-LEVEL SOLUTION ---")
    shopper = engine.calculate_priority_route(start, end, 200)
    ambulance = engine.calculate_priority_route(start, end, 5000)

    print(f"Shopper (Priority 200) path: {len(shopper['coordinates'])} steps.")
    print(f"Ambulance (Priority 5000) path: {len(ambulance['coordinates'])} steps.")

    print("\n--- FINAL ANALYSIS ---")
    if shopper['coordinates'] != ambulance['coordinates']:
        print("✅ SUCCESS: The algorithm successfully split the traffic!")
        print(" -> The Ambulance pushed through the 'Golden Path'.")
        print(" -> The Shopper was rerouted to a parallel block to prevent gridlock.")
    else:
        print("❌ FAILED: The traffic did not split.")

if __name__ == "__main__":
    run_final_proof()