const API_BASE = 'http://localhost:8000/api/asteroids';

let state = {
    asteroidsByDate: {},
    flatAsteroids: [],
    stats: {},
    selectedAsteroid: null,
    sortBy: 'risk',
    startDate: '',
    endDate: ''
};

const startDateInput = document.getElementById('start-date-input');
const endDateInput = document.getElementById('end-date-input');
const updateBtn = document.getElementById('update-btn');
const simThreatBtn = document.getElementById('sim-threat-btn');
const btnText = document.getElementById('btn-text');
const loader = document.getElementById('loader');
const noDataMsg = document.getElementById('no-data-msg');
const asteroidList = document.getElementById('asteroid-list');
const inspectorPlaceholder = document.getElementById('inspector-placeholder');
const inspectorDetails = document.getElementById('inspector-details');
const sortBySelect = document.getElementById('sort-by');

const statTotal = document.getElementById('stat-total');
const statHazard = document.getElementById('stat-hazard');
const statMaxScore = document.getElementById('stat-max-score');
const statMaxName = document.getElementById('stat-max-name');
const statAvgSpeed = document.getElementById('stat-avg-speed');

document.addEventListener('DOMContentLoaded', () => {
    initDefaultDates();
    setupEventListeners();
    fetchTelemetry();
});

function initDefaultDates() {
    const today = new Date();
    const future = new Date();
    future.setDate(today.getDate() + 6);

    state.startDate = formatDate(today);
    state.endDate = formatDate(future);

    startDateInput.value = state.startDate;
    endDateInput.value = state.endDate;
    
    startDateInput.max = state.endDate;
    endDateInput.min = state.startDate;
}

function setupEventListeners() {
    startDateInput.addEventListener('change', (e) => {
        state.startDate = e.target.value;
        endDateInput.min = state.startDate;
    });

    endDateInput.addEventListener('change', (e) => {
        state.endDate = e.target.value;
        startDateInput.max = state.endDate;
    });

    updateBtn.addEventListener('click', () => fetchTelemetry());
    
    simThreatBtn.addEventListener('click', () => injectCriticalThreat());
    
    sortBySelect.addEventListener('change', (e) => {
        state.sortBy = e.target.value;
        renderAsteroidList();
    });
}

async function fetchTelemetry() {
    toggleLoader(true);
    clearInspector();

    try {
        const queryParams = `?start_date=${state.startDate}&end_date=${state.endDate}`;
        
        const listResponse = await fetch(`${API_BASE}${queryParams}`);
        if (!listResponse.ok) {
            const err = await listResponse.json();
            throw new Error(err.detail || 'Failed to fetch telemetry data.');
        }
        state.asteroidsByDate = await listResponse.json();
        
        state.flatAsteroids = [];
        Object.keys(state.asteroidsByDate).forEach(date => {
            state.flatAsteroids.push(...state.asteroidsByDate[date]);
        });

        const statsResponse = await fetch(`${API_BASE}/stats${queryParams}`);
        if (statsResponse.ok) {
            state.stats = await statsResponse.json();
            renderStats(state.stats);
        } else {
            calculateClientStats();
        }

        renderAsteroidList();

    } catch (err) {
        console.error(err);
        showErrorToast(err.message);
        state.flatAsteroids = [];
        renderAsteroidList();
        renderStats({
            total_tracked: 0,
            hazardous_count: 0,
            max_hazard_score: 0,
            max_hazard_asteroid: null,
            average_diameter_meters: 0,
            average_velocity_km_h: 0,
            danger_levels: {}
        });
    } finally {
        toggleLoader(false);
    }
}

function renderStats(stats) {
    animateCount(statTotal, stats.total_tracked);
    animateCount(statHazard, stats.hazardous_count);
    
    const scoreVal = stats.max_hazard_score || 0;
    statMaxScore.textContent = scoreVal.toFixed(2);
    
    const scoreCard = document.getElementById('stat-risk-card');
    scoreCard.className = 'stat-card glass';
    if (scoreVal >= 7.0) scoreCard.classList.add('border-red');
    else if (scoreVal >= 4.0) scoreCard.classList.add('border-orange');
    else if (scoreVal >= 2.0) scoreCard.classList.add('border-yellow');
    else scoreCard.classList.add('border-cyan');

    if (stats.max_hazard_asteroid) {
        statMaxName.textContent = stats.max_hazard_asteroid.name;
    } else {
        statMaxName.textContent = "None Detected";
    }

    animateCount(statAvgSpeed, Math.round(stats.average_velocity_km_h), " km/h");
}

