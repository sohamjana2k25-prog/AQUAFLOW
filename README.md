# 🌊 AquaFlow: Priority-Based Urban Waterlogging & Routing Engine

An integrated urban governance solution designed to mitigate the impact of flash floods and waterlogging on city transportation. The system combines real-time weather analytics, crowdsourced ground-truth verification, and a dynamic routing engine to provide safe navigation paths during monsoon emergencies.

---

## 🌟 Key Features

* **☁️ Predictive Rainfall Engine**: Analyzes real-time weather data to calculate predicted risk levels based on the ratio of rainfall intensity (mm/hr) to sector elevation (m).
* **📸 Crowdsourced Validation**: Enables users to submit flood reports including GPS coordinates, water depth on a 1-5 scale, and photographic evidence for ground-truth verification.
* **🧠 Smart Consensus Algorithm**: Automatically marks road segments as flooded only when a threshold of 3 or more reports is reached within a 100-meter radius within a 60-minute window.
* **🗺️ Dynamic Road Costs**: Updates the cost of road segments in real-time; flooded segments are assigned high weights (e.g., 500) to force the routing engine to calculate optimal detours.

---

## 🚀 Getting Started (Local Run)

Follow these steps to set up the environment and launch the integrated system on your local machine.

### 1. Prerequisites
Ensure you have the following installed:
* **Python 3.10+**
* **Node.js (v18+) and npm**
* **Supabase Account** (with PostGIS enabled and a public storage bucket named `flood-reports`)
* **OpenWeatherMap API Key** (One Call 3.0 subscription)

### 2. Project Structure
Ensure your project directory is organized exactly as follows:

    AQUAFLOW/
    ├── backend/               # Role 2: Routing Engine (FastAPI)
    ├── data-nexus/            # Role 3: Information Backbone (FastAPI)
    │   ├── main.py            # Nexus server logic
    │   ├── .env               # API credentials and port settings
    │   └── test_api.py        # API verification suite
    └── frontend/              # Role 1: User Interface
        └── floodflow/         # Next.js project directory

### 3. Database & Environment Setup
1. **Initialize Database**: Execute the `database_schema.sql` script in your Supabase SQL Editor to create tables for `city_sectors`, `user_reports`, and `road_segments`.
2. **Configure Environment**: Create a `.env` file in the `data-nexus` directory with your `SUPABASE_URL`, `SUPABASE_KEY`, and `OPENWEATHERMAP_API_KEY`. Add `PORT=8001` to avoid conflicts.
3. **Install Dependencies**: 
   * Navigate to `backend` and run `pip install -r requirements.txt`
   * Navigate to `data-nexus` and run `pip install -r requirements.txt`
   * Navigate to `frontend/floodflow` and run `npm install`

### 4. Launch the Application
The system requires three concurrent terminal sessions to operate. Open three tabs and run the following:

* **Terminal 1 (Routing Engine)**: 
  `cd backend`
  `uvicorn main:app --reload --port 8000`
  
* **Terminal 2 (Data Nexus)**: 
  `cd data-nexus`
  `python main.py` *(Runs on port 8001)*
  
* **Terminal 3 (Frontend)**: 
  `cd frontend/floodflow`
  `npm run dev` *(Runs on port 3000)*

---

## 💡 Usage Instructions

1. **Monitor Risks**: Access the dashboard at `http://localhost:3000` to view real-time sector risk levels and the flood heatmap.
2. **Report Incidents**: Use the user interface to submit flood reports; ensure GPS is enabled to provide accurate coordinates.
3. **Verify Consensus**: Submit multiple reports in the same vicinity (within 100m). Watch the terminal logs to witness the consensus algorithm automatically trigger and update the database road costs.
4. **Dynamic Routing**: Use the search bar to find routes. The routing engine will automatically fetch the live costs from the Data Nexus and calculate detours that avoid road segments currently marked as flooded.

---

## 🛡️ Tech Stack & Privacy

* **Frontend**: Next.js, React, Leaflet.js
* **Backend**: FastAPI (Python), Uvicorn
* **Database**: Supabase (PostgreSQL), PostGIS for spatial queries
* **Integrations**: OpenWeatherMap API

**Data Sovereignty**: All user-submitted reports and geographic data are securely routed through your personal Supabase instance, ensuring full control over your city's emergency intelligence.
