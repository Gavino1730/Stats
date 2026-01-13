// Trends Page JavaScript
let teamCharts = {};
let playerCharts = {};
let allPlayers = [];
let currentTrendsData = null;
let comprehensiveInsights = null;

// Clean AI response text (removes markdown symbols)
function formatAIResponse(text) {
    return text
        // Remove headers (### Header -> Header)
        .replace(/^#{1,6}\s+(.+)$/gm, '$1')
        // Remove bold markers (**text** or __text__ -> text)
        .replace(/\*\*(.+?)\*\*/g, '$1')
        .replace(/__(.+?)__/g, '$1')
        // Remove italic markers (*text* or _text_ -> text)
        .replace(/\*(.+?)\*/g, '$1')
        .replace(/_(.+?)_/g, '$1')
        // Clean up bullet points
        .replace(/^[•\-\*]\s+/gm, '• ')
        // Convert line breaks
        .replace(/\n/g, '<br>');
}

document.addEventListener('DOMContentLoaded', async () => {
    // Load data in parallel for faster page interaction
    await Promise.all([
        loadPlayers(),
        loadTeamTrends(),
        loadVolatilityStats(),
        loadComprehensiveInsights()
    ]);
    setupTabs();
    // Don't set up player/comparison selectors yet - they're in hidden tabs
});

async function loadPlayers() {
    try {
        const response = await fetch('/api/players');
        allPlayers = await response.json();
    } catch (error) {
        console.error('Error loading players:', error);
    }
}

async function loadComprehensiveInsights() {
    try {
        const response = await fetch('/api/comprehensive-insights');
        comprehensiveInsights = await response.json();
        console.log('Loaded comprehensive insights:', comprehensiveInsights);
    } catch (error) {
        console.error('Error loading comprehensive insights:', error);
    }
}

async function loadVolatilityStats() {
    try {
        const response = await fetch('/api/advanced/volatility');
        const data = await response.json();
        
        document.getElementById('ppg-range').textContent = data.team_volatility.ppg_range;
        document.getElementById('fg-std').textContent = data.team_volatility.fg_pct_std_dev.toFixed(1) + '%';
        document.getElementById('to-std').textContent = data.team_volatility.to_std_dev.toFixed(1);
    } catch (error) {
        console.error('Error loading volatility stats:', error);
    }
}

function setupPlayerSelector() {
    const select = document.getElementById('playerSelect');
    
    if (!select) {
        console.error('playerSelect element not found');
        return;
    }
    
    // Clear existing options except the first one
    while (select.options.length > 1) {
        select.remove(1);
    }
    
    allPlayers.forEach(player => {
        const option = document.createElement('option');
        option.value = player.name;  // Use abbreviated name for API
        option.textContent = (player.full_name || player.name).split(' ')[0];  // Display first name only
        select.appendChild(option);
    });

    select.addEventListener('change', async (e) => {
        if (e.target.value) {
            await loadPlayerTrends(e.target.value);
        }
    });
}

async function loadTeamTrends() {
    try {
        const response = await fetch('/api/team-trends');
        const trends = await response.json();
        currentTrendsData = trends;  // Store for AI analysis
        
        // Sort by date to ensure chronological order
        const gameIds = trends.games;
        const sortedIndices = gameIds.map((_, i) => i).sort((a, b) => {
            const dateA = new Date(trends.dates[a]);
            const dateB = new Date(trends.dates[b]);
            return dateA - dateB;
        });
        
        const sortedOpp = sortedIndices.map(i => trends.opponents[i]);
        const sortedVcScore = sortedIndices.map(i => trends.vc_score[i]);
        const sortedOppScore = sortedIndices.map(i => trends.opp_score[i]);
        const sortedFgPct = sortedIndices.map(i => trends.fg_pct[i]);
        const sortedFg3Pct = sortedIndices.map(i => trends.fg3_pct[i]);
        const sortedAsst = sortedIndices.map(i => trends.asst[i]);
        const sortedTo = sortedIndices.map(i => trends.to[i]);

        // Scoring Chart
        const scoringCtx = document.getElementById('teamScoringChart').getContext('2d');
        if (teamCharts.scoring) teamCharts.scoring.destroy();
        teamCharts.scoring = new Chart(scoringCtx, {
            type: 'line',
            data: {
                labels: sortedOpp,
                datasets: [
                    {
                        label: 'Valley Catholic',
                        data: sortedVcScore,
                        borderColor: '#4169E1',
                        backgroundColor: 'rgba(65, 105, 225, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 6,
                        pointBackgroundColor: '#4169E1',
                        pointHoverRadius: 8
                    },
                    {
                        label: 'Opponents',
                        data: sortedOppScore,
                        borderColor: '#808080',
                        backgroundColor: 'rgba(128, 128, 128, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 6,
                        pointBackgroundColor: '#808080',
                        pointHoverRadius: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.85)',
                        padding: 12,
                        titleFont: { size: 12, weight: 'bold' },
                        bodyFont: { size: 11 },
                        borderColor: '#4169E1',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y.toFixed(1);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });

        // Shooting Efficiency Chart
        const shootingCtx = document.getElementById('teamShootingChart').getContext('2d');
        if (teamCharts.shooting) teamCharts.shooting.destroy();
        teamCharts.shooting = new Chart(shootingCtx, {
            type: 'bar',
            data: {
                labels: sortedOpp,
                datasets: [
                    {
                        label: 'FG%',
                        data: sortedFgPct,
                        backgroundColor: '#4169E1',
                        borderColor: '#4169E1',
                        borderWidth: 1
                    },
                    {
                        label: '3P%',
                        data: sortedFg3Pct,
                        backgroundColor: '#808080',
                        borderColor: '#808080',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.85)',
                        padding: 12,
                        titleFont: { size: 12, weight: 'bold' },
                        bodyFont: { size: 11 },
                        borderColor: '#4169E1',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y.toFixed(1) + '%';
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });

        // Assists vs Turnovers Chart
        const astCtx = document.getElementById('teamAstChart').getContext('2d');
        if (teamCharts.ast) teamCharts.ast.destroy();
        teamCharts.ast = new Chart(astCtx, {
            type: 'line',
            data: {
                labels: sortedOpp,
                datasets: [
                    {
                        label: 'Assists',
                        data: sortedAsst,
                        borderColor: '#4169E1',
                        backgroundColor: 'rgba(65, 105, 225, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointBackgroundColor: '#4169E1'
                    },
                    {
                        label: 'Turnovers',
                        data: sortedTo,
                        borderColor: '#808080',
                        backgroundColor: 'rgba(128, 128, 128, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointBackgroundColor: '#808080'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.85)',
                        padding: 12,
                        titleFont: { size: 12, weight: 'bold' },
                        bodyFont: { size: 11 },
                        borderColor: '#4169E1',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y.toFixed(1);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        // Prepare sorted stat arrays for new charts
        const sortedReb = sortedIndices.map(i => trends.reb[i]);
        const sortedOreb = sortedIndices.map(i => trends.oreb[i]);
        const sortedDreb = sortedIndices.map(i => trends.dreb[i]);
        const sortedStl = sortedIndices.map(i => trends.stl[i]);
        const sortedBlk = sortedIndices.map(i => trends.blk[i]);
        const sortedFt = sortedIndices.map(i => trends.ft[i]);
        const sortedFta = sortedIndices.map(i => trends.fta[i]);
        
        // Rebounding Trends Chart
        const reboundingCtx = document.getElementById('teamReboundingChart').getContext('2d');
        if (teamCharts.rebounding) teamCharts.rebounding.destroy();
        teamCharts.rebounding = new Chart(reboundingCtx, {
            type: 'line',
            data: {
                labels: sortedOpp,
                datasets: [
                    {
                        label: 'Total Rebounds',
                        data: sortedReb,
                        borderColor: '#4169E1',
                        backgroundColor: 'rgba(65, 105, 225, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5
                    },
                    {
                        label: 'Offensive Rebounds',
                        data: sortedOreb,
                        borderColor: '#32CD32',
                        backgroundColor: 'rgba(50, 205, 50, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.85)',
                        padding: 12
                    }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        
        // Defensive Activity Chart
        const defenseCtx = document.getElementById('teamDefenseChart').getContext('2d');
        if (teamCharts.defense) teamCharts.defense.destroy();
        teamCharts.defense = new Chart(defenseCtx, {
            type: 'bar',
            data: {
                labels: sortedOpp,
                datasets: [
                    {
                        label: 'Steals',
                        data: sortedStl,
                        backgroundColor: '#FF8C00',
                        borderColor: '#FF8C00'
                    },
                    {
                        label: 'Blocks',
                        data: sortedBlk,
                        backgroundColor: '#DC143C',
                        borderColor: '#DC143C'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        
        // Free Throw Performance Chart
        const ftCtx = document.getElementById('teamFTChart').getContext('2d');
        if (teamCharts.ft) teamCharts.ft.destroy();
        teamCharts.ft = new Chart(ftCtx, {
            type: 'line',
            data: {
                labels: sortedOpp,
                datasets: [
                    {
                        label: 'FT%',
                        data: sortedIndices.map(i => {
                            const ft = sortedFt[i];
                            const fta = sortedFta[i];
                            return fta > 0 ? (ft / fta * 100) : 0;
                        }),
                        borderColor: '#9932CC',
                        backgroundColor: 'rgba(153, 50, 204, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.85)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                return 'FT%: ' + context.parsed.y.toFixed(1) + '%';
                            }
                        }
                    }
                },
                scales: {
                    y: { 
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error loading team trends:', error);
    }
}

async function loadPlayerTrends(playerName) {
    try {
        const response = await fetch(`/api/player-trends/${playerName}`);
        const trends = await response.json();
        
        // Sort by date to ensure chronological order
        const gameIds = trends.games;
        const sortedIndices = gameIds.map((_, i) => i).sort((a, b) => {
            const dateA = new Date(trends.dates[a]);
            const dateB = new Date(trends.dates[b]);
            return dateA - dateB;
        });
        
        const sortedOpp = sortedIndices.map(i => trends.opponents[i]);
        const sortedPts = sortedIndices.map(i => trends.pts[i]);
        const sortedFg = sortedIndices.map(i => trends.fg[i]);
        const sortedFgAtt = sortedIndices.map(i => trends.fg_att[i]);
        const sortedFg3 = sortedIndices.map(i => trends.fg3[i]);
        const sortedFg3Att = sortedIndices.map(i => {
            if (trends.fg3_att) return trends.fg3_att[i];
            return 0;
        });
        const sortedReb = sortedIndices.map(i => trends.reb[i]);
        const sortedAsst = sortedIndices.map(i => trends.asst[i]);

        // Points Chart
        const ptsCtx = document.getElementById('playerPtsChart').getContext('2d');
        if (playerCharts.pts) playerCharts.pts.destroy();
        playerCharts.pts = new Chart(ptsCtx, {
            type: 'line',
            data: {
                labels: sortedOpp,
                datasets: [
                    {
                        label: 'Points',
                        data: sortedPts,
                        borderColor: '#4169E1',
                        backgroundColor: 'rgba(65, 105, 225, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 6,
                        pointBackgroundColor: '#4169E1',
                        pointHoverRadius: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.85)',
                        padding: 12,
                        titleFont: { size: 12, weight: 'bold' },
                        bodyFont: { size: 11 },
                        borderColor: '#4169E1',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return 'Points: ' + context.parsed.y.toFixed(1);
                            }
                        }
                    }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        // Shooting Efficiency Chart
        const shootingCtx = document.getElementById('playerShootingChart').getContext('2d');
        if (playerCharts.shooting) playerCharts.shooting.destroy();
        
        const fg_pct = sortedFg.map((fg, i) => sortedFgAtt[i] > 0 ? (fg / sortedFgAtt[i]) * 100 : 0);
        const fg3_pct = sortedFg3.map((fg3, i) => sortedFg3Att[i] > 0 ? (fg3 / sortedFg3Att[i]) * 100 : 0);

        playerCharts.shooting = new Chart(shootingCtx, {
            type: 'bar',
            data: {
                labels: sortedOpp,
                datasets: [
                    {
                        label: 'FG%',
                        data: fg_pct,
                        backgroundColor: '#4169E1',
                        borderColor: '#4169E1',
                        borderWidth: 1
                    },
                    {
                        label: '3P%',
                        data: fg3_pct,
                        backgroundColor: '#808080',
                        borderColor: '#808080',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: true, position: 'top' },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.85)',
                        padding: 12,
                        titleFont: { size: 12, weight: 'bold' },
                        bodyFont: { size: 11 },
                        borderColor: '#4169E1',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y.toFixed(1) + '%';
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });

        // Rebounds & Assists Chart
        const rebAstCtx = document.getElementById('playerRebAstChart').getContext('2d');
        if (playerCharts.rebAst) playerCharts.rebAst.destroy();
        playerCharts.rebAst = new Chart(rebAstCtx, {
            type: 'line',
            data: {
                labels: sortedOpp,
                datasets: [
                    {
                        label: 'Rebounds',
                        data: sortedReb,
                        borderColor: '#4169E1',
                        backgroundColor: 'rgba(65, 105, 225, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointBackgroundColor: '#4169E1'
                    },
                    {
                        label: 'Assists',
                        data: sortedAsst,
                        borderColor: '#808080',
                        backgroundColor: 'rgba(128, 128, 128, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointBackgroundColor: '#808080'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: true, position: 'top' },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.85)',
                        padding: 12,
                        titleFont: { size: 12, weight: 'bold' },
                        bodyFont: { size: 11 },
                        borderColor: '#4169E1',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y.toFixed(1);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        
        // Plus/Minus Impact Chart
        const plusMinusCtx = document.getElementById('playerPlusMinusChart').getContext('2d');
        if (playerCharts.plusMinus) playerCharts.plusMinus.destroy();
        
        const plusMinusData = sortedIndices.map(i => {
            const gameLogs = trends.game_logs || [];
            return gameLogs[i]?.plus_minus || 0;
        });
        
        playerCharts.plusMinus = new Chart(plusMinusCtx, {
            type: 'bar',
            data: {
                labels: sortedOpp,
                datasets: [{
                    label: 'Plus/Minus',
                    data: plusMinusData,
                    backgroundColor: plusMinusData.map(val => val >= 0 ? '#4ade80' : '#f87171'),
                    borderColor: plusMinusData.map(val => val >= 0 ? '#22c55e' : '#ef4444'),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.85)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                const val = context.parsed.y;
                                return 'Plus/Minus: ' + (val > 0 ? '+' : '') + val;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: function(context) {
                                if (context.tick.value === 0) {
                                    return 'rgba(255, 255, 255, 0.5)';
                                }
                                return 'rgba(255, 255, 255, 0.1)';
                            }
                        }
                    }
                }
            }
        });
        
        // Turnovers & Fouls Chart
        const toFoulsCtx = document.getElementById('playerTOFoulsChart').getContext('2d');
        if (playerCharts.toFouls) playerCharts.toFouls.destroy();
        
        const toData = sortedIndices.map(i => trends.to ? trends.to[i] : 0);
        const foulsData = sortedIndices.map(i => {
            const gameLogs = trends.game_logs || [];
            return gameLogs[i]?.fouls || 0;
        });
        
        playerCharts.toFouls = new Chart(toFoulsCtx, {
            type: 'line',
            data: {
                labels: sortedOpp,
                datasets: [
                    {
                        label: 'Turnovers',
                        data: toData,
                        borderColor: '#f87171',
                        backgroundColor: 'rgba(248, 113, 113, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5
                    },
                    {
                        label: 'Fouls',
                        data: foulsData,
                        borderColor: '#fb923c',
                        backgroundColor: 'rgba(251, 146, 60, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: true, position: 'top' },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.85)',
                        padding: 12
                    }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    } catch (error) {
        console.error('Error loading player trends:', error);
    }
}



function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    console.log('Setting up tabs:', tabButtons.length, 'buttons found,', tabContents.length, 'content sections found');
    
    // Track which tabs have been initialized
    const initializedTabs = new Set();

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;
            console.log('Tab clicked:', tabName);

            tabButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            button.classList.add('active');
            const tabElement = document.getElementById(`${tabName}-tab`);
            
            if (tabElement) {
                tabElement.classList.add('active');
                console.log('Activated tab:', tabName);
            } else {
                console.error('Tab element not found:', `${tabName}-tab`);
            }
            
            // Initialize tab content on first view
            if (!initializedTabs.has(tabName)) {
                initializedTabs.add(tabName);
                console.log('Initializing tab for first time:', tabName);
                
                if (tabName === 'insights') {
                    displayComprehensiveInsights();
                } else if (tabName === 'player') {
                    setupPlayerSelector();
                } else if (tabName === 'comparison') {
                    setupComparisonSelectors();
                }
            } else if (tabName === 'insights') {
                // Refresh insights each time
                displayComprehensiveInsights();
            }
        });
    });
}

function displayComprehensiveInsights() {
    if (!comprehensiveInsights) return;
    
    // Display team insights
    displayTeamInsights();
    
    // Display recommendations
    displayRecommendations();
    
    // Display player insights
    displayPlayerInsights();
}

function displayTeamInsights() {
    const container = document.getElementById('team-insights-grid');
    const insights = comprehensiveInsights;
    
    if (!insights.team_trends) return;
    
    const trends = insights.team_trends;
    
    container.innerHTML = `
        <div class="insight-card">
            <div class="insight-title">Recent Performance</div>
            <div class="insight-content">
                <p><strong>Record:</strong> ${trends.recent_performance?.record || 'N/A'}</p>
                <p><strong>Avg Score:</strong> ${trends.recent_performance?.avg_score || 'N/A'}</p>
                <p><strong>Point Differential:</strong> ${trends.recent_performance?.point_differential > 0 ? '+' : ''}${trends.recent_performance?.point_differential || 'N/A'}</p>
                <p><strong>Trend:</strong> ${trends.recent_performance?.trend || 'N/A'}</p>
            </div>
        </div>
        
        <div class="insight-card">
            <div class="insight-title">Scoring Trends</div>
            <div class="insight-content">
                <p><strong>Recent Avg:</strong> ${trends.scoring_trends?.recent_avg || 'N/A'} PPG</p>
                <p><strong>Early Season:</strong> ${trends.scoring_trends?.early_avg || 'N/A'} PPG</p>
                <p><strong>Improvement:</strong> ${trends.scoring_trends?.improvement > 0 ? '+' : ''}${trends.scoring_trends?.improvement || 'N/A'}</p>
                <p><strong>Trend:</strong> ${trends.scoring_trends?.trend || 'N/A'}</p>
            </div>
        </div>
        
        <div class="insight-card">
            <div class="insight-title">Defensive Trends</div>
            <div class="insight-content">
                <p><strong>Recent Allowed:</strong> ${trends.defensive_trends?.recent_avg_allowed || 'N/A'} PPG</p>
                <p><strong>Early Season:</strong> ${trends.defensive_trends?.early_avg_allowed || 'N/A'} PPG</p>
                <p><strong>Improvement:</strong> ${trends.defensive_trends?.improvement > 0 ? '+' : ''}${trends.defensive_trends?.improvement || 'N/A'}</p>
                <p><strong>Trend:</strong> ${trends.defensive_trends?.trend || 'N/A'}</p>
            </div>
        </div>
        
        <div class="insight-card">
            <div class="insight-title">Key Metrics</div>
            <div class="insight-content">
                <p><strong>Win %:</strong> ${insights.key_metrics?.win_pct || 'N/A'}%</p>
                <p><strong>FG%:</strong> ${insights.key_metrics?.fg_pct || 'N/A'}%</p>
                <p><strong>3P%:</strong> ${insights.key_metrics?.fg3_pct || 'N/A'}%</p>
                <p><strong>AST/TO:</strong> ${((insights.key_metrics?.apg || 0) / (insights.key_metrics?.tpg || 1)).toFixed(2)}</p>
            </div>
        </div>
    `;
}

function displayRecommendations() {
    const container = document.getElementById('recommendations-list');
    const recommendations = comprehensiveInsights?.recommendations || [];
    
    if (recommendations.length === 0) {
        container.innerHTML = '<li>No specific recommendations at this time.</li>';
        return;
    }
    
    container.innerHTML = recommendations.map(rec => `
        <li class="rec-${rec.priority.toLowerCase()}">
            <strong>${rec.category} (${rec.priority} Priority):</strong> ${rec.recommendation}
            <br><small><em>${rec.reason}</em></small>
        </li>
    `).join('');
}

function displayPlayerInsights() {
    const container = document.getElementById('player-insights-grid');
    const playerInsights = comprehensiveInsights?.player_insights || [];
    
    if (playerInsights.length === 0) {
        container.innerHTML = '<div class="player-insight-card">No player insights available.</div>';
        return;
    }
    
    container.innerHTML = playerInsights.slice(0, 12).map(player => `
        <div class="player-insight-card">
            <div class="player-insight-name">${player.name}</div>
            <div class="player-insight-role">${player.role}</div>
            
            <div class="strengths">
                <h4>Strengths</h4>
                <div class="strength-tags">
                    ${(player.strengths || []).map(strength => `<span class="strength-tag">${strength}</span>`).join('')}
                </div>
            </div>
            
            <div class="improvements">
                <h4>Areas for Improvement</h4>
                <div class="improvement-tags">
                    ${(player.areas_for_improvement || []).map(area => `<span class="improvement-tag">${area}</span>`).join('')}
                </div>
            </div>
            
            <div style="margin-top: 0.75rem; font-size: 0.85rem; color: var(--text-light);">
                Efficiency Grade: <strong>${player.efficiency_grade}</strong>
            </div>
        </div>
    `).join('');
}

function setupComparisonSelectors() {
    const player1Select = document.getElementById('player1Select');
    const player2Select = document.getElementById('player2Select');
    const compareButton = document.getElementById('compareButton');
    
    if (!player1Select || !player2Select || !compareButton) {
        console.error('Comparison selector elements not found');
        return;
    }
    
    // Clear existing options except the first one
    while (player1Select.options.length > 1) {
        player1Select.remove(1);
    }
    while (player2Select.options.length > 1) {
        player2Select.remove(1);
    }
    
    // Populate player options
    allPlayers.forEach(player => {
        const firstName = (player.full_name || player.name).split(' ')[0];
        const option1 = new Option(firstName, player.name);
        const option2 = new Option(firstName, player.name);
        player1Select.appendChild(option1);
        player2Select.appendChild(option2);
    });
    
    // Setup compare button
    compareButton.addEventListener('click', compareSelectedPlayers);
}

async function compareSelectedPlayers() {
    const player1 = document.getElementById('player1Select').value;
    const player2 = document.getElementById('player2Select').value;
    
    if (!player1 || !player2) {
        alert('Please select both players to compare');
        return;
    }
    
    if (player1 === player2) {
        alert('Please select two different players');
        return;
    }
    
    try {
        const response = await fetch(`/api/player-comparison?players=${player1}&players=${player2}`);
        const comparison = await response.json();
        
        displayComparison(comparison);
    } catch (error) {
        console.error('Error comparing players:', error);
    }
}

function displayComparison(comparison) {
    const container = document.getElementById('comparison-results');
    
    if (!comparison.players || comparison.players.length < 2) {
        container.innerHTML = '<div class="error">Unable to load comparison data</div>';
        return;
    }
    
    const player1 = comparison.players[0];
    const player2 = comparison.players[1];
    
    const compareStats = [
        { key: 'ppg', label: 'Points Per Game' },
        { key: 'rpg', label: 'Rebounds Per Game' },
        { key: 'apg', label: 'Assists Per Game' },
        { key: 'tpg', label: 'Turnovers Per Game', lowerBetter: true },
        { key: 'fg_pct', label: 'Field Goal %' },
        { key: 'fg3_pct', label: '3-Point %' },
        { key: 'ft_pct', label: 'Free Throw %' }
    ];
    
    container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; margin-bottom: 1rem;">
            <h3>${player1.name} vs ${player2.name}</h3>
        </div>
        
        ${compareStats.map(stat => {
            const val1 = player1.basic_stats[stat.key] || 0;
            const val2 = player2.basic_stats[stat.key] || 0;
            
            let winner1 = false, winner2 = false;
            if (stat.lowerBetter) {
                winner1 = val1 < val2;
                winner2 = val2 < val1;
            } else {
                winner1 = val1 > val2;
                winner2 = val2 > val1;
            }
            
            return `
                <div class="comparison-stat">
                    <div class="comparison-stat-name">${stat.label}</div>
                    <div class="comparison-values">
                        <div class="comparison-value ${winner1 ? 'comparison-winner' : ''}">
                            ${formatStatValue(val1, stat.key)}
                        </div>
                        <div style="color: var(--text-light); font-size: 0.8rem;">vs</div>
                        <div class="comparison-value ${winner2 ? 'comparison-winner' : ''}">
                            ${formatStatValue(val2, stat.key)}
                        </div>
                    </div>
                </div>
            `;
        }).join('')}
        
        <div style="grid-column: 1 / -1; margin-top: 1rem; padding: 1rem; background: var(--light-bg); border-radius: 6px;">
            <h4 style="margin: 0 0 0.5rem 0;">Player Roles</h4>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div><strong>${player1.name}:</strong> ${player1.role}</div>
                <div><strong>${player2.name}:</strong> ${player2.role}</div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem;">
                <div><strong>Efficiency Grade:</strong> ${player1.efficiency_grade}</div>
                <div><strong>Efficiency Grade:</strong> ${player2.efficiency_grade}</div>
            </div>
        </div>
    `;
}

function formatStatValue(value, stat) {
    if (stat.includes('_pct')) {
        return `${value.toFixed(1)}%`;
    }
    if (stat.includes('pg')) {
        return value.toFixed(1);
    }
    return Math.round(value);
}
