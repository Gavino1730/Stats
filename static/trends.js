// Trends Page JavaScript
let teamCharts = {};
let playerCharts = {};
let allPlayers = [];
let currentTrendsData = null;

// Convert markdown-like formatting to HTML
function formatAIResponse(text) {
    return text
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.+?)__/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/_(.+?)_/g, '<em>$1</em>')
        .replace(/^[•\-\*] (.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
        .replace(/\n/g, '<br>');
}

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

// AI Trend Analysis
async function analyzeTrends() {
    try {
        const contentDiv = document.getElementById('ai-trends-content');
        const activeTab = document.querySelector('.tab-button.active').dataset.tab;
        
        contentDiv.style.display = 'block';
        contentDiv.innerHTML = '<div class="loading" style="padding: 1.5rem; text-align: center; color: #4169E1;"><div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div><div>AI analyzing trends and patterns...</div></div>';
        
        let query = '';
        let type = 'trends';
        
        if (activeTab === 'team') {
            // Analyze team trends
            query = `Analyze our team's performance trends across all games. Look at:
            
- Scoring patterns and consistency (PPG range, volatility)
- Shooting efficiency trends (FG%, 3PT%)
- Ball movement and turnover patterns (assists vs turnovers)
- Win/loss patterns and what correlates with success
- Areas of improvement over the season
- Key strengths to maintain and weaknesses to address

Provide actionable coaching insights and specific recommendations.`;
        } else {
            // Analyze player trends
            const playerSelect = document.getElementById('playerSelect');
            const selectedPlayer = playerSelect.value;
            
            if (!selectedPlayer) {
                contentDiv.innerHTML = '<div style="padding: 1.5rem; text-align: center; color: #ff6b6b;">⚠️ Please select a player first</div>';
                return;
            }
            
            query = `Analyze ${selectedPlayer}'s performance trends across all games. Look at:

- Scoring consistency and patterns
- Shooting efficiency trends (FG%, 3PT%, FT%)
- Rebounding and playmaking trends
- Hot/cold streaks and what might be causing them
- Areas of improvement and development
- Role optimization and coaching recommendations

Provide specific, actionable insights for player development.`;
        }
        
        const response = await fetch('/api/ai/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, type })
        });
        
        const data = await response.json();
        
        if (data.error) {
            contentDiv.innerHTML = `
                <div style="padding: 1.5rem; background: rgba(255, 107, 107, 0.1); border-radius: 6px; border-left: 4px solid #ff6b6b;">
                    <div style="font-weight: 600; margin-bottom: 0.5rem; color: #ff6b6b;">⚠️ ${data.error}</div>
                    <p style="margin: 0; color: #666;">Please configure your OpenAI API key as an environment variable: <code>OPENAI_API_KEY</code></p>
                </div>`;
        } else {
            contentDiv.innerHTML = `
                <div style="padding: 1.5rem; background: white; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 2px solid #4169E1;">
                        <div style="font-size: 2rem;">📊</div>
                        <div style="font-weight: 600; font-size: 1.1rem; color: #4169E1;">AI Insights</div>
                    </div>
                    <div class="ai-response" style="line-height: 1.7; color: #333;">${formatAIResponse(data.analysis)}</div>
                </div>`;
        }
    } catch (error) {
        document.getElementById('ai-trends-content').innerHTML = `
            <div style="padding: 1.5rem; background: rgba(255, 107, 107, 0.1); border-radius: 6px; border-left: 4px solid #ff6b6b;">
                <div style="font-weight: 600; color: #ff6b6b;">Error: ${error.message}</div>
            </div>`;
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
