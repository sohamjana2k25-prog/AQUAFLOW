# 🚀 Flood Alert System - Role 3 Setup Checklist

## Part 1: Prerequisites
- [ ] Python 3.10+ installed (`python --version`)
- [ ] Git installed (or download zip of files)
- [ ] Text editor (VS Code, Sublime, etc.)
- [ ] Internet connection (for APIs)

## Part 2: Supabase Setup (15 minutes)

### Create Supabase Project
- [ ] Go to https://supabase.com
- [ ] Sign up / Log in
- [ ] Create new project
- [ ] Wait for project to initialize (5-10 minutes)

### Get Credentials
- [ ] Go to Settings → API
- [ ] Copy **Project URL** → save it
- [ ] Copy **Anon Public Key** → save it
- [ ] ⚠️ Do NOT use Service Role Key

### Enable PostGIS
- [ ] Go to SQL Editor
- [ ] Run: `CREATE EXTENSION IF NOT EXISTS postgis;`
- [ ] Should return: `CREATE EXTENSION`

### Create Storage Bucket
- [ ] Go to Storage section
- [ ] Click "Create a new bucket"
- [ ] Name: `flood-reports`
- [ ] Public: **Yes**
- [ ] Click Create
- [ ] Verify you see the bucket in the list

## Part 3: OpenWeatherMap API (5 minutes)

- [ ] Go to https://openweathermap.org/api
- [ ] Sign up for free account
- [ ] Go to "API keys" section
- [ ] Copy your default API key
- [ ] Save it somewhere safe

## Part 4: Project Setup (10 minutes)

### Clone/Download Code
- [ ] Download all files from GitHub/your source
- [ ] Extract to a folder (e.g., `flood-alert`)
- [ ] Open terminal in that folder

### Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```
- [ ] Verify: should see `(venv)` in your terminal

### Install Dependencies
```bash
pip install -r requirements.txt
```
- [ ] Wait for installation to complete
- [ ] No errors should appear

### Create .env File
```bash
cp .env.example .env
```
- [ ] Open `.env` in your editor
- [ ] Add your Supabase URL
- [ ] Add your Supabase Key
- [ ] Add your OpenWeatherMap API key
- [ ] Save

### Example .env file:
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
OPENWEATHERMAP_API_KEY=your-openweathermap-key
```

## Part 5: Database Setup (10 minutes)

### Initialize Database Schema
- [ ] Open your Supabase project
- [ ] Go to SQL Editor
- [ ] Open `database_schema.sql` in your editor
- [ ] Copy entire contents
- [ ] Paste into Supabase SQL Editor
- [ ] Click Run (or Ctrl+Enter)
- [ ] Wait for success message

### Verify Tables Created
- [ ] Go to Table Editor in Supabase
- [ ] You should see:
  - [ ] `city_sectors` (with 5 example sectors)
  - [ ] `user_reports`
  - [ ] `road_segments`
  - [ ] `consensus_events`

### Verify Functions Created
- [ ] Still in SQL Editor
- [ ] Go to "Functions" section
- [ ] You should see:
  - [ ] `get_nearby_reports`
  - [ ] `get_nearest_road`
  - [ ] `find_flooded_segments`

## Part 6: Run & Test (5 minutes)

### Start the Server
```bash
python main.py
```
- [ ] You should see:
  ```
  INFO:     Uvicorn running on http://0.0.0.0:8000
  INFO:     Starting background tasks...
  ```

### Test in New Terminal
```bash
# Keep first terminal running, open a new one
curl http://localhost:8000/health
```
- [ ] Should return: `{"status":"healthy",...}`

### Run Full Test Suite
```bash
python test_api.py
```
- [ ] Should show all tests passing
- [ ] If any fail, check error messages

## Part 7: Integration Testing (Optional)

### Test with Member 1 (Frontend)
- [ ] Verify they can access `GET /sectors/risk`
- [ ] Check that data updates every 5 minutes
- [ ] Test heatmap colors match risk levels

### Test with Member 2 (Routing Engine)
- [ ] Verify they can access `GET /live-costs`
- [ ] Submit test reports and verify road costs update
- [ ] Test that consensus (3 reports) triggers flooding

### Manual Testing
- [ ] Submit a report: `curl -X POST http://localhost:8000/report ...`
- [ ] Check `/live-costs` to see if cost changed
- [ ] Check `/admin/gallery` to see your report

