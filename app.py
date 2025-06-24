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