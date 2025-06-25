// static/js/report.js

// Global variables
let currentRouteId = null;
let reportData = {};

// Initialize the report
async function initializeReport(routeId) {
    currentRouteId = routeId;
    showLoading(true);
    
    try {
        // Load all report data
        await loadReportData(routeId);
        
        // Populate all sections
        populateRouteDetails();
        populateOverviewSection();
        populateSafetyCompliance();
        populateRiskZones();
        populateSeasonalConditions();
        populateEnvironmentalSection();
        populateSharpTurnsSection();
        populatePointsOfInterest();
        populateNetworkCoverage();
        populateWeatherAnalysis();
        populateEmergencyPlanning();
        populateRouteMap();
        populateTrafficAnalysis();
        populateElevationTerrain();
        
        // Setup navigation
        setupSidebarNavigation();
        
        showLoading(false);
        
    } catch (error) {
        console.error('Error initializing report:', error);
        showError('Failed to load report data');
        showLoading(false);
    }
}

// Load all report data from API endpoints
async function loadReportData(routeId) {
    const endpoints = [
        'overview',
        'turns', 
        'pois',
        'network',
        'weather',
        'compliance',
        'elevation',
        'emergency',
        'traffic'
    ];
    
    const promises = endpoints.map(endpoint => 
        fetch(`/api/routes/${routeId}/${endpoint}`)
            .then(response => response.json())
            .then(data => ({ [endpoint]: data }))
            .catch(error => ({ [endpoint]: { error: error.message } }))
    );
    
    const results = await Promise.all(promises);
    reportData = Object.assign({}, ...results);
}

// Show/hide loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = show ? 'flex' : 'none';
}

// Show error message
function showError(message) {
    alert(`Error: ${message}`);
}

// Populate route details card
function populateRouteDetails() {
    const container = document.getElementById('routeDetailsCard');
    const overview = reportData.overview;
    
    if (!overview || overview.error) {
        container.innerHTML = '<p class="error">Route details not available</p>';
        return;
    }
    
    const routeInfo = overview.route_info || {};
    
    container.innerHTML = `
        <h3><i class="fas fa-route"></i> Route Analysis Details</h3>
        <div class="details-grid">
            <div class="detail-item">
                <strong>Route ID:</strong> ${routeInfo.id ? routeInfo.id.substring(0, 12) + '...' : 'Unknown'}
            </div>
            <div class="detail-item">
                <strong>Origin:</strong> ${truncateText(routeInfo.from_address || 'Unknown Location', 50)}
            </div>
            <div class="detail-item">
                <strong>Destination:</strong> ${truncateText(routeInfo.to_address || 'Unknown Location', 50)}
            </div>
            <div class="detail-item">
                <strong>Total Distance:</strong> ${routeInfo.distance || 'Unknown'}
            </div>
            <div class="detail-item">
                <strong>Estimated Duration:</strong> ${routeInfo.duration || 'Unknown'}
            </div>
            <div class="detail-item">
                <strong>Analysis Date:</strong> ${new Date().toLocaleDateString()}
            </div>
        </div>
    `;
}

// Populate overview section
function populateOverviewSection() {
    const routeInfoCard = document.getElementById('routeInfoCard');
    const statisticsCard = document.getElementById('statisticsCard');
    const statusIndicators = document.getElementById('statusIndicators');
    
    const overview = reportData.overview;
    
    if (!overview || overview.error) {
        routeInfoCard.innerHTML = '<p class="error">Overview data not available</p>';
        return;
    }
    
    const routeInfo = overview.route_info || {};
    const statistics = overview.statistics || {};
    
    // Route Information
    routeInfoCard.innerHTML = `
        <h3><i class="fas fa-info-circle"></i> Route Information</h3>
        <table class="data-table">
            <tr><td><strong>From Address</strong></td><td>${routeInfo.from_address || 'Not specified'}</td></tr>
            <tr><td><strong>To Address</strong></td><td>${routeInfo.to_address || 'Not specified'}</td></tr>
            <tr><td><strong>Distance</strong></td><td>${routeInfo.distance || 'Not calculated'}</td></tr>
            <tr><td><strong>Duration</strong></td><td>${routeInfo.duration || 'Not calculated'}</td></tr>
            <tr><td><strong>Total GPS Points</strong></td><td>${statistics.total_points || 0}</td></tr>
        </table>
    `;
    
    // Statistics
    statisticsCard.innerHTML = `
        <h3><i class="fas fa-chart-bar"></i> Route Analysis Statistics</h3>
        <table class="data-table">
            <tr><td><strong>Sharp Turns Detected</strong></td><td>${statistics.total_sharp_turns || 0}</td></tr>
            <tr><td><strong>Critical Turns (≥70°)</strong></td><td>${statistics.critical_turns || 0}</td></tr>
            <tr><td><strong>Points of Interest</strong></td><td>${statistics.total_pois || 0}</td></tr>
            <tr><td><strong>Safety Score</strong></td><td>${statistics.safety_score || 'N/A'}/100</td></tr>
            <tr><td><strong>Risk Level</strong></td><td>${statistics.risk_level || 'Unknown'}</td></tr>
        </table>
    `;
    
    // Status Indicators
    const safetyScore = statistics.safety_score || 0;
    const riskLevel = statistics.risk_level || 'Unknown';
    
    statusIndicators.innerHTML = `
        <div class="status-indicator ${getStatusClass(safetyScore)}">
            <h4>Safety Score</h4>
            <div class="status-value">${safetyScore}/100</div>
            <div class="status-label">${getScoreLabel(safetyScore)}</div>
        </div>
        <div class="status-indicator ${getRiskClass(riskLevel)}">
            <h4>Risk Level</h4>
            <div class="status-value">${riskLevel}</div>
            <div class="status-label">${getRiskDescription(riskLevel)}</div>
        </div>
        <div class="status-indicator ${getTurnsClass(statistics.critical_turns || 0)}">
            <h4>Critical Turns</h4>
            <div class="status-value">${statistics.critical_turns || 0}</div>
            <div class="status-label">${getTurnsLabel(statistics.critical_turns || 0)}</div>
        </div>
    `;
}

