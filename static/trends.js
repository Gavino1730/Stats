// Trends Page JavaScript
let teamCharts = {};
let playerCharts = {};
let allPlayers = [];

document.addEventListener('DOMContentLoaded', async () => {
    // Load data in parallel for faster page interaction
    await Promise.all([
        loadPlayers(),
        loadTeamTrends(),
        loadVolatilityStats()
    ]);
    setupTabs();
    setupPlayerSelector();
});

async function loadPlayers() {
    try {
        const response = await fetch('/api/players');
        allPlayers = await response.json();
    } catch (error) {
        console.error('Error loading players:', error);
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
    
    allPlayers.forEach(player => {
        const option = document.createElement('option');
        option.value = player.name;
        option.textContent = player.name;
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
    } catch (error) {
        console.error('Error loading player trends:', error);
    }
}

function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;

            tabButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            button.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');
        });
    });
}
