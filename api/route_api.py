# api/route_api.py - REST API Endpoints for Route Data Access
# Purpose: Provide REST API endpoints for accessing specific route data pages
# Dependencies: sqlite3, json, datetime
# Author: Route Analysis System
# Created: 2024

import json
import datetime
from typing import Dict, List, Any, Optional

class RouteAPI:
    """REST API interface for route data access"""
    
    def __init__(self, db_manager, api_tracker):
        self.db_manager = db_manager
        self.api_tracker = api_tracker
    
    def get_route_data(self, route_id: str) -> Optional[Dict]:
        """Get complete route data for a specific route"""
        try:
            route = self.db_manager.get_route(route_id)
            if not route:
                return None
            
            # Get all related data
            route_points = self.db_manager.get_route_points(route_id)
            sharp_turns = self.db_manager.get_sharp_turns(route_id)
            weather_data = self.db_manager.get_weather_data(route_id)
            network_coverage = self.db_manager.get_network_coverage(route_id)
            stored_images = self.db_manager.get_stored_images(route_id)
            
            # Get POIs by type
            pois = {
                'hospitals': self.db_manager.get_pois_by_type(route_id, 'hospital'),
                'gas_stations': self.db_manager.get_pois_by_type(route_id, 'gas_station'),
                'schools': self.db_manager.get_pois_by_type(route_id, 'school'),
                'restaurants': self.db_manager.get_pois_by_type(route_id, 'restaurant'),
                'police': self.db_manager.get_pois_by_type(route_id, 'police'),
                'fire_stations': self.db_manager.get_pois_by_type(route_id, 'fire_station')
            }
            
            return {
                'route_info': route,
                'route_points': route_points,
                'sharp_turns': sharp_turns,
                'weather_data': weather_data,
                'network_coverage': network_coverage,
                'pois': pois,
                'stored_images': stored_images,
                'api_usage': self.api_tracker.get_api_usage_by_route(route_id)
            }
            
        except Exception as e:
            print(f"Error getting route data: {e}")
            return None
    def get_emergency_contacts(self, route_id: str) -> Dict[str, Any]:
        """Get emergency contacts with phone numbers"""
        try:
            emergency_contacts = {
                'hospitals': self.db_manager.get_emergency_contacts_by_type(route_id, 'hospital'),
                'police_stations': self.db_manager.get_emergency_contacts_by_type(route_id, 'police_station'),
                'fire_stations': self.db_manager.get_emergency_contacts_by_type(route_id, 'fire_station'),
                'pharmacies': self.db_manager.get_emergency_contacts_by_type(route_id, 'pharmacy'),
                'urgent_care': self.db_manager.get_emergency_contacts_by_type(route_id, 'urgent_care')
            }
            
            # Statistics
            total_facilities = sum(len(facilities) for facilities in emergency_contacts.values())
            facilities_with_phone = sum(
                len([f for f in facilities if f.get('formatted_phone_number')])
                for facilities in emergency_contacts.values()
            )
            
            return {
                'emergency_contacts': emergency_contacts,
                'statistics': {
                    'total_facilities': total_facilities,
                    'facilities_with_phone': facilities_with_phone,
                    'phone_coverage_percentage': round((facilities_with_phone / total_facilities * 100), 1) if total_facilities > 0 else 0
                },
                'quick_contacts': {
                    'national_emergency': '112',
                    'police': '100', 
                    'fire': '101',
                    'ambulance': '108',
                    'highway_patrol': '1033'
                }
            }
            
        except Exception as e:
            return {'error': str(e)}
    def get_route_overview(self, route_id: str) -> Dict[str, Any]:
        """Get route overview data with enhanced safety scoring"""
        try:
            route = self.db_manager.get_route(route_id)
            if not route:
                return {'error': 'Route not found'}
            
            # Calculate statistics
            sharp_turns = self.db_manager.get_sharp_turns(route_id)
            network_coverage = self.db_manager.get_network_coverage(route_id)
            
            # Count network issues
            dead_zones = len([c for c in network_coverage if c.get('is_dead_zone')])
            poor_zones = len([c for c in network_coverage if c.get('is_poor_coverage')])
            
            # Calculate enhanced safety score
            safety_analysis = self._calculate_safety_score(sharp_turns, dead_zones, poor_zones)
            
            overview = {
                'route_info': route,
                'statistics': {
                    'total_points': route['total_points'],
                    'total_sharp_turns': len(sharp_turns),
                    'extreme_turns': safety_analysis['hazard_counts']['extreme_turns'],
                    'blind_spots': safety_analysis['hazard_counts']['blind_spots'],
                    'sharp_danger': safety_analysis['hazard_counts']['sharp_danger'],
                    'moderate_turns': safety_analysis['hazard_counts']['moderate_turns'],
                    'dead_zones': dead_zones,
                    'poor_coverage_zones': poor_zones,
                    # Enhanced scoring data
                    'safety_score': safety_analysis['traditional_score'],  # For backward compatibility
                    'risk_points': safety_analysis['risk_points'],
                    'risk_level': safety_analysis['risk_level'],
                    'risk_category': safety_analysis['risk_category'],
                    'safety_rating': safety_analysis['safety_rating'],
                    'color_indicator': safety_analysis['color_indicator'],
                    'scoring_breakdown': safety_analysis['scoring_breakdown'],
                    'total_penalty_points': safety_analysis['total_penalty_points']
                },
                'generated_at': datetime.datetime.now().isoformat()
            }
            
            return overview
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_sharp_turns(self, route_id: str) -> Dict[str, Any]:
        """Get sharp turns data (Page 2: Sharp Turns Analysis)"""
        try:
            sharp_turns = self.db_manager.get_sharp_turns(route_id)
            
            # Get stored images for turns
            turn_images = self.db_manager.get_stored_images(route_id, 'street_view')
            satellite_images = self.db_manager.get_stored_images(route_id, 'satellite')
            
            # Categorize turns
            categorized_turns = {
                'extreme_blind_spots': [t for t in sharp_turns if t['angle'] >= 90],
                'blind_spots': [t for t in sharp_turns if 80 <= t['angle'] < 90],
                'sharp_danger': [t for t in sharp_turns if 70 <= t['angle'] < 80],
                'moderate_turns': [t for t in sharp_turns if 45 <= t['angle'] < 70]
            }
            
            # Add image information to turns
            for category in categorized_turns.values():
                for turn in category:
                    turn['street_view_images'] = [
                        img for img in turn_images 
                        if abs(img['latitude'] - turn['latitude']) < 0.001 and 
                           abs(img['longitude'] - turn['longitude']) < 0.001
                    ]
                    turn['satellite_images'] = [
                        img for img in satellite_images 
                        if abs(img['latitude'] - turn['latitude']) < 0.001 and 
                           abs(img['longitude'] - turn['longitude']) < 0.001
                    ]
            
            return {
                'total_turns': len(sharp_turns),
                'categorized_turns': categorized_turns,
                'summary': {
                    'most_dangerous_angle': max([t['angle'] for t in sharp_turns]) if sharp_turns else 0,
                    'average_angle': sum([t['angle'] for t in sharp_turns]) / len(sharp_turns) if sharp_turns else 0,
                    'critical_turns_count': len(categorized_turns['extreme_blind_spots']) + len(categorized_turns['blind_spots'])
                },
                'images_available': {
                    'street_view': len(turn_images),
                    'satellite': len(satellite_images)
                }
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_points_of_interest(self, route_id: str) -> Dict[str, Any]:
        """Get POI data (Page 3: Points of Interest)"""
        try:
            pois = {
                'hospitals': self.db_manager.get_pois_by_type(route_id, 'hospital'),
                'gas_stations': self.db_manager.get_pois_by_type(route_id, 'gas_station'),
                'schools': self.db_manager.get_pois_by_type(route_id, 'school'),
                'restaurants': self.db_manager.get_pois_by_type(route_id, 'restaurant'),
                'police': self.db_manager.get_pois_by_type(route_id, 'police'),
                'fire_stations': self.db_manager.get_pois_by_type(route_id, 'fire_station')
            }
            
            # Calculate POI statistics
            total_pois = sum(len(poi_list) for poi_list in pois.values())
            
            # Categorize by importance
            emergency_services = len(pois['hospitals']) + len(pois['police']) + len(pois['fire_stations'])
            essential_services = len(pois['gas_stations'])
            other_services = len(pois['schools']) + len(pois['restaurants'])
            
            return {
                'pois_by_type': pois,
                'statistics': {
                    'total_pois': total_pois,
                    'emergency_services': emergency_services,
                    'essential_services': essential_services,
                    'other_services': other_services,
                    'coverage_score': min(100, (emergency_services * 20) + (essential_services * 10) + (other_services * 5))
                },
                'recommendations': self._generate_poi_recommendations(pois)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_network_coverage(self, route_id: str) -> Dict[str, Any]:
        """Get network coverage data (Page 4: Network Analysis)"""
        try:
            coverage_data = self.db_manager.get_network_coverage(route_id)
            
            if not coverage_data:
                return {'error': 'No network coverage data available'}
            
            # Analyze coverage quality
            quality_counts = {}
            for point in coverage_data:
                quality = point['coverage_quality']
                quality_counts[quality] = quality_counts.get(quality, 0) + 1
            
            # Calculate overall score
            total_points = len(coverage_data)
            excellent = quality_counts.get('excellent', 0)
            good = quality_counts.get('good', 0)
            fair = quality_counts.get('fair', 0)
            poor = quality_counts.get('poor', 0)
            dead = quality_counts.get('dead', 0)
            
            overall_score = ((excellent * 100) + (good * 80) + (fair * 60) + (poor * 40) + (dead * 0)) / total_points if total_points > 0 else 0
            
            # Identify problem areas
            dead_zones = [point for point in coverage_data if point['is_dead_zone']]
            poor_zones = [point for point in coverage_data if point['is_poor_coverage']]
            
            return {
                'coverage_analysis': coverage_data,
                'quality_distribution': quality_counts,
                'statistics': {
                    'total_points_analyzed': total_points,
                    'overall_coverage_score': round(overall_score, 1),
                    'dead_zones_count': len(dead_zones),
                    'poor_coverage_count': len(poor_zones),
                    'good_coverage_percentage': round(((excellent + good) / total_points) * 100, 1) if total_points > 0 else 0
                },
                'problem_areas': {
                    'dead_zones': dead_zones,
                    'poor_coverage_zones': poor_zones
                },
                'recommendations': self._generate_network_recommendations(dead_zones, poor_zones)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_weather_data(self, route_id: str) -> Dict[str, Any]:
        """Get weather data (Page 5: Weather Analysis)"""
        try:
            weather_data = self.db_manager.get_weather_data(route_id)
            
            if not weather_data:
                return {'error': 'No weather data available'}
            
            # Analyze weather conditions
            conditions = {}
            temperatures = []
            humidity_levels = []
            wind_speeds = []
            
            for point in weather_data:
                condition = point['weather_condition']
                conditions[condition] = conditions.get(condition, 0) + 1
                
                if point['temperature']:
                    temperatures.append(point['temperature'])
                if point['humidity']:
                    humidity_levels.append(point['humidity'])
                if point['wind_speed']:
                    wind_speeds.append(point['wind_speed'])
            
            # Calculate statistics
            avg_temp = sum(temperatures) / len(temperatures) if temperatures else 0
            avg_humidity = sum(humidity_levels) / len(humidity_levels) if humidity_levels else 0
            avg_wind = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0
            
            # Identify weather risks
            weather_risks = []
            if avg_temp > 40:
                weather_risks.append('Extreme heat - risk of vehicle overheating')
            elif avg_temp < 5:
                weather_risks.append('Cold weather - potential vehicle starting issues')
            
            if avg_wind > 50:
                weather_risks.append('Strong winds - driving difficulty for high vehicles')
            
            if 'Rain' in conditions or 'Thunderstorm' in conditions:
                weather_risks.append('Wet conditions - reduced visibility and traction')
            
            return {
                'weather_points': weather_data,
                'conditions_summary': conditions,
                'statistics': {
                    'points_analyzed': len(weather_data),
                    'average_temperature': round(avg_temp, 1),
                    'average_humidity': round(avg_humidity, 1),
                    'average_wind_speed': round(avg_wind, 1),
                    'temperature_range': {
                        'min': min(temperatures) if temperatures else 0,
                        'max': max(temperatures) if temperatures else 0
                    }
                },
                'weather_risks': weather_risks,
                'recommendations': self._generate_weather_recommendations(avg_temp, conditions, weather_risks)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_compliance_data(self, route_id: str, vehicle_type: str = 'heavy_goods_vehicle') -> Dict[str, Any]:
        """Get compliance data (Page 6: Regulatory Compliance)"""
        try:
            route = self.db_manager.get_route(route_id)
            if not route:
                return {'error': 'Route not found'}
            
            # Vehicle type configurations
            vehicle_configs = {
                'heavy_goods_vehicle': {
                    'weight': 18000,
                    'category': 'Heavy Goods Vehicle',
                    'ais_140_required': True,
                    'permit_complexity': 'HIGH',
                    'rtsp_applicable': True
                },
                'medium_goods_vehicle': {
                    'weight': 8000,
                    'category': 'Medium Goods Vehicle',
                    'ais_140_required': True,
                    'permit_complexity': 'MEDIUM',
                    'rtsp_applicable': True
                },
                'light_vehicle': {
                    'weight': 2500,
                    'category': 'Light Motor Vehicle',
                    'ais_140_required': False,
                    'permit_complexity': 'LOW',
                    'rtsp_applicable': False
                }
            }
            
            vehicle_config = vehicle_configs.get(vehicle_type, vehicle_configs['heavy_goods_vehicle'])
            
            # Calculate compliance score
            compliance_score = 100
            compliance_issues = []
            
            # Check route duration for RTSP compliance
            if vehicle_config['rtsp_applicable']:
                try:
                    duration_str = route['duration'] or '0 hours'
                    duration_hours = self._parse_duration_to_hours(duration_str)
                    if duration_hours > 10:
                        compliance_score -= 25
                        compliance_issues.append('RTSP violation - driving time exceeds 10 hours')
                except:
                    pass
            
            # AIS-140 compliance
            if vehicle_config['ais_140_required']:
                compliance_score -= 20  # Assume not installed
                compliance_issues.append('AIS-140 GPS tracking device required')
            
            # Distance-based permits
            distance_str = route['distance'] or '0 km'
            distance_km = self._parse_distance_to_km(distance_str)
            if distance_km > 500:
                compliance_score -= 15
                compliance_issues.append('Long distance route - additional permits may be required')
            
            # Weight-based restrictions
            if vehicle_config['weight'] > 16000:
                compliance_score -= 10
                compliance_issues.append('Heavy vehicle - weight restrictions may apply')
            
            return {
                'vehicle_info': {
                    'type': vehicle_type,
                    'category': vehicle_config['category'],
                    'weight': vehicle_config['weight'],
                    'ais_140_required': vehicle_config['ais_140_required']
                },
                'route_analysis': {
                    'distance': route['distance'],
                    'duration': route['duration'],
                    'estimated_duration_hours': self._parse_duration_to_hours(route['duration'] or '0'),
                    'from_address': route['from_address'],
                    'to_address': route['to_address']
                },
                'compliance_assessment': {
                    'overall_score': max(0, compliance_score),
                    'compliance_level': 'COMPLIANT' if compliance_score >= 80 else 'NEEDS ATTENTION' if compliance_score >= 60 else 'NON-COMPLIANT',
                    'issues_identified': compliance_issues,
                    'critical_requirements': [
                        'Valid driving license for vehicle category',
                        'Vehicle registration and insurance',
                        'Route permits for interstate travel',
                        'AIS-140 GPS device (if required)',
                        'Compliance with driving time limits'
                    ]
                },
                'recommendations': self._generate_compliance_recommendations(vehicle_type, compliance_issues)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_elevation_data(self, route_id: str) -> Dict[str, Any]:
        """Get elevation data with better error handling and debugging"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # First, check if we have ANY elevation data for this route
                cursor.execute("SELECT COUNT(*) as count FROM elevation_data WHERE route_id = ?", (route_id,))
                count_result = cursor.fetchone()
                record_count = count_result['count'] if count_result else 0
                
                print(f"🔍 Found {record_count} elevation records for route {route_id}")
                
                if record_count == 0:
                    return {'error': f'No elevation data found for route {route_id}. Google Elevation API may have failed during analysis.'}
                
                cursor.execute("""
                    SELECT * FROM elevation_data 
                    WHERE route_id = ?
                    ORDER BY id
                """, (route_id,))
                
                elevation_data = [dict(row) for row in cursor.fetchall()]
                
                if not elevation_data:
                    return {'error': 'No elevation data available'}
                
                # Calculate elevation statistics
                elevations = [point['elevation'] for point in elevation_data]
                
                min_elevation = min(elevations)
                max_elevation = max(elevations)
                avg_elevation = sum(elevations) / len(elevations)
                elevation_range = max_elevation - min_elevation
                
                # Identify significant elevation changes
                significant_changes = []
                for i in range(1, len(elevation_data)):
                    prev_elevation = elevation_data[i-1]['elevation']
                    curr_elevation = elevation_data[i]['elevation']
                    change = abs(curr_elevation - prev_elevation)
                    
                    if change > 50:  # 50m threshold for significant change
                        significant_changes.append({
                            'location': {
                                'latitude': elevation_data[i]['latitude'],
                                'longitude': elevation_data[i]['longitude']
                            },
                            'elevation_change': change,
                            'type': 'ascent' if curr_elevation > prev_elevation else 'descent',
                            'from_elevation': prev_elevation,
                            'to_elevation': curr_elevation
                        })
                
                # Classify terrain
                terrain_type = self._classify_terrain(elevation_range, avg_elevation)
                driving_difficulty = self._assess_driving_difficulty(significant_changes)
                fuel_impact = self._assess_fuel_impact(significant_changes)
                
                return {
                    'elevation_points': elevation_data,
                    'statistics': {
                        'min_elevation': round(min_elevation, 1),
                        'max_elevation': round(max_elevation, 1),
                        'average_elevation': round(avg_elevation, 1),
                        'elevation_range': round(elevation_range, 1),
                        'total_points': len(elevation_data)
                    },
                    'significant_changes': significant_changes,
                    'terrain_analysis': {
                        'terrain_type': terrain_type,
                        'driving_difficulty': driving_difficulty,
                        'fuel_impact': fuel_impact
                    }
                }
                
        except Exception as e:
            print(f"❌ Error getting elevation data: {e}")
            return {'error': str(e)}
    
    def get_traffic_data(self, route_id: str) -> Dict[str, Any]:
        """Get traffic data from database - REAL IMPLEMENTATION"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check if we have traffic data
                cursor.execute("SELECT COUNT(*) as count FROM traffic_data WHERE route_id = ?", (route_id,))
                count_result = cursor.fetchone()
                record_count = count_result['count'] if count_result else 0
                
                print(f"🔍 Found {record_count} traffic records for route {route_id}")
                
                if record_count == 0:
                    return {'error': f'No traffic data found for route {route_id}. Traffic analysis may not have been completed.'}
                
                cursor.execute("""
                    SELECT * FROM traffic_data 
                    WHERE route_id = ?
                    ORDER BY id
                """, (route_id,))
                
                traffic_data = [dict(row) for row in cursor.fetchall()]
                
                # Analyze traffic statistics
                congestion_counts = {}
                total_segments = len(traffic_data)
                avg_travel_time_index = 0
                avg_current_speed = 0
                avg_free_flow_speed = 0
                
                for data in traffic_data:
                    congestion = data['congestion_level']
                    congestion_counts[congestion] = congestion_counts.get(congestion, 0) + 1
                    avg_travel_time_index += data.get('travel_time_index', 1.0)
                    avg_current_speed += data.get('current_speed', 0)
                    avg_free_flow_speed += data.get('free_flow_speed', 0)
                
                # Calculate averages
                if total_segments > 0:
                    avg_travel_time_index /= total_segments
                    avg_current_speed /= total_segments
                    avg_free_flow_speed /= total_segments
                
                # Calculate overall traffic score
                heavy_segments = congestion_counts.get('HEAVY', 0)
                moderate_segments = congestion_counts.get('MODERATE', 0)
                light_segments = congestion_counts.get('LIGHT', 0)
                free_flow_segments = congestion_counts.get('FREE_FLOW', 0)
                
                # Traffic score (0-100, higher is better)
                traffic_score = ((free_flow_segments * 100) + (light_segments * 75) + 
                            (moderate_segments * 50) + (heavy_segments * 25)) / total_segments if total_segments > 0 else 0
                
                return {
                    'traffic_analysis': traffic_data,
                    'statistics': {
                        'total_segments_analyzed': total_segments,
                        'average_travel_time_index': round(avg_travel_time_index, 2),
                        'average_current_speed': round(avg_current_speed, 1),
                        'average_free_flow_speed': round(avg_free_flow_speed, 1),
                        'overall_traffic_score': round(traffic_score, 1),
                        'congestion_distribution': congestion_counts,
                        'traffic_condition': self._get_traffic_condition(traffic_score)
                    },
                    'congestion_analysis': {
                        'heavy_traffic_segments': heavy_segments,
                        'moderate_traffic_segments': moderate_segments,
                        'light_traffic_segments': light_segments,
                        'free_flow_segments': free_flow_segments,
                        'worst_congestion_percentage': round((heavy_segments / total_segments) * 100, 1) if total_segments > 0 else 0
                    },
                    'recommendations': self._generate_traffic_recommendations(traffic_score, congestion_counts)
                }
                
        except Exception as e:
            print(f"❌ Error getting traffic data: {e}")
            return {'error': str(e)}
    def _get_traffic_condition(self, score: float) -> str:
        """Get traffic condition based on score"""
        if score >= 80:
            return "EXCELLENT"
        elif score >= 60:
            return "GOOD"
        elif score >= 40:
            return "MODERATE"
        elif score >= 20:
            return "POOR"
        else:
            return "SEVERE"

    def _generate_traffic_recommendations(self, score: float, congestion_counts: Dict) -> List[str]:
        """Generate traffic-based recommendations"""
        recommendations = []
        
        heavy_count = congestion_counts.get('HEAVY', 0)
        moderate_count = congestion_counts.get('MODERATE', 0)
        
        if heavy_count > 0:
            recommendations.append(f"Route has {heavy_count} heavily congested segments - consider alternative routes")
            recommendations.append("Plan for significant delays during peak hours")
        
        if moderate_count > 0:
            recommendations.append(f"{moderate_count} segments have moderate traffic - allow extra travel time")
        
        if score < 50:
            recommendations.append("Consider traveling during off-peak hours to avoid traffic")
            recommendations.append("Use real-time navigation apps for dynamic route optimization")
        
        recommendations.extend([
            "Check current traffic conditions before departure",
            "Consider public transportation alternatives for heavily congested routes",
            "Plan rest stops during low-traffic segments"
        ])
        
        return recommendations
    def get_emergency_data(self, route_id: str) -> Dict[str, Any]:
        """Get emergency preparedness data (Page 9: Emergency Planning)"""
        try:
            # Get emergency services POIs
            hospitals = self.db_manager.get_pois_by_type(route_id, 'hospital')
            police = self.db_manager.get_pois_by_type(route_id, 'police')
            fire_stations = self.db_manager.get_pois_by_type(route_id, 'fire_station')
            
            # Get network coverage for emergency communication
            network_coverage = self.db_manager.get_network_coverage(route_id)
            dead_zones = [point for point in network_coverage if point['is_dead_zone']]
            
            # Calculate emergency preparedness score
            emergency_score = 100
            
            if len(hospitals) == 0:
                emergency_score -= 30
            elif len(hospitals) < 3:
                emergency_score -= 15
            
            if len(police) == 0:
                emergency_score -= 20
            elif len(police) < 2:
                emergency_score -= 10
            
            if len(fire_stations) == 0:
                emergency_score -= 20
            elif len(fire_stations) < 2:
                emergency_score -= 10
            
            if len(dead_zones) > 5:
                emergency_score -= 20
            elif len(dead_zones) > 2:
                emergency_score -= 10
            
            return {
                'emergency_services': {
                    'hospitals': hospitals,
                    'police_stations': police,
                    'fire_stations': fire_stations
                },
                'communication_analysis': {
                    'total_coverage_points': len(network_coverage),
                    'dead_zones': len(dead_zones),
                    'communication_reliability': 'HIGH' if len(dead_zones) < 3 else 'MEDIUM' if len(dead_zones) < 6 else 'LOW'
                },
                'preparedness_assessment': {
                    'emergency_score': max(0, emergency_score),
                    'preparedness_level': 'EXCELLENT' if emergency_score >= 80 else 'GOOD' if emergency_score >= 60 else 'NEEDS IMPROVEMENT',
                    'critical_gaps': self._identify_emergency_gaps(hospitals, police, fire_stations, dead_zones)
                },
                'emergency_contacts': {
                    'national_emergency': '112',
                    'police': '100',
                    'fire': '101',
                    'ambulance': '108',
                    'highway_patrol': '1033'
                },
                'recommendations': self._generate_emergency_recommendations(emergency_score, dead_zones)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # Helper methods
    def _calculate_safety_score(self, sharp_turns: List[Dict], dead_zones: int, poor_zones: int) -> Dict:
        """Calculate comprehensive safety score with detailed breakdown"""
        
        # Categorize sharp turns
        extreme_turns = len([t for t in sharp_turns if t['angle'] >= 90])
        blind_spots = len([t for t in sharp_turns if 80 <= t['angle'] < 90])
        sharp_danger = len([t for t in sharp_turns if 70 <= t['angle'] < 80])
        moderate_turns = len([t for t in sharp_turns if 45 <= t['angle'] < 70])
        
        # Calculate individual penalty points
        penalties = {
            'extreme_turns': extreme_turns * 20,
            'blind_spots': blind_spots * 15,
            'sharp_danger': sharp_danger * 10,
            'dead_zones': dead_zones * 8,
            'poor_coverage': poor_zones * 4
        }
        
        total_penalty_points = sum(penalties.values())
        
        # Calculate traditional score (0-100 scale)
        base_score = 100
        traditional_score = max(0, min(100, base_score - total_penalty_points))
        
        # Calculate risk points (higher = more dangerous)
        risk_points = total_penalty_points
        
        # Determine risk level based on risk points
        if risk_points >= 150:
            risk_level = "CRITICAL"
            risk_category = "EXTREME RISK"
            color_indicator = "RED"
        elif risk_points >= 100:
            risk_level = "HIGH"
            risk_category = "HIGH RISK"
            color_indicator = "ORANGE"
        elif risk_points >= 50:
            risk_level = "MODERATE"
            risk_category = "MODERATE RISK"
            color_indicator = "YELLOW"
        elif risk_points >= 20:
            risk_level = "LOW"
            risk_category = "LOW RISK"
            color_indicator = "BLUE"
        else:
            risk_level = "MINIMAL"
            risk_category = "SAFE ROUTE"
            color_indicator = "GREEN"
        
        # Create detailed scoring breakdown
        scoring_breakdown = [
            {
                'hazard_type': 'Extreme Turns (≥90°)',
                'count': extreme_turns,
                'penalty_per_item': 20,
                'total_penalty': penalties['extreme_turns'],
                'risk_level': 'CRITICAL' if extreme_turns > 0 else 'NONE'
            },
            {
                'hazard_type': 'High-Risk Blind Spots (80-90°)',
                'count': blind_spots,
                'penalty_per_item': 15,
                'total_penalty': penalties['blind_spots'],
                'risk_level': 'HIGH' if blind_spots > 0 else 'NONE'
            },
            {
                'hazard_type': 'Sharp Danger Zones (70-80°)',
                'count': sharp_danger,
                'penalty_per_item': 10,
                'total_penalty': penalties['sharp_danger'],
                'risk_level': 'MODERATE' if sharp_danger > 0 else 'NONE'
            },
            {
                'hazard_type': 'Network Dead Zones',
                'count': dead_zones,
                'penalty_per_item': 8,
                'total_penalty': penalties['dead_zones'],
                'risk_level': 'HIGH' if dead_zones > 0 else 'NONE'
            },
            {
                'hazard_type': 'Poor Coverage Areas',
                'count': poor_zones,
                'penalty_per_item': 4,
                'total_penalty': penalties['poor_coverage'],
                'risk_level': 'LOW' if poor_zones > 0 else 'NONE'
            }
        ]
        
        # Calculate percentages of total risk
        for item in scoring_breakdown:
            if total_penalty_points > 0:
                item['percentage_of_total_risk'] = round((item['total_penalty'] / total_penalty_points) * 100, 1)
            else:
                item['percentage_of_total_risk'] = 0
        
        return {
            'traditional_score': traditional_score,
            'risk_points': risk_points,
            'risk_level': risk_level,
            'risk_category': risk_category,
            'color_indicator': color_indicator,
            'total_penalty_points': total_penalty_points,
            'scoring_breakdown': scoring_breakdown,
            'hazard_counts': {
                'extreme_turns': extreme_turns,
                'blind_spots': blind_spots,
                'sharp_danger': sharp_danger,
                'moderate_turns': moderate_turns,
                'dead_zones': dead_zones,
                'poor_coverage': poor_zones
            },
            'safety_rating': self._get_safety_rating_from_points(risk_points)
        }
    def _get_safety_rating_from_points(self, risk_points: int) -> str:
        """Get safety rating based on risk points"""
        if risk_points >= 150:
            return 'CRITICAL RISK'
        elif risk_points >= 100:
            return 'HIGH RISK'
        elif risk_points >= 50:
            return 'MODERATE RISK'
        elif risk_points >= 20:
            return 'LOW RISK'
        else:
            return 'SAFE ROUTE'
    def _get_safety_rating(self, score: int) -> str:
        """Get safety rating based on score"""
        if score >= 90:
            return 'EXCELLENT'
        elif score >= 80:
            return 'GOOD'
        elif score >= 70:
            return 'FAIR'
        elif score >= 60:
            return 'POOR'
        else:
            return 'DANGEROUS'
    
    def _parse_duration_to_hours(self, duration_str: str) -> float:
        """Parse duration string to hours"""
        try:
            import re
            hours = 0
            
            # Extract hours
            hour_match = re.search(r'(\d+)\s*hour', duration_str.lower())
            if hour_match:
                hours += int(hour_match.group(1))
            
            # Extract minutes
            min_match = re.search(r'(\d+)\s*min', duration_str.lower())
            if min_match:
                hours += int(min_match.group(1)) / 60
            
            return hours
        except:
            return 0
    
    def _parse_distance_to_km(self, distance_str: str) -> float:
        """Parse distance string to kilometers"""
        try:
            import re
            if 'km' in distance_str.lower():
                km_match = re.search(r'([\d,]+)', distance_str)
                if km_match:
                    return float(km_match.group(1).replace(',', ''))
            return 0
        except:
            return 0
    
    def _generate_poi_recommendations(self, pois: Dict) -> List[str]:
        """Generate POI-based recommendations"""
        recommendations = []
        
        if len(pois['hospitals']) == 0:
            recommendations.append("No hospitals found along route - identify nearest medical facilities")
        
        if len(pois['gas_stations']) < 3:
            recommendations.append("Limited fuel stations - plan refueling stops in advance")
        
        if len(pois['police']) == 0:
            recommendations.append("No police stations identified - note emergency contact numbers")
        
        return recommendations
    
    def _generate_network_recommendations(self, dead_zones: List, poor_zones: List) -> List[str]:
        """Generate network coverage recommendations"""
        recommendations = []
        
        if len(dead_zones) > 0:
            recommendations.append(f"Route has {len(dead_zones)} dead zones - consider satellite communication device")
        
        if len(poor_zones) > 3:
            recommendations.append("Multiple poor coverage areas - download offline maps before travel")
        
        recommendations.append("Inform someone of your route and expected arrival time")
        
        return recommendations
    
    def _generate_weather_recommendations(self, avg_temp: float, conditions: Dict, risks: List) -> List[str]:
        """Generate weather-based recommendations"""
        recommendations = []
        
        if avg_temp > 35:
            recommendations.append("High temperatures - check vehicle cooling system and carry extra water")
        
        if avg_temp < 10:
            recommendations.append("Cold weather - check battery and ensure proper engine fluids")
        
        if 'Rain' in conditions:
            recommendations.append("Wet conditions expected - reduce speed and increase following distance")
        
        return recommendations
    
    def _generate_compliance_recommendations(self, vehicle_type: str, issues: List) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = [
            "Ensure all vehicle documents are current and accessible",
            "Verify driver license category matches vehicle type",
            "Check route-specific permits and restrictions"
        ]
        
        if 'AIS-140' in str(issues):
            recommendations.append("Install AIS-140 compliant GPS tracking device")
        
        if 'RTSP' in str(issues):
            recommendations.append("Plan mandatory rest stops to comply with driving time limits")
        
        return recommendations
    
    def _classify_terrain(self, elevation_range: float, avg_elevation: float) -> str:
        """Classify terrain type"""
        if elevation_range > 1000:
            return "MOUNTAINOUS"
        elif elevation_range > 500:
            return "HILLY"
        elif avg_elevation > 1500:
            return "HIGH_PLATEAU"
        else:
            return "PLAINS"
    
    def _assess_driving_difficulty(self, significant_changes: List) -> str:
        """Assess driving difficulty based on elevation changes"""
        if len(significant_changes) > 10:
            return "HIGH"
        elif len(significant_changes) > 5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _assess_fuel_impact(self, significant_changes: List) -> str:
        """Assess fuel consumption impact"""
        ascents = len([c for c in significant_changes if c['type'] == 'ascent'])
        if ascents > 5:
            return "HIGH - Increased fuel consumption expected"
        elif ascents > 2:
            return "MEDIUM - Some increase in fuel consumption"
        else:
            return "LOW - Minimal impact on fuel consumption"
    
    def _identify_emergency_gaps(self, hospitals: List, police: List, fire_stations: List, dead_zones: List) -> List[str]:
        """Identify critical emergency preparedness gaps"""
        gaps = []
        
        if len(hospitals) == 0:
            gaps.append("No hospitals identified along route")
        
        if len(police) == 0:
            gaps.append("No police stations identified")
        
        if len(fire_stations) == 0:
            gaps.append("No fire stations identified")
        
        if len(dead_zones) > 5:
            gaps.append("Multiple communication dead zones")
        
        return gaps
    
    def _generate_emergency_recommendations(self, emergency_score: int, dead_zones: List) -> List[str]:
        """Generate emergency preparedness recommendations"""
        recommendations = [
            "Carry first aid kit and emergency supplies",
            "Keep emergency contact numbers readily available",
            "Inform someone of your travel plans and timeline"
        ]
        
        if emergency_score < 70:
            recommendations.append("Route has limited emergency services - extra caution advised")
        
        if len(dead_zones) > 3:
            recommendations.append("Consider satellite communication device for dead zones")
        
        return recommendations
    # ADD THESE NEW METHODS in the RouteAPI class:

    def get_route_highways(self, route_id: str) -> Dict[str, Any]:
        """Get highway information for route"""
        try:
            highways = self.db_manager.get_route_highways(route_id)
            
            if not highways:
                return {'error': 'No highway data found for this route'}
            
            # Format highway names as comma-separated string
            highway_names = [highway['highway_name'] for highway in highways]
            highway_names_str = ', '.join(highway_names)
            
            # Categorize highways by type
            highway_by_type = {}
            total_length = 0
            
            for highway in highways:
                highway_type = highway['highway_type']
                if highway_type not in highway_by_type:
                    highway_by_type[highway_type] = []
                highway_by_type[highway_type].append(highway)
                total_length += highway.get('length_km', 0)
            
            return {
                'highways': highways,
                'highway_names_string': highway_names_str,
                'highway_by_type': highway_by_type,
                'statistics': {
                    'total_highways': len(highways),
                    'total_highway_length': round(total_length, 2),
                    'highway_types': list(highway_by_type.keys())
                }
            }
            
        except Exception as e:
            return {'error': str(e)}

    def get_route_terrain(self, route_id: str) -> Dict[str, Any]:
        """Get terrain classification for route"""
        try:
            terrain = self.db_manager.get_route_terrain(route_id)
            
            if not terrain:
                return {'error': 'No terrain data found for this route'}
            
            # Parse classification details
            import json
            classification_details = {}
            try:
                classification_details = json.loads(terrain.get('classification_details', '{}'))
            except:
                pass
            
            return {
                'terrain_classification': terrain,
                'terrain_type': terrain.get('terrain_type', 'Unknown'),
                'confidence_score': terrain.get('terrain_score', 0),
                'elevation_variance': terrain.get('elevation_variance', 0),
                'urban_density_score': terrain.get('urban_density_score', 0),
                'classification_details': classification_details,
                'terrain_description': self._get_terrain_description(terrain.get('terrain_type', 'Unknown'))
            }
            
        except Exception as e:
            return {'error': str(e)}

    def get_enhanced_route_overview(self, route_id: str) -> Dict[str, Any]:
        """Get comprehensive route overview data for enhanced PDF"""
        try:
            # Get all enhanced overview data
            overview_data = self.db_manager.get_enhanced_route_overview_data(route_id)
            
            if not overview_data:
                return {'error': 'Route not found'}
            
            # Get highway and terrain data
            highway_data = self.get_route_highways(route_id)
            terrain_data = self.get_route_terrain(route_id)
            
            # Combine all data
            enhanced_overview = {
                'route_info': overview_data.get('route_info', {}),
                'statistics': overview_data.get('statistics', {}),
                'highways': highway_data,
                'terrain': terrain_data,
                'route_points': overview_data.get('route_points', []),
                'sharp_turns': overview_data.get('sharp_turns', []),
                'pois': overview_data.get('pois', {}),
                'enhanced_features': {
                    'has_highway_data': not highway_data.get('error'),
                    'has_terrain_data': not terrain_data.get('error'),
                    'highway_count': len(overview_data.get('highways', [])),
                    'terrain_confidence': terrain_data.get('confidence_score', 0) if not terrain_data.get('error') else 0
                }
            }
            
            return enhanced_overview
            
        except Exception as e:
            return {'error': str(e)}

    def _get_terrain_description(self, terrain_type: str) -> str:
        """Get descriptive text for terrain type"""
        descriptions = {
            'Urban Dense': 'High-density urban area with frequent traffic and numerous facilities',
            'Urban Moderate': 'Moderate urban development with good infrastructure',
            'Semi-Urban Plains': 'Mixed development area transitioning between urban and rural',
            'Rural Plains': 'Flat rural area with minimal development',
            'Rural Hilly': 'Hilly rural terrain with challenging elevation changes',
            'Urban Hilly': 'Hilly urban area with steep gradients and urban infrastructure',
            'Mountainous Semi-Urban': 'Mountainous terrain with some development',
            'Rural Mountainous': 'Remote mountainous area with minimal infrastructure',
            'Mixed Terrain': 'Varied terrain with multiple characteristics'
        }
        return descriptions.get(terrain_type, 'Terrain characteristics not fully analyzed')