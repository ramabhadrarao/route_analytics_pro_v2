# analysis/emergency_analyzer.py - Complete Emergency Response Analysis System
# Purpose: Analyze emergency preparedness using Google Places API and emergency services data
# Dependencies: requests, googlemaps, os, time
# Author: Enhanced Route Analysis System
# Created: 2024

import os
import time
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import googlemaps

class EmergencyResponseAnalyzer:
    """Comprehensive emergency response analysis using multiple APIs"""
    
    def __init__(self, api_tracker):
        self.api_tracker = api_tracker
        
        # Load API keys from environment
        self.google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        
        # Initialize Google Maps client
        if self.google_api_key:
            self.gmaps = googlemaps.Client(key=self.google_api_key)
        else:
            self.gmaps = None
        
        # Emergency facility types and configurations
        self.emergency_types = {
            'hospital': {
                'google_types': ['hospital', 'emergency_room'],
                'priority': 1,
                'search_radius': 15000,  # 15km for hospitals
                'icon': 'fas fa-hospital',
                'color': '#dc3545',
                'description': 'Medical emergency facilities'
            },
            'police': {
                'google_types': ['police'],
                'priority': 2,
                'search_radius': 10000,  # 10km for police
                'icon': 'fas fa-shield-alt',
                'color': '#0052a3',
                'description': 'Law enforcement facilities'
            },
            'fire_station': {
                'google_types': ['fire_station'],
                'priority': 3,
                'search_radius': 12000,  # 12km for fire stations
                'icon': 'fas fa-fire-extinguisher',
                'color': '#fd7e14',
                'description': 'Fire and rescue services'
            },
            'emergency_clinic': {
                'google_types': ['doctor', 'health', 'clinic'],
                'priority': 4,
                'search_radius': 8000,  # 8km for clinics
                'icon': 'fas fa-clinic-medical',
                'color': '#28a745',
                'description': 'Urgent care and medical clinics'
            },
            'pharmacy': {
                'google_types': ['pharmacy'],
                'priority': 5,
                'search_radius': 5000,  # 5km for pharmacies
                'icon': 'fas fa-pills',
                'color': '#17a2b8',
                'description': '24-hour pharmacies'
            }
        }
        
        print(f"🚨 Emergency Response Analyzer initialized")
        print(f"   Google Maps API: {'✅ Configured' if self.google_api_key else '❌ Missing'}")
        print(f"   Emergency Types: {len(self.emergency_types)} categories")
    
    def analyze_emergency_preparedness(self, route_points: List[List[float]], route_id: str) -> Dict[str, Any]:
        """Comprehensive emergency preparedness analysis"""
        try:
            print(f"🔍 Starting comprehensive emergency preparedness analysis...")
            
            emergency_data = {
                'emergency_facilities': {},
                'coverage_analysis': {},
                'response_times': {},
                'preparedness_score': 0,
                'critical_gaps': [],
                'recommendations': []
            }
            
            # Sample points for analysis
            step = max(1, len(route_points) // 8)
            sampled_points = route_points[::step]
            
            print(f"   Analyzing {len(sampled_points)} strategic points for emergency coverage")
            
            # Analyze each emergency type
            for emergency_type, config in self.emergency_types.items():
                print(f"   🔍 Searching for {emergency_type} facilities...")
                
                facilities = self._find_emergency_facilities(
                    sampled_points, emergency_type, config
                )
                
                if facilities:
                    emergency_data['emergency_facilities'][emergency_type] = facilities
                    print(f"   ✅ Found {len(facilities)} {emergency_type} facilities")
                else:
                    print(f"   ⚠️ No {emergency_type} facilities found")
            
            # Analyze coverage and response times
            emergency_data['coverage_analysis'] = self._analyze_emergency_coverage(
                route_points, emergency_data['emergency_facilities']
            )
            
            emergency_data['response_times'] = self._estimate_response_times(
                route_points, emergency_data['emergency_facilities']
            )
            
            # Calculate preparedness score
            emergency_data['preparedness_score'] = self._calculate_preparedness_score(
                emergency_data['emergency_facilities']
            )
            
            # Identify critical gaps
            emergency_data['critical_gaps'] = self._identify_critical_gaps(
                emergency_data['emergency_facilities'], emergency_data['coverage_analysis']
            )
            
            # Generate recommendations
            emergency_data['recommendations'] = self._generate_emergency_recommendations(
                emergency_data
            )
            
            # Store route summary
            emergency_data['route_summary'] = self._generate_route_summary(emergency_data)
            
            total_facilities = sum(len(facilities) for facilities in emergency_data['emergency_facilities'].values())
            print(f"✅ Emergency preparedness analysis completed. Found {total_facilities} emergency facilities")
            
            return emergency_data
            
        except Exception as e:
            print(f"❌ Emergency preparedness analysis failed: {e}")
            return {}
    
    def _find_emergency_facilities(self, sampled_points: List[List[float]], 
                                 emergency_type: str, config: Dict) -> List[Dict]:
        """Find emergency facilities using Google Places API"""
        if not self.gmaps:
            return []
        
        all_facilities = []
        seen_facilities = set()  # To avoid duplicates
        
        for point in sampled_points[:6]:  # Limit to 6 search points
            try:
                for google_type in config['google_types']:
                    try:
                        start_time = time.time()
                        
                        # Search for facilities
                        places_result = self.gmaps.places_nearby(
                            location=(point[0], point[1]),
                            radius=config['search_radius'],
                            type=google_type,
                            language='en'
                        )
                        
                        response_time = time.time() - start_time
                        
                        # Log API usage
                        self.api_tracker.log_api_call(
                            f'google_places_emergency_{emergency_type}',
                            '/place/nearbysearch/json',
                            200 if places_result else 400,
                            response_time,
                            bool(places_result.get('results'))
                        )
                        
                        # Process results
                        for place in places_result.get('results', [])[:8]:  # Limit per search
                            place_id = place.get('place_id')
                            if place_id and place_id not in seen_facilities:
                                facility = self._process_emergency_facility(place, emergency_type)
                                if facility:
                                    all_facilities.append(facility)
                                    seen_facilities.add(place_id)
                        
                        time.sleep(0.2)  # Rate limiting
                        
                    except Exception as e:
                        print(f"   Error searching {google_type}: {e}")
                        continue
                        
            except Exception as e:
                print(f"   Error searching point {point}: {e}")
                continue
        
        # Sort by distance and limit results
        all_facilities.sort(key=lambda x: x.get('distance_km', 999))
        return all_facilities[:20]  # Limit to 20 facilities per type
    
    def _process_emergency_facility(self, place: Dict, emergency_type: str) -> Optional[Dict]:
        """Process and enhance emergency facility data"""
        try:
            # Extract basic information
            geometry = place.get('geometry', {})
            location = geometry.get('location', {})
            lat = location.get('lat', 0)
            lng = location.get('lng', 0)
            
            if lat == 0 or lng == 0:
                return None
            
            # Get detailed information
            detailed_info = self._get_facility_details(place.get('place_id', ''))
            
            facility = {
                'name': place.get('name', 'Unknown Facility'),
                'latitude': lat,
                'longitude': lng,
                'place_id': place.get('place_id', ''),
                'address': place.get('vicinity', ''),
                'rating': place.get('rating', 0),
                'user_ratings_total': place.get('user_ratings_total', 0),
                'types': place.get('types', []),
                'business_status': place.get('business_status', 'OPERATIONAL'),
                'emergency_type': emergency_type,
                'priority_level': self.emergency_types[emergency_type]['priority']
            }
            
            # Add detailed information if available
            if detailed_info:
                facility.update({
                    'formatted_address': detailed_info.get('formatted_address', ''),
                    'formatted_phone_number': detailed_info.get('formatted_phone_number', ''),
                    'international_phone_number': detailed_info.get('international_phone_number', ''),
                    'website': detailed_info.get('website', ''),
                    'opening_hours': detailed_info.get('opening_hours', {}),
                    'permanently_closed': detailed_info.get('permanently_closed', False)
                })
            
            # Calculate operational status
            facility['operational_status'] = self._assess_operational_status(facility)
            
            return facility
            
        except Exception as e:
            print(f"Error processing emergency facility: {e}")
            return None
    
    def _get_facility_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed facility information"""
        if not self.gmaps or not place_id:
            return None
        
        try:
            start_time = time.time()
            
            fields = [
                'formatted_address', 'formatted_phone_number', 'international_phone_number',
                'website', 'opening_hours', 'permanently_closed', 'business_status'
            ]
            
            place_details = self.gmaps.place(
                place_id=place_id,
                fields=fields,
                language='en'
            )
            
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'google_place_details_emergency',
                '/place/details/json',
                200 if place_details else 400,
                response_time,
                bool(place_details.get('result'))
            )
            
            if place_details and 'result' in place_details:
                return place_details['result']
            
            return None
            
        except Exception as e:
            print(f"Error getting facility details: {e}")
            return None
    
    def _assess_operational_status(self, facility: Dict) -> str:
        """Assess if facility is operational"""
        if facility.get('permanently_closed', False):
            return 'CLOSED'
        
        if facility.get('business_status') == 'CLOSED_TEMPORARILY':
            return 'TEMPORARILY_CLOSED'
        
        # Check opening hours for 24/7 facilities
        opening_hours = facility.get('opening_hours', {})
        if opening_hours.get('open_now', True):
            periods = opening_hours.get('periods', [])
            if periods and len(periods) == 1 and not periods[0].get('close'):
                return '24_7_OPERATIONAL'
        
        return 'OPERATIONAL'
    
    def _analyze_emergency_coverage(self, route_points: List[List[float]], 
                                  facilities: Dict) -> Dict:
        """Analyze emergency coverage along the route"""
        try:
            coverage_analysis = {
                'total_route_points': len(route_points),
                'covered_points': 0,
                'coverage_gaps': [],
                'average_distance_to_nearest': 0,
                'coverage_by_type': {}
            }
            
            covered_points = 0
            total_distance = 0
            distance_threshold = 25000  # 25km threshold for coverage
            
            # Sample every 10th point for analysis
            sample_points = route_points[::max(1, len(route_points) // 50)]
            
            for point in sample_points:
                nearest_distance = float('inf')
                point_covered = False
                
                # Check distance to nearest emergency facility
                for facility_type, facility_list in facilities.items():
                    for facility in facility_list:
                        distance = self._calculate_distance(
                            point[0], point[1], 
                            facility['latitude'], facility['longitude']
                        )
                        
                        nearest_distance = min(nearest_distance, distance)
                        
                        if distance <= distance_threshold:
                            point_covered = True
                
                if point_covered:
                    covered_points += 1
                else:
                    coverage_analysis['coverage_gaps'].append({
                        'latitude': point[0],
                        'longitude': point[1],
                        'distance_to_nearest': round(nearest_distance / 1000, 2)
                    })
                
                total_distance += nearest_distance
            
            coverage_analysis['covered_points'] = covered_points
            coverage_analysis['coverage_percentage'] = (covered_points / len(sample_points)) * 100
            coverage_analysis['average_distance_to_nearest'] = round((total_distance / len(sample_points)) / 1000, 2)
            
            return coverage_analysis
            
        except Exception as e:
            print(f"Error analyzing emergency coverage: {e}")
            return {}
    
    def _estimate_response_times(self, route_points: List[List[float]], 
                               facilities: Dict) -> Dict:
        """Estimate emergency response times"""
        response_times = {
            'average_response_time': 0,
            'response_times_by_type': {},
            'fastest_response_areas': [],
            'slowest_response_areas': []
        }
        
        try:
            # Sample points for response time analysis
            sample_points = route_points[::max(1, len(route_points) // 20)]
            
            total_response_time = 0
            point_count = 0
            
            for point in sample_points:
                fastest_time = float('inf')
                
                for facility_type, facility_list in facilities.items():
                    for facility in facility_list:
                        # Calculate distance
                        distance = self._calculate_distance(
                            point[0], point[1],
                            facility['latitude'], facility['longitude']
                        )
                        
                        # Estimate response time (simplified calculation)
                        # Base time + travel time (assuming 60 km/h average speed)
                        base_time = 2  # 2 minutes base response time
                        travel_time = (distance / 1000) / 60 * 60  # Convert to minutes
                        total_time = base_time + travel_time
                        
                        fastest_time = min(fastest_time, total_time)
                
                if fastest_time != float('inf'):
                    total_response_time += fastest_time
                    point_count += 1
                    
                    # Categorize response areas
                    if fastest_time <= 10:  # 10 minutes or less
                        response_times['fastest_response_areas'].append({
                            'latitude': point[0],
                            'longitude': point[1],
                            'response_time': round(fastest_time, 1)
                        })
                    elif fastest_time > 20:  # More than 20 minutes
                        response_times['slowest_response_areas'].append({
                            'latitude': point[0],
                            'longitude': point[1],
                            'response_time': round(fastest_time, 1)
                        })
            
            if point_count > 0:
                response_times['average_response_time'] = round(total_response_time / point_count, 1)
            
            return response_times
            
        except Exception as e:
            print(f"Error estimating response times: {e}")
            return response_times
    
    def _calculate_preparedness_score(self, facilities: Dict) -> int:
        """Calculate overall emergency preparedness score"""
        score = 0
        
        # Scoring weights by facility type
        weights = {
            'hospital': 30,
            'police': 25,
            'fire_station': 25,
            'emergency_clinic': 15,
            'pharmacy': 5
        }
        
        for facility_type, weight in weights.items():
            facility_count = len(facilities.get(facility_type, []))
            
            if facility_count > 0:
                # Full points for having facilities, bonus for multiple
                type_score = weight
                if facility_count >= 3:
                    type_score += 5  # Bonus for good coverage
                elif facility_count >= 2:
                    type_score += 2  # Small bonus
                
                score += min(type_score, weight + 5)  # Cap bonus
        
        return min(100, score)
    
    def _identify_critical_gaps(self, facilities: Dict, coverage_analysis: Dict) -> List[str]:
        """Identify critical emergency preparedness gaps"""
        gaps = []
        
        # Check for missing facility types
        critical_types = ['hospital', 'police', 'fire_station']
        for facility_type in critical_types:
            if not facilities.get(facility_type):
                gaps.append(f"No {facility_type.replace('_', ' ')} facilities found along route")
        
        # Check coverage percentage
        coverage_pct = coverage_analysis.get('coverage_percentage', 0)
        if coverage_pct < 50:
            gaps.append(f"Poor emergency coverage - only {coverage_pct:.1f}% of route covered")
        
        # Check average distance to facilities
        avg_distance = coverage_analysis.get('average_distance_to_nearest', 0)
        if avg_distance > 30:
            gaps.append(f"Emergency facilities too far - average {avg_distance:.1f}km distance")
        
        # Check for coverage gaps
        gap_count = len(coverage_analysis.get('coverage_gaps', []))
        if gap_count > 10:
            gaps.append(f"Multiple coverage gaps identified - {gap_count} areas without nearby facilities")
        
        return gaps
    
    def _generate_emergency_recommendations(self, emergency_data: Dict) -> List[str]:
        """Generate emergency preparedness recommendations"""
        recommendations = []
        
        score = emergency_data.get('preparedness_score', 0)
        gaps = emergency_data.get('critical_gaps', [])
        
        # Score-based recommendations
        if score < 50:
            recommendations.append("CRITICAL: Route has poor emergency preparedness - consider alternative routes")
            recommendations.append("Carry comprehensive emergency kit including first aid and communication devices")
        elif score < 70:
            recommendations.append("Route has moderate emergency preparedness - extra precautions recommended")
        
        # Gap-specific recommendations
        if any('hospital' in gap for gap in gaps):
            recommendations.append("No hospitals found - identify nearest medical facilities before travel")
            recommendations.append("Carry emergency medical contact numbers and consider medical insurance")
        
        if any('police' in gap for gap in gaps):
            recommendations.append("Limited law enforcement presence - save emergency numbers: 100 (Police)")
        
        if any('coverage' in gap.lower() for gap in gaps):
            recommendations.append("Route has emergency coverage gaps - inform others of travel plans")
            recommendations.append("Consider satellite communication device for remote areas")
        
        # General recommendations
        recommendations.extend([
            "Carry emergency contact list including local emergency numbers",
            "Ensure vehicle emergency kit includes: first aid, tools, flashlight, water",
            "Keep fuel tank above half-full in areas with limited emergency coverage",
            "Download offline maps and emergency contact apps"
        ])
        
        return recommendations[:10]  # Limit to 10 recommendations
    
    def _generate_route_summary(self, emergency_data: Dict) -> Dict:
        """Generate emergency preparedness route summary"""
        facilities = emergency_data.get('emergency_facilities', {})
        
        return {
            'total_facilities': sum(len(f_list) for f_list in facilities.values()),
            'facility_types_available': list(facilities.keys()),
            'preparedness_score': emergency_data.get('preparedness_score', 0),
            'critical_gaps_count': len(emergency_data.get('critical_gaps', [])),
            'overall_assessment': self._get_overall_assessment(emergency_data.get('preparedness_score', 0)),
            'primary_concerns': emergency_data.get('critical_gaps', [])[:3]
        }
    
    def _get_overall_assessment(self, score: int) -> str:
        """Get overall emergency preparedness assessment"""
        if score >= 80:
            return "EXCELLENT EMERGENCY PREPAREDNESS"
        elif score >= 60:
            return "GOOD EMERGENCY PREPAREDNESS"
        elif score >= 40:
            return "MODERATE EMERGENCY PREPAREDNESS"
        else:
            return "POOR EMERGENCY PREPAREDNESS"
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in meters"""
        import math
        
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lng/2) * math.sin(delta_lng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def store_emergency_data(self, route_id: str, emergency_data: Dict) -> bool:
        """Store emergency analysis in database"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.api_tracker.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Create emergency analysis table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS emergency_analysis (
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
                        operational_status TEXT,
                        priority_level INTEGER,
                        distance_km REAL,
                        response_time_minutes REAL,
                        additional_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (route_id) REFERENCES routes (id)
                    )
                """)
                
                # Store all emergency facilities
                facilities = emergency_data.get('emergency_facilities', {})
                total_stored = 0
                
                for facility_type, facility_list in facilities.items():
                    for facility in facility_list:
                        cursor.execute("""
                            INSERT INTO emergency_analysis 
                            (route_id, facility_type, facility_name, latitude, longitude,
                             formatted_address, formatted_phone_number, international_phone_number,
                             website, opening_hours, rating, operational_status, priority_level,
                             additional_data)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            route_id,
                            facility_type,
                            facility.get('name', 'Unknown'),
                            facility.get('latitude', 0),
                            facility.get('longitude', 0),
                            facility.get('formatted_address', ''),
                            facility.get('formatted_phone_number', ''),
                            facility.get('international_phone_number', ''),
                            facility.get('website', ''),
                            json.dumps(facility.get('opening_hours', {})),
                            facility.get('rating', 0),
                            facility.get('operational_status', 'UNKNOWN'),
                            facility.get('priority_level', 5),
                            json.dumps(facility)
                        ))
                        total_stored += 1
                
                conn.commit()
                print(f"✅ Stored {total_stored} emergency facilities in database")
                return True
                
        except Exception as e:
            print(f"❌ Error storing emergency data: {e}")
            return False