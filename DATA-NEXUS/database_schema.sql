-- ============================================================
-- SUPABASE SQL SCHEMA FOR FLOOD ALERT SYSTEM (Role 3)
-- ============================================================
-- Copy and paste this into the SQL Editor in your Supabase dashboard
-- Make sure PostGIS extension is enabled in Supabase

-- Enable PostGIS extension (should already be enabled in Supabase)
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- TABLE 1: CITY SECTORS (Weather monitoring)
-- ============================================================
CREATE TABLE IF NOT EXISTS city_sectors (
    id BIGSERIAL PRIMARY KEY,
    sector_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    elevation INT NOT NULL,
    rainfall_mm_hr DECIMAL(6, 2) DEFAULT 0,
    risk_level VARCHAR(20) DEFAULT 'safe', -- safe, low, moderate, high
    risk_score INT DEFAULT 0, -- 0-3
    risk_percentage DECIMAL(8, 2) DEFAULT 0,
    last_updated TIMESTAMP DEFAULT now(),
    created_at TIMESTAMP DEFAULT now()
);

-- Create geometry column for sector center
SELECT AddGeometryColumn('city_sectors', 'geom', 4326, 'POINT', 2);
CREATE INDEX idx_city_sectors_geom ON city_sectors USING GIST(geom);

-- ============================================================
-- TABLE 2: USER REPORTS (Crowdsourced validation)
-- ============================================================
CREATE TABLE IF NOT EXISTS user_reports (
    id BIGSERIAL PRIMARY KEY,
    latitude DECIMAL(10, 6) NOT NULL,
    longitude DECIMAL(10, 6) NOT NULL,
    water_depth INT NOT NULL, -- 1-5 scale
    description TEXT,
    image_url TEXT,
    verified BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP DEFAULT now(),
    created_at TIMESTAMP DEFAULT now()
);

-- Create geometry column for report location
SELECT AddGeometryColumn('user_reports', 'geom', 4326, 'POINT', 2);
CREATE INDEX idx_user_reports_geom ON user_reports USING GIST(geom);
CREATE INDEX idx_user_reports_timestamp ON user_reports(timestamp DESC);

-- ============================================================
-- TABLE 3: ROAD SEGMENTS (Network of roads)
-- ============================================================
CREATE TABLE IF NOT EXISTS road_segments (
    id BIGSERIAL PRIMARY KEY,
    osm_way_id VARCHAR(50) UNIQUE,
    name VARCHAR(255),
    current_cost INT DEFAULT 1, -- 1-1000, higher = more dangerous
    is_flooded BOOLEAN DEFAULT FALSE,
    last_flooded TIMESTAMP,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Create geometry column for road LineString
SELECT AddGeometryColumn('road_segments', 'geom', 4326, 'LINESTRING', 2);
CREATE INDEX idx_road_segments_geom ON road_segments USING GIST(geom);
CREATE INDEX idx_road_segments_cost ON road_segments(current_cost);

-- ============================================================
-- TABLE 4: CONSENSUS TRACKING (For debugging)
-- ============================================================
CREATE TABLE IF NOT EXISTS consensus_events (
    id BIGSERIAL PRIMARY KEY,
    road_id BIGINT REFERENCES road_segments(id),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    report_count INT,
    triggered_at TIMESTAMP DEFAULT now()
);

-- ============================================================
-- FUNCTION 1: get_nearby_reports
-- Returns reports within a radius in the last N minutes
-- ============================================================
CREATE OR REPLACE FUNCTION get_nearby_reports(
    lat DECIMAL,
    lng DECIMAL,
    radius_m INT,
    time_threshold TIMESTAMP
)
RETURNS TABLE (
    id BIGINT,
    latitude DECIMAL,
    longitude DECIMAL,
    water_depth INT,
    image_url TEXT,
    "timestamp" TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ur.id,
        ur.latitude,
        ur.longitude,
        ur.water_depth,
        ur.image_url,
        ur.timestamp
    FROM user_reports ur
    WHERE ur.timestamp > time_threshold
        AND ST_DWithin(
            ur.geom,
            ST_SetSRID(ST_MakePoint(lng, lat), 4326),
            radius_m
        )
    ORDER BY ur.timestamp DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- FUNCTION 2: get_nearest_road
-- Returns the nearest road segment to a point
-- ============================================================
CREATE OR REPLACE FUNCTION get_nearest_road(
    lat DECIMAL,
    lng DECIMAL
)
RETURNS TABLE (
    id BIGINT,
    name VARCHAR,
    distance_m DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rs.id,
        rs.name,
        ST_Distance(
            rs.geom,
            ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography
        )::DECIMAL as distance_m
    FROM road_segments rs
    ORDER BY rs.geom <-> ST_SetSRID(ST_MakePoint(lng, lat), 4326)
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- FUNCTION 3: find_flooded_segments
-- Returns all currently flooded road segments
-- ============================================================
CREATE OR REPLACE FUNCTION find_flooded_segments()
RETURNS TABLE (
    id BIGINT,
    name VARCHAR,
    current_cost INT,
    distance_from_origin DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rs.id,
        rs.name,
        rs.current_cost,
        0::DECIMAL as distance_from_origin
    FROM road_segments rs
    WHERE rs.is_flooded = TRUE
    ORDER BY rs.current_cost DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- INITIAL DATA (Example data for Kolkata)
-- ============================================================

-- Insert example sectors
INSERT INTO city_sectors (sector_id, name, latitude, longitude, elevation, risk_level, risk_score)
VALUES 
    ('salt_lake', 'Salt Lake', 22.5726, 88.4041, 5, 'safe', 0),
    ('new_town', 'New Town', 22.5850, 88.4150, 7, 'safe', 0),
    ('south_kolkata', 'South Kolkata', 22.5283, 88.3617, 4, 'safe', 0),
    ('north_kolkata', 'North Kolkata', 22.6345, 88.3639, 6, 'safe', 0),
    ('central', 'Central', 22.5669, 88.3704, 5, 'safe', 0)
ON CONFLICT (sector_id) DO NOTHING;

-- Update geometry for sectors
UPDATE city_sectors 
SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
WHERE geom IS NULL;

-- ============================================================
-- POLICIES (Row Level Security - Optional but Recommended)
-- ============================================================

-- Enable RLS on tables
ALTER TABLE user_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE city_sectors ENABLE ROW LEVEL SECURITY;
ALTER TABLE road_segments ENABLE ROW LEVEL SECURITY;

-- Allow anyone to select and insert reports (for public reports)
CREATE POLICY "Enable insert for all users" ON user_reports
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable select for all users" ON user_reports
    FOR SELECT USING (true);

-- Allow anyone to select sectors and roads
CREATE POLICY "Enable select for all users on sectors" ON city_sectors
    FOR SELECT USING (true);

CREATE POLICY "Enable select for all users on roads" ON road_segments
    FOR SELECT USING (true);

-- Only allow updates to road_segments from backend (authenticated users)
CREATE POLICY "Enable updates for authenticated users" ON road_segments
    FOR UPDATE USING (auth.role() = 'authenticated')
    WITH CHECK (auth.role() = 'authenticated');

-- ============================================================
-- STORAGE (File uploads for photos)
-- ============================================================
-- Create a bucket in Supabase Storage dashboard:
-- Bucket name: "flood-reports"
-- Public: true
-- File size limit: 10MB

-- Run this in Supabase SQL to verify storage
-- SELECT * FROM storage.buckets;