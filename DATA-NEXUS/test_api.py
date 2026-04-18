#!/usr/bin/env python3
"""
API Testing Guide and Examples for Flood Alert System (Role 3)
Run this script to test all endpoints and verify your setup
"""

import requests
import json
import time
from datetime import datetime

# Change this to your actual server URL
BASE_URL = "http://localhost:8001"

# ANSI colors for pretty output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}ℹ {text}{RESET}")

# ============================================================
# TEST 1: Health Check
# ============================================================
def test_health_check():
    print_header("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        
        if response.status_code == 200:
            print_success(f"Server is healthy")
            print(json.dumps(data, indent=2))
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to {BASE_URL}")
        print_info("Make sure the server is running: python main.py")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ============================================================
# TEST 2: Get Sector Risks
# ============================================================
def test_get_sector_risks():
    print_header("TEST 2: Get Sector Risks")
    print_info("This endpoint should return weather data for all sectors")
    
    try:
        response = requests.get(f"{BASE_URL}/sectors/risk")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved {len(data.get('sectors', []))} sectors")
            print(json.dumps(data, indent=2)[:500] + "...\n")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ============================================================
# TEST 3: Submit Flood Report (without photo)
# ============================================================
def test_submit_report_no_photo():
    print_header("TEST 3: Submit Flood Report (Without Photo)")
    print_info("Submitting a test report for Salt Lake sector")
    
    data = {
        'latitude': 22.5726,
        'longitude': 88.4041,
        'water_depth': 3,
        'description': 'Test report - water level rising near Salt Lake'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/report", data=data)
        
        if response.status_code == 200:
            result = response.json()
            print_success("Report submitted successfully")
            print(json.dumps(result, indent=2))
            return result.get('report_id')
        else:
            print_error(f"Failed: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None

# ============================================================
# TEST 4: Get Live Road Costs
# ============================================================
def test_get_live_costs():
    print_header("TEST 4: Get Live Road Costs")
    print_info("This is what Member 2's routing engine uses")
    
    try:
        response = requests.get(f"{BASE_URL}/live-costs")
        
        if response.status_code == 200:
            data = response.json()
            roads = data.get('roads', [])
            print_success(f"Retrieved costs for {len(roads)} roads")
            
            # Show a few examples
            print("\nSample of road costs:")
            for road in roads[:5]:
                status = f"{RED}FLOODED{RESET}" if road['cost'] > 100 else f"{GREEN}SAFE{RESET}"
                print(f"  Road {road['road_id']}: Cost {road['cost']} [{status}]")
            
            if len(roads) > 5:
                print(f"  ... and {len(roads) - 5} more roads")
            
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ============================================================
# TEST 5: Submit Multiple Reports (Test Consensus)
# ============================================================
def test_consensus_algorithm():
    print_header("TEST 5: Consensus Algorithm Test")
    print_info("Submitting 3 reports in the same location (should trigger consensus)")
    
    # Submit 3 reports within 100m radius
    locations = [
        {'lat': 22.5726, 'lng': 88.4041, 'desc': 'Report 1 - from User A'},
        {'lat': 22.5727, 'lng': 88.4042, 'desc': 'Report 2 - from User B'},
        {'lat': 22.5725, 'lng': 88.4040, 'desc': 'Report 3 - from User C'},
    ]
    
    report_count = 0
    for location in locations:
        data = {
            'latitude': location['lat'],
            'longitude': location['lng'],
            'water_depth': 4,
            'description': location['desc']
        }
        
        try:
            response = requests.post(f"{BASE_URL}/report", data=data)
            if response.status_code == 200:
                report_count += 1
                print_success(f"Submitted: {location['desc']}")
                print(f"  Response: {response.json()['message']}")
            else:
                print_error(f"Failed to submit: {location['desc']}")
        except Exception as e:
            print_error(f"Error: {e}")
    
    print_info(f"Submitted {report_count} reports")
    print_info("If consensus was reached, a road segment near this location should now be marked flooded")
    print_info("Check /live-costs endpoint - look for roads with high costs")
    
    return report_count == 3

# ============================================================
# TEST 6: Get Admin Gallery
# ============================================================
def test_get_gallery():
    print_header("TEST 6: Admin Gallery")
    print_info("View recent flood reports (only shows reports with photos)")
    
    try:
        response = requests.get(f"{BASE_URL}/admin/gallery?limit=5")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved {data.get('count', 0)} reports with photos")
            
            reports = data.get('reports', [])
            if reports:
                for i, report in enumerate(reports[:3], 1):
                    print(f"\n  Report {i}:")
                    print(f"    ID: {report['id']}")
                    print(f"    Location: ({report['latitude']:.4f}, {report['longitude']:.4f})")
                    print(f"    Water Depth: {report['water_depth']}/5")
                    print(f"    Time: {report['timestamp']}")
                    if report.get('image_url'):
                        print(f"    Photo: {report['image_url'][:50]}...")
            else:
                print_info("No reports with photos yet. Submit a report with a photo to test this.")
            
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ============================================================
# TEST 7: Debug Configuration
# ============================================================
def test_debug_config():
    print_header("TEST 7: Debug Configuration")
    print_info("View configured city sectors and risk thresholds")
    
    try:
        response = requests.get(f"{BASE_URL}/debug/sectors")
        
        if response.status_code == 200:
            data = response.json()
            sectors = data.get('sectors', {})
            thresholds = data.get('thresholds', {})
            
            print_success(f"Found {len(sectors)} configured sectors:")
            for sector_id, sector_data in list(sectors.items())[:3]:
                print(f"\n  {sector_data['name']}:")
                print(f"    Location: ({sector_data['lat']}, {sector_data['lng']})")
                print(f"    Elevation: {sector_data['elevation']}m")
            
            print(f"\n  Risk Thresholds:")
            for level, threshold in thresholds.items():
                print(f"    {level.capitalize()}: Rp > {threshold}")
            
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

# ============================================================
# CURL COMMANDS REFERENCE
# ============================================================
def print_curl_reference():
    print_header("CURL COMMANDS REFERENCE")
    
    commands = {
        "Health Check": 'curl http://localhost:8000/health',
        
        "Get Sector Risks": 'curl http://localhost:8000/sectors/risk',
        
        "Submit Report (No Photo)": '''curl -X POST "http://localhost:8000/report" \\
  -F "latitude=22.5726" \\
  -F "longitude=88.4041" \\
  -F "water_depth=3" \\
  -F "description=Water overflowing"''',
        
        "Submit Report (With Photo)": '''curl -X POST "http://localhost:8000/report" \\
  -F "latitude=22.5726" \\
  -F "longitude=88.4041" \\
  -F "water_depth=3" \\
  -F "file=@/path/to/photo.jpg"''',
        
        "Get Live Costs": 'curl http://localhost:8000/live-costs',
        
        "Get Gallery": 'curl http://localhost:8000/admin/gallery?limit=10',
        
        "Pretty Print JSON": 'curl http://localhost:8000/sectors/risk | python -m json.tool'
    }
    
    for name, command in commands.items():
        print(f"{YELLOW}{name}:{RESET}")
        print(f"{command}\n")

# ============================================================
# MAIN TEST RUNNER
# ============================================================
def run_all_tests():
    print(f"\n{BLUE}╔══════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║  Flood Alert System - API Test Suite                ║{RESET}")
    print(f"{BLUE}║  Role 3 Backend Testing                             ║{RESET}")
    print(f"{BLUE}╚══════════════════════════════════════════════════════╝{RESET}")
    
    print(f"\n{YELLOW}Testing endpoint: {BASE_URL}{RESET}")
    print(f"{YELLOW}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")
    
    results = {}
    
    # Run all tests
    results['Health Check'] = test_health_check()
    
    if not results['Health Check']:
        print_error("Cannot continue testing - server is not running")
        return
    
    time.sleep(1)
    results['Sector Risks'] = test_get_sector_risks()
    
    time.sleep(1)
    results['Submit Report'] = test_submit_report_no_photo() is not None
    
    time.sleep(1)
    results['Live Costs'] = test_get_live_costs()
    
    time.sleep(1)
    results['Consensus Algorithm'] = test_consensus_algorithm()
    
    time.sleep(1)
    results['Admin Gallery'] = test_get_gallery()
    
    time.sleep(1)
    results['Debug Config'] = test_debug_config()
    
    # Print summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = f"{GREEN}PASSED{RESET}" if passed_flag else f"{RED}FAILED{RESET}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{YELLOW}Total: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"{GREEN}🎉 All tests passed! Your API is ready for the hackathon!{RESET}")
    else:
        print(f"{YELLOW}⚠️  Some tests failed. Check your setup.{RESET}")
    
    # Print curl reference
    print_curl_reference()

if __name__ == "__main__":
    run_all_tests()
