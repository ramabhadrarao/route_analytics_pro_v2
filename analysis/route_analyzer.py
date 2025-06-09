# analysis/route_analyzer.py - Complete Route Analysis Engine
# Purpose: Analyze CSV routes, fetch data from APIs, store images and data in database
# Dependencies: googlemaps, requests, PIL, io
# Author: Route Analysis System
# Created: 2024
import sys
import csv
import os
import json
import uuid
import datetime
import math
import time
import requests
from typing import List, Dict, Tuple, Optional
import googlemaps
from PIL import Image
import io
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from translation_before_db import TextTranslator
class RouteAnalyzer:
    """Complete route analysis with API integration and data storage"""
    
    def __init__(self, api_tracker):
        self.api_tracker = api_tracker
        self.db_manager = api_tracker.db_manager
        
        # Initialize API clients
        self.google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        self.openweather_api_key = os.environ.get('OPENWEATHER_API_KEY')
        self.text_translator = TextTranslator(preferred_method='googletrans')
        if self.google_api_key:
            self.gmaps = googlemaps.Client(key=self.google_api_key)
        else:
            self.gmaps = None
            print("⚠️ Google Maps API key not configured")
    
    def analyze_csv_route(self, csv_file_path: str, user_id: str) -> Optional[str]:
        """
        Complete route analysis from CSV file
        Returns route_id if successful, None if failed
        """
        try:
            print(f"🚀 Starting route analysis for {csv_file_path}")
            
            # Generate unique route ID
            route_id = str(uuid.uuid4())
            filename = os.path.basename(csv_file_path)
            
            # Step 1: Read CSV coordinates
            route_points = self._read_csv_coordinates(csv_file_path)
            if not route_points:
                print("❌ No valid coordinates found in CSV")
                return None
            
            print(f"📍 Loaded {len(route_points)} GPS coordinates")
            
            # Step 2: Get route information from Google Maps
            route_info = self._get_google_route_info(route_points[0], route_points[-1])
            
            # Step 3: Create route record in database
            success = self.db_manager.create_route(
                route_id=route_id,
                user_id=user_id,
                filename=filename,
                from_address=route_info.get('start_address'),
                to_address=route_info.get('end_address'),
                distance=route_info.get('distance'),
                duration=route_info.get('duration'),
                total_points=len(route_points)
            )
            
            if not success:
                print("❌ Failed to create route record")
                return None
            
            # Step 4: Store route points
            self.db_manager.store_route_points(route_id, route_points)
            
            # Step 5: Analyze sharp turns
            print("🔄 Analyzing sharp turns...")
            sharp_turns = self._analyze_sharp_turns(route_points)
            if sharp_turns:
                self.db_manager.store_sharp_turns(route_id, sharp_turns)
                # Store street view and satellite images for critical turns
                self._store_turn_images(route_id, sharp_turns)
            
            # Step 6: Find Points of Interest
            print("🔍 Finding Points of Interest...")
            self._analyze_and_store_pois(route_id, route_points)
            
            # Step 7: Get weather data
            print("🌤️ Analyzing weather conditions...")
            weather_data = self._get_weather_data(route_points)
            if weather_data:
                self.db_manager.store_weather_data(route_id, weather_data)
            
            # Step 8: Analyze network coverage
            print("📡 Analyzing network coverage...")
            coverage_data = self._analyze_network_coverage(route_points)
            if coverage_data:
                self.db_manager.store_network_coverage(route_id, coverage_data)
            
            # Step 9: Get elevation data
            print("🏔️ Getting elevation data...")
            elevation_data = self._get_elevation_data(route_points)
            if elevation_data:
                self._store_elevation_data(route_id, elevation_data)
            
            # Step 10: Generate comprehensive map
            print("🗺️ Generating comprehensive route map...")
            self._generate_and_store_route_map(route_id, route_points, sharp_turns)
            
            print(f"✅ Route analysis completed successfully. Route ID: {route_id}")
            return route_id
            
        except Exception as e:
            print(f"❌ Route analysis failed: {e}")
            return None
        finally:
            # Cleanup uploaded file
            try:
                os.remove(csv_file_path)
            except:
                pass
    
    def _read_csv_coordinates(self, csv_file_path: str) -> List[List[float]]:
        """Read and validate GPS coordinates from CSV file"""
        coordinates = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row_num, row in enumerate(reader):
                    if len(row) >= 2:
                        try:
                            lat = float(row[0])
                            lng = float(row[1])
                            
                            # Validate coordinates
                            if -90 <= lat <= 90 and -180 <= lng <= 180:
                                coordinates.append([lat, lng])
                            
                        except (ValueError, IndexError):
                            continue
            
            return coordinates
            
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return []
    
    def _get_google_route_info(self, start_point: List[float], end_point: List[float]) -> Dict:
        """Get route information from Google Directions API"""
        if not self.gmaps:
            return {'error': 'Google Maps not configured'}
        
        try:
            start_time = time.time()
            
            # Call Google Directions API
            directions_result = self.gmaps.directions(
                origin=start_point,
                destination=end_point,
                mode="driving",
                alternatives=False,
                language='en'
            )
            
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'google_directions', 
                '/directions/json',
                200 if directions_result else 400,
                response_time,
                bool(directions_result)
            )
            
            if directions_result:
                route = directions_result[0]
                leg = route['legs'][0]
                
                return {
                    'start_address': leg.get('start_address', 'Unknown'),
                    'end_address': leg.get('end_address', 'Unknown'),
                    'distance': leg.get('distance', {}).get('text', 'Unknown'),
                    'duration': leg.get('duration', {}).get('text', 'Unknown'),
                    'polyline': route.get('overview_polyline', {}).get('points', '')
                }
            
            return {'error': 'No route found'}
            
        except Exception as e:
            print(f"Google Directions API error: {e}")
            self.api_tracker.log_api_call(
                'google_directions', 
                '/directions/json',
                500,
                0,
                False,
                str(e)
            )
            return {'error': str(e)}
    
    def _analyze_sharp_turns(self, route_points: List[List[float]]) -> List[Dict]:
        """Analyze route for sharp turns and dangerous angles"""
        if len(route_points) < 3:
            return []
        
        sharp_turns = []
        
        # Sample points to avoid too many calculations
        step = max(1, len(route_points) // 100)
        sampled_points = route_points[::step]
        
        for i in range(1, len(sampled_points) - 1):
            try:
                p1 = sampled_points[i-1]
                p2 = sampled_points[i]
                p3 = sampled_points[i+1]
                
                # Calculate turn angle
                angle = self._calculate_turn_angle(p1, p2, p3)
                
                # Consider turns >= 45 degrees as significant
                if angle >= 45:
                    classification = self._classify_turn(angle)
                    danger_level = self._get_danger_level(angle)
                    recommended_speed = self._get_recommended_speed(angle)
                    
                    sharp_turns.append({
                        'lat': p2[0],
                        'lng': p2[1],
                        'angle': round(angle, 2),
                        'classification': classification,
                        'danger_level': danger_level,
                        'recommended_speed': recommended_speed,
                        'point_index': i * step
                    })
                    
            except Exception as e:
                continue
        
        # Sort by angle (most dangerous first)
        sharp_turns.sort(key=lambda x: x['angle'], reverse=True)
        
        print(f"📐 Found {len(sharp_turns)} sharp turns")
        return sharp_turns[:50]  # Limit to top 50
    
    def _calculate_turn_angle(self, p1: List[float], p2: List[float], p3: List[float]) -> float:
        """Calculate turn angle between three GPS points"""
        # Calculate bearings
        bearing1 = self._calculate_bearing(p1, p2)
        bearing2 = self._calculate_bearing(p2, p3)
        
        # Calculate turn angle
        angle = abs(bearing2 - bearing1)
        if angle > 180:
            angle = 360 - angle
            
        return angle
    
    def _calculate_bearing(self, point1: List[float], point2: List[float]) -> float:
        """Calculate bearing between two GPS points"""
        lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
        lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])
        
        dlon = lon2 - lon1
        
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def _classify_turn(self, angle: float) -> str:
        """Classify turn based on angle"""
        if angle >= 90:
            return "EXTREME BLIND SPOT"
        elif angle >= 80:
            return "HIGH-RISK BLIND SPOT"
        elif angle >= 70:
            return "BLIND SPOT"
        elif angle >= 60:
            return "HIGH-ANGLE TURN"
        else:
            return "SHARP TURN"
    
    def _get_danger_level(self, angle: float) -> str:
        """Get danger level for turn"""
        if angle >= 90:
            return "CRITICAL"
        elif angle >= 80:
            return "EXTREME"
        elif angle >= 70:
            return "HIGH"
        elif angle >= 60:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_recommended_speed(self, angle: float) -> int:
        """Get recommended speed for turn"""
        if angle >= 90:
            return 15
        elif angle >= 80:
            return 20
        elif angle >= 70:
            return 25
        elif angle >= 60:
            return 30
        else:
            return 40
    
    def _store_turn_images(self, route_id: str, sharp_turns: List[Dict]):
        """Store street view and satellite images for critical turns"""
        if not self.google_api_key:
            return
        
        # Store images for the most critical turns (top 10)
        critical_turns = [turn for turn in sharp_turns if turn['angle'] >= 70][:10]
        
        for i, turn in enumerate(critical_turns):
            try:
                lat, lng = turn['lat'], turn['lng']
                
                # Store street view image
                self._store_street_view_image(route_id, lat, lng, f"turn_{i+1}")
                
                # Store satellite image
                self._store_satellite_image(route_id, lat, lng, f"turn_{i+1}")
                
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                print(f"Error storing images for turn {i+1}: {e}")
    
    def _store_street_view_image(self, route_id: str, lat: float, lng: float, 
                                identifier: str) -> bool:
        """Download and store street view image"""
        try:
            start_time = time.time()
            
            # Try multiple headings for best view
            for heading in [0, 90, 180, 270]:
                url = "https://maps.googleapis.com/maps/api/streetview"
                params = {
                    'size': '640x640',
                    'location': f'{lat},{lng}',
                    'heading': heading,
                    'pitch': 5,
                    'fov': 90,
                    'key': self.google_api_key
                }
                
                response = requests.get(url, params=params, timeout=15)
                response_time = time.time() - start_time
                
                # Log API usage
                self.api_tracker.log_api_call(
                    'google_streetview',
                    '/streetview',
                    response.status_code,
                    response_time,
                    response.status_code == 200
                )
                
                if response.status_code == 200 and len(response.content) > 3000:
                    # Valid street view image
                    filename = f"streetview_{route_id}_{identifier}_h{heading}.jpg"
                    file_path = os.path.join('images', 'street_view', filename)
                    
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Store in database
                    self.db_manager.store_image(
                        route_id=route_id,
                        image_type='street_view',
                        filename=filename,
                        file_path=file_path,
                        latitude=lat,
                        longitude=lng,
                        file_size=len(response.content)
                    )
                    
                    print(f"✅ Stored street view: {filename}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error storing street view image: {e}")
            return False
    
    def _store_satellite_image(self, route_id: str, lat: float, lng: float, 
                              identifier: str) -> bool:
        """Download and store satellite image"""
        try:
            start_time = time.time()
            
            url = "https://maps.googleapis.com/maps/api/staticmap"
            params = {
                'center': f'{lat},{lng}',
                'zoom': 18,
                'size': '640x640',
                'maptype': 'satellite',
                'markers': f'color:red|size:mid|{lat},{lng}',
                'key': self.google_api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'google_staticmap',
                '/staticmap',
                response.status_code,
                response_time,
                response.status_code == 200
            )
            
            if response.status_code == 200:
                filename = f"satellite_{route_id}_{identifier}.png"
                file_path = os.path.join('images', 'satellite', filename)
                
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                # Store in database
                self.db_manager.store_image(
                    route_id=route_id,
                    image_type='satellite',
                    filename=filename,
                    file_path=file_path,
                    latitude=lat,
                    longitude=lng,
                    file_size=len(response.content)
                )
                
                print(f"✅ Stored satellite image: {filename}")
                return True
                
        except Exception as e:
            print(f"Error storing satellite image: {e}")
            return False
        
        return False
    
    def _analyze_and_store_pois(self, route_id: str, route_points: List[List[float]]):
        """Find and store all types of POIs along the route"""
        if not self.gmaps:
            return
        
        # Sample points for POI search
        step = max(1, len(route_points) // 10)
        sampled_points = route_points[::step]
        
        poi_types = {
            'hospital': 'hospital',
            'gas_station': 'gas_station', 
            'school': 'school',
            'restaurant': 'restaurant',
            'police': 'police',
            'fire_station': 'fire_station'
        }
        
        for poi_type, google_type in poi_types.items():
            print(f"🔍 Searching for {poi_type}s...")
            pois_found = {}
            
            for point in sampled_points[:5]:  # Limit search points
                try:
                    places = self._search_nearby_places(point[0], point[1], google_type)
                    for place in places[:15]:  # Top 3 per location
                        name = place.get('name', 'Unknown')
                        vicinity = place.get('vicinity', 'Unknown location')
                        # Translate to English before storing
                        english_name = self.text_translator.translate_to_english(name)
                        english_vicinity = self.text_translator.translate_to_english(vicinity)
                        pois_found[english_name] = english_vicinity

                        
                except Exception as e:
                    print(f"Error searching {poi_type}: {e}")
            
            if pois_found:
                self.db_manager.store_pois(route_id, pois_found, poi_type)
                print(f"✅ Stored {len(pois_found)} {poi_type}s")
    
    def _search_nearby_places(self, lat: float, lng: float, place_type: str) -> List[Dict]:
        """Search for nearby places using Google Places API"""
        try:
            start_time = time.time()
            
            # Use googlemaps library
            places_result = self.gmaps.places_nearby(
                location=(lat, lng),
                radius=5000,
                type=place_type,
                language='en'
            )
            
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'google_places',
                '/place/nearbysearch/json',
                200 if places_result else 400,
                response_time,
                bool(places_result.get('results'))
            )
            
            return places_result.get('results', [])
            
        except Exception as e:
            print(f"Places API error: {e}")
            self.api_tracker.log_api_call(
                'google_places',
                '/place/nearbysearch/json',
                500,
                0,
                False,
                str(e)
            )
            return []
    
    def _get_weather_data(self, route_points: List[List[float]]) -> List[Dict]:
        """Get weather data for route points"""
        if not self.openweather_api_key:
            return []
        
        weather_data = []
        
        # Sample 10 points for weather
        step = max(1, len(route_points) // 10)
        sampled_points = route_points[::step]
        
        for i, point in enumerate(sampled_points[:10]):
            try:
                start_time = time.time()
                
                url = "http://api.openweathermap.org/data/2.5/weather"
                params = {
                    'lat': point[0],
                    'lon': point[1],
                    'appid': self.openweather_api_key,
                    'units': 'metric'
                }
                
                response = requests.get(url, params=params, timeout=10)
                response_time = time.time() - start_time
                
                # Log API usage
                self.api_tracker.log_api_call(
                    'openweather',
                    '/weather',
                    response.status_code,
                    response_time,
                    response.status_code == 200
                )
                
                if response.status_code == 200:
                    data = response.json()
                    weather_data.append({
                        'coordinates': {'lat': point[0], 'lng': point[1]},
                        'temp': data['main']['temp'],
                        'humidity': data['main']['humidity'],
                        'wind_speed': data.get('wind', {}).get('speed', 0),
                        'main': data['weather'][0]['main'],
                        'description': data['weather'][0]['description']
                    })
                
            except Exception as e:
                print(f"Weather API error for point {point}: {e}")
                continue
        
        print(f"🌤️ Retrieved weather data for {len(weather_data)} points")
        return weather_data
    
    def _analyze_network_coverage(self, route_points: List[List[float]]) -> List[Dict]:
        """Simulate network coverage analysis (placeholder for real implementation)"""
        coverage_data = []
        
        # Sample points for coverage analysis
        step = max(1, len(route_points) // 20)
        sampled_points = route_points[::step]
        
        for point in sampled_points[:20]:
            # Simulate coverage analysis (in real implementation, use cellular coverage APIs)
            import random
            random.seed(hash(f"{point[0]}{point[1]}"))
            
            signal_strength = random.randint(-120, -60)
            
            if signal_strength > -70:
                quality = 'excellent'
            elif signal_strength > -85:
                quality = 'good'
            elif signal_strength > -100:
                quality = 'fair'
            elif signal_strength > -110:
                quality = 'poor'
            else:
                quality = 'dead'
            
            coverage_data.append({
                'coordinates': {'lat': point[0], 'lng': point[1]},
                'coverage_quality': quality,
                'coverage_data': {
                    'signal_strength': signal_strength,
                    'network_type': '4G',
                    'technologies': ['LTE', 'GSM']
                }
            })
        
        print(f"📡 Analyzed network coverage for {len(coverage_data)} points")
        return coverage_data
    
    def _get_elevation_data(self, route_points: List[List[float]]) -> List[Dict]:
        """Get elevation data using Google Elevation API"""
        if not self.gmaps:
            return []
        
        try:
            # Sample points for elevation
            step = max(1, len(route_points) // 20)
            sampled_points = route_points[::step]
            
            start_time = time.time()
            
            # Call Google Elevation API
            elevation_result = self.gmaps.elevation(sampled_points[:20])
            
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'google_elevation',
                '/elevation/json',
                200 if elevation_result else 400,
                response_time,
                bool(elevation_result)
            )
            
            if elevation_result:
                print(f"🏔️ Retrieved elevation data for {len(elevation_result)} points")
                return elevation_result
            
        except Exception as e:
            print(f"Elevation API error: {e}")
            self.api_tracker.log_api_call(
                'google_elevation',
                '/elevation/json',
                500,
                0,
                False,
                str(e)
            )
        
        return []
    
    def _store_elevation_data(self, route_id: str, elevation_data: List[Dict]):
        """Store elevation data in database"""
        try:
            with self.db_manager.db_path as conn:
                cursor = conn.cursor()
                
                for data in elevation_data:
                    location = data.get('location', {})
                    cursor.execute("""
                        INSERT INTO elevation_data 
                        (route_id, latitude, longitude, elevation)
                        VALUES (?, ?, ?, ?)
                    """, (
                        route_id,
                        location.get('lat', 0),
                        location.get('lng', 0),
                        data.get('elevation', 0)
                    ))
                
                conn.commit()
                print(f"✅ Stored elevation data for {len(elevation_data)} points")
                
        except Exception as e:
            print(f"Error storing elevation data: {e}")
    
    def _generate_and_store_route_map(self, route_id: str, route_points: List[List[float]], 
                                     sharp_turns: List[Dict]):
        """Generate and store comprehensive route map"""
        if not self.google_api_key:
            return
        
        try:
            # Create route path
            path_points = route_points[::max(1, len(route_points)//50)]  # Sample for URL limits
            path_string = '|'.join([f"{point[0]},{point[1]}" for point in path_points])
            
            # Add markers for critical turns
            markers = []
            for i, turn in enumerate(sharp_turns[:10]):  # Limit markers
                color = 'red' if turn['angle'] >= 80 else 'orange' if turn['angle'] >= 70 else 'yellow'
                markers.append(f"color:{color}|size:mid|{turn['lat']},{turn['lng']}")
            
            markers_string = '&'.join([f"markers={marker}" for marker in markers])
            
            # Generate map URL
            center_lat = sum(point[0] for point in route_points) / len(route_points)
            center_lng = sum(point[1] for point in route_points) / len(route_points)
            
            url = "https://maps.googleapis.com/maps/api/staticmap"
            params = {
                'center': f'{center_lat},{center_lng}',
                'zoom': 10,
                'size': '800x600',
                'maptype': 'roadmap',
                'path': f'color:0x0000ff|weight:3|{path_string}',
                'key': self.google_api_key
            }
            
            # Add markers to URL
            if markers:
                url += '&' + markers_string
            
            start_time = time.time()
            response = requests.get(url, params=params, timeout=30)
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'google_staticmap',
                '/staticmap',
                response.status_code,
                response_time,
                response.status_code == 200
            )
            
            if response.status_code == 200:
                filename = f"route_map_{route_id}.png"
                file_path = os.path.join('images', 'maps', filename)
                
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                # Store in database
                self.db_manager.store_image(
                    route_id=route_id,
                    image_type='route_map',
                    filename=filename,
                    file_path=file_path,
                    file_size=len(response.content)
                )
                
                print(f"✅ Stored comprehensive route map: {filename}")
                
        except Exception as e:
            print(f"Error generating route map: {e}")