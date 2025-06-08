# utils/api_tracker.py - API Usage Tracker and Monitor
# Purpose: Track all API calls, monitor status, test connectivity, record usage statistics
# Dependencies: requests, datetime, os
# Author: Route Analysis System
# Created: 2024

import os
import time
import datetime
import requests
from typing import Dict, List, Any, Optional

class APITracker:
    """Track and monitor all API usage across the system"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Load API keys from environment
        self.api_keys = {
            'google_maps': os.environ.get('GOOGLE_MAPS_API_KEY'),
            'openweather': os.environ.get('OPENWEATHER_API_KEY'),
            'tomtom': os.environ.get('TOMTOM_API_KEY'),
            'here': os.environ.get('HERE_API_KEY'),
            'visualcrossing': os.environ.get('VISUALCROSSING_API_KEY'),
            'tomorrow_io': os.environ.get('TOMORROW_IO_API_KEY'),
            'mapbox': os.environ.get('MAPBOX_API_KEY')
        }
        
        # API endpoints for testing
        self.test_endpoints = {
            'google_maps': 'https://maps.googleapis.com/maps/api/geocode/json?address=Delhi&key={key}',
            'openweather': 'http://api.openweathermap.org/data/2.5/weather?q=Delhi&appid={key}',
            'tomtom': 'https://api.tomtom.com/search/2/geocode/Delhi.json?key={key}',
            'here': 'https://geocode.search.hereapi.com/v1/geocode?q=Delhi&apikey={key}',
            'visualcrossing': 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Delhi?key={key}',
            'tomorrow_io': 'https://api.tomorrow.io/v4/weather/forecast?location=Delhi&apikey={key}',
            'mapbox': 'https://api.mapbox.com/geocoding/v5/mapbox.places/Delhi.json?access_token={key}'
        }
        
        print(f"🔑 API Tracker initialized with {len([k for k in self.api_keys.values() if k])} configured APIs")
    
    def log_api_call(self, api_name: str, endpoint: str, response_code: int,
                     response_time: float, success: bool, route_id: str = None,
                     error_message: str = None):
        """Log an API call to the database"""
        try:
            self.db_manager.log_api_usage(
                api_name=api_name,
                endpoint=endpoint,
                response_code=response_code,
                response_time=response_time,
                success=success,
                route_id=route_id,
                error_message=error_message
            )
        except Exception as e:
            print(f"Error logging API call: {e}")
    
    def test_api(self, api_name: str) -> Dict[str, Any]:
        """Test a specific API for connectivity and validity"""
        api_key = self.api_keys.get(api_name)
        test_url = self.test_endpoints.get(api_name)
        
        if not api_key:
            return {
                'api_name': api_name,
                'status': 'error',
                'message': 'API key not configured',
                'response_time': 0,
                'response_code': 0
            }
        
        if not test_url:
            return {
                'api_name': api_name,
                'status': 'error',
                'message': 'Test endpoint not defined',
                'response_time': 0,
                'response_code': 0
            }
        
        try:
            start_time = time.time()
            
            # Format URL with API key
            formatted_url = test_url.format(key=api_key)
            
            # Make test request
            response = requests.get(formatted_url, timeout=10)
            response_time = time.time() - start_time
            
            # Log the test call
            self.log_api_call(
                api_name=f"{api_name}_test",
                endpoint=test_url.split('?')[0],
                response_code=response.status_code,
                response_time=response_time,
                success=response.status_code == 200
            )
            
            if response.status_code == 200:
                return {
                    'api_name': api_name,
                    'status': 'success',
                    'message': 'API is working correctly',
                    'response_time': round(response_time, 3),
                    'response_code': response.status_code
                }
            else:
                return {
                    'api_name': api_name,
                    'status': 'error',
                    'message': f'API returned error: {response.status_code}',
                    'response_time': round(response_time, 3),
                    'response_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {
                'api_name': api_name,
                'status': 'error',
                'message': 'API request timed out',
                'response_time': 10.0,
                'response_code': 0
            }
        except requests.exceptions.RequestException as e:
            return {
                'api_name': api_name,
                'status': 'error',
                'message': f'Network error: {str(e)}',
                'response_time': 0,
                'response_code': 0
            }
        except Exception as e:
            return {
                'api_name': api_name,
                'status': 'error',
                'message': f'Unknown error: {str(e)}',
                'response_time': 0,
                'response_code': 0
            }
    
    def test_all_apis(self) -> Dict[str, Any]:
        """Test all configured APIs"""
        print("🧪 Testing all configured APIs...")
        
        results = {}
        overall_status = 'success'
        working_count = 0
        total_count = len(self.api_keys)
        
        for api_name in self.api_keys.keys():
            print(f"   Testing {api_name}...")
            result = self.test_api(api_name)
            results[api_name] = result
            
            if result['status'] == 'success':
                working_count += 1
                print(f"   ✅ {api_name}: Working ({result['response_time']}s)")
            else:
                print(f"   ❌ {api_name}: {result['message']}")
                if overall_status == 'success':
                    overall_status = 'partial'
        
        if working_count == 0:
            overall_status = 'failure'
        
        summary = {
            'overall_status': overall_status,
            'working_apis': working_count,
            'total_apis': total_count,
            'success_rate': round((working_count / total_count) * 100, 1),
            'test_timestamp': datetime.datetime.now().isoformat(),
            'results': results
        }
        
        print(f"🔍 API Test Summary: {working_count}/{total_count} APIs working ({summary['success_rate']}%)")
        return summary
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get current API configuration status"""
        status = {}
        
        for api_name, api_key in self.api_keys.items():
            status[api_name] = {
                'configured': bool(api_key),
                'key_length': len(api_key) if api_key else 0,
                'masked_key': f"{api_key[:8]}..." if api_key and len(api_key) > 8 else 'Not configured'
            }
        
        return status
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed API status including usage statistics"""
        # Get basic status
        basic_status = self.get_api_status()
        
        # Get usage statistics from database
        usage_stats = self.db_manager.get_api_usage_stats()
        
        # Get recent performance
        recent_performance = self._get_recent_performance()
        
        return {
            'api_configuration': basic_status,
            'usage_statistics': usage_stats,
            'recent_performance': recent_performance,
            'summary': {
                'configured_apis': len([k for k in self.api_keys.values() if k]),
                'total_apis': len(self.api_keys),
                'configuration_complete': len([k for k in self.api_keys.values() if k]) == len(self.api_keys)
            }
        }
    
    def _get_recent_performance(self) -> Dict[str, Any]:
        """Get recent API performance metrics"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Performance in last 24 hours
                cursor.execute("""
                    SELECT api_name,
                           COUNT(*) as call_count,
                           AVG(response_time) as avg_response_time,
                           SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls,
                           MIN(timestamp) as first_call,
                           MAX(timestamp) as last_call
                    FROM api_usage 
                    WHERE timestamp > datetime('now', '-24 hours')
                    GROUP BY api_name
                    ORDER BY call_count DESC
                """)
                
                performance_data = [dict(row) for row in cursor.fetchall()]
                
                # Calculate success rates
                for item in performance_data:
                    if item['call_count'] > 0:
                        item['success_rate'] = round((item['successful_calls'] / item['call_count']) * 100, 1)
                        item['avg_response_time'] = round(item['avg_response_time'], 3)
                    else:
                        item['success_rate'] = 0
                
                return {
                    'period': 'Last 24 hours',
                    'performance_by_api': performance_data,
                    'total_calls': sum(item['call_count'] for item in performance_data),
                    'overall_success_rate': round(
                        sum(item['successful_calls'] for item in performance_data) / 
                        max(sum(item['call_count'] for item in performance_data), 1) * 100, 1
                    )
                }
                
        except Exception as e:
            print(f"Error getting recent performance: {e}")
            return {'error': str(e)}
    
    def get_api_usage_by_route(self, route_id: str) -> List[Dict]:
        """Get API usage for a specific route"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT api_name, endpoint, response_code, response_time, 
                           success, timestamp, error_message
                    FROM api_usage 
                    WHERE route_id = ?
                    ORDER BY timestamp
                """, (route_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            print(f"Error getting route API usage: {e}")
            return []
    
    def get_daily_usage_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get daily API usage summary for the last N days"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT DATE(timestamp) as date,
                           api_name,
                           COUNT(*) as call_count,
                           SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls
                    FROM api_usage 
                    WHERE timestamp > datetime('now', '-{} days')
                    GROUP BY DATE(timestamp), api_name
                    ORDER BY date DESC, api_name
                """.format(days))
                
                daily_data = [dict(row) for row in cursor.fetchall()]
                
                # Process data for charts/visualization
                dates = sorted(list(set(item['date'] for item in daily_data)))
                api_names = sorted(list(set(item['api_name'] for item in daily_data)))
                
                chart_data = {
                    'dates': dates,
                    'api_names': api_names,
                    'daily_usage': daily_data
                }
                
                return chart_data
                
        except Exception as e:
            print(f"Error getting daily usage summary: {e}")
            return {}
    
    def generate_usage_report(self, route_id: str = None) -> Dict[str, Any]:
        """Generate comprehensive API usage report"""
        report = {
            'generated_at': datetime.datetime.now().isoformat(),
            'report_type': 'route_specific' if route_id else 'system_wide'
        }
        
        if route_id:
            # Route-specific report
            report['route_id'] = route_id
            report['api_calls'] = self.get_api_usage_by_route(route_id)
            report['summary'] = {
                'total_calls': len(report['api_calls']),
                'successful_calls': len([call for call in report['api_calls'] if call['success']]),
                'apis_used': len(set(call['api_name'] for call in report['api_calls'])),
                'total_response_time': sum(call['response_time'] for call in report['api_calls'])
            }
        else:
            # System-wide report
            report['usage_statistics'] = self.db_manager.get_api_usage_stats()
            report['recent_performance'] = self._get_recent_performance()
            report['daily_summary'] = self.get_daily_usage_summary()
        
        return report
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old API usage logs"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM api_usage 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                print(f"🧹 Cleaned up {deleted_count} old API usage logs (older than {days_to_keep} days)")
                return deleted_count
                
        except Exception as e:
            print(f"Error cleaning up old logs: {e}")
            return 0