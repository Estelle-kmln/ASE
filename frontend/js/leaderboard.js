// Configuration
const LEADERBOARD_API_URL = 'http://localhost:8080/api/leaderboard';
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
            <tr>
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
