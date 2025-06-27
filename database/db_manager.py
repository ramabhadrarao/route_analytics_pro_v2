# database/db_manager.py - SQLite Database Manager for Route Analysis System
# Purpose: Handle all database operations including route storage, API tracking, and image management
# Dependencies: sqlite3, json, datetime
# Author: Route Analysis System
# Created: 2024

import sqlite3
import json
import datetime
import os
from typing import Dict, List, Any, Optional

class DatabaseManager:
    """Manages all database operations for the route analysis system"""
    
    def __init__(self, db_path: str = "database/route_analysis.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with all required tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Routes table - main route information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS routes (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    from_address TEXT,
                    to_address TEXT,
                    distance TEXT,
                    duration TEXT,
                    total_points INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # Route points - GPS coordinates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS route_points (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    point_index INTEGER NOT NULL,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # Sharp turns analysis
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sharp_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    angle REAL NOT NULL,
                    classification TEXT,
                    danger_level TEXT,
                    recommended_speed INTEGER,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # Points of Interest
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pois (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    poi_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    address TEXT,
                    distance_from_route REAL,
                    additional_info TEXT,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # Weather data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    temperature REAL,
                    humidity INTEGER,
                    wind_speed REAL,
                    weather_condition TEXT,
                    description TEXT,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # Network coverage data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS network_coverage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    signal_strength INTEGER,
                    network_type TEXT,
                    coverage_quality TEXT,
                    technologies TEXT,
                    is_dead_zone BOOLEAN DEFAULT 0,
                    is_poor_coverage BOOLEAN DEFAULT 0,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # Elevation data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS elevation_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    elevation REAL NOT NULL,
                    elevation_change REAL,
                    gradient REAL,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # API usage tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT,
                    api_name TEXT NOT NULL,
                    endpoint TEXT,
                    method TEXT DEFAULT 'GET',
                    response_code INTEGER,
                    response_time REAL,
                    success BOOLEAN,
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # Stored images (street view, satellite, maps)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stored_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    image_type TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # Traffic data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS traffic_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    congestion_level TEXT,
                    travel_time_index REAL,
                    free_flow_speed INTEGER,
                    current_speed INTEGER,
                    incidents_count INTEGER DEFAULT 0,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # Compliance data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    vehicle_type TEXT NOT NULL,
                    compliance_score INTEGER,
                    ais_140_required BOOLEAN,
                    permits_required TEXT,
                    restrictions TEXT,
                    recommendations TEXT,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # Road quality data (from your enhanced system)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS road_quality_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    issue_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    description TEXT,
                    recommended_speed INTEGER,
                    api_sources TEXT,
                    analysis_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # Environmental risks data (from your enhanced system)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS environmental_risks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    risk_category TEXT NOT NULL,
                    risk_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT,
                    recommendations TEXT,
                    source_api TEXT,
                    additional_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # NEW EMERGENCY CONTACTS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emergency_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    facility_type TEXT NOT NULL,
                    facility_name TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    formatted_address TEXT,
                    formatted_phone_number TEXT,
                    international_phone_number TEXT,
                    website TEXT,
                    opening_hours TEXT,
                    rating REAL,
                    user_ratings_total INTEGER,
                    business_status TEXT,
                    emergency_services TEXT,
                    distance_from_route REAL,
                    place_id TEXT,
                    additional_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            # Highway information table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS route_highways (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    highway_name TEXT NOT NULL,
                    highway_type TEXT NOT NULL,
                    start_latitude REAL,
                    start_longitude REAL,
                    end_latitude REAL,
                    end_longitude REAL,
                    length_km REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # Terrain classification table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS route_terrain (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_id TEXT NOT NULL,
                    terrain_type TEXT NOT NULL,
                    terrain_score REAL,
                    elevation_variance REAL,
                    urban_density_score REAL,
                    classification_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (route_id) REFERENCES routes (id)
                )
            """)
            
            # SAFE COLUMN ADDITIONS TO EXISTING POIS TABLE
            # Check existing columns first
            cursor.execute("PRAGMA table_info(pois)")
            existing_columns = [column[1] for column in cursor.fetchall()]
            
            # Only add columns that don't exist
            if 'phone_number' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE pois ADD COLUMN phone_number TEXT")
                    print("✅ Added phone_number column to pois table")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ Could not add phone_number column: {e}")
            
            if 'place_id' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE pois ADD COLUMN place_id TEXT")
                    print("✅ Added place_id column to pois table")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ Could not add place_id column: {e}")
            
            if 'rating' not in existing_columns:
                try:
                    cursor.execute("ALTER TABLE pois ADD COLUMN rating REAL")
                    print("✅ Added rating column to pois table")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ Could not add rating column: {e}")
            
            conn.commit()
            print("✅ Database initialized successfully with emergency contacts support")
    
    def create_route(self, route_id: str, user_id: str, filename: str, 
                    from_address: str = None, to_address: str = None,
                    distance: str = None, duration: str = None, 
                    total_points: int = 0) -> bool:
        """Create a new route record"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO routes 
                    (id, user_id, filename, from_address, to_address, distance, duration, total_points)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (route_id, user_id, filename, from_address, to_address, distance, duration, total_points))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating route: {e}")
            return False
    
    def store_route_points(self, route_id: str, points: List[List[float]]) -> bool:
        """Store route GPS coordinates"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for i, point in enumerate(points):
                    cursor.execute("""
                        INSERT INTO route_points (route_id, latitude, longitude, point_index)
                        VALUES (?, ?, ?, ?)
                    """, (route_id, point[0], point[1], i))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error storing route points: {e}")
            return False
    
    def store_sharp_turns(self, route_id: str, turns: List[Dict]) -> bool:
        """Store sharp turns analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for turn in turns:
                    cursor.execute("""
                        INSERT INTO sharp_turns 
                        (route_id, latitude, longitude, angle, classification, danger_level, recommended_speed)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        route_id, turn['lat'], turn['lng'], turn['angle'],
                        turn.get('classification'), turn.get('danger_level'),
                        turn.get('recommended_speed')
                    ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error storing sharp turns: {e}")
            return False
    
    def store_pois(self, route_id: str, pois: Dict, poi_type: str) -> bool:
        """Store points of interest"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for name, address in pois.items():
                    # Extract coordinates if available (simplified)
                    lat, lng = 0.0, 0.0  # Would be calculated from address
                    
                    cursor.execute("""
                        INSERT INTO pois 
                        (route_id, poi_type, name, latitude, longitude, address)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (route_id, poi_type, name, lat, lng, address))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error storing POIs: {e}")
            return False
    
    def store_weather_data(self, route_id: str, weather_points: List[Dict]) -> bool:
        """Store weather data for route points"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for weather in weather_points:
                    coords = weather.get('coordinates', {})
                    cursor.execute("""
                        INSERT INTO weather_data 
                        (route_id, latitude, longitude, temperature, humidity, wind_speed, 
                         weather_condition, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        route_id, coords.get('lat', 0), coords.get('lng', 0),
                        weather.get('temp'), weather.get('humidity'), weather.get('wind_speed'),
                        weather.get('main'), weather.get('description')
                    ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error storing weather data: {e}")
            return False
    
    def store_network_coverage(self, route_id: str, coverage_data: List[Dict]) -> bool:
        """Store network coverage analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for point in coverage_data:
                    coords = point.get('coordinates', {})
                    coverage = point.get('coverage_data', {})
                    
                    cursor.execute("""
                        INSERT INTO network_coverage 
                        (route_id, latitude, longitude, signal_strength, network_type, 
                         coverage_quality, technologies, is_dead_zone, is_poor_coverage)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        route_id, coords.get('lat', 0), coords.get('lng', 0),
                        coverage.get('signal_strength'), coverage.get('network_type'),
                        point.get('coverage_quality'), json.dumps(coverage.get('technologies', [])),
                        point.get('coverage_quality') == 'dead',
                        point.get('coverage_quality') == 'poor'
                    ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error storing network coverage: {e}")
            return False
    
    def store_image(self, route_id: str, image_type: str, filename: str, 
                   file_path: str, latitude: float = None, longitude: float = None,
                   file_size: int = None) -> bool:
        """Store image file information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO stored_images 
                    (route_id, image_type, latitude, longitude, filename, file_path, file_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (route_id, image_type, latitude, longitude, filename, file_path, file_size))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error storing image info: {e}")
            return False
    
    def log_api_usage(self, api_name: str, endpoint: str, response_code: int,
                     response_time: float, success: bool, route_id: str = None,
                     error_message: str = None) -> bool:
        """Log API usage for tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO api_usage 
                    (route_id, api_name, endpoint, response_code, response_time, 
                     success, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (route_id, api_name, endpoint, response_code, response_time, success, error_message))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error logging API usage: {e}")
            return False
    
    def get_route(self, route_id: str) -> Optional[Dict]:
        """Get route basic information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM routes WHERE id = ?", (route_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Error getting route: {e}")
            return None
    
    def get_route_points(self, route_id: str) -> List[Dict]:
        """Get all route points"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT latitude, longitude, point_index 
                    FROM route_points 
                    WHERE route_id = ? 
                    ORDER BY point_index
                """, (route_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting route points: {e}")
            return []
    
    def get_sharp_turns(self, route_id: str) -> List[Dict]:
        """Get sharp turns for route"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sharp_turns WHERE route_id = ?", (route_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting sharp turns: {e}")
            return []
    
    def get_pois_by_type(self, route_id: str, poi_type: str) -> List[Dict]:
        """Get POIs of specific type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM pois WHERE route_id = ? AND poi_type = ?", 
                             (route_id, poi_type))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting POIs: {e}")
            return []
    
    def get_weather_data(self, route_id: str) -> List[Dict]:
        """Get weather data for route"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM weather_data WHERE route_id = ?", (route_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting weather data: {e}")
            return []
    
    def get_network_coverage(self, route_id: str) -> List[Dict]:
        """Get network coverage data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM network_coverage WHERE route_id = ?", (route_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting network coverage: {e}")
            return []
    
    def get_user_routes(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get all routes for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM routes 
                    WHERE user_id = ? AND status = 'active'
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (user_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting user routes: {e}")
            return []
    
    def get_recent_routes(self, limit: int = 10) -> List[Dict]:
        """Get recent routes across all users"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM routes 
                    WHERE status = 'active'
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting recent routes: {e}")
            return []
    
    def get_api_usage_stats(self) -> Dict:
        """Get API usage statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Total calls per API
                cursor.execute("""
                    SELECT api_name, COUNT(*) as total_calls, 
                           SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls,
                           AVG(response_time) as avg_response_time
                    FROM api_usage 
                    GROUP BY api_name
                """)
                api_stats = [dict(row) for row in cursor.fetchall()]
                
                # Recent usage (last 24 hours)
                cursor.execute("""
                    SELECT COUNT(*) as recent_calls
                    FROM api_usage 
                    WHERE timestamp > datetime('now', '-24 hours')
                """)
                recent_calls = cursor.fetchone()[0]
                
                return {
                    'api_stats': api_stats,
                    'recent_calls': recent_calls,
                    'timestamp': datetime.datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Error getting API stats: {e}")
            return {}
    def store_pois_with_coordinates(self, route_id: str, pois: Dict, poi_type: str) -> bool:
        """Store points of interest WITH REAL GPS COORDINATES"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for poi_key, poi_data in pois.items():
                    cursor.execute("""
                        INSERT INTO pois 
                        (route_id, poi_type, name, latitude, longitude, address, 
                        distance_from_route, additional_info)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        route_id, 
                        poi_type, 
                        poi_data['name'], 
                        poi_data['latitude'],      # REAL GPS LATITUDE
                        poi_data['longitude'],     # REAL GPS LONGITUDE
                        poi_data['address'],
                        0,  # distance_from_route - could be calculated later
                        json.dumps({
                            'place_id': poi_data.get('place_id', ''),
                            'rating': poi_data.get('rating', 0),
                            'types': poi_data.get('types', [])
                        })
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error storing POIs with coordinates: {e}")
            return False
    def get_stored_images(self, route_id: str, image_type: str = None) -> List[Dict]:
        """Get stored images for route"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if image_type:
                    cursor.execute("""
                        SELECT * FROM stored_images 
                        WHERE route_id = ? AND image_type = ?
                        ORDER BY created_at
                    """, (route_id, image_type))
                else:
                    cursor.execute("""
                        SELECT * FROM stored_images 
                        WHERE route_id = ?
                        ORDER BY image_type, created_at
                    """, (route_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting stored images: {e}")
            return []
    def store_emergency_contacts(self, route_id: str, emergency_data: Dict) -> bool:
        """Store emergency contacts/facilities data in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stored_count = 0
                
                # Process different types of emergency facilities
                emergency_types = {
                    'hospitals': 'hospital',
                    'police_stations': 'police',
                    'fire_stations': 'fire_station',
                    'emergency_clinics': 'emergency_clinic',
                    'ambulance_services': 'ambulance'
                }
                
                for data_key, facility_type in emergency_types.items():
                    facilities = emergency_data.get(data_key, [])
                    
                    for facility in facilities:
                        try:
                            # Prepare additional info as JSON
                            additional_info = {
                                'types': facility.get('types', []),
                                'vicinity': facility.get('vicinity', ''),
                                'photos': facility.get('photos', []),
                                'price_level': facility.get('price_level'),
                                'google_data': facility.get('google_data', {})
                            }
                            
                            cursor.execute("""
                                INSERT INTO emergency_contacts 
                                (route_id, facility_type, facility_name, latitude, longitude,
                                formatted_address, formatted_phone_number, international_phone_number,
                                website, opening_hours, rating, user_ratings_total, business_status,
                                emergency_services, distance_from_route, place_id, additional_info)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                route_id,
                                facility_type,
                                facility.get('name', 'Unknown Facility'),
                                facility.get('latitude', 0),
                                facility.get('longitude', 0),
                                facility.get('formatted_address', facility.get('address', '')),
                                facility.get('formatted_phone_number', ''),
                                facility.get('international_phone_number', ''),
                                facility.get('website', ''),
                                json.dumps(facility.get('opening_hours', {})),
                                facility.get('rating', 0),
                                facility.get('user_ratings_total', 0),
                                facility.get('business_status', ''),
                                facility_type.replace('_', ' ').title(),
                                facility.get('distance_from_route', 0),
                                facility.get('place_id', ''),
                                json.dumps(additional_info)
                            ))
                            stored_count += 1
                            
                        except Exception as e:
                            print(f"Error storing emergency facility: {e}")
                            continue
                
                conn.commit()
                print(f"✅ Stored {stored_count} emergency contacts in database")
                return True
                
        except Exception as e:
            print(f"❌ Error storing emergency contacts: {e}")
            return False

    def get_emergency_contacts(self, route_id: str) -> List[Dict]:
        """Get emergency contacts for a specific route"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM emergency_contacts 
                    WHERE route_id = ?
                    ORDER BY facility_type, distance_from_route
                """, (route_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"Error getting emergency contacts: {e}")
            return []

    def get_emergency_contacts_by_type(self, route_id: str, facility_type: str) -> List[Dict]:
        """Get emergency contacts of specific type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM emergency_contacts 
                    WHERE route_id = ? AND facility_type = ?
                    ORDER BY distance_from_route, rating DESC
                """, (route_id, facility_type))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"Error getting emergency contacts by type: {e}")
            return []

    def get_emergency_statistics(self, route_id: str) -> Dict:
        """Get emergency preparedness statistics for a route"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Count facilities by type
                cursor.execute("""
                    SELECT facility_type, COUNT(*) as count
                    FROM emergency_contacts 
                    WHERE route_id = ?
                    GROUP BY facility_type
                """, (route_id,))
                
                facility_counts = {row['facility_type']: row['count'] for row in cursor.fetchall()}
                
                # Calculate preparedness score
                preparedness_score = self._calculate_emergency_preparedness_score(facility_counts)
                
                # Get closest facilities
                cursor.execute("""
                    SELECT facility_type, facility_name, distance_from_route, formatted_phone_number
                    FROM emergency_contacts 
                    WHERE route_id = ?
                    ORDER BY distance_from_route
                    LIMIT 5
                """, (route_id,))
                
                closest_facilities = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'facility_counts': facility_counts,
                    'preparedness_score': preparedness_score,
                    'closest_facilities': closest_facilities,
                    'total_facilities': sum(facility_counts.values()),
                    'has_medical': facility_counts.get('hospital', 0) > 0,
                    'has_police': facility_counts.get('police', 0) > 0,
                    'has_fire': facility_counts.get('fire_station', 0) > 0
                }
                
        except Exception as e:
            print(f"Error getting emergency statistics: {e}")
            return {}

    def _calculate_emergency_preparedness_score(self, facility_counts: Dict) -> int:
        """Calculate emergency preparedness score based on available facilities"""
        score = 0
        
        # Critical facilities (higher weight)
        if facility_counts.get('hospital', 0) > 0:
            score += 30
        if facility_counts.get('police', 0) > 0:
            score += 25
        if facility_counts.get('fire_station', 0) > 0:
            score += 25
        
        # Additional facilities
        if facility_counts.get('emergency_clinic', 0) > 0:
            score += 15
        if facility_counts.get('ambulance', 0) > 0:
            score += 5
        
        return min(100, score)
    def get_route_highways(self, route_id: str) -> List[Dict]:
        """Get highway information for route"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM route_highways WHERE route_id = ?", (route_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting route highways: {e}")
            return []

    def get_route_terrain(self, route_id: str) -> Optional[Dict]:
        """Get terrain classification for route"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM route_terrain WHERE route_id = ? LIMIT 1", (route_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Error getting route terrain: {e}")
            return None

    def get_enhanced_route_overview_data(self, route_id: str) -> Dict[str, Any]:
        """Get all data needed for enhanced route overview"""
        try:
            # Get basic route info
            route = self.get_route(route_id)
            if not route:
                return {}
            
            # Get highways
            highways = self.get_route_highways(route_id)
            
            # Get terrain
            terrain = self.get_route_terrain(route_id)
            
            # Get route statistics
            route_points = self.get_route_points(route_id)
            sharp_turns = self.get_sharp_turns(route_id)
            pois = {
                'hospitals': self.get_pois_by_type(route_id, 'hospital'),
                'gas_stations': self.get_pois_by_type(route_id, 'gas_station'),
                'schools': self.get_pois_by_type(route_id, 'school'),
                'restaurants': self.get_pois_by_type(route_id, 'restaurant'),
                'police': self.get_pois_by_type(route_id, 'police'),
                'fire_stations': self.get_pois_by_type(route_id, 'fire_station')
            }
            
            return {
                'route_info': route,
                'highways': highways,
                'terrain': terrain,
                'route_points': route_points,
                'sharp_turns': sharp_turns,
                'pois': pois,
                'statistics': {
                    'total_points': len(route_points),
                    'total_sharp_turns': len(sharp_turns),
                    'critical_turns': len([t for t in sharp_turns if t.get('angle', 0) >= 70]),
                    'total_pois': sum(len(poi_list) for poi_list in pois.values()),
                    'total_highways': len(highways)
                }
            }
            
        except Exception as e:
            print(f"Error getting enhanced route overview data: {e}")
            return {}
    # Enhanced POI database methods for db_manager.py
    # Add these methods to your DatabaseManager class

    def get_enhanced_pois_by_type(self, route_id: str, poi_type: str) -> List[Dict]:
        """Get enhanced POIs with additional contact and location details"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Enhanced query to get all POI data including phone numbers
                cursor.execute("""
                    SELECT 
                        name,
                        latitude,
                        longitude,
                        address,
                        phone_number,
                        place_id,
                        rating,
                        additional_info,
                        distance_from_route
                    FROM pois 
                    WHERE route_id = ? AND poi_type = ?
                    ORDER BY 
                        CASE 
                            WHEN latitude != 0 AND longitude != 0 THEN 0 
                            ELSE 1 
                        END,
                        rating DESC,
                        name
                """, (route_id, poi_type))
                
                pois = []
                for row in cursor.fetchall():
                    poi_dict = dict(row)
                    
                    # Parse additional_info if it exists
                    if poi_dict.get('additional_info'):
                        try:
                            additional_data = json.loads(poi_dict['additional_info'])
                            # Merge additional data with main POI data
                            poi_dict.update(additional_data)
                        except:
                            pass
                    
                    pois.append(poi_dict)
                
                return pois
                
        except Exception as e:
            print(f"Error getting enhanced POIs: {e}")
            return []

    def get_poi_with_contact_info(self, route_id: str, poi_type: str) -> List[Dict]:
        """Get POIs with contact information prioritized"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # First try to get from emergency_contacts table (better data)
                cursor.execute("""
                    SELECT 
                        facility_name as name,
                        latitude,
                        longitude,
                        formatted_address as address,
                        formatted_phone_number as phone_number,
                        international_phone_number,
                        website,
                        rating,
                        place_id,
                        distance_from_route
                    FROM emergency_contacts 
                    WHERE route_id = ? AND facility_type = ?
                    ORDER BY rating DESC, distance_from_route ASC
                """, (route_id, poi_type))
                
                emergency_contacts = [dict(row) for row in cursor.fetchall()]
                
                if emergency_contacts:
                    return emergency_contacts
                
                # Fallback to regular POIs table
                return self.get_enhanced_pois_by_type(route_id, poi_type)
                
        except Exception as e:
            print(f"Error getting POI contact info: {e}")
            return self.get_enhanced_pois_by_type(route_id, poi_type)
    def get_complete_route_data_for_map(self, route_id: str) -> Dict[str, Any]:
        """Get all route data optimized for map display"""
        try:
            result = {
                'route_info': self.get_route(route_id),
                'route_points': self.get_route_points(route_id),
                'sharp_turns': self.get_sharp_turns(route_id),
                'pois_by_type': {},
                'network_coverage': self.get_network_coverage(route_id),
                'emergency_contacts': self.get_emergency_contacts(route_id),
                'traffic_data': [],
                'stored_images': self.get_stored_images(route_id)
            }
            
            # Get POIs by type with GPS coordinates
            poi_types = ['hospital', 'gas_station', 'school', 'restaurant', 'police', 'fire_station']
            for poi_type in poi_types:
                pois = self.get_enhanced_pois_by_type(route_id, poi_type)
                # Filter only POIs with valid GPS coordinates
                valid_pois = [
                    poi for poi in pois 
                    if poi.get('latitude', 0) != 0 and poi.get('longitude', 0) != 0
                ]
                result['pois_by_type'][poi_type] = valid_pois
            
            # Get traffic data
            try:
                import sqlite3
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM traffic_data WHERE route_id = ?", (route_id,))
                    result['traffic_data'] = [dict(row) for row in cursor.fetchall()]
            except Exception as e:
                print(f"Error getting traffic data: {e}")
                result['traffic_data'] = []
            
            return result
            
        except Exception as e:
            print(f"Error getting complete route data: {e}")
            return {}

    def get_map_markers_data(self, route_id: str) -> Dict[str, Any]:
        """Get optimized marker data for map display"""
        try:
            markers = {
                'pois': {},
                'sharp_turns': [],
                'network_issues': [],
                'emergency_services': [],
                'traffic_incidents': [],
                'environmental_risks': []
            }
            
            # Get POIs with valid coordinates
            poi_types = ['hospital', 'gas_station', 'school', 'restaurant', 'police', 'fire_station']
            for poi_type in poi_types:
                pois = self.get_enhanced_pois_by_type(route_id, poi_type)
                valid_pois = []
                for poi in pois:
                    if poi.get('latitude', 0) != 0 and poi.get('longitude', 0) != 0:
                        # Add map-specific data
                        poi['marker_color'] = self._get_poi_marker_color(poi_type)
                        poi['marker_icon'] = self._get_poi_marker_icon(poi_type)
                        valid_pois.append(poi)
                markers['pois'][poi_type] = valid_pois
            
            # Get sharp turns
            sharp_turns = self.get_sharp_turns(route_id)
            for turn in sharp_turns:
                turn['marker_color'] = self._get_danger_color(turn.get('danger_level', 'LOW'))
                turn['marker_icon'] = '⚠'
            markers['sharp_turns'] = sharp_turns
            
            # Get network issues
            network_coverage = self.get_network_coverage(route_id)
            network_issues = []
            for point in network_coverage:
                if point.get('is_dead_zone') or point.get('is_poor_coverage'):
                    point['marker_color'] = '#e83e8c' if point.get('is_dead_zone') else '#ffc107'
                    point['marker_icon'] = '📵' if point.get('is_dead_zone') else '📶'
                    network_issues.append(point)
            markers['network_issues'] = network_issues
            
            # Get emergency services
            emergency_contacts = self.get_emergency_contacts(route_id)
            for contact in emergency_contacts:
                contact['marker_color'] = self._get_emergency_color(contact.get('facility_type', ''))
                contact['marker_icon'] = self._get_emergency_icon(contact.get('facility_type', ''))
            markers['emergency_services'] = emergency_contacts
            
            # Get traffic incidents
            try:
                import sqlite3
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT * FROM traffic_data 
                        WHERE route_id = ? AND congestion_level IN ('HEAVY', 'MODERATE')
                    """, (route_id,))
                    traffic_incidents = []
                    for row in cursor.fetchall():
                        incident = dict(row)
                        incident['marker_color'] = self._get_traffic_color(incident.get('congestion_level', ''))
                        incident['marker_icon'] = '🚦'
                        traffic_incidents.append(incident)
                    markers['traffic_incidents'] = traffic_incidents
            except:
                markers['traffic_incidents'] = []
            
            return markers
            
        except Exception as e:
            print(f"Error getting map markers data: {e}")
            return {}

    def _get_poi_marker_color(self, poi_type: str) -> str:
        """Get marker color for POI type"""
        colors = {
            'hospital': '#dc3545',
            'gas_station': '#28a745',
            'school': '#ffc107',
            'restaurant': '#17a2b8',
            'police': '#0052a3',
            'fire_station': '#fd7e14'
        }
        return colors.get(poi_type, '#6c757d')

    def _get_poi_marker_icon(self, poi_type: str) -> str:
        """Get marker icon for POI type"""
        icons = {
            'hospital': '🏥',
            'gas_station': '⛽',
            'school': '🏫',
            'restaurant': '🍽',
            'police': '👮',
            'fire_station': '🚒'
        }
        return icons.get(poi_type, '📍')

    def _get_danger_color(self, danger_level: str) -> str:
        """Get color for danger level"""
        colors = {
            'CRITICAL': '#dc3545',
            'EXTREME': '#fd7e14',
            'HIGH': '#ffc107',
            'MEDIUM': '#28a745',
            'LOW': '#17a2b8'
        }
        return colors.get(danger_level, '#6c757d')

    def _get_emergency_color(self, facility_type: str) -> str:
        """Get color for emergency facility type"""
        colors = {
            'hospital': '#dc3545',
            'police': '#0052a3',
            'fire_station': '#fd7e14',
            'ambulance': '#dc3545',
            'emergency_clinic': '#fd7e14'
        }
        return colors.get(facility_type, '#6f42c1')

    def _get_emergency_icon(self, facility_type: str) -> str:
        """Get icon for emergency facility type"""
        icons = {
            'hospital': '🏥',
            'police': '👮',
            'fire_station': '🚒',
            'ambulance': '🚑',
            'emergency_clinic': '⚕'
        }
        return icons.get(facility_type, '🚨')

    def _get_traffic_color(self, congestion_level: str) -> str:
        """Get color for traffic congestion level"""
        colors = {
            'HEAVY': '#dc3545',
            'MODERATE': '#ffc107',
            'LIGHT': '#28a745',
            'FREE_FLOW': '#17a2b8'
        }
        return colors.get(congestion_level, '#6c757d')

    def get_route_bounds(self, route_id: str) -> Optional[Dict]:
        """Get route bounding box for map initialization"""
        try:
            route_points = self.get_route_points(route_id)
            if not route_points:
                return None
            
            latitudes = [p['latitude'] for p in route_points]
            longitudes = [p['longitude'] for p in route_points]
            
            return {
                'north': max(latitudes),
                'south': min(latitudes),
                'east': max(longitudes),
                'west': min(longitudes),
                'center': {
                    'lat': sum(latitudes) / len(latitudes),
                    'lng': sum(longitudes) / len(longitudes)
                }
            }
            
        except Exception as e:
            print(f"Error getting route bounds: {e}")
            return None

    def get_optimized_route_points(self, route_id: str, max_points: int = 500) -> List[Dict]:
        """Get optimized route points for animation (sample if too many)"""
        try:
            route_points = self.get_route_points(route_id)
            
            if not route_points:
                return []
            
            total_points = len(route_points)
            if total_points <= max_points:
                return route_points
            
            # Sample every nth point to reduce to max_points
            step = total_points // max_points
            optimized_points = route_points[::step]
            
            # Always include first and last points
            if optimized_points[0] != route_points[0]:
                optimized_points.insert(0, route_points[0])
            if optimized_points[-1] != route_points[-1]:
                optimized_points.append(route_points[-1])
            
            return optimized_points
            
        except Exception as e:
            print(f"Error getting optimized route points: {e}")
            return []

    def store_route_analytics(self, route_id: str, analytics_data: Dict) -> bool:
        """Store route analytics data for map performance tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create analytics table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS route_analytics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        route_id TEXT NOT NULL,
                        map_loads INTEGER DEFAULT 0,
                        animation_runs INTEGER DEFAULT 0,
                        markers_displayed INTEGER DEFAULT 0,
                        user_interactions INTEGER DEFAULT 0,
                        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        performance_data TEXT,
                        FOREIGN KEY (route_id) REFERENCES routes (id)
                    )
                """)
                
                # Insert or update analytics
                cursor.execute("""
                    INSERT OR REPLACE INTO route_analytics 
                    (route_id, map_loads, animation_runs, markers_displayed, 
                    user_interactions, performance_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    route_id,
                    analytics_data.get('map_loads', 0),
                    analytics_data.get('animation_runs', 0),
                    analytics_data.get('markers_displayed', 0),
                    analytics_data.get('user_interactions', 0),
                    json.dumps(analytics_data.get('performance_data', {}))
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error storing route analytics: {e}")
            return False

    