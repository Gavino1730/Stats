// Dashboard JavaScript
let scoringChart = null;
let shootingChart = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Load critical data in parallel
    await Promise.all([
        loadSeasonStats(),
        loadLeaderboards()
    ]);
    
    // Load charts after critical data is ready (don't block)
    loadCharts().catch(console.error);
});

async function loadSeasonStats() {
    try {
        const response = await fetch('/api/season-stats');
        const stats = await response.json();

        document.getElementById('record').textContent = `${stats.win}-${stats.loss}`;
        document.getElementById('ppg').textContent = stats.ppg.toFixed(1);
        document.getElementById('fg-pct').textContent = stats.fg_pct.toFixed(1) + '%';
        document.getElementById('rpg').textContent = stats.rpg.toFixed(1);
        document.getElementById('apg').textContent = stats.apg.toFixed(1);
        document.getElementById('three-pct').textContent = stats.fg3_pct.toFixed(1) + '%';
    } catch (error) {
        console.error('Error loading season stats:', error);
    }
}

async function loadLeaderboards() {
    try {
        const response = await fetch('/api/leaderboards');
        const leaderboards = await response.json();

        // Top Scorers
        const scorersHtml = leaderboards.ppg.slice(0, 5).map(p => `
            <tr>
                <td><strong>${p.name}</strong></td>
                <td>${p.ppg.toFixed(1)}</td>
                <td>${p.games}</td>
            </tr>
        `).join('');
        document.getElementById('top-scorers').innerHTML = scorersHtml;

        // Top Rebounders
        const reboundersHtml = leaderboards.rpg.slice(0, 5).map(p => `
            <tr>
                <td><strong>${p.name}</strong></td>
                <td>${p.rpg.toFixed(1)}</td>
                <td>${p.games}</td>
            </tr>
        `).join('');
        document.getElementById('top-rebounders').innerHTML = reboundersHtml;

        // Top Assist Leaders
        const assistsHtml = leaderboards.apg.slice(0, 5).map(p => `
            <tr>
                <td><strong>${p.name}</strong></td>
                <td>${p.apg.toFixed(1)}</td>
                <td>${p.games}</td>
            </tr>
        `).join('');
        document.getElementById('top-assists').innerHTML = assistsHtml;
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
        const trends = await response.json();
        
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
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        font: {
                            size: isMobile ? 10 : 12
                        },
                        callback: function(value) {
                            return value;
                        }
                    }
                },
                x: {
                    ticks: {
                        font: {
                            size: isMobile ? 9 : 11
                        },
                        maxRotation: isMobile ? 45 : 0,
                        minRotation: isMobile ? 45 : 0
                    }
                }
            }
        };

        // Scoring Chart
        const scoringCtx = document.getElementById('scoringChart').getContext('2d');
        if (scoringChart) scoringChart.destroy();
        scoringChart = new Chart(scoringCtx, {
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
            options: commonOptions
        });

        // Shooting Efficiency Chart
        const shootingCtx = document.getElementById('shootingChart').getContext('2d');
        if (shootingChart) shootingChart.destroy();
        shootingChart = new Chart(shootingCtx, {
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
            options: commonOptions
        });
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}
