// Games Page JavaScript
let allGames = [];
let gameModal = null;

document.addEventListener('DOMContentLoaded', async () => {
    await loadGames();
    setupFilters();
    setupModal();
});

async function loadGames() {
    try {
        const response = await fetch('/api/games');
        allGames = await response.json();
        
        // Sort games by date
        allGames.sort((a, b) => {
            const dateA = new Date(a.date);
            const dateB = new Date(b.date);
            return dateA - dateB;
        });
        
        displayGames(allGames);
    } catch (error) {
        console.error('Error loading games:', error);
    }
}

function displayGames(games) {
    const container = document.getElementById('games-container');
    container.innerHTML = '';
    
    games.forEach(game => {
        const pointDiff = game.vc_score - game.opp_score;
        const gameCard = document.createElement('div');
        gameCard.className = 'game-card';
        gameCard.innerHTML = `
            <div class="game-card-header">
                <div class="game-card-date">${game.date}</div>
                <span class="result-badge ${game.result === 'W' ? 'win' : 'loss'}">
                    ${game.result === 'W' ? 'W' : 'L'}
                </span>
            </div>
            <div class="game-card-opponent">${game.location === 'away' ? '@' : 'vs'} ${game.opponent}</div>
            <div class="game-card-score">
                <div class="game-card-score-vc">${game.vc_score}</div>
                <div class="game-card-score-divider">-</div>
                <div class="game-card-score-opp">${game.opp_score}</div>
            </div>
            <div class="game-card-diff ${pointDiff > 0 ? 'positive' : 'negative'}">
                ${pointDiff > 0 ? '+' : ''}${pointDiff}
            </div>
        `;
        
        gameCard.addEventListener('click', () => showGameDetail(game));
        container.appendChild(gameCard);
    });
}

function setupFilters() {
    const searchInput = document.getElementById('game-search');
    const resultFilter = document.getElementById('game-result-filter');

    searchInput.addEventListener('input', filterGames);
    resultFilter.addEventListener('change', filterGames);
}

function filterGames() {
    const searchValue = document.getElementById('game-search').value.toLowerCase();
    const resultValue = document.getElementById('game-result-filter').value;

    const filtered = allGames.filter(game => {
        const matchesSearch = game.opponent.toLowerCase().includes(searchValue);
        const matchesResult = resultValue === '' || game.result === resultValue;
        return matchesSearch && matchesResult;
    });

    displayGames(filtered);
}

