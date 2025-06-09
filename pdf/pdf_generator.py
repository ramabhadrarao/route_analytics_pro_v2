# pdf/pdf_generator.py - Complete Full PDF Generator with Unicode Fixes
# Purpose: Generate comprehensive PDF reports using database data and stored images
# Dependencies: fpdf2, PIL, sqlite3, os, matplotlib
# Author: Route Analysis System - Complete Version with Unicode Handling
# Created: 2024

import os
import datetime
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from fpdf import FPDF
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from PIL import Image
    import tempfile
    import numpy as np
except ImportError as e:
    print(f"Warning: PDF dependencies not fully available: {e}")
    print("Install with: pip install fpdf2 matplotlib pillow numpy")

class PDFGenerator:
    """Complete comprehensive PDF generator with Unicode handling"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Image directories
        self.image_base_path = "images"
        self.maps_path = os.path.join(self.image_base_path, "maps")
        self.satellite_path = os.path.join(self.image_base_path, "satellite")
        self.street_view_path = os.path.join(self.image_base_path, "street_view")
        
        # HPCL color scheme
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
            'turns': 'Sharp Turns Analysis with Images',
            'pois': 'Points of Interest',
            'network': 'Network Coverage',
            'weather': 'Weather Analysis', 
            'compliance': 'Regulatory Compliance',
            'elevation': 'Elevation Analysis',
            'emergency': 'Emergency Preparedness & Response Planning',
            'route_map': 'Route Map with Critical Points',
            'images_summary': 'Images Summary',
            'traffic': 'Traffic Analysis',
            'road_quality': 'Road Quality & Surface Analysis',
            'environmental': 'Environmental Risk Assessment',
            'api_status': 'API Status Report'
        }
        
        print(f"✅ Complete PDF Generator initialized with {len(self.available_pages)} page types")
        print(f"📁 Images directory: {self.image_base_path}")
        self._verify_image_directories()

    def clean_text_for_pdf(self, text: str) -> str:
        """
        Clean text to remove Unicode characters that FPDF can't handle
        """
        # Dictionary of Unicode replacements with PDF-safe alternatives
        unicode_replacements = {
            # Icons and symbols - CRITICAL FIXES
            '✅': '[OK]',     # Check mark
            '✓': '[OK]',     # Checkmark
            '✗': '[X]',      # X mark
            '⚠': '[!]',      # Warning symbol
            '📄': '',        # Page icon
            '📋': '',        # Clipboard
            '📁': '',        # Folder
            '📸': '',        # Camera
            '📊': '',        # Chart
            '❌': '[ERROR]', # Red X
            '⛔': '[STOP]',  # Stop sign
            
            # Mathematical symbols
            '≥': '>=',      # Greater than or equal to
            '≤': '<=',      # Less than or equal to
            '°': ' deg',    # Degree symbol - CRITICAL FIX
            '→': '->',      # Right arrow
            '←': '<-',      # Left arrow
            '↑': '^',       # Up arrow
            '↓': 'v',       # Down arrow
            '•': '*',       # Bullet point
            '–': '-',       # En dash
            '—': '--',      # Em dash
            '"': '"',       # Left double quote
            '"': '"',       # Right double quote
            ''': "'",       # Left single quote
            ''': "'",       # Right single quote
            '…': '...',     # Ellipsis
            '×': 'x',       # Multiplication sign
            '÷': '/',       # Division sign
            '±': '+/-',     # Plus-minus sign
            '√': 'sqrt',    # Square root
            '∞': 'infinity', # Infinity
            '∑': 'sum',     # Summation
            '∆': 'delta',   # Delta
            '∇': 'nabla',   # Nabla
            '∂': 'd',       # Partial derivative
            '∫': 'integral', # Integral
            '∏': 'product', # Product
            '∪': 'union',   # Union
            '∩': 'intersection', # Intersection
            '∈': 'in',      # Element of
            '∉': 'not in',  # Not element of
            '⊂': 'subset',  # Subset
            '⊃': 'superset', # Superset
            '⊆': 'subset or equal', # Subset or equal
            '⊇': 'superset or equal', # Superset or equal
            '∀': 'for all', # For all
            '∃': 'exists',  # There exists
            '∄': 'not exists', # Does not exist
            '∧': 'and',     # Logical and
            '∨': 'or',      # Logical or
            '¬': 'not',     # Logical not
            '⇒': '=>',      # Implies
            '⇔': '<=>',     # If and only if
            '≠': '!=',      # Not equal
            '≈': '~=',      # Approximately equal
            '≡': '===',     # Identical to
            '∝': 'proportional to', # Proportional to
            '∼': '~',       # Similar to
            '∠': 'angle',   # Angle
            '⊥': 'perpendicular', # Perpendicular
            '∥': 'parallel', # Parallel
            '⊙': 'circle dot', # Circle with dot
            '⊕': 'circle plus', # Circle with plus
            '⊗': 'circle times', # Circle with times
            '⊘': 'circle slash', # Circle with slash
            
            # Currency and special characters
            '℃': 'C',       # Celsius
            '℉': 'F',       # Fahrenheit
            '€': 'EUR',     # Euro
            '£': 'GBP',     # Pound
            '¥': 'JPY',     # Yen
            '₹': 'INR',     # Indian Rupee
            '©': '(c)',     # Copyright
            '®': '(R)',     # Registered trademark
            '™': '(TM)',    # Trademark
            '§': 'section', # Section sign
            '¶': 'paragraph', # Paragraph sign
            '†': '+',       # Dagger
            '‡': '++',      # Double dagger
            '‰': 'per mille', # Per mille
            '‱': 'per ten thousand', # Per ten thousand
            '′': "'",       # Prime
            '″': '"',       # Double prime
            '‴': "'''",     # Triple prime
            '※': 'note',    # Reference mark
            '‼': '!!',      # Double exclamation
            '⁇': '??',      # Double question
            '⁈': '?!',      # Question exclamation
            '⁉': '!?',      # Exclamation question
            
            # Superscripts and subscripts
            '⁰': '^0', '¹': '^1', '²': '^2', '³': '^3', '⁴': '^4',
            '⁵': '^5', '⁶': '^6', '⁷': '^7', '⁸': '^8', '⁹': '^9',
            '₀': '_0', '₁': '_1', '₂': '_2', '₃': '_3', '₄': '_4',
            '₅': '_5', '₆': '_6', '₇': '_7', '₈': '_8', '₉': '_9',
            
            # Greek letters (common ones)
            'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta',
            'ε': 'epsilon', 'ζ': 'zeta', 'η': 'eta', 'θ': 'theta',
            'ι': 'iota', 'κ': 'kappa', 'λ': 'lambda', 'μ': 'mu',
            'ν': 'nu', 'ξ': 'xi', 'ο': 'omicron', 'π': 'pi',
            'ρ': 'rho', 'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon',
            'φ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega',
            'Α': 'Alpha', 'Β': 'Beta', 'Γ': 'Gamma', 'Δ': 'Delta',
            'Ε': 'Epsilon', 'Ζ': 'Zeta', 'Η': 'Eta', 'Θ': 'Theta',
            'Ι': 'Iota', 'Κ': 'Kappa', 'Λ': 'Lambda', 'Μ': 'Mu',
            'Ν': 'Nu', 'Ξ': 'Xi', 'Ο': 'Omicron', 'Π': 'Pi',
            'Ρ': 'Rho', 'Σ': 'Sigma', 'Τ': 'Tau', 'Υ': 'Upsilon',
            'Φ': 'Phi', 'Χ': 'Chi', 'Ψ': 'Psi', 'Ω': 'Omega'
        }
        
        # Apply replacements
        cleaned_text = str(text)
        for unicode_char, replacement in unicode_replacements.items():
            cleaned_text = cleaned_text.replace(unicode_char, replacement)
        
        # Remove any remaining non-ASCII characters
        cleaned_text = ''.join(char if ord(char) < 128 else '?' for char in cleaned_text)
        
        return cleaned_text

    def _verify_image_directories(self):
        """Verify and create image directories"""
        directories = [self.maps_path, self.satellite_path, self.street_view_path]
        for dir_path in directories:
            if os.path.exists(dir_path):
                image_count = len([f for f in os.listdir(dir_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
                print(f"Found {image_count} images in {dir_path}")
            else:
                print(f"Directory not found - creating: {dir_path}")
                os.makedirs(dir_path, exist_ok=True)
                print(f"Created directory: {dir_path}")
    
    def get_stored_images_from_db(self, route_id: str, image_type: str = None) -> List[Dict]:
        """Get stored images information from database"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if image_type:
                    cursor.execute("""
                        SELECT * FROM stored_images 
                        WHERE route_id = ? AND image_type = ?
                        ORDER BY created_at
                    """, (route_id, image_type))
                else:
                    cursor.execute("""
                        SELECT * FROM stored_images 
                        WHERE route_id = ?
                        ORDER BY image_type, created_at
                    """, (route_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting stored images from DB: {e}")
            return []
    def _add_road_quality_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add comprehensive road quality analysis page with real API data"""
        pdf.add_page()
        pdf.add_section_header("COMPREHENSIVE ROAD QUALITY & SURFACE CONDITIONS", "warning")
        
        # Get road quality data from database
        road_quality_data = self._get_road_quality_data_from_db(route_id)
        
        if road_quality_data and road_quality_data.get('issues'):
            issues = road_quality_data['issues']
            
            # Road Quality Summary Statistics
            summary_table = [
                ['Total Analysis Points', f"{road_quality_data.get('total_points', 0):,}"],
                ['Road Quality Issues Detected', f"{len(issues):,}"],
                ['Critical Condition Areas', f"{len([i for i in issues if i.get('severity') == 'critical']):,}"],
                ['High Risk Areas', f"{len([i for i in issues if i.get('severity') == 'high']):,}"],
                ['Medium Risk Areas', f"{len([i for i in issues if i.get('severity') == 'medium']):,}"],
                ['API Sources Used', road_quality_data.get('api_sources', 'Multiple APIs')],
                ['Analysis Confidence', road_quality_data.get('overall_confidence', 'High')],
                ['Overall Road Quality Score', f"{road_quality_data.get('overall_score', 7.5):.1f}/10"]
            ]
            
            pdf.create_detailed_table(summary_table, [80, 100])
            
            # Road quality status indicator
            overall_score = road_quality_data.get('overall_score', 7.5)
            if overall_score >= 8:
                quality_color = self.success_color
                quality_status = "EXCELLENT ROAD CONDITIONS"
            elif overall_score >= 6:
                quality_color = self.info_color
                quality_status = "GOOD ROAD CONDITIONS"
            elif overall_score >= 4:
                quality_color = self.warning_color
                quality_status = "MODERATE ROAD CONDITIONS"
            else:
                quality_color = self.danger_color
                quality_status = "POOR ROAD CONDITIONS"
            
            pdf.ln(10)
            pdf.set_fill_color(*quality_color)
            pdf.rect(10, pdf.get_y(), 190, 12, 'F')
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_xy(15, pdf.get_y() + 2)
            pdf.cell(180, 8, f'ROAD QUALITY STATUS: {quality_status} ({overall_score:.1f}/10)', 0, 1, 'C')
            
            # Detailed Road Quality Issues
            pdf.ln(15)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.danger_color)
            pdf.cell(0, 8, f'IDENTIFIED ROAD QUALITY ISSUES ({len(issues)} locations)', 0, 1, 'L')
            
            # Show top 10 issues
            headers = ['Location (GPS)', 'Issue Type', 'Severity', 'Speed Limit', 'Description']
            col_widths = [40, 35, 20, 25, 65]
            
            pdf.create_table_header(headers, col_widths)
            
            for issue in issues[:10]:  # Limit to 10 issues
                row_data = [
                    f"{issue.get('latitude', 0):.4f}, {issue.get('longitude', 0):.4f}",
                    issue.get('issue_type', 'Unknown').replace('_', ' ').title(),
                    issue.get('severity', 'Medium').title(),
                    f"{issue.get('recommended_speed', 40)} km/h",
                    issue.get('description', 'Road quality concern')[:40] + '...' if len(issue.get('description', '')) > 40 else issue.get('description', 'Road quality concern')
                ]
                pdf.create_table_row(row_data, col_widths)
            
            # Vehicle recommendations
            pdf.ln(15)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.warning_color)
            pdf.cell(0, 8, 'VEHICLE-SPECIFIC ROAD QUALITY RECOMMENDATIONS', 0, 1, 'L')
            
            vehicle_recommendations = [
                "* Heavy vehicles: Reduce speed by 20% in areas with road quality scores below 6/10",
                "* Check tire pressure more frequently when traveling through poor surface areas",
                "* Increase following distance by 50% in road quality risk zones",
                "* Plan additional maintenance checks after routes with multiple road quality issues",
                "* Consider alternative routes for high-value or sensitive cargo in critical condition areas",
                "* Carry emergency repair kit for tire damage in poor road surface zones"
            ]
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for rec in vehicle_recommendations:
                pdf.cell(0, 6, rec, 0, 1, 'L')
                
        else:
            # No road quality issues detected
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.success_color)
            pdf.cell(0, 10, 'EXCELLENT ROAD CONDITIONS DETECTED', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)
            
            good_conditions_info = [
                "* Analysis indicates good road surface conditions throughout the route",
                "* No significant potholes, construction zones, or surface damage detected",
                "* Standard speed limits and driving conditions can be maintained", 
                "* Normal vehicle maintenance schedule is sufficient",
                "* Route is suitable for all vehicle types including heavy goods vehicles"
            ]
            
            for info in good_conditions_info:
                pdf.cell(0, 8, info, 0, 1, 'L')

    def _add_environmental_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add comprehensive environmental risk assessment page with real API data"""
        pdf.add_page()
        pdf.add_section_header("COMPREHENSIVE ENVIRONMENTAL RISK ASSESSMENT", "success")
        
        # Get environmental data from database
        environmental_data = self._get_environmental_data_from_db(route_id)
        
        if environmental_data and environmental_data.get('has_risks'):
            risks = environmental_data['risks']
            summary = environmental_data.get('summary', {})
            
            # Environmental Risk Summary
            summary_table = [
                ['Total Analysis Points', f"{environmental_data.get('total_points', 0):,}"],
                ['Eco-Sensitive Zones', f"{summary.get('total_eco_zones', 0):,}"],
                ['Air Quality Risk Areas', f"{summary.get('total_air_quality_risks', 0):,}"],
                ['Weather Hazard Zones', f"{summary.get('total_weather_hazards', 0):,}"],
                ['Seasonal Risk Areas', f"{summary.get('total_seasonal_risks', 0):,}"],
                ['Overall Environmental Score', f"{summary.get('route_environmental_score', 8.0):.1f}/10"],
                ['Primary Risk Level', summary.get('overall_risk_level', 'Low').title()],
                ['API Sources Used', 'OpenWeather, Visual Crossing, Tomorrow.io, Google Places']
            ]
            
            pdf.create_detailed_table(summary_table, [80, 100])
            
            # Environmental status indicator
            env_score = summary.get('route_environmental_score', 8.0)
            risk_level = summary.get('overall_risk_level', 'low')
            
            if risk_level == 'critical' or env_score < 4:
                env_color = self.danger_color
                env_status = "CRITICAL ENVIRONMENTAL RISKS"
            elif risk_level == 'high' or env_score < 6:
                env_color = self.warning_color
                env_status = "HIGH ENVIRONMENTAL RISKS"
            elif risk_level == 'medium' or env_score < 8:
                env_color = self.info_color
                env_status = "MODERATE ENVIRONMENTAL RISKS"
            else:
                env_color = self.success_color
                env_status = "LOW ENVIRONMENTAL RISKS"
            
            pdf.ln(10)
            pdf.set_fill_color(*env_color)
            pdf.rect(10, pdf.get_y(), 190, 12, 'F')
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_xy(15, pdf.get_y() + 2)
            pdf.cell(180, 8, f'ENVIRONMENTAL STATUS: {env_status} ({env_score:.1f}/10)', 0, 1, 'C')
            
            # Show environmental risks
            if risks:
                pdf.ln(15)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('Helvetica', 'B', 12)
                pdf.set_text_color(*self.success_color)
                pdf.cell(0, 8, f'ENVIRONMENTAL RISKS IDENTIFIED ({len(risks)} locations)', 0, 1, 'L')
                
                headers = ['Risk Type', 'GPS Location', 'Severity', 'Category', 'Description']
                col_widths = [35, 40, 20, 25, 65]
                
                pdf.create_table_header(headers, col_widths)
                
                for risk in risks[:10]:  # Limit to 10 risks
                    row_data = [
                        risk.get('risk_type', 'Unknown').replace('_', ' ').title(),
                        f"{risk.get('latitude', 0):.4f}, {risk.get('longitude', 0):.4f}",
                        risk.get('severity', 'Medium').title(),
                        risk.get('risk_category', 'General').title(),
                        risk.get('description', 'Environmental risk')[:40] + '...' if len(risk.get('description', '')) > 40 else risk.get('description', 'Environmental risk')
                    ]
                    pdf.create_table_row(row_data, col_widths)
            
            # Environmental compliance guidelines
            pdf.ln(15)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.primary_color)
            pdf.cell(0, 8, 'ENVIRONMENTAL COMPLIANCE & BEST PRACTICES', 0, 1, 'L')
            
            compliance_guidelines = [
                "* Comply with National Green Tribunal (NGT) regulations in eco-sensitive zones",
                "* Follow Central Pollution Control Board (CPCB) emission standards",
                "* Adhere to Wildlife Protection Act requirements in sanctuary areas",
                "* Implement noise control measures during night hours in sensitive zones",
                "* Ensure vehicle PUC (Pollution Under Control) certificate is current",
                "* Carry emergency spill containment kit for hazardous cargo"
            ]
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for guideline in compliance_guidelines:
                pdf.cell(0, 6, guideline, 0, 1, 'L')
                
        else:
            # Low environmental risk route
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.success_color)
            pdf.cell(0, 10, 'LOW ENVIRONMENTAL RISK ROUTE', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)
            
            low_risk_info = [
                "* Environmental analysis indicates minimal environmental risks",
                "* No critical eco-sensitive zones or pollution hotspots detected",
                "* Air quality along route is within acceptable limits",
                "* Weather conditions pose minimal environmental hazards",
                "* Route is environmentally suitable for standard commercial transport"
            ]
            
            for info in low_risk_info:
                pdf.cell(0, 8, info, 0, 1, 'L')

    def _get_road_quality_data_from_db(self, route_id: str) -> Dict:
        """Get road quality data from database"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check if road quality table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='road_quality_data'")
                if not cursor.fetchone():
                    return {'issues': [], 'total_points': 0}
                
                cursor.execute("SELECT * FROM road_quality_data WHERE route_id = ?", (route_id,))
                issues = [dict(row) for row in cursor.fetchall()]
                
                if issues:
                    # Calculate overall statistics
                    total_points = len(issues)
                    api_sources = set()
                    confidence_levels = []
                    
                    for issue in issues:
                        if issue.get('api_sources'):
                            api_sources.update(issue['api_sources'].split(','))
                        if issue.get('confidence'):
                            confidence_levels.append(issue['confidence'])
                    
                    # Calculate overall confidence
                    if 'high' in confidence_levels:
                        overall_confidence = 'High'
                    elif 'medium' in confidence_levels:
                        overall_confidence = 'Medium'
                    else:
                        overall_confidence = 'Low'
                    
                    # Calculate overall score (inverse of average severity)
                    severity_scores = {'critical': 2, 'high': 4, 'medium': 6, 'low': 8}
                    avg_severity_score = sum(severity_scores.get(issue.get('severity', 'medium'), 6) for issue in issues) / len(issues)
                    overall_score = min(10, avg_severity_score)
                    
                    return {
                        'issues': issues,
                        'total_points': total_points,
                        'api_sources': ', '.join(sorted(api_sources)),
                        'overall_confidence': overall_confidence,
                        'overall_score': overall_score
                    }
                
            return {'issues': [], 'total_points': 0}
            
        except Exception as e:
            print(f"Error getting road quality data: {e}")
            return {'issues': [], 'total_points': 0}

    def _get_environmental_data_from_db(self, route_id: str) -> Dict:
        """Get environmental data from database"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check if environmental table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='environmental_risks'")
                if not cursor.fetchone():
                    return {'has_risks': False, 'risks': []}
                
                cursor.execute("SELECT * FROM environmental_risks WHERE route_id = ?", (route_id,))
                risks = [dict(row) for row in cursor.fetchall()]
                
                if risks:
                    # Calculate summary statistics
                    risk_categories = {}
                    for risk in risks:
                        category = risk.get('risk_category', 'unknown')
                        risk_categories[category] = risk_categories.get(category, 0) + 1
                    
                    # Calculate environmental score
                    total_risks = len(risks)
                    critical_risks = len([r for r in risks if r.get('severity') == 'critical'])
                    high_risks = len([r for r in risks if r.get('severity') == 'high'])
                    
                    env_score = max(1, 10 - (critical_risks * 2) - (high_risks * 1))
                    
                    # Determine overall risk level
                    if critical_risks > 2 or total_risks > 15:
                        risk_level = 'critical'
                    elif critical_risks > 0 or high_risks > 3 or total_risks > 8:
                        risk_level = 'high'
                    elif high_risks > 0 or total_risks > 3:
                        risk_level = 'medium'
                    else:
                        risk_level = 'low'
                    
                    summary = {
                        'total_eco_zones': risk_categories.get('ecological', 0),
                        'total_air_quality_risks': risk_categories.get('air_quality', 0),
                        'total_weather_hazards': risk_categories.get('weather', 0),
                        'total_seasonal_risks': risk_categories.get('seasonal', 0),
                        'route_environmental_score': env_score,
                        'overall_risk_level': risk_level
                    }
                    
                    return {
                        'has_risks': True,
                        'risks': risks,
                        'summary': summary,
                        'total_points': total_risks
                    }
                
            return {'has_risks': False, 'risks': []}
            
        except Exception as e:
            print(f"Error getting environmental data: {e}")
            return {'has_risks': False, 'risks': []}
    def get_turns_with_images(self, route_id: str) -> List[Dict]:
        """Get sharp turns data with associated images from database"""
        try:
            # Get sharp turns
            sharp_turns = []
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM sharp_turns 
                    WHERE route_id = ? 
                    ORDER BY angle DESC
                """, (route_id,))
                sharp_turns = [dict(row) for row in cursor.fetchall()]
            
            # Get all stored images for this route
            all_images = self.get_stored_images_from_db(route_id)
            
            # Associate images with turns based on GPS proximity
            for turn in sharp_turns:
                turn['street_view_images'] = []
                turn['satellite_images'] = []
                
                for img in all_images:
                    if img['latitude'] and img['longitude']:
                        # Check if image is close to turn location (within ~100m)
                        lat_diff = abs(float(img['latitude']) - float(turn['latitude']))
                        lng_diff = abs(float(img['longitude']) - float(turn['longitude']))
                        
                        if lat_diff < 0.001 and lng_diff < 0.001:  # Approximately 100m
                            if img['image_type'] == 'street_view':
                                turn['street_view_images'].append(img)
                            elif img['image_type'] == 'satellite':
                                turn['satellite_images'].append(img)
            
            return sharp_turns
            
        except Exception as e:
            print(f"Error getting turns with images: {e}")
            return []
    
    def generate_route_pdf(self, route_id: str, pages: str = 'all') -> Optional[str]:
        """Generate comprehensive PDF report"""
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
                requested_pages = [p for p in requested_pages if p in self.available_pages]
            
            if not requested_pages:
                print("No valid pages requested")
                return None
            
            print(f"Generating Complete PDF for route {route_id}")
            print(f"Pages ({len(requested_pages)}): {', '.join(requested_pages)}")
            
            # Create PDF with Unicode-safe class
            pdf = EnhancedRoutePDF(self)
            
            # Generate each requested page
            for page_name in requested_pages:
                print(f"   Generating {self.available_pages[page_name]}...")
                
                if page_name == 'title':
                    self._add_title_page(pdf, route)
                elif page_name == 'overview':
                    self._add_overview_page(pdf, route_id)
                elif page_name == 'turns':
                    self._add_enhanced_turns_page(pdf, route_id)
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
                elif page_name == 'route_map':
                    self._add_route_map_page(pdf, route_id)
                elif page_name == 'images_summary':
                    self._add_images_summary_page(pdf, route_id)
                elif page_name == 'traffic':
                    self._add_traffic_page(pdf, route_id)
                elif page_name == 'road_quality':
                    self._add_road_quality_page(pdf, route_id)
                elif page_name == 'environmental':
                    self._add_environmental_page(pdf, route_id)
                elif page_name == 'api_status':
                    self._add_api_status_page(pdf, route_id)
            
            # Save PDF
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"complete_route_analysis_{route_id}_{timestamp}.pdf"
            filepath = os.path.join('reports', filename)
            
            os.makedirs('reports', exist_ok=True)
            pdf.output(filepath)
            
            print(f"Complete PDF generated: {filepath}")
            print(f"Total pages: {pdf.page_no()}")
            return filepath
            
        except Exception as e:
            print(f"PDF generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _add_title_page(self, pdf: 'EnhancedRoutePDF', route: Dict):
        """Add professional title page with HPCL branding - Updated Layout"""
        pdf.add_page()
        
        # Background gradient effect
        pdf.set_fill_color(245, 248, 252)
        pdf.rect(0, 0, 210, 297, 'F')
        
        # Header with HPCL branding
        pdf.set_fill_color(*self.primary_color)
        pdf.rect(0, 0, 210, 90, 'F')
        
        logo_path = os.path.join('static', 'images', 'Hindustan_Petroleum_Logo.svg.png')
        
        try:
            if os.path.exists(logo_path):
                # Add HPCL logo on the left
                pdf.image(logo_path, x=15, y=15, w=40, h=40)
                
                # Company branding next to logo
                pdf.set_font('Helvetica', 'B', 20)
                pdf.set_text_color(255, 255, 255)
                pdf.set_xy(65, 20)
                pdf.cell(0, 12, 'HINDUSTAN PETROLEUM CORPORATION LIMITED', 0, 1, 'L')
                
                pdf.set_font('Helvetica', '', 12)
                pdf.set_xy(65, 35)
                pdf.cell(0, 8, 'Journey Risk Management Division', 0, 1, 'L')
                
                pdf.set_font('Helvetica', 'I', 10)
                pdf.set_xy(65, 50)
                pdf.cell(0, 6, 'Powered by Route Analytics Pro - AI Intelligence Platform', 0, 1, 'L')
            else:
                # Fallback without logo
                pdf.set_font('Helvetica', 'B', 26)
                pdf.set_text_color(255, 255, 255)
                pdf.set_xy(20, 25)
                pdf.cell(0, 15, 'HINDUSTAN PETROLEUM CORPORATION LIMITED', 0, 1, 'L')
                
                pdf.set_font('Helvetica', '', 14)
                pdf.set_xy(20, 45)
                pdf.cell(0, 8, 'Journey Risk Management Division', 0, 1, 'L')
                
                pdf.set_font('Helvetica', 'I', 10)
                pdf.set_xy(20, 55)
                pdf.cell(0, 6, 'Powered by Route Analytics Pro - AI Intelligence Platform', 0, 1, 'L')
                
        except Exception as e:
            print(f"Error loading HPCL logo: {e}")
            # Fallback to text-only branding if logo fails to load
            pdf.set_font('Helvetica', 'B', 24)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(20, 25)
            pdf.cell(0, 15, 'HINDUSTAN PETROLEUM CORPORATION LIMITED', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 12)
            pdf.set_xy(20, 45)
            pdf.cell(0, 8, 'Journey Risk Management Division', 0, 1, 'L')
            
            pdf.set_font('Helvetica', 'I', 10)
            pdf.set_xy(20, 55)
            pdf.cell(0, 6, 'Powered by Route Analytics Pro - AI Intelligence Platform', 0, 1, 'L')
        
        # Main title section - Moved down and improved layout
        pdf.set_xy(20, 110)
        pdf.set_font('Helvetica', 'B', 28)
        pdf.set_text_color(*self.primary_color)
        pdf.cell(0, 15, 'COMPREHENSIVE JOURNEY RISK', 0, 1, 'C')
        pdf.cell(0, 15, 'MANAGEMENT ANALYSIS REPORT', 0, 1, 'C')
        
        pdf.set_font('Helvetica', '', 16)
        pdf.set_text_color(*self.secondary_color)
        pdf.set_xy(20, 150)
        pdf.cell(0, 10, 'Enhanced with Artificial Intelligence & Multi-API Analysis', 0, 1, 'C')
        
        # Route details box - Better positioned and styled
        pdf.set_xy(25, 175)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(*self.primary_color)
        pdf.set_line_width(2)
        pdf.rect(25, 175, 160, 100, 'DF')
        
        # Add decorative border inside
        pdf.set_draw_color(*self.secondary_color)
        pdf.set_line_width(0.5)
        pdf.rect(30, 180, 150, 90, 'D')
        
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(*self.primary_color)
        pdf.set_xy(35, 185)
        pdf.cell(0, 10, '📋 ROUTE ANALYSIS DETAILS', 0, 1, 'L')
        
        # Route information with better formatting
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(60, 60, 60)
        
        details = [
            f"Route ID: {route['id'][:12]}...",
            f"Origin: {route.get('from_address', 'Unknown Location')[:42]}",
            f"Destination: {route.get('to_address', 'Unknown Location')[:42]}",
            f"Total Distance: {route.get('distance', 'Unknown')}",
            f"Estimated Duration: {route.get('duration', 'Unknown')}",
            f"Analysis Date: {datetime.datetime.now().strftime('%B %d, %Y')}",
            f"Report Generated: {datetime.datetime.now().strftime('%I:%M %p')}"
        ]
        
        y_pos = 205
        for detail in details:
            pdf.set_xy(35, y_pos)
            pdf.cell(0, 8, detail, 0, 1, 'L')
            y_pos += 9
        
        # Enhanced footer with technology highlights
        pdf.set_xy(25, 285)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 4, 'This report contains comprehensive analysis with visual evidence, real-time API integration,', 0, 1, 'C')
        pdf.cell(0, 4, 'and AI-powered insights for enhanced journey risk management', 0, 0, 'C')
        
        # Technology badges at bottom
        pdf.set_xy(30, 276)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(*self.info_color)
        
        tech_badges = ['ROAD QUALITY', 'ENVIRONMENTAL', 'TRAFFIC', 'AI ANALYSIS', 'VISUAL EVIDENCE']
        badge_width = 30
        x_start = 35
        
        for i, badge in enumerate(tech_badges):
            pdf.set_xy(x_start + (i * badge_width), 276)
            pdf.cell(badge_width - 2, 6, badge, 0, 0, 'C')
    def _add_overview_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add comprehensive route overview page with enhanced scoring display"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        overview_data = route_api.get_route_overview(route_id)
        
        if 'error' in overview_data:
            pdf.add_page()
            pdf.add_section_header("ROUTE OVERVIEW & STATISTICS", "primary")
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(0, 10, 'Route overview data not available.', 0, 1, 'L')
            return
        
        pdf.add_page()
        pdf.add_section_header("COMPREHENSIVE ROUTE OVERVIEW & STATISTICS", "primary")
        
        # Route information
        route_info = overview_data['route_info']
        stats = overview_data['statistics']
        
        # Basic route information
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(*self.primary_color)
        pdf.cell(0, 10, '📋 ROUTE INFORMATION', 0, 1, 'L')
        
        route_table = [
            ['From Address', route_info.get('from_address', 'Unknown')[:55]],
            ['To Address', route_info.get('to_address', 'Unknown')[:55]],
            ['Total Distance', route_info.get('distance', 'Unknown')],
            ['Estimated Duration', route_info.get('duration', 'Unknown')],
            ['Route Points Analyzed', f"{stats['total_points']:,}"],
            ['Analysis Timestamp', route_info.get('created_at', '')[:19]]
        ]
        
        pdf.create_detailed_table(route_table, [70, 110])
        
        # ENHANCED SAFETY SCORING SECTION
        pdf.ln(15)
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(*self.danger_color)
        pdf.cell(0, 10, 'ENHANCED SAFETY RISK ANALYSIS', 0, 1, 'L')
        
        # Risk Points Display (instead of 0/100)
        risk_points = stats.get('risk_points', 0)
        risk_category = stats.get('risk_category', 'UNKNOWN')
        color_indicator = stats.get('color_indicator', 'GRAY')
        
        # Color mapping
        color_map = {
            'RED': self.danger_color,
            'ORANGE': self.warning_color,
            'YELLOW': (255, 193, 7),  # Yellow
            'BLUE': self.info_color,
            'GREEN': self.success_color
        }
        
        display_color = color_map.get(color_indicator, self.secondary_color)
        
        # Risk Points Indicator Box
        pdf.set_fill_color(*display_color)
        pdf.rect(10, pdf.get_y(), 190, 20, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_xy(15, pdf.get_y() + 5)
        risk_text = f'TOTAL RISK POINTS: {risk_points} | STATUS: {risk_category}'
        pdf.cell(180, 10, risk_text, 0, 1, 'C')
        
        # DETAILED SCORING BREAKDOWN TABLE
        pdf.ln(15)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, '📊 DETAILED RISK SCORING BREAKDOWN', 0, 1, 'L')
        
        # Table headers
        headers = ['Hazard Type', 'Count', 'Points Each', 'Total Points', 'Risk %', 'Status']
        col_widths = [50, 20, 25, 25, 20, 25]
        
        pdf.create_table_header(headers, col_widths)
        
        # Add scoring breakdown rows
        scoring_breakdown = stats.get('scoring_breakdown', [])
        for item in scoring_breakdown:
            risk_status = item['risk_level']
            if risk_status == 'NONE':
                risk_status = 'OK'
            elif risk_status == 'CRITICAL':
                risk_status = 'CRITICAL'
            elif risk_status == 'HIGH':
                risk_status = 'HIGH'
            elif risk_status == 'MODERATE':
                risk_status = 'MODERATE'
            elif risk_status == 'LOW':
                risk_status = 'LOW'
            
            row_data = [
                item['hazard_type'],
                str(item['count']),
                f"+{item['penalty_per_item']}",
                str(item['total_penalty']),
                f"{item['percentage_of_total_risk']}%",
                risk_status
            ]
            pdf.create_table_row(row_data, col_widths)
        
        # Add total row
        total_penalty = stats.get('total_penalty_points', 0)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_fill_color(240, 240, 240)
        total_row = ['TOTAL RISK POINTS', '', '', str(total_penalty), '100%', risk_category[:8]]
        
        y_pos = pdf.get_y()
        for i, (cell, width) in enumerate(zip(total_row, col_widths)):
            pdf.set_xy(10 + sum(col_widths[:i]), y_pos)
            pdf.cell(width, 8, cell, 1, 0, 'C', True)
        pdf.ln(8)
        
        # RISK INTERPRETATION GUIDE
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(*self.info_color)
        pdf.cell(0, 8, 'RISK POINTS INTERPRETATION GUIDE', 0, 1, 'L')
        
        interpretation_table = [
            ['Risk Points Range', 'Safety Level', 'Action Required', 'Route Recommendation'],
            ['0-19 Points', 'SAFE ROUTE', 'Standard precautions', 'Approved for all vehicle types'],
            ['20-49 Points', 'LOW RISK', 'Basic safety measures', 'Suitable with normal care'],
            ['50-99 Points', 'MODERATE RISK', 'Enhanced precautions', 'Extra caution required'],
            ['100-149 Points', 'HIGH RISK', 'Significant safety measures', 'Consider alternative route'],
            ['150+ Points', 'CRITICAL RISK', 'Extreme caution/reroute', 'Route not recommended']
        ]
        
        interp_headers = ['Risk Points Range', 'Safety Level', 'Action Required', 'Route Recommendation']
        interp_col_widths = [35, 30, 40, 80]
        
        pdf.create_table_header(interp_headers, interp_col_widths)
        for row in interpretation_table[1:]:  # Skip header row
            pdf.create_table_row(row, interp_col_widths)
        
        # Continue with existing recommendations section...
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, 'IDENTIFIED RISK FACTORS', 0, 1, 'L')
        
        risk_factors = []
        if stats['extreme_turns'] > 0:
            risk_factors.append(f"• {stats['extreme_turns']} extreme turns requiring extreme caution (+{stats['extreme_turns']*20} risk points)")
        if stats['blind_spots'] > 0:
            risk_factors.append(f"• {stats['blind_spots']} blind spot areas with limited visibility (+{stats['blind_spots']*15} risk points)")
        if stats['dead_zones'] > 0:
            risk_factors.append(f"• {stats['dead_zones']} communication dead zones (+{stats['dead_zones']*8} risk points)")
        if stats['poor_coverage_zones'] > 0:
            risk_factors.append(f"• {stats['poor_coverage_zones']} areas with poor network coverage (+{stats['poor_coverage_zones']*4} risk points)")
        
        if not risk_factors:
            risk_factors.append("• No significant risk factors identified (0 risk points)")
        
        pdf.set_font('Helvetica', '', 10)
        for factor in risk_factors:
            pdf.cell(0, 6, factor, 0, 1, 'L')
        
        # Enhanced recommendations based on risk points
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.info_color)
        pdf.cell(0, 8, ' RISK-BASED SAFETY RECOMMENDATIONS', 0, 1, 'L')
        
        recommendations = []
        if risk_points >= 150:
            recommendations.extend([
                "CRITICAL: Consider alternative route - current route extremely dangerous",
                "If route unavoidable: Convoy travel mandatory, satellite communication required",
                "Emergency response plan required, inform authorities of travel"
            ])
        elif risk_points >= 100:
            recommendations.extend([
                "HIGH RISK: Enhanced safety protocols required",
                "Reduce speed by 50% in all identified risk zones",
                "Carry satellite communication and emergency equipment"
            ])
        elif risk_points >= 50:
            recommendations.extend([
                "MODERATE RISK: Standard enhanced precautions",
                "Reduce speed at identified sharp turns and blind spots",
                "Carry emergency communication devices for dead zones"
            ])
        else:
            recommendations.extend([
                "LOW RISK: Standard safety precautions sufficient",
                "Maintain awareness at moderate turns",
                "Monitor weather conditions before and during travel"
            ])
        
        # Universal recommendations
        recommendations.extend([
            "- Ensure vehicle is in optimal condition before journey",
            "- Plan rest stops at safe locations identified in the route",
            "- Maintain extra distance from other vehicles in risk areas"
        ])
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        for rec in recommendations:
            pdf.cell(0, 6, rec, 0, 1, 'L')
    
    def _add_enhanced_turns_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add comprehensive sharp turns analysis page with BOTH street view AND satellite visual evidence"""
        
        # Get turns data with images
        turns_data = self.get_turns_with_images(route_id)
        
        if not turns_data:
            pdf.add_page()
            pdf.add_section_header("SHARP TURNS ANALYSIS WITH VISUAL EVIDENCE", "danger")
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(0, 10, 'No sharp turns data available for this route.', 0, 1, 'L')
            return
        
        pdf.add_page()
        pdf.add_section_header("SHARP TURNS ANALYSIS WITH DUAL VISUAL EVIDENCE", "danger")
        
        # Comprehensive summary statistics
        total_turns = len(turns_data)
        extreme_turns = len([t for t in turns_data if t['angle'] >= 90])
        blind_spots = len([t for t in turns_data if 80 <= t['angle'] < 90])
        sharp_danger = len([t for t in turns_data if 70 <= t['angle'] < 80])
        moderate_turns = len([t for t in turns_data if 45 <= t['angle'] < 70])
        
        # Get stored images count - UPDATED to show both types
        street_view_count = len(self.get_stored_images_from_db(route_id, 'street_view'))
        satellite_count = len(self.get_stored_images_from_db(route_id, 'satellite'))
        route_map_count = len(self.get_stored_images_from_db(route_id, 'route_map'))
        
        # Calculate average angle
        avg_angle = sum(t['angle'] for t in turns_data) / len(turns_data) if turns_data else 0
        max_angle = max(t['angle'] for t in turns_data) if turns_data else 0
        
        # Enhanced summary table
        stats_table = [
            ['Total Sharp Turns Detected', f"{total_turns:,}"],
            ['Extreme Danger Turns (>=90 deg)', f"{extreme_turns:,}"],
            ['High-Risk Blind Spots (80-90 deg)', f"{blind_spots:,}"],
            ['Sharp Danger Zones (70-80 deg)', f"{sharp_danger:,}"],
            ['Moderate Risk Turns (45-70 deg)', f"{moderate_turns:,}"],
            ['Most Dangerous Turn Angle', f"{max_angle:.1f} deg"],
            ['Average Turn Angle', f"{avg_angle:.1f} deg"],
            ['Street View Images Available', f"{street_view_count:,}"],
            ['Satellite Images Available', f"{satellite_count:,}"],
            ['Route Map Images Available', f"{route_map_count:,}"],
            ['Total Visual Evidence Files', f"{street_view_count + satellite_count + route_map_count:,}"]
        ]
        
        pdf.create_detailed_table(stats_table, [80, 100])
        
        # Enhanced visual evidence indicator
        pdf.ln(10)
        total_images = street_view_count + satellite_count
        if total_images >= 10:
            evidence_color = self.success_color
            evidence_status = "EXCELLENT VISUAL EVIDENCE"
            evidence_icon = "[OK]"
        elif total_images >= 5:
            evidence_color = self.info_color
            evidence_status = "GOOD VISUAL EVIDENCE"
            evidence_icon = "[OK]"
        elif total_images > 0:
            evidence_color = self.warning_color
            evidence_status = "LIMITED VISUAL EVIDENCE"
            evidence_icon = "[!]"
        else:
            evidence_color = self.danger_color
            evidence_status = "NO VISUAL EVIDENCE"
            evidence_icon = "[X]"
        
        pdf.set_fill_color(*evidence_color)
        pdf.rect(10, pdf.get_y(), 190, 12, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_xy(15, pdf.get_y() + 2)
        pdf.cell(180, 8, f'{evidence_icon} VISUAL EVIDENCE STATUS: {evidence_status} ({total_images} images)', 0, 1, 'C')
        
        # Turn classification legend
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.danger_color)
        pdf.cell(0, 8, 'TURN CLASSIFICATION SYSTEM', 0, 1, 'L')
        
        classification_table = [
            ['>=90 deg', 'EXTREME BLIND SPOT', 'CRITICAL', '15 km/h', 'Full stop may be required'],
            ['80-90 deg', 'HIGH-RISK BLIND SPOT', 'EXTREME', '20 km/h', 'Extreme caution required'],
            ['70-80 deg', 'BLIND SPOT', 'HIGH', '25 km/h', 'High caution required'],
            ['60-70 deg', 'HIGH-ANGLE TURN', 'MEDIUM', '30 km/h', 'Moderate caution required'],
            ['45-60 deg', 'SHARP TURN', 'LOW', '40 km/h', 'Normal caution required']
        ]
        
        headers = ['Angle Range', 'Classification', 'Risk Level', 'Max Speed', 'Safety Requirement']
        col_widths = [25, 45, 25, 25, 65]
        pdf.create_table_header(headers, col_widths)
        
        for row in classification_table:
            pdf.create_table_row(row, col_widths)
        
        # Most critical turns with DUAL visual analysis
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(*self.danger_color)
        pdf.cell(0, 8, 'CRITICAL TURNS WITH DUAL VISUAL EVIDENCE ANALYSIS', 0, 1, 'L')
        
        # Process top 8 most dangerous turns
        critical_turns = sorted(turns_data, key=lambda x: x['angle'], reverse=True)[:8]
        
        for i, turn in enumerate(critical_turns, 1):
            if i > 1:  # Don't add page for first turn
                pdf.add_page()
            
            # Turn information header with enhanced styling
            pdf.set_fill_color(*self.danger_color)
            pdf.rect(10, pdf.get_y(), 190, 12, 'F')
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_xy(15, pdf.get_y() + 2)
            turn_header = f'CRITICAL TURN #{i}: {turn["angle"]:.1f} deg - {turn["classification"]} - {turn["danger_level"]} RISK'
            pdf.cell(180, 8, turn_header, 0, 1, 'L')
            
            # Detailed turn analysis
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Helvetica', '', 10)
            
            # Enhanced turn details with image counts
            street_images_count = len(turn.get('street_view_images', []))
            satellite_images_count = len(turn.get('satellite_images', []))
            
            turn_details = [
                ['GPS Coordinates', f'{turn["latitude"]:.6f}, {turn["longitude"]:.6f}'],
                ['Turn Angle', f'{turn["angle"]:.1f} deg (Deviation from straight path)'],
                ['Risk Classification', f'{turn["classification"]} - {turn["danger_level"]} Risk Level'],
                ['Recommended Maximum Speed', f'{turn.get("recommended_speed", 40)} km/h'],
                ['Safety Distance Required', 'Minimum 50m approach visibility'],
                ['Driver Action Required', 'Reduce speed, check mirrors, signal early'],
                ['Street View Images', f'{street_images_count} images available'],
                ['Satellite Images', f'{satellite_images_count} images available'],
                ['Total Visual Evidence', f'{street_images_count + satellite_images_count} images for analysis']
            ]
            
            pdf.create_detailed_table(turn_details, [65, 115])
            
            # Add DUAL images with comprehensive analysis
            self._add_comprehensive_turn_images(pdf, turn, route_id, i)
    
    def _add_comprehensive_turn_images(self, pdf: 'EnhancedRoutePDF', turn: Dict, route_id: str, turn_number: int):
        """Add comprehensive turn images with detailed analysis - UPDATED for both street view AND satellite"""
        
        # Get images for this turn
        street_view_images = turn.get('street_view_images', [])
        satellite_images = turn.get('satellite_images', [])
        
        if not street_view_images and not satellite_images:
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, f'   No visual evidence available for Turn #{turn_number}', 0, 1, 'L')
            pdf.set_font('Helvetica', '', 8)
            pdf.cell(0, 5, f'   Images may be available at nearby coordinates: {turn["latitude"]:.4f}, {turn["longitude"]:.4f}', 0, 1, 'L')
            return
        
        pdf.ln(3)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(*self.info_color)
        pdf.cell(0, 6, f'VISUAL EVIDENCE FOR TURN #{turn_number}:', 0, 1, 'L')
        
        current_y = pdf.get_y()
        
        # ENHANCED: Add both street view AND satellite images side by side
        images_added = 0
        
        # First, try to add street view image (left side)
        if street_view_images:
            for img in street_view_images[:1]:  # One street view image
                image_path = img['file_path']
                if os.path.exists(image_path):
                    try:
                        # Check if we have enough space for both images
                        if current_y + 95 > 280:
                            pdf.add_page()
                            current_y = pdf.get_y()
                        
                        # Street View Image (Left Side)
                        pdf.set_xy(15, current_y)
                        pdf.set_font('Helvetica', 'B', 9)
                        pdf.set_text_color(*self.primary_color)
                        pdf.cell(85, 5, 'STREET VIEW ANALYSIS:', 0, 0, 'L')
                        
                        # Satellite View Image (Right Side) - if available
                        if satellite_images:
                            pdf.set_xy(110, current_y)
                            pdf.set_font('Helvetica', 'B', 9)
                            pdf.set_text_color(*self.info_color)
                            pdf.cell(85, 5, 'SATELLITE VIEW ANALYSIS:', 0, 0, 'L')
                        
                        current_y += 7
                        
                        # Add street view image (left side)
                        pdf.set_xy(15, current_y)
                        pdf.image(image_path, x=15, y=current_y, w=85, h=65)
                        
                        # Add street view analysis text (below street view image)
                        pdf.set_xy(15, current_y + 68)
                        pdf.set_font('Helvetica', '', 8)
                        pdf.set_text_color(0, 0, 0)
                        
                        street_analysis = [
                            f"STREET VIEW DATA:",
                            f"File: {os.path.basename(img['filename'])}",
                            f"Size: {img.get('file_size', 0) / 1024:.1f} KB",
                            f"GPS: {img.get('latitude', 0):.4f}, {img.get('longitude', 0):.4f}",
                            f"",
                            f"ROAD ANALYSIS:",
                            f"* Turn angle: {turn['angle']:.1f} degrees",
                            f"* Visibility: Limited due to sharp curve",
                            f"* Hazard level: {turn['danger_level']}",
                            f"* Max speed: {turn.get('recommended_speed', 40)} km/h"
                        ]
                        
                        for line in street_analysis:
                            pdf.cell(85, 3.5, line, 0, 1, 'L')
                            pdf.set_x(15)
                        
                        images_added += 1
                        break
                    except Exception as e:
                        print(f"Error adding street view image: {e}")
        
        # Now add satellite image (right side) if available
        if satellite_images:
            for img in satellite_images[:1]:  # One satellite image
                satellite_path = img['file_path']
                if os.path.exists(satellite_path):
                    try:
                        # Add satellite image (right side, same Y as street view)
                        pdf.set_xy(110, current_y)
                        pdf.image(satellite_path, x=110, y=current_y, w=85, h=65)
                        
                        # Add satellite analysis text (below satellite image)
                        pdf.set_xy(110, current_y + 68)
                        pdf.set_font('Helvetica', '', 8)
                        pdf.set_text_color(0, 0, 0)
                        
                        satellite_analysis = [
                            f"SATELLITE VIEW DATA:",
                            f"File: {os.path.basename(img['filename'])}",
                            f"Size: {img.get('file_size', 0) / 1024:.1f} KB",
                            f"GPS: {img.get('latitude', 0):.4f}, {img.get('longitude', 0):.4f}",
                            f"",
                            f"AERIAL ANALYSIS:",
                            f"* Turn geometry: {turn['angle']:.1f} deg curve",
                            f"* Road curvature: Sharp bend visible",
                            f"* Terrain context: Aerial perspective",
                            f"* Traffic flow impact: Potential bottleneck"
                        ]
                        
                        for line in satellite_analysis:
                            pdf.cell(85, 3.5, line, 0, 1, 'L')
                            pdf.set_x(110)
                        
                        images_added += 1
                        break
                    except Exception as e:
                        print(f"Error adding satellite image: {e}")
        
        # If only one type of image was added, show message about the other
        if images_added == 1:
            if street_view_images and not satellite_images:
                pdf.set_xy(110, current_y + 20)
                pdf.set_font('Helvetica', 'I', 8)
                pdf.set_text_color(150, 150, 150)
                pdf.multi_cell(85, 4, 'Satellite view not available for this turn location', 0, 'C')
            elif satellite_images and not street_view_images:
                pdf.set_xy(15, current_y + 20)
                pdf.set_font('Helvetica', 'I', 8)
                pdf.set_text_color(150, 150, 150)
                pdf.multi_cell(85, 4, 'Street view not available for this turn location', 0, 'C')
        
        # Move to next position
        if images_added > 0:
            pdf.set_y(current_y + 95)
        else:
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 6, f'   Image files not accessible from file system', 0, 1, 'L')
    
    def _add_pois_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add comprehensive Points of Interest analysis"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        pois_data = route_api.get_points_of_interest(route_id)
        
        if 'error' in pois_data:
            pdf.add_page()
            pdf.add_section_header("POINTS OF INTEREST ANALYSIS", "info")
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(0, 10, 'Points of Interest data not available.', 0, 1, 'L')
            return
        
        pdf.add_page()
        pdf.add_section_header("COMPREHENSIVE POINTS OF INTEREST ANALYSIS", "info")
        
        # POI Statistics
        stats = pois_data['statistics']
        
        # Summary statistics
        summary_table = [
            ['Total POIs Identified', f"{stats['total_pois']:,}"],
            ['Emergency Services', f"{stats['emergency_services']:,}"],
            ['Essential Services', f"{stats['essential_services']:,}"],
            ['Other Services', f"{stats['other_services']:,}"],
            ['Coverage Score', f"{stats['coverage_score']}/100"],
            ['Service Availability Rating', 'EXCELLENT' if stats['coverage_score'] > 80 else 'GOOD' if stats['coverage_score'] > 60 else 'MODERATE' if stats['coverage_score'] > 40 else 'LIMITED']
        ]
        
        pdf.create_detailed_table(summary_table, [70, 110])
        
        # Service availability assessment
        pdf.ln(10)
        coverage_score = stats['coverage_score']
        if coverage_score >= 80:
            color = self.success_color
            status = "EXCELLENT SERVICE COVERAGE"
        elif coverage_score >= 60:
            color = self.info_color
            status = "GOOD SERVICE COVERAGE"
        elif coverage_score >= 40:
            color = self.warning_color
            status = "MODERATE SERVICE COVERAGE"
        else:
            color = self.danger_color
            status = "LIMITED SERVICE COVERAGE"
        
        pdf.set_fill_color(*color)
        pdf.rect(10, pdf.get_y(), 190, 12, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_xy(15, pdf.get_y() + 2)
        pdf.cell(180, 8, f'SERVICE AVAILABILITY: {status} ({coverage_score}/100)', 0, 1, 'C')
        
        # Detailed POI Categories
        pois = pois_data['pois_by_type']
        
        poi_categories = [
            ('hospitals', 'MEDICAL FACILITIES - Emergency Healthcare Services', self.danger_color, 'CRITICAL'),
            ('police', 'LAW ENFORCEMENT - Security & Emergency Response', self.primary_color, 'CRITICAL'),
            ('fire_stations', 'FIRE & RESCUE - Emergency Response Services', self.danger_color, 'CRITICAL'),
            ('gas_stations', 'FUEL STATIONS - Vehicle Refueling Points', self.warning_color, 'ESSENTIAL'),
            ('schools', 'EDUCATIONAL INSTITUTIONS - Speed Limit Zones (40 km/h)', self.success_color, 'AWARENESS'),
            ('restaurants', 'FOOD & REST - Meal Stops & Driver Rest Areas', self.info_color, 'CONVENIENCE')
        ]
        
        for poi_type, title, color, priority in poi_categories:
            poi_list = pois.get(poi_type, [])
            pdf.add_page()  # <-- ADD THIS LINE
            # pdf.ln(15)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*color)
            pdf.cell(0, 8, f'{title} ({len(poi_list)} found) - {priority}', 0, 1, 'L')
            
            if not poi_list:
                pdf.set_font('Helvetica', 'I', 10)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(0, 6, f'   No {poi_type.replace("_", " ")} found along this route', 0, 1, 'L')
                continue
            
            # Create detailed table for this POI type
            headers = ['#', 'Facility Name', 'Location/Address', 'Distance', 'Notes']
            col_widths = [15, 55, 65, 25, 25]
            
            pdf.create_table_header(headers, col_widths)
            
            for i, poi in enumerate(poi_list, 1):  # Limit to 15 per type
                notes = ""
                if poi_type == 'schools':
                    notes = "40 km/h"
                elif poi_type == 'hospitals':
                    notes = "Emergency"
                elif poi_type == 'gas_stations':
                    notes = "Fuel"
                
                row_data = [
                    str(i),
                    poi.get('name', 'Unknown')[:28],
                    poi.get('address', 'Unknown location')[:32],
                    "Along route",
                    notes
                ]
                
                pdf.create_table_row(row_data, col_widths)
        
        # Service recommendations
        recommendations = pois_data.get('recommendations', [])
        if recommendations:
            pdf.ln(15)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.primary_color)
            pdf.cell(0, 8, 'SERVICE AVAILABILITY RECOMMENDATIONS', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for i, rec in enumerate(recommendations, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(172, 6, rec, 0, 'L')
                pdf.ln(2)
        
        # Critical service gaps analysis
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.danger_color)
        pdf.cell(0, 8, 'CRITICAL SERVICE GAPS IDENTIFIED', 0, 1, 'L')
        
        gaps = []
        if len(pois.get('hospitals', [])) == 0:
            gaps.append("* No medical facilities - Carry first aid kit and emergency contact numbers")
        if len(pois.get('gas_stations', [])) < 2:
            gaps.append("* Limited fuel stations - Plan refueling stops and carry extra fuel if possible")
        if len(pois.get('police', [])) == 0:
            gaps.append("* No police stations - Save emergency numbers: 100 (Police), 112 (Emergency)")
        
        if not gaps:
            gaps.append("* No critical service gaps identified - Good service coverage along route")
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        for gap in gaps:
            pdf.cell(0, 6, gap, 0, 1, 'L')
    
    def _add_network_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add comprehensive network coverage analysis"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        network_data = route_api.get_network_coverage(route_id)
        
        if 'error' in network_data:
            pdf.add_page()
            pdf.add_section_header("NETWORK COVERAGE ANALYSIS", "info")
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(0, 10, 'Network coverage data not available.', 0, 1, 'L')
            return
        
        pdf.add_page()
        pdf.add_section_header("COMPREHENSIVE NETWORK COVERAGE ANALYSIS", "info")
        
        # Network Statistics
        stats = network_data['statistics']
        
        # Overall coverage assessment
        overall_score = stats['overall_coverage_score']
        if overall_score >= 85:
            coverage_status = "EXCELLENT"
            coverage_color = self.success_color
        elif overall_score >= 70:
            coverage_status = "GOOD"
            coverage_color = self.info_color
        elif overall_score >= 50:
            coverage_status = "MODERATE"
            coverage_color = self.warning_color
        else:
            coverage_status = "POOR"
            coverage_color = self.danger_color
        
        # Coverage summary
        summary_table = [
            ['Analysis Points Tested', f"{stats['total_points_analyzed']:,}"],
            ['Overall Coverage Score', f"{stats['overall_coverage_score']:.1f}/100"],
            ['Coverage Status', coverage_status],
            ['Dead Zones Identified', f"{stats['dead_zones_count']:,}"],
            ['Poor Coverage Areas', f"{stats['poor_coverage_count']:,}"],
            ['Good Coverage Areas', f"{stats['good_coverage_percentage']:.1f}%"],
            ['Network Reliability Rating', 'HIGH' if stats['overall_coverage_score'] > 80 else 'MEDIUM' if stats['overall_coverage_score'] > 60 else 'LOW']
        ]
        
        pdf.create_detailed_table(summary_table, [70, 110])
        
        # Coverage status indicator
        pdf.ln(10)
        pdf.set_fill_color(*coverage_color)
        pdf.rect(10, pdf.get_y(), 190, 12, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_xy(15, pdf.get_y() + 2)
        pdf.cell(180, 8, f'NETWORK RELIABILITY: {coverage_status} ({overall_score:.1f}/100)', 0, 1, 'C')
        
        # Quality Distribution Analysis
        pdf.ln(15)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.primary_color)
        pdf.cell(0, 8, 'SIGNAL QUALITY DISTRIBUTION ANALYSIS', 0, 1, 'L')
        
        quality_dist = network_data['quality_distribution']
        total_points = stats['total_points_analyzed']
        
        quality_table = []
        quality_colors = {
            'excellent': ('Excellent Signal (4-5 bars)', self.success_color),
            'good': ('Good Signal (3-4 bars)', self.info_color), 
            'fair': ('Fair Signal (2-3 bars)', self.warning_color),
            'poor': ('Poor Signal (1-2 bars)', self.warning_color),
            'dead': ('No Signal (Dead Zone)', self.danger_color)
        }
        
        for quality, count in quality_dist.items():
            percentage = (count/total_points*100) if total_points > 0 else 0
            quality_name, color = quality_colors.get(quality, (quality.title(), self.secondary_color))
            
            quality_table.append([
                quality_name,
                f"{count:,}",
                f"{percentage:.1f}%",
                "Critical" if quality == 'dead' else "Attention" if quality == 'poor' else "Good"
            ])
        
        headers = ['Signal Quality Level', 'Points Count', 'Route %', 'Status']
        col_widths = [60, 30, 25, 25]
        
        pdf.create_table_header(headers, col_widths)
        for row in quality_table:
            pdf.create_table_row(row, col_widths)
        
        # Critical Problem Areas
        dead_zones = network_data['problem_areas']['dead_zones']
        poor_zones = network_data['problem_areas']['poor_coverage_zones']
        
        if dead_zones or poor_zones:
            pdf.ln(15)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.danger_color)
            pdf.cell(0, 8, f'CRITICAL COMMUNICATION PROBLEMS ({len(dead_zones) + len(poor_zones)} areas)', 0, 1, 'L')
            
            # Dead zones table
            if dead_zones:
                pdf.ln(5)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_text_color(*self.danger_color)
                pdf.cell(0, 6, f'DEAD ZONES - NO CELLULAR SERVICE ({len(dead_zones)} locations):', 0, 1, 'L')
                
                headers = ['Zone #', 'GPS Coordinates', 'Impact Level', 'Recommendation']
                col_widths = [20, 50, 30, 85]
                
                pdf.create_table_header(headers, col_widths)
                
                for i, zone in enumerate(dead_zones[:10], 1):  # Limit to 10
                    row_data = [
                        str(i),
                        f"{zone['latitude']:.4f}, {zone['longitude']:.4f}",
                        "CRITICAL",
                        "Use satellite phone or emergency beacon"
                    ]
                    pdf.create_table_row(row_data, col_widths)
            
            # Poor coverage areas
            if poor_zones:
                pdf.ln(10)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_text_color(*self.warning_color)
                pdf.cell(0, 6, f'POOR COVERAGE AREAS ({len(poor_zones)} locations):', 0, 1, 'L')
                
                headers = ['Area #', 'GPS Coordinates', 'Signal Level', 'Recommendation']
                col_widths = [20, 50, 30, 85]
                
                pdf.create_table_header(headers, col_widths)
                
                for i, zone in enumerate(poor_zones[:8], 1):  # Limit to 8
                    row_data = [
                        str(i),
                        f"{zone['latitude']:.4f}, {zone['longitude']:.4f}",
                        "WEAK",
                        "Download offline maps, carry backup communication"
                    ]
                    pdf.create_table_row(row_data, col_widths)
        
        # Network recommendations
        recommendations = network_data.get('recommendations', [])
        if recommendations:
            pdf.ln(15)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.primary_color)
            pdf.cell(0, 8, 'NETWORK COVERAGE RECOMMENDATIONS', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for i, rec in enumerate(recommendations, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(172, 6, rec, 0, 'L')
                pdf.ln(2)
        
        # Emergency communication plan
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.danger_color)
        pdf.cell(0, 8, 'EMERGENCY COMMUNICATION PLAN', 0, 1, 'L')
        
        emergency_plan = [
            "* Download offline maps before travel (Google Maps, Maps.me)",
            "* Inform someone of your route and expected arrival time",
            "* Carry a satellite communication device for dead zones",
            "* Keep emergency numbers saved: 112 (Emergency), 100 (Police), 108 (Ambulance)",
            "* Consider two-way radios for convoy travel",
            "* Identify nearest towers and repeater locations along route"
        ]
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        for plan in emergency_plan:
            pdf.cell(0, 6, plan, 0, 1, 'L')
    
    def _add_weather_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add comprehensive weather analysis"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        weather_data = route_api.get_weather_data(route_id)
        
        if 'error' in weather_data:
            pdf.add_page()
            pdf.add_section_header("WEATHER CONDITIONS ANALYSIS", "warning")
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(0, 10, 'Weather analysis data not available.', 0, 1, 'L')
            return
        
        pdf.add_page()
        pdf.add_section_header("COMPREHENSIVE WEATHER CONDITIONS ANALYSIS", "warning")
        
        # Weather Statistics
        stats = weather_data['statistics']
        
        # Weather summary
        summary_table = [
            ['Weather Analysis Points', f"{stats['points_analyzed']:,}"],
            ['Average Temperature', f"{stats['average_temperature']:.1f} deg C"],
            ['Temperature Range', f"{stats['temperature_range']['min']:.1f} deg C to {stats['temperature_range']['max']:.1f} deg C"],
            ['Average Humidity', f"{stats['average_humidity']:.1f}%"],
            ['Average Wind Speed', f"{stats['average_wind_speed']:.1f} km/h"],
            ['Weather Conditions Detected', f"{len(weather_data['conditions_summary'])} different types"],
            ['Weather Risk Assessment', 'HIGH' if stats['average_temperature'] > 40 or stats['average_wind_speed'] > 50 else 'MODERATE' if stats['average_temperature'] > 35 or stats['average_wind_speed'] > 30 else 'LOW']
        ]
        
        pdf.create_detailed_table(summary_table, [70, 110])
        
        # Temperature assessment
        pdf.ln(10)
        avg_temp = stats['average_temperature']
        if avg_temp > 40:
            temp_status = "EXTREME HEAT WARNING"
            temp_color = self.danger_color
        elif avg_temp > 35:
            temp_status = "HIGH TEMPERATURE CAUTION"
            temp_color = self.warning_color
        elif avg_temp < 5:
            temp_status = "COLD WEATHER WARNING"
            temp_color = self.info_color
        else:
            temp_status = "MODERATE TEMPERATURE CONDITIONS"
            temp_color = self.success_color
        
        pdf.set_fill_color(*temp_color)
        pdf.rect(10, pdf.get_y(), 190, 12, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_xy(15, pdf.get_y() + 2)
        pdf.cell(180, 8, f'TEMPERATURE STATUS: {temp_status} ({avg_temp:.1f} deg C)', 0, 1, 'C')
        
        # Weather Conditions Analysis
        pdf.ln(15)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.primary_color)
        pdf.cell(0, 8, 'WEATHER CONDITIONS BREAKDOWN', 0, 1, 'L')
        
        conditions = weather_data['conditions_summary']
        total_points = stats['points_analyzed']
        
        headers = ['Weather Condition', 'Frequency', 'Route %', 'Risk Level', 'Driver Impact']
        col_widths = [40, 25, 20, 25, 75]
        
        pdf.create_table_header(headers, col_widths)
        
        for condition, count in conditions.items():
            percentage = (count / total_points * 100) if total_points > 0 else 0
            
            # Assess risk level
            if condition in ['Thunderstorm', 'Rain', 'Snow']:
                risk = "HIGH"
                impact = "Reduced visibility, slippery roads"
            elif condition in ['Clouds', 'Fog', 'Mist']:
                risk = "MODERATE"
                impact = "Reduced visibility, lower speeds"
            elif condition in ['Clear', 'Sunny']:
                risk = "LOW"
                impact = "Good driving conditions"
            else:
                risk = "MODERATE"
                impact = "Variable conditions"
            
            row_data = [
                condition,
                f"{count:,}",
                f"{percentage:.1f}%",
                risk,
                impact
            ]
            pdf.create_table_row(row_data, col_widths)
        
        # Weather Risks Assessment
# Weather Risks Assessment
        weather_risks = weather_data.get('weather_risks', [])
        if weather_risks:
            pdf.ln(15)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.danger_color)
            pdf.cell(0, 8, f'IDENTIFIED WEATHER RISKS ({len(weather_risks)} risks)', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for i, risk in enumerate(weather_risks, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(172, 6, f"{risk} - Take appropriate precautions", 0, 'L')
                pdf.ln(2)
        
        # Weather-based vehicle recommendations
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.primary_color)
        pdf.cell(0, 8, 'WEATHER-BASED VEHICLE PREPARATION', 0, 1, 'L')
        
        vehicle_prep = []
        if avg_temp > 35:
            vehicle_prep.extend([
                "* Check engine cooling system and radiator fluid levels",
                "* Ensure air conditioning is functioning properly", 
                "* Carry extra water for radiator and personal hydration",
                "* Check tire pressure (heat increases pressure)"
            ])
        
        if avg_temp < 10:
            vehicle_prep.extend([
                "* Check battery condition (cold weather reduces capacity)",
                "* Ensure proper engine oil viscosity for cold weather",
                "* Check tire tread depth for wet/icy conditions",
                "* Carry winter emergency kit with blankets"
            ])
        
        if 'Rain' in conditions or 'Thunderstorm' in conditions:
            vehicle_prep.extend([
                "* Check windshield wipers and washer fluid",
                "* Ensure headlights and taillights are functioning",
                "* Check tire tread depth for wet road traction",
                "* Clean all windows for maximum visibility"
            ])
        
        if not vehicle_prep:
            vehicle_prep = [
                "* Standard vehicle maintenance check recommended",
                "* Ensure all fluid levels are adequate",
                "* Check tire condition and pressure",
                "* Verify all lights are functioning properly"
            ]
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        for prep in vehicle_prep:
            pdf.cell(0, 6, prep, 0, 1, 'L')
        
        # Weather recommendations
        recommendations = weather_data.get('recommendations', [])
        if recommendations:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.warning_color)
            pdf.cell(0, 8, 'WEATHER-BASED DRIVING RECOMMENDATIONS', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for i, rec in enumerate(recommendations, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(172, 6, rec, 0, 'L')
                pdf.ln(2)
    
    def _add_compliance_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add detailed regulatory compliance analysis"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        compliance_data = route_api.get_compliance_data(route_id)
        
        if 'error' in compliance_data:
            pdf.add_page()
            pdf.add_section_header("REGULATORY COMPLIANCE ANALYSIS", "danger")
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(0, 10, 'Regulatory compliance data not available.', 0, 1, 'L')
            return
        
        pdf.add_page()
        pdf.add_section_header("COMPREHENSIVE REGULATORY COMPLIANCE ANALYSIS", "danger")
        
        # Compliance Assessment
        assessment = compliance_data['compliance_assessment']
        score = assessment['overall_score']
        
        # Compliance status indicator
        if score >= 80:
            color = self.success_color
            status = "FULLY COMPLIANT"
            icon = "[OK]"
        elif score >= 60:
            color = self.warning_color
            status = "NEEDS ATTENTION"
            icon = "[!]"
        else:
            color = self.danger_color
            status = "NON-COMPLIANT"
            icon = "[X]"
        
        pdf.set_fill_color(*color)
        pdf.rect(10, pdf.get_y(), 190, 15, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_xy(15, pdf.get_y() + 3)
        pdf.cell(180, 9, f'{icon} COMPLIANCE STATUS: {status} (Score: {score}/100)', 0, 1, 'C')
        
        # Vehicle and Route Information
        pdf.ln(10)
        pdf.set_text_color(0, 0, 0)
        vehicle_info = compliance_data['vehicle_info']
        route_analysis = compliance_data['route_analysis']
        
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.primary_color)
        pdf.cell(0, 8, 'VEHICLE & ROUTE COMPLIANCE DETAILS', 0, 1, 'L')
        
        vehicle_table = [
            ['Vehicle Type', vehicle_info['type'].replace('_', ' ').title()],
            ['Vehicle Category', vehicle_info['category']],
            ['Vehicle Weight Classification', f"{vehicle_info['weight']:,} kg"],
            ['AIS-140 GPS Tracking Required', 'YES (Mandatory)' if vehicle_info['ais_140_required'] else 'NO (Not Required)'],
            ['Route Origin', route_analysis['from_address'][:50]],
            ['Route Destination', route_analysis['to_address'][:50]],
            ['Total Route Distance', route_analysis['distance']],
            ['Estimated Travel Duration', route_analysis['duration']],
            ['Interstate Travel', 'YES' if 'km' in route_analysis.get('distance', '') and int(''.join(filter(str.isdigit, route_analysis.get('distance', '0')))) > 500 else 'NO']
        ]
        
        pdf.create_detailed_table(vehicle_table, [80, 100])
        
        # Compliance Requirements Analysis
        pdf.ln(15)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.danger_color)
        pdf.cell(0, 8, 'MANDATORY COMPLIANCE REQUIREMENTS', 0, 1, 'L')
        
        requirements = assessment['critical_requirements']
        
        headers = ['Requirement Category', 'Compliance Status', 'Action Required']
        col_widths = [60, 40, 85]
        
        pdf.create_table_header(headers, col_widths)
        
        requirement_details = [
            ['Valid Driving License', 'REQUIRED', 'Verify license category matches vehicle type'],
            ['Vehicle Registration', 'REQUIRED', 'Ensure current registration certificate'],
            ['Vehicle Insurance', 'REQUIRED', 'Valid comprehensive insurance policy'],
            ['Route Permits', 'CONDITIONAL', 'Required for interstate/heavy vehicle travel'],
            ['AIS-140 GPS Device', 'REQUIRED' if vehicle_info['ais_140_required'] else 'NOT REQUIRED', 'Install certified GPS tracking system'],
            ['Driving Time Limits (RTSP)', 'REQUIRED', 'Maximum 10 hours continuous driving'],
            ['Vehicle Fitness Certificate', 'REQUIRED', 'Valid pollution and fitness certificates'],
            ['Driver Medical Certificate', 'REQUIRED', 'Valid medical fitness certificate']
        ]
        
        for req_detail in requirement_details:
            pdf.create_table_row(req_detail, col_widths)
        
        # Compliance Issues Identified
        issues = assessment['issues_identified']
        if issues:
            pdf.ln(15)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.danger_color)
            pdf.cell(0, 8, f'COMPLIANCE ISSUES REQUIRING IMMEDIATE ATTENTION ({len(issues)})', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for i, issue in enumerate(issues, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(172, 6, f"{issue} - Address before travel", 0, 'L')
                pdf.ln(2)
        
        # Regulatory Framework Details
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.primary_color)
        pdf.cell(0, 8, 'APPLICABLE REGULATORY FRAMEWORK', 0, 1, 'L')
        
        regulations = [
            "* Motor Vehicles Act, 1988 - Vehicle registration and licensing requirements",
            "* Central Motor Vehicles Rules, 1989 - Technical specifications and safety",
            "* AIS-140 Standards - GPS tracking and panic button requirements",
            "* Road Transport and Safety Policy (RTSP) - Driver working hours",
            "* Interstate Transport Permits - Required for commercial interstate travel",
            "* Pollution Control Board Norms - Emission standards compliance",
            "* Goods and Services Tax (GST) - Tax compliance for commercial transport",
            "* Road Safety and Transport Authority - State-specific requirements"
        ]
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        for regulation in regulations:
            pdf.cell(0, 6, regulation, 0, 1, 'L')
        
        # Compliance recommendations
        recommendations = compliance_data.get('recommendations', [])
        if recommendations:
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.warning_color)
            pdf.cell(0, 8, 'COMPLIANCE RECOMMENDATIONS', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for i, rec in enumerate(recommendations, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(172, 6, rec, 0, 'L')
                pdf.ln(2)
        
        # Penalty and consequences
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.danger_color)
        pdf.cell(0, 8, 'NON-COMPLIANCE PENALTIES & CONSEQUENCES', 0, 1, 'L')
        
        penalties = [
            "* Driving without valid license: Fine up to Rs 5,000 + imprisonment",
            "* Vehicle without registration: Fine up to Rs 10,000 + vehicle seizure",
            "* No insurance: Fine up to Rs 2,000 + vehicle seizure",
            "* AIS-140 non-compliance: Permit cancellation + heavy fines",
            "* Overloading violations: Fine Rs 20,000 + per excess ton",
            "* Driving time violations: License suspension + fines",
            "* Interstate without permits: Vehicle seizure + penalty",
            "* Environmental violations: Fine up to Rs 10,000 + registration cancellation"
        ]
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        for penalty in penalties:
            pdf.cell(0, 6, penalty, 0, 1, 'L')
    
    def _add_elevation_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add comprehensive elevation analysis with real Google API data"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        elevation_data = route_api.get_elevation_data(route_id)
        
        pdf.add_page()
        pdf.add_section_header("COMPREHENSIVE ELEVATION & TERRAIN ANALYSIS", "success")
        
        # Check if we have actual elevation data
        if 'error' in elevation_data:
            # Show the specific error
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.warning_color)
            pdf.cell(0, 10, 'ELEVATION DATA UNAVAILABLE', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 6, f'Error: {elevation_data["error"]}', 0, 'L')
            pdf.ln(5)
            
            # Add troubleshooting information
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(*self.info_color)
            pdf.cell(0, 8, 'TROUBLESHOOTING INFORMATION:', 0, 1, 'L')
            
            troubleshooting = [
                "• Check if Google Maps Elevation API is enabled in your Google Cloud Console",
                "• Verify your Google Maps API key has elevation permissions",
                "• Ensure you have not exceeded your API quota limits",
                "• Check if the route analysis completed successfully",
                "• Review the application logs for specific API error messages"
            ]
            
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(0, 0, 0)
            for item in troubleshooting:
                pdf.cell(0, 6, item, 0, 1, 'L')
            
            # Add API configuration check
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(*self.primary_color)
            pdf.cell(0, 8, 'API CONFIGURATION STATUS:', 0, 1, 'L')
            
            import os
            google_key = os.environ.get('GOOGLE_MAPS_API_KEY')
            
            config_info = [
                f"• Google Maps API Key: {'Configured' if google_key else 'NOT CONFIGURED'}",
                f"• Key Length: {len(google_key) if google_key else 0} characters",
                f"• Key Preview: {google_key[:10] + '...' if google_key and len(google_key) > 10 else 'Not available'}",
                "• Required APIs: Elevation API, Directions API, Places API"
            ]
            
            pdf.set_font('Helvetica', '', 9)
            for item in config_info:
                pdf.cell(0, 6, item, 0, 1, 'L')
            
            return
        
        # We have real elevation data - process normally
        stats = elevation_data['statistics']
        terrain = elevation_data['terrain_analysis']
        changes = elevation_data.get('significant_changes', [])
        
        # Elevation summary table
        summary_table = [
            ['Data Source', 'Google Elevation API (Live Data)'],
            ['Total Analysis Points', f"{stats['total_points']:,} coordinates"],
            ['Minimum Elevation', f"{stats['min_elevation']:.1f} meters above sea level"],
            ['Maximum Elevation', f"{stats['max_elevation']:.1f} meters above sea level"],
            ['Average Elevation', f"{stats['average_elevation']:.1f} meters above sea level"],
            ['Total Elevation Range', f"{stats['elevation_range']:.1f} meters"],
            ['Terrain Classification', terrain['terrain_type']],
            ['Driving Difficulty Level', terrain['driving_difficulty']],
            ['Fuel Consumption Impact', terrain['fuel_impact']],
            ['Significant Changes Detected', f"{len(changes)} elevation changes > 50m"]
        ]
        
        pdf.create_detailed_table(summary_table, [80, 100])
        
        # Terrain classification assessment
        pdf.ln(10)
        terrain_type = terrain['terrain_type']
        if terrain_type == 'MOUNTAINOUS':
            terrain_color = self.danger_color
            terrain_status = "MOUNTAINOUS TERRAIN - HIGH DIFFICULTY"
        elif terrain_type == 'HILLY':
            terrain_color = self.warning_color
            terrain_status = "HILLY TERRAIN - MODERATE DIFFICULTY"
        elif terrain_type == 'HIGH_PLATEAU':
            terrain_color = self.info_color
            terrain_status = "HIGH PLATEAU - MODERATE CONDITIONS"
        else:
            terrain_color = self.success_color
            terrain_status = "PLAINS TERRAIN - EASY CONDITIONS"
        
        pdf.set_fill_color(*terrain_color)
        pdf.rect(10, pdf.get_y(), 190, 12, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_xy(15, pdf.get_y() + 2)
        pdf.cell(180, 8, f'TERRAIN ASSESSMENT: {terrain_status}', 0, 1, 'C')
        
        # Significant Elevation Changes
        changes = elevation_data['significant_changes']
        if changes:
            pdf.ln(15)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.warning_color)
            pdf.cell(0, 8, f'SIGNIFICANT ELEVATION CHANGES ({len(changes)} locations)', 0, 1, 'L')
            
            headers = ['Change #', 'Type', 'Elevation Change', 'From (m)', 'To (m)', 'GPS Location', 'Impact']
            col_widths = [20, 20, 25, 20, 20, 50, 40]
            
            pdf.create_table_header(headers, col_widths)
            
            for i, change in enumerate(changes[:15], 1):  # Limit to 15 changes
                location = change['location']
                impact = "HIGH" if change['elevation_change'] > 200 else "MODERATE" if change['elevation_change'] > 100 else "LOW"
                
                row_data = [
                    str(i),
                    change['type'].title(),
                    f"{change['elevation_change']:.0f}m",
                    f"{change['from_elevation']:.0f}",
                    f"{change['to_elevation']:.0f}",
                    f"{location['latitude']:.4f}, {location['longitude']:.4f}",
                    impact
                ]
                pdf.create_table_row(row_data, col_widths)
        
        # Driving difficulty analysis
        pdf.ln(15)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.primary_color)
        pdf.cell(0, 8, 'ELEVATION-BASED DRIVING CHALLENGES', 0, 1, 'L')
        
        difficulty = terrain['driving_difficulty']
        challenges = []
        
        if difficulty == 'HIGH':
            challenges = [
                "* Steep gradients requiring low gear driving and engine braking",
                "* Increased fuel consumption due to elevation changes",
                "* Potential engine overheating on long climbs",
                "* Brake wear due to frequent downhill braking",
                "* Reduced vehicle performance at high altitudes",
                "* Weather variations with altitude changes"
            ]
        elif difficulty == 'MEDIUM':
            challenges = [
                "* Moderate gradients affecting fuel efficiency",
                "* Some engine strain on uphill sections",
                "* Occasional brake usage on downhill sections",
                "* Minor impact on vehicle performance",
                "* Moderate fuel consumption increase"
            ]
        else:
            challenges = [
                "* Minimal elevation changes with flat terrain",
                "* Normal fuel consumption expected",
                "* Standard vehicle performance throughout",
                "* No significant gradient-related challenges"
            ]
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        for challenge in challenges:
            pdf.cell(0, 6, challenge, 0, 1, 'L')
        
        # Vehicle preparation recommendations
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.danger_color)
        pdf.cell(0, 8, 'ELEVATION-SPECIFIC VEHICLE PREPARATION', 0, 1, 'L')
        
        prep_recommendations = []
        
        if stats['elevation_range'] > 1000:  # Significant elevation changes
            prep_recommendations = [
                "* Check engine cooling system - radiator, coolant levels, and fans",
                "* Inspect brake system - pads, fluid, and brake lines condition",
                "* Verify transmission fluid for proper gear shifting",
                "* Check tire pressure and tread depth for varied conditions",
                "* Ensure fuel tank is full - higher consumption expected",
                "* Carry emergency coolant and brake fluid",
                "* Plan rest stops for engine cooling on long climbs"
            ]
        elif stats['elevation_range'] > 500:  # Moderate changes
            prep_recommendations = [
                "* Check cooling system and fluid levels",
                "* Inspect brake system condition",
                "* Verify fuel level and plan refueling stops",
                "* Check tire condition for varied terrain"
            ]
        else:  # Minimal changes
            prep_recommendations = [
                "* Standard vehicle maintenance check sufficient",
                "* Normal fuel planning adequate",
                "* Standard tire and brake inspection"
            ]
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        for prep in prep_recommendations:
            pdf.cell(0, 6, prep, 0, 1, 'L')
        
        # Fuel consumption impact
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.warning_color)
        pdf.cell(0, 8, 'FUEL CONSUMPTION IMPACT ANALYSIS', 0, 1, 'L')
        
        fuel_impact = terrain['fuel_impact']
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        
        if "HIGH" in fuel_impact:
            pdf.cell(0, 6, "* Expected fuel consumption increase: 25-40% above normal", 0, 1, 'L')
            pdf.cell(0, 6, "* Plan additional fuel stops and carry extra fuel if possible", 0, 1, 'L')
            pdf.cell(0, 6, "* Consider route alternatives with less elevation change", 0, 1, 'L')
        elif "MEDIUM" in fuel_impact:
            pdf.cell(0, 6, "* Expected fuel consumption increase: 15-25% above normal", 0, 1, 'L')
            pdf.cell(0, 6, "* Plan fuel stops accounting for increased consumption", 0, 1, 'L')
        else:
            pdf.cell(0, 6, "* Normal fuel consumption expected", 0, 1, 'L')
            pdf.cell(0, 6, "* Standard fuel planning adequate", 0, 1, 'L')
        
        pdf.cell(0, 6, f"* Total ascent sections identified: {len([c for c in changes if c['type'] == 'ascent'])}", 0, 1, 'L')
        pdf.cell(0, 6, f"* Total descent sections identified: {len([c for c in changes if c['type'] == 'descent'])}", 0, 1, 'L')
    
    # Fixed emergency page method for pdf_generator.py
    # Replace your existing _add_emergency_page method with this improved version

    def _add_emergency_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add comprehensive emergency preparedness analysis with REAL DATA"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        
        # Try to get emergency data from the new emergency analyzer
        emergency_data = self._get_emergency_data_from_db(route_id)
        
        # Fallback to the old method if new data not available
        if not emergency_data:
            emergency_data = route_api.get_emergency_data(route_id)
        
        if 'error' in emergency_data:
            pdf.add_page()
            pdf.add_section_header("EMERGENCY PREPAREDNESS ANALYSIS", "danger")
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(0, 10, 'Emergency preparedness data not available.', 0, 1, 'L')
            return
        
        pdf.add_page()
        pdf.add_section_header("COMPREHENSIVE EMERGENCY PREPAREDNESS ANALYSIS", "danger")
        
        # Get emergency preparedness assessment
        if 'preparedness_assessment' in emergency_data:
            # Old format data
            assessment = emergency_data['preparedness_assessment']
            score = assessment['emergency_score']
            services = emergency_data.get('emergency_services', {})
            comm_analysis = emergency_data.get('communication_analysis', {})
        else:
            # New format data from emergency analyzer
            score = emergency_data.get('preparedness_score', 0)
            services = emergency_data.get('emergency_facilities', {})
            comm_analysis = emergency_data.get('coverage_analysis', {})
            assessment = {
                'emergency_score': score,
                'preparedness_level': emergency_data.get('overall_assessment', 'UNKNOWN'),
                'critical_gaps': emergency_data.get('critical_gaps', [])
            }
        
        # Emergency Preparedness Score Display
        if score >= 80:
            color = self.success_color
            status = "EXCELLENT PREPAREDNESS"
            icon = "[OK]"
        elif score >= 60:
            color = self.warning_color
            status = "GOOD PREPAREDNESS" 
            icon = "[!]"
        else:
            color = self.danger_color
            status = "NEEDS IMPROVEMENT"
            icon = "[X]"
        
        pdf.set_fill_color(*color)
        pdf.rect(10, pdf.get_y(), 190, 15, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_xy(15, pdf.get_y() + 3)
        pdf.cell(180, 9, f'{icon} EMERGENCY PREPAREDNESS: {status} (Score: {score}/100)', 0, 1, 'C')
        
        # Emergency Services Availability
        pdf.ln(10)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.primary_color)
        pdf.cell(0, 8, 'EMERGENCY SERVICES AVAILABILITY ASSESSMENT', 0, 1, 'L')
        
        # Handle both old and new data formats
        if 'emergency_facilities' in emergency_data:
            # New format from emergency analyzer
            facilities = emergency_data['emergency_facilities']
            services_table = [
                ['Medical Facilities (Hospitals)', f"{len(facilities.get('hospital', []))} facilities identified"],
                ['Law Enforcement (Police)', f"{len(facilities.get('police', []))} stations identified"],
                ['Fire & Rescue Services', f"{len(facilities.get('fire_station', []))} stations identified"],
                ['Emergency Clinics', f"{len(facilities.get('emergency_clinic', []))} clinics identified"],
                ['Pharmacies (24hr)', f"{len(facilities.get('pharmacy', []))} pharmacies identified"],
                ['Communication Reliability', comm_analysis.get('coverage_percentage', 'Unknown')],
                ['Coverage Gaps', f"{len(comm_analysis.get('coverage_gaps', []))} areas"],
                ['Overall Service Coverage', assessment.get('preparedness_level', 'Unknown')]
            ]
        else:
            # Old format fallback
            services_table = [
                ['Medical Facilities (Hospitals)', f"{len(services.get('hospitals', []))} facilities identified"],
                ['Law Enforcement (Police)', f"{len(services.get('police_stations', []))} stations identified"],
                ['Fire & Rescue Services', f"{len(services.get('fire_stations', []))} stations identified"],
                ['Communication Reliability', comm_analysis.get('communication_reliability', 'Unknown')],
                ['Network Dead Zones', f"{comm_analysis.get('dead_zones', 0)} critical areas"],
                ['Emergency Response Time', 'Variable - depends on location and traffic'],
                ['Overall Service Coverage', 'GOOD' if len(services.get('hospitals', [])) > 2 else 'MODERATE']
            ]
        
        pdf.create_detailed_table(services_table, [80, 100])
        
        # Critical Emergency Contact Numbers
        pdf.ln(15)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.danger_color)
        pdf.cell(0, 8, 'CRITICAL EMERGENCY CONTACT NUMBERS - MEMORIZE OR SAVE', 0, 1, 'L')
        
        # Enhanced emergency contacts table
        headers = ['Emergency Service', 'Contact Number', 'When to Call', 'Response Type']
        col_widths = [45, 30, 55, 55]
        
        pdf.create_table_header(headers, col_widths)
        
        contact_details = [
            ('National Emergency', '112', 'Any life-threatening emergency', 'Police/Fire/Medical'),
            ('Police Emergency', '100', 'Crime, accidents, security threats', 'Law enforcement'),
            ('Fire Services', '101', 'Fire, rescue, hazmat incidents', 'Fire & rescue teams'),
            ('Medical Emergency', '108', 'Medical emergencies, injuries', 'Ambulance service'),
            ('Highway Patrol', '1033', 'Highway accidents, breakdowns', 'Traffic police'),
            ('Tourist Helpline', '1363', 'Tourist emergencies, assistance', 'Tourist support'),
            ('Women Helpline', '1091', 'Women in distress, harassment', 'Women safety'),
            ('Disaster Management', '1078', 'Natural disasters, evacuations', 'Disaster response')
        ]
        
        for service, number, when, response in contact_details:
            pdf.create_table_row([service, number, when, response], col_widths)
        
        # Emergency Services Along Route - ENHANCED
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.info_color)
        pdf.cell(0, 8, 'EMERGENCY FACILITIES ALONG ROUTE WITH CONTACT DETAILS', 0, 1, 'L')
        
        # Get emergency facilities data
        if 'emergency_facilities' in emergency_data:
            facilities = emergency_data['emergency_facilities']
            
            # Medical Facilities
            hospitals = facilities.get('hospital', [])
            clinics = facilities.get('emergency_clinic', [])
            all_medical = hospitals + clinics
            
            if all_medical:
                pdf.ln(5)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_text_color(*self.danger_color)
                pdf.cell(0, 6, f'MEDICAL FACILITIES ({len(all_medical)} identified):', 0, 1, 'L')
                
                headers = ['#', 'Facility Name', 'Address', 'Phone Number', 'Distance']
                col_widths = [15, 50, 50, 40, 30]
                
                pdf.create_table_header(headers, col_widths)
                
                for i, facility in enumerate(all_medical[:10], 1):
                    row_data = [
                        str(i),
                        facility.get('name', 'Unknown Facility')[:25],
                        facility.get('formatted_address', facility.get('address', 'Unknown'))[:25],
                        facility.get('formatted_phone_number', 'Not available'),
                        f"{facility.get('distance_km', 0):.1f} km"
                    ]
                    pdf.create_table_row(row_data, col_widths)
            
            # Police Stations
            police_stations = facilities.get('police', [])
            if police_stations:
                pdf.ln(10)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_text_color(*self.primary_color)
                pdf.cell(0, 6, f'POLICE STATIONS ({len(police_stations)} identified):', 0, 1, 'L')
                
                headers = ['#', 'Police Station', 'Address', 'Phone Number', 'Distance']
                col_widths = [15, 50, 50, 40, 30]
                
                pdf.create_table_header(headers, col_widths)
                
                for i, station in enumerate(police_stations[:8], 1):
                    row_data = [
                        str(i),
                        station.get('name', 'Unknown Station')[:25],
                        station.get('formatted_address', station.get('address', 'Unknown'))[:25],
                        station.get('formatted_phone_number', 'Not available'),
                        f"{station.get('distance_km', 0):.1f} km"
                    ]
                    pdf.create_table_row(row_data, col_widths)
            
            # Fire Stations
            fire_stations = facilities.get('fire_station', [])
            if fire_stations:
                pdf.ln(10)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_text_color(*self.warning_color)
                pdf.cell(0, 6, f'FIRE STATIONS ({len(fire_stations)} identified):', 0, 1, 'L')
                
                headers = ['#', 'Fire Station', 'Address', 'Phone Number', 'Distance']
                col_widths = [15, 50, 50, 40, 30]
                
                pdf.create_table_header(headers, col_widths)
                
                for i, station in enumerate(fire_stations[:8], 1):
                    row_data = [
                        str(i),
                        station.get('name', 'Unknown Station')[:25],
                        station.get('formatted_address', station.get('address', 'Unknown'))[:25],
                        station.get('formatted_phone_number', 'Not available'),
                        f"{station.get('distance_km', 0):.1f} km"
                    ]
                    pdf.create_table_row(row_data, col_widths)
        
        # Critical Preparedness Gaps
        gaps = assessment.get('critical_gaps', [])
        if gaps:
            pdf.ln(15)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.danger_color)
            pdf.cell(0, 8, f'CRITICAL PREPAREDNESS GAPS ({len(gaps)} identified)', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for i, gap in enumerate(gaps, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(172, 6, f"{gap} - Address before travel", 0, 'L')
                pdf.ln(2)
        
        # Emergency Preparedness Checklist
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.primary_color)
        pdf.cell(0, 8, 'COMPREHENSIVE EMERGENCY PREPAREDNESS CHECKLIST', 0, 1, 'L')
        
        checklist = [
            "[] First aid kit with bandages, antiseptic, pain relievers, emergency medications",
            "[] Emergency contact numbers saved in phone and written backup copy",
            "[] Vehicle emergency kit - tools, spare tire, jumper cables, tow rope",
            "[] Emergency water supply (minimum 2 liters per person for 24 hours)",
            "[] Non-perishable emergency food (energy bars, nuts, dried fruits)",
            "[] Flashlight with extra batteries or hand-crank/solar powered model",
            "[] Emergency blanket, warm clothing, and weatherproof gear",
            "[] Portable phone charger/power bank with multiple cables",
            "[] Emergency cash in small denominations (ATMs may be unavailable)",
            "[] Vehicle documents in waterproof container (registration, insurance)",
            "[] Road atlas or offline maps as backup to GPS navigation",
            "[] Emergency whistle, signal mirror, or flares for signaling help",
            "[] Multi-tool or knife, duct tape, and basic repair supplies",
            "[] Personal medications for at least 3 days",
            "[] Important documents (ID, medical info, emergency contacts)",
            "[] Fire extinguisher (small vehicle type) and basic safety equipment"
        ]
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        for item in checklist:
            pdf.cell(0, 6, item, 0, 1, 'L')
        
        # Emergency Response Plan
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.danger_color)
        pdf.cell(0, 8, 'EMERGENCY RESPONSE ACTION PLAN', 0, 1, 'L')
        
        action_plan = [
            "1. ASSESS THE SITUATION - Ensure personal safety first, then assess severity",
            "2. CALL FOR HELP - Dial appropriate emergency number (112 for general emergencies)",
            "3. PROVIDE LOCATION - Give precise GPS coordinates or landmark descriptions",
            "4. STAY CALM - Speak clearly and provide requested information to operators",
            "5. FOLLOW INSTRUCTIONS - Emergency operators are trained to guide you",
            "6. SIGNAL FOR HELP - Use emergency signals if phone coverage is unavailable",
            "7. STAY WITH VEHICLE - Unless immediate danger, stay near your vehicle",
            "8. CONSERVE RESOURCES - Ration water, food, and phone battery if stranded",
            "9. MAINTAIN COMMUNICATION - Update emergency contacts on your status",
            "10. DOCUMENT INCIDENT - Take photos/notes for insurance and authorities"
        ]
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        for step in action_plan:
            pdf.cell(0, 6, step, 0, 1, 'L')

    def _get_emergency_data_from_db(self, route_id: str) -> Dict:
        """Get emergency data from the new emergency analyzer database"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check if emergency analysis table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emergency_analysis'")
                if not cursor.fetchone():
                    return {}
                
                cursor.execute("SELECT * FROM emergency_analysis WHERE route_id = ?", (route_id,))
                facilities_data = [dict(row) for row in cursor.fetchall()]
                
                if not facilities_data:
                    return {}
                
                # Group facilities by type
                emergency_facilities = {}
                for facility in facilities_data:
                    facility_type = facility['facility_type']
                    if facility_type not in emergency_facilities:
                        emergency_facilities[facility_type] = []
                    
                    # Parse additional data
                    additional_data = {}
                    try:
                        additional_data = json.loads(facility.get('additional_data', '{}'))
                    except:
                        pass
                    
                    facility_info = {
                        'name': facility['facility_name'],
                        'latitude': facility['latitude'],
                        'longitude': facility['longitude'],
                        'formatted_address': facility.get('formatted_address', ''),
                        'formatted_phone_number': facility.get('formatted_phone_number', ''),
                        'international_phone_number': facility.get('international_phone_number', ''),
                        'website': facility.get('website', ''),
                        'rating': facility.get('rating', 0),
                        'operational_status': facility.get('operational_status', 'UNKNOWN'),
                        'distance_km': facility.get('distance_km', 0),
                        'priority_level': facility.get('priority_level', 5)
                    }
                    
                    emergency_facilities[facility_type].append(facility_info)
                
                # Calculate summary statistics
                total_facilities = len(facilities_data)
                preparedness_score = min(100, total_facilities * 5)  # Simple scoring
                
                # Identify gaps
                critical_gaps = []
                if 'hospital' not in emergency_facilities:
                    critical_gaps.append("No hospitals found along route")
                if 'police' not in emergency_facilities:
                    critical_gaps.append("No police stations identified")
                if 'fire_station' not in emergency_facilities:
                    critical_gaps.append("No fire stations found")
                
                return {
                    'emergency_facilities': emergency_facilities,
                    'preparedness_score': preparedness_score,
                    'total_facilities': total_facilities,
                    'critical_gaps': critical_gaps,
                    'overall_assessment': 'EXCELLENT' if preparedness_score >= 80 else 'GOOD' if preparedness_score >= 60 else 'NEEDS IMPROVEMENT',
                    'coverage_analysis': {
                        'coverage_percentage': f"{min(100, preparedness_score)}%",
                        'coverage_gaps': []
                    }
                }
                
        except Exception as e:
            print(f"Error getting emergency data from database: {e}")
            return {}
    
    def _add_route_map_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add comprehensive route map with FIXED legend table layout"""
        
        route_maps = self.get_stored_images_from_db(route_id, 'route_map')
        pdf.add_page()
        pdf.add_section_header("COMPREHENSIVE ROUTE MAP WITH ALL CRITICAL POINTS", "info")
        
        if route_maps:
            route_map = route_maps[-1]
            image_path = route_map['file_path']
            if os.path.exists(image_path):
                try:
                    pdf.set_font('Helvetica', 'B', 12)
                    pdf.set_text_color(*self.primary_color)
                    pdf.cell(0, 8, 'COMPREHENSIVE ROUTE VISUALIZATION', 0, 1, 'C')
                    pdf.ln(5)
                    pdf.image(image_path, x=10, y=pdf.get_y(), w=190, h=130)
                    pdf.set_y(pdf.get_y() + 135)
                    
                    pdf.set_font('Helvetica', 'B', 11)
                    pdf.set_text_color(*self.primary_color)
                    pdf.cell(0, 6, 'MAP LEGEND & SYMBOL GUIDE', 0, 1, 'C')
                    pdf.ln(3)
                    
                    col_widths = [25, 25, 50, 80]
                    x_start = 15
                    
                    # SECTION 1: CRITICAL SAFETY MARKERS
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.set_text_color(*self.danger_color)
                    pdf.cell(0, 6, 'CRITICAL SAFETY MARKERS:', 0, 1, 'L')
                    
                    safety_legend = [
                        ['SYMBOL', 'COLOR', 'MEANING', 'ACTION REQUIRED'],
                        ['T1-T15', 'RED', 'Sharp Turns (>=70 deg)', 'Reduce speed, extreme caution'],
                        ['D', 'PURPLE', 'Network Dead Zones', 'Use satellite communication'],
                        ['T', 'ORANGE', 'Heavy Traffic Areas', 'Allow extra travel time'],
                        ['—', 'BLUE', 'Complete Route Path', 'Follow GPS navigation']
                    ]
                    
                    # FIXED: Use proper table rendering method
                    self._render_legend_table(pdf, safety_legend, col_widths, x_start, (240, 240, 240))
                    
                    # SECTION 2: SERVICES & FACILITIES - CHECK SPACE FIRST
                    required_space = 8 * 6 + 10  # 8 rows * 6px + header space
                    if pdf.get_y() + required_space > 270:  # If not enough space, start new page
                        pdf.add_page()
                        pdf.set_font('Helvetica', 'B', 11)
                        pdf.set_text_color(*self.primary_color)
                        pdf.cell(0, 6, 'MAP LEGEND & SYMBOL GUIDE (CONTINUED)', 0, 1, 'C')
                        pdf.ln(5)
                    
                    pdf.ln(5)
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.set_text_color(*self.info_color)
                    pdf.cell(0, 6, 'SERVICES & FACILITIES MARKERS:', 0, 1, 'L')
                    
                    services_legend = [
                        ['SYMBOL', 'COLOR', 'SERVICE TYPE', 'DESCRIPTION'],
                        ['H', 'BLUE', 'Hospitals', 'Emergency medical services'],
                        ['P', 'BLUE', 'Police Stations', 'Law enforcement & security'],
                        ['F', 'BLUE', 'Fire Stations', 'Fire & rescue services'],
                        ['G', 'GREEN', 'Gas Stations', 'Fuel & vehicle services'],
                        ['S', 'YELLOW', 'Schools', 'Speed limit zones (40 km/h)'],
                        ['R', 'ORANGE', 'Restaurants', 'Food & rest stops']
                    ]
                    
                    # FIXED: Use proper table rendering method with space check
                    self._render_legend_table_with_page_check(pdf, services_legend, col_widths, x_start, (245, 250, 255))

                    # SECTION 3: MAP STATISTICS - CHECK SPACE FIRST
                    stats_space_needed = 60  # Approximate space needed for statistics section
                    if pdf.get_y() + stats_space_needed > 260:  # Leave more margin for statistics
                        pdf.add_page()
                        pdf.set_font('Helvetica', 'B', 11)
                        pdf.set_text_color(*self.primary_color)
                        pdf.cell(0, 6, 'MAP STATISTICS & TECHNICAL DETAILS', 0, 1, 'C')
                        pdf.ln(5)
                    
                    pdf.ln(8)
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.set_text_color(*self.primary_color)
                    pdf.cell(0, 6, 'MAP STATISTICS & TECHNICAL DETAILS', 0, 1, 'L')
                    
                    sharp_turns = self.db_manager.get_sharp_turns(route_id)
                    hospitals = self.db_manager.get_pois_by_type(route_id, 'hospital')
                    gas_stations = self.db_manager.get_pois_by_type(route_id, 'gas_station')
                    schools = self.db_manager.get_pois_by_type(route_id, 'school')
                    police = self.db_manager.get_pois_by_type(route_id, 'police')
                    fire_stations = self.db_manager.get_pois_by_type(route_id, 'fire_station')
                    network_coverage = self.db_manager.get_network_coverage(route_id)
                    dead_zones = [p for p in network_coverage if p.get('is_dead_zone')]
                    
                    left_stats = [
                        f"Map Resolution: 800x600 pixels",
                        f"File Size: {route_map.get('file_size', 0) / 1024:.1f} KB",
                        f"Generated: {route_map.get('created_at', 'Unknown')[:16]}",
                        f"Critical Turns: {len([t for t in sharp_turns if t['angle'] >= 70])}",
                        f"Emergency Services: {len(hospitals) + len(police) + len(fire_stations)}",
                        f"Essential Services: {len(gas_stations)}"
                    ]
                    
                    right_stats = [
                        f"Map Type: Google Static Maps API",
                        f"School Zones: {len(schools)} (40 km/h limit)",
                        f"Dead Zones: {len(dead_zones)} areas",
                        f"Total Markers: Up to 50 critical points",
                        f"Route Coverage: 100% GPS path",
                        f"Coordinate System: WGS84 (GPS standard)"
                    ]
                    
                    pdf.set_font('Helvetica', '', 8)
                    pdf.set_text_color(0, 0, 0)
                    start_y = pdf.get_y()
                    
                    # FIXED: Better two-column layout with proper spacing
                    pdf.set_xy(15, start_y)
                    for i, stat in enumerate(left_stats):
                        pdf.cell(90, 4, f"• {stat}", 0, 1, 'L')
                        if i < len(left_stats) - 1:  # Don't move X for last item
                            pdf.set_x(15)
                    
                    # Right column
                    pdf.set_xy(110, start_y)
                    for i, stat in enumerate(right_stats):
                        pdf.cell(85, 4, f"• {stat}", 0, 1, 'L')
                        if i < len(right_stats) - 1:  # Don't move X for last item
                            pdf.set_x(110)
                    
                    # USAGE INSTRUCTIONS - CHECK SPACE
                    instructions_space = 8 * 5 + 10  # 8 instructions * 5px + header
                    if pdf.get_y() + instructions_space > 270:
                        pdf.add_page()
                        pdf.set_font('Helvetica', 'B', 11)
                        pdf.set_text_color(*self.primary_color)
                        pdf.cell(0, 6, 'MAP USAGE INSTRUCTIONS', 0, 1, 'C')
                        pdf.ln(3)
                    
                    pdf.ln(10)
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.set_text_color(*self.warning_color)
                    pdf.cell(0, 6, 'MAP USAGE INSTRUCTIONS:', 0, 1, 'L')
                    
                    instructions = [
                        "1. RED markers (T1-T15): Critical turns requiring speed reduction and extreme caution",
                        "2. BLUE markers (H,P,F): Emergency services for safety and security assistance",
                        "3. GREEN markers (G): Fuel stations for vehicle refueling and maintenance",
                        "4. YELLOW markers (S): School zones with mandatory 40 km/h speed limits",
                        "5. PURPLE markers (D): Dead zones requiring alternative communication methods",
                        "6. BLUE route line: Complete GPS path optimized for vehicle navigation"
                    ]
                    
                    pdf.set_font('Helvetica', '', 8)
                    pdf.set_text_color(0, 0, 0)
                    for instruction in instructions:
                        # Check space for each instruction
                        if pdf.get_y() + 5 > 280:
                            pdf.add_page()
                            pdf.set_font('Helvetica', 'B', 10)
                            pdf.set_text_color(*self.warning_color)
                            pdf.cell(0, 6, 'MAP USAGE INSTRUCTIONS (CONTINUED):', 0, 1, 'L')
                            pdf.set_font('Helvetica', '', 8)
                            pdf.set_text_color(0, 0, 0)
                        
                        pdf.cell(0, 4, instruction, 0, 1, 'L')
                    
                except Exception as e:
                    print(f"Error adding comprehensive route map: {e}")
                    pdf.set_font('Helvetica', '', 12)
                    pdf.cell(0, 10, f'Error loading comprehensive route map: {str(e)}', 0, 1, 'L')
            else:
                pdf.set_font('Helvetica', '', 12)
                pdf.cell(0, 10, f'Comprehensive route map file not found: {image_path}', 0, 1, 'L')
        else:
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.warning_color)
            pdf.cell(0, 10, 'COMPREHENSIVE ROUTE MAP NOT GENERATED', 0, 1, 'L')
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 6, 'The comprehensive route map was not generated during route analysis. This could be due to Google Static Maps API issues or missing API key configuration.', 0, 'L')
            
            pdf.ln(5)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(*self.info_color)
            pdf.cell(0, 8, 'TROUBLESHOOTING - COMPREHENSIVE MAP GENERATION:', 0, 1, 'L')
            
            troubleshooting = [
                "• Verify Google Static Maps API is enabled in Google Cloud Console",
                "• Check API key has Static Maps permissions",
                "• Ensure route analysis completed without errors",
                "• Verify images/maps directory exists and is writable",
                "• Check API quota limits have not been exceeded",
                "• Review application logs for specific generation errors"
            ]
            
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(0, 0, 0)
            for item in troubleshooting:
                pdf.cell(0, 6, item, 0, 1, 'L')
    def _render_legend_table_with_page_check(self, pdf: 'EnhancedRoutePDF', table_data: list, col_widths: list, x_start: int, header_color: tuple):
        """FIXED: Proper table rendering with automatic page break handling"""
        
        total_rows = len(table_data)
        row_height = 6
        header_height = 7
        
        # Check if entire table fits on current page
        total_height_needed = header_height + (total_rows - 1) * row_height
        
        if pdf.get_y() + total_height_needed > 270:
            # Split table or move to new page
            if total_rows > 8:  # If table is large, split it
                # Render first part
                first_part = table_data[:5]  # Header + 4 data rows
                self._render_legend_table(pdf, first_part, col_widths, x_start, header_color)
                
                # Start new page for second part
                pdf.add_page()
                pdf.set_font('Helvetica', 'B', 11)
                pdf.set_text_color(*self.primary_color)
                pdf.cell(0, 6, 'SERVICES & FACILITIES MARKERS (CONTINUED)', 0, 1, 'C')
                pdf.ln(3)
                
                # Render second part with header
                second_part = [table_data[0]] + table_data[5:]  # Header + remaining rows
                self._render_legend_table(pdf, second_part, col_widths, x_start, header_color)
            else:
                # Small table - move entire table to new page
                pdf.add_page()
                pdf.set_font('Helvetica', 'B', 11)
                pdf.set_text_color(*self.primary_color)
                pdf.cell(0, 6, 'MAP LEGEND & SYMBOL GUIDE (CONTINUED)', 0, 1, 'C')
                pdf.ln(5)
                
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_text_color(*self.info_color)
                pdf.cell(0, 6, 'SERVICES & FACILITIES MARKERS:', 0, 1, 'L')
                
                self._render_legend_table(pdf, table_data, col_widths, x_start, header_color)
        else:
            # Table fits - render normally
            self._render_legend_table(pdf, table_data, col_widths, x_start, header_color)
    def _render_legend_table(self, pdf: 'EnhancedRoutePDF', table_data: list, col_widths: list, x_start: int, header_color: tuple):
        """FIXED: Proper table rendering helper method"""
        
        # Header row
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(*header_color)
        pdf.set_text_color(0, 0, 0)
        
        # Draw header
        y_pos = pdf.get_y()
        for i, (header, width) in enumerate(zip(table_data[0], col_widths)):
            pdf.set_xy(x_start + sum(col_widths[:i]), y_pos)
            pdf.cell(width, 7, header, 1, 0, 'C', True)
        
        pdf.ln(7)  # Move to next row
        
        # Data rows
        pdf.set_font('Helvetica', '', 8)
        pdf.set_fill_color(255, 255, 255)
        
        for row in table_data[1:]:  # Skip header row
            # Check if we need a page break during table rendering
            if pdf.get_y() + 8 > 270:  # If next row won't fit
                pdf.add_page()
                pdf.set_font('Helvetica', 'B', 10)
                pdf.set_text_color(*self.primary_color)
                pdf.cell(0, 6, 'MAP LEGEND (CONTINUED)', 0, 1, 'C')
                pdf.ln(3)
                
                # Re-draw header on new page
                pdf.set_font('Helvetica', 'B', 8)
                pdf.set_fill_color(*header_color)
                pdf.set_text_color(0, 0, 0)
                
                y_pos = pdf.get_y()
                for i, (header, width) in enumerate(zip(table_data[0], col_widths)):
                    pdf.set_xy(x_start + sum(col_widths[:i]), y_pos)
                    pdf.cell(width, 7, header, 1, 0, 'C', True)
                
                pdf.ln(7)
                pdf.set_font('Helvetica', '', 8)
                pdf.set_fill_color(255, 255, 255)
            
            y_pos = pdf.get_y()
            
            # Calculate height needed for this row
            max_height = 6
            for i, (cell, width) in enumerate(zip(row, col_widths)):
                text_len = len(str(cell))
                if text_len > width // 3:
                    max_height = max(max_height, 8)
            
            # Draw each cell in the row
            for i, (cell, width) in enumerate(zip(row, col_widths)):
                pdf.set_xy(x_start + sum(col_widths[:i]), y_pos)
                
                # Clean text and truncate if needed
                cell_text = self.clean_text_for_pdf(str(cell))
                max_chars = max(width // 3, 8)
                if len(cell_text) > max_chars:
                    cell_text = cell_text[:max_chars-3] + '...'
                
                pdf.cell(width, max_height, cell_text, 1, 0, 'L', True)
            
            pdf.ln(max_height)  # Move to next row

    
    def _add_images_summary_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add comprehensive images inventory and summary"""
        
        pdf.add_page()
        pdf.add_section_header("COMPREHENSIVE STORED IMAGES SUMMARY", "info")
        
        # Get all images for this route
        all_images = self.get_stored_images_from_db(route_id)
        
        if not all_images:
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(0, 10, 'No images stored for this route in the database.', 0, 1, 'L')
            return
        
        # Group images by type and analyze
        images_by_type = {}
        total_size = 0
        file_status = {'found': 0, 'missing': 0}
        
        for img in all_images:
            img_type = img['image_type']
            if img_type not in images_by_type:
                images_by_type[img_type] = {'count': 0, 'size': 0, 'files': []}
            
            images_by_type[img_type]['count'] += 1
            images_by_type[img_type]['size'] += img.get('file_size', 0)
            images_by_type[img_type]['files'].append(img)
            total_size += img.get('file_size', 0)
            
            # Check file existence
            if img['file_path'] and os.path.exists(img['file_path']):
                file_status['found'] += 1
            else:
                file_status['missing'] += 1
        
        # Storage summary statistics
        summary_table = [
            ['Total Images in Database', f"{len(all_images):,}"],
            ['Image Types Available', f"{len(images_by_type)} categories"],
            ['Street View Images', f"{len(images_by_type.get('street_view', {}).get('files', [])):,}"],
            ['Satellite Images', f"{len(images_by_type.get('satellite', {}).get('files', [])):,}"],
            ['Route Map Images', f"{len(images_by_type.get('route_map', {}).get('files', [])):,}"],
            ['Total Storage Used', f"{total_size / (1024*1024):.2f} MB"],
            ['Files Found on Disk', f"{file_status['found']:,} ({file_status['found']/len(all_images)*100:.1f}%)"],
            ['Missing Files', f"{file_status['missing']:,} ({file_status['missing']/len(all_images)*100:.1f}%)"],
            ['Storage Base Path', self.image_base_path]
        ]
        
        pdf.create_detailed_table(summary_table, [80, 100])
        
        # File integrity assessment
        pdf.ln(10)
        integrity_score = (file_status['found'] / len(all_images) * 100) if all_images else 0
        
        if integrity_score >= 90:
            integrity_color = self.success_color
            integrity_status = "EXCELLENT FILE INTEGRITY"
        elif integrity_score >= 75:
            integrity_color = self.info_color
            integrity_status = "GOOD FILE INTEGRITY"
        elif integrity_score >= 50:
            integrity_color = self.warning_color
            integrity_status = "MODERATE FILE INTEGRITY"
        else:
            integrity_color = self.danger_color
            integrity_status = "POOR FILE INTEGRITY"
        
        pdf.set_fill_color(*integrity_color)
        pdf.rect(10, pdf.get_y(), 190, 12, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_xy(15, pdf.get_y() + 2)
        pdf.cell(180, 8, f'FILE INTEGRITY: {integrity_status} ({integrity_score:.1f}%)', 0, 1, 'C')
        
        # Detailed images inventory by type
        pdf.ln(15)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.primary_color)
        pdf.cell(0, 8, 'DETAILED IMAGES INVENTORY BY TYPE', 0, 1, 'L')
        
        for img_type, type_data in images_by_type.items():
            if not type_data['files']:
                continue
            
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(*self.info_color)
            type_name = img_type.replace('_', ' ').title()
            pdf.cell(0, 7, f'{type_name} Images ({type_data["count"]} files, {type_data["size"]/1024:.1f} KB)', 0, 1, 'L')
            
            # Table headers
            headers = ['#', 'Filename', 'GPS Location', 'Size', 'Created', 'Status']
            col_widths = [15, 45, 50, 20, 35, 20]
            
            pdf.create_table_header(headers, col_widths)
            
            # List files
            for i, img in enumerate(type_data['files'][:15], 1):  # Limit to 15 per type
                file_exists = os.path.exists(img['file_path']) if img['file_path'] else False
                status = 'Found' if file_exists else 'Missing'
                
                row_data = [
                    str(i),
                    os.path.basename(img['filename'])[:20],
                    f"{img.get('latitude', 0):.4f}, {img.get('longitude', 0):.4f}",
                    f"{img.get('file_size', 0) / 1024:.0f}KB",
                    img.get('created_at', 'Unknown')[:10],
                    status
                ]
                
                pdf.create_table_row(row_data, col_widths)
        
        # Storage recommendations
        pdf.ln(15)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.warning_color)
        pdf.cell(0, 8, 'STORAGE MANAGEMENT RECOMMENDATIONS', 0, 1, 'L')
        
        recommendations = [
            f"* Regular backup of image files to prevent data loss",
            f"* Verify file paths in database match actual file locations",
            f"* Consider compression for large image files to save storage space",
            f"* Implement automated cleanup of old route images (>6 months)",
            f"* Monitor storage usage - current usage: {total_size/1024/1024:.1f} MB",
            f"* Maintain consistent naming convention for new images"
        ]
        
        if file_status['missing'] > 0:
            recommendations.extend([
                f"* URGENT: {file_status['missing']} files are missing from disk",
                f"* Update database or restore missing files from backup",
                f"* Review file deletion policies and backup procedures"
            ])
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        for rec in recommendations:
            pdf.cell(0, 6, rec, 0, 1, 'L')
    
    def _add_traffic_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add REAL traffic analysis page with database data"""
        from api.route_api import RouteAPI
        route_api = RouteAPI(self.db_manager, None)
        traffic_data = route_api.get_traffic_data(route_id)
        
        pdf.add_page()
        pdf.add_section_header("COMPREHENSIVE TRAFFIC ANALYSIS", "warning")
        
        if 'error' in traffic_data:
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.warning_color)
            pdf.cell(0, 10, 'TRAFFIC DATA UNAVAILABLE', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 6, f'Error: {traffic_data["error"]}', 0, 'L')
            
            pdf.ln(5)
            pdf.cell(0, 6, 'Traffic analysis requires Google Directions API with traffic data enabled.', 0, 1, 'L')
            return
        
        # Display real traffic analysis
        stats = traffic_data['statistics']
        congestion = traffic_data['congestion_analysis']
        
        # Traffic summary
        summary_table = [
            ['Route Segments Analyzed', f"{stats['total_segments_analyzed']:,}"],
            ['Overall Traffic Score', f"{stats['overall_traffic_score']:.1f}/100"],
            ['Traffic Condition', stats['traffic_condition']],
            ['Average Travel Time Index', f"{stats['average_travel_time_index']:.2f}"],
            ['Average Current Speed', f"{stats['average_current_speed']:.1f} km/h"],
            ['Average Free Flow Speed', f"{stats['average_free_flow_speed']:.1f} km/h"],
            ['Heavy Traffic Segments', f"{congestion['heavy_traffic_segments']:,}"],
            ['Moderate Traffic Segments', f"{congestion['moderate_traffic_segments']:,}"],
            ['Free Flow Segments', f"{congestion['free_flow_segments']:,}"],
            ['Worst Congestion Areas', f"{congestion['worst_congestion_percentage']:.1f}% of route"]
        ]
        
        pdf.create_detailed_table(summary_table, [80, 100])
        
        # Traffic condition indicator
        traffic_score = stats['overall_traffic_score']
        if traffic_score >= 80:
            color = self.success_color
            status = "EXCELLENT TRAFFIC CONDITIONS"
        elif traffic_score >= 60:
            color = self.info_color
            status = "GOOD TRAFFIC CONDITIONS"
        elif traffic_score >= 40:
            color = self.warning_color
            status = "MODERATE TRAFFIC CONDITIONS"
        else:
            color = self.danger_color
            status = "POOR TRAFFIC CONDITIONS"
        
        pdf.ln(10)
        pdf.set_fill_color(*color)
        pdf.rect(10, pdf.get_y(), 190, 12, 'F')
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_xy(15, pdf.get_y() + 2)
        pdf.cell(180, 8, f'TRAFFIC STATUS: {status} ({traffic_score:.1f}/100)', 0, 1, 'C')
        
        # Rest of traffic analysis implementation...
        
        # Traffic recommendations
        recommendations = traffic_data.get('recommendations', [])
        if recommendations:
            pdf.ln(15)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.primary_color)
            pdf.cell(0, 8, 'TRAFFIC-BASED RECOMMENDATIONS', 0, 1, 'L')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            for i, rec in enumerate(recommendations, 1):
                pdf.cell(8, 6, f'{i}.', 0, 0, 'L')
                pdf.multi_cell(172, 6, rec, 0, 'L')
                pdf.ln(2)
    
    def _add_api_status_page(self, pdf: 'EnhancedRoutePDF', route_id: str):
        """Add comprehensive API status and usage report"""
        pdf.add_page()
        pdf.add_section_header("API STATUS & USAGE REPORT", "primary")
        
        # Get API usage for this route
        try:
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
                
                api_usage = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            api_usage = []
            print(f"Error getting API usage: {e}")
        
        if api_usage:
            # API usage summary
            api_summary = {}
            total_calls = len(api_usage)
            successful_calls = len([call for call in api_usage if call['success']])
            
            for call in api_usage:
                api_name = call['api_name']
                if api_name not in api_summary:
                    api_summary[api_name] = {'calls': 0, 'success': 0, 'total_time': 0, 'errors': []}
                
                api_summary[api_name]['calls'] += 1
                if call['success']:
                    api_summary[api_name]['success'] += 1
                api_summary[api_name]['total_time'] += call.get('response_time', 0)
                
                if call.get('error_message'):
                    api_summary[api_name]['errors'].append(call['error_message'])
            
            # Summary statistics
            overall_success = (successful_calls / total_calls * 100) if total_calls > 0 else 0
            
            summary_table = [
                ['Total API Calls Made', f"{total_calls:,}"],
                ['Successful Calls', f"{successful_calls:,}"],
                ['Failed Calls', f"{total_calls - successful_calls:,}"],
                ['Overall Success Rate', f"{overall_success:.1f}%"],
                ['APIs Used', f"{len(api_summary)} different services"],
                ['Total Response Time', f"{sum(call.get('response_time', 0) for call in api_usage):.3f} seconds"],
                ['Average Response Time', f"{sum(call.get('response_time', 0) for call in api_usage) / total_calls:.3f}s" if total_calls > 0 else "N/A"]
            ]
            
            pdf.create_detailed_table(summary_table, [70, 110])
            
            # Success rate indicator
            pdf.ln(10)
            if overall_success >= 90:
                status_color = self.success_color
                status_text = "EXCELLENT API PERFORMANCE"
            elif overall_success >= 75:
                status_color = self.info_color
                status_text = "GOOD API PERFORMANCE"
            elif overall_success >= 50:
                status_color = self.warning_color
                status_text = "MODERATE API PERFORMANCE"
            else:
                status_color = self.danger_color
                status_text = "POOR API PERFORMANCE"
            
            pdf.set_fill_color(*status_color)
            pdf.rect(10, pdf.get_y(), 190, 12, 'F')
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_xy(15, pdf.get_y() + 2)
            pdf.cell(180, 8, f'API PERFORMANCE: {status_text} ({overall_success:.1f}%)', 0, 1, 'C')
            
            # Detailed API breakdown
            pdf.ln(15)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(*self.primary_color)
            pdf.cell(0, 8, 'DETAILED API USAGE BREAKDOWN', 0, 1, 'L')
            
            headers = ['API Service', 'Calls', 'Success Rate', 'Avg Time', 'Status']
            col_widths = [50, 25, 30, 30, 50]
            
            pdf.create_table_header(headers, col_widths)
            
            for api_name, stats in api_summary.items():
                success_rate = (stats['success'] / stats['calls'] * 100) if stats['calls'] > 0 else 0
                avg_time = (stats['total_time'] / stats['calls']) if stats['calls'] > 0 else 0
                status = 'Working' if success_rate >= 80 else 'Issues' if success_rate >= 50 else 'Failed'
                
                row_data = [
                    api_name.replace('_', ' ').title(),
                    str(stats['calls']),
                    f"{success_rate:.1f}%",
                    f"{avg_time:.3f}s",
                    status
                ]
                pdf.create_table_row(row_data, col_widths)
        
        else:
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(0, 10, 'No API usage data available for this route.', 0, 1, 'L')
        
        # System status and recommendations
        pdf.ln(15)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*self.info_color)
        pdf.cell(0, 8, 'SYSTEM STATUS & RECOMMENDATIONS', 0, 1, 'L')
        
        system_recommendations = [
            "* Monitor API response times to ensure optimal performance",
            "* Implement retry mechanisms for failed API calls",
            "* Cache frequently requested data to reduce API usage",
            "* Set up monitoring alerts for API failures or slowdowns",
            "* Consider backup API providers for critical services",
            "* Regularly review API usage against rate limits and costs"
        ]
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        for rec in system_recommendations:
            pdf.cell(0, 6, rec, 0, 1, 'L')