## Part 8: Deployment Prep (Optional)

### For Deployment to Railway/Render:
- [ ] Push code to GitHub
- [ ] Create account on Railway.app or Render.com
- [ ] Connect your GitHub repo
- [ ] Add environment variables:
  - [ ] `SUPABASE_URL`
  - [ ] `SUPABASE_KEY`
  - [ ] `OPENWEATHERMAP_API_KEY`
- [ ] Deploy (1 click)

## Part 9: Hackathon Demo Prep

### Create Demo Script
- [ ] Test `/sectors/risk` endpoint
- [ ] Submit 3 test reports at same location
- [ ] Show `/admin/gallery` with your photos
- [ ] Demonstrate `/live-costs` showing road cost change

### Demo Talking Points
- [ ] "We solve the 'herd effect' by detecting floods automatically"
- [ ] "Weather data + GPS location = early warning system"
- [ ] "User photos provide proof for route optimization"
- [ ] "Consensus algorithm prevents false reports"
- [ ] "Real-time road costs guide users away from danger"

## Troubleshooting Checklist

If something doesn't work:

### Server Won't Start
- [ ] Check Python version: `python --version` (need 3.10+)
- [ ] Check virtual environment: `source venv/bin/activate`
- [ ] Check dependencies: `pip install -r requirements.txt`
- [ ] Check `.env` file exists and has values

### Can't Connect to Supabase
- [ ] Check SUPABASE_URL is correct
- [ ] Check SUPABASE_KEY is correct (use Anon key, not Service Role)
- [ ] Check table names match (lowercase)
- [ ] Run schema SQL again

### No Data in /sectors/risk
- [ ] Check OpenWeatherMap API key is valid
- [ ] Check city_sectors table has data
- [ ] Wait 5 minutes for first update
- [ ] Check server logs for errors

### Can't Upload Photos
- [ ] Check flood-reports bucket exists in Storage
- [ ] Check bucket is set to Public
- [ ] Check SUPABASE_KEY has storage permissions

## Success Indicators

### You're Ready if:
- [x] `curl http://localhost:8000/health` returns 200
- [x] `/sectors/risk` shows data with risk levels
- [x] You can submit reports to `/report` endpoint
- [x] `/live-costs` shows road data
- [x] `test_api.py` runs with all tests passing
- [x] Photos upload to storage successfully
- [x] Consensus triggers when 3 reports are nearby

## Time Estimate
- Total setup: **1 hour**
  - Supabase: 15 min
  - APIs: 5 min
  - Project setup: 10 min
  - Database: 10 min
  - Testing: 10 min
  - Debugging: 10 min

## Quick Reference

### Most Important Files
- `main.py` - The FastAPI server
- `.env` - Your credentials (don't commit!)
- `database_schema.sql` - Database setup
- `test_api.py` - Testing script
- `README.md` - Full documentation

### Most Important Endpoints
- `GET /health` - Check if server is running
- `GET /sectors/risk` - Get weather data (for Member 1)
- `POST /report` - Submit flood reports
- `GET /live-costs` - Get road costs (for Member 2)
- `GET /admin/gallery` - View recent reports

### Quick Commands
```bash
# Start server
python main.py

# Test API
python test_api.py

# Check specific endpoint
curl http://localhost:8000/sectors/risk

# View logs
# (just watch the terminal where main.py is running)
```

---

## Need Help?

1. Check `README.md` for detailed explanations
2. Check `test_api.py` for example requests
3. Look at error messages in server logs
4. Check Supabase dashboard to verify tables/data
5. Verify .env file has all 3 credentials

Good luck! 🚀
