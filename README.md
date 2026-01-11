# Valley Catholic Basketball Stats - Web Application

A full-featured interactive website for viewing Valley Catholic boys basketball statistics.

## Features

✅ **Dashboard** - Season overview with key stats and charts
✅ **Games** - Complete game-by-game box scores with detailed player stats
✅ **Players** - Individual player profiles with season stats and game logs
✅ **Trends** - Interactive charts showing team and player performance trends
✅ **Leaderboards** - Leaders in PPG, RPG, APG, and shooting percentages
✅ **Search & Filter** - Find games and players easily
✅ **Responsive Design** - Works on desktop, tablet, and mobile

## Installation & Running

### Prerequisites
- Python 3.7+ (already installed)
- Flask (will be installed automatically)

### Quick Start

1. **Open PowerShell** in the Stats folder (or activate the virtual environment)

2. **Run the app:**
   ```powershell
   python app.py
   ```

3. **Open in browser:**
   - Navigate to: `http://localhost:5000`
   - The website will automatically load

4. **Stop the app:**
   - Press `Ctrl+C` in PowerShell

## Navigation

### Dashboard (Home)
- **What you see:** Season overview, key stats, recent games, top performers
- **Charts:** Scoring trends and shooting efficiency
- **Leaderboards:** Top 5 scorers, rebounders, and assist leaders

### Games
- **What you see:** All 9 games with complete box scores
- **Features:** Search by opponent, filter by wins/losses
- **Details:** Player stats, team totals, shooting percentages

### Players
- **What you see:** All 13 players with season stats
- **Features:** Search by name, sort by PPG/RPG/APG/FG%
- **Click a player:** View detailed profile with full season stats and game-by-game log

### Trends
- **Team Trends:**
  - Scoring by game
  - Shooting efficiency progression
  - Assists vs turnovers
- **Player Trends:**
  - Select any player
  - View points, shooting, rebounds & assists by game
  - Identify patterns and performance trends

## Data Included

**Season Record:** 8-1 (89% win rate)

**Team Averages:**
- PPG: 83.3
- FG%: 47.0%
- 3P%: 32.0%
- FT%: 73.0%
- RPG: 32.0
- APG: 18.4

**Top Performers:**
1. M Mueller - 25.4 PPG
2. C Bonnett - 24.8 PPG, 7.8 APG
3. G Frank - 22.7 PPG
4. H Lomber - 20.6 PPG, 5.7 RPG
5. M Mehta - 17.7 PPG

**Games Tracked:**
- Knappa (W 83-58)
- Gladstone (W 88-41)
- Scappoose (L 69-90)
- Pleasant Hill (W 73-45)
- Banks (W 87-65)
- Tillamook (W 85-35)
- Jefferson (W 97-13)
- Mid Pacific (W 80-54)
- Regis (W 92-86)

## File Structure

```
Stats/
├── app.py                    # Flask application
├── vc_stats_output.json      # Complete stats database
├── schedule.txt              # Game schedule
├── templates/                # HTML pages
│   ├── base.html            # Base template
│   ├── dashboard.html       # Home page
│   ├── games.html           # Games page
│   ├── players.html         # Players page
│   └── trends.html          # Trends page
└── static/                   # Assets
    ├── style.css            # Styling
    ├── main.js              # Navigation
    ├── dashboard.js         # Dashboard logic
    ├── games.js             # Games page logic
    ├── players.js           # Players page logic
    └── trends.js            # Trends page logic
```

## Updating Stats

When new games are added:

1. Update the PDF stat sheets in `Stat Sheets/Stats/`
2. Update `schedule.txt` with the new games
3. Run the parser to regenerate `vc_stats_output.json`:
   ```powershell
   python parse_stats.py
   ```
4. Reload the website to see updated stats

## Troubleshooting

**Problem: "Address already in use"**
- Another instance of the app is running
- Kill the process or use a different port:
  ```powershell
  python app.py --port 5001
  ```

**Problem: Stats not updating**
- Make sure `vc_stats_output.json` was regenerated
- Clear browser cache (Ctrl+Shift+Delete)
- Restart the Flask app

**Problem: Charts not showing**
- Check browser console (F12) for errors
- Make sure internet is connected (needs Chart.js CDN)
- Try a different browser

## Technologies Used

- **Backend:** Python Flask
- **Frontend:** HTML5, CSS3, JavaScript
- **Charts:** Chart.js
- **Data:** JSON

---

**Built for Valley Catholic Basketball - 2025-2026 Season**
