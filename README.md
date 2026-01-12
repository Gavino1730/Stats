# 🏀 Valley Catholic Basketball Stats

Basketball statistics platform with AI-powered analysis for Valley Catholic High School's varsity team.

## Features

- **Advanced Stats**: eFG%, TS%, PPP, shot analytics, win/loss patterns
- **AI Analysis**: Player evaluation, game breakdowns, diagnostic insights
- **6 Pages**: Dashboard, Games, Players, Trends, Analysis, AI Coach
- **Dark Theme**: School colors (Royal Blue)
- **Mobile Friendly**: Responsive design

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your-key-here" > .env

# Run the app
python main.py

# Visit http://localhost:5000
```

## Project Structure

```
src/
  app.py           # Flask app with all routes
  config.py        # Configuration settings
  data_manager.py  # Data loading and caching
  ai_service.py    # OpenAI API integration
  advanced_stats.py # Statistics calculations
  models.py        # Database models (optional)

data/              # JSON data files
static/            # CSS, JS, images
templates/         # HTML templates
```

## Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

1. Push code to GitHub
2. Visit [railway.app](https://railway.app) and connect your repository
3. Set `OPENAI_API_KEY` environment variable
4. Deploy! Your app will be live at `your-app.railway.app`

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 📁 Project Structure

```
vc-basketball-stats/
├── app.py                      # Flask application and API endpoints
├── advanced_stats.py           # Advanced statistics calculator
├── vc_stats_output.json        # Game and player statistics data
├── templates/                  # HTML templates (6 pages)
├── static/                     # JavaScript and CSS
│   ├── style.css
│   ├── dashboard.js
│   ├── games.js
│   ├── players.js
│   ├── trends.js
│   ├── ai-insights.js
│   └── service-worker.js
├── requirements.txt            # Python dependencies
├── Procfile                    # Railway/Heroku deployment
├── railway.json                # Railway configuration
└── .env.example                # Environment variables template
```

## 🔌 API Endpoints

### Advanced Stats
- `GET /api/advanced/team` - Team advanced statistics
- `GET /api/advanced/player/<name>` - Player advanced statistics
- `GET /api/advanced/patterns` - Win/loss patterns
- `GET /api/advanced/volatility` - Consistency metrics
- `GET /api/advanced/insights` - Auto-generated insights
- `GET /api/advanced/all` - All advanced stats in one call

### AI Analysis
- `POST /api/ai/analyze` - AI-powered analysis
- `GET /api/ai/player-insights/<name>` - Player diagnostic analysis
- `GET /api/ai/game-analysis/<id>` - Game breakdown
- `GET /api/ai/team-summary` - Season performance diagnosis

## 📱 Pages

### Dashboard
- **Season Overview**: eFG%, TS%, PPP, AST% with auto-generated insights

### Games
- **Complete Box Scores**: All 9 games with detailed player stats
- **Search & Filter**: Find games by opponent, filter wins/losses

### Players
- **Player Profiles**: All 13 players with season stats and game logs
- **Advanced Stats Panel**: eFG%, TS%, Usage%, Scoring Share, Role classification
- **Game-by-Game Logs**: Performance trends over time

### Trends
- **Interactive Charts**: Team scoring, shooting, assists vs turnovers
- **Volatility Metrics**: PPG Range, FG% Std Dev, TO Std Dev
- **Player Comparisons**: Select any player to view individual trends

### Analysis
- **AI Insights**: Comprehensive season analysis with pattern detection
- **Filterable Views**: Focus on specific aspects of team performance

### AI Coach
- **Custom Queries**: Ask specific questions about players, games, or trends
- **Diagnostic Output**: Data-driven responses without speculation

## 🧮 Advanced Metrics Explained

### Efficiency Metrics
- **eFG% (Effective Field Goal %)**: `(FG + 0.5 × 3PT) / FGA × 100`
- **TS% (True Shooting %)**: `PTS / (2 × (FGA + 0.44 × FTA)) × 100`
- **PPP (Points Per Possession)**: `PTS / Estimated Possessions`

### Usage Metrics
- **Usage Proxy**: `(FGA + 0.44 × FTA + TO) / Team Total × 100`
- **Scoring Share**: `Player PTS / Team PTS × 100`

### Win Conditions
- Threshold-based records (e.g., "Team is 7-0 when TO ≤ 13")
- Average stats in wins vs losses
- Failure mode detection

## 🤖 AI Analysis System

### Capabilities
- Player performance diagnosis
- Game root cause analysis
- Season pattern detection
- Win condition identification
- Tactical adjustment recommendations

### Limitations (By Design)
❌ Cannot infer:
- Defensive matchups beyond STL/BLK
- Player effort or confidence
- Coaching intent or momentum
- Shot selection by location

All insights are derived from box score data only.

## 🛠️ Tech Stack

- **Backend**: Flask 3.0, Python 3.11, Gunicorn
- **Frontend**: Vanilla JavaScript, Chart.js
- **AI**: OpenAI API with intelligent model selection:
  - **GPT-5.2**: Main analysis (game recaps, season summary, player diagnostics)
  - **GPT-5-mini**: Quick insights (short blurbs, simple deltas, UI copy)
  - **GPT-4.1**: Available for long-context season-wide processing
- **Deployment**: Railway
- **Caching**: LRU cache, Service Worker

## 📊 Performance

- **Backend Caching**: LRU cache on high-traffic endpoints
- **Frontend Optimization**: Parallel API loading with Promise.all()
- **Service Worker**: Offline caching for static assets
- **Results**: 55-65% faster first load, 90% faster cached responses

## 🔒 Security

- ✅ API keys in environment variables (never committed)
- ✅ `.env` file gitignored
- ✅ Input sanitization for AI queries
- ✅ Production mode in deployment

## 📝 License

This project is for Valley Catholic High School Basketball Team use.

---

Built with ❤️ for Valley Catholic Basketball## Troubleshooting

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
