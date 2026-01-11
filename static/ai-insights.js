// AI Insights JavaScript
let allPlayers = [];
let allGames = [];
let chatHistory = [];

// Convert markdown-like formatting to HTML
function formatAIResponse(text) {
    return text
        // Convert headers (### Header -> <h3>Header</h3>)
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        // Convert bold (**text** or __text__ -> <strong>text</strong>)
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.+?)__/g, '<strong>$1</strong>')
        // Convert italic (*text* or _text_ -> <em>text</em>)
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/_(.+?)_/g, '<em>$1</em>')
        // Convert bullet points (- item or * item -> <li>item</li>)
        .replace(/^[•\-\*] (.+)$/gm, '<li>$1</li>')
        // Wrap consecutive list items in <ul>
        .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
        // Convert line breaks
        .replace(/\n/g, '<br>');
}

document.addEventListener('DOMContentLoaded', async () => {
    await loadPlayersAndGames();
});

async function loadPlayersAndGames() {
    try {
        const playersResponse = await fetch('/api/players');
        allPlayers = await playersResponse.json();
        
        const gamesResponse = await fetch('/api/games');
        allGames = await gamesResponse.json();
        
        // Populate dropdowns
        const playerSelect = document.getElementById('player-select');
        allPlayers.forEach(player => {
            const option = document.createElement('option');
            option.value = player.name;
            option.textContent = player.name;
            playerSelect.appendChild(option);
        });
        
        const gameSelect = document.getElementById('game-select');
        allGames.forEach(game => {
            const option = document.createElement('option');
            option.value = game.gameId;
            option.textContent = `${game.date} - ${game.location === 'away' ? '@' : 'vs'} ${game.opponent}`;
            gameSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

function showAskCoach() {
    document.getElementById('team-summary').style.display = 'none';
    document.getElementById('ask-coach-section').style.display = 'block';
    document.getElementById('player-analysis-section').style.display = 'none';
    document.getElementById('game-analysis-section').style.display = 'none';
    document.getElementById('coach-response').style.display = 'none';
}

function showPlayerAnalysis() {
    document.getElementById('team-summary').style.display = 'none';
    document.getElementById('ask-coach-section').style.display = 'none';
    document.getElementById('player-analysis-section').style.display = 'block';
    document.getElementById('game-analysis-section').style.display = 'none';
}

function showGameAnalysis() {
    document.getElementById('team-summary').style.display = 'none';
    document.getElementById('ask-coach-section').style.display = 'none';
    document.getElementById('player-analysis-section').style.display = 'none';
    document.getElementById('game-analysis-section').style.display = 'block';
}

async function regenerateTeamSummary() {
    if (!confirm('Regenerate team summary? This will create a new AI analysis for all users.')) {
        return;
    }
    
    try {
        const content = document.getElementById('team-summary-content');
        content.innerHTML = '<div class="loading">Clearing cache and regenerating...</div>';
        
        // Delete the cached summary
        await fetch('/api/ai/team-summary', { method: 'DELETE' });
        
        // Wait a moment then reload
        await new Promise(resolve => setTimeout(resolve, 500));
        await loadTeamSummary();
    } catch (error) {
        document.getElementById('team-summary-content').innerHTML = `<div class="error-message">Error regenerating: ${error.message}</div>`;
    }
}

async function loadTeamSummary() {
    try {
        document.getElementById('team-summary').style.display = 'block';
        document.getElementById('ask-coach-section').style.display = 'none';
        document.getElementById('player-analysis-section').style.display = 'none';
        document.getElementById('game-analysis-section').style.display = 'none';
        
        const response = await fetch('/api/ai/team-summary');
        if (!response.ok) throw new Error('Failed to load summary');
        
        const data = await response.json();
        const content = document.getElementById('team-summary-content');
        
        if (data.error) {
            content.innerHTML = `<div class="error-message">⚠️ ${data.error}</div>
                <p>Please configure your OpenAI API key as an environment variable: <code>OPENAI_API_KEY</code></p>`;
        } else {
            content.innerHTML = `<div class="ai-response">${formatAIResponse(data.summary)}</div>`;
        }
    } catch (error) {
        document.getElementById('team-summary-content').innerHTML = `<div class="error-message">Error: ${error.message}</div>`;
    }
}

async function askCoach() {
    try {
        const question = document.getElementById('question-input').value.trim();
        const analysisType = document.getElementById('analysis-type').value;
        const askBtn = document.getElementById('ask-btn');
        
        if (!question) {
            alert('Please ask a question');
            return;
        }
        
        askBtn.disabled = true;
        askBtn.textContent = 'Analyzing...';
        document.getElementById('coach-response').style.display = 'block';
        document.getElementById('coach-answer-content').innerHTML = '<div class="loading">AI Coach is thinking...</div>';
        
        const response = await fetch('/api/ai/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: question, type: analysisType })
        });
        
        const data = await response.json();
        
        if (data.error) {
            document.getElementById('coach-answer-content').innerHTML = 
                `<div class="error-message">⚠️ ${data.error}</div>
                <p>Please configure your OpenAI API key as an environment variable: <code>OPENAI_API_KEY</code></p>`;
        } else {
            document.getElementById('coach-answer-content').innerHTML = 
                `<div class="ai-response"><strong>AI Response:</strong><br>${formatAIResponse(data.analysis)}</div>`;
        }
        
        askBtn.disabled = false;
        askBtn.textContent = 'Get AI Insight';
    } catch (error) {
        document.getElementById('coach-answer-content').innerHTML = 
            `<div class="error-message">Error: ${error.message}</div>`;
        document.getElementById('ask-btn').disabled = false;
        document.getElementById('ask-btn').textContent = 'Get AI Insight';
    }
}

async function analyzeSelectedPlayer() {
    const playerName = document.getElementById('player-select').value;
    if (!playerName) return;
    
    try {
        const content = document.getElementById('player-insights-content');
        content.innerHTML = '<div class="loading">AI Coach analyzing player...</div>';
        
        const response = await fetch(`/api/ai/player-insights/${playerName}`);
        const data = await response.json();
        
        if (data.error) {
            content.innerHTML = `<div class="error-message">⚠️ ${data.error}</div>
                <p>Please configure your OpenAI API key as an environment variable: <code>OPENAI_API_KEY</code></p>`;
        } else {
            content.innerHTML = `<div class="ai-response"><strong>${data.player} - AI Insights:</strong><br>${formatAIResponse(data.insights)}</div>`;
        }
    } catch (error) {
        document.getElementById('player-insights-content').innerHTML = 
            `<div class="error-message">Error: ${error.message}</div>`;
    }
}

async function analyzeSelectedGame() {
    const gameId = document.getElementById('game-select').value;
    if (!gameId) return;
    
    try {
        const content = document.getElementById('game-insights-content');
        content.innerHTML = '<div class="loading">AI Coach analyzing game...</div>';
        
        const response = await fetch(`/api/ai/game-analysis/${gameId}`);
        const data = await response.json();
        
        if (data.error) {
            content.innerHTML = `<div class="error-message">⚠️ ${data.error}</div>
                <p>Please configure your OpenAI API key as an environment variable: <code>OPENAI_API_KEY</code></p>`;
        } else {
            content.innerHTML = `<div class="ai-response"><strong>Game vs ${data.game} - AI Analysis:</strong><br>${formatAIResponse(data.analysis)}</div>`;
        }
    } catch (error) {
        document.getElementById('game-insights-content').innerHTML = 
            `<div class="error-message">Error: ${error.message}</div>`;
    }
}

function toggleAIChat() {
    const chatBox = document.getElementById('chat-box');
    chatBox.style.display = chatBox.style.display === 'none' ? 'block' : 'none';
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    input.value = '';
    
    // Add user message to chat
    const messages = document.getElementById('chat-messages');
    const userMsg = document.createElement('div');
    userMsg.className = 'chat-message user-message';
    userMsg.textContent = message;
    messages.appendChild(userMsg);
    
    try {
        const response = await fetch('/api/ai/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: message, type: 'general' })
        });
        
        const data = await response.json();
        
        const aiMsg = document.createElement('div');
        aiMsg.className = 'chat-message ai-message';
        aiMsg.innerHTML = data.error ? `Error: ${data.error}` : formatAIResponse(data.analysis);
        messages.appendChild(aiMsg);
        
        messages.scrollTop = messages.scrollHeight;
    } catch (error) {
        const errorMsg = document.createElement('div');
        errorMsg.className = 'chat-message error-message';
        errorMsg.textContent = `Error: ${error.message}`;
        messages.appendChild(errorMsg);
    }
}

function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}