async function showGameDetail(game) {
    // Calculate stat differentials
    const pointDiff = game.vc_score - game.opp_score;
    const vcFgPct = (game.team_stats.fg / game.team_stats.fga * 100).toFixed(1);
    const vc3pPct = (game.team_stats.fg3 / game.team_stats.fg3a * 100).toFixed(1);
    const vcFtPct = (game.team_stats.ft / game.team_stats.fta * 100).toFixed(1);
    
    const detailHtml = `
        <div class="game-detail-header">
            <div class="game-detail-info">
                <div class="game-detail-date">${game.date}</div>
                <div class="game-detail-opponent">${game.location === 'away' ? '@' : 'vs'} ${game.opponent}</div>
            </div>
            <div class="game-detail-result ${game.result === 'W' ? 'win' : 'loss'}">
                ${game.result === 'W' ? 'WIN' : 'LOSS'}
            </div>
        </div>

        <div class="game-detail-score">
            <div class="score-column">
                <div class="score-team">Valley Catholic</div>
                <div class="score-value">${game.vc_score}</div>
            </div>
            <div class="score-column">
                <div class="score-team">${game.opponent}</div>
                <div class="score-value">${game.opp_score}</div>
            </div>
        </div>

        <div class="stat-differentials">
            <div class="stat-diff-item">
                <div class="stat-diff-label">Point Differential</div>
                <div class="stat-diff-value ${pointDiff > 0 ? 'positive' : 'negative'}">
                    ${pointDiff > 0 ? '+' : ''}${pointDiff}
                </div>
            </div>
            <div class="stat-diff-item">
                <div class="stat-diff-label">FG%</div>
                <div class="stat-diff-value">${vcFgPct}%</div>
            </div>
            <div class="stat-diff-item">
                <div class="stat-diff-label">3P%</div>
                <div class="stat-diff-value">${vc3pPct}%</div>
            </div>
            <div class="stat-diff-item">
                <div class="stat-diff-label">FT%</div>
                <div class="stat-diff-value">${vcFtPct}%</div>
            </div>
        </div>

        <h3 style="margin-top: 2rem; color: var(--primary); margin-bottom: 1rem;">Valley Catholic Box Score</h3>
        <table class="box-score-table">
            <thead>
                <tr>
                    <th>Player</th>
                    <th>FG</th>
                    <th>3P</th>
                    <th>FT</th>
                    <th>REB</th>
                    <th>OREB</th>
                    <th>DREB</th>
                    <th>AST</th>
                    <th>STL</th>
                    <th>BLK</th>
                    <th>TO</th>
                    <th>PF</th>
                    <th>+/-</th>
                    <th>PTS</th>
                </tr>
            </thead>
            <tbody>
                ${game.player_stats.map(p => `
                    <tr>
                        <td><strong>${p.name}</strong> (#${p.number})</td>
                        <td>${p.fg_made}-${p.fg_att}</td>
                        <td>${p.fg3_made}-${p.fg3_att}</td>
                        <td>${p.ft_made}-${p.ft_att}</td>
                        <td><strong>${p.oreb + p.dreb}</strong></td>
                        <td>${p.oreb}</td>
                        <td>${p.dreb}</td>
                        <td>${p.asst}</td>
                        <td>${p.stl}</td>
                        <td>${p.blk}</td>
                        <td style="color: ${p.to >= 4 ? '#dc3545' : 'inherit'};">${p.to}</td>
                        <td>${p.fouls}</td>
                        <td style="font-weight: 700; color: ${(p.plus_minus || 0) > 0 ? 'var(--success)' : (p.plus_minus || 0) < 0 ? '#dc3545' : 'inherit'};">${(p.plus_minus || 0) > 0 ? '+' : ''}${p.plus_minus || 0}</td>
                        <td><strong>${p.pts}</strong></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        <div style="margin-top: 1rem; padding: 1rem; background: var(--light-bg); border-radius: 4px;">
            <div style="font-weight: 700; margin-bottom: 0.5rem;">Team Totals</div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0.5rem; font-size: 0.9rem;">
                <div><strong>FG:</strong> ${game.team_stats.fg}-${game.team_stats.fga} (${vcFgPct}%)</div>
                <div><strong>3P:</strong> ${game.team_stats.fg3}-${game.team_stats.fg3a} (${vc3pPct}%)</div>
                <div><strong>FT:</strong> ${game.team_stats.ft}-${game.team_stats.fta} (${vcFtPct}%)</div>
                <div><strong>REB:</strong> ${game.team_stats.reb} (${game.team_stats.oreb}+${game.team_stats.dreb})</div>
                <div><strong>AST:</strong> ${game.team_stats.asst}</div>
                <div><strong>TO:</strong> ${game.team_stats.to}</div>
                <div><strong>STL:</strong> ${game.team_stats.stl}</div>
                <div><strong>BLK:</strong> ${game.team_stats.blk}</div>
                <div><strong>PF:</strong> ${game.team_stats.fouls || 0}</div>
            </div>
        </div>
    `;
    
    document.getElementById('gameDetail').innerHTML = detailHtml;
    gameModal.classList.add('show');
}

function setupModal() {
    gameModal = document.getElementById('gameModal');
    const closeBtn = document.querySelector('.close');
    
    closeBtn.addEventListener('click', () => {
        gameModal.classList.remove('show');
    });
    
    window.addEventListener('click', (e) => {
        if (e.target === gameModal) {
            gameModal.classList.remove('show');
        }
    });
}

