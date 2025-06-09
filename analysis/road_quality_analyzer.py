# analysis/road_quality_analyzer.py - Real API Integration for Road Quality Analysis
# Purpose: Analyze road surface conditions using TomTom, HERE, and MapBox APIs
# Dependencies: requests, googlemaps, os
# Author: Enhanced Route Analysis System
# Created: 2024

import os
import time
import requests
import math
from typing import List, Dict, Any, Optional
import googlemaps

class RoadQualityAnalyzer:
    """Comprehensive road quality analysis using multiple APIs"""
    
    def __init__(self, api_tracker):
        self.api_tracker = api_tracker
        
        # Load API keys from environment
        self.tomtom_api_key = os.environ.get('TOMTOM_API_KEY')
        self.here_api_key = os.environ.get('HERE_API_KEY')
        self.mapbox_api_key = os.environ.get('MAPBOX_API_KEY')
        self.google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        
        # Initialize Google Maps client
        if self.google_api_key:
            self.gmaps = googlemaps.Client(key=self.google_api_key)
        
        print(f"🛣️ Road Quality Analyzer initialized")
        print(f"   TomTom API: {'✅ Configured' if self.tomtom_api_key else '❌ Missing'}")
        print(f"   HERE API: {'✅ Configured' if self.here_api_key else '❌ Missing'}")
        print(f"   MapBox API: {'✅ Configured' if self.mapbox_api_key else '❌ Missing'}")
    
    def analyze_road_conditions(self, route_points: List[List[float]], route_id: str) -> List[Dict]:
        """Comprehensive road quality analysis using multiple APIs"""
        try:
            print(f"🔍 Starting comprehensive road quality analysis...")
            
            road_issues = []
            
            # Sample points for analysis (every 20th point to avoid API overuse)
            step = max(1, len(route_points) // 20)
            sampled_points = route_points[::step]
            
            print(f"   Analyzing {len(sampled_points)} sample points along route")
            
            for i, point in enumerate(sampled_points[:25]):  # Limit to 25 points
                try:
                    # Multi-API road quality assessment
                    road_data = self._comprehensive_road_assessment(point[0], point[1])
                    
                    if road_data and road_data.get('has_issues'):
                        road_issues.append({
                            'route_id': route_id,
                            'latitude': point[0],
                            'longitude': point[1],
                            'issue_type': road_data.get('primary_issue', 'surface_quality'),
                            'severity': road_data.get('severity', 'medium'),
                            'confidence': road_data.get('confidence', 'medium'),
                            'description': road_data.get('description', 'Road quality concern detected'),
                            'recommended_speed': road_data.get('recommended_speed', 40),
                            'api_sources': road_data.get('sources', []),
                            'analysis_details': road_data.get('details', {})
                        })
                        
                        print(f"   🚨 Issue detected at {point[0]:.4f},{point[1]:.4f}: {road_data.get('primary_issue')}")
                    
                    # Rate limiting between API calls
                    time.sleep(0.2)
                    
                except Exception as e:
                    print(f"   ⚠️ Error analyzing point {i+1}: {e}")
                    continue
            
            print(f"✅ Road quality analysis completed. Found {len(road_issues)} potential issues")
            return road_issues
            
        except Exception as e:
            print(f"❌ Road quality analysis failed: {e}")
            return []
    
    def _comprehensive_road_assessment(self, lat: float, lng: float) -> Optional[Dict]:
        """Multi-API road quality assessment for a single point"""
        assessments = []
        
        # 1. TomTom Road Quality Analysis
        if self.tomtom_api_key:
            tomtom_data = self._get_tomtom_road_data(lat, lng)
            if tomtom_data:
                assessments.append(tomtom_data)
        
        # 2. HERE Road Analysis
        if self.here_api_key:
            here_data = self._get_here_road_data(lat, lng)
            if here_data:
                assessments.append(here_data)
        
        # 3. MapBox Road Analysis
        if self.mapbox_api_key:
            mapbox_data = self._get_mapbox_road_data(lat, lng)
            if mapbox_data:
                assessments.append(mapbox_data)
        
        # 4. Google Roads API (if available)
        google_data = self._get_google_road_data(lat, lng)
        if google_data:
            assessments.append(google_data)
        
        # Combine assessments
        return self._combine_road_assessments(assessments, lat, lng)
    
    def _get_tomtom_road_data(self, lat: float, lng: float) -> Optional[Dict]:
        """Get road quality data from TomTom API"""
        try:
            start_time = time.time()
            
            # TomTom Road Information API
            url = "https://api.tomtom.com/routing/1/calculateRoute/{},{}/json"
            params = {
                'key': self.tomtom_api_key,
                'routeType': 'fastest',
                'traffic': 'true',
                'travelMode': 'car'
            }
            
            # Create a short route segment for analysis
            nearby_lat = lat + 0.001  # ~100m offset
            nearby_lng = lng + 0.001
            formatted_url = url.format(f"{lat},{lng}", f"{nearby_lat},{nearby_lng}")
            
            response = requests.get(formatted_url, params=params, timeout=10)
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'tomtom_road_quality',
                '/routing/calculateRoute',
                response.status_code,
                response_time,
                response.status_code == 200
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract road quality indicators
                route = data.get('routes', [{}])[0]
                summary = route.get('summary', {})
                
                # Analyze traffic delay as road quality indicator
                travel_time = summary.get('travelTimeInSeconds', 0)
                traffic_delay = summary.get('trafficDelayInSeconds', 0)
                
                quality_score = self._calculate_quality_score_tomtom(travel_time, traffic_delay)
                
                return {
                    'source': 'tomtom',
                    'quality_score': quality_score,
                    'has_issues': quality_score < 6,
                    'confidence': 'high',
                    'raw_data': {
                        'travel_time': travel_time,
                        'traffic_delay': traffic_delay,
                        'distance': summary.get('lengthInMeters', 0)
                    }
                }
            
        except Exception as e:
            print(f"TomTom API error: {e}")
            self.api_tracker.log_api_call(
                'tomtom_road_quality',
                '/routing/calculateRoute',
                500,
                0,
                False,
                str(e)
            )
        
        return None
    
    def _get_here_road_data(self, lat: float, lng: float) -> Optional[Dict]:
        """Get road quality data from HERE API"""
        try:
            start_time = time.time()
            
            # HERE Routing API with road attributes
            url = "https://router.hereapi.com/v8/routes"
            params = {
                'apikey': self.here_api_key,
                'transportMode': 'car',
                'origin': f"{lat},{lng}",
                'destination': f"{lat + 0.001},{lng + 0.001}",
                'return': 'summary,attributes',
                'attributes': 'shape,roadAttributes'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'here_road_quality',
                '/v8/routes',
                response.status_code,
                response_time,
                response.status_code == 200
            )
            
            if response.status_code == 200:
                data = response.json()
                
                routes = data.get('routes', [])
                if routes:
                    route = routes[0]
                    
                    # Extract road attributes
                    sections = route.get('sections', [])
                    if sections:
                        section = sections[0]
                        attributes = section.get('attributes', {})
                        
                        # HERE road quality indicators
                        road_attributes = attributes.get('roadAttributes', [])
                        
                        quality_issues = []
                        for attr in road_attributes:
                            if any(issue in str(attr).lower() for issue in 
                                  ['unpaved', 'construction', 'poor', 'damaged']):
                                quality_issues.append(str(attr))
                        
                        quality_score = 8 - len(quality_issues) * 2
                        
                        return {
                            'source': 'here',
                            'quality_score': max(1, quality_score),
                            'has_issues': len(quality_issues) > 0 or quality_score < 6,
                            'confidence': 'high',
                            'issues_detected': quality_issues,
                            'raw_data': {
                                'road_attributes': road_attributes,
                                'distance': route.get('summary', {}).get('length', 0)
                            }
                        }
            
        except Exception as e:
            print(f"HERE API error: {e}")
            self.api_tracker.log_api_call(
                'here_road_quality',
                '/v8/routes',
                500,
                0,
                False,
                str(e)
            )
        
        return None
    
    def _get_mapbox_road_data(self, lat: float, lng: float) -> Optional[Dict]:
        """Get road quality data from MapBox API"""
        try:
            start_time = time.time()
            
            # MapBox Directions API with road surface data
            url = "https://api.mapbox.com/directions/v5/mapbox/driving"
            coordinates = f"{lng},{lat};{lng + 0.001},{lat + 0.001}"
            
            params = {
                'access_token': self.mapbox_api_key,
                'geometries': 'geojson',
                'annotations': 'duration,distance,speed',
                'overview': 'full'
            }
            
            full_url = f"{url}/{coordinates}"
            response = requests.get(full_url, params=params, timeout=10)
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'mapbox_road_quality',
                '/directions/v5/mapbox/driving',
                response.status_code,
                response_time,
                response.status_code == 200
            )
            
            if response.status_code == 200:
                data = response.json()
                
                routes = data.get('routes', [])
                if routes:
                    route = routes[0]
                    legs = route.get('legs', [])
                    
                    if legs:
                        leg = legs[0]
                        
                        # Analyze speed annotations for road quality
                        annotations = leg.get('annotation', {})
                        speeds = annotations.get('speed', [])
                        durations = annotations.get('duration', [])
                        
                        if speeds:
                            avg_speed = sum(speeds) / len(speeds)
                            expected_speed = 50  # km/h expected for good roads
                            
                            # Quality score based on speed analysis
                            speed_ratio = avg_speed / expected_speed
                            quality_score = min(10, speed_ratio * 8)
                            
                            return {
                                'source': 'mapbox',
                                'quality_score': quality_score,
                                'has_issues': quality_score < 6,
                                'confidence': 'medium',
                                'raw_data': {
                                    'average_speed': avg_speed,
                                    'expected_speed': expected_speed,
                                    'distance': route.get('distance', 0),
                                    'duration': route.get('duration', 0)
                                }
                            }
            
        except Exception as e:
            print(f"MapBox API error: {e}")
            self.api_tracker.log_api_call(
                'mapbox_road_quality',
                '/directions/v5/mapbox/driving',
                500,
                0,
                False,
                str(e)
            )
        
        return None
    
    def _get_google_road_data(self, lat: float, lng: float) -> Optional[Dict]:
        """Get road quality indicators from Google Roads API"""
        try:
            if not self.gmaps:
                return None
            
            start_time = time.time()
            
            # Use Google Roads API to snap to roads and get road info
            path = [(lat, lng), (lat + 0.001, lng + 0.001)]
            
            # Google Roads: Snap to Roads
            snapped = self.gmaps.snap_to_roads(path, interpolate=True)
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'google_roads',
                '/roads/snapToRoads',
                200 if snapped else 400,
                response_time,
                bool(snapped)
            )
            
            if snapped:
                # Analyze snapping accuracy as quality indicator
                original_point = path[0]
                snapped_point = (snapped[0]['location']['latitude'], 
                               snapped[0]['location']['longitude'])
                
                # Calculate snapping distance
                distance = self._calculate_distance(original_point, snapped_point)
                
                # Quality score based on snapping accuracy
                if distance < 5:  # Very close snap = good road
                    quality_score = 9
                elif distance < 20:  # Moderate snap = decent road
                    quality_score = 7
                elif distance < 50:  # Poor snap = questionable road
                    quality_score = 5
                else:  # Very poor snap = bad road
                    quality_score = 3
                
                return {
                    'source': 'google_roads',
                    'quality_score': quality_score,
                    'has_issues': quality_score < 6,
                    'confidence': 'medium',
                    'raw_data': {
                        'snap_distance': distance,
                        'place_id': snapped[0].get('placeId', ''),
                        'snapped_points': len(snapped)
                    }
                }
            
        except Exception as e:
            print(f"Google Roads API error: {e}")
            self.api_tracker.log_api_call(
                'google_roads',
                '/roads/snapToRoads',
                500,
                0,
                False,
                str(e)
            )
        
        return None
    
    def _combine_road_assessments(self, assessments: List[Dict], lat: float, lng: float) -> Optional[Dict]:
        """Combine multiple API assessments into final road quality analysis"""
        if not assessments:
            return None
        
        # Calculate weighted average quality score
        total_score = 0
        total_weight = 0
        sources = []
        confidence_levels = []
        
        for assessment in assessments:
            weight = 1.0
            if assessment['source'] == 'tomtom':
                weight = 1.2  # TomTom has good road data
            elif assessment['source'] == 'here':
                weight = 1.1  # HERE has detailed road attributes
            
            total_score += assessment['quality_score'] * weight
            total_weight += weight
            sources.append(assessment['source'])
            confidence_levels.append(assessment['confidence'])
        
        avg_quality_score = total_score / total_weight if total_weight > 0 else 5
        
        # Determine primary issue type
        primary_issue = self._determine_primary_issue(assessments, avg_quality_score)
        
        # Determine overall confidence
        if 'high' in confidence_levels:
            overall_confidence = 'high'
        elif 'medium' in confidence_levels:
            overall_confidence = 'medium'
        else:
            overall_confidence = 'low'
        
        # Generate description and recommendations
        description, recommended_speed = self._generate_road_recommendations(
            avg_quality_score, primary_issue, len(assessments)
        )
        
        return {
            'has_issues': avg_quality_score < 6.5,
            'quality_score': round(avg_quality_score, 1),
            'primary_issue': primary_issue,
            'severity': self._get_severity_level(avg_quality_score),
            'confidence': overall_confidence,
            'description': description,
            'recommended_speed': recommended_speed,
            'sources': sources,
            'details': {
                'individual_assessments': assessments,
                'weighted_average': round(avg_quality_score, 1),
                'apis_consulted': len(assessments)
            }
        }
    
    def _calculate_quality_score_tomtom(self, travel_time: int, traffic_delay: int) -> float:
        """Calculate quality score from TomTom data"""
        if travel_time == 0:
            return 5  # Neutral score
        
        delay_ratio = traffic_delay / travel_time if travel_time > 0 else 0
        
        # Higher delay ratio suggests poor road conditions
        if delay_ratio > 0.5:
            return 3  # Poor quality
        elif delay_ratio > 0.3:
            return 5  # Average quality
        elif delay_ratio > 0.1:
            return 7  # Good quality
        else:
            return 9  # Excellent quality
    
    def _calculate_distance(self, point1: tuple, point2: tuple) -> float:
        """Calculate distance between two GPS points in meters"""
        lat1, lon1 = point1
        lat2, lon2 = point2
        
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
    
    def _determine_primary_issue(self, assessments: List[Dict], avg_score: float) -> str:
        """Determine the primary road quality issue"""
        if avg_score >= 7:
            return 'good_condition'
        elif avg_score >= 5:
            return 'minor_issues'
        elif avg_score >= 3:
            return 'poor_surface'
        else:
            return 'critical_condition'
    
    def _get_severity_level(self, quality_score: float) -> str:
        """Get severity level based on quality score"""
        if quality_score >= 8:
            return 'low'
        elif quality_score >= 6:
            return 'medium'
        elif quality_score >= 4:
            return 'high'
        else:
            return 'critical'
    
    def _generate_road_recommendations(self, quality_score: float, issue_type: str, 
                                     api_count: int) -> tuple:
        """Generate description and recommended speed"""
        if quality_score >= 8:
            description = f"Good road conditions detected (confidence: {api_count} APIs)"
            recommended_speed = 60
        elif quality_score >= 6:
            description = f"Minor road quality concerns detected (confidence: {api_count} APIs)"
            recommended_speed = 50
        elif quality_score >= 4:
            description = f"Poor road surface conditions detected (confidence: {api_count} APIs)"
            recommended_speed = 40
        else:
            description = f"Critical road conditions - exercise extreme caution (confidence: {api_count} APIs)"
            recommended_speed = 30
        
        return description, recommended_speed
    
    def store_road_quality_data(self, route_id: str, road_issues: List[Dict]) -> bool:
        """Store road quality analysis in database"""
        if not road_issues:
            return True
        
        try:
            import sqlite3
            
            with sqlite3.connect(self.api_tracker.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Create road quality table if it doesn't exist
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
                
                # Insert road quality data
                for issue in road_issues:
                    cursor.execute("""
                        INSERT INTO road_quality_data 
                        (route_id, latitude, longitude, issue_type, severity, confidence,
                         description, recommended_speed, api_sources, analysis_details)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        issue['route_id'],
                        issue['latitude'],
                        issue['longitude'],
                        issue['issue_type'],
                        issue['severity'],
                        issue['confidence'],
                        issue['description'],
                        issue['recommended_speed'],
                        ','.join(issue.get('api_sources', [])),
                        str(issue.get('analysis_details', {}))
                    ))
                
                conn.commit()
                print(f"✅ Stored {len(road_issues)} road quality assessments in database")
                return True
                
        except Exception as e:
            print(f"❌ Error storing road quality data: {e}")
            return False