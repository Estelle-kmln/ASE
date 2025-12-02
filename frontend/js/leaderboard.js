// Configuration
const LEADERBOARD_API_URL = 'http://localhost:8080/api/leaderboard';
const GAME_API_URL = 'http://localhost:8080/api/games';
const ITEMS_PER_PAGE = 10;

// State
let currentPage = 1;
let totalPages = 1;
let allMatches = [];

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
    loadMatches();
});

async function loadMatches() {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${LEADERBOARD_API_URL}/my-matches`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            allMatches = data.matches || [];
            totalPages = Math.ceil(allMatches.length / ITEMS_PER_PAGE) || 1;
            renderPage();
        } else {
            showError('Failed to load matches');
        }
    } catch (error) {
        console.error('Error loading matches:', error);
        showError('Network error. Please try again.');
    }
}

function renderPage() {
    const tbody = document.getElementById('leaderboard-body');
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    const pageMatches = allMatches.slice(start, end);
    
    if (pageMatches.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">No matches found</td></tr>';
        return;
    }
    
    tbody.innerHTML = pageMatches.map(match => {
        const date = new Date(match.date).toLocaleDateString();
        const isWinner = match.result === 'win';
        const resultClass = isWinner ? 'winner' : 'loser';
        const resultText = isWinner ? 'Victory' : 'Defeat';
        
        return `
            <tr class="match-row" onclick="viewMatchDetails('${match.game_id}')" style="cursor: pointer;">
                <td>${date}</td>
                <td>${match.opponent}</td>
                <td>${match.my_score}</td>
                <td>${match.opponent_score}</td>
                <td class="${resultClass}">${resultText}</td>
            </tr>
        `;
    }).join('');
    
    updatePagination();
}

function updatePagination() {
    document.getElementById('current-page').textContent = currentPage;
    document.getElementById('total-pages').textContent = totalPages;
    
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
}

function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        renderPage();
    }
}

function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        renderPage();
    }
}

function showError(message) {
    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #e74c3c;">${message}</td></tr>`;
}

function goHome() {
    window.location.href = 'index.html';
}

async function viewMatchDetails(gameId) {
    const modal = document.getElementById('match-details-modal');
    const content = document.getElementById('match-details-content');
    
    // Show modal with loading state
    modal.style.display = 'block';
    content.innerHTML = '<div class="loading"></div>';
    
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${GAME_API_URL}/${gameId}/details`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayMatchDetails(data);
        } else {
            content.innerHTML = `<p style="color: #e74c3c;">${data.error || 'Failed to load match details'}</p>`;
        }
    } catch (error) {
        console.error('Error loading match details:', error);
        content.innerHTML = '<p style="color: #e74c3c;">Network error. Please try again.</p>';
    }
}

function displayMatchDetails(match) {
    const content = document.getElementById('match-details-content');
    const currentUser = JSON.parse(localStorage.getItem('user')).username;
    
    // Determine if current user is player1 or player2
    const isPlayer1 = match.player1_name === currentUser;
    const myName = isPlayer1 ? match.player1_name : match.player2_name;
    const opponentName = isPlayer1 ? match.player2_name : match.player1_name;
    const myScore = isPlayer1 ? match.player1_score : match.player2_score;
    const opponentScore = isPlayer1 ? match.player2_score : match.player1_score;
    
    let html = `
        <div class="match-summary">
            <h3>Match Summary</h3>
            <div class="players-info">
                <div class="player-info">
                    <strong>You (${myName})</strong>
                    <div class="score">${myScore}</div>
                </div>
                <div class="vs">VS</div>
                <div class="player-info">
                    <strong>${opponentName}</strong>
                    <div class="score">${opponentScore}</div>
                </div>
            </div>
            <div class="match-result">
                ${match.winner === myName ? '<span class="winner">Victory!</span>' : '<span class="loser">Defeat</span>'}
            </div>
        </div>
        
        <div class="rounds-history">
            <h3>Round History</h3>
    `;
    
    if (match.round_history && match.round_history.length > 0) {
        match.round_history.forEach((round, index) => {
            const myCard = isPlayer1 ? round.player1_card : round.player2_card;
            const opponentCard = isPlayer1 ? round.player2_card : round.player1_card;
            const myScoreAfter = isPlayer1 ? round.player1_score_after : round.player2_score_after;
            const opponentScoreAfter = isPlayer1 ? round.player2_score_after : round.player1_score_after;
            
            let roundResult = '';
            if (round.round_tied) {
                roundResult = '<span class="tie">Tie</span>';
            } else if (round.round_winner === (isPlayer1 ? 1 : 2)) {
                roundResult = '<span class="winner">Won</span>';
            } else {
                roundResult = '<span class="loser">Lost</span>';
            }
            
            const isTieBreaker = round.is_tiebreaker ? ' (Tie-Breaker)' : '';
            
            html += `
                <div class="round-detail">
                    <h4>Round ${round.round}${isTieBreaker}</h4>
                    <div class="cards-played">
                        <div class="card-display">
                            <div class="card-label">Your Card</div>
                            <div class="card ${myCard.type.toLowerCase()}">
                                <div class="card-type">${myCard.type}</div>
                                <div class="card-power">Power: ${myCard.power}</div>
                            </div>
                        </div>
                        <div class="vs-small">VS</div>
                        <div class="card-display">
                            <div class="card-label">Opponent's Card</div>
                            <div class="card ${opponentCard.type.toLowerCase()}">
                                <div class="card-type">${opponentCard.type}</div>
                                <div class="card-power">Power: ${opponentCard.power}</div>
                            </div>
                        </div>
                    </div>
                    <div class="round-outcome">
                        <div>Result: ${roundResult}</div>
                        <div class="round-score">Score: ${myScoreAfter} - ${opponentScoreAfter}</div>
                    </div>
                </div>
            `;
        });
    } else {
        html += '<p>No round history available.</p>';
    }
    
    html += '</div>';
    
    content.innerHTML = html;
}

function closeMatchDetails() {
    const modal = document.getElementById('match-details-modal');
    modal.style.display = 'none';
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById('match-details-modal');
    if (event.target === modal) {
        closeMatchDetails();
    }
}
