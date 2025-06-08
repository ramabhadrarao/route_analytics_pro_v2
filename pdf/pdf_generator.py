# pdf/pdf_generator.py - Modular PDF Generator for Route Analysis System
# Purpose: Generate PDF reports page by page from database data with exact look and feel
# Dependencies: fpdf2, PIL, requests, matplotlib
# Author: Route Analysis System
# Created: 2024

import os
import datetime
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from fpdf import FPDF
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from PIL import Image
    import requests
    import io
    import tempfile
except ImportError as e:
    print(f"Warning: PDF dependencies not fully available: {e}")
    print("Install with: pip install fpdf2 matplotlib pillow requests")

class PDFGenerator:
    """Modular PDF generator with page-based generation from database"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # HPCL color scheme (matching original)
        self.primary_color = (0, 82, 147)      # HPCL Blue
        self.secondary_color = (60, 60, 60)    # Dark Gray
        self.danger_color = (220, 53, 69)      # Red
        self.warning_color = (253, 126, 20)    # Orange
        self.success_color = (40, 167, 69)     # Green
        self.info_color = (0, 82, 147)         # HPCL Blue
        
        # Available pages
        self.available_pages = {
            'title': 'Title Page',
            'overview': 'Route Overview',
            'turns': 'Sharp Turns Analysis',
            'pois': 'Points of Interest',
            'network': 'Network Coverage',
            'weather': 'Weather Analysis', 
            'compliance': 'Regulatory Compliance',
            'elevation': 'Elevation Analysis',
            'emergency': 'Emergency Planning',
            'api_status': 'API Status Report'
        }
    
    def generate_route_pdf(self, route_id: str, pages: str = 'all') -> Optional[str]:
        """
        Generate PDF report for specific route with selected pages
        
        Args:
            route_id: Route identifier
            pages: Comma-separated page names or 'all'
        
        Returns:
            Path to generated PDF file or None if failed
        """
        try:
            # Get route data
            route = self.db_manager.get_route(route_id)
            if not route:
                print(f"Route {route_id} not found")
                return None
            
            # Parse requested pages
            if pages.lower() == 'all':
                requested_pages = list(self.available_pages.keys())
            else:
                requested_pages = [p.strip() for p in pages.split(',')]
                # Validate page names
                requested_pages = [p for p in requested_pages if p in self.available_pages]
            
            if not requested_pages:
                print("No valid pages requested")
                return None
            
            print(f"📄 Generating PDF for route {route_id} with pages: {', '.join(requested_pages)}")
            
            # Create PDF
            pdf = EnhancedRoutePDF()
            
            # Generate each requested page
            for page_name in requested_pages:
                print(f"   Generating {self.available_pages[page_name]}...")
                
                if page_name == 'title':
                    self._add_title_page(pdf, route)
                elif page_name == 'overview':
                    self._add_overview_page(pdf, route_id)
                elif page_name == 'turns':
                    self._add_turns_page(pdf, route_id)
                elif page_name == 'pois':
                    self._add_pois_page(pdf, route_id)
                elif page_name == 'network':
                    self._add_network_page(pdf, route_id)
                elif page_name == 'weather':
                    self._add_weather_page(pdf, route_id)
                elif page_name == 'compliance':
                    self._add_compliance_page(pdf, route_id)
                elif page_name == 'elevation':
                    self._add_elevation_page(pdf, route_id)
                elif page_name == 'emergency':
                    self._add_emergency_page(pdf, route_id)
                elif page_name == 'api_status':
                    self._add_api_status_page(pdf, route_id)
            
            # Save PDF
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"route_analysis_{route_id}_{timestamp}.pdf"
            filepath = os.path.join('reports', filename)
            
            os.makedirs('reports', exist_ok=True)
            pdf.output(filepath)
            
            print(f"✅ PDF generated successfully: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            return None
    
    def _add_title_page(self, pdf: 'EnhancedRoutePDF', route: Dict):
        """Add professional title page"""
        pdf.add_page()
        
        # Background
        pdf.set_fill_color(245, 248, 252)
        pdf.rect(0, 0, 210, 297, 'F')
        
        # Header with HPCL branding
        pdf.set_fill_color(*self.primary_color)
        pdf.rect(0, 0, 210, 90, 'F')
        
        # Title
        pdf.set_font('Helvetica', 'B', 26)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(20, 25)
        pdf.cell(0, 15, 'HINDUSTAN PETROLEUM CORPORATION LIMITED', 0, 1, 'L')
        
        pdf.set_font('Helvetica', '', 14)
        pdf.set_xy(20, 45)
        pdf.cell(0, 8, 'Journey Risk Management Division', 0, 1, 'L')
        
        # Route information
        pdf.set_xy(20, 110)
        pdf.set_font('Helvetica', 'B', 20)
        pdf.set_text_color(*self.primary_color)
        pdf.cell(0, 12, 'JOURNEY RISK MANAGEMENT (JRM) STUDY', 0, 1, 'C')
        pdf.cell(0, 12, 'USING ARTIFICIAL INTELLIGENCE (AI)', 0, 1, 'C')
        
        # Route details box
        pdf.set_xy(25, 175)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(*self.primary_color)
        pdf.rect(25, 175, 160, 100, 'DF')
        
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(*self.primary_color)
        pdf.set_xy(35, 185)
        pdf.cell(0, 10, 'ROUTE ANALYSIS REPORT', 0, 1, 'L')
        
        # Route details
        pdf.set_font('Helvetica', '', 12)
        pdf.set_text_color(60, 60, 60)
        
        details = [
            f"Route ID: {route['id'][:8]}...",
            f"From: {route.get('from_address', 'Unknown')[:50]}...",
            f"To: {route.get('to_address', 'Unknown')[:50]}...",
            f"Distance: {route.get('distance', 'Unknown')}",
            f"Duration: {route.get('duration', 'Unknown')}",
            f"Generated: {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        ]
        
        y_pos = 205
        for detail in details:
            pdf.set_xy(35, y_pos)
            pdf.cell(0, 8, detail, 0, 1, 'L')
            y_pos += 10
    
    def _add_overview_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add route overview page"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        overview_data = route_api.get_route_overview(route_id)
        
        if 'error' in overview_data:
            return
        
        pdf.add_page()
        pdf.add_section_header("ROUTE OVERVIEW & STATISTICS", "primary")
        
        # Route information
        route_info = overview_data['route_info']
        stats = overview_data['statistics']
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, 'ROUTE INFORMATION', 0, 1, 'L')
        
        route_table = [
            ['From Address', route_info.get('from_address', 'Unknown')[:60]],
            ['To Address', route_info.get('to_address', 'Unknown')[:60]],
            ['Total Distance', route_info.get('distance', 'Unknown')],
            ['Estimated Duration', route_info.get('duration', 'Unknown')],
            ['Route Points Analyzed', str(stats['total_points'])],
            ['Analysis Date', route_info.get('created_at', '')[:19]],
            ['Overall Safety Score', f"{stats['safety_score']}/100 - {stats['safety_rating']}"]
        ]
        
        pdf.create_simple_table(route_table, [60, 120])
        
        # Hazard statistics
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, 'HAZARD ANALYSIS SUMMARY', 0, 1, 'L')
        
        hazard_table = [
            ['Total Sharp Turns', str(stats['total_sharp_turns'])],
            ['Extreme Turns (>90°)', str(stats['extreme_turns'])],
            ['Blind Spots (80-90°)', str(stats['blind_spots'])],
            ['Sharp Danger (70-80°)', str(stats['sharp_danger'])],
            ['Moderate Turns (45-70°)', str(stats['moderate_turns'])],
            ['Network Dead Zones', str(stats['dead_zones'])],
            ['Poor Coverage Areas', str(stats['poor_coverage_zones'])]
        ]
        
        pdf.create_simple_table(hazard_table, [60, 120])
        
        # Safety assessment
        pdf.ln(10)
        safety_score = stats['safety_score']
        if safety_score >= 80:
            color = self.success_color
            status = "SAFE"
        elif safety_score >= 60:
            color = self.warning_color
            status = "MODERATE RISK"
        else:
            color = self.danger_color
            status = "HIGH RISK"
        
        pdf.set_fill_color(*color)
        pdf.rect(10, pdf.get_y(), 190, 15, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_xy(15, pdf.get_y() + 3)
        pdf.cell(180, 9, f'OVERALL SAFETY ASSESSMENT: {status} (Score: {safety_score}/100)', 0, 1, 'C')
    
    def _add_turns_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add sharp turns analysis page"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        turns_data = route_api.get_sharp_turns(route_id)
        
        if 'error' in turns_data:
            return
        
        pdf.add_page()
        pdf.add_section_header("SHARP TURNS ANALYSIS", "danger")
        
        # Summary statistics
        summary = turns_data['summary']
        
        stats_table = [
            ['Total Sharp Turns', str(turns_data['total_turns'])],
            ['Most Dangerous Angle', f"{summary['most_dangerous_angle']:.1f}°"],
            ['Average Turn Angle', f"{summary['average_angle']:.1f}°"],
            ['Critical Turns', str(summary['critical_turns_count'])],
            ['Street View Images', str(turns_data['images_available']['street_view'])],
            ['Satellite Images', str(turns_data['images_available']['satellite'])]
        ]
        
        pdf.create_simple_table(stats_table, [60, 120])
        
        # Categorized turns table
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.danger_color)
        pdf.cell(0, 8, 'DANGEROUS TURNS BY CATEGORY', 0, 1, 'L')
        
        categorized = turns_data['categorized_turns']
        
        # Create table for all turns
        headers = ['Turn #', 'Angle', 'Classification', 'Danger Level', 'Speed Limit', 'GPS Coordinates']
        col_widths = [15, 20, 40, 25, 25, 60]
        
        pdf.create_table_header(headers, col_widths)
        
        # Add turns by category (most dangerous first)
        turn_number = 1
        for category_name, turns in [
            ('extreme_blind_spots', categorized['extreme_blind_spots']),
            ('blind_spots', categorized['blind_spots']),
            ('sharp_danger', categorized['sharp_danger']),
            ('moderate_turns', categorized['moderate_turns'])
        ]:
            for turn in turns[:5]:  # Limit per category
                if pdf.get_y() > 270:
                    break
                
                row_data = [
                    str(turn_number),
                    f"{turn['angle']:.1f}°",
                    turn['classification'],
                    turn['danger_level'],
                    f"{turn.get('recommended_speed', 40)} km/h",
                    f"{turn['latitude']:.4f}, {turn['longitude']:.4f}"
                ]
                
                pdf.create_table_row(row_data, col_widths)
                turn_number += 1
        
        # Add stored images information
        if turns_data['images_available']['street_view'] > 0:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, 'STORED TURN IMAGES', 0, 1, 'L')
            
            # Get and display sample images
            stored_images = self.db_manager.get_stored_images(route_id, 'street_view')
            self._add_stored_images_info(pdf, stored_images[:5])
    
    def _add_pois_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add Points of Interest page"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        pois_data = route_api.get_points_of_interest(route_id)
        
        if 'error' in pois_data:
            return
        
        pdf.add_page()
        pdf.add_section_header("POINTS OF INTEREST ALONG ROUTE", "info")
        
        # POI Statistics
        stats = pois_data['statistics']
        
        stats_table = [
            ['Total POIs Found', str(stats['total_pois'])],
            ['Emergency Services', str(stats['emergency_services'])],
            ['Essential Services', str(stats['essential_services'])],
            ['Other Services', str(stats['other_services'])],
            ['Coverage Score', f"{stats['coverage_score']}/100"],
            ['Service Availability', 'GOOD' if stats['coverage_score'] > 70 else 'MODERATE' if stats['coverage_score'] > 40 else 'LIMITED']
        ]
        
        pdf.create_simple_table(stats_table, [60, 120])
        
        # POI Categories
        pois = pois_data['pois_by_type']
        
        poi_categories = [
            ('hospitals', 'HOSPITALS - Emergency Medical Services', self.danger_color),
            ('gas_stations', 'FUEL STATIONS - Refueling Points', self.warning_color),
            ('police', 'POLICE STATIONS - Security Services', self.primary_color),
            ('fire_stations', 'FIRE STATIONS - Emergency Response', self.danger_color),
            ('schools', 'SCHOOLS - Speed Limit Zones (40 km/h)', self.success_color),
            ('restaurants', 'RESTAURANTS - Rest & Food Stops', self.info_color)
        ]
        
        for poi_type, title, color in poi_categories:
            poi_list = pois.get(poi_type, [])
            if not poi_list:
                continue
            
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*color)
            pdf.cell(0, 8, f'{title} ({len(poi_list)} found)', 0, 1, 'L')
            
            # Create table for this POI type
            headers = ['S.No', 'Name', 'Address', 'Distance Info']
            col_widths = [15, 60, 70, 40]
            
            pdf.create_table_header(headers, col_widths)
            
            for i, poi in enumerate(poi_list[:10], 1):  # Limit to 10 per type
                row_data = [
                    str(i),
                    poi.get('name', 'Unknown')[:25],
                    poi.get('address', 'Unknown location')[:30],
                    f"Along route"
                ]
                
                pdf.create_table_row(row_data, col_widths)
        
        # Recommendations
        recommendations = pois_data.get('recommendations', [])
        if recommendations:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, 'POI RECOMMENDATIONS', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            for i, rec in enumerate(recommendations, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(170, 6, rec, 0, 'L')
                pdf.ln(2)
    
    def _add_network_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add network coverage analysis page"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        network_data = route_api.get_network_coverage(route_id)
        
        if 'error' in network_data:
            return
        
        pdf.add_page()
        pdf.add_section_header("NETWORK COVERAGE ANALYSIS", "info")
        
        # Network Statistics
        stats = network_data['statistics']
        
        stats_table = [
            ['Points Analyzed', str(stats['total_points_analyzed'])],
            ['Overall Coverage Score', f"{stats['overall_coverage_score']}/100"],
            ['Dead Zones', str(stats['dead_zones_count'])],
            ['Poor Coverage Areas', str(stats['poor_coverage_count'])],
            ['Good Coverage', f"{stats['good_coverage_percentage']}%"],
            ['Network Reliability', 'HIGH' if stats['overall_coverage_score'] > 80 else 'MEDIUM' if stats['overall_coverage_score'] > 60 else 'LOW']
        ]
        
        pdf.create_simple_table(stats_table, [60, 120])
        
        # Quality Distribution
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, 'COVERAGE QUALITY DISTRIBUTION', 0, 1, 'L')
        
        quality_dist = network_data['quality_distribution']
        quality_table = []
        
        quality_colors = {
            'excellent': 'Excellent (Strong Signal)',
            'good': 'Good (Reliable Signal)',
            'fair': 'Fair (Adequate Signal)',
            'poor': 'Poor (Weak Signal)',
            'dead': 'Dead Zone (No Signal)'
        }
        
        for quality, count in quality_dist.items():
            quality_table.append([
                quality_colors.get(quality, quality.title()),
                str(count),
                f"{(count/stats['total_points_analyzed']*100):.1f}%" if stats['total_points_analyzed'] > 0 else "0%"
            ])
        
        headers = ['Coverage Quality', 'Points', 'Percentage']
        col_widths = [60, 30, 30]
        
        pdf.create_table_header(headers, col_widths)
        for row in quality_table:
            pdf.create_table_row(row, col_widths)
        
        # Problem Areas
        dead_zones = network_data['problem_areas']['dead_zones']
        if dead_zones:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.danger_color)
            pdf.cell(0, 8, f'NETWORK DEAD ZONES ({len(dead_zones)} identified)', 0, 1, 'L')
            
            headers = ['Zone #', 'GPS Coordinates', 'Coverage Quality', 'Impact']
            col_widths = [20, 50, 40, 75]
            
            pdf.create_table_header(headers, col_widths)
            
            for i, zone in enumerate(dead_zones[:10], 1):
                row_data = [
                    str(i),
                    f"{zone['latitude']:.4f}, {zone['longitude']:.4f}",
                    zone['coverage_quality'].title(),
                    "No cellular service available"
                ]
                pdf.create_table_row(row_data, col_widths)
        
        # Recommendations
        recommendations = network_data.get('recommendations', [])
        if recommendations:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, 'NETWORK COVERAGE RECOMMENDATIONS', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            for i, rec in enumerate(recommendations, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(170, 6, rec, 0, 'L')
                pdf.ln(2)
    
    def _add_weather_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add weather analysis page"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        weather_data = route_api.get_weather_data(route_id)
        
        if 'error' in weather_data:
            return
        
        pdf.add_page()
        pdf.add_section_header("WEATHER CONDITIONS ANALYSIS", "warning")
        
        # Weather Statistics
        stats = weather_data['statistics']
        
        stats_table = [
            ['Weather Points Analyzed', str(stats['points_analyzed'])],
            ['Average Temperature', f"{stats['average_temperature']}°C"],
            ['Average Humidity', f"{stats['average_humidity']}%"],
            ['Average Wind Speed', f"{stats['average_wind_speed']} km/h"],
            ['Temperature Range', f"{stats['temperature_range']['min']}°C to {stats['temperature_range']['max']}°C"],
            ['Weather Conditions', f"{len(weather_data['conditions_summary'])} different conditions"]
        ]
        
        pdf.create_simple_table(stats_table, [60, 120])
        
        # Weather Conditions Summary
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, 'WEATHER CONDITIONS SUMMARY', 0, 1, 'L')
        
        conditions = weather_data['conditions_summary']
        
        headers = ['Weather Condition', 'Occurrences', 'Impact Assessment']
        col_widths = [50, 30, 105]
        
        pdf.create_table_header(headers, col_widths)
        
        for condition, count in conditions.items():
            impact = "HIGH RISK" if condition in ['Thunderstorm', 'Rain'] else "MODERATE" if condition in ['Clouds'] else "LOW RISK"
            row_data = [condition, str(count), impact]
            pdf.create_table_row(row_data, col_widths)
        
        # Weather Risks
        weather_risks = weather_data.get('weather_risks', [])
        if weather_risks:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.danger_color)
            pdf.cell(0, 8, 'IDENTIFIED WEATHER RISKS', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for i, risk in enumerate(weather_risks, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(170, 6, risk, 0, 'L')
                pdf.ln(2)
        
        # Weather Recommendations
        recommendations = weather_data.get('recommendations', [])
        if recommendations:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, 'WEATHER-BASED RECOMMENDATIONS', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            for i, rec in enumerate(recommendations, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(170, 6, rec, 0, 'L')
                pdf.ln(2)
    
    def _add_compliance_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add regulatory compliance page"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        compliance_data = route_api.get_compliance_data(route_id)
        
        if 'error' in compliance_data:
            return
        
        pdf.add_page()
        pdf.add_section_header("REGULATORY COMPLIANCE ANALYSIS", "danger")
        
        # Compliance Score
        assessment = compliance_data['compliance_assessment']
        score = assessment['overall_score']
        
        if score >= 80:
            color = self.success_color
            status = "COMPLIANT"
        elif score >= 60:
            color = self.warning_color
            status = "NEEDS ATTENTION"
        else:
            color = self.danger_color
            status = "NON-COMPLIANT"
        
        pdf.set_fill_color(*color)
        pdf.rect(10, pdf.get_y(), 190, 15, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_xy(15, pdf.get_y() + 3)
        pdf.cell(180, 9, f'COMPLIANCE STATUS: {status} (Score: {score}/100)', 0, 1, 'C')
        pdf.ln(5)
        
        # Vehicle Information
        pdf.set_text_color(0, 0, 0)
        vehicle_info = compliance_data['vehicle_info']
        
        vehicle_table = [
            ['Vehicle Type', vehicle_info['type'].replace('_', ' ').title()],
            ['Vehicle Category', vehicle_info['category']],
            ['Vehicle Weight', f"{vehicle_info['weight']:,} kg"],
            ['AIS-140 Required', 'YES' if vehicle_info['ais_140_required'] else 'NO'],
            ['Route Distance', compliance_data['route_analysis']['distance']],
            ['Estimated Duration', compliance_data['route_analysis']['duration']]
        ]
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, 'VEHICLE & ROUTE INFORMATION', 0, 1, 'L')
        pdf.create_simple_table(vehicle_table, [60, 120])
        
        # Compliance Issues
        issues = assessment['issues_identified']
        if issues:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.danger_color)
            pdf.cell(0, 8, f'COMPLIANCE ISSUES IDENTIFIED ({len(issues)})', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for i, issue in enumerate(issues, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(170, 6, issue, 0, 'L')
                pdf.ln(2)
        
        # Critical Requirements
        requirements = assessment['critical_requirements']
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, 'CRITICAL COMPLIANCE REQUIREMENTS', 0, 1, 'L')
        
        pdf.set_font('Helvetica', '', 10)
        for i, req in enumerate(requirements, 1):
            pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
            pdf.multi_cell(170, 6, req, 0, 'L')
            pdf.ln(2)
        
        # Recommendations
        recommendations = compliance_data.get('recommendations', [])
        if recommendations:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 8, 'COMPLIANCE RECOMMENDATIONS', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            for i, rec in enumerate(recommendations, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(170, 6, rec, 0, 'L')
                pdf.ln(2)
    
    def _add_elevation_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add elevation analysis page"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        elevation_data = route_api.get_elevation_data(route_id)
        
        if 'error' in elevation_data:
            return
        
        pdf.add_page()
        pdf.add_section_header("ELEVATION ANALYSIS", "success")
        
        # Elevation Statistics
        stats = elevation_data['statistics']
        
        stats_table = [
            ['Minimum Elevation', f"{stats['min_elevation']} m"],
            ['Maximum Elevation', f"{stats['max_elevation']} m"],
            ['Average Elevation', f"{stats['average_elevation']} m"],
            ['Elevation Range', f"{stats['elevation_range']} m"],
            ['Total Points Analyzed', str(stats['total_points'])],
            ['Terrain Type', elevation_data['terrain_analysis']['terrain_type']]
        ]
        
        pdf.create_simple_table(stats_table, [60, 120])
        
        # Terrain Analysis
        terrain = elevation_data['terrain_analysis']
        
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, 'TERRAIN ANALYSIS', 0, 1, 'L')
        
        terrain_table = [
            ['Terrain Classification', terrain['terrain_type']],
            ['Driving Difficulty', terrain['driving_difficulty']],
            ['Fuel Impact', terrain['fuel_impact']]
        ]
        
        pdf.create_simple_table(terrain_table, [60, 120])
        
        # Significant Elevation Changes
        changes = elevation_data['significant_changes']
        if changes:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.warning_color)
            pdf.cell(0, 8, f'SIGNIFICANT ELEVATION CHANGES ({len(changes)})', 0, 1, 'L')
            
            headers = ['Change #', 'Type', 'Elevation Change', 'From (m)', 'To (m)', 'GPS Coordinates']
            col_widths = [20, 25, 30, 25, 25, 60]
            
            pdf.create_table_header(headers, col_widths)
            
            for i, change in enumerate(changes[:10], 1):
                location = change['location']
                row_data = [
                    str(i),
                    change['type'].title(),
                    f"{change['elevation_change']:.0f} m",
                    f"{change['from_elevation']:.0f}",
                    f"{change['to_elevation']:.0f}",
                    f"{location['latitude']:.4f}, {location['longitude']:.4f}"
                ]
                pdf.create_table_row(row_data, col_widths)
    
    def _add_emergency_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add emergency planning page"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        emergency_data = route_api.get_emergency_data(route_id)
        
        if 'error' in emergency_data:
            return
        
        pdf.add_page()
        pdf.add_section_header("EMERGENCY PREPAREDNESS ANALYSIS", "danger")
        
        # Emergency Score
        assessment = emergency_data['preparedness_assessment']
        score = assessment['emergency_score']
        
        if score >= 80:
            color = self.success_color
            status = "EXCELLENT"
        elif score >= 60:
            color = self.warning_color
            status = "GOOD"
        else:
            color = self.danger_color
            status = "NEEDS IMPROVEMENT"
        
        pdf.set_fill_color(*color)
        pdf.rect(10, pdf.get_y(), 190, 15, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_xy(15, pdf.get_y() + 3)
        pdf.cell(180, 9, f'EMERGENCY PREPAREDNESS: {status} (Score: {score}/100)', 0, 1, 'C')
        pdf.ln(5)
        
        # Emergency Services Summary
        services = emergency_data['emergency_services']
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, 'EMERGENCY SERVICES AVAILABILITY', 0, 1, 'L')
        
        services_table = [
            ['Hospitals', str(len(services['hospitals']))],
            ['Police Stations', str(len(services['police_stations']))],
            ['Fire Stations', str(len(services['fire_stations']))],
            ['Communication Reliability', emergency_data['communication_analysis']['communication_reliability']],
            ['Network Dead Zones', str(emergency_data['communication_analysis']['dead_zones'])]
        ]
        
        pdf.create_simple_table(services_table, [60, 120])
        
        # Emergency Contacts
        contacts = emergency_data['emergency_contacts']
        
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, 'EMERGENCY CONTACT NUMBERS', 0, 1, 'L')
        
        headers = ['Service', 'Contact Number', 'Purpose']
        col_widths = [40, 30, 115]
        
        pdf.create_table_header(headers, col_widths)
        
        contact_list = [
            ('National Emergency', contacts['national_emergency'], 'All emergency services'),
            ('Police', contacts['police'], 'Police assistance'),
            ('Fire Services', contacts['fire'], 'Fire and rescue'),
            ('Ambulance', contacts['ambulance'], 'Medical emergency'),
            ('Highway Patrol', contacts['highway_patrol'], 'Highway assistance')
        ]
        
        for service, number, purpose in contact_list:
            pdf.create_table_row([service, number, purpose], col_widths)
        
        # Critical Gaps
        gaps = assessment.get('critical_gaps', [])
        if gaps:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.danger_color)
            pdf.cell(0, 8, 'CRITICAL PREPAREDNESS GAPS', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for i, gap in enumerate(gaps, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(170, 6, gap, 0, 'L')
                pdf.ln(2)
        
        # Emergency Recommendations
        recommendations = emergency_data.get('recommendations', [])
        if recommendations:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, 'EMERGENCY PREPAREDNESS RECOMMENDATIONS', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            for i, rec in enumerate(recommendations, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(170, 6, rec, 0, 'L')
                pdf.ln(2)
    
    def _add_api_status_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add API status and usage page"""
        from utils.api_tracker import APITracker
        
        # Get API usage for this route
        api_usage = self.db_manager.api_tracker.get_api_usage_by_route(route_id) if hasattr(self.db_manager, 'api_tracker') else []
        
        pdf.add_page()
        pdf.add_section_header("API STATUS & USAGE REPORT", "primary")
        
        # API Usage Summary for this route
        if api_usage:
            api_summary = {}
            total_calls = len(api_usage)
            successful_calls = len([call for call in api_usage if call['success']])
            
            for call in api_usage:
                api_name = call['api_name']
                if api_name not in api_summary:
                    api_summary[api_name] = {'calls': 0, 'success': 0, 'total_time': 0}
                
                api_summary[api_name]['calls'] += 1
                if call['success']:
                    api_summary[api_name]['success'] += 1
                api_summary[api_name]['total_time'] += call.get('response_time', 0)
            
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 8, f'API USAGE FOR THIS ROUTE (Total: {total_calls} calls)', 0, 1, 'L')
            
            headers = ['API Service', 'Calls Made', 'Success Rate', 'Avg Response Time']
            col_widths = [50, 30, 30, 45]
            
            pdf.create_table_header(headers, col_widths)
            
            for api_name, stats in api_summary.items():
                success_rate = (stats['success'] / stats['calls'] * 100) if stats['calls'] > 0 else 0
                avg_time = (stats['total_time'] / stats['calls']) if stats['calls'] > 0 else 0
                
                row_data = [
                    api_name.replace('_', ' ').title(),
                    str(stats['calls']),
                    f"{success_rate:.1f}%",
                    f"{avg_time:.3f}s"
                ]
                pdf.create_table_row(row_data, col_widths)
            
            # Overall success rate
            overall_success = (successful_calls / total_calls * 100) if total_calls > 0 else 0
            
            pdf.ln(5)
            pdf.set_font('Helvetica', 'B', 12)
            if overall_success >= 90:
                pdf.set_text_color(*self.success_color)
                status = "EXCELLENT"
            elif overall_success >= 75:
                pdf.set_text_color(*self.info_color)
                status = "GOOD"
            else:
                pdf.set_text_color(*self.danger_color)
                status = "NEEDS ATTENTION"
            
            pdf.cell(0, 8, f'OVERALL API SUCCESS RATE: {overall_success:.1f}% - {status}', 0, 1, 'L')
        
        else:
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(0, 8, 'No API usage data available for this route.', 0, 1, 'L')
        
        # Stored Images Summary
        stored_images = self.db_manager.get_stored_images(route_id)
        if stored_images:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, f'STORED IMAGES SUMMARY ({len(stored_images)} images)', 0, 1, 'L')
            
            # Group images by type
            image_types = {}
            total_size = 0
            
            for img in stored_images:
                img_type = img['image_type']
                if img_type not in image_types:
                    image_types[img_type] = {'count': 0, 'size': 0}
                
                image_types[img_type]['count'] += 1
                image_types[img_type]['size'] += img.get('file_size', 0)
                total_size += img.get('file_size', 0)
            
            headers = ['Image Type', 'Count', 'Total Size', 'Storage Location']
            col_widths = [40, 20, 30, 95]
            
            pdf.create_table_header(headers, col_widths)
            
            for img_type, stats in image_types.items():
                size_mb = stats['size'] / (1024 * 1024) if stats['size'] > 0 else 0
                
                row_data = [
                    img_type.replace('_', ' ').title(),
                    str(stats['count']),
                    f"{size_mb:.1f} MB",
                    f"images/{img_type}/"
                ]
                pdf.create_table_row(row_data, col_widths)
            
            pdf.ln(5)
            total_size_mb = total_size / (1024 * 1024) if total_size > 0 else 0
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 6, f'Total Storage Used: {total_size_mb:.1f} MB', 0, 1, 'L')
    
    def _add_stored_images_info(self, pdf: 'EnhancedRoutePDF', images: List[Dict]):
        """Add information about stored images"""
        if not images:
            return
        
        headers = ['Image File', 'Type', 'Location', 'Size', 'Date Created']
        col_widths = [40, 25, 50, 25, 45]
        
        pdf.create_table_header(headers, col_widths)
        
        for img in images:
            size_kb = img.get('file_size', 0) / 1024 if img.get('file_size') else 0
            created_date = img.get('created_at', '')[:16].replace('T', ' ')
            
            row_data = [
                img['filename'][:20],
                img['image_type'].replace('_', ' ').title(),
                f"{img.get('latitude', 0):.4f}, {img.get('longitude', 0):.4f}",
                f"{size_kb:.0f} KB",
                created_date
            ]
            pdf.create_table_row(row_data, col_widths)


