import os
import time
import requests
import googlemaps
from typing import List, Dict, Any, Optional

class EmergencyFacilitiesAnalyzer:
    """Enhanced emergency facilities analyzer with phone numbers"""
    
    def __init__(self, api_tracker, db_manager):
        self.api_tracker = api_tracker
        self.db_manager = db_manager
        self.google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        
        if self.google_api_key:
            self.gmaps = googlemaps.Client(key=self.google_api_key)
        else:
            self.gmaps = None
            print("⚠️ Google Maps API key not configured for emergency analysis")
    
    def analyze_emergency_facilities(self, route_points: List[List[float]], route_id: str) -> Dict[str, List[Dict]]:
        """Comprehensive emergency facilities analysis with phone numbers"""
        try:
            print(f"🚨 Starting enhanced emergency facilities analysis...")
            
            emergency_data = {
                'hospitals': [],
                'police_stations': [],
                'fire_stations': [],
                'pharmacies': [],
                'urgent_care': []
            }
            
            # Emergency facility types with their Google Places types
            facility_types = {
                'hospitals': ['hospital', 'emergency_room'],
                'police_stations': ['police'],
                'fire_stations': ['fire_station'],
                'pharmacies': ['pharmacy', 'drugstore'],
                'urgent_care': ['doctor', 'clinic']
            }
            
            # Sample points for emergency search
            step = max(1, len(route_points) // 8)  # Every 8th point
            sampled_points = route_points[::step]
            
            print(f"   Searching emergency facilities around {len(sampled_points)} route points")
            
            for facility_category, google_types in facility_types.items():
                print(f"🔍 Searching for {facility_category}...")
                
                facilities_found = {}  # Use dict to avoid duplicates
                
                for point in sampled_points[:6]:  # Limit to 6 search points
                    for google_type in google_types:
                        try:
                            facilities = self._search_emergency_facilities(
                                point[0], point[1], google_type, facility_category
                            )
                            
                            for facility in facilities:
                                # Use place_id as unique key
                                facilities_found[facility['place_id']] = facility
                            
                            time.sleep(0.2)  # Rate limiting
                            
                        except Exception as e:
                            print(f"   Error searching {google_type}: {e}")
                            continue
                
                # Get detailed information including phone numbers
                enhanced_facilities = []
                for facility in list(facilities_found.values())[:15]:  # Limit to 15 per type
                    enhanced_facility = self._get_detailed_facility_info(facility)
                    if enhanced_facility:
                        enhanced_facilities.append(enhanced_facility)
                
                emergency_data[facility_category] = enhanced_facilities
                print(f"✅ Found {len(enhanced_facilities)} {facility_category} with contact details")
            
            # Store in database
            all_facilities = []
            for category, facilities in emergency_data.items():
                all_facilities.extend(facilities)
            
            if all_facilities:
                self.db_manager.store_emergency_contacts(route_id, all_facilities)
                print(f"📞 Stored {len(all_facilities)} emergency contacts in database")
            
            return emergency_data
            
        except Exception as e:
            print(f"❌ Emergency facilities analysis failed: {e}")
            return {}
    
    def _search_emergency_facilities(self, lat: float, lng: float, 
                                   place_type: str, facility_category: str) -> List[Dict]:
        """Search for emergency facilities using Google Places API"""
        if not self.gmaps:
            return []
        
        try:
            start_time = time.time()
            
            # Search nearby places
            places_result = self.gmaps.places_nearby(
                location=(lat, lng),
                radius=10000,  # 10km radius for emergency facilities
                type=place_type,
                language='en'
            )
            
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'google_places_emergency',
                '/place/nearbysearch/json',
                200 if places_result else 400,
                response_time,
                bool(places_result.get('results'))
            )
            
            facilities = []
            for place in places_result.get('results', []):
                facility = {
                    'place_id': place.get('place_id'),
                    'name': place.get('name', 'Unknown'),
                    'facility_type': facility_category.rstrip('s'),  # Remove 's' from plural
                    'latitude': place['geometry']['location']['lat'],
                    'longitude': place['geometry']['location']['lng'],
                    'address': place.get('vicinity', ''),
                    'rating': place.get('rating', 0),
                    'types': place.get('types', [])
                }
                facilities.append(facility)
            
            return facilities
            
        except Exception as e:
            print(f"Error searching emergency facilities: {e}")
            return []
    
    def _get_detailed_facility_info(self, facility: Dict) -> Optional[Dict]:
        """Get detailed facility information including phone numbers"""
        if not self.gmaps or not facility.get('place_id'):
            return facility
        
        try:
            start_time = time.time()
            
            # Get place details
            place_details = self.gmaps.place(
                place_id=facility['place_id'],
                fields=[
                    'name', 'formatted_address', 'formatted_phone_number',
                    'international_phone_number', 'website', 'rating',
                    'opening_hours', 'geometry', 'types'
                ],
                language='en'
            )
            
            response_time = time.time() - start_time
            
            # Log API usage
            self.api_tracker.log_api_call(
                'google_place_details',
                '/place/details/json',
                200 if place_details else 400,
                response_time,
                bool(place_details.get('result'))
            )
            
            if place_details and place_details.get('result'):
                details = place_details['result']
                
                # Enhanced facility information
                enhanced_facility = facility.copy()
                enhanced_facility.update({
                    'phone_number': details.get('formatted_phone_number'),
                    'formatted_phone_number': details.get('formatted_phone_number'),
                    'international_phone_number': details.get('international_phone_number'),
                    'address': details.get('formatted_address', facility.get('address', '')),
                    'website': details.get('website'),
                    'rating': details.get('rating', facility.get('rating', 0)),
                    'opening_hours': details.get('opening_hours', {}),
                    'has_phone': bool(details.get('formatted_phone_number')),
                    'is_24_7': self._check_24_7_availability(details.get('opening_hours', {}))
                })
                
                return enhanced_facility
            
            return facility
            
        except Exception as e:
            print(f"Error getting facility details: {e}")
            return facility
    
    def _check_24_7_availability(self, opening_hours: Dict) -> bool:
        """Check if facility is available 24/7"""
        try:
            periods = opening_hours.get('periods', [])
            if not periods:
                return False
            
            # Check if open 24/7 (period with open but no close)
            for period in periods:
                if 'close' not in period and 'open' in period:
                    return True
            
            return False
            
        except:
            return False