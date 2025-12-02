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
    setupMenu();
});

function setupMenu() {
    // Set user info in dropdown
    const userInfoElement = document.getElementById('user-info');
    if (userInfoElement && currentUser) {
        userInfoElement.textContent = currentUser.username;
    }
    
    // Menu toggle
    const menuBtn = document.getElementById('menu-btn');
    const dropdownMenu = document.getElementById('dropdown-menu');
    
    if (menuBtn && dropdownMenu) {
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdownMenu.classList.toggle('active');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', () => {
            dropdownMenu.classList.remove('active');
        });
    }
}

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
    console.log('Game state:', gameState);
    
    // Update player names
    document.getElementById('player1-name').textContent = gameState.player1.name || 'Player 1';
    document.getElementById('player2-name').textContent = gameState.player2.name || 'Player 2';
    
    // Update scores
    document.getElementById('player1-score').textContent = gameState.player1.score || 0;
    document.getElementById('player2-score').textContent = gameState.player2.score || 0;
    
    // Update turn number
    document.getElementById('turn-number').textContent = gameState.turn || 1;
    
    // Determine which player is current user
    const isPlayer1 = currentUser.username === gameState.player1.name;
    const myState = isPlayer1 ? gameState.player1 : gameState.player2;
    const opponentState = isPlayer1 ? gameState.player2 : gameState.player1;
    
    // STRICT GAME LOGIC:
    // 1. If I haven't drawn -> show draw button
    // 2. If I've drawn but not played -> show hand and play button
    // 3. If I've played -> show "waiting for opponent" message
    // 4. When both have played -> round auto-resolves and flags reset
    
    const drawButton = document.getElementById('draw-cards-btn');
    const playButton = document.getElementById('play-card-btn');
    const viewDetailsButton = document.getElementById('view-details-btn');
    const gameActions = document.querySelector('.game-actions');
    const indicator = document.getElementById('turn-indicator');
    
    if (!myState.has_drawn) {
        // Player needs to draw cards
        drawButton.style.display = 'block';
        if (gameActions) gameActions.style.display = 'none';
        indicator.textContent = 'Draw your 3 cards!';
        indicator.style.color = '#3498db';
        hand = [];
        renderHand();
    } else if (myState.has_drawn && !myState.has_played) {
        // Player has drawn, now needs to play
        drawButton.style.display = 'none';
        if (gameActions) gameActions.style.display = 'flex';
        playButton.disabled = hand.length === 0 || selectedCardIndex === null;
        viewDetailsButton.disabled = hand.length === 0 || selectedCardIndex === null;
        indicator.textContent = 'Select a card to play!';
        indicator.style.color = '#f39c12';
    } else if (myState.has_played && !opponentState.has_played) {
        // Player has played, waiting for opponent
        drawButton.style.display = 'none';
        if (gameActions) gameActions.style.display = 'none';
        indicator.textContent = 'Waiting for opponent to play...';
        indicator.style.color = '#7f8c8d';
        hand = [];
        renderHand();
    } else if (myState.has_played && opponentState.has_played) {
        // Both have played - round is being resolved
        // This state should be very brief - immediately refresh
        drawButton.style.display = 'none';
        if (gameActions) gameActions.style.display = 'none';
        indicator.textContent = 'Round resolving...';
        indicator.style.color = '#27ae60';
        hand = [];
        renderHand();
        
        // Force immediate refresh to get resolved state
        setTimeout(() => {
            loadGameState();
        }, 500);
    }
    
    // Update played cards if available
    updatePlayedCards();
    
    // Check if game is over
    if (!gameState.is_active) {
        // If game ended without a winner, it was quit by a player
        if (!gameState.winner) {
            // Game was quit - redirect to home
            clearInterval(pollInterval);
            alert('Game was ended by a player.');
            window.location.href = 'index.html';
        } else {
            // Game finished naturally - show game over modal
            showGameOver();
        }
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
    
    // Enable play button and view details button
    document.getElementById('play-card-btn').disabled = false;
    document.getElementById('view-details-btn').disabled = false;
}

function viewCardDetails() {
    if (selectedCardIndex === null || hand.length === 0) {
        alert('Please select a card first');
        return;
    }
    
    const selectedCard = hand[selectedCardIndex];
    
    // Update modal content
    document.getElementById('detail-card-emoji').textContent = cardEmojis[selectedCard.type];
    document.getElementById('detail-card-type').textContent = selectedCard.type;
    document.getElementById('detail-card-power').textContent = selectedCard.power;
    
    // Add strategy information with power mechanics
    const baseStrategyInfo = {
        'Rock': 'Rock beats Scissors but loses to Paper',
        'Paper': 'Paper beats Rock but loses to Scissors',
        'Scissors': 'Scissors beats Paper but loses to Rock'
    };
    
    const powerInfo = `\n\nPower Mechanics:\n• Higher power wins ties (e.g., Power ${selectedCard.power} beats Power ${selectedCard.power - 1})${selectedCard.power === 13 ? '\n• Power 13 is the strongest!' : ''}${selectedCard.power === 1 ? '\n• Power 1 is the weakest and beats nothing in a tie' : ''}\n• Same type + same power = tie (no winner)`;
    
    document.getElementById('detail-card-strategy').textContent = baseStrategyInfo[selectedCard.type] + powerInfo;
    
    // Show modal
    document.getElementById('card-details-modal').classList.add('active');
}

function closeCardDetails() {
    document.getElementById('card-details-modal').classList.remove('active');
}

async function playSelectedCard() {
    if (selectedCardIndex === null) {
        alert('Please select a card to play');
        return;
    }
    
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${GAME_API_URL}/${gameId}/play-card`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ 
                card_index: selectedCardIndex
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Card has been played, hand is now empty (2 cards discarded)
            hand = [];
            selectedCardIndex = null;
            
            // Update display
            renderHand();
            
            // Show played card indicator
            document.getElementById('turn-indicator').textContent = 'Card played! Waiting for opponent...';
            document.getElementById('turn-indicator').style.color = '#7f8c8d';
            
            // Refresh game state
            await loadGameState();
            
            // If both played, show round result
            if (data.round_resolved && data.round_result) {
                showRoundResult(data.round_result);
            }
        } else {
            alert('Failed to play card: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error playing card:', error);
        alert('Network error. Please try again.');
    }
}

function showRoundResult(result) {
    let message = '';
    
    if (result.round_tied) {
        message = 'Round tied! No points awarded.';
    } else {
        const winnerName = result.round_winner === 1 ? gameState.player1.name : gameState.player2.name;
        message = `${winnerName} wins the round!`;
    }
    
    // Show a temporary notification
    const indicator = document.getElementById('turn-indicator');
    indicator.textContent = message;
    indicator.style.color = '#27ae60';
    
    // Reset after 3 seconds
    setTimeout(() => {
        loadGameState();
    }, 3000);
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
    
    // Check if current user is the winner (backend returns winner as username)
    const isWinner = gameState.winner === currentUser.username;
    const isTie = !gameState.winner;
    
    if (isTie) {
        icon.textContent = '🤝';
        result.textContent = 'Tie Game!';
        result.classList.add('tie');
    } else if (isWinner) {
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
    
    finalScore.textContent = `Final Score: ${gameState.player1.score} - ${gameState.player2.score}`;
    
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

function quitAndNavigate(page) {
    // Deactivate the game by stopping polling
    if (pollInterval) {
        clearInterval(pollInterval);
    }
    // Navigate to the requested page
    window.location.href = page;
}

// Clean up polling on page unload
window.addEventListener('beforeunload', () => {
    if (pollInterval) {
        clearInterval(pollInterval);
    }
});
