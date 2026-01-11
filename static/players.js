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
        const [playerResponse, advancedResponse] = await Promise.all([
            fetch(`/api/player/${playerName}`),
            fetch(`/api/advanced/player/${playerName}`)
        ]);
        
        const data = await playerResponse.json();
        const advancedData = advancedResponse.ok ? await advancedResponse.json() : null;
        
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
        
        // Build advanced stats section if available
        let advancedHtml = '';
        if (advancedData) {
            const scoringEff = advancedData.scoring_efficiency;
            const usage = advancedData.usage_role;
            const ballHandling = advancedData.ball_handling;
            const rebounding = advancedData.rebounding;
            const defense = advancedData.defense_activity;
            
            advancedHtml = `
                <div style="margin: 1.5rem 0;">
                    <h3 style="margin: 0 0 1rem 0; font-size: 1.1rem; color: var(--primary);">Advanced Analytics</h3>
                    
                    <!-- Scoring Efficiency -->
                    <div style="margin-bottom: 1.5rem; padding: 1rem; background: var(--light-bg); border-radius: 6px; border-left: 3px solid var(--primary);">
                        <h4 style="margin: 0 0 0.75rem 0; font-size: 0.85rem; text-transform: uppercase; color: var(--text-light);">Scoring Efficiency</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 0.75rem;">
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">eFG%</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${scoringEff.efg_pct.toFixed(1)}%</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">TS%</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${scoringEff.ts_pct.toFixed(1)}%</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">Pts/Shot</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${scoringEff.pts_per_shot.toFixed(2)}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">2PT%</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${scoringEff.fg2_pct.toFixed(1)}%</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">3PT%</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${scoringEff.fg3_pct.toFixed(1)}%</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">FT%</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${scoringEff.ft_pct.toFixed(1)}%</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Usage & Role -->
                    <div style="margin-bottom: 1.5rem; padding: 1rem; background: var(--light-bg); border-radius: 6px; border-left: 3px solid #4169E1;">
                        <h4 style="margin: 0 0 0.75rem 0; font-size: 0.85rem; text-transform: uppercase; color: var(--text-light);">Usage & Role</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 0.75rem;">
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">Usage %</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${usage.usage_proxy.toFixed(1)}%</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">Scoring Share</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${usage.scoring_share.toFixed(1)}%</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">Shot Volume %</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${usage.shot_volume_share.toFixed(1)}%</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">Role</div>
                                <div style="font-weight: 700; font-size: 0.85rem; color: var(--primary);">
                                    ${usage.primary_scorer ? 'PRIMARY' : usage.secondary_scorer ? 'SECONDARY' : 'ROLE PLAYER'}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Ball Handling & Playmaking -->
                    <div style="margin-bottom: 1.5rem; padding: 1rem; background: var(--light-bg); border-radius: 6px; border-left: 3px solid #32CD32;">
                        <h4 style="margin: 0 0 0.75rem 0; font-size: 0.85rem; text-transform: uppercase; color: var(--text-light);">Ball Handling & Playmaking</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 0.75rem;">
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">AST/G</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${ballHandling.ast_rate.toFixed(1)}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">AST/TO</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${ballHandling.ast_to_ratio.toFixed(2)}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">TO/G</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${ballHandling.to_rate.toFixed(1)}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Rebounding -->
                    <div style="margin-bottom: 1.5rem; padding: 1rem; background: var(--light-bg); border-radius: 6px; border-left: 3px solid #FF8C00;">
                        <h4 style="margin: 0 0 0.75rem 0; font-size: 0.85rem; text-transform: uppercase; color: var(--text-light);">Rebounding</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 0.75rem;">
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">Total REB/G</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${rebounding.reb_rate.toFixed(1)}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">OREB/G</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${rebounding.oreb_rate.toFixed(1)}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">DREB/G</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${rebounding.dreb_rate.toFixed(1)}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">OREB %</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${(rebounding.oreb_rate / rebounding.reb_rate * 100).toFixed(1)}%</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Defense & Activity -->
                    <div style="margin-bottom: 1.5rem; padding: 1rem; background: var(--light-bg); border-radius: 6px; border-left: 3px solid #DC143C;">
                        <h4 style="margin: 0 0 0.75rem 0; font-size: 0.85rem; text-transform: uppercase; color: var(--text-light);">Defense & Activity</h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 0.75rem;">
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">STL/G</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${defense.stl_rate.toFixed(1)}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">BLK/G</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${defense.blk_rate.toFixed(1)}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">STL+BLK/G</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${(defense.stl_rate + defense.blk_rate).toFixed(1)}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: var(--text-light);">Fouls/G</div>
                                <div style="font-weight: 700; font-size: 1.1rem;">${defense.foul_rate.toFixed(1)}</div>
                            </div>
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
            
            <!-- Season Totals -->
            <div style="margin: 1.5rem 0;">
                <h3 style="margin: 0 0 1rem 0; font-size: 1.1rem; color: var(--primary);">Season Totals (${data.season_stats.games} Games)</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 0.75rem; padding: 1rem; background: var(--card-bg); border-radius: 6px; border: 1px solid var(--border);">
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">PTS</div>
                        <div style="font-weight: 700; font-size: 1.3rem; color: var(--primary);">${data.season_stats.pts}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">REB</div>
                        <div style="font-weight: 700; font-size: 1.3rem;">${data.season_stats.reb}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">AST</div>
                        <div style="font-weight: 700; font-size: 1.3rem;">${data.season_stats.asst}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">STL</div>
                        <div style="font-weight: 700; font-size: 1.3rem;">${data.season_stats.stl}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">BLK</div>
                        <div style="font-weight: 700; font-size: 1.3rem;">${data.season_stats.blk}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">TO</div>
                        <div style="font-weight: 700; font-size: 1.3rem;">${data.season_stats.to}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">FG</div>
                        <div style="font-weight: 700; font-size: 1.1rem;">${data.season_stats.fg}-${data.season_stats.fga}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">3PT</div>
                        <div style="font-weight: 700; font-size: 1.1rem;">${data.season_stats.fg3}-${data.season_stats.fg3a}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">FT</div>
                        <div style="font-weight: 700; font-size: 1.1rem;">${data.season_stats.ft}-${data.season_stats.fta}</div>
                    </div>
                </div>
            </div>
            
            <!-- Per Game Averages -->
            <div style="margin: 1.5rem 0;">
                <h3 style="margin: 0 0 1rem 0; font-size: 1.1rem; color: var(--primary);">Per Game Averages</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 0.75rem; padding: 1rem; background: var(--card-bg); border-radius: 6px; border: 1px solid var(--border);">
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">PPG</div>
                        <div style="font-weight: 700; font-size: 1.3rem; color: var(--primary);">${data.season_stats.ppg.toFixed(1)}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">RPG</div>
                        <div style="font-weight: 700; font-size: 1.3rem;">${data.season_stats.rpg.toFixed(1)}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">APG</div>
                        <div style="font-weight: 700; font-size: 1.3rem;">${data.season_stats.apg.toFixed(1)}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">FG%</div>
                        <div style="font-weight: 700; font-size: 1.3rem;">${data.season_stats.fg_pct.toFixed(1)}%</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">3P%</div>
                        <div style="font-weight: 700; font-size: 1.3rem;">${data.season_stats.fg3_pct.toFixed(1)}%</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.7rem; color: var(--text-light);">FT%</div>
                        <div style="font-weight: 700; font-size: 1.3rem;">${data.season_stats.ft_pct.toFixed(1)}%</div>
                    </div>
                </div>
            </div>

            ${advancedHtml}

            <h3 style="margin-top: 2rem; color: var(--primary); margin-bottom: 1rem;">Game-by-Game Performance</h3>
            <table class="box-score-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Opponent</th>
                        <th>MIN</th>
                        <th>PTS</th>
                        <th>FG</th>
                        <th>FG%</th>
                        <th>3P</th>
                        <th>3P%</th>
                        <th>FT</th>
                        <th>FT%</th>
                        <th>REB</th>
                        <th>OREB</th>
                        <th>DREB</th>
                        <th>AST</th>
                        <th>STL</th>
                        <th>BLK</th>
                        <th>TO</th>
                        <th>PF</th>
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
                        const fgPct = stats.fg_att > 0 ? (stats.fg_made / stats.fg_att * 100).toFixed(1) : '0.0';
                        const fg3Pct = stats.fg3_att > 0 ? (stats.fg3_made / stats.fg3_att * 100).toFixed(1) : '0.0';
                        const ftPct = stats.ft_att > 0 ? (stats.ft_made / stats.ft_att * 100).toFixed(1) : '0.0';
                        
                        return `
                            <tr>
                                <td>${game.date}</td>
                                <td>${game.location === 'away' ? '@' : 'vs'} ${game.opponent}</td>
                                <td>${stats.minutes || '-'}</td>
                                <td><strong style="color: var(--primary);">${stats.pts}</strong></td>
                                <td>${stats.fg_made}-${stats.fg_att}</td>
                                <td>${fgPct}%</td>
                                <td>${stats.fg3_made}-${stats.fg3_att}</td>
                                <td>${fg3Pct}%</td>
                                <td>${stats.ft_made}-${stats.ft_att}</td>
                                <td>${ftPct}%</td>
                                <td><strong>${reb}</strong></td>
                                <td>${stats.oreb}</td>
                                <td>${stats.dreb}</td>
                                <td>${stats.asst}</td>
                                <td>${stats.stl}</td>
                                <td>${stats.blk}</td>
                                <td>${stats.to}</td>
                                <td>${stats.fouls}</td>
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
