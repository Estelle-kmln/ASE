// Configuration
const LEADERBOARD_API_URL = 'https://localhost:8443/api/leaderboard';

// Check authentication immediately (before DOM loads)
(function() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (!token || !user) {
        localStorage.clear();
        window.location.href = 'login.html';
        return;
    }
    
    try {
        const userData = JSON.parse(user);
        if (!userData || !userData.username) {
            throw new Error('Invalid user data');
        }
    } catch (e) {
        localStorage.clear();
        window.location.href = 'login.html';
        return;
    }
})();

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupMenu();
    loadAllStatistics();
});

function setupMenu() {
    const user = localStorage.getItem('user');
    let currentUser = null;
    
    try {
        currentUser = JSON.parse(user);
    } catch (e) {
        console.error('Error parsing user data:', e);
    }
    
    const userInfoElement = document.getElementById('user-info');
    if (userInfoElement && currentUser) {
        userInfoElement.textContent = currentUser.username;
    }
    
    const menuBtn = document.getElementById('menu-btn');
    const dropdownMenu = document.getElementById('dropdown-menu');
    
    if (menuBtn && dropdownMenu) {
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.classList.toggle('active');
        });
        
        document.addEventListener('click', () => {
            dropdownMenu.classList.remove('active');
        });
    }
}

function navigateTo(page) {
    window.location.href = page;
}

function goHome() {
    window.location.href = 'index.html';
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

async function loadAllStatistics() {
    const user = JSON.parse(localStorage.getItem('user'));
    const isAdmin = user && user.is_admin === true;
    
    // Load personal stats and top players for everyone
    await Promise.all([
        loadPersonalStats(),
        loadTopPlayers()
    ]);
    
    // Only load recent games for admins
    if (isAdmin) {
        document.getElementById('recent-games-section').style.display = 'block';
        await loadRecentGames();
    }
}

async function loadPersonalStats() {
    const token = localStorage.getItem('token');
    const user = JSON.parse(localStorage.getItem('user'));
    const username = user.username;
    
    try {
        const response = await fetch(`${LEADERBOARD_API_URL}/player/${username}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayPersonalStats(data);
        } else if (response.status === 401 || response.status === 404) {
            console.error('Unauthorized or user not found - clearing session');
            localStorage.clear();
            window.location.href = 'login.html';
        } else {
            showPersonalStatsError();
        }
    } catch (error) {
        console.error('Error loading personal stats:', error);
        showPersonalStatsError();
    }
}

function displayPersonalStats(stats) {
    document.getElementById('total-games').textContent = stats.total_games || 0;
    document.getElementById('total-wins').textContent = stats.wins || 0;
    document.getElementById('total-losses').textContent = stats.losses || 0;
    document.getElementById('win-percentage').textContent = stats.win_percentage 
        ? `${stats.win_percentage}%` 
        : '0%';
}

function showPersonalStatsError() {
    document.getElementById('total-games').textContent = '0';
    document.getElementById('total-wins').textContent = '0';
    document.getElementById('total-losses').textContent = '0';
    document.getElementById('win-percentage').textContent = '0%';
}

async function loadTopPlayers() {
    const token = localStorage.getItem('token');
    
    // Show loading indicators
    document.getElementById('top-wins-loading').style.display = 'block';
    document.getElementById('top-percentage-loading').style.display = 'block';
    document.getElementById('most-active-loading').style.display = 'block';
    
    try {
        const response = await fetch(`${LEADERBOARD_API_URL}/top-players`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayTopPlayers(data);
        } else if (response.status === 401 || response.status === 404) {
            console.error('Unauthorized or user not found - clearing session');
            localStorage.clear();
            window.location.href = 'login.html';
        } else {
            showTopPlayersError();
        }
    } catch (error) {
        console.error('Error loading top players:', error);
        showTopPlayersError();
    } finally {
        // Hide loading indicators
        document.getElementById('top-wins-loading').style.display = 'none';
        document.getElementById('top-percentage-loading').style.display = 'none';
        document.getElementById('most-active-loading').style.display = 'none';
    }
}

function displayTopPlayers(data) {
    // Top by wins
    const topWinsList = document.getElementById('top-wins-list');
    topWinsList.innerHTML = '';
    if (data.top_by_wins && data.top_by_wins.length > 0) {
        data.top_by_wins.forEach((player, index) => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="player-rank">${index + 1}.</span>
                <span class="player-name">${player.player}</span>
                <span class="player-stat">${player.wins} wins</span>
            `;
            topWinsList.appendChild(li);
        });
    } else {
        topWinsList.innerHTML = '<li class="no-data">No data available</li>';
    }
    
    // Top by win percentage
    const topPercentageList = document.getElementById('top-percentage-list');
    topPercentageList.innerHTML = '';
    if (data.top_by_win_percentage && data.top_by_win_percentage.length > 0) {
        data.top_by_win_percentage.forEach((player, index) => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="player-rank">${index + 1}.</span>
                <span class="player-name">${player.player}</span>
                <span class="player-stat">${player.win_percentage}%</span>
            `;
            topPercentageList.appendChild(li);
        });
    } else {
        topPercentageList.innerHTML = '<li class="no-data">No data available</li>';
    }
    
    // Most active
    const mostActiveList = document.getElementById('most-active-list');
    mostActiveList.innerHTML = '';
    if (data.most_active && data.most_active.length > 0) {
        data.most_active.forEach((player, index) => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="player-rank">${index + 1}.</span>
                <span class="player-name">${player.player}</span>
                <span class="player-stat">${player.total_games} games</span>
            `;
            mostActiveList.appendChild(li);
        });
    } else {
        mostActiveList.innerHTML = '<li class="no-data">No data available</li>';
    }
}

function showTopPlayersError() {
    const errorMessage = '<li class="error-message">Failed to load data</li>';
    document.getElementById('top-wins-list').innerHTML = errorMessage;
    document.getElementById('top-percentage-list').innerHTML = errorMessage;
    document.getElementById('most-active-list').innerHTML = errorMessage;
}

async function loadRecentGames() {
    const token = localStorage.getItem('token');
    const loading = document.getElementById('recent-games-loading');
    const container = document.getElementById('recent-games-container');
    
    loading.style.display = 'block';
    
    try {
        const response = await fetch(`${LEADERBOARD_API_URL}/recent-games?limit=10`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayRecentGames(data.recent_games);
        } else {
            container.innerHTML = '<p class="error-message">Failed to load recent games</p>';
        }
    } catch (error) {
        console.error('Error loading recent games:', error);
        container.innerHTML = '<p class="error-message">Failed to load recent games</p>';
    } finally {
        loading.style.display = 'none';
    }
}

function displayRecentGames(games) {
    const container = document.getElementById('recent-games-container');
    
    if (!games || games.length === 0) {
        container.innerHTML = '<p class="no-data">No recent games available</p>';
        return;
    }
    
    const table = document.createElement('table');
    table.className = 'recent-games-table';
    
    table.innerHTML = `
        <thead>
            <tr>
                <th>Players</th>
                <th>Score</th>
                <th>Winner</th>
                <th>Turns</th>
                <th>Completed</th>
            </tr>
        </thead>
        <tbody>
            ${games.map(game => `
                <tr>
                    <td>${game.player1_name} vs ${game.player2_name}</td>
                    <td>${game.player1_score} - ${game.player2_score}</td>
                    <td>${game.winner || 'Tie'}</td>
                    <td>${game.duration_turns}</td>
                    <td>${formatDate(game.completed_at)}</td>
                </tr>
            `).join('')}
        </tbody>
    `;
    
    container.innerHTML = '';
    container.appendChild(table);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
}