function calculateClientStats() {
    const count = state.flatAsteroids.length;
    if (count === 0) {
        renderStats({
            total_tracked: 0,
            hazardous_count: 0,
            max_hazard_score: 0,
            max_hazard_asteroid: null,
            average_diameter_meters: 0,
            average_velocity_km_h: 0
        });
        return;
    }

    const hazardous = state.flatAsteroids.filter(a => a.is_potentially_hazardous).length;
    const maxAst = state.flatAsteroids.reduce((max, cur) => 
        (cur.risk_assessment.hazard_score > max.risk_assessment.hazard_score) ? cur : max, 
        state.flatAsteroids[0]
    );
    const avgVelocity = state.flatAsteroids.reduce((sum, cur) => sum + cur.velocity_km_h, 0) / count;
    
    renderStats({
        total_tracked: count,
        hazardous_count: hazardous,
        max_hazard_score: maxAst.risk_assessment.hazard_score,
        max_hazard_asteroid: maxAst,
        average_velocity_km_h: avgVelocity
    });
}

function renderAsteroidList() {
    asteroidList.innerHTML = '';
    
    if (state.flatAsteroids.length === 0) {
        noDataMsg.classList.remove('hide');
        return;
    }
    
    noDataMsg.classList.add('hide');

    const sorted = [...state.flatAsteroids].sort((a, b) => {
        if (state.sortBy === 'risk') {
            return b.risk_assessment.hazard_score - a.risk_assessment.hazard_score;
        } else if (state.sortBy === 'distance') {
            return a.miss_distance_km - b.miss_distance_km;
        } else if (state.sortBy === 'size') {
            const sizeA = (a.diameter_min_meters + a.diameter_max_meters) / 2;
            const sizeB = (b.diameter_min_meters + b.diameter_max_meters) / 2;
            return sizeB - sizeA;
        } else if (state.sortBy === 'velocity') {
            return b.velocity_km_h - a.velocity_km_h;
        }
        return 0;
    });

    sorted.forEach(ast => {
        const card = createAsteroidCard(ast);
        asteroidList.appendChild(card);
    });
}

const RISK_TOOLTIPS = {
    minimal: "No threat. Routine orbital pass.",
    low: "Small chance of concern. Monitoring advised.",
    moderate: "Notable proximity. Radar tracking active.",
    high: "Serious threat. Agency alert issued.",
    critical: "Collision likely. Global emergency protocol."
};

function createAsteroidCard(ast) {
    const dangerLvl = ast.risk_assessment.danger_level.toLowerCase();
    const card = document.createElement('div');
    card.className = `asteroid-card ${dangerLvl} ${state.selectedAsteroid && state.selectedAsteroid.id === ast.id ? 'selected' : ''}`;
    card.setAttribute('data-id', ast.id);
    
    const avgDia = (ast.diameter_min_meters + ast.diameter_max_meters) / 2;
    const scoreVal = ast.risk_assessment.hazard_score;
    const tooltipText = RISK_TOOLTIPS[dangerLvl] || '';

    card.innerHTML = `
        <div class="card-details-left">
            <div class="ast-card-info">
                <div class="ast-name">${ast.name}</div>
                <div class="ast-sub-telemetry">
                    <span>SIZE: ${Math.round(avgDia)}M</span>
                    <span>VELOCITY: ${formatVelocity(ast.velocity_km_h)}</span>
                    <span>DISTANCE: ${formatDistance(ast.miss_distance_km)}</span>
                </div>
            </div>
        </div>
        <div class="card-details-right">
            <span class="badge badge-${dangerLvl}" data-tooltip="${tooltipText}">${ast.risk_assessment.danger_level}</span>
            <span class="risk-score-text font-mono">SCORE: ${scoreVal.toFixed(1)}</span>
        </div>
    `;

    card.addEventListener('click', () => selectAsteroid(ast));
    return card;
}

