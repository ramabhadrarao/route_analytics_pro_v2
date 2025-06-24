# utils/map_enhancer.py - Enhanced Mapping and Road Analysis
# Purpose: Advanced mapping features, highway detection, terrain classification
# Dependencies: googlemaps, requests, math
# Author: Enhanced Route Analysis System
# Created: 2024

import os
import time
import math
import requests
from typing import List, Dict, Any, Optional
import googlemaps

class MapEnhancer:
    """Enhanced mapping with detailed markers and road analysis"""
    
    def __init__(self, api_tracker):
        self.api_tracker = api_tracker
        self.google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        
        if self.google_api_key:
            self.gmaps = googlemaps.Client(key=self.google_api_key)
        else:
            self.gmaps = None
            
        # Highway classification patterns
        self.highway_patterns = {
            'NH': ['National Highway', 'NH-', 'NH ', 'National Hwy'],
            'SH': ['State Highway', 'SH-', 'SH ', 'State Hwy'],
            'MDR': ['Major District Road', 'MDR-', 'MDR '],
            'ODR': ['Other District Road', 'ODR-', 'ODR '],
            'VR': ['Village Road', 'VR-', 'Village Road']
        }
        
        print("🗺️ Map Enhancer initialized")
    
    def detect_highway_segments(self, route_points: List[List[float]]) -> List[Dict]:
        """Detect and classify highway segments along the route"""
        if not self.gmaps:
            return []
        
        highways = []
        processed_roads = set()  # FIXED: Store highway names (strings) instead of dicts
        
        try:
            # Sample points for highway detection (every 5km approximately)
            step = max(1, len(route_points) // 20)
            sampled_points = route_points[::step]
            
            print(f"🛣️ Detecting highways along {len(sampled_points)} route segments...")
            
            for i in range(len(sampled_points) - 1):
                try:
                    start_point = sampled_points[i]
                    end_point = sampled_points[i + 1]
                    
                    # Get detailed directions for this segment
                    start_time = time.time()
                    
                    directions_result = self.gmaps.directions(
                        origin=start_point,
                        destination=end_point,
                        mode="driving",
                        alternatives=True,
                        language='en'
                    )
                    
                    response_time = time.time() - start_time
                    
                    # Log API usage
                    self.api_tracker.log_api_call(
                        'google_directions_highways',
                        '/directions/json',
                        200 if directions_result else 400,
                        response_time,
                        bool(directions_result)
                    )
                    
                    if directions_result:
                        # Process each route alternative
                        for route in directions_result:
                            for leg in route['legs']:
                                for step in leg['steps']:
                                    # Extract road information from step instructions
                                    instruction = step.get('html_instructions', '')
                                    
                                    # Look for highway mentions in instructions
                                    detected_highway = self._extract_highway_from_text(instruction)
                                    # FIXED: Check highway name (string) instead of dict
                                    if detected_highway and detected_highway['name'] not in processed_roads:
                                        
                                        highway_info = {
                                            'highway_name': detected_highway['name'],
                                            'highway_type': detected_highway['type'],
                                            'start_latitude': start_point[0],
                                            'start_longitude': start_point[1],
                                            'end_latitude': end_point[0],
                                            'end_longitude': end_point[1],
                                            'length_km': self._calculate_distance(start_point, end_point) / 1000,
                                            'instruction_context': instruction[:100]
                                        }
                                        
                                        highways.append(highway_info)
                                        processed_roads.add(detected_highway['name'])  # FIXED: Add string, not dict
                                        
                                        print(f"   🛣️ Found: {detected_highway['name']} ({detected_highway['type']})")
                    
                    time.sleep(0.2)  # Rate limiting
                    
                except Exception as e:
                    print(f"   Error analyzing segment {i}: {e}")
                    continue
            
            # Also try to get highways using Roads API
            roads_highways = self._detect_highways_via_roads_api(route_points)
            
            # Merge and deduplicate
            all_highways = highways + roads_highways
            unique_highways = self._deduplicate_highways(all_highways)
            
            print(f"✅ Detected {len(unique_highways)} unique highways")
            return unique_highways
            
        except Exception as e:
            print(f"❌ Highway detection failed: {e}")
            return []
    
    def _extract_highway_from_text(self, text: str) -> Optional[Dict]:
        """Extract highway information from instruction text"""
        text_upper = text.upper()
        
        for highway_type, patterns in self.highway_patterns.items():
            for pattern in patterns:
                if pattern.upper() in text_upper:
                    # Try to extract highway number using multiple approaches
                    import re
                    
                    # Approach 1: Look for exact pattern matches
                    exact_patterns = [
                        rf"{highway_type}-(\d+)",
                        rf"{highway_type}\s+(\d+)",
                        rf"{highway_type}(\d+)"
                    ]
                    
                    for exact_pattern in exact_patterns:
                        match = re.search(exact_pattern, text, re.IGNORECASE)
                        if match:
                            highway_number = match.group(1)
                            highway_name = f"{highway_type}-{highway_number}"
                            
                            return {
                                'name': highway_name,
                                'type': self._get_highway_type_description(highway_type),
                                'number': highway_number
                            }
                    
                    # Approach 2: Look for general number after highway mention
                    # Find the position of the highway type in text
                    highway_pos = text_upper.find(pattern.upper())
                    if highway_pos != -1:
                        # Look for numbers in the next 20 characters
                        search_text = text[highway_pos:highway_pos + 20]
                        number_match = re.search(r'(\d+)', search_text)
                        if number_match:
                            highway_number = number_match.group(1)
                            highway_name = f"{highway_type}-{highway_number}"
                            
                            return {
                                'name': highway_name,
                                'type': self._get_highway_type_description(highway_type),
                                'number': highway_number
                            }
        
        return None
    
    def _get_highway_type_description(self, highway_type: str) -> str:
        """Get full description of highway type"""
        descriptions = {
            'NH': 'National Highway',
            'SH': 'State Highway', 
            'MDR': 'Major District Road',
            'ODR': 'Other District Road',
            'VR': 'Village Road'
        }
        return descriptions.get(highway_type, 'Unknown')
    
    def _detect_highways_via_roads_api(self, route_points: List[List[float]]) -> List[Dict]:
        """Use Google Roads API to detect highway segments"""
        if not self.gmaps:
            return []
        
        highways = []
        
        try:
            # Sample fewer points for Roads API (has stricter limits)
            step = max(1, len(route_points) // 10)
            sampled_points = route_points[::step]
            
            # Process in batches of 10 points (Roads API limit)
            batch_size = 10
            for i in range(0, len(sampled_points), batch_size):
                batch_points = sampled_points[i:i + batch_size]
                
                start_time = time.time()
                
                # Snap to roads
                snapped_roads = self.gmaps.snap_to_roads(batch_points, interpolate=True)
                
                response_time = time.time() - start_time
                
                # Log API usage
                self.api_tracker.log_api_call(
                    'google_roads_highways',
                    '/roads/snapToRoads',
                    200 if snapped_roads else 400,
                    response_time,
                    bool(snapped_roads)
                )
                
                if snapped_roads:
                    # Get place IDs and try to get road names
                    for road_point in snapped_roads:
                        place_id = road_point.get('placeId')
                        if place_id:
                            road_details = self._get_road_details_from_place_id(place_id)
                            if road_details and 'highway' in str(road_details).lower():
                                highways.append(road_details)
                
                time.sleep(0.5)  # Rate limiting for Roads API
                
        except Exception as e:
            print(f"Roads API highway detection error: {e}")
        
        return highways
    
    def _get_road_details_from_place_id(self, place_id: str) -> Optional[Dict]:
        """Get road details from Google Place ID"""
        if not self.gmaps:
            return None
        
        try:
            start_time = time.time()
            
            # FIXED: Remove 'types' from fields list as it's invalid
            place_details = self.gmaps.place(
                place_id=place_id,
                fields=['name', 'formatted_address', 'geometry'],  # REMOVED 'types'
                language='en'
            )
            
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'google_place_details_roads',
                '/place/details/json',
                200 if place_details else 400,
                response_time,
                bool(place_details)
            )
            
            if place_details and 'result' in place_details:
                result = place_details['result']
                name = result.get('name', '')
                
                # Check if this looks like a highway
                highway_info = self._extract_highway_from_text(name)
                if highway_info:
                    location = result.get('geometry', {}).get('location', {})
                    return {
                        'highway_name': highway_info['name'],
                        'highway_type': highway_info['type'],
                        'start_latitude': location.get('lat', 0),
                        'start_longitude': location.get('lng', 0),
                        'place_id': place_id,
                        'formatted_address': result.get('formatted_address', '')
                    }
            
        except Exception as e:
            print(f"Error getting road details: {e}")
        
        return None
    
    def _deduplicate_highways(self, highways: List[Dict]) -> List[Dict]:
        """Remove duplicate highway entries"""
        seen_highways = set()
        unique_highways = []
        
        for highway in highways:
            highway_key = highway.get('highway_name', 'Unknown')  # FIXED: Use .get() for safety
            if highway_key not in seen_highways:
                seen_highways.add(highway_key)
                unique_highways.append(highway)
        
        return unique_highways
    
    def classify_terrain_zones(self, route_points: List[List[float]], 
                              pois: Dict, elevation_data: List[Dict]) -> Dict:
        """Analyze terrain based on multiple factors"""
        
        print("🏞️ Classifying terrain along route...")
        
        terrain_analysis = {
            'primary_terrain': 'Mixed',
            'terrain_breakdown': {},
            'urban_density_score': 0,
            'elevation_variance': 0,
            'terrain_confidence': 0,
            'zone_details': []
        }
        
        try:
            # 1. Analyze elevation variance
            elevations = [point.get('elevation', 0) for point in elevation_data if point.get('elevation')]
            if elevations:
                elevation_variance = self._calculate_variance(elevations)
                terrain_analysis['elevation_variance'] = elevation_variance
                
                # Classify based on elevation
                if elevation_variance > 5000:  # High variance
                    elevation_terrain = 'Mountainous'
                elif elevation_variance > 1000:
                    elevation_terrain = 'Hilly'
                else:
                    elevation_terrain = 'Flat'
            else:
                elevation_terrain = 'Unknown'
            
            # 2. Analyze urban density based on POIs
            total_pois = sum(len(poi_list) for poi_list in pois.values())
            route_length_km = self._estimate_route_length(route_points)
            
            if route_length_km > 0:
                poi_density = total_pois / route_length_km
                
                if poi_density > 10:
                    urban_density = 'Urban Dense'
                    urban_score = 90
                elif poi_density > 5:
                    urban_density = 'Urban Moderate'
                    urban_score = 70
                elif poi_density > 2:
                    urban_density = 'Semi-Urban'
                    urban_score = 50
                else:
                    urban_density = 'Rural'
                    urban_score = 20
            else:
                urban_density = 'Unknown'
                urban_score = 0
            
            terrain_analysis['urban_density_score'] = urban_score
            
            # 3. Combine terrain classification
            primary_terrain = self._determine_primary_terrain(elevation_terrain, urban_density)
            terrain_analysis['primary_terrain'] = primary_terrain
            
            # 4. Calculate terrain breakdown percentages
            terrain_analysis['terrain_breakdown'] = {
                'elevation_component': elevation_terrain,
                'urban_component': urban_density,
                'poi_density_per_km': round(poi_density, 2) if route_length_km > 0 else 0,
                'route_length_km': round(route_length_km, 2)
            }
            
            # 5. Calculate confidence score
            confidence = self._calculate_terrain_confidence(elevation_data, total_pois, route_length_km)
            terrain_analysis['terrain_confidence'] = confidence
            
            print(f"✅ Terrain classified as: {primary_terrain} (confidence: {confidence}%)")
            
        except Exception as e:
            print(f"❌ Terrain classification failed: {e}")
        
        return terrain_analysis
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def _estimate_route_length(self, route_points: List[List[float]]) -> float:
        """Estimate total route length in kilometers"""
        total_distance = 0
        
        for i in range(len(route_points) - 1):
            distance = self._calculate_distance(route_points[i], route_points[i + 1])
            total_distance += distance
        
        return total_distance / 1000  # Convert to kilometers
    
    def _calculate_distance(self, point1: List[float], point2: List[float]) -> float:
        """Calculate distance between two GPS points in meters"""
        lat1, lon1 = point1[0], point1[1]
        lat2, lon2 = point2[0], point2[1]
        
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _determine_primary_terrain(self, elevation_terrain: str, urban_density: str) -> str:
        """Determine primary terrain classification"""
        
        # Terrain combination matrix
        terrain_matrix = {
            ('Mountainous', 'Urban Dense'): 'Urban Mountainous',
            ('Mountainous', 'Urban Moderate'): 'Hilly Urban',
            ('Mountainous', 'Semi-Urban'): 'Mountainous Semi-Urban',
            ('Mountainous', 'Rural'): 'Rural Mountainous',
            
            ('Hilly', 'Urban Dense'): 'Urban Hilly',
            ('Hilly', 'Urban Moderate'): 'Hilly Urban',
            ('Hilly', 'Semi-Urban'): 'Hilly Semi-Urban', 
            ('Hilly', 'Rural'): 'Rural Hilly',
            
            ('Flat', 'Urban Dense'): 'Urban Dense',
            ('Flat', 'Urban Moderate'): 'Urban Moderate',
            ('Flat', 'Semi-Urban'): 'Semi-Urban Plains',
            ('Flat', 'Rural'): 'Rural Plains',
            
            # ADDED: Handle Unknown cases
            ('Unknown', 'Urban Dense'): 'Urban Area',
            ('Unknown', 'Urban Moderate'): 'Urban Area',
            ('Unknown', 'Semi-Urban'): 'Semi-Urban Area',
            ('Unknown', 'Rural'): 'Rural Area',
            ('Unknown', 'Unknown'): 'Mixed Terrain',
            ('Flat', 'Unknown'): 'Flat Terrain',
            ('Hilly', 'Unknown'): 'Hilly Terrain',
            ('Mountainous', 'Unknown'): 'Mountainous Terrain'
        }
        
        return terrain_matrix.get((elevation_terrain, urban_density), 'Mixed Terrain')
    
    def _calculate_terrain_confidence(self, elevation_data: List[Dict], 
                                    total_pois: int, route_length: float) -> int:
        """Calculate confidence percentage for terrain classification"""
        confidence = 0
        
        # Elevation data quality (0-40 points)
        if len(elevation_data) > 10:
            confidence += 40
        elif len(elevation_data) > 5:
            confidence += 30
        elif len(elevation_data) > 0:
            confidence += 20
        
        # POI data quality (0-30 points)
        if total_pois > 20:
            confidence += 30
        elif total_pois > 10:
            confidence += 25
        elif total_pois > 5:
            confidence += 20
        elif total_pois > 0:
            confidence += 15
        
        # Route length adequacy (0-30 points)
        if route_length > 50:
            confidence += 30
        elif route_length > 20:
            confidence += 25
        elif route_length > 10:
            confidence += 20
        elif route_length > 0:
            confidence += 15
        
        return min(100, confidence)
    
    def generate_comprehensive_markers(self, route_data: Dict) -> List[Dict]:
        """Generate all marker data for enhanced map"""
        
        markers = []
        
        try:
            route_info = route_data.get('route_info', {})
            sharp_turns = route_data.get('sharp_turns', [])
            pois = route_data.get('pois', {})
            route_points = route_data.get('route_points', [])
            
            # 1. Start and End markers
            if route_points:
                start_point = route_points[0]
                end_point = route_points[-1]
                
                markers.append({
                    'type': 'start',
                    'latitude': start_point['latitude'],
                    'longitude': start_point['longitude'],
                    'icon': 'green',
                    'label': 'A',
                    'size': 'large',
                    'description': 'Route Start'
                })
                
                markers.append({
                    'type': 'end',
                    'latitude': end_point['latitude'],
                    'longitude': end_point['longitude'],
                    'icon': 'red',
                    'label': 'B', 
                    'size': 'large',
                    'description': 'Route End'
                })
            
            # 2. Critical sharp turns (most dangerous)
            critical_turns = [turn for turn in sharp_turns if turn.get('angle', 0) >= 70]
            for i, turn in enumerate(critical_turns[:10]):  # Limit to 10 most critical
                markers.append({
                    'type': 'critical_turn',
                    'latitude': turn['latitude'],
                    'longitude': turn['longitude'],
                    'icon': 'orange',
                    'label': f'T{i+1}',
                    'size': 'medium',
                    'description': f"Sharp Turn: {turn.get('angle', 0):.1f}°"
                })
            
            # 3. Emergency services (hospitals, police, fire stations)
            emergency_types = {
                'hospitals': {'icon': 'red', 'label': 'H', 'description': 'Hospital'},
                'police': {'icon': 'blue', 'label': 'P', 'description': 'Police Station'},
                'fire_stations': {'icon': 'orange', 'label': 'F', 'description': 'Fire Station'}
            }
            
            for poi_type, config in emergency_types.items():
                poi_list = pois.get(poi_type, [])
                for i, poi in enumerate(poi_list[:5]):  # Limit to 5 per type
                    if poi.get('latitude', 0) != 0 and poi.get('longitude', 0) != 0:
                        markers.append({
                            'type': poi_type,
                            'latitude': poi['latitude'],
                            'longitude': poi['longitude'],
                            'icon': config['icon'],
                            'label': config['label'],
                            'size': 'small',
                            'description': f"{config['description']}: {poi.get('name', 'Unknown')}"
                        })
            
            # 4. Essential services
            essential_types = {
                'gas_stations': {'icon': 'green', 'label': 'G', 'description': 'Gas Station'},
                'schools': {'icon': 'yellow', 'label': 'S', 'description': 'School'}
            }
            
            for poi_type, config in essential_types.items():
                poi_list = pois.get(poi_type, [])
                for i, poi in enumerate(poi_list[:3]):  # Limit to 3 per type
                    if poi.get('latitude', 0) != 0 and poi.get('longitude', 0) != 0:
                        markers.append({
                            'type': poi_type,
                            'latitude': poi['latitude'],
                            'longitude': poi['longitude'],
                            'icon': config['icon'],
                            'label': config['label'],
                            'size': 'tiny',
                            'description': f"{config['description']}: {poi.get('name', 'Unknown')}"
                        })
            
            print(f"✅ Generated {len(markers)} comprehensive markers")
            return markers
            
        except Exception as e:
            print(f"❌ Error generating markers: {e}")
            return []