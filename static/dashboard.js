// Dashboard JavaScript
let scoringChart = null;
let shootingChart = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded!');
        return;
    }
    
    // Load critical data in parallel
    await Promise.all([
        loadSeasonStats(),
        loadLeaderboards(),
        loadAdvancedStats()
    ]);
    
    // Load charts after critical data is ready (don't block)
    loadCharts().catch(console.error);
});

async function loadSeasonStats() {
    try {
        const response = await fetch('/api/season-stats');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const stats = await response.json();
        
        if (!stats) {
            console.error('No season stats data received');
            return;
        }

        const recordEl = document.getElementById('record');
        if (recordEl) recordEl.textContent = `${stats.win}-${stats.loss}`;
        
        const ppgEl = document.getElementById('ppg');
        if (ppgEl) ppgEl.textContent = stats.ppg.toFixed(1);
        
        const fgPctEl = document.getElementById('fg-pct');
        if (fgPctEl) fgPctEl.textContent = stats.fg_pct.toFixed(1) + '%';
        
        const rpgEl = document.getElementById('rpg');
        if (rpgEl) rpgEl.textContent = stats.rpg.toFixed(1);
        
        const apgEl = document.getElementById('apg');
        if (apgEl) apgEl.textContent = stats.apg.toFixed(1);
    } catch (error) {
        console.error('Error loading season stats:', error);
    }
}

async function loadAdvancedStats() {
    try {
        const response = await fetch('/api/advanced/team');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const stats = await response.json();
        
        if (!stats || !stats.scoring_efficiency || !stats.ball_movement) {
            console.error('Invalid advanced stats data structure:', stats);
            return;
        }
        
        // Update advanced efficiency metrics
        const efgPctEl = document.getElementById('efg-pct');
        if (efgPctEl) efgPctEl.textContent = stats.scoring_efficiency.efg_pct.toFixed(1) + '%';
        
        const tsPctEl = document.getElementById('ts-pct');
        if (tsPctEl) tsPctEl.textContent = stats.scoring_efficiency.ts_pct.toFixed(1) + '%';
        
        const pppEl = document.getElementById('ppp');
        if (pppEl) pppEl.textContent = stats.scoring_efficiency.ppp.toFixed(2);
        
        const astRateEl = document.getElementById('ast-rate');
        if (astRateEl) astRateEl.textContent = stats.ball_movement.assisted_scoring_rate.toFixed(1) + '%';
    } catch (error) {
        console.error('Error loading advanced stats:', error);
    }
}

async function loadLeaderboards() {
    try {
        const response = await fetch('/api/leaderboards');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const leaderboards = await response.json();
        
        // Validate data structure
        if (!leaderboards || !leaderboards.pts || !leaderboards.reb || !leaderboards.asst) {
            console.error('Invalid leaderboards data structure:', leaderboards);
            return;
        }

        // Top Scorers
        const topScorersEl = document.getElementById('top-scorers');
        if (topScorersEl) {
            const scorersHtml = leaderboards.pts.slice(0, 5).map(p => `
                <tr>
                    <td><strong>${p.first_name || p.name.split(' ')[0]}</strong></td>
                    <td>${p.pts}</td>
                </tr>
            `).join('');
            topScorersEl.innerHTML = scorersHtml;
        }

        // Top Rebounders
        const topReboundersEl = document.getElementById('top-rebounders');
        if (topReboundersEl) {
            const reboundersHtml = leaderboards.reb.slice(0, 5).map(p => `
                <tr>
                    <td><strong>${p.first_name || p.name.split(' ')[0]}</strong></td>
                    <td>${p.reb}</td>
                </tr>
            `).join('');
            topReboundersEl.innerHTML = reboundersHtml;
        }

        // Top Assist Leaders
        const topAssistsEl = document.getElementById('top-assists');
        if (topAssistsEl) {
            const assistsHtml = leaderboards.asst.slice(0, 5).map(p => `
                <tr>
                    <td><strong>${p.first_name || p.name.split(' ')[0]}</strong></td>
                    <td>${p.asst}</td>
                </tr>
            `).join('');
            topAssistsEl.innerHTML = assistsHtml;
        }
    } catch (error) {
        console.error('Error loading leaderboards:', error);
    }
}

