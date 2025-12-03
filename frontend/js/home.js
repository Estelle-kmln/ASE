// Configuration
const GAME_API_URL = 'http://localhost:8080/api/games';

// State
let currentUser = null;
let currentGameId = null;
let pollInterval = null;

// Check authentication immediately (before DOM loads)
(function() {
    console.log('Auth check starting...');
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    console.log('Token:', token ? 'exists' : 'missing');
    console.log('User:', user ? 'exists' : 'missing');
    
    if (!token || !user) {
        // Clear any stale data
        console.log('No token or user, redirecting to login...');
        localStorage.clear();
        window.location.href = 'login.html';
        return;
    }
    
    try {
        currentUser = JSON.parse(user);
        console.log('Parsed user:', currentUser);
        if (!currentUser || !currentUser.username) {
            throw new Error('Invalid user data');
        }
    } catch (e) {
        // Invalid data in localStorage
        console.error('Error parsing user data:', e);
        localStorage.clear();
        window.location.href = 'login.html';
        return;
    }
    console.log('Auth check passed');
})();

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    displayUserInfo();
    loadUserGames(); // Load user's games on page load
    
    // Refresh games list every 5 seconds to auto-remove finished games
    setInterval(loadUserGames, 5000);
});

function displayUserInfo() {
    console.log('Current user:', currentUser);
    if (currentUser && currentUser.username) {
        document.getElementById('user-info').textContent = `Logged in as: ${currentUser.username}`;
    } else {
        console.error('User data is invalid:', currentUser);
        document.getElementById('user-info').textContent = `Logged in as: Unknown`;
    }
}

function initializeEventListeners() {
    document.getElementById('menu-btn').addEventListener('click', toggleMenu);
    document.getElementById('launch-game-btn').addEventListener('click', launchGame);
    document.getElementById('join-game-btn').addEventListener('click', () => openModal('join-modal'));
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        const menu = document.getElementById('dropdown-menu');
        const menuBtn = document.getElementById('menu-btn');
        if (!menu.contains(e.target) && !menuBtn.contains(e.target)) {
            menu.classList.remove('active');
        }
    });
}

function toggleMenu() {
    const menu = document.getElementById('dropdown-menu');
    menu.classList.toggle('active');
}

