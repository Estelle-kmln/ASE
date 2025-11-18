// Configuration
const GAME_API_URL = 'http://localhost:8080/api/game';

// State
let currentUser = null;
let currentGameId = null;
let pollInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    initializeEventListeners();
});

function checkAuth() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (!token || !user) {
        window.location.href = 'login.html';
        return;
    }
    
    currentUser = JSON.parse(user);
    document.getElementById('user-info').textContent = `Logged in as: ${currentUser.username}`;
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

async function launchGame() {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${GAME_API_URL}/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentGameId = data.game_id;
            document.getElementById('game-code').textContent = data.game_id;
            openModal('launch-modal');
            
            // Start polling for opponent
            startPollingForOpponent(data.game_id);
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
