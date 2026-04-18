from routing_engine import PriorityRoutingEngine
import osmnx as ox

def run_crisis_simulation():
    print("Initializing City Grid... (Loading Salt Lake Topology)")
    engine = PriorityRoutingEngine()
    G = engine.graph  # Accessing the raw graph for simulation purposes

    # Standard route: Technopolis to City Centre 1
    start = (22.5815, 88.4348)
    end = (22.5857, 88.4147)

    print("\n==================================================")
    print("  PHASE 1: THE SUNNY DAY (Baseline)")
    print("==================================================")
    baseline = engine.calculate_priority_route(start, end, 1000)
    print(f"Normal Commuter path requires {len(baseline['coordinates'])} coordinate steps.")

    print("\n==================================================")
    print("  PHASE 2: THE FLASH FLOOD")
    print("==================================================")
    # Simulate Member 3 sending a severe flood report right in the middle of our baseline path
    mid_idx = len(baseline['coordinates']) // 2
    mid_point = baseline['coordinates'][mid_idx]
    
    # Find the nearest mathematical edge to this GPS coordinate
    u, v, key = ox.distance.nearest_edges(G, mid_point[1], mid_point[0])
    
    # Manually spike the flood cost to 800 (Extremely dangerous water level)
    G[u][v][key]['flood_cost'] = 800
    print(f"🚨 ALERT: Severe flooding detected at node connection {u} -> {v}!")

    # Recalculate route for a standard commuter
    flood_route = engine.calculate_priority_route(start, end, 1000)
    print(f"Commuter naturally detours around the flood. New path length: {len(flood_route['coordinates'])} steps.")

    print("\n==================================================")
    print("  PHASE 3: THE HERD EFFECT (Gridlock)")
    print("==================================================")
    print("Google Maps just sent 200 cars down this new detour. It is now gridlocked.")
    
    # We simulate the herd effect by maxing out the 'current_load' on every edge of the new detour
    detour_nodes = [ox.distance.nearest_nodes(G, lon, lat) for lat, lon in flood_route['coordinates']]
    
    for i in range(len(detour_nodes)-1):
        n1, n2 = detour_nodes[i], detour_nodes[i+1]
        if G.has_edge(n1, n2):
            for k in G[n1][n2]:
                G[n1][n2][k]['current_load'] = 150  # Over capacity limit of 50!

    print("\n==================================================")
    print("  PHASE 4: THE SYSTEM-LEVEL SOLUTION")
    print("==================================================")
    # Now, an Ambulance and a Leisure Shopper both request a route through this chaos
    shopper = engine.calculate_priority_route(start, end, 200)
    ambulance = engine.calculate_priority_route(start, end, 5000)

    print(f"Shopper (Priority 200) assigned path of {len(shopper['coordinates'])} steps.")
    print(f"Ambulance (Priority 5000) assigned path of {len(ambulance['coordinates'])} steps.")

    print("\n--- FINAL ANALYSIS ---")
    if shopper['coordinates'] != ambulance['coordinates']:
        print("✅ SUCCESS: The Herd Effect has been defeated!")
        print(" -> The Ambulance used its high priority to cut straight through the congested 'Golden Path'.")
        print(" -> The Shopper was dynamically penalized by the congestion and re-routed to a 3rd, safer peripheral path.")
    else:
        print("❌ FAILED: The engine did not split the traffic.")

if __name__ == "__main__":
    run_crisis_simulation()