function selectAsteroid(ast) {
    state.selectedAsteroid = ast;
    
    document.querySelectorAll('.asteroid-card').forEach(card => {
        if (card.getAttribute('data-id') === ast.id) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    });

    inspectorPlaceholder.classList.add('hide');
    inspectorDetails.classList.remove('hide');

    const avgDia = (ast.diameter_min_meters + ast.diameter_max_meters) / 2;
    const dangerLvl = ast.risk_assessment.danger_level.toLowerCase();
    
    const isHazardous = ast.is_potentially_hazardous;
    const threatBadgeClass = isHazardous ? 'hazardous' : '';
    const threatBadgeText = isHazardous ? 'NASA HAZARD CLASSIFIED' : 'NASA REGULAR ORBIT';
    
    const radius = avgDia / 2;
    const volume = (4/3) * Math.PI * Math.pow(radius, 3);
    const massKg = volume * 3000;
    
    const velMps = (ast.velocity_km_h * 1000) / 3600;
    const energyJoules = 0.5 * massKg * Math.pow(velMps, 2);
    const energyMegatons = energyJoules / 4.184e15;

    inspectorDetails.innerHTML = `
        <div class="inspector-header">
            <div class="inspector-title-area">
                <h2>${ast.name}</h2>
                <div class="ast-id">NASA REFERENCE ID: ${ast.id.split('_')[0]}</div>
                <div class="danger-box">
                    <span class="badge badge-${dangerLvl}" data-tooltip="${RISK_TOOLTIPS[dangerLvl] || ''}">${ast.risk_assessment.danger_level} RISK</span>
                    <span class="badge hazard-badge-nasa ${threatBadgeClass}">${threatBadgeText}</span>
                </div>
            </div>
        </div>

        <div class="risk-description-card ${dangerLvl}">
            <h4>RISK_ASSESSMENT_REPORT</h4>
            <p>${ast.risk_assessment.description}</p>
        </div>

        <div class="telemetry-grid">
            <div class="telemetry-item">
                <div class="telemetry-label">ESTIMATED_SIZE</div>
                <div class="telemetry-value">${Math.round(ast.diameter_min_meters)} - ${Math.round(ast.diameter_max_meters)} m</div>
            </div>
            
            <div class="telemetry-item">
                <div class="telemetry-label">ORBITAL_VELOCITY</div>
                <div class="telemetry-value">${formatVelocity(ast.velocity_km_h)} <span style="font-size:0.7rem; color:var(--color-text-muted);">(${Math.round(velMps/1000*10)/10} km/s)</span></div>
            </div>
            
            <div class="telemetry-item">
                <div class="telemetry-label">CLOSEST_APPROACH</div>
                <div class="telemetry-value">${ast.close_approach_date}</div>
            </div>
            
            <div class="telemetry-item">
                <div class="telemetry-label">MISS_DISTANCE</div>
                <div class="telemetry-value">${formatDistance(ast.miss_distance_km)} <span style="font-size:0.7rem; color:var(--color-text-muted);">(${Math.round(ast.miss_distance_km/384400*10)/10} LD)</span></div>
            </div>
        </div>

        <div class="physics-container">
            <h3>ORBITAL_PHYSICS_AND_DANGER_ANALYTICS</h3>
            <div class="physics-scores-row">
                <div class="physics-score-item">
                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <span class="physics-score-label">Hazard Score</span>
                        <span class="physics-score-text text-cyan">${ast.risk_assessment.hazard_score.toFixed(2)} / 10</span>
                    </div>
                    <div class="physics-score-bar-bg">
                        <div class="physics-score-bar-fill bg-cyan" id="hazard-score-fill"></div>
                    </div>
                </div>
                
                <div class="physics-score-item">
                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <span class="physics-score-label">Torino Scale</span>
                        <span class="physics-score-text text-orange">${ast.risk_assessment.torino_scale} / 10</span>
                    </div>
                    <div class="physics-score-bar-bg">
                        <div class="physics-score-bar-fill bg-orange" id="torino-scale-fill"></div>
                    </div>
                </div>
            </div>
            
            <div class="physics-details-extended">
                <div>
                    <span>Est. Mass:</span> 
                    <span>${formatMass(massKg)}</span>
                </div>
                <div>
                    <span>Collision Prob:</span> 
                    <span>${ast.risk_assessment.impact_probability.toExponential(2)}</span>
                </div>
                <div style="grid-column: span 2;">
                    <span>Kinetic Impact Energy:</span> 
                    <span>${formatEnergy(energyMegatons)}</span>
                </div>
            </div>
        </div>
    `;

    setTimeout(() => {
        const hazardFill = document.getElementById('hazard-score-fill');
        const torinoFill = document.getElementById('torino-scale-fill');
        if (hazardFill) hazardFill.style.width = `${ast.risk_assessment.hazard_score * 10}%`;
        if (torinoFill) torinoFill.style.width = `${ast.risk_assessment.torino_scale * 10}%`;
    }, 50);
}