async function loadRecentGames() {
    try {
        const response = await fetch('/api/games');
        let games = await response.json();

        // Sort games by date
        games.sort((a, b) => {
            const dateA = new Date(a.date);
            const dateB = new Date(b.date);
            return dateA - dateB;
        });

        const gamesList = document.getElementById('games-list');
        const recentGames = games.slice(-5).reverse();

        gamesList.innerHTML = recentGames.map(game => `
            <div class="game-card">
                <div class="game-info">
                    <div class="game-date">${game.date}</div>
                    <div class="game-opponent">
                        ${game.location === 'away' ? '@' : 'vs'} ${game.opponent}
                    </div>
                </div>
                <div class="game-score">
                    <span class="score-vc">${game.vc_score}</span>
                    <span class="score-separator">-</span>
                    <span class="score-opp">${game.opp_score}</span>
                    <span class="result-badge ${game.result === 'W' ? 'win' : 'loss'}">
                        ${game.result === 'W' ? 'WIN' : 'LOSS'}
                    </span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading games:', error);
    }
}

async function loadCharts() {
    try {
        const response = await fetch('/api/team-trends');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const trends = await response.json();
        
        // Validate data
        if (!trends || !trends.games || trends.games.length === 0) {
            console.warn('No game data available for charts');
            return;
        }
        
        // Sort by date to ensure chronological order
        const gameIds = trends.games;
        const sortedIndices = gameIds.map((_, i) => i).sort((a, b) => {
            const dateA = new Date(trends.dates[a]);
            const dateB = new Date(trends.dates[b]);
            return dateA - dateB;
        });
        
        const sortedOpponents = sortedIndices.map(i => trends.opponents[i]);
        const sortedVcScore = sortedIndices.map(i => trends.vc_score[i]);
        const sortedOppScore = sortedIndices.map(i => trends.opp_score[i]);
        const sortedFgPct = sortedIndices.map(i => trends.fg_pct[i]);
        const sortedFg3Pct = sortedIndices.map(i => trends.fg3_pct[i]);

        // Determine if mobile
        const isMobile = window.innerWidth < 768;
        
        // Common chart options for mobile/desktop
        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: isMobile ? 'bottom' : 'top',
                    labels: {
                        font: {
                            size: isMobile ? 11 : 12
                        },
                        padding: isMobile ? 10 : 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.85)',
                    padding: 12,
                    titleFont: { size: 12, weight: 'bold' },
                    bodyFont: { size: 11 },
                    borderColor: '#4169E1',
                    borderWidth: 1,
                    displayColors: true,
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
            }
        };
        
        // Options specifically for scoring chart (points scored)
        const scoringOptions = {
            ...commonOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        font: {
                            size: isMobile ? 10 : 12
                        }
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: isMobile ? 10 : 12
                        },
                        maxRotation: 45,
                        minRotation: 45,
                        autoSkip: false,
                        padding: 5
                    }
                }
            }
        };
        
        // Options specifically for shooting percentage chart
        const shootingOptions = {
            ...commonOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        font: {
                            size: isMobile ? 10 : 12
                        },
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: isMobile ? 10 : 12
                        },
                        maxRotation: 45,
                        minRotation: 45,
                        autoSkip: false,
                        padding: 5
                    }
                }
            }
        };

        // Scoring Chart
        const scoringCtx = document.getElementById('scoringChart');
        if (!scoringCtx) {
            console.error('Scoring chart canvas not found');
            return;
        }
        
        if (scoringChart) scoringChart.destroy();
        scoringChart = new Chart(scoringCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: sortedOpponents,
                datasets: [
                    {
                        label: 'Valley Catholic',
                        data: sortedVcScore,
                        borderColor: '#4169E1',
                        backgroundColor: 'rgba(65, 105, 225, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: isMobile ? 3 : 5,
                        pointBackgroundColor: '#4169E1',
                        borderWidth: 2
                    },
                    {
                        label: 'Opponents',
                        data: sortedOppScore,
                        borderColor: '#808080',
                        backgroundColor: 'rgba(128, 128, 128, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: isMobile ? 3 : 5,
                        pointBackgroundColor: '#808080',
                        borderWidth: 2
                    }
                ]
            },
            options: scoringOptions
        });

        // Shooting Efficiency Chart
        const shootingCtx = document.getElementById('shootingChart');
        if (!shootingCtx) {
            console.error('Shooting chart canvas not found');
            return;
        }
        
        if (shootingChart) shootingChart.destroy();
        shootingChart = new Chart(shootingCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: sortedOpponents,
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
            options: shootingOptions
        });
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}
