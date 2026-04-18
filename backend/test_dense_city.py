from routing_engine import PriorityRoutingEngine
import osmnx as ox

def run_dense_city_simulation():
    print("Initializing Dense Urban Grid... (Loading Howrah Topology)")
    # Howrah has a guaranteed polygon and is extremely dense
    engine = PriorityRoutingEngine(place_name="Howrah, West Bengal")
    G = engine.graph 

    # Route: Howrah Station to Nabanna (Shibpur)
    start = (22.5839, 88.3433)
    end = (22.5601, 88.3129)

    print("\n--- PHASE 1: THE SUNNY DAY ---")
    baseline = engine.calculate_priority_route(start, end, 1000)
    print(f"Normal Commuter path: {len(baseline['coordinates'])} coordinate steps.")

    print("\n--- PHASE 2: THE FLASH FLOOD ---")
    # Trigger a flood perfectly in the middle of the baseline path
    mid_idx = len(baseline['coordinates']) // 2
    mid_point = baseline['coordinates'][mid_idx]
    
    u, v, key = ox.distance.nearest_edges(G, mid_point[1], mid_point[0])
    G[u][v][key]['flood_cost'] = 800
    print(f"🚨 Flooding triggered at edge {u} -> {v}!")

    flood_route = engine.calculate_priority_route(start, end, 1000)
    print(f"Detour path length: {len(flood_route['coordinates'])} steps.")

    print("\n--- PHASE 3: THE HERD EFFECT ---")
    # Simulate Google Maps funneling 200 cars onto the new detour
    detour_nodes = [ox.distance.nearest_nodes(G, lon, lat) for lat, lon in flood_route['coordinates']]
    for i in range(len(detour_nodes)-1):
        n1, n2 = detour_nodes[i], detour_nodes[i+1]
        if G.has_edge(n1, n2):
            for k in G[n1][n2]:
                G[n1][n2][k]['current_load'] = 150  # Massive Gridlock

    print("\n--- PHASE 4: SYSTEM-LEVEL SOLUTION (With elegant 2.5x penalty) ---")
    shopper = engine.calculate_priority_route(start, end, 200)
    ambulance = engine.calculate_priority_route(start, end, 5000)

    print(f"Shopper (Priority 200) path: {len(shopper['coordinates'])} steps.")
    print(f"Ambulance (Priority 5000) path: {len(ambulance['coordinates'])} steps.")

    print("\n--- FINAL ANALYSIS ---")
    if shopper['coordinates'] != ambulance['coordinates']:
        print("✅ SUCCESS: The dense topology naturally split the traffic using the minimal 2.5x mathematical penalty!")
    else:
        print("❌ FAILED: The traffic did not split.")

if __name__ == "__main__":
    run_dense_city_simulation()