function clearInspector() {
    state.selectedAsteroid = null;
    inspectorPlaceholder.classList.remove('hide');
    inspectorDetails.classList.add('hide');
}

function injectCriticalThreat() {
    const checkId = "2026CRIT_SIM";
    if (state.flatAsteroids.some(a => a.id === checkId)) {
        const existing = state.flatAsteroids.find(a => a.id === checkId);
        selectAsteroid(existing);
        return;
    }

    const threatAsteroid = {
        id: checkId,
        name: "99999 Apophis-X (Critical Threat Sim)",
        diameter_min_meters: 1400.0,
        diameter_max_meters: 1850.0,
        is_potentially_hazardous: true,
        close_approach_date: state.startDate,
        epoch_date_close_approach: Date.now(),
        velocity_km_h: 148300.0,
        miss_distance_km: 18200.0,
        orbiting_body: "Earth",
        risk_assessment: {
            hazard_score: 9.85,
            torino_scale: 10,
            impact_probability: 0.048,
            danger_level: "CRITICAL",
            description: "CRITICAL COLLISION ALERT. Simulating a 1.6km diameter asteroid passing within 18,200km of Earth surface (inside geostationary communication satellite orbit ring). Approximated impact velocity of 148,300 km/h with an estimated kinetic impact payload of 350,000 Megatons of TNT (roughly 23 million Hiroshima devices). Torino Scale hazard rating 10. Global planetary threat context activated."
        }
    };

    state.flatAsteroids.unshift(threatAsteroid);
    
    calculateClientStats();
    
    renderAsteroidList();
    selectAsteroid(threatAsteroid);
    
    showErrorToast("WARNING: Critical Asteroid Collision Threat Simulated!");
}

function toggleLoader(show) {
    if (show) {
        loader.classList.remove('hide');
        asteroidList.classList.add('hide');
        noDataMsg.classList.add('hide');
        updateBtn.disabled = true;
        btnText.textContent = "SYNCING...";
    } else {
        loader.classList.add('hide');
        asteroidList.classList.remove('hide');
        updateBtn.disabled = false;
        btnText.textContent = "SYNC_TELEMETRY";
    }
}

function formatDate(date) {
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
}

function formatVelocity(vel) {
    return `${Math.round(vel).toLocaleString()} km/h`;
}

function formatDistance(dist) {
    if (dist < 1000000) {
        return `${Math.round(dist).toLocaleString()} km`;
    }
    const milKm = dist / 1000000;
    return `${milKm.toFixed(2)}M km`;
}

function formatMass(mass) {
    if (mass >= 1e12) return `${(mass/1e12).toFixed(2)}T kg (Trillion)`;
    if (mass >= 1e9) return `${(mass/1e9).toFixed(2)}B kg (Billion)`;
    if (mass >= 1e6) return `${(mass/1e6).toFixed(2)}M kg (Million)`;
    return `${Math.round(mass).toLocaleString()} kg`;
}

function formatEnergy(mt) {
    if (mt >= 1e6) return `${(mt/1e6).toFixed(2)}M MT (Million Megatons of TNT)`;
    if (mt >= 1e3) return `${(mt/1e3).toFixed(2)}K MT (Thousand Megatons of TNT)`;
    return `${mt.toFixed(1)} MT (Megatons of TNT)`;
}

function animateCount(element, target, suffix = '') {
    if (isNaN(target)) {
        element.textContent = target + suffix;
        return;
    }
    
    const duration = 800;
    const startTime = performance.now();
    const startVal = 0;
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const easeProgress = progress * (2 - progress);
        const currentVal = Math.round(startVal + easeProgress * (target - startVal));
        
        element.textContent = currentVal.toLocaleString() + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = target.toLocaleString() + suffix;
        }
    }
    
    requestAnimationFrame(update);
}

function showErrorToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-flat';
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.padding = '0.8rem 1.5rem';
    toast.style.backgroundColor = 'var(--color-bg-card)';
    toast.style.border = '1px solid var(--color-border)';
    toast.style.borderLeft = '3px solid var(--color-orange)';
    toast.style.color = '#fff';
    toast.style.fontSize = '0.8rem';
    toast.style.fontFamily = 'var(--font-mono)';
    toast.style.zIndex = '1000';
    toast.style.transition = 'opacity 0.5s ease-out';
    toast.innerHTML = `ALERT: ${message}`;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 500);
    }, 4500);
}
