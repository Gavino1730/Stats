// Players Page JavaScript
let allPlayers = [];
let playerModal = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Load and setup in parallel for faster interaction
    await loadPlayers();
    setupFilters();
    setupModal();
});

async function loadPlayers() {
    try {
        const response = await fetch('/api/players');
        allPlayers = await response.json();
        // Sort by number by default
        allPlayers.sort((a, b) => a.number - b.number);
        displayPlayers(allPlayers);
    } catch (error) {
        console.error('Error loading players:', error);
    }
}

function displayPlayers(players) {
    const container = document.getElementById('players-container');
    container.innerHTML = '';
    
    players.forEach(player => {
        const card = document.createElement('div');
        card.className = 'player-card';
        card.innerHTML = `
            <div class="player-number">#${player.number || '-'}</div>
            <div class="player-name">${player.name}</div>
            <div class="player-stats">
                <div class="player-stat-item">
                    <div class="player-stat-label">PPG</div>
                    <div class="player-stat-value">${player.ppg.toFixed(1)}</div>
                </div>
                <div class="player-stat-item">
                    <div class="player-stat-label">RPG</div>
                    <div class="player-stat-value">${player.rpg.toFixed(1)}</div>
                </div>
                <div class="player-stat-item">
                    <div class="player-stat-label">APG</div>
                    <div class="player-stat-value">${player.apg.toFixed(1)}</div>
                </div>
                <div class="player-stat-item">
                    <div class="player-stat-label">FG%</div>
                    <div class="player-stat-value">${player.fg_pct.toFixed(1)}%</div>
                </div>
            </div>
        `;
        
        card.addEventListener('click', () => showPlayerDetail(player.name));
        container.appendChild(card);
    });
}

function setupFilters() {
    const searchInput = document.getElementById('player-search');
    const sortSelect = document.getElementById('stat-sort');

    searchInput.addEventListener('input', filterPlayers);
    sortSelect.addEventListener('change', sortPlayers);
}

function filterPlayers() {
    const searchValue = document.getElementById('player-search').value.toLowerCase();
    const filtered = allPlayers.filter(p => p.name.toLowerCase().includes(searchValue));
    displayPlayers(filtered);
}

function sortPlayers() {
    const sortValue = document.getElementById('stat-sort').value;
    const sorted = [...allPlayers].sort((a, b) => {
        if (sortValue === 'ppg') return b.ppg - a.ppg;
        if (sortValue === 'rpg') return b.rpg - a.rpg;
        if (sortValue === 'apg') return b.apg - a.apg;
        if (sortValue === 'fg_pct') return b.fg_pct - a.fg_pct;
        return 0;
    });
    displayPlayers(sorted);
}

async function showPlayerDetail(playerName) {
    try {
        const response = await fetch(`/api/player/${playerName}`);
        const data = await response.json();
        
        // Build roster info section if available
        let rosterHtml = '';
        if (data.roster_info) {
            rosterHtml = `
                <div class="roster-info" style="margin-bottom: 1.5rem; padding: 1rem; background: var(--light-bg); border-radius: 6px; border: 1px solid var(--border);">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                        <div>
                            <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-light); font-weight: 700; letter-spacing: 0.5px;">Grade</div>
                            <div style="font-size: 1.2rem; font-weight: 700; color: var(--primary);">${data.roster_info.grade}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-light); font-weight: 700; letter-spacing: 0.5px;">Number</div>
                            <div style="font-size: 1.2rem; font-weight: 700; color: var(--primary);">#${data.roster_info.number}</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        const detailHtml = `
            <div class="player-detail-header">
                <div class="player-detail-info">
                    <div class="player-detail-number">Player #${data.season_stats.number || '-'}</div>
                    <div class="player-detail-name">${data.season_stats.name}</div>
                </div>
            </div>

            ${rosterHtml}

            <div class="player-detail-stats">
                <div class="detail-stat">
                    <div class="detail-stat-label">PPG</div>
                    <div class="detail-stat-value">${data.season_stats.ppg.toFixed(1)}</div>
                </div>
                <div class="detail-stat">
                    <div class="detail-stat-label">RPG</div>
                    <div class="detail-stat-value">${data.season_stats.rpg.toFixed(1)}</div>
                </div>
                <div class="detail-stat">
                    <div class="detail-stat-label">APG</div>
                    <div class="detail-stat-value">${data.season_stats.apg.toFixed(1)}</div>
                </div>
                <div class="detail-stat">
                    <div class="detail-stat-label">FG%</div>
                    <div class="detail-stat-value">${data.season_stats.fg_pct.toFixed(1)}%</div>
                </div>
                <div class="detail-stat">
                    <div class="detail-stat-label">3P%</div>
                    <div class="detail-stat-value">${data.season_stats.fg3_pct.toFixed(1)}%</div>
                </div>
                <div class="detail-stat">
                    <div class="detail-stat-label">FT%</div>
                    <div class="detail-stat-value">${data.season_stats.ft_pct.toFixed(1)}%</div>
                </div>
                <div class="detail-stat">
                    <div class="detail-stat-label">Games</div>
                    <div class="detail-stat-value">${data.season_stats.games}</div>
                </div>
                <div class="detail-stat">
                    <div class="detail-stat-label">Total Points</div>
                    <div class="detail-stat-value">${data.season_stats.pts}</div>
                </div>
            </div>

            <h3 style="margin-top: 2rem; color: var(--primary); margin-bottom: 1rem;">Game Log</h3>
            <table class="box-score-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Opponent</th>
                        <th>FG</th>
                        <th>3P</th>
                        <th>FT</th>
                        <th>REB</th>
                        <th>AST</th>
                        <th>STL</th>
                        <th>PTS</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.game_logs.sort((a, b) => {
                        const dateA = new Date(a.date);
                        const dateB = new Date(b.date);
                        return dateA - dateB;
                    }).map(game => {
                        const stats = game.stats;
                        const reb = stats.oreb + stats.dreb;
                        return `
                            <tr>
                                <td>${game.date}</td>
                                <td>${game.location === 'away' ? '@' : 'vs'} ${game.opponent}</td>
                                <td>${stats.fg_made}-${stats.fg_att}</td>
                                <td>${stats.fg3_made}-${stats.fg3_att}</td>
                                <td>${stats.ft_made}-${stats.ft_att}</td>
                                <td>${reb}</td>
                                <td>${stats.asst}</td>
                                <td>${stats.stl}</td>
                                <td><strong>${stats.pts}</strong></td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        `;
        
        document.getElementById('playerDetail').innerHTML = detailHtml;
        playerModal.classList.add('show');
    } catch (error) {
        console.error('Error loading player detail:', error);
    }
}

function setupModal() {
    playerModal = document.getElementById('playerModal');
    const closeBtn = document.querySelector('.close');
    
    closeBtn.addEventListener('click', () => {
        playerModal.classList.remove('show');
    });
    
    window.addEventListener('click', (e) => {
        if (e.target === playerModal) {
            playerModal.classList.remove('show');
        }
    });
}
