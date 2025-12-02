// Configuration
const GAME_API_URL = 'http://localhost:8080/api/games';

// State
let gameId = null;
let currentUser = null;
let gameState = null;
let selectedCardIndex = null;
let pollInterval = null;
let hand = [];

// Card type to emoji mapping
const cardEmojis = {
    'Rock': '🪨',
    'Paper': '📄',
    'Scissors': '✂️'
};

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
        currentUser = JSON.parse(user);
        if (!currentUser || !currentUser.username) {
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
    getGameIdFromUrl();
    loadGameState();
});

function getGameIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    gameId = urlParams.get('game_id');
    
    if (!gameId) {
        alert('No game ID provided');
        window.location.href = 'index.html';
    }
}

async function loadGameState() {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${GAME_API_URL}/${gameId}/state`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            gameState = data;
            updateGameDisplay();
            
            // Start polling for game updates
            startPolling();
        } else {
            alert('Failed to load game: ' + (data.error || 'Unknown error'));
            window.location.href = 'index.html';
        }
    } catch (error) {
        console.error('Error loading game:', error);
        alert('Network error. Please try again.');
    }
}

function updateGameDisplay() {
    // Update player names
    document.getElementById('player1-name').textContent = gameState.player1_name || 'Player 1';
    document.getElementById('player2-name').textContent = gameState.player2_name || 'Player 2';
    
    // Update scores
    document.getElementById('player1-score').textContent = gameState.player1_score || 0;
    document.getElementById('player2-score').textContent = gameState.player2_score || 0;
    
    // Update turn number
    document.getElementById('turn-number').textContent = gameState.current_turn || 1;
    
    // Update hand
    if (gameState.hand) {
        hand = gameState.hand;
        renderHand();
    }
    
    // Update turn indicator
    updateTurnIndicator();
    
    // Update played cards if available
    updatePlayedCards();
    
    // Check if game is over
    if (gameState.status === 'completed') {
        showGameOver();
    }
}

function renderHand() {
    const handContainer = document.getElementById('hand');
    handContainer.innerHTML = '';
    
    hand.forEach((card, index) => {
        const cardElement = document.createElement('div');
        cardElement.className = 'card';
        cardElement.innerHTML = `
            <span>${cardEmojis[card.type]}</span>
            <div class="card-power">P: ${card.power}</div>
        `;
        cardElement.onclick = () => selectCard(index);
        handContainer.appendChild(cardElement);
    });
}

function selectCard(index) {
    // Remove selection from all cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => card.classList.remove('selected'));
    
    // Select the clicked card
    cards[index].classList.add('selected');
    selectedCardIndex = index;
    
    // Enable play button
    document.getElementById('play-card-btn').disabled = false;
}

async function playSelectedCard() {
    if (selectedCardIndex === null) {
        alert('Please select a card to play');
        return;
    }
    
    const token = localStorage.getItem('token');
    const selectedCard = hand[selectedCardIndex];
    
    try {
        const response = await fetch(`${GAME_API_URL}/${gameId}/play-card`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ 
                card: selectedCard,
                card_index: selectedCardIndex
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Remove played card from hand
            hand.splice(selectedCardIndex, 1);
            selectedCardIndex = null;
            
            // Disable play button
            document.getElementById('play-card-btn').disabled = true;
            
            // Update display
            renderHand();
            
            // Show played card
            const player1Card = document.getElementById('player1-card');
            player1Card.innerHTML = `
                <span>${cardEmojis[selectedCard.type]}</span>
                <div class="card-power">P: ${selectedCard.power}</div>
            `;
            
            // Update turn indicator
            document.getElementById('turn-indicator').textContent = 'Waiting for opponent...';
            
            // Refresh game state
            await loadGameState();
        } else {
            alert('Failed to play card: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error playing card:', error);
        alert('Network error. Please try again.');
    }
}

function updateTurnIndicator() {
    const indicator = document.getElementById('turn-indicator');
    
    if (gameState.waiting_for_player === currentUser.id) {
        indicator.textContent = 'Your turn to play!';
        indicator.style.color = '#f39c12';
    } else {
        indicator.textContent = 'Waiting for opponent...';
        indicator.style.color = '#7f8c8d';
        document.getElementById('play-card-btn').disabled = true;
    }
}

function updatePlayedCards() {
    const player1Card = document.getElementById('player1-card');
    const player2Card = document.getElementById('player2-card');
    
    if (gameState.last_round) {
        const round = gameState.last_round;
        
        // Show player 1's card
        if (round.player1_card) {
            player1Card.innerHTML = `
                <span>${cardEmojis[round.player1_card.type]}</span>
                <div class="card-power">P: ${round.player1_card.power}</div>
            `;
        }
        
        // Show player 2's card
        if (round.player2_card) {
            player2Card.innerHTML = `
                <span>${cardEmojis[round.player2_card.type]}</span>
                <div class="card-power">P: ${round.player2_card.power}</div>
            `;
        }
    } else {
        player1Card.innerHTML = '<span>?</span>';
        player2Card.innerHTML = '<span>?</span>';
    }
}

function startPolling() {
    pollInterval = setInterval(async () => {
        const token = localStorage.getItem('token');
        
        try {
            const response = await fetch(`${GAME_API_URL}/${gameId}/state`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                gameState = data;
                updateGameDisplay();
            }
        } catch (error) {
            console.error('Error polling game state:', error);
        }
    }, 3000); // Poll every 3 seconds
}

function showGameOver() {
    clearInterval(pollInterval);
    
    const modal = document.getElementById('game-over-modal');
    const icon = document.getElementById('victory-icon');
    const result = document.getElementById('game-result');
    const finalScore = document.getElementById('final-score');
    
    const isWinner = gameState.winner_id === currentUser.id;
    
    if (isWinner) {
        icon.textContent = '👑';
        icon.classList.add('win');
        result.textContent = 'Victory!';
        result.classList.add('win');
    } else {
        icon.textContent = '💀';
        icon.classList.add('lose');
        result.textContent = 'Defeat!';
        result.classList.add('lose');
    }
    
    finalScore.textContent = `Final Score: ${gameState.player1_score} - ${gameState.player2_score}`;
    
    modal.classList.add('active');
}

function returnToHome() {
    window.location.href = 'index.html';
}

function quitGame() {
    if (confirm('Are you sure you want to quit the game?')) {
        if (pollInterval) {
            clearInterval(pollInterval);
        }
        window.location.href = 'index.html';
    }
}

// Clean up polling on page unload
window.addEventListener('beforeunload', () => {
    if (pollInterval) {
        clearInterval(pollInterval);
    }
});