class EnhancedRoutePDF(FPDF):
    """Enhanced PDF class with HPCL styling and utility methods"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
        # HPCL color scheme
        self.primary_color = (0, 82, 147)
        self.danger_color = (220, 53, 69)
        self.warning_color = (253, 126, 20)
        self.success_color = (40, 167, 69)
        self.info_color = (0, 82, 147)
    
    def header(self):
        """Page header with HPCL branding"""
        if self.page_no() == 1:
            return
        
        self.set_fill_color(*self.primary_color)
        self.rect(0, 0, 210, 22, 'F')
        
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 7)
        self.cell(0, 8, 'HPCL - Journey Risk Management Study (AI-Powered)', 0, 0, 'L')
        
        self.set_xy(-40, 7)
        self.cell(0, 8, f'Page {self.page_no()}', 0, 0, 'R')
        
        self.ln(27)
    
    def footer(self):
        """Page footer"""
        self.set_y(-15)
        self.set_draw_color(*self.primary_color)
        self.line(10, self.get_y(), 200, self.get_y())
        
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(*self.primary_color)
        self.set_y(-10)
        self.cell(0, 5, 'Generated by HPCL Journey Risk Management System', 0, 0, 'C')
    
    def add_section_header(self, title: str, color_type: str = 'primary'):
        """Add section header with color coding"""
        colors = {
            'primary': self.primary_color,
            'danger': self.danger_color,
            'success': self.success_color,
            'warning': self.warning_color,
            'info': self.info_color
        }
        
        color = colors.get(color_type, self.primary_color)
        
        if self.get_y() > 250:
            self.add_page()
        
        self.set_font('Helvetica', 'B', 16)
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.rect(10, self.get_y(), 190, 15, 'F')
        
        self.set_xy(15, self.get_y() + 3)
        self.cell(180, 9, title, 0, 1, 'L')
        self.ln(5)
    
    def create_simple_table(self, data: List[List[str]], col_widths: List[int]):
        """Create a simple two-column table"""
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        
        for row in data:
            if self.get_y() > 260:
                self.add_page()
            
            y_pos = self.get_y()
            
            # First column (bold)
            self.set_font('Helvetica', 'B', 10)
            self.set_xy(10, y_pos)
            self.cell(col_widths[0], 8, str(row[0])[:30], 1, 0, 'L')
            
            # Second column
            self.set_font('Helvetica', '', 10)
            self.set_xy(10 + col_widths[0], y_pos)
            self.cell(col_widths[1], 8, str(row[1])[:50], 1, 0, 'L')
            
            self.ln(8)
        
        self.ln(3)
    
    def create_table_header(self, headers: List[str], col_widths: List[int]):
        """Create table header"""
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(230, 230, 230)
        self.set_text_color(0, 0, 0)
        
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            self.set_xy(10 + sum(col_widths[:i]), self.get_y())
            self.cell(width, 10, header, 1, 0, 'C', True)
        self.ln(10)
    
    def create_table_row(self, row_data: List[str], col_widths: List[int]):
        """Create table row"""
        if self.get_y() > 270:
            self.add_page()
        
        self.set_font('Helvetica', '', 8)
        self.set_fill_color(255, 255, 255)
        self.set_text_color(0, 0, 0)
        
        y_pos = self.get_y()
        
        for i, (cell, width) in enumerate(zip(row_data, col_widths)):
            self.set_xy(10 + sum(col_widths[:i]), y_pos)
            self.cell(width, 8, str(cell)[:width//4], 1, 0, 'L')
        
        self.ln(8)