from routing_engine import PriorityRoutingEngine

def run_benchmarks():
    engine = PriorityRoutingEngine()
    
    # Starting at Technopolis, going to City Centre 1
    start = (22.5815, 88.4348)
    end = (22.5857, 88.4147)

    print("\n--- RUNNING ROUTE TESTS ---")
    
    # 1. Ask for an Emergency Route (Priority 5000)
    emergency_path = engine.calculate_priority_route(start, end, priority_level=5000)
    
    # 2. Ask for a Leisure Route (Priority 200)
    leisure_path = engine.calculate_priority_route(start, end, priority_level=200)

    print(f"Ambulance Path Points: {len(emergency_path['coordinates'])}")
    print(f"Shopper Path Points: {len(leisure_path['coordinates'])}")
    
    if emergency_path['coordinates'] != leisure_path['coordinates']:
        print("SUCCESS: Your engine gave the shopper a different route to keep the road clear for the ambulance!")
    else:
        print("Paths are identical (the best path is currently empty).")

if __name__ == "__main__":
    run_benchmarks()