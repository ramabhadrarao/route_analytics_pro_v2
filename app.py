# app.py - Main Flask Application for Route Analysis System
# Purpose: Main application file with authentication, file upload, and API endpoints
# Dependencies: Flask, SQLite, googlemaps, requests
# Author: Route Analysis System
# Created: 2024

import os
import sqlite3
import json
import uuid
import datetime
import csv
from pathlib import Path
from flask import Flask, request, jsonify, session, render_template, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import googlemaps
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import custom modules
from database.db_manager import DatabaseManager
from api.route_api import RouteAPI
from analysis.route_analyzer import RouteAnalyzer
from pdf.pdf_generator import PDFGenerator
from utils.api_tracker import APITracker

class RouteAnalysisApp:
    """Main Route Analysis Application"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = os.environ.get('SECRET_KEY', 'route-analysis-2024')
        
        # Configuration
        self.app.config.update({
            'UPLOAD_FOLDER': 'uploads',
            'IMAGES_FOLDER': 'images',
            'REPORTS_FOLDER': 'reports',
            'MAX_CONTENT_LENGTH': 16 * 1024 * 1024  # 16MB
        })
        
        # Create directories
        self._create_directories()
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.api_tracker = APITracker(self.db_manager)
        self.route_analyzer = RouteAnalyzer(self.api_tracker)
        self.route_api = RouteAPI(self.db_manager, self.api_tracker)
        self.pdf_generator = PDFGenerator(self.db_manager, self.api_tracker)
        # self.pdf_generator = PDFGenerator(self.db_manager)
        
        # Admin credentials
        self.ADMIN_USERNAME = 'admin'
        self.ADMIN_PASSWORD = 'admin123'
        
        # Setup routes
        self._setup_routes()
        
    def _create_directories(self):
        """Create required directories"""
        directories = [
            'uploads', 'images', 'reports', 'database',
            'images/street_view', 'images/satellite', 'images/maps'
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _setup_routes(self):
        """Setup all Flask routes"""
        
        # Authentication routes
        @self.app.route('/')
        def index():
            if 'logged_in' not in session:
                return redirect(url_for('login'))
            return redirect(url_for('dashboard'))
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                
                if username == self.ADMIN_USERNAME and password == self.ADMIN_PASSWORD:
                    session['logged_in'] = True
                    session['username'] = username
                    session['user_id'] = str(uuid.uuid4())
                    return jsonify({'status': 'success', 'redirect': url_for('dashboard')})
                else:
                    return jsonify({'status': 'error', 'message': 'Invalid credentials'})
            
            return render_template('login.html')
        
        @self.app.route('/logout')
        def logout():
            session.clear()
            return redirect(url_for('login'))
        
        # Main application routes
        @self.app.route('/dashboard')
        def dashboard():
            if 'logged_in' not in session:
                return redirect(url_for('login'))
            
            # Get recent routes
            recent_routes = self.db_manager.get_recent_routes(limit=10)
            api_status = self.api_tracker.get_api_status()
            
            return render_template('dashboard.html', 
                                 recent_routes=recent_routes,
                                 api_status=api_status)
        @self.app.route('/api/routes/<route_id>/emergency-contacts')
        def route_emergency_contacts(route_id):
            """Get emergency contacts with phone numbers"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            return jsonify(self.route_api.get_emergency_contacts(route_id))
        @self.app.route('/upload-csv', methods=['POST'])
        def upload_csv():
            """Handle CSV upload and route analysis"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            try:
                if 'csv_file' not in request.files:
                    return jsonify({'error': 'No file uploaded'}), 400
                
                file = request.files['csv_file']
                if not file.filename.lower().endswith('.csv'):
                    return jsonify({'error': 'Please upload a CSV file'}), 400
                
                # Save file
                filename = secure_filename(file.filename)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Analyze route
                route_id = self.route_analyzer.analyze_csv_route(filepath, session['user_id'])
                
                if route_id:
                    return jsonify({
                        'status': 'success',
                        'route_id': route_id,
                        'message': 'Route analyzed successfully'
                    })
                else:
                    return jsonify({'error': 'Route analysis failed'}), 500
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # API Status routes
        @self.app.route('/api/status')
        def api_status():
            """Get API status and usage"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            return jsonify(self.api_tracker.get_detailed_status())
        
        @self.app.route('/api/test-apis')
        def test_apis():
            """Test all configured APIs"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            return jsonify(self.api_tracker.test_all_apis())
        
        # Route management routes
        @self.app.route('/api/routes')
        def get_routes():
            """Get all routes for current user"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            routes = self.db_manager.get_user_routes(session['user_id'])
            return jsonify({'routes': routes})
        
        @self.app.route('/api/routes/<route_id>')
        def get_route_details(route_id):
            """Get detailed route information"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            route_data = self.route_api.get_route_data(route_id)
            if route_data:
                return jsonify(route_data)
            else:
                return jsonify({'error': 'Route not found'}), 404
        
        # PDF Generation routes
        @self.app.route('/api/pdf/<route_id>')
        def generate_pdf_route(route_id):
            """Generate PDF for specific route"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            # Get requested pages from query parameters
            pages = request.args.get('pages', 'all')
            
            try:
                pdf_path = self.pdf_generator.generate_route_pdf(route_id, pages)
                if pdf_path:
                    return send_file(pdf_path, as_attachment=True)
                else:
                    return jsonify({'error': 'PDF generation failed'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Page-specific data routes
        @self.app.route('/api/routes/<route_id>/overview')
        def route_overview(route_id):
            return jsonify(self.route_api.get_route_overview(route_id))
        
        @self.app.route('/api/routes/<route_id>/turns')
        def route_turns(route_id):
            return jsonify(self.route_api.get_sharp_turns(route_id))
        
        @self.app.route('/api/routes/<route_id>/pois')
        def route_pois(route_id):
            return jsonify(self.route_api.get_points_of_interest(route_id))
        
        @self.app.route('/api/routes/<route_id>/network')
        def route_network(route_id):
            return jsonify(self.route_api.get_network_coverage(route_id))
        
        @self.app.route('/api/routes/<route_id>/weather')
        def route_weather(route_id):
            return jsonify(self.route_api.get_weather_data(route_id))
        
        @self.app.route('/api/routes/<route_id>/compliance')
        def route_compliance(route_id):
            vehicle_type = request.args.get('vehicle_type', 'heavy_goods_vehicle')
            return jsonify(self.route_api.get_compliance_data(route_id, vehicle_type))
        
        @self.app.route('/api/routes/<route_id>/elevation')
        def route_elevation(route_id):
            return jsonify(self.route_api.get_elevation_data(route_id))
        
        @self.app.route('/api/routes/<route_id>/traffic')
        def route_traffic(route_id):
            return jsonify(self.route_api.get_traffic_data(route_id))
        
        @self.app.route('/api/routes/<route_id>/emergency')
        def route_emergency(route_id):
            return jsonify(self.route_api.get_emergency_data(route_id))
        
        # Image management routes
        @self.app.route('/images/<path:filename>')
        def serve_image(filename):
            """Serve stored images"""
            return send_file(os.path.join('images', filename))
        @self.app.route('/api/routes/<route_id>/enhanced-overview')
        def route_enhanced_overview(route_id):
            """Get enhanced route overview with highways and terrain"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            return jsonify(self.route_api.get_enhanced_route_overview(route_id))
        # Add this route to your app.py file

        @self.app.route('/report/<route_id>')
        def view_route_report(route_id):
            """Display comprehensive web report for a specific route"""
            if 'logged_in' not in session:
                return redirect(url_for('login'))
            
            # Verify route exists
            route = self.db_manager.get_route(route_id)
            if not route:
                return render_template('error.html', 
                                    error_message=f'Route {route_id} not found'), 404
            
            # Add current date for the template
            import datetime
            current_date = datetime.datetime.now().strftime('%B %d, %Y')
            
            return render_template('route_report.html', 
                                route_id=route_id, 
                                route=route, 
                                current_date=current_date)

        # Also add this route to get enhanced overview data
        @self.app.route('/api/routes/<route_id>/enhanced-overview')
        def route_enhanced_overview_with_map_data(route_id):
            """Get enhanced route overview with map-ready data"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            try:
                # Get basic enhanced overview
                overview_data = self.route_api.get_enhanced_route_overview(route_id)
                
                if 'error' in overview_data:
                    return jsonify(overview_data)
                
                # Add map-specific data
                route_points = self.db_manager.get_route_points(route_id)
                stored_images = self.db_manager.get_stored_images(route_id)
                
                # Calculate route bounds for map initialization
                if route_points:
                    latitudes = [p['latitude'] for p in route_points]
                    longitudes = [p['longitude'] for p in route_points]
                    
                    overview_data['map_bounds'] = {
                        'north': max(latitudes),
                        'south': min(latitudes),
                        'east': max(longitudes),
                        'west': min(longitudes),
                        'center': {
                            'lat': sum(latitudes) / len(latitudes),
                            'lng': sum(longitudes) / len(longitudes)
                        }
                    }
                
                # Add image availability
                overview_data['available_images'] = {
                    'street_view': len([img for img in stored_images if img.get('image_type') == 'street_view']),
                    'satellite': len([img for img in stored_images if img.get('image_type') == 'satellite']),
                    'route_maps': len([img for img in stored_images if img.get('image_type') == 'route_map']),
                    'total': len(stored_images)
                }
                
                return jsonify(overview_data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        # Helper method for the class
        def _calculate_recommended_animation_speed(self, point_count: int) -> int:
            """Calculate recommended animation speed based on point count"""
            if point_count <= 100:
                return 8  # Fast for short routes
            elif point_count <= 300:
                return 5  # Medium speed
            elif point_count <= 500:
                return 3  # Slower for longer routes
            else:
                return 2  # Very slow for very long routes

        # Update your existing live map route
        @self.app.route('/map/<route_id>')
        def live_route_map(route_id):
            """Display live interactive map for a specific route"""
            if 'logged_in' not in session:
                return redirect(url_for('login'))
            
            # Verify route exists
            route = self.db_manager.get_route(route_id)
            if not route:
                return render_template('error.html', 
                                    error_message=f'Route {route_id} not found'), 404
            
            # Check if route has GPS points
            route_points = self.db_manager.get_route_points(route_id)
            if not route_points:
                return render_template('error.html',
                                    error_message=f'Route {route_id} has no GPS coordinates for map display'), 404
            
            # Get route statistics for initial display
            route_stats = {
                'total_points': len(route_points),
                'has_pois': bool(self.db_manager.get_pois_by_type(route_id, 'hospital')),
                'has_turns': bool(self.db_manager.get_sharp_turns(route_id)),
                'has_network': bool(self.db_manager.get_network_coverage(route_id))
            }
            
            return render_template('live_map.html', 
                                route_id=route_id, 
                                route=route,
                                route_stats=route_stats)

        # Add error handling for map-related errors
        @self.app.errorhandler(404)
        def not_found_error(error):
            if request.path.startswith('/map/'):
                return render_template('error.html', 
                                    error_message='Route not found or invalid route ID'), 404
            return render_template('error.html', 
                                error_message='Page not found'), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            if request.path.startswith('/api/routes/'):
                return jsonify({'error': 'Internal server error', 'map_ready': False}), 500
            return render_template('error.html', 
                                error_message='Internal server error'), 500

        # Add route for testing map functionality
        @self.app.route('/api/test-map/<route_id>')
        def test_map_functionality(route_id):
            """Test map functionality for a specific route"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            try:
                test_results = {
                    'route_exists': bool(self.db_manager.get_route(route_id)),
                    'has_route_points': bool(self.db_manager.get_route_points(route_id)),
                    'has_pois': bool(self.db_manager.get_pois_by_type(route_id, 'hospital')),
                    'has_sharp_turns': bool(self.db_manager.get_sharp_turns(route_id)),
                    'has_network_data': bool(self.db_manager.get_network_coverage(route_id)),
                    'has_stored_images': bool(self.db_manager.get_stored_images(route_id)),
                    'google_maps_api_key': bool(os.environ.get('GOOGLE_MAPS_API_KEY')),
                    'database_accessible': True
                }
                
                # Count available data
                route_points = self.db_manager.get_route_points(route_id)
                test_results['data_counts'] = {
                    'route_points': len(route_points) if route_points else 0,
                    'sharp_turns': len(self.db_manager.get_sharp_turns(route_id)),
                    'pois': sum(len(self.db_manager.get_pois_by_type(route_id, poi_type)) 
                            for poi_type in ['hospital', 'gas_station', 'police', 'fire_station']),
                    'network_points': len(self.db_manager.get_network_coverage(route_id)),
                    'stored_images': len(self.db_manager.get_stored_images(route_id))
                }
                
                # Overall readiness
                test_results['map_ready'] = (
                    test_results['route_exists'] and 
                    test_results['has_route_points'] and 
                    test_results['google_maps_api_key']
                )
                
                test_results['recommendations'] = []
                if not test_results['has_route_points']:
                    test_results['recommendations'].append('Upload and analyze a CSV file with GPS coordinates')
                if not test_results['google_maps_api_key']:
                    test_results['recommendations'].append('Configure GOOGLE_MAPS_API_KEY in environment variables')
                if test_results['data_counts']['route_points'] < 10:
                    test_results['recommendations'].append('Route has very few GPS points - map may not display properly')
                
                return jsonify(test_results)
                
            except Exception as e:
                return jsonify({
                    'error': str(e),
                    'map_ready': False,
                    'database_accessible': False
                }), 500
        # Update your existing route or add this new one
        @self.app.route('/api/routes/<route_id>/complete-data')
        def get_complete_route_data(route_id):
            """Get all route data needed for interactive map in one call"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            try:
                # Get all route data using the enhanced database methods
                complete_data = self.db_manager.get_complete_route_data_for_map(route_id)
                
                if not complete_data:
                    return jsonify({'error': 'Route not found or no data available'}), 404
                
                # Add additional API data
                try:
                    overview_data = self.route_api.get_enhanced_route_overview(route_id)
                    pois_data = self.route_api.get_enhanced_points_of_interest(route_id)
                    turns_data = self.route_api.get_sharp_turns(route_id)
                    network_data = self.route_api.get_network_coverage(route_id)
                    emergency_data = self.route_api.get_emergency_data(route_id)
                    traffic_data = self.route_api.get_traffic_data(route_id)
                    
                    # Combine database and API data
                    enhanced_data = {
                        'overview': overview_data,
                        'pois': pois_data,
                        'turns': turns_data,
                        'network': network_data,
                        'emergency': emergency_data,
                        'traffic': traffic_data,
                        'database_data': complete_data,
                        'map_ready': True,
                        'api_status': 'success'
                    }
                    
                    return jsonify(enhanced_data)
                    
                except Exception as api_error:
                    print(f"API data error: {api_error}")
                    # Return database data only if API fails
                    complete_data['map_ready'] = True
                    complete_data['api_status'] = 'partial'
                    complete_data['api_error'] = str(api_error)
                    return jsonify(complete_data)
                
            except Exception as e:
                print(f"Complete data error: {e}")
                return jsonify({'error': str(e), 'map_ready': False}), 500
        @self.app.route('/api/routes/<route_id>/animation-points')
        def get_animation_points(route_id):
            """Get optimized route points for smooth animation"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            try:
                # Get optimized points for animation
                max_points = int(request.args.get('max_points', 500))
                optimized_points = self.db_manager.get_optimized_route_points(route_id, max_points)
                
                if not optimized_points:
                    return jsonify({'error': 'No route points found'}), 404
                
                # Get original count for comparison
                all_points = self.db_manager.get_route_points(route_id)
                original_count = len(all_points) if all_points else 0
                
                return jsonify({
                    'route_points': optimized_points,
                    'animation_points_count': len(optimized_points),
                    'original_points_count': original_count,
                    'optimization_ratio': len(optimized_points) / original_count if original_count > 0 else 0,
                    'recommended_speed': self._calculate_recommended_animation_speed(len(optimized_points))
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        @self.app.route('/api/routes/<route_id>/map-bounds')
        def get_map_bounds(route_id):
            """Get route bounds for map initialization"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            try:
                bounds = self.db_manager.get_route_bounds(route_id)
                
                if not bounds:
                    return jsonify({'error': 'No route bounds available'}), 404
                
                # Add recommended zoom level
                lat_span = bounds['north'] - bounds['south']
                lng_span = bounds['east'] - bounds['west']
                max_span = max(lat_span, lng_span)
                
                if max_span <= 0.01:
                    recommended_zoom = 15
                elif max_span <= 0.05:
                    recommended_zoom = 13
                elif max_span <= 0.1:
                    recommended_zoom = 12
                elif max_span <= 0.5:
                    recommended_zoom = 10
                elif max_span <= 1.0:
                    recommended_zoom = 9
                else:
                    recommended_zoom = 8
                
                bounds['recommended_zoom'] = recommended_zoom
                bounds['span'] = {'lat': lat_span, 'lng': lng_span}
                
                return jsonify(bounds)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        @self.app.route('/api/routes/<route_id>/animation-data')
        def get_animation_data(route_id):
            """Get optimized route points for animation"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            try:
                route_points = self.db_manager.get_route_points(route_id)
                
                if not route_points:
                    return jsonify({'error': 'No route points found'}), 404
                
                # Optimize points for animation (sample every Nth point based on total)
                total_points = len(route_points)
                if total_points > 1000:
                    step = total_points // 500  # Limit to ~500 points for smooth animation
                    optimized_points = route_points[::step]
                else:
                    optimized_points = route_points
                
                return jsonify({
                    'route_points': optimized_points,
                    'total_original_points': total_points,
                    'animation_points': len(optimized_points),
                    'optimization_ratio': len(optimized_points) / total_points if total_points > 0 else 0
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        @self.app.route('/api/routes/<route_id>/map-markers')
        def get_map_markers_optimized(route_id):
            """Get optimized markers data for map display"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            try:
                markers_data = self.db_manager.get_map_markers_data(route_id)
                
                if not markers_data:
                    return jsonify({'error': 'No marker data found'}), 404
                
                # Add summary statistics
                markers_data['statistics'] = {
                    'total_poi_markers': sum(len(pois) for pois in markers_data['pois'].values()),
                    'sharp_turn_markers': len(markers_data['sharp_turns']),
                    'network_issue_markers': len(markers_data['network_issues']),
                    'emergency_service_markers': len(markers_data['emergency_services']),
                    'traffic_incident_markers': len(markers_data['traffic_incidents']),
                    'total_markers': (
                        sum(len(pois) for pois in markers_data['pois'].values()) +
                        len(markers_data['sharp_turns']) +
                        len(markers_data['network_issues']) +
                        len(markers_data['emergency_services']) +
                        len(markers_data['traffic_incidents'])
                    )
                }
                
                return jsonify(markers_data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/routes/<route_id>/gps-track/<float:lat>/<float:lng>')
        def track_gps_position(route_id, lat, lng):
            """Track current GPS position and find nearest route point"""
            if 'logged_in' not in session:
                return jsonify({'error': 'Not authenticated'}), 401
            
            try:
                route_points = self.db_manager.get_route_points(route_id)
                
                if not route_points:
                    return jsonify({'error': 'No route points found'}), 404
                
                # Find nearest route point
                min_distance = float('inf')
                nearest_point = None
                nearest_index = -1
                
                for i, point in enumerate(route_points):
                    # Simple distance calculation (for more accuracy, use haversine formula)
                    distance = ((lat - point['latitude'])**2 + (lng - point['longitude'])**2)**0.5
                    if distance < min_distance:
                        min_distance = distance
                        nearest_point = point
                        nearest_index = i
                
                # Calculate progress percentage
                progress_percentage = (nearest_index / len(route_points)) * 100 if route_points else 0
                
                # Get nearby POIs (within 1km)
                nearby_pois = []
                try:
                    poi_types = ['hospital', 'gas_station', 'police', 'fire_station']
                    for poi_type in poi_types:
                        pois = self.db_manager.get_enhanced_pois_by_type(route_id, poi_type)
                        for poi in pois:
                            if poi.get('latitude', 0) != 0 and poi.get('longitude', 0) != 0:
                                poi_distance = ((lat - poi['latitude'])**2 + (lng - poi['longitude'])**2)**0.5
                                if poi_distance < 0.01:  # Roughly 1km
                                    nearby_pois.append({
                                        'name': poi.get('name', 'Unknown'),
                                        'type': poi_type,
                                        'distance': poi_distance * 111,  # Convert to rough km
                                        'phone': poi.get('phone_number', poi.get('formatted_phone_number', ''))
                                    })
                except:
                    pass
                
                return jsonify({
                    'current_position': {'lat': lat, 'lng': lng},
                    'nearest_route_point': nearest_point,
                    'route_progress': {
                        'current_index': nearest_index,
                        'total_points': len(route_points),
                        'progress_percentage': round(progress_percentage, 2)
                    },
                    'nearby_pois': nearby_pois,
                    'distance_to_route': round(min_distance * 111, 2)  # Rough km conversion
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    def run(self, debug=True, port=5000):
        """Run the Flask application"""
        print("\n🚀 Starting Fresh Route Analysis System...")
        print("=" * 70)
        print(f"📍 Admin Login: {self.ADMIN_USERNAME} / {self.ADMIN_PASSWORD}")
        print(f"💾 Database: SQLite with comprehensive route storage")
        print(f"🔧 API Tracking: All API calls monitored and logged")
        print(f"📊 PDF Generator: Modular page-based generation")
        print(f"🌐 Application URL: http://localhost:{port}")
        print("=" * 70)
        
        self.app.run(debug=debug, host='0.0.0.0', port=port)

# Create and run application
if __name__ == '__main__':
    app = RouteAnalysisApp()
    app.run()