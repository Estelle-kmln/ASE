// Configuration
const GAME_API_URL = 'https://localhost:8443/api/games';
const DECK_SIZE = 22;

// State
let deckMode = 'manual';
let cardCounts = {
    rock: 0,
    paper: 0,
    scissors: 0
};
let gameId = null;
let pollInterval = null;

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
    getGameIdFromUrl();
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

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

function getGameIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    gameId = urlParams.get('game_id');
    
    if (!gameId) {
        alert('No game ID provided');
        window.location.href = 'index.html';
    }
}

function selectDeckMode(mode) {
    deckMode = mode;
    
    const manualBtn = document.getElementById('manual-btn');
    const randomBtn = document.getElementById('random-btn');
    const manualSelection = document.getElementById('manual-selection');
    
    if (mode === 'manual') {
        manualBtn.classList.add('active');
        randomBtn.classList.remove('active');
        manualSelection.classList.add('active');
    } else {
        manualBtn.classList.remove('active');
        randomBtn.classList.add('active');
        manualSelection.classList.remove('active');
    }
}

function incrementCard(type) {
    const total = getTotalCards();
    if (total < DECK_SIZE) {
        cardCounts[type]++;
        updateDisplay();
    }
}

function decrementCard(type) {
    if (cardCounts[type] > 0) {
        cardCounts[type]--;
        updateDisplay();
    }
}

function getTotalCards() {
    return cardCounts.rock + cardCounts.paper + cardCounts.scissors;
}

function updateDisplay() {
    document.getElementById('rock-count').textContent = cardCounts.rock;
    document.getElementById('paper-count').textContent = cardCounts.paper;
    document.getElementById('scissors-count').textContent = cardCounts.scissors;
    document.getElementById('total-cards').textContent = getTotalCards();
}

async function confirmDeck() {
    const token = localStorage.getItem('token');
    
    let deck;
    if (deckMode === 'manual') {
        const total = getTotalCards();
        if (total !== DECK_SIZE) {
            alert(`Please select exactly ${DECK_SIZE} cards. Currently selected: ${total}`);
            return;
        }
        
        // Create deck array based on counts
        deck = [];
        for (let i = 0; i < cardCounts.rock; i++) {
            deck.push({ type: 'Rock' });
        }
        for (let i = 0; i < cardCounts.paper; i++) {
            deck.push({ type: 'Paper' });
        }
        for (let i = 0; i < cardCounts.scissors; i++) {
            deck.push({ type: 'Scissors' });
        }
    } else {
        // Random deck generation
        deck = generateRandomDeck();
    }
    
    try {
        const response = await fetch(`${GAME_API_URL}/${gameId}/select-deck`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ deck })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Start polling to check if both players have selected decks
            startPollingForGameStart();
        } else if (response.status === 401 || response.status === 404) {
            console.error('Unauthorized or user not found - clearing session');
            localStorage.clear();
            window.location.href = 'login.html';
        } else {
            alert('Failed to select deck: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error selecting deck:', error);
        alert('Network error. Please try again.');
    }
}

function generateRandomDeck() {
    const deck = [];
    const types = ['Rock', 'Paper', 'Scissors'];
    
    for (let i = 0; i < DECK_SIZE; i++) {
        const randomType = types[Math.floor(Math.random() * types.length)];
        deck.push({ type: randomType });
    }
    
    return deck;
}

function startPollingForGameStart() {
    // Disable the confirm button and show waiting message
    const confirmBtn = document.getElementById('confirm-deck-btn');
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Waiting for opponent...';
    
    pollInterval = setInterval(async () => {
        const token = localStorage.getItem('token');
        
        try {
            const response = await fetch(`${GAME_API_URL}/${gameId}/status`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.status === 401 || response.status === 404) {
                console.error('Unauthorized or user not found - clearing session');
                clearInterval(pollInterval);
                localStorage.clear();
                window.location.href = 'login.html';
                return;
            } else if (!response.ok) {
                // Game might have been cancelled/ignored
                clearInterval(pollInterval);
                alert('The game invitation was cancelled or declined by your opponent.');
                window.location.href = 'index.html';
                return;
            }
            
            const data = await response.json();
            
            // Check if game was ignored/cancelled
            if (data.status === 'ignored') {
                clearInterval(pollInterval);
                alert('The game invitation was cancelled or declined by your opponent.');
                window.location.href = 'index.html';
                return;
            }
            
            if (data.status === 'in_progress') {
                // Both players have selected decks, game can start!
                clearInterval(pollInterval);
                window.location.href = `game.html?game_id=${gameId}`;
            }
        } catch (error) {
            console.error('Error polling game status:', error);
        }
    }, 2000); // Poll every 2 seconds
}

function goBack() {
    if (pollInterval) {
        clearInterval(pollInterval);
    }
    window.location.href = 'index.html';
}

// Clean up polling on page unload
window.addEventListener('beforeunload', () => {
    if (pollInterval) {
        clearInterval(pollInterval);
    }
});
