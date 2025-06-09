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
            
            conn.commit()
            print("✅ Database initialized successfully")
    
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