function navigateTo(page) {
    window.location.href = page;
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

async function loadUserGames() {
    const token = localStorage.getItem('token');
    if (!currentUser || !currentUser.username) {
        console.log('No current user found:', currentUser);
        return;
    }
    
    console.log('Loading games for user:', currentUser.username);
    
    try {
        const response = await fetch(`${GAME_API_URL}/user/${currentUser.username}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            console.error('Failed to load games:', response.status);
            return;
        }
        
        const data = await response.json();
        const games = data.games || [];
        
        console.log('Loaded games:', games);
        
        // Separate pending and active games - use case-insensitive comparison
        const currentUsername = currentUser.username.toLowerCase();
        
        const pendingGames = games.filter(game => 
            game.is_active &&  // Only show active game invitations
            game.player2_name && 
            game.player2_name.toLowerCase() === currentUsername && 
            !game.player2_id
        );
        const activeGames = games.filter(game => 
            game.is_active && (game.player1_id || game.player2_id)
        );
        
        console.log('Pending games:', pendingGames);
        console.log('Active games:', activeGames);
        
        displayPendingGames(pendingGames);
        displayActiveGames(activeGames);
        
        // Show the section if there are any games
        if (pendingGames.length > 0 || activeGames.length > 0) {
            document.getElementById('my-games-section').style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading games:', error);
    }
}

function displayPendingGames(games) {
    const container = document.getElementById('pending-games-container');
    const list = document.getElementById('pending-games-list');
    
    if (games.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    list.innerHTML = games.map(game => `
        <div style="background: rgba(255, 215, 0, 0.1); border: 2px solid #ffd700; border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="color: white;">
                    <strong>${game.player1_name}</strong> invited you to play
                    <br>
                    <small style="color: #ccc;">Game ID: ${game.game_id.substring(0, 8)}...</small>
                </div>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="btn" style="margin: 0; padding: 0.5rem 1rem;" onclick="joinPendingGame('${game.game_id}')">
                        Join Game
                    </button>
                    <button class="btn" style="margin: 0; padding: 0.5rem 1rem; background: #e74c3c;" onclick="ignoreInvitation('${game.game_id}')">
                        Ignore
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function displayActiveGames(games) {
    const container = document.getElementById('active-games-container');
    const list = document.getElementById('active-games-list');
    
    if (games.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    list.innerHTML = games.map(game => {
        const opponent = game.player1_name === currentUser.username ? game.player2_name : game.player1_name;
        return `
        <div style="background: rgba(76, 175, 80, 0.1); border: 2px solid #4CAF50; border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="color: white;">
                    <strong>vs ${opponent}</strong>
                    <br>
                    <small style="color: #ccc;">Turn ${game.turn || 1}</small>
                </div>
                <button class="btn" style="margin: 0; padding: 0.5rem 1rem; background: #4CAF50;" onclick="continueGame('${game.game_id}')">
                    Continue
                </button>
            </div>
        </div>
    `}).join('');
}

async function joinPendingGame(gameId) {
    window.location.href = `game.html?game_id=${gameId}`;
}

function continueGame(gameId) {
    window.location.href = `game.html?game_id=${gameId}`;
}

async function ignoreInvitation(gameId) {
    const token = localStorage.getItem('token');
    
    try {
        // Call the end game endpoint to mark the game as inactive
        await fetch(`${GAME_API_URL}/${gameId}/end`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
    } catch (error) {
        console.error('Error ending game:', error);
    }
    
    // Refresh the games list to remove the ignored invitation
    await loadUserGames();
}

async function launchGame() {
    const token = localStorage.getItem('token');
    
    // Prompt for opponent's username
    const player2Name = prompt('Enter opponent username:');
    if (!player2Name || player2Name.trim() === '') {
        alert('Opponent username is required');
        return;
    }
    
    try {
        const response = await fetch(`${GAME_API_URL}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                player2_name: player2Name.trim()
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentGameId = data.game_id;
            // Redirect directly to game page (decks are auto-created by backend)
            window.location.href = `game.html?game_id=${data.game_id}`;
        } else {
            alert('Failed to create game: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error creating game:', error);
        alert('Network error. Please try again.');
    }
}

function startPollingForOpponent(gameId) {
    pollInterval = setInterval(async () => {
        const token = localStorage.getItem('token');
        
        try {
            const response = await fetch(`${GAME_API_URL}/${gameId}/status`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            const data = await response.json();
            
            if (data.status === 'waiting_for_decks' || data.player2_id) {
                // Opponent joined!
                clearInterval(pollInterval);
                closeModal('launch-modal');
                
                // Redirect to deck selection
                window.location.href = `deck-selection.html?game_id=${gameId}`;
            }
        } catch (error) {
            console.error('Error polling game status:', error);
        }
    }, 2000); // Poll every 2 seconds
}

async function joinGame() {
    const gameCode = document.getElementById('game-code-input').value.trim().toUpperCase();
    const alertContainer = document.getElementById('join-alert');
    
    if (!gameCode) {
        alertContainer.innerHTML = '<div class="alert alert-error">Please enter a game code</div>';
        return;
    }
    
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${GAME_API_URL}/${gameCode}/join`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            closeModal('join-modal');
            // Redirect to deck selection
            window.location.href = `deck-selection.html?game_id=${gameCode}`;
        } else {
            alertContainer.innerHTML = `<div class="alert alert-error">${data.error || 'Failed to join game'}</div>`;
        }
    } catch (error) {
        console.error('Error joining game:', error);
        alertContainer.innerHTML = '<div class="alert alert-error">Network error. Please try again.</div>';
    }
}

function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    
    if (modalId === 'launch-modal' && pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
    
    if (modalId === 'join-modal') {
        document.getElementById('game-code-input').value = '';
        document.getElementById('join-alert').innerHTML = '';
    }
}

// Clean up polling on page unload
window.addEventListener('beforeunload', () => {
    if (pollInterval) {
        clearInterval(pollInterval);
    }
});