// Populate safety compliance section
function populateSafetyCompliance() {
    const container = document.getElementById('complianceGrid');
    const compliance = reportData.compliance;
    
    if (!compliance || compliance.error) {
        container.innerHTML = '<p class="error">Compliance data not available</p>';
        return;
    }
    
    const assessment = compliance.compliance_assessment || {};
    const vehicleInfo = compliance.vehicle_info || {};
    
    container.innerHTML = `
        <div class="compliance-overview">
            <div class="compliance-score ${getComplianceClass(assessment.overall_score)}">
                <h3>Compliance Status: ${assessment.compliance_level || 'Unknown'}</h3>
                <div class="score">${assessment.overall_score || 0}/100</div>
            </div>
        </div>
        
        <div class="compliance-details">
            <h3><i class="fas fa-clipboard-check"></i> Vehicle & Route Compliance</h3>
            <table class="data-table">
                <tr><td><strong>Vehicle Type</strong></td><td>${vehicleInfo.category || 'Unknown'}</td></tr>
                <tr><td><strong>AIS-140 Required</strong></td><td>${vehicleInfo.ais_140_required ? 'YES (Mandatory)' : 'NO'}</td></tr>
                <tr><td><strong>Speed Limits</strong></td><td>NH: 60 km/h; SH: 55 km/h; Rural: 25–30 km/h</td></tr>
                <tr><td><strong>Night Driving</strong></td><td>Prohibited: 00:00–06:00 hrs</td></tr>
                <tr><td><strong>Rest Breaks</strong></td><td>Mandatory 15-30 min every 3 hours</td></tr>
                <tr><td><strong>VTS Requirement</strong></td><td>VTS device shall be functional</td></tr>
            </table>
        </div>
        
        ${assessment.issues_identified && assessment.issues_identified.length > 0 ? `
            <div class="compliance-issues">
                <h3><i class="fas fa-exclamation-triangle"></i> Issues Requiring Attention</h3>
                <ul>
                    ${assessment.issues_identified.map(issue => `<li>${issue}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
    `;
}

// Populate risk zones section
function populateRiskZones() {
    const container = document.getElementById('riskZonesContainer');
    const turns = reportData.turns;
    const network = reportData.network;
    
    if (!turns || turns.error) {
        container.innerHTML = '<p class="error">Risk zones data not available</p>';
        return;
    }
    
    const criticalTurns = turns.categorized_turns?.extreme_blind_spots || [];
    const blindSpots = turns.categorized_turns?.blind_spots || [];
    const deadZones = network?.problem_areas?.dead_zones || [];
    
    let riskZonesHtml = `
        <div class="risk-summary">
            <h3><i class="fas fa-chart-pie"></i> Risk Zones Summary</h3>
            <div class="risk-stats">
                <div class="risk-stat">
                    <span class="risk-number">${criticalTurns.length}</span>
                    <span class="risk-label">Extreme Turns</span>
                </div>
                <div class="risk-stat">
                    <span class="risk-number">${blindSpots.length}</span>
                    <span class="risk-label">Blind Spots</span>
                </div>
                <div class="risk-stat">
                    <span class="risk-number">${deadZones.length}</span>
                    <span class="risk-label">Dead Zones</span>
                </div>
            </div>
        </div>
        
        <div class="risk-zones-list">
    `;
    
    // Add critical turns
    criticalTurns.slice(0, 5).forEach((turn, index) => {
        riskZonesHtml += `
            <div class="risk-zone-card">
                <div class="risk-zone-header">
                    <h4><i class="fas fa-exclamation-triangle"></i> Critical Turn #${index + 1}</h4>
                    <span class="risk-level-critical">CRITICAL</span>
                </div>
                <div class="risk-details">
                    <p><strong>Location:</strong> ${turn.latitude?.toFixed(4)}, ${turn.longitude?.toFixed(4)}</p>
                    <p><strong>Angle:</strong> ${turn.angle}°</p>
                    <p><strong>Recommended Speed:</strong> ${turn.recommended_speed} km/h</p>
                    <p><strong>Action Required:</strong> Full stop may be required, extreme caution</p>
                </div>
            </div>
        `;
    });
    
    // Add dead zones
    deadZones.slice(0, 3).forEach((zone, index) => {
        riskZonesHtml += `
            <div class="risk-zone-card">
                <div class="risk-zone-header">
                    <h4><i class="fas fa-signal"></i> Communication Dead Zone #${index + 1}</h4>
                    <span class="risk-level-high">HIGH</span>
                </div>
                <div class="risk-details">
                    <p><strong>Location:</strong> ${zone.latitude?.toFixed(4)}, ${zone.longitude?.toFixed(4)}</p>
                    <p><strong>Impact:</strong> No cellular service available</p>
                    <p><strong>Action Required:</strong> Use satellite communication device</p>
                </div>
            </div>
        `;
    });
    
    riskZonesHtml += '</div>';
    container.innerHTML = riskZonesHtml;
}

// Populate seasonal conditions section
function populateSeasonalConditions() {
    const container = document.getElementById('seasonalContainer');
    
    // Generate seasonal conditions based on current season and route data
    const currentSeason = getCurrentSeason();
    const turns = reportData.turns;
    const overview = reportData.overview;
    
    container.innerHTML = `
        <div class="seasonal-overview">
            <h3><i class="fas fa-calendar-alt"></i> Current Season: ${currentSeason}</h3>
            <div class="season-alert">
                <p>Review ${currentSeason.toLowerCase()} specific conditions below before departure.</p>
            </div>
        </div>
        
        <div class="seasonal-conditions">
            <h3><i class="fas fa-exclamation-circle"></i> Seasonal Driving Conditions</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Season/Condition</th>
                        <th>Critical Stretches</th>
                        <th>Typical Challenges</th>
                        <th>Driver Caution</th>
                    </tr>
                </thead>
                <tbody>
                    ${generateSeasonalRows()}
                </tbody>
            </table>
        </div>
        
        <div class="seasonal-recommendations">
            <h3><i class="fas fa-lightbulb"></i> Seasonal Recommendations</h3>
            <ul>
                ${getSeasonalRecommendations(currentSeason).map(rec => `<li>${rec}</li>`).join('')}
            </ul>
        </div>
    `;
}

// Populate environmental section
function populateEnvironmentalSection() {
    const container = document.getElementById('environmentalContainer');
    
    container.innerHTML = `
        <div class="environmental-overview">
            <h3><i class="fas fa-leaf"></i> Environmental Impact Assessment</h3>
            <div class="env-score-card">
                <div class="env-score">8.5/10</div>
                <div class="env-status">Low Environmental Risk</div>
            </div>
        </div>
        
        <div class="environmental-zones">
            <h3><i class="fas fa-tree"></i> Environmental Considerations</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Zone/Area</th>
                        <th>Location</th>
                        <th>Environmental Risk</th>
                        <th>Guidelines</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Eco-sensitive Areas</td>
                        <td>Rural sections</td>
                        <td>Wildlife crossing zones</td>
                        <td>Drive slowly, avoid honking</td>
                    </tr>
                    <tr>
                        <td>Waterbody Crossings</td>
                        <td>Bridge sections</td>
                        <td>Pollution prevention</td>
                        <td>No refueling near bridges</td>
                    </tr>
                    <tr>
                        <td>School Areas</td>
                        <td>Urban zones</td>
                        <td>Pedestrian safety</td>
                        <td>25-30 km/h speed limit</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="environmental-guidelines">
            <h3><i class="fas fa-clipboard-list"></i> Environmental Guidelines</h3>
            <ul>
                <li>Never discard trash or spill fuel - carry spill kits and clean-up materials</li>
                <li>Avoid honking in populated areas and during cultural gatherings</li>
                <li>Follow local traffic signage and state-specific restrictions</li>
                <li>Be courteous to local communities - stop only at designated points</li>
            </ul>
        </div>
    `;
}

// Populate sharp turns section
function populateSharpTurnsSection() {
    const container = document.getElementById('turnsContainer');
    const turns = reportData.turns;
    
    if (!turns || turns.error) {
        container.innerHTML = '<p class="error">Sharp turns data not available</p>';
        return;
    }
    
    const totalTurns = turns.total_turns || 0;
    const categorizedTurns = turns.categorized_turns || {};
    
    container.innerHTML = `
        <div class="turns-overview">
            <h3><i class="fas fa-tachometer-alt"></i> Sharp Turns Analysis Summary</h3>
            <div class="turns-stats">
                <div class="stat-card">
                    <div class="stat-number">${totalTurns}</div>
                    <div class="stat-label">Total Sharp Turns</div>
                </div>
                <div class="stat-card danger">
                    <div class="stat-number">${(categorizedTurns.extreme_blind_spots || []).length}</div>
                    <div class="stat-label">Extreme Danger</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-number">${(categorizedTurns.blind_spots || []).length}</div>
                    <div class="stat-label">High Risk</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-number">${(categorizedTurns.sharp_danger || []).length}</div>
                    <div class="stat-label">Moderate Risk</div>
                </div>
            </div>
        </div>
        
        <div class="turn-classification">
            <h3><i class="fas fa-layer-group"></i> Turn Classification System</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Angle Range</th>
                        <th>Classification</th>
                        <th>Risk Level</th>
                        <th>Max Speed</th>
                        <th>Safety Requirement</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="danger-row">
                        <td>≥90°</td>
                        <td>EXTREME BLIND SPOT</td>
                        <td>CRITICAL</td>
                        <td>15 km/h</td>
                        <td>Full stop may be required</td>
                    </tr>
                    <tr class="warning-row">
                        <td>80-90°</td>
                        <td>HIGH-RISK BLIND SPOT</td>
                        <td>EXTREME</td>
                        <td>20 km/h</td>
                        <td>Extreme caution required</td>
                    </tr>
                    <tr class="info-row">
                        <td>70-80°</td>
                        <td>BLIND SPOT</td>
                        <td>HIGH</td>
                        <td>25 km/h</td>
                        <td>High caution required</td>
                    </tr>
                    <tr>
                        <td>60-70°</td>
                        <td>HIGH-ANGLE TURN</td>
                        <td>MEDIUM</td>
                        <td>30 km/h</td>
                        <td>Moderate caution required</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="critical-turns">
            <h3><i class="fas fa-exclamation-triangle"></i> Most Critical Turns</h3>
            ${generateCriticalTurnCards(categorizedTurns)}
        </div>
    `;
}

// Populate points of interest section
function populatePointsOfInterest() {
    const container = document.getElementById('poiContainer');
    const pois = reportData.pois;
    
    if (!pois || pois.error) {
        container.innerHTML = '<p class="error">Points of Interest data not available</p>';
        return;
    }
    
    const poisByType = pois.pois_by_type || {};
    const statistics = pois.statistics || {};
    
    container.innerHTML = `
        <div class="poi-overview">
            <h3><i class="fas fa-map-marked-alt"></i> Service Availability Assessment</h3>
            <div class="poi-score ${getServiceClass(statistics.coverage_score || 0)}">
                <div class="score">${statistics.coverage_score || 0}/100</div>
                <div class="label">Service Coverage Score</div>
            </div>
        </div>
        
        <div class="poi-stats">
            <div class="stat-grid">
                <div class="stat-item">
                    <span class="stat-value">${statistics.total_pois || 0}</span>
                    <span class="stat-label">Total POIs</span>
                </div>
                <div class="stat-item emergency">
                    <span class="stat-value">${statistics.emergency_services || 0}</span>
                    <span class="stat-label">Emergency Services</span>
                </div>
                <div class="stat-item essential">
                    <span class="stat-value">${statistics.essential_services || 0}</span>
                    <span class="stat-label">Essential Services</span>
                </div>
                <div class="stat-item other">
                    <span class="stat-value">${statistics.other_services || 0}</span>
                    <span class="stat-label">Other Services</span>
                </div>
            </div>
        </div>
        
        <div class="poi-categories">
            ${generatePOICategories(poisByType)}
        </div>
    `;
}

// Populate network coverage section
function populateNetworkCoverage() {
    const container = document.getElementById('networkContainer');
    const network = reportData.network;
    
    if (!network || network.error) {
        container.innerHTML = '<p class="error">Network coverage data not available</p>';
        return;
    }
    
    const statistics = network.statistics || {};
    const qualityDist = network.quality_distribution || {};
    
    container.innerHTML = `
        <div class="network-overview">
            <h3><i class="fas fa-wifi"></i> Network Coverage Analysis</h3>
            <div class="coverage-score ${getCoverageClass(statistics.overall_coverage_score || 0)}">
                <div class="score">${statistics.overall_coverage_score || 0}/100</div>
                <div class="label">Coverage Reliability</div>
            </div>
        </div>
        
        <div class="network-stats">
            <table class="data-table">
                <tr><td><strong>Analysis Points</strong></td><td>${statistics.total_points_analyzed || 0}</td></tr>
                <tr><td><strong>Dead Zones</strong></td><td>${statistics.dead_zones_count || 0}</td></tr>
                <tr><td><strong>Poor Coverage Areas</strong></td><td>${statistics.poor_coverage_count || 0}</td></tr>
                <tr><td><strong>Good Coverage</strong></td><td>${statistics.good_coverage_percentage || 0}%</td></tr>
            </table>
        </div>
        
        <div class="signal-quality">
            <h3><i class="fas fa-signal"></i> Signal Quality Distribution</h3>
            <div class="quality-bars">
                ${generateQualityBars(qualityDist, statistics.total_points_analyzed || 1)}
            </div>
        </div>
        
        ${(statistics.dead_zones_count || 0) > 0 ? `
            <div class="dead-zones-alert">
                <h3><i class="fas fa-exclamation-triangle"></i> Communication Dead Zones Detected</h3>
                <p>Route has ${statistics.dead_zones_count} areas with no cellular service. Consider carrying satellite communication device.</p>
            </div>
        ` : ''}
        
        <div class="network-recommendations">
            <h3><i class="fas fa-lightbulb"></i> Network Coverage Recommendations</h3>
            <ul>
                <li>Download offline maps before travel (Google Maps, Maps.me)</li>
                <li>Inform someone of your route and expected arrival time</li>
                <li>Keep emergency numbers saved: 112 (Emergency), 100 (Police), 108 (Ambulance)</li>
                ${(statistics.dead_zones_count || 0) > 0 ? '<li>Carry satellite communication device for dead zones</li>' : ''}
            </ul>
        </div>
    `;
}

// Populate weather analysis section
function populateWeatherAnalysis() {
    const container = document.getElementById('weatherContainer');
    const weather = reportData.weather;
    
    if (!weather || weather.error) {
        container.innerHTML = '<p class="error">Weather analysis data not available</p>';
        return;
    }
    
    const statistics = weather.statistics || {};
    const conditions = weather.conditions_summary || {};
    const risks = weather.weather_risks || [];
    
    container.innerHTML = `
        <div class="weather-overview">
            <h3><i class="fas fa-thermometer-half"></i> Weather Conditions Summary</h3>
            <div class="weather-stats-grid">
                <div class="weather-stat">
                    <div class="weather-value">${statistics.average_temperature || 0}°C</div>
                    <div class="weather-label">Average Temperature</div>
                </div>
                <div class="weather-stat">
                    <div class="weather-value">${statistics.average_humidity || 0}%</div>
                    <div class="weather-label">Average Humidity</div>
                </div>
                <div class="weather-stat">
                    <div class="weather-value">${statistics.average_wind_speed || 0} km/h</div>
                    <div class="weather-label">Wind Speed</div>
                </div>
            </div>
        </div>
        
        <div class="weather-conditions">
            <h3><i class="fas fa-cloud"></i> Weather Conditions Breakdown</h3>
            <div class="conditions-grid">
                ${generateWeatherConditions(conditions, statistics.points_analyzed || 1)}
            </div>
        </div>
        
        ${risks.length > 0 ? `
            <div class="weather-risks">
                <h3><i class="fas fa-exclamation-triangle"></i> Weather Risks Identified</h3>
                <ul>
                    ${risks.map(risk => `<li>${risk}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
        
        <div class="weather-preparation">
            <h3><i class="fas fa-tools"></i> Weather-Based Vehicle Preparation</h3>
            <ul>
                ${generateWeatherPreparation(statistics.average_temperature || 25, conditions)}
            </ul>
        </div>
    `;
}

// Populate emergency planning section
function populateEmergencyPlanning() {
    const container = document.getElementById('emergencyContainer');
    const emergency = reportData.emergency;
    
    if (!emergency || emergency.error) {
        container.innerHTML = '<p class="error">Emergency planning data not available</p>';
        return;
    }
    
    const assessment = emergency.preparedness_assessment || emergency;
    const services = emergency.emergency_services || {};
    
    container.innerHTML = `
        <div class="emergency-overview">
            <h3><i class="fas fa-shield-alt"></i> Emergency Preparedness Assessment</h3>
            <div class="emergency-score ${getEmergencyClass(assessment.emergency_score || 0)}">
                <div class="score">${assessment.emergency_score || 0}/100</div>
                <div class="label">${assessment.preparedness_level || 'Unknown'}</div>
            </div>
        </div>
        
        <div class="emergency-contacts">
            <h3><i class="fas fa-phone"></i> Critical Emergency Contact Numbers</h3>
            <div class="contacts-grid">
                <div class="contact-card emergency">
                    <div class="contact-number">112</div>
                    <div class="contact-label">National Emergency</div>
                    <div class="contact-desc">Any life-threatening emergency</div>
                </div>
                <div class="contact-card police">
                    <div class="contact-number">100</div>
                    <div class="contact-label">Police Emergency</div>
                    <div class="contact-desc">Crime, accidents, security</div>
                </div>
                <div class="contact-card fire">
                    <div class="contact-number">101</div>
                    <div class="contact-label">Fire Services</div>
                    <div class="contact-desc">Fire, rescue, hazmat</div>
                </div>
                <div class="contact-card medical">
                    <div class="contact-number">108</div>
                    <div class="contact-label">Medical Emergency</div>
                    <div class="contact-desc">Medical emergencies, injuries</div>
                </div>
                <div class="contact-card highway">
                    <div class="contact-number">1033</div>
                    <div class="contact-label">Highway Patrol</div>
                    <div class="contact-desc">Highway accidents, breakdowns</div>
                </div>
                <div class="contact-card women">
                    <div class="contact-number">1091</div>
                    <div class="contact-label">Women Helpline</div>
                    <div class="contact-desc">Women in distress</div>
                </div>
                </div>
        </div>
        
        <div class="emergency-services">
            <h3><i class="fas fa-hospital"></i> Emergency Services Along Route</h3>
            <div class="services-summary">
                <div class="service-stat">
                    <span class="service-count">${(services.hospitals || []).length}</span>
                    <span class="service-label">Hospitals</span>
                </div>
                <div class="service-stat">
                    <span class="service-count">${(services.police_stations || []).length}</span>
                    <span class="service-label">Police Stations</span>
                </div>
                <div class="service-stat">
                    <span class="service-count">${(services.fire_stations || []).length}</span>
                    <span class="service-label">Fire Stations</span>
                </div>
            </div>
        </div>
        
        <div class="emergency-checklist">
            <h3><i class="fas fa-clipboard-check"></i> Emergency Preparedness Checklist</h3>
            <div class="checklist-grid">
                <div class="checklist-item">
                    <input type="checkbox" id="first-aid"> <label for="first-aid">First aid kit with medical supplies</label>
                </div>
                <div class="checklist-item">
                    <input type="checkbox" id="emergency-contacts"> <label for="emergency-contacts">Emergency contact numbers saved</label>
                </div>
                <div class="checklist-item">
                    <input type="checkbox" id="vehicle-kit"> <label for="vehicle-kit">Vehicle emergency kit (tools, spare tire)</label>
                </div>
                <div class="checklist-item">
                    <input type="checkbox" id="water-supply"> <label for="water-supply">Emergency water supply (2L minimum)</label>
                </div>
                <div class="checklist-item">
                    <input type="checkbox" id="flashlight"> <label for="flashlight">Flashlight with extra batteries</label>
                </div>
                <div class="checklist-item">
                    <input type="checkbox" id="phone-charger"> <label for="phone-charger">Portable phone charger/power bank</label>
                </div>
            </div>
        </div>
    `;
}

// Populate route map section
function populateRouteMap() {
    const container = document.getElementById('mapContainer');
    
    container.innerHTML = `
        <div class="map-overview">
            <h3><i class="fas fa-map"></i> Comprehensive Route Visualization</h3>
            <p>Interactive route map showing all critical points, emergency services, and hazard zones.</p>
        </div>
        
        <div class="route-map-container">
            <div class="map-placeholder">
                <i class="fas fa-map" style="font-size: 4rem; color: #ccc;"></i>
                <p>Route map will be displayed here</p>
                <p>Loading comprehensive route visualization...</p>
            </div>
        </div>
        
        <div class="map-legend">
            <h3><i class="fas fa-info-circle"></i> Map Legend & Symbol Guide</h3>
            <div class="legend-grid">
                <div class="legend-section">
                    <h4>Critical Safety Markers</h4>
                    <div class="legend-items">
                        <div class="legend-item">
                            <div class="legend-symbol" style="background: #dc3545;">T1-T15</div>
                            <span>Sharp Turns (≥70°)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-symbol" style="background: #6f42c1;">D</div>
                            <span>Network Dead Zones</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-symbol" style="background: #fd7e14;">T</div>
                            <span>Heavy Traffic Areas</span>
                        </div>
                    </div>
                </div>
                <div class="legend-section">
                    <h4>Services & Facilities</h4>
                    <div class="legend-items">
                        <div class="legend-item">
                            <div class="legend-symbol" style="background: #007bff;">H</div>
                            <span>Hospitals</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-symbol" style="background: #007bff;">P</div>
                            <span>Police Stations</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-symbol" style="background: #28a745;">G</div>
                            <span>Gas Stations</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-symbol" style="background: #ffc107;">S</div>
                            <span>Schools (40 km/h)</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Populate traffic analysis section
function populateTrafficAnalysis() {
    const container = document.getElementById('trafficContainer');
    const traffic = reportData.traffic;
    
    if (!traffic || traffic.error) {
        container.innerHTML = `
            <div class="traffic-unavailable">
                <h3><i class="fas fa-info-circle"></i> Traffic Data Status</h3>
                <p>Traffic analysis data is not available for this route. This could be due to:</p>
                <ul>
                    <li>Google Directions API with traffic data not enabled</li>
                    <li>Route analysis completed without traffic information</li>
                    <li>API quota limitations or configuration issues</li>
                </ul>
                <div class="traffic-recommendations">
                    <h4>General Traffic Recommendations:</h4>
                    <ul>
                        <li>Check current traffic conditions before departure</li>
                        <li>Use real-time navigation apps for dynamic route optimization</li>
                        <li>Plan for additional travel time during peak hours</li>
                        <li>Consider alternative routes for heavily congested areas</li>
                    </ul>
                </div>
            </div>
        `;
        return;
    }
    
    const statistics = traffic.statistics || {};
    const congestion = traffic.congestion_analysis || {};
    
    container.innerHTML = `
        <div class="traffic-overview">
            <h3><i class="fas fa-traffic-light"></i> Traffic Conditions Assessment</h3>
            <div class="traffic-score ${getTrafficClass(statistics.overall_traffic_score || 0)}">
                <div class="score">${statistics.overall_traffic_score || 0}/100</div>
                <div class="label">${statistics.traffic_condition || 'Unknown'}</div>
            </div>
        </div>
        
        <div class="traffic-stats">
            <table class="data-table">
                <tr><td><strong>Segments Analyzed</strong></td><td>${statistics.total_segments_analyzed || 0}</td></tr>
                <tr><td><strong>Average Travel Time Index</strong></td><td>${statistics.average_travel_time_index || 0}</td></tr>
                <tr><td><strong>Average Current Speed</strong></td><td>${statistics.average_current_speed || 0} km/h</td></tr>
                <tr><td><strong>Average Free Flow Speed</strong></td><td>${statistics.average_free_flow_speed || 0} km/h</td></tr>
                <tr><td><strong>Heavy Traffic Segments</strong></td><td>${congestion.heavy_traffic_segments || 0}</td></tr>
                <tr><td><strong>Free Flow Segments</strong></td><td>${congestion.free_flow_segments || 0}</td></tr>
            </table>
        </div>
        
        <div class="congestion-analysis">
            <h3><i class="fas fa-chart-bar"></i> Congestion Distribution</h3>
            <div class="congestion-bars">
                ${generateCongestionBars(congestion)}
            </div>
        </div>
        
        <div class="traffic-recommendations">
            <h3><i class="fas fa-route"></i> Traffic-Based Recommendations</h3>
            <ul>
                ${generateTrafficRecommendations(statistics.overall_traffic_score || 0, congestion)}
            </ul>
        </div>
    `;
}

// Populate elevation and terrain section
function populateElevationTerrain() {
    const container = document.getElementById('elevationContainer');
    const elevation = reportData.elevation;
    
    if (!elevation || elevation.error) {
        container.innerHTML = `
            <div class="elevation-unavailable">
                <h3><i class="fas fa-exclamation-triangle"></i> Elevation Data Unavailable</h3>
                <div class="error-details">
                    <p><strong>Error:</strong> ${elevation?.error || 'Elevation analysis data not available'}</p>
                </div>
                <div class="troubleshooting">
                    <h4><i class="fas fa-tools"></i> Troubleshooting Information:</h4>
                    <ul>
                        <li>Check if Google Maps Elevation API is enabled</li>
                        <li>Verify Google Maps API key has elevation permissions</li>
                        <li>Ensure API quota limits have not been exceeded</li>
                        <li>Review application logs for specific API errors</li>
                    </ul>
                </div>
                <div class="general-advice">
                    <h4>General Elevation Considerations:</h4>
                    <ul>
                        <li>Monitor vehicle performance on steep gradients</li>
                        <li>Check engine cooling system for mountain routes</li>
                        <li>Plan additional fuel stops for hilly terrain</li>
                        <li>Use lower gears on steep inclines and declines</li>
                    </ul>
                </div>
            </div>
        `;
        return;
    }
    
    const statistics = elevation.statistics || {};
    const terrainAnalysis = elevation.terrain_analysis || {};
    const significantChanges = elevation.significant_changes || [];
    
    container.innerHTML = `
        <div class="elevation-overview">
            <h3><i class="fas fa-mountain"></i> Elevation & Terrain Analysis</h3>
            <div class="terrain-classification ${getTerrainClass(terrainAnalysis.terrain_type)}">
                <div class="terrain-type">${terrainAnalysis.terrain_type || 'Unknown'}</div>
                <div class="difficulty-level">${terrainAnalysis.driving_difficulty || 'Unknown'} Difficulty</div>
            </div>
        </div>
        
        <div class="elevation-stats">
            <div class="elevation-grid">
                <div class="elevation-stat">
                    <div class="stat-value">${statistics.min_elevation || 0}m</div>
                    <div class="stat-label">Minimum Elevation</div>
                </div>
                <div class="elevation-stat">
                    <div class="stat-value">${statistics.max_elevation || 0}m</div>
                    <div class="stat-label">Maximum Elevation</div>
                </div>
                <div class="elevation-stat">
                    <div class="stat-value">${statistics.average_elevation || 0}m</div>
                    <div class="stat-label">Average Elevation</div>
                </div>
                <div class="elevation-stat">
                    <div class="stat-value">${statistics.elevation_range || 0}m</div>
                    <div class="stat-label">Elevation Range</div>
                </div>
            </div>
        </div>
        
        ${significantChanges.length > 0 ? `
            <div class="elevation-changes">
                <h3><i class="fas fa-chart-line"></i> Significant Elevation Changes</h3>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>Change</th>
                            <th>From (m)</th>
                            <th>To (m)</th>
                            <th>GPS Location</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${significantChanges.slice(0, 10).map(change => `
                            <tr>
                                <td>${change.type || 'Unknown'}</td>
                                <td>${change.elevation_change || 0}m</td>
                                <td>${change.from_elevation || 0}</td>
                                <td>${change.to_elevation || 0}</td>
                                <td>${change.location?.latitude?.toFixed(4) || 0}, ${change.location?.longitude?.toFixed(4) || 0}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        ` : ''}
        
        <div class="terrain-challenges">
            <h3><i class="fas fa-exclamation-circle"></i> Terrain-Based Challenges</h3>
            <div class="fuel-impact">
                <strong>Fuel Consumption Impact:</strong> ${terrainAnalysis.fuel_impact || 'Standard consumption expected'}
            </div>
            <ul>
                ${generateTerrainChallenges(terrainAnalysis.driving_difficulty, statistics.elevation_range || 0)}
            </ul>
        </div>
        
        <div class="vehicle-preparation">
            <h3><i class="fas fa-wrench"></i> Vehicle Preparation Recommendations</h3>
            <ul>
                ${generateElevationPreparation(statistics.elevation_range || 0)}
            </ul>
        </div>
    `;
}

// Setup sidebar navigation
function setupSidebarNavigation() {
    const sidebarLinks = document.querySelectorAll('.sidebar-menu a');
    
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            sidebarLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Scroll to target section
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Update active link on scroll
    window.addEventListener('scroll', updateActiveNavLink);
}

// Update active navigation link based on scroll position
function updateActiveNavLink() {
    const sections = document.querySelectorAll('.report-section');
    const sidebarLinks = document.querySelectorAll('.sidebar-menu a');
    
    let currentSection = '';
    
    sections.forEach(section => {
        const rect = section.getBoundingClientRect();
        if (rect.top <= 100 && rect.bottom >= 100) {
            currentSection = section.id;
        }
    });
    
    sidebarLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${currentSection}`) {
            link.classList.add('active');
        }
    });
}

// Utility functions for generating content

function getCurrentSeason() {
    const month = new Date().getMonth();
    if (month >= 11 || month <= 1) return 'Winter';
    if (month >= 2 && month <= 4) return 'Summer';
    if (month >= 5 && month <= 9) return 'Monsoon';
    return 'Post-Monsoon';
}

function generateSeasonalRows() {
    return `
        <tr>
            <td>Summer</td>
            <td>Highway sections, urban areas</td>
            <td>Extreme heat, vehicle overheating risk</td>
            <td>Check cooling system, carry extra water</td>
        </tr>
        <tr>
            <td>Monsoon</td>
            <td>Ghat sections, low-lying areas</td>
            <td>Waterlogging, reduced visibility, landslides</td>
            <td>Reduce speed, avoid sudden braking</td>
        </tr>
        <tr>
            <td>Winter</td>
            <td>Elevated sections, early morning</td>
            <td>Fog, poor visibility, cold weather</td>
            <td>Use fog lamps, avoid early morning starts</td>
        </tr>
        <tr>
            <td>High Congestion</td>
            <td>Urban centers, toll plazas</td>
            <td>Traffic delays, stop-and-go conditions</td>
            <td>Plan for delays, maintain patience</td>
        </tr>
    `;
}

function getSeasonalRecommendations(season) {
    const recommendations = {
        'Summer': [
            'Check vehicle cooling system before departure',
            'Carry extra water for both vehicle and personal use',
            'Plan travel during cooler hours if possible',
            'Monitor tire pressure regularly in hot weather'
        ],
        'Monsoon': [
            'Check windshield wipers and washer fluid',
            'Ensure all lights are functioning properly',
            'Reduce speed on wet roads',
            'Avoid driving through standing water'
        ],
        'Winter': [
            'Check battery condition for cold weather',
            'Use fog lamps during low visibility',
            'Carry winter emergency kit',
            'Plan for delayed departure times'
        ]
    };
    
    return recommendations[season] || [
        'Follow standard safety precautions',
        'Monitor weather conditions before travel',
        'Ensure vehicle is properly maintained'
    ];
}

function generateCriticalTurnCards(categorizedTurns) {
    const extremeTurns = categorizedTurns.extreme_blind_spots || [];
    const blindSpots = categorizedTurns.blind_spots || [];
    
    let html = '';
    
    [...extremeTurns.slice(0, 3), ...blindSpots.slice(0, 2)].forEach((turn, index) => {
        html += `
            <div class="turn-card">
                <div class="turn-header">
                    <h4><i class="fas fa-exclamation-triangle"></i> Critical Turn #${index + 1}</h4>
                    <div class="turn-angle">${turn.angle}°</div>
                </div>
                <div class="turn-details">
                    <p><strong>Classification:</strong> ${turn.classification}</p>
                    <p><strong>GPS Location:</strong> ${turn.latitude?.toFixed(6)}, ${turn.longitude?.toFixed(6)}</p>
                    <p><strong>Recommended Speed:</strong> ${turn.recommended_speed} km/h</p>
                    <p><strong>Danger Level:</strong> ${turn.danger_level}</p>
                </div>
                <div class="turn-images">
                    <div class="turn-image">
                        <div class="image-placeholder">
                            <i class="fas fa-camera"></i>
                            <p>Street View</p>
                        </div>
                        <div class="turn-image-caption">Driver's perspective view</div>
                    </div>
                    <div class="turn-image">
                        <div class="image-placeholder">
                            <i class="fas fa-satellite"></i>
                            <p>Satellite View</p>
                        </div>
                        <div class="turn-image-caption">Aerial perspective view</div>
                    </div>
                </div>
            </div>
        `;
    });
    
    return html || '<p>No critical turns data available</p>';
}

function generatePOICategories(poisByType) {
    const categories = [
        { key: 'hospitals', name: 'Medical Facilities', icon: 'fas fa-hospital', color: '#dc3545', priority: 'CRITICAL' },
        { key: 'police', name: 'Law Enforcement', icon: 'fas fa-shield-alt', color: '#0052a3', priority: 'CRITICAL' },
        { key: 'fire_stations', name: 'Fire & Rescue', icon: 'fas fa-fire-extinguisher', color: '#fd7e14', priority: 'CRITICAL' },
        { key: 'gas_stations', name: 'Fuel Stations', icon: 'fas fa-gas-pump', color: '#28a745', priority: 'ESSENTIAL' },
        { key: 'schools', name: 'Educational Institutions', icon: 'fas fa-school', color: '#ffc107', priority: 'AWARENESS' },
        { key: 'restaurants', name: 'Food & Rest', icon: 'fas fa-utensils', color: '#17a2b8', priority: 'CONVENIENCE' }
    ];
    
    let html = '<div class="poi-grid">';
    
    categories.forEach(category => {
        const pois = poisByType[category.key] || [];
        html += `
            <div class="poi-card">
                <div class="poi-header">
                    <div class="poi-icon" style="background-color: ${category.color};">
                        <i class="${category.icon}"></i>
                    </div>
                    <div>
                        <h4>${category.name}</h4>
                        <span class="poi-priority">${category.priority}</span>
                    </div>
                </div>
                <div class="poi-count">
                    <span class="count">${pois.length}</span>
                    <span class="label">facilities found</span>
                </div>
                <div class="poi-list">
                    ${pois.slice(0, 3).map(poi => `
                        <div class="poi-item">
                            <strong>${truncateText(poi.name || 'Unknown', 25)}</strong>
                            <small>${truncateText(poi.address || 'Unknown location', 30)}</small>
                        </div>
                    `).join('')}
                    ${pois.length > 3 ? `<small>...and ${pois.length - 3} more</small>` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function generateQualityBars(qualityDist, totalPoints) {
    const qualities = [
        { key: 'excellent', label: 'Excellent', color: '#28a745' },
        { key: 'good', label: 'Good', color: '#17a2b8' },
        { key: 'fair', label: 'Fair', color: '#ffc107' },
        { key: 'poor', label: 'Poor', color: '#fd7e14' },
        { key: 'dead', label: 'Dead Zone', color: '#dc3545' }
    ];
    
    let html = '';
    
    qualities.forEach(quality => {
        const count = qualityDist[quality.key] || 0;
        const percentage = totalPoints > 0 ? (count / totalPoints * 100) : 0;
        
        html += `
            <div class="quality-bar">
                <div class="quality-label">
                    <span>${quality.label}</span>
                    <span>${count} (${percentage.toFixed(1)}%)</span>
                </div>
                <div class="quality-progress">
                    <div class="quality-fill" style="width: ${percentage}%; background-color: ${quality.color};"></div>
                </div>
            </div>
        `;
    });
    
    return html;
}

function generateWeatherConditions(conditions, totalPoints) {
    let html = '';
    
    Object.entries(conditions).forEach(([condition, count]) => {
        const percentage = totalPoints > 0 ? (count / totalPoints * 100) : 0;
        const iconClass = getWeatherIcon(condition);
        
        html += `
            <div class="weather-condition-card">
                <div class="weather-icon">
                    <i class="${iconClass}"></i>
                </div>
                <div class="weather-info">
                    <h4>${condition}</h4>
                    <p>${count} points (${percentage.toFixed(1)}%)</p>
                </div>
            </div>
        `;
    });
    
    return html;
}

function generateWeatherPreparation(avgTemp, conditions) {
    let preparations = [];
    
    if (avgTemp > 35) {
        preparations.push('<li>Check engine cooling system and radiator fluid levels</li>');
        preparations.push('<li>Ensure air conditioning is functioning properly</li>');
        preparations.push('<li>Carry extra water for radiator and personal hydration</li>');
    }
    
    if (avgTemp < 10) {
        preparations.push('<li>Check battery condition (cold weather reduces capacity)</li>');
        preparations.push('<li>Ensure proper engine oil viscosity for cold weather</li>');
        preparations.push('<li>Check tire tread depth for wet/icy conditions</li>');
    }
    
    if (Object.keys(conditions).some(c => c.includes('Rain') || c.includes('Storm'))) {
        preparations.push('<li>Check windshield wipers and washer fluid</li>');
        preparations.push('<li>Ensure headlights and taillights are functioning</li>');
        preparations.push('<li>Check tire tread depth for wet road traction</li>');
    }
    
    if (preparations.length === 0) {
        preparations.push('<li>Standard vehicle maintenance check recommended</li>');
        preparations.push('<li>Ensure all fluid levels are adequate</li>');
        preparations.push('<li>Check tire condition and pressure</li>');
    }
    
    return preparations.join('');
}

function generateCongestionBars(congestion) {
    const segments = [
        { key: 'free_flow_segments', label: 'Free Flow', color: '#28a745' },
        { key: 'light_traffic_segments', label: 'Light Traffic', color: '#17a2b8' },
        { key: 'moderate_traffic_segments', label: 'Moderate Traffic', color: '#ffc107' },
        { key: 'heavy_traffic_segments', label: 'Heavy Traffic', color: '#dc3545' }
    ];
    
    const total = Object.values(congestion).reduce((sum, val) => sum + (val || 0), 0);
    
    let html = '';
    
    segments.forEach(segment => {
        const count = congestion[segment.key] || 0;
        const percentage = total > 0 ? (count / total * 100) : 0;
        
        html += `
            <div class="congestion-bar">
                <div class="congestion-label">
                    <span>${segment.label}</span>
                    <span>${count} segments (${percentage.toFixed(1)}%)</span>
                </div>
                <div class="congestion-progress">
                    <div class="congestion-fill" style="width: ${percentage}%; background-color: ${segment.color};"></div>
                </div>
            </div>
        `;
    });
    
    return html;
}

function generateTrafficRecommendations(trafficScore, congestion) {
    let recommendations = [];
    
    const heavySegments = congestion.heavy_traffic_segments || 0;
    const moderateSegments = congestion.moderate_traffic_segments || 0;
    
    if (heavySegments > 0) {
        recommendations.push(`<li>Route has ${heavySegments} heavily congested segments - consider alternative routes</li>`);
        recommendations.push('<li>Plan for significant delays during peak hours</li>');
    }
    
    if (moderateSegments > 0) {
        recommendations.push(`<li>${moderateSegments} segments have moderate traffic - allow extra travel time</li>`);
    }
    
    if (trafficScore < 50) {
        recommendations.push('<li>Consider traveling during off-peak hours to avoid traffic</li>');
        recommendations.push('<li>Use real-time navigation apps for dynamic route optimization</li>');
    }
    
    recommendations.push('<li>Check current traffic conditions before departure</li>');
    recommendations.push('<li>Plan rest stops during low-traffic segments</li>');
    
    return recommendations.join('');
}

function generateTerrainChallenges(difficulty, elevationRange) {
    let challenges = [];
    
    if (difficulty === 'HIGH' || elevationRange > 1000) {
        challenges.push('<li>Steep gradients requiring low gear driving and engine braking</li>');
        challenges.push('<li>Increased fuel consumption due to elevation changes</li>');
        challenges.push('<li>Potential engine overheating on long climbs</li>');
        challenges.push('<li>Brake wear due to frequent downhill braking</li>');
    } else if (difficulty === 'MEDIUM' || elevationRange > 500) {
        challenges.push('<li>Moderate gradients affecting fuel efficiency</li>');
        challenges.push('<li>Some engine strain on uphill sections</li>');
        challenges.push('<li>Occasional brake usage on downhill sections</li>');
    } else {
        challenges.push('<li>Minimal elevation changes with flat terrain</li>');
        challenges.push('<li>Normal fuel consumption expected</li>');
        challenges.push('<li>Standard vehicle performance throughout</li>');
    }
    
    return challenges.join('');
}

function generateElevationPreparation(elevationRange) {
    let preparations = [];
    
    if (elevationRange > 1000) {
        preparations.push('<li>Check engine cooling system - radiator, coolant levels, and fans</li>');
        preparations.push('<li>Inspect brake system - pads, fluid, and brake lines condition</li>');
        preparations.push('<li>Verify transmission fluid for proper gear shifting</li>');
        preparations.push('<li>Ensure fuel tank is full - higher consumption expected</li>');
        preparations.push('<li>Carry emergency coolant and brake fluid</li>');
    } else if (elevationRange > 500) {
        preparations.push('<li>Check cooling system and fluid levels</li>');
        preparations.push('<li>Inspect brake system condition</li>');
        preparations.push('<li>Verify fuel level and plan refueling stops</li>');
    } else {
        preparations.push('<li>Standard vehicle maintenance check sufficient</li>');
        preparations.push('<li>Normal fuel planning adequate</li>');
    }
    
    return preparations.join('');
}

// Utility functions for styling classes

function getStatusClass(score) {
    if (score >= 80) return 'status-excellent';
    if (score >= 60) return 'status-good';
    if (score >= 40) return 'status-moderate';
    return 'status-poor';
}

function getScoreLabel(score) {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Moderate';
    return 'Poor';
}

function getRiskClass(riskLevel) {
    switch (riskLevel?.toLowerCase()) {
        case 'critical':
        case 'high':
            return 'status-poor';
        case 'medium':
        case 'moderate':
            return 'status-moderate';
        case 'low':
            return 'status-good';
        default:
            return 'status-moderate';
    }
}

function getRiskDescription(riskLevel) {
    switch (riskLevel?.toLowerCase()) {
        case 'critical':
            return 'Immediate attention required';
        case 'high':
            return 'High caution advised';
        case 'medium':
        case 'moderate':
            return 'Standard precautions';
        case 'low':
            return 'Minimal risk detected';
        default:
            return 'Risk assessment pending';
    }
}

function getTurnsClass(criticalTurns) {
    if (criticalTurns === 0) return 'status-excellent';
    if (criticalTurns <= 2) return 'status-good';
    if (criticalTurns <= 5) return 'status-moderate';
    return 'status-poor';
}

function getTurnsLabel(criticalTurns) {
    if (criticalTurns === 0) return 'No critical turns';
    if (criticalTurns <= 2) return 'Few critical turns';
    if (criticalTurns <= 5) return 'Moderate concern';
    return 'High attention needed';
}

function getComplianceClass(score) {
    if (score >= 80) return 'status-excellent';
    if (score >= 60) return 'status-moderate';
    return 'status-poor';
}

function getServiceClass(score) {
    if (score >= 80) return 'status-excellent';
    if (score >= 60) return 'status-good';
    if (score >= 40) return 'status-moderate';
    return 'status-poor';
}

function getCoverageClass(score) {
    if (score >= 85) return 'status-excellent';
    if (score >= 70) return 'status-good';
    if (score >= 50) return 'status-moderate';
    return 'status-poor';
}

function getTrafficClass(score) {
    if (score >= 80) return 'status-excellent';
    if (score >= 60) return 'status-good';
    if (score >= 40) return 'status-moderate';
    return 'status-poor';
}

function getTerrainClass(terrainType) {
    switch (terrainType?.toLowerCase()) {
        case 'plains':
            return 'status-excellent';
        case 'hilly':
        case 'high_plateau':
            return 'status-moderate';
        case 'mountainous':
            return 'status-poor';
        default:
            return 'status-good';
    }
}

function getEmergencyClass(score) {
    if (score >= 80) return 'status-excellent';
    if (score >= 60) return 'status-good';
    return 'status-poor';
}

function getWeatherIcon(condition) {
    const iconMap = {
        'clear': 'fas fa-sun',
        'sunny': 'fas fa-sun',
        'clouds': 'fas fa-cloud',
        'cloudy': 'fas fa-cloud',
        'rain': 'fas fa-cloud-rain',
        'drizzle': 'fas fa-cloud-drizzle',
        'thunderstorm': 'fas fa-bolt',
        'snow': 'fas fa-snowflake',
        'mist': 'fas fa-smog',
        'fog': 'fas fa-smog',
        'haze': 'fas fa-smog'
    };
    
    const key = condition.toLowerCase();
    return iconMap[key] || 'fas fa-cloud';
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Download PDF function
function downloadPDF() {
    if (currentRouteId) {
        window.open(`/api/pdf/${currentRouteId}?pages=all`, '_blank');
    } else {
        alert('No route selected for PDF download');
    }
}

// Mobile sidebar toggle
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('active');
}

// Add mobile menu button if screen is small
function addMobileMenuButton() {
    if (window.innerWidth <= 768) {
        const nav = document.querySelector('.nav-container');
        const menuButton = document.createElement('button');
        menuButton.innerHTML = '<i class="fas fa-bars"></i>';
        menuButton.className = 'mobile-menu-btn';
        menuButton.onclick = toggleSidebar;
        nav.insertBefore(menuButton, nav.firstChild);
    }
}

// Initialize mobile features
window.addEventListener('resize', addMobileMenuButton);
document.addEventListener('DOMContentLoaded', addMobileMenuButton);

// Smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', function() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Print functionality
function printReport() {
    window.print();
}

// Add print styles dynamically
function addPrintStyles() {
    const printStyles = `
        @media print {
            .report-nav, .sidebar { display: none !important; }
            .main-content { margin-left: 0 !important; max-width: 100% !important; }
            .report-section { page-break-inside: avoid; margin-bottom: 1rem; }
            .section-header { background: #000 !important; color: #fff !important; }
            .status-indicator { page-break-inside: avoid; }
            .turn-card, .poi-card, .risk-zone-card { page-break-inside: avoid; }
        }
    `;
    
    const style = document.createElement('style');
    style.textContent = printStyles;
    document.head.appendChild(style);
}

// Initialize print styles
document.addEventListener('DOMContentLoaded', addPrintStyles);

// Error handling for failed API calls
function handleApiError(endpoint, error) {
    console.error(`API Error for ${endpoint}:`, error);
    
    // Show user-friendly error message
    const errorContainer = document.createElement('div');
    errorContainer.className = 'api-error';
    errorContainer.innerHTML = `
        <div class="error-content">
            <i class="fas fa-exclamation-triangle"></i>
            <h4>Data Loading Error</h4>
            <p>Failed to load ${endpoint} data. Please refresh the page or contact support.</p>
        </div>
    `;
    
    return errorContainer;
}

// Add loading states for sections
function showSectionLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="section-loading">
                <div class="loading-spinner-small"></div>
                <p>Loading data...</p>
            </div>
        `;
    }
}

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Format date strings
function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch (error) {
        return dateString;
    }
}

// Export functions for global use
window.initializeReport = initializeReport;
window.downloadPDF = downloadPDF;
window.printReport = printReport;
window.toggleSidebar = toggleSidebar;