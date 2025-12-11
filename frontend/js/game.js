// Configuration
const GAME_API_URL = 'https://localhost:8443/api/games';

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
        } else if (response.status === 401 || response.status === 404) {
            console.error('Unauthorized or user not found - clearing session');
            localStorage.clear();
            window.location.href = 'login.html';
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
    
    // Check if game is over FIRST (including tiebreaker declined scenario)
    if (gameState.game_status === 'completed' || gameState.game_status === 'abandoned' || gameState.game_status === 'ignored') {
        // Close any open tiebreaker modal if game ended
        const tiebreakerModal = document.getElementById('tiebreaker-modal');
        if (tiebreakerModal && tiebreakerModal.classList.contains('active')) {
            tiebreakerModal.classList.remove('active');
        }
        
        // If game ended without a winner and not from tiebreaker, it was quit by a player
        if (!gameState.winner && !gameState.awaiting_tiebreaker_response && 
            !(gameState.player1_tiebreaker_decision || gameState.player2_tiebreaker_decision)) {
            // Game was quit - redirect to home
            clearInterval(pollInterval);
            alert('Game was ended by a player.');
            window.location.href = 'index.html';
        } else {
            // Game finished naturally - show game over modal
            showGameOver();
        }
        return;
    }
    
    // Check if game is awaiting tiebreaker decision
    if (gameState.awaiting_tiebreaker_response) {
        // Show tiebreaker decision modal
        showTiebreakerDecisionModal();
        return;
    }
    
    // Check if both players agreed to tiebreaker and need to play their 22nd card
    if (gameState.player1_tiebreaker_decision === 'yes' && 
        gameState.player2_tiebreaker_decision === 'yes' && 
        gameState.game_status === 'active' &&
        !gameState.player1_played_card && !gameState.player2_played_card) {
        // Both agreed, show interface to play tiebreaker card
        showTiebreakerPlayInterface();
        return;
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
            console.error('Failed to draw cards:', data.error || 'Unknown error');
            alert('Failed to draw cards: ' + (data.error || 'Unknown error'));
            // Refresh game state to see if game has ended
            await loadGameState();
        }
    } catch (error) {
        console.error('Error drawing cards:', error);
        alert('Network error: ' + error.message + '\n\nPlease check your connection and SSL certificate.');
        // Try to refresh game state
        try {
            await loadGameState();
        } catch (e) {
            console.error('Could not refresh game state:', e);
        }
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
    const myCard = document.getElementById('player1-card');
    const opponentCard = document.getElementById('player2-card');
    
    console.log('Updating played cards. Game state:', gameState);
    
    // Determine which player is current user
    const isPlayer1 = currentUser.username === gameState.player1.name;
    const myState = isPlayer1 ? gameState.player1 : gameState.player2;
    const opponentState = isPlayer1 ? gameState.player2 : gameState.player1;
    
    console.log('I am player1:', isPlayer1);
    console.log('My state:', myState);
    console.log('Opponent state:', opponentState);
    console.log('My played card:', myState.played_card);
    console.log('Opponent played card:', opponentState.played_card);
    console.log('Last round:', gameState.last_round);
    
    // Determine what to show for MY card
    if (myState.played_card) {
        // I've played this turn - show my current card
        myCard.innerHTML = `
            <span>${cardEmojis[myState.played_card.type]}</span>
            <div class="card-power">P: ${myState.played_card.power}</div>
        `;
    } else if (gameState.last_round) {
        // I haven't played yet this turn - show last round's card
        const myLastCard = isPlayer1 ? gameState.last_round.player1_card : gameState.last_round.player2_card;
        if (myLastCard) {
            myCard.innerHTML = `
                <span>${cardEmojis[myLastCard.type]}</span>
                <div class="card-power">P: ${myLastCard.power}</div>
            `;
        } else {
            myCard.innerHTML = '<span>?</span>';
        }
    } else {
        // First round, no card played yet
        myCard.innerHTML = '<span>?</span>';
    }
    
    // Determine what to show for OPPONENT's card
    if (myState.played_card && opponentState.played_card) {
        // Both have played - show opponent's current card
        opponentCard.innerHTML = `
            <span>${cardEmojis[opponentState.played_card.type]}</span>
            <div class="card-power">P: ${opponentState.played_card.power}</div>
        `;
    } else if (!myState.played_card && gameState.last_round) {
        // I haven't played yet - show last round's opponent card
        const opponentLastCard = isPlayer1 ? gameState.last_round.player2_card : gameState.last_round.player1_card;
        if (opponentLastCard) {
            opponentCard.innerHTML = `
                <span>${cardEmojis[opponentLastCard.type]}</span>
                <div class="card-power">P: ${opponentLastCard.power}</div>
            `;
        } else {
            opponentCard.innerHTML = '<span>?</span>';
        }
    } else {
        // I've played but opponent hasn't, or first round
        opponentCard.innerHTML = '<span>?</span>';
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
            } else if (response.status === 401 || response.status === 404) {
                console.error('Unauthorized or user not found - clearing session');
                clearInterval(pollInterval);
                localStorage.clear();
                window.location.href = 'login.html';
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

async function quitGame() {
    if (confirm('Are you sure you want to quit the game?')) {
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
            // Continue with navigation even if the API call fails
        }
        
        if (pollInterval) {
            clearInterval(pollInterval);
        }
        window.location.href = 'index.html';
    }
}

async function quitAndNavigate(page) {
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
        // Continue with navigation even if the API call fails
    }
    
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

// Tiebreaker functionality
let tiebreakerModalShown = false;
let tiebreakerPlayInterfaceShown = false;

function showTiebreakerDecisionModal() {
    if (tiebreakerModalShown) return; // Only show once
    tiebreakerModalShown = true;
    
    // Check if current user already made a decision
    const isPlayer1 = currentUser.username === gameState.player1.name;
    const myDecision = isPlayer1 ? gameState.player1_tiebreaker_decision : gameState.player2_tiebreaker_decision;
    
    if (myDecision) {
        // Already decided, just show waiting message
        const indicator = document.getElementById('turn-indicator');
        indicator.textContent = 'Waiting for opponent\'s tiebreaker decision...';
        indicator.style.color = '#7f8c8d';
        return;
    }
    
    // Show tiebreaker modal
    const modal = document.getElementById('tiebreaker-modal');
    modal.classList.add('active');
}

function acceptTiebreaker() {
    const modal = document.getElementById('tiebreaker-modal');
    modal.classList.remove('active');
    submitTiebreakerDecision('yes');
}

function declineTiebreaker() {
    const modal = document.getElementById('tiebreaker-modal');
    modal.classList.remove('active');
    submitTiebreakerDecision('no');
}

async function submitTiebreakerDecision(decision) {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${GAME_API_URL}/${gameId}/tiebreaker-decision`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ decision })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (data.both_players_decided) {
                if (data.proceed_to_tiebreaker) {
                    // Both said yes, refresh to show tiebreaker play interface
                    await loadGameState();
                } else {
                    // At least one said no, game ended
                    alert(data.message);
                    await loadGameState(); // This will trigger game over modal
                }
            } else {
                // Waiting for other player
                const indicator = document.getElementById('turn-indicator');
                indicator.textContent = 'Waiting for opponent\'s tiebreaker decision...';
                indicator.style.color = '#7f8c8d';
            }
        } else {
            alert('Failed to submit decision: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error submitting tiebreaker decision:', error);
        alert('Network error. Please try again.');
    }
}

function showTiebreakerPlayInterface() {
    if (tiebreakerPlayInterfaceShown) return; // Only show once
    
    const isPlayer1 = currentUser.username === gameState.player1.name;
    const myPlayedCard = isPlayer1 ? gameState.player1.played_card : gameState.player2.played_card;
    
    if (myPlayedCard) {
        // Already played, waiting for opponent
        const indicator = document.getElementById('turn-indicator');
        indicator.textContent = 'Your tiebreaker card has been played! Waiting for opponent...';
        indicator.style.color = '#7f8c8d';
        
        // Check if both played to resolve
        const opponentPlayedCard = isPlayer1 ? gameState.player2.played_card : gameState.player1.played_card;
        if (opponentPlayedCard) {
            // Both played, will resolve shortly
            setTimeout(() => loadGameState(), 1000);
        }
        return;
    }
    
    tiebreakerPlayInterfaceShown = true;
    
    // Show tiebreaker play button with exciting styling
    const indicator = document.getElementById('turn-indicator');
    indicator.innerHTML = `
        <div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <p style="margin-bottom: 10px; color: white; font-size: 1.3rem; font-weight: bold;">🎲 TIEBREAKER ROUND! 🎲</p>
            <p style="margin-bottom: 15px; color: #f0f0f0; font-size: 1.1rem;">Both players are ready!</p>
            <button id="play-tiebreaker-btn" style="padding: 15px 40px; font-size: 1.2rem; cursor: pointer; background: #27ae60; color: white; border: none; border-radius: 8px; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.3); transition: all 0.3s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                🃏 Play Your Last Card! 🃏
            </button>
        </div>
    `;
    
    document.getElementById('play-tiebreaker-btn').onclick = playTiebreakerCard;
}

async function playTiebreakerCard() {
    const token = localStorage.getItem('token');
    
    // Update indicator immediately
    const indicator = document.getElementById('turn-indicator');
    indicator.innerHTML = '<div style="text-align: center; color: #f39c12; font-size: 1.2rem;">⏳ Playing your tiebreaker card...</div>';
    
    try {
        const response = await fetch(`${GAME_API_URL}/${gameId}/tiebreaker-play`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Show which card was played with dramatic effect
            indicator.innerHTML = `
                <div style="text-align: center; background: #27ae60; padding: 15px; border-radius: 8px; color: white;">
                    <p style="font-size: 1.3rem; margin: 0;">✨ You played: ${cardEmojis[data.tiebreaker_card_played.type]} Power ${data.tiebreaker_card_played.power} ✨</p>
                </div>
            `;
            
            if (data.both_played && data.tiebreaker_resolved) {
                // Wait a moment then show result
                setTimeout(() => {
                    if (data.is_tied) {
                        indicator.innerHTML = `
                            <div style="text-align: center; background: #95a5a6; padding: 15px; border-radius: 8px; color: white;">
                                <p style="font-size: 1.3rem; margin: 0;">🤝 The tiebreaker cards were identical! Game ends as a tie.</p>
                            </div>
                        `;
                    } else {
                        const isWinner = data.winner === currentUser.username;
                        const bgColor = isWinner ? '#27ae60' : '#e74c3c';
                        const emoji = isWinner ? '👑' : '💀';
                        indicator.innerHTML = `
                            <div style="text-align: center; background: ${bgColor}; padding: 15px; border-radius: 8px; color: white;">
                                <p style="font-size: 1.3rem; margin: 0;">${emoji} ${data.winner} wins the tiebreaker! ${emoji}</p>
                            </div>
                        `;
                    }
                    
                    // Load final game state after showing result
                    setTimeout(() => loadGameState(), 2000);
                }, 1000);
            } else {
                // Waiting for opponent
                setTimeout(() => loadGameState(), 1000);
            }
        } else {
            alert('Failed to play tiebreaker card: ' + (data.error || 'Unknown error'));
            await loadGameState();
        }
    } catch (error) {
        console.error('Error playing tiebreaker card:', error);
        alert('Network error. Please try again.');
        await loadGameState();
    }
}
