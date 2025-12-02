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
        const response = await fetch(`${GAME_API_URL}/${gameId}`, {
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
    document.getElementById('player1-name').textContent = gameState.player1.name || 'Player 1';
    document.getElementById('player2-name').textContent = gameState.player2.name || 'Player 2';
    
    // Update scores
    document.getElementById('player1-score').textContent = gameState.player1.score || 0;
    document.getElementById('player2-score').textContent = gameState.player2.score || 0;
    
    // Update turn number
    document.getElementById('turn-number').textContent = gameState.turn || 1;
    
    // Check if we need to draw cards
    const isPlayer1 = currentUser.username === gameState.player1.name;
    const myHand = isPlayer1 ? gameState.player1.hand_size : gameState.player2.hand_size;
    
    if (myHand === 0) {
        // Need to draw cards
        document.getElementById('draw-cards-btn').style.display = 'block';
        document.getElementById('play-card-btn').style.display = 'none';
        document.getElementById('turn-indicator').textContent = 'Draw cards to start!';
        document.getElementById('turn-indicator').style.color = '#3498db';
        hand = [];
        renderHand();
    } else {
        // Have cards - can play
        document.getElementById('draw-cards-btn').style.display = 'none';
        document.getElementById('play-card-btn').style.display = 'block';
        updateTurnIndicator();
    }
    
    // Update played cards if available
    updatePlayedCards();
    
    // Check if game is over
    if (!gameState.is_active) {
        showGameOver();
    }
}

async function drawCards() {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${GAME_API_URL}/${gameId}/draw-hand`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            hand = data.hand || [];
            renderHand();
            await loadGameState();
        } else {
            alert('Failed to draw cards: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error drawing cards:', error);
        alert('Network error. Please try again.');
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
    const isPlayer1 = currentUser.username === gameState.player1.name;
    
    // Check if both players have drawn cards
    const myHandSize = isPlayer1 ? gameState.player1.hand_size : gameState.player2.hand_size;
    const opponentHandSize = isPlayer1 ? gameState.player2.hand_size : gameState.player1.hand_size;
    
    if (opponentHandSize === 0) {
        indicator.textContent = 'Waiting for opponent to draw cards...';
        indicator.style.color = '#7f8c8d';
        document.getElementById('play-card-btn').disabled = true;
        return;
    }
    
    // Both players have cards - check whose turn it is
    const currentPlayer = gameState.turn % 2 === 1 ? gameState.player1.name : gameState.player2.name;
    
    if (currentUser.username === currentPlayer) {
        indicator.textContent = 'Your turn to play!';
        indicator.style.color = '#f39c12';
        document.getElementById('play-card-btn').disabled = false;
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
            const response = await fetch(`${GAME_API_URL}/${gameId}`, {
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