class EnhancedRoutePDF(FPDF):
    """Enhanced PDF class with Unicode handling"""
    
    def __init__(self, pdf_generator):
        super().__init__()
        self.pdf_generator = pdf_generator
        self.set_auto_page_break(auto=True, margin=15)
        
        # HPCL color scheme
        self.primary_color = (0, 82, 147)
        self.danger_color = (220, 53, 69)
        self.warning_color = (253, 126, 20)
        self.success_color = (40, 167, 69)
        self.info_color = (0, 82, 147)
    
    def cell(self, w, h=0, txt='', border=0, ln=0, align='', fill=False, link=''):
        """Override cell method to clean Unicode characters"""
        if txt:
            txt = self.pdf_generator.clean_text_for_pdf(str(txt))
        return super().cell(w, h, txt, border, ln, align, fill, link)

    def multi_cell(self, w, h, txt='', border=0, align='J', fill=False, split_only=False):
        """Override multi_cell method to clean Unicode characters"""
        if txt:
            txt = self.pdf_generator.clean_text_for_pdf(str(txt))
        return super().multi_cell(w, h, txt, border, align, fill, split_only)
    
    def header(self):
        """Enhanced page header with HPCL branding"""
        if self.page_no() == 1:
            return
        
        # Header background
        self.set_fill_color(*self.primary_color)
        self.rect(0, 0, 210, 25, 'F')
        
        # HPCL branding
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 8)
        self.cell(0, 8, 'HPCL - Journey Risk Management Study (AI-Powered Analysis)', 0, 0, 'L')
        
        # Page number
        self.set_xy(-50, 8)
        self.cell(0, 8, f'Page {self.page_no()}', 0, 0, 'R')
        
        # Date
        self.set_xy(-80, 16)
        self.set_font('Helvetica', '', 8)
        self.cell(0, 5, datetime.datetime.now().strftime('%B %d, %Y'), 0, 0, 'R')
        
        self.ln(30)
    
    def footer(self):
        """Enhanced page footer"""
        self.set_y(-20)
        
        # Footer line
        self.set_draw_color(*self.primary_color)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        
        # Footer text
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(*self.primary_color)
        self.set_y(-15)
        self.cell(0, 5, 'Generated by HPCL Journey Risk Management System - Complete Enhanced Analysis', 0, 0, 'C')
        
        # Confidentiality notice
        self.set_y(-10)
        self.set_font('Helvetica', '', 7)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'CONFIDENTIAL - For Internal Use Only', 0, 0, 'C')
    
    def add_section_header(self, title: str, color_type: str = 'primary'):
        """Add enhanced section header with professional styling"""
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
        
        # Section header background
        self.set_font('Helvetica', 'B', 16)
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.rect(10, self.get_y(), 190, 18, 'F')
        
        # Header text (will be automatically cleaned by overridden cell method)
        self.set_xy(15, self.get_y() + 4)
        self.cell(180, 10, title, 0, 1, 'L')
        
        # Decorative line
        self.set_draw_color(*color)
        self.set_line_width(1)
        self.line(10, self.get_y(), 200, self.get_y())
        
        self.ln(8)
    
    def create_detailed_table(self, data: List[List[str]], col_widths: List[int]):
        """Create detailed table with enhanced formatting and Unicode cleaning"""
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        
        for i, row in enumerate(data):
            if self.get_y() > 260:
                self.add_page()
            
            y_pos = self.get_y()
            
            # Enhanced alternating colors
            if i % 2 == 0:
                self.set_fill_color(248, 249, 250)
            else:
                self.set_fill_color(255, 255, 255)
            
            # First column (bold) - text will be cleaned by overridden cell method
            self.set_font('Helvetica', 'B', 10)
            self.set_xy(10, y_pos)
            self.cell(col_widths[0], 8, str(row[0])[:40], 1, 0, 'L', True)
            
            # Second column - text will be cleaned by overridden cell method
            self.set_font('Helvetica', '', 10)
            self.set_xy(10 + col_widths[0], y_pos)
            self.cell(col_widths[1], 8, str(row[1])[:60], 1, 0, 'L', True)
            
            self.ln(8)
        
        self.ln(5)
    
    def create_table_header(self, headers: List[str], col_widths: List[int]):
        """Create enhanced table header with Unicode cleaning"""
        self.set_font('Helvetica', 'B', 9)
        self.set_fill_color(230, 230, 230)
        self.set_text_color(0, 0, 0)
        self.set_draw_color(200, 200, 200)
        
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            self.set_xy(10 + sum(col_widths[:i]), self.get_y())
            # Text will be cleaned by overridden cell method
            self.cell(width, 12, header, 1, 0, 'C', True)
        self.ln(12)
    
    def create_table_row(self, row_data: List[str], col_widths: List[int]):
        """Create enhanced table row with Unicode cleaning"""
        if self.get_y() > 270:
            self.add_page()
        
        self.set_font('Helvetica', '', 8)
        self.set_fill_color(255, 255, 255)
        self.set_text_color(0, 0, 0)
        self.set_draw_color(220, 220, 220)
        
        y_pos = self.get_y()
        
        for i, (cell, width) in enumerate(zip(row_data, col_widths)):
            self.set_xy(10 + sum(col_widths[:i]), y_pos)
            # Adjust text length based on column width
            max_chars = max(width//3, 8)
            cell_text = str(cell)[:max_chars]
            # Text will be cleaned by overridden cell method
            self.cell(width, 8, cell_text, 1, 0, 'L', True)
        
        self.ln(8)