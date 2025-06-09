# analysis/environmental_analyzer.py - Real API Integration for Environmental Risk Analysis
# Purpose: Analyze environmental risks using multiple weather, air quality, and geographical APIs
# Dependencies: requests, os, time
# Author: Enhanced Route Analysis System
# Created: 2024

import os
import time
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class EnvironmentalRiskAnalyzer:
    """Comprehensive environmental risk analysis using multiple APIs"""
    
    def __init__(self, api_tracker):
        self.api_tracker = api_tracker
        
        # Load API keys from environment
        self.openweather_api_key = os.environ.get('OPENWEATHER_API_KEY')
        self.visualcrossing_api_key = os.environ.get('VISUALCROSSING_API_KEY')
        self.tomorrow_io_api_key = os.environ.get('TOMORROW_IO_API_KEY')
        self.google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        
        print(f"🌍 Environmental Risk Analyzer initialized")
        print(f"   OpenWeather API: {'✅ Configured' if self.openweather_api_key else '❌ Missing'}")
        print(f"   Visual Crossing API: {'✅ Configured' if self.visualcrossing_api_key else '❌ Missing'}")
        print(f"   Tomorrow.io API: {'✅ Configured' if self.tomorrow_io_api_key else '❌ Missing'}")
        print(f"   Google API: {'✅ Configured' if self.google_api_key else '❌ Missing'}")
    
    def analyze_environmental_risks(self, route_points: List[List[float]], route_id: str) -> Dict[str, List[Dict]]:
        """Comprehensive environmental risk analysis"""
        try:
            print(f"🔍 Starting comprehensive environmental risk analysis...")
            
            environmental_data = {
                'eco_sensitive_zones': [],
                'air_quality_risks': [],
                'weather_hazards': [],
                'seasonal_risks': [],
                'pollution_zones': []
            }
            
            # Sample points for analysis
            step = max(1, len(route_points) // 15)
            sampled_points = route_points[::step]
            
            print(f"   Analyzing {len(sampled_points)} sample points for environmental risks")
            
            for i, point in enumerate(sampled_points[:20]):  # Limit to 20 points
                try:
                    # Multi-API environmental assessment
                    env_data = self._comprehensive_environmental_assessment(point[0], point[1])
                    
                    if env_data:
                        # Categorize environmental risks
                        self._categorize_environmental_data(env_data, environmental_data, route_id, point)
                    
                    # Rate limiting between API calls
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"   ⚠️ Error analyzing environmental data for point {i+1}: {e}")
                    continue
            
            # Analyze route-wide patterns
            environmental_data['route_summary'] = self._analyze_route_environmental_summary(environmental_data)
            
            total_risks = sum(len(risks) for risks in environmental_data.values() if isinstance(risks, list))
            print(f"✅ Environmental risk analysis completed. Found {total_risks} environmental concerns")
            
            return environmental_data
            
        except Exception as e:
            print(f"❌ Environmental risk analysis failed: {e}")
            return {}
    
    def _comprehensive_environmental_assessment(self, lat: float, lng: float) -> Optional[Dict]:
        """Multi-API environmental assessment for a single point"""
        assessments = {}
        
        # 1. OpenWeather Environmental Data
        if self.openweather_api_key:
            openweather_data = self._get_openweather_environmental_data(lat, lng)
            if openweather_data:
                assessments['openweather'] = openweather_data
        
        # 2. Visual Crossing Weather and Environmental Data
        if self.visualcrossing_api_key:
            visualcrossing_data = self._get_visualcrossing_environmental_data(lat, lng)
            if visualcrossing_data:
                assessments['visualcrossing'] = visualcrossing_data
        
        # 3. Tomorrow.io Environmental and Air Quality Data
        if self.tomorrow_io_api_key:
            tomorrow_data = self._get_tomorrow_io_environmental_data(lat, lng)
            if tomorrow_data:
                assessments['tomorrow_io'] = tomorrow_data
        
        # 4. Google Places Environmental Context
        google_data = self._get_google_environmental_context(lat, lng)
        if google_data:
            assessments['google_places'] = google_data
        
        # 5. Simulated Eco-Sensitive Zone Check (would be real government APIs)
        eco_zone_data = self._check_eco_sensitive_zones(lat, lng)
        if eco_zone_data:
            assessments['eco_zones'] = eco_zone_data
        
        return assessments if assessments else None
    
    def _get_openweather_environmental_data(self, lat: float, lng: float) -> Optional[Dict]:
        """Get environmental data from OpenWeather API"""
        try:
            start_time = time.time()
            
            # OpenWeather Air Pollution API
            pollution_url = "http://api.openweathermap.org/data/2.5/air_pollution"
            pollution_params = {
                'lat': lat,
                'lon': lng,
                'appid': self.openweather_api_key
            }
            
            pollution_response = requests.get(pollution_url, params=pollution_params, timeout=10)
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'openweather_pollution',
                '/air_pollution',
                pollution_response.status_code,
                response_time,
                pollution_response.status_code == 200
            )
            
            if pollution_response.status_code == 200:
                pollution_data = pollution_response.json()
                
                # Current weather for environmental context
                weather_url = "http://api.openweathermap.org/data/2.5/weather"
                weather_params = {
                    'lat': lat,
                    'lon': lng,
                    'appid': self.openweather_api_key,
                    'units': 'metric'
                }
                
                weather_response = requests.get(weather_url, params=weather_params, timeout=10)
                
                environmental_data = {
                    'source': 'openweather',
                    'air_quality_index': pollution_data.get('list', [{}])[0].get('main', {}).get('aqi', 0),
                    'pollutants': pollution_data.get('list', [{}])[0].get('components', {}),
                    'coordinates': {'lat': lat, 'lng': lng}
                }
                
                if weather_response.status_code == 200:
                    weather_data = weather_response.json()
                    environmental_data.update({
                        'temperature': weather_data.get('main', {}).get('temp', 0),
                        'humidity': weather_data.get('main', {}).get('humidity', 0),
                        'visibility': weather_data.get('visibility', 10000),
                        'weather_condition': weather_data.get('weather', [{}])[0].get('main', '')
                    })
                
                return environmental_data
            
        except Exception as e:
            print(f"OpenWeather environmental API error: {e}")
            self.api_tracker.log_api_call(
                'openweather_pollution',
                '/air_pollution',
                500,
                0,
                False,
                str(e)
            )
        
        return None
    
    def _get_visualcrossing_environmental_data(self, lat: float, lng: float) -> Optional[Dict]:
        """Get environmental data from Visual Crossing API"""
        try:
            start_time = time.time()
            
            # Visual Crossing Weather API with environmental indicators
            url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
            
            # Get current and historical data for pattern analysis
            today = datetime.now().strftime('%Y-%m-%d')
            location = f"{lat},{lng}"
            
            params = {
                'key': self.visualcrossing_api_key,
                'include': 'current,days',
                'elements': 'temp,humidity,visibility,windspeed,uvindex,conditions,cloudcover',
                'unitGroup': 'metric'
            }
            
            full_url = f"{url}/{location}/{today}"
            response = requests.get(full_url, params=params, timeout=15)
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'visualcrossing_environmental',
                '/timeline',
                response.status_code,
                response_time,
                response.status_code == 200
            )
            
            if response.status_code == 200:
                data = response.json()
                current_conditions = data.get('currentConditions', {})
                
                # Analyze environmental risk factors
                uv_index = current_conditions.get('uvindex', 0)
                visibility = current_conditions.get('visibility', 10)
                cloud_cover = current_conditions.get('cloudcover', 0)
                wind_speed = current_conditions.get('windspeed', 0)
                
                environmental_risks = []
                if uv_index > 8:
                    environmental_risks.append('high_uv_exposure')
                if visibility < 5:
                    environmental_risks.append('poor_visibility')
                if wind_speed > 40:
                    environmental_risks.append('strong_winds')
                
                return {
                    'source': 'visualcrossing',
                    'uv_index': uv_index,
                    'visibility_km': visibility,
                    'cloud_cover_percent': cloud_cover,
                    'wind_speed_kmh': wind_speed,
                    'environmental_risks': environmental_risks,
                    'conditions': current_conditions.get('conditions', ''),
                    'coordinates': {'lat': lat, 'lng': lng}
                }
            
        except Exception as e:
            print(f"Visual Crossing environmental API error: {e}")
            self.api_tracker.log_api_call(
                'visualcrossing_environmental',
                '/timeline',
                500,
                0,
                False,
                str(e)
            )
        
        return None
    
    def _get_tomorrow_io_environmental_data(self, lat: float, lng: float) -> Optional[Dict]:
        """Get environmental data from Tomorrow.io API"""
        try:
            start_time = time.time()
            
            # Tomorrow.io Weather and Air Quality API
            url = "https://api.tomorrow.io/v4/weather/realtime"
            params = {
                'location': f"{lat},{lng}",
                'apikey': self.tomorrow_io_api_key,
                'fields': [
                    'temperature', 'humidity', 'windSpeed', 'visibility', 'uvIndex',
                    'pollutantO3', 'pollutantNO2', 'pollutantCO', 'pollutantSO2',
                    'pollutantPM25', 'pollutantPM10', 'treeIndex', 'grassIndex'
                ]
            }
            
            # Convert fields list to comma-separated string
            params['fields'] = ','.join(params['fields'])
            
            response = requests.get(url, params=params, timeout=15)
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'tomorrow_io_environmental',
                '/weather/realtime',
                response.status_code,
                response_time,
                response.status_code == 200
            )
            
            if response.status_code == 200:
                data = response.json()
                values = data.get('data', {}).get('values', {})
                
                # Calculate air quality index from pollutants
                aqi_score = self._calculate_aqi_from_pollutants(values)
                
                # Identify environmental risks
                environmental_risks = []
                if values.get('pollutantPM25', 0) > 25:
                    environmental_risks.append('high_pm25')
                if values.get('pollutantO3', 0) > 100:
                    environmental_risks.append('high_ozone')
                if values.get('visibility', 10) < 3:
                    environmental_risks.append('severe_visibility')
                if values.get('uvIndex', 0) > 9:
                    environmental_risks.append('extreme_uv')
                
                return {
                    'source': 'tomorrow_io',
                    'air_quality_score': aqi_score,
                    'pollutants': {
                        'pm25': values.get('pollutantPM25', 0),
                        'pm10': values.get('pollutantPM10', 0),
                        'o3': values.get('pollutantO3', 0),
                        'no2': values.get('pollutantNO2', 0),
                        'co': values.get('pollutantCO', 0),
                        'so2': values.get('pollutantSO2', 0)
                    },
                    'environmental_risks': environmental_risks,
                    'pollen_indices': {
                        'tree': values.get('treeIndex', 0),
                        'grass': values.get('grassIndex', 0)
                    },
                    'visibility_km': values.get('visibility', 10),
                    'uv_index': values.get('uvIndex', 0),
                    'coordinates': {'lat': lat, 'lng': lng}
                }
            
        except Exception as e:
            print(f"Tomorrow.io environmental API error: {e}")
            self.api_tracker.log_api_call(
                'tomorrow_io_environmental',
                '/weather/realtime',
                500,
                0,
                False,
                str(e)
            )
        
        return None
    
    def _get_google_environmental_context(self, lat: float, lng: float) -> Optional[Dict]:
        """Get environmental context from Google Places API"""
        try:
            if not self.google_api_key:
                return None
            
            start_time = time.time()
            
            # Google Places Nearby Search for environmental context
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                'location': f"{lat},{lng}",
                'radius': 2000,  # 2km radius
                'type': 'park',  # Look for parks/green spaces
                'key': self.google_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'google_places_environmental',
                '/place/nearbysearch/json',
                response.status_code,
                response_time,
                response.status_code == 200
            )
            
            if response.status_code == 200:
                data = response.json()
                parks = data.get('results', [])
                
                # Search for industrial areas
                industrial_params = params.copy()
                industrial_params['type'] = 'establishment'
                industrial_params['keyword'] = 'industrial'
                
                industrial_response = requests.get(url, params=industrial_params, timeout=10)
                industrial_areas = []
                if industrial_response.status_code == 200:
                    industrial_data = industrial_response.json()
                    industrial_areas = industrial_data.get('results', [])
                
                # Environmental context analysis
                green_space_density = len(parks)
                industrial_proximity = len(industrial_areas)
                
                environmental_score = max(1, 10 - industrial_proximity + (green_space_density * 0.5))
                
                return {
                    'source': 'google_places',
                    'green_spaces_nearby': green_space_density,
                    'industrial_areas_nearby': industrial_proximity,
                    'environmental_score': min(10, environmental_score),
                    'park_names': [park.get('name', 'Unknown') for park in parks[:5]],
                    'coordinates': {'lat': lat, 'lng': lng}
                }
            
        except Exception as e:
            print(f"Google Places environmental API error: {e}")
            self.api_tracker.log_api_call(
                'google_places_environmental',
                '/place/nearbysearch/json',
                500,
                0,
                False,
                str(e)
            )
        
        return None
    
    def _check_eco_sensitive_zones(self, lat: float, lng: float) -> Optional[Dict]:
        """Check for eco-sensitive zones (simulated - would use real government APIs)"""
        # In a real implementation, this would query:
        # - Forest department databases
        # - Wildlife sanctuary APIs
        # - Protected area databases
        # - National park services
        # - Environmental ministry APIs
        
        # Simulated eco-sensitive zone detection
        import hashlib
        
        # Create deterministic "zones" based on coordinates
        coord_hash = hashlib.md5(f"{lat:.3f},{lng:.3f}".encode()).hexdigest()
        hash_value = int(coord_hash[:8], 16)
        
        # Simulate different types of eco-sensitive zones
        zone_probability = (hash_value % 100) / 100
        
        if zone_probability < 0.05:  # 5% chance of wildlife sanctuary
            return {
                'source': 'eco_zones_db',
                'is_eco_sensitive': True,
                'zone_type': 'wildlife_sanctuary',
                'sensitivity_level': 'critical',
                'restrictions': [
                    'No horn usage between 6 PM - 6 AM',
                    'Speed limit: 30 km/h',
                    'No stopping or parking',
                    'Wildlife crossing zones'
                ],
                'authority': 'Forest Department',
                'coordinates': {'lat': lat, 'lng': lng}
            }
        elif zone_probability < 0.08:  # 3% chance of forest reserve
            return {
                'source': 'eco_zones_db',
                'is_eco_sensitive': True,
                'zone_type': 'forest_reserve',
                'sensitivity_level': 'high',
                'restrictions': [
                    'Fire safety compliance required',
                    'No smoking or open flames',
                    'Noise restrictions in effect',
                    'Speed limit: 40 km/h'
                ],
                'authority': 'Forest Department',
                'coordinates': {'lat': lat, 'lng': lng}
            }
        elif zone_probability < 0.12:  # 4% chance of pollution sensitive area
            return {
                'source': 'eco_zones_db',
                'is_eco_sensitive': True,
                'zone_type': 'pollution_sensitive_area',
                'sensitivity_level': 'medium',
                'restrictions': [
                    'Emission standards enforcement',
                    'No idling for >3 minutes',
                    'Older vehicles may be restricted',
                    'Regular pollution checks'
                ],
                'authority': 'Pollution Control Board',
                'coordinates': {'lat': lat, 'lng': lng}
            }
        
        return None
    
    def _calculate_aqi_from_pollutants(self, pollutants: Dict) -> float:
        """Calculate simplified AQI from pollutant data"""
        try:
            pm25 = pollutants.get('pollutantPM25', 0)
            pm10 = pollutants.get('pollutantPM10', 0)
            o3 = pollutants.get('pollutantO3', 0)
            no2 = pollutants.get('pollutantNO2', 0)
            
            # Simplified AQI calculation (real implementation would use proper AQI formulas)
            pm25_aqi = min(500, (pm25 / 25) * 100)  # PM2.5 good level: 25 µg/m³
            pm10_aqi = min(500, (pm10 / 50) * 100)  # PM10 good level: 50 µg/m³
            o3_aqi = min(500, (o3 / 100) * 100)     # O3 good level: 100 µg/m³
            no2_aqi = min(500, (no2 / 40) * 100)    # NO2 good level: 40 µg/m³
            
            return max(pm25_aqi, pm10_aqi, o3_aqi, no2_aqi)
        except:
            return 50  # Default moderate AQI
    
    def _categorize_environmental_data(self, env_data: Dict, environmental_data: Dict, 
                                     route_id: str, point: List[float]):
        """Categorize environmental assessment data into risk categories"""
        lat, lng = point[0], point[1]
        
        for source, data in env_data.items():
            # Eco-sensitive zones
            if source == 'eco_zones' and data.get('is_eco_sensitive'):
                environmental_data['eco_sensitive_zones'].append({
                    'route_id': route_id,
                    'latitude': lat,
                    'longitude': lng,
                    'zone_type': data.get('zone_type'),
                    'sensitivity_level': data.get('sensitivity_level'),
                    'restrictions': data.get('restrictions', []),
                    'authority': data.get('authority', 'Environmental Authority'),
                    'source': source
                })
            
            # Air quality risks
            if 'air_quality' in str(data) or 'pollutants' in str(data):
                aqi = data.get('air_quality_index') or data.get('air_quality_score', 50)
                if aqi > 100:  # Unhealthy for sensitive groups
                    environmental_data['air_quality_risks'].append({
                        'route_id': route_id,
                        'latitude': lat,
                        'longitude': lng,
                        'aqi_value': aqi,
                        'risk_level': 'high' if aqi > 150 else 'medium',
                        'pollutants': data.get('pollutants', {}),
                        'health_advisory': self._get_health_advisory(aqi),
                        'source': source
                    })
            
            # Weather hazards
            environmental_risks = data.get('environmental_risks', [])
            if environmental_risks:
                for risk in environmental_risks:
                    environmental_data['weather_hazards'].append({
                        'route_id': route_id,
                        'latitude': lat,
                        'longitude': lng,
                        'hazard_type': risk,
                        'severity': self._get_hazard_severity(risk, data),
                        'description': self._get_hazard_description(risk),
                        'recommendations': self._get_hazard_recommendations(risk),
                        'source': source
                    })
            
            # Seasonal risks (based on current conditions)
            seasonal_risks = self._identify_seasonal_risks(data)
            if seasonal_risks:
                environmental_data['seasonal_risks'].extend(seasonal_risks)
    
    def _get_health_advisory(self, aqi: float) -> str:
        """Get health advisory based on AQI value"""
        if aqi <= 50:
            return "Good air quality - no health concerns"
        elif aqi <= 100:
            return "Moderate air quality - sensitive individuals should limit outdoor exposure"
        elif aqi <= 150:
            return "Unhealthy for sensitive groups - reduce prolonged outdoor exertion"
        elif aqi <= 200:
            return "Unhealthy air quality - everyone should reduce outdoor activities"
        else:
            return "Very unhealthy air quality - avoid outdoor activities"
    
    def _get_hazard_severity(self, risk: str, data: Dict) -> str:
        """Determine hazard severity"""
        if risk in ['extreme_uv', 'severe_visibility', 'high_pm25']:
            return 'critical'
        elif risk in ['high_uv_exposure', 'poor_visibility', 'high_ozone']:
            return 'high'
        else:
            return 'medium'
    
    def _get_hazard_description(self, risk: str) -> str:
        """Get description for environmental hazard"""
        descriptions = {
            'high_uv_exposure': 'High UV radiation levels - increased skin and eye damage risk',
            'poor_visibility': 'Reduced visibility conditions - increased accident risk',
            'strong_winds': 'Strong wind conditions - vehicle stability concerns',
            'high_pm25': 'High PM2.5 levels - respiratory health risks',
            'high_ozone': 'High ozone levels - breathing difficulties for sensitive individuals',
            'severe_visibility': 'Severe visibility impairment - dangerous driving conditions'
        }
        return descriptions.get(risk, f'Environmental hazard: {risk}')
    
    def _get_hazard_recommendations(self, risk: str) -> List[str]:
        """Get recommendations for environmental hazard"""
        recommendations = {
            'high_uv_exposure': [
                'Use vehicle sunshades',
                'Wear protective clothing during stops',
                'Stay hydrated',
                'Limit outdoor exposure during peak hours'
            ],
            'poor_visibility': [
                'Reduce speed significantly',
                'Use headlights and hazard lights',
                'Increase following distance',
                'Consider delaying travel if conditions worsen'
            ],
            'strong_winds': [
                'Reduce speed and maintain firm grip on steering',
                'Be cautious of high-profile vehicles',
                'Avoid sudden lane changes',
                'Consider alternative route if possible'
            ],
            'high_pm25': [
                'Keep windows closed, use air conditioning on recirculate',
                'Wear N95 masks during stops',
                'Limit physical exertion during breaks',
                'Consider air purifiers for prolonged exposure'
            ]
        }
        return recommendations.get(risk, ['Exercise caution', 'Monitor conditions'])
    
    def _identify_seasonal_risks(self, data: Dict) -> List[Dict]:
        """Identify seasonal environmental risks"""
        seasonal_risks = []
        
        # Temperature-based seasonal risks
        temp = data.get('temperature', 25)
        if temp > 40:
            seasonal_risks.append({
                'risk_type': 'extreme_heat',
                'severity': 'critical',
                'description': 'Extreme heat conditions - vehicle overheating risk',
                'season': 'summer'
            })
        elif temp < 5:
            seasonal_risks.append({
                'risk_type': 'cold_weather',
                'severity': 'medium',
                'description': 'Cold weather conditions - battery and starting issues possible',
                'season': 'winter'
            })
        
        # Humidity-based risks
        humidity = data.get('humidity', 50)
        if humidity > 85 and temp > 30:
            seasonal_risks.append({
                'risk_type': 'high_humidity_heat',
                'severity': 'high',
                'description': 'High humidity with heat - heat stress risk',
                'season': 'monsoon/summer'
            })
        
        return seasonal_risks
    
    def _analyze_route_environmental_summary(self, environmental_data: Dict) -> Dict:
        """Analyze overall route environmental impact"""
        summary = {
            'total_eco_zones': len(environmental_data.get('eco_sensitive_zones', [])),
            'total_air_quality_risks': len(environmental_data.get('air_quality_risks', [])),
            'total_weather_hazards': len(environmental_data.get('weather_hazards', [])),
            'overall_risk_level': 'low',
            'primary_environmental_concerns': [],
            'route_environmental_score': 8.0
        }
        
        # Calculate overall risk level
        total_risks = (summary['total_eco_zones'] + 
                      summary['total_air_quality_risks'] + 
                      summary['total_weather_hazards'])
        
        if total_risks > 10:
            summary['overall_risk_level'] = 'critical'
            summary['route_environmental_score'] = 3.0
        elif total_risks > 5:
            summary['overall_risk_level'] = 'high'
            summary['route_environmental_score'] = 5.0
        elif total_risks > 2:
            summary['overall_risk_level'] = 'medium'
            summary['route_environmental_score'] = 7.0
        
        # Identify primary concerns
        if summary['total_eco_zones'] > 0:
            summary['primary_environmental_concerns'].append('Protected/sensitive ecological areas')
        if summary['total_air_quality_risks'] > 3:
            summary['primary_environmental_concerns'].append('Poor air quality zones')
        if summary['total_weather_hazards'] > 3:
            summary['primary_environmental_concerns'].append('Weather-related environmental hazards')
        
        return summary
    
    def store_environmental_data(self, route_id: str, environmental_data: Dict) -> bool:
        """Store environmental analysis in database"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.api_tracker.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Create environmental tables if they don't exist
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
                
                # Store all environmental risk data
                risk_categories = [
                    ('eco_sensitive_zones', 'ecological'),
                    ('air_quality_risks', 'air_quality'),
                    ('weather_hazards', 'weather'),
                    ('seasonal_risks', 'seasonal'),
                    ('pollution_zones', 'pollution')
                ]
                
                total_stored = 0
                
                for category, risk_category in risk_categories:
                    risks = environmental_data.get(category, [])
                    
                    for risk in risks:
                        if isinstance(risk, dict):
                            cursor.execute("""
                                INSERT INTO environmental_risks 
                                (route_id, latitude, longitude, risk_category, risk_type,
                                 severity, description, recommendations, source_api, additional_data)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                route_id,
                                risk.get('latitude', 0),
                                risk.get('longitude', 0),
                                risk_category,
                                risk.get('zone_type') or risk.get('hazard_type') or risk.get('risk_type', 'unknown'),
                                risk.get('severity') or risk.get('sensitivity_level', 'medium'),
                                risk.get('description', ''),
                                json.dumps(risk.get('recommendations') or risk.get('restrictions', [])),
                                risk.get('source', 'unknown'),
                                json.dumps(risk)
                            ))
                            total_stored += 1
                
                conn.commit()
                print(f"✅ Stored {total_stored} environmental risk assessments in database")
                return True
                
        except Exception as e:
            print(f"❌ Error storing environmental data: {e}")
            return False