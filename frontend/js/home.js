// Configuration
const GAME_API_URL = 'https://localhost:8443/api/games';

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
    
    // Initialize token management if available
    if (window.TokenManagement) {
        window.TokenManagement.initializeTokenManagement();
    }
})();

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    displayUserInfo();
    checkAdminStatus(); // Check if user is admin
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

async function checkAdminStatus() {
    try {
        const fetchFunc = window.TokenManagement ? window.TokenManagement.authenticatedFetch : fetch;
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Add auth header if not using authenticatedFetch
        if (!window.TokenManagement) {
            const token = localStorage.getItem('token');
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetchFunc('https://localhost:8443/api/auth/profile', {
            method: 'GET',
            headers: headers
        });

        if (response.ok) {
            const data = await response.json();
            console.log('Admin check response:', data);
            if (data.user && data.user.is_admin) {
                console.log('User is admin, showing admin link');
                document.getElementById('admin-link').style.display = 'block';
            } else {
                console.log('User is not admin');
            }
        } else {
            console.error('Admin check failed:', response.status);
        }
    } catch (error) {
        console.error('Error checking admin status:', error);
    }
}

function initializeEventListeners() {
    document.getElementById('menu-btn').addEventListener('click', toggleMenu);
    document.getElementById('launch-game-btn').addEventListener('click', launchGame);
    
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
    if (window.TokenManagement) {
        window.TokenManagement.logout();
    } else {
        // Fallback
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('token_expiry');
        localStorage.removeItem('user');
        window.location.href = 'login.html';
    }
}

async function loadUserGames() {
    if (!currentUser || !currentUser.username) {
        console.log('No current user found:', currentUser);
        return;
    }
    
    console.log('Loading games for user:', currentUser.username);
    
    try {
        const fetchFunc = window.TokenManagement ? window.TokenManagement.authenticatedFetch : fetch;
        const headers = {};
        
        // Add auth header if not using authenticatedFetch
        if (!window.TokenManagement) {
            const token = localStorage.getItem('token');
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetchFunc(`${GAME_API_URL}/user/${currentUser.username}`, {
            headers: headers
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
        
        const pendingGames = games.filter(game => {
            const isPlayer1 = game.player1_name && game.player1_name.toLowerCase() === currentUsername;
            const isPlayer2 = game.player2_name && game.player2_name.toLowerCase() === currentUsername;
            return game.game_status === 'pending' && (isPlayer1 || isPlayer2);
        });
        
        const activeGames = games.filter(game => 
            (game.game_status === 'active' || game.game_status === 'deck_selection') && 
            (game.player1_id || game.player2_id)
        );
        
        console.log('Pending games:', pendingGames);
        console.log('Active games:', activeGames);
        
        displayPendingGames(pendingGames);
        displayActiveGames(activeGames);
        
        // Show the section if there are any games, otherwise hide it
        const myGamesSection = document.getElementById('my-games-section');
        if (pendingGames.length > 0 || activeGames.length > 0) {
            myGamesSection.style.display = 'block';
        } else {
            myGamesSection.style.display = 'none';
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
    const currentUsername = currentUser.username.toLowerCase();
    
    list.innerHTML = games.map(game => {
        const isInviter = game.player1_name.toLowerCase() === currentUsername;
        const opponent = isInviter ? game.player2_name : game.player1_name;
        
        if (isInviter) {
            // You sent the invitation - waiting for opponent
            return `
                <div style="background: rgba(52, 152, 219, 0.1); border: 2px solid #3498db; border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="color: white;">
                            <strong>Waiting for ${opponent}</strong> to accept invitation
                            <br>
                            <small style="color: #ccc;">Game ID: ${game.game_id.substring(0, 8)}...</small>
                        </div>
                        <div style="display: flex; gap: 0.5rem;">
                            <button class="btn" style="margin: 0; padding: 0.5rem 1rem;" onclick="joinPendingGame('${game.game_id}')">
                                Start Deck Selection
                            </button>
                            <button class="btn" style="margin: 0; padding: 0.5rem 1rem; background: #e74c3c;" onclick="cancelInvitation('${game.game_id}')">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            `;
        } else {
            // You received the invitation
            return `
                <div style="background: rgba(255, 215, 0, 0.1); border: 2px solid #ffd700; border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="color: white;">
                            <strong>${opponent}</strong> invited you to play
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
            `;
        }
    }).join('');
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
    // Accept the invitation and transition to deck selection
    const token = localStorage.getItem('token');
    
    try {
        // First, mark the game as accepted (transition from pending to deck_selection)
        const acceptResponse = await fetch(`${GAME_API_URL}/${gameId}/accept`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (acceptResponse.ok) {
            // Successfully accepted, go to deck selection
            window.location.href = `deck-selection.html?game_id=${gameId}`;
        } else {
            // If accept endpoint doesn't exist or fails, check current status
            const response = await fetch(`${GAME_API_URL}/${gameId}/status`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // If game is in deck_selection or pending status, go to deck selection page
                if (data.status === 'deck_selection' || data.status === 'pending') {
                    window.location.href = `deck-selection.html?game_id=${gameId}`;
                } else {
                    // Otherwise go to game page
                    window.location.href = `game.html?game_id=${gameId}`;
                }
            } else {
                // If status check fails, just go to deck selection page
                window.location.href = `deck-selection.html?game_id=${gameId}`;
            }
        }
    } catch (error) {
        console.error('Error joining game:', error);
        // On error, try to go to deck selection page anyway
        window.location.href = `deck-selection.html?game_id=${gameId}`;
    }
}

async function continueGame(gameId) {
    // Check game status first to determine where to redirect
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${GAME_API_URL}/${gameId}/status`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // If game is in deck_selection status, go to deck selection page
            if (data.status === 'deck_selection') {
                window.location.href = `deck-selection.html?game_id=${gameId}`;
            } else {
                // Otherwise go to game page
                window.location.href = `game.html?game_id=${gameId}`;
            }
        } else {
            // If status check fails, just go to game page
            window.location.href = `game.html?game_id=${gameId}`;
        }
    } catch (error) {
        console.error('Error checking game status:', error);
        window.location.href = `game.html?game_id=${gameId}`;
    }
}

async function ignoreInvitation(gameId) {
    const token = localStorage.getItem('token');
    
    try {
        // Call the new ignore invitation endpoint
        const response = await fetch(`${GAME_API_URL}/${gameId}/ignore`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            console.error('Error ignoring invitation:', error);
            alert(error.error || 'Failed to ignore invitation');
            return;
        }
    } catch (error) {
        console.error('Error ignoring invitation:', error);
    }
    
    // Refresh the games list to remove the ignored invitation
    await loadUserGames();
}

async function cancelInvitation(gameId) {
    const token = localStorage.getItem('token');
    
    try {
        // Call the cancel invitation endpoint
        const response = await fetch(`${GAME_API_URL}/${gameId}/cancel`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            console.error('Error cancelling invitation:', error);
            alert(error.error || 'Failed to cancel invitation');
            return;
        }
    } catch (error) {
        console.error('Error cancelling invitation:', error);
    }
    
    // Refresh the games list to remove the cancelled invitation
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
            // Redirect to deck selection page (new flow requires deck selection)
            window.location.href = `deck-selection.html?game_id=${data.game_id}`;
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
