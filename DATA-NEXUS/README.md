# Flood Alert System - Role 3 Backend
## The Nexus: Weather Data → Ground Truth → Routing Engine

This is the complete backend implementation for **Role 3** in the hackathon. You manage the information flow between weather APIs, user reports, and the routing logic.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Setup Instructions](#setup-instructions)
3. [API Endpoints](#api-endpoints)
4. [Architecture](#architecture)
5. [Deployment](#deployment)
6. [Demo Strategy](#demo-strategy)

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Supabase
```bash
# Create a .env file from the template
cp .env.example .env

# Fill in your Supabase credentials:
# - SUPABASE_URL: Get from your Supabase project settings
# - SUPABASE_KEY: Get from your Supabase project settings (anon key)
```

### 3. Initialize Database
```bash
# Go to your Supabase project SQL Editor
# Copy-paste the entire contents of database_schema.sql
# Run it to create all tables and functions
```

### 4. Set Up OpenWeatherMap API
```bash
# Go to https://openweathermap.org/api
# Sign up for free and get an API key
# Add it to your .env file as OPENWEATHERMAP_API_KEY
```

### 5. Create Storage Bucket
```bash
# In your Supabase dashboard:
# 1. Go to Storage
# 2. Create a new bucket called "flood-reports"
# 3. Make it public (allow public access to files)
# 4. Set max file size to 10MB (or higher)
```

### 6. Run the Server
```bash
python main.py

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Starting background tasks...
```

### 7. Test the API
```bash
# In another terminal:
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","timestamp":"2024-..."}
```

---

## 🔧 Setup Instructions (Detailed)

### Prerequisites
- Python 3.10+
- Supabase account (free tier works)
- OpenWeatherMap API key
- Git (optional)

### Step 1: Supabase Setup

1. Go to https://supabase.com
2. Create a new project (free tier is fine)
3. Wait for the project to initialize
4. Go to **Settings → API** to get:
   - **Project URL** (SUPABASE_URL)
   - **Anon Public Key** (SUPABASE_KEY) - NOT the service role key
5. Verify PostGIS is enabled:
   - Go to **SQL Editor**
   - Run: `CREATE EXTENSION IF NOT EXISTS postgis;`
   - Should return: `CREATE EXTENSION`

### Step 2: Initialize Database

1. Go to **SQL Editor** in Supabase
2. Copy the entire `database_schema.sql` file
3. Paste it into the SQL editor
4. Click **Run** (or Ctrl+Enter)
5. Verify all tables are created:
   - Go to **Table Editor**
   - You should see: `city_sectors`, `user_reports`, `road_segments`, etc.

### Step 3: Set Up Storage

1. Go to **Storage** section
2. Click **Create a new bucket**
   - Bucket name: `flood-reports`
   - Public/Private: **Public**
3. Click **Create**

### Step 4: OpenWeatherMap API

1. Go to https://openweathermap.org/api
2. Sign up (free)
3. Go to **API keys**
4. Copy your default API key
5. Add to `.env`:
   ```
   OPENWEATHERMAP_API_KEY=your_key_here
   ```

### Step 5: Configure .env

Create a `.env` file in the project root:

```bash
# Copy the template
cp .env.example .env

# Edit .env with your credentials
# nano .env  (or use your editor)
```

Fill in:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
OPENWEATHERMAP_API_KEY=your-api-key
```

### Step 6: Install & Run

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

---

## 📡 API Endpoints

### 1. **POST /report** - Submit Flood Reports
**What it does:** Receives flood reports from users with photos

**Request:**
```bash
curl -X POST "http://localhost:8000/report" \
  -F "latitude=22.5726" \
  -F "longitude=88.4041" \
  -F "water_depth=3" \
  -F "description=Water overflowing from drain" \
  -F "file=@/path/to/photo.jpg"
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| latitude | float | Yes | GPS latitude |
| longitude | float | Yes | GPS longitude |
| water_depth | int | Yes | Water level 1-5 (1=ankle, 5=chest) |
| description | string | No | Description of the flood |
| file | file | No | Photo of the flood |

**Response:**
```json
{
  "status": "success",
  "message": "Report submitted successfully",
  "report_id": 42,
  "image_url": "https://your-storage.com/reports/20240117_150323_photo.jpg"
}
```

**Important:** This triggers the **consensus algorithm**:
- If ≥3 reports within 100m in the last 60 minutes → road is marked flooded
- Road cost automatically set to 500 (high)

---

### 2. **GET /live-costs** - Get Current Road Costs
**What it does:** Returns the cost of each road (used by Member 2's routing engine)

**Request:**
```bash
curl "http://localhost:8000/live-costs"
```

**Response:**
```json
{
  "status": "success",
  "timestamp": "2024-01-17T15:30:00",
  "roads": [
    {"road_id": 101, "cost": 1},
    {"road_id": 102, "cost": 500},
    {"road_id": 103, "cost": 1}
  ]
}
```

**Note:** Member 2's algorithm calls this every time to calculate optimal routes.

---

### 3. **GET /sectors/risk** - Get Sector Risk Levels
**What it does:** Returns real-time risk levels for all city sectors (used by Member 1's heatmap)

**Request:**
```bash
curl "http://localhost:8000/sectors/risk"
```

**Response:**
```json
{
  "status": "success",
  "timestamp": "2024-01-17T15:30:00",
  "sectors": [
    {
      "sector_id": "salt_lake",
      "name": "Salt Lake",
      "latitude": 22.5726,
      "longitude": 88.4041,
      "elevation": 5,
      "rainfall_mm_hr": 2.5,
      "risk_level": "moderate",
      "risk_score": 2,
      "risk_percentage": 0.5,
      "last_updated": "2024-01-17T15:29:00"
    },
    ...
  ]
}
```

**Risk Levels:**
- `safe`: Risk % < 0.5
- `low`: 0.5 ≤ Risk % < 1.5
- `moderate`: 1.5 ≤ Risk % < 3.0
- `high`: Risk % ≥ 3.0

---

### 4. **GET /admin/gallery** - View Recent Reports
**What it does:** Shows the last N flood reports with photos (perfect for your pitch!)

**Request:**
```bash
curl "http://localhost:8000/admin/gallery?limit=10"
```

**Response:**
```json
{
  "status": "success",
  "count": 3,
  "reports": [
    {
      "id": 42,
      "image_url": "https://storage.com/reports/photo.jpg",
      "timestamp": "2024-01-17T15:30:00",
      "latitude": 22.5726,
      "longitude": 88.4041,
      "water_depth": 3,
      "description": "Water overflowing"
    },
    ...
  ]
}
```

---

### 5. **GET /health** - Health Check
**What it does:** Simple health check endpoint

**Request:**
```bash
curl "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-17T15:30:00"
}
```

---

### 6. **GET /debug/sectors** - Debug Configuration
**What it does:** Shows all configured city sectors and thresholds

**Request:**
```bash
curl "http://localhost:8000/debug/sectors"
```

**Response:**
```json
{
  "sectors": {
    "salt_lake": {
      "lat": 22.5726,
      "lng": 88.4041,
      "elevation": 5,
      "name": "Salt Lake"
    },
    ...
  },
  "thresholds": {
    "low": 0.5,
    "moderate": 1.5,
    "high": 3.0
  }
}
```

---

## 🏗️ Architecture

### Three Phases

```
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: Predictive Rainfall Engine                    │
│  ────────────────────────────────────────────           │
│  • Polls OpenWeatherMap API every 5 minutes              │
│  • Calculates: Rp = Rainfall / Elevation                │
│  • Updates city_sectors table with risk levels          │
│  • Output → Member 1 (Heatmap visualization)            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 2: Crowdsourced Validation API                   │
│  ────────────────────────────────────────────           │
│  • Receives user reports with photos                    │
│  • Stores images in Supabase Storage                    │
│  • Runs consensus algorithm (≥3 reports in 100m)        │
│  • Updates road_segments costs when consensus met       │
│  • Output → Member 2 (Routing engine)                   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 3: Live Cost Feed                                │
│  ────────────────────────────────────────────           │
│  • /live-costs endpoint returns road costs              │
│  • Called by Member 2's routing algorithm               │
│  • Combines: elevation risks + user reports             │
│  • Result → Optimal, congestion-avoiding routes         │
└─────────────────────────────────────────────────────────┘
```

### Database Schema

```
city_sectors
├─ sector_id (PK)
├─ name
├─ latitude, longitude
├─ elevation
├─ rainfall_mm_hr (live)
├─ risk_level (safe/low/moderate/high)
├─ risk_score (0-3)
└─ geom (PostGIS POINT)

user_reports
├─ id (PK)
├─ latitude, longitude
├─ water_depth (1-5)
├─ image_url
├─ timestamp
└─ geom (PostGIS POINT)

road_segments
├─ id (PK)
├─ osm_way_id
├─ name
├─ current_cost (1-1000)
├─ is_flooded (boolean)
└─ geom (PostGIS LINESTRING)
```

### Risk Calculation

```
Risk Percentage (Rp) = Rainfall Intensity (mm/hr) / Sector Elevation (m)

Examples:
─────────────────────────────────────────
5 mm/hr rainfall, 5m elevation → Rp = 1.0 (MODERATE)
2 mm/hr rainfall, 5m elevation → Rp = 0.4 (SAFE)
10 mm/hr rainfall, 3m elevation → Rp = 3.3 (HIGH)
```

---

## 🌐 Deployment

### Option 1: Railway (Recommended for Hackathon)

1. Push code to GitHub
2. Go to https://railway.app
3. Connect GitHub repo
4. Add environment variables from `.env`
5. Deploy (1 click)

### Option 2: Render

1. Go to https://render.com
2. Create new Web Service
3. Connect GitHub
4. Set environment variables
5. Deploy

### Option 3: Heroku

1. Install Heroku CLI
2. Run:
   ```bash
   heroku login
   heroku create your-app-name
   heroku config:set SUPABASE_URL=your_url
   heroku config:set SUPABASE_KEY=your_key
   heroku config:set OPENWEATHERMAP_API_KEY=your_key
   git push heroku main
   ```

### Option 4: Local Development (for testing)

```bash
python main.py
# Runs on http://localhost:8000
```

---

## 🎤 Demo Strategy

### What to Show the Judges

#### 1. **The Weather Dashboard**
```bash
# Show real-time rainfall and risk levels
curl "http://localhost:8000/sectors/risk" | python -m json.tool
```
→ "Our system monitors rainfall in real-time and predicts flood risk before it happens"

#### 2. **Submit a Test Report**
```bash
# Simulate a flood report (without photo for demo)
curl -X POST "http://localhost:8000/report" \
  -F "latitude=22.5726" \
  -F "longitude=88.4041" \
  -F "water_depth=4" \
  -F "description=Demo report - water level rising"
```
→ "Users can report floods instantly from their phones with photos"

#### 3. **The Photo Gallery**
```bash
# Show proof of reports
curl "http://localhost:8000/admin/gallery?limit=5" | python -m json.tool
```
→ "We have real visual evidence stored for every report. This builds trust."

#### 4. **Live Road Costs**
```bash
# Show how roads get marked as dangerous
curl "http://localhost:8000/live-costs" | python -m json.tool
```
→ "When consensus is reached, we automatically mark roads as flooded and increase their cost for routing"

---

## 🔐 Security Notes

1. **Don't commit `.env`** - it has your API keys
   - Add to `.gitignore`:
     ```
     .env
     venv/
     __pycache__/
     *.pyc
     ```

2. **Rate Limiting** (optional, add for production):
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   ```

3. **Input Validation** - Add in production:
   - Validate latitude/longitude ranges
   - Validate water_depth is 1-5
   - Rate limit /report endpoint

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'supabase'"
```bash
pip install -r requirements.txt
```

### "SUPABASE_URL not found"
```bash
# Check your .env file exists and has correct values
cat .env
```

### "PostGIS extension not found"
```bash
# Run in Supabase SQL Editor:
CREATE EXTENSION IF NOT EXISTS postgis;
```

### "Storage bucket not found"
```bash
# Create bucket in Supabase Dashboard:
# Storage → Create Bucket → "flood-reports" → Public
```

### "Background task not running"
Check logs:
```bash
# You should see:
# INFO:     Starting background tasks...
# INFO:     Starting sector risk update...
```

---

## 📊 For the Judges: Key Points

1. **Real-time Weather Integration** - We fetch live rainfall data
2. **Crowdsourced Validation** - Users report flooding with photographic evidence
3. **Smart Consensus Algorithm** - We prevent false reports (≥3 confirmations in 100m)
4. **Dynamic Road Costs** - Flooded roads automatically get high costs
5. **Multi-layer Architecture** - Three specialized roles (Member 1, 2, 3) working seamlessly

---

## 📝 Notes for Other Team Members

### For Member 1 (Frontend/Map):
- Call `GET /sectors/risk` to populate your heatmap
- Update every 30 seconds for near real-time display
- Use the `risk_score` (0-3) for color intensity

### For Member 2 (Routing Engine):
- Call `GET /live-costs` to get current road weights
- Format: `[{"road_id": 101, "cost": 500}, ...]`
- Incorporate costs into your A* or Dijkstra algorithm
- Higher cost = avoid this road

### For Deployment:
- Make sure all three services are running
- Test the integration: report → Member 2's routing changes
- Demo: submit fake reports, watch road costs spike

---

## 🎯 What You've Built

You've built the **information backbone** of the system:

✅ Live weather monitoring
✅ User report collection with photo storage
✅ Smart consensus algorithm (prevents false reports)
✅ Database integration with PostGIS for spatial queries
✅ REST APIs for Members 1 and 2
✅ Admin gallery for proof

**Total Time:** ~2-3 hours to set up
**Impact:** Solves the "herd effect" problem mentioned in the hackathon brief

Good luck! 🚀
