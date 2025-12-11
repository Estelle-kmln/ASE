// Configuration
const LEADERBOARD_API_URL = 'https://localhost:8443/api/leaderboard';

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
    loadVisibilityPreference();
    loadRankings();
    setupVisibilityToggle();
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

function goHome() {
    window.location.href = 'welcome.html';
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

async function loadVisibilityPreference() {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${LEADERBOARD_API_URL}/visibility`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const toggle = document.getElementById('visibility-toggle');
            // Checkbox is "Hide from others", so inverse of show_on_leaderboard
            toggle.checked = !data.show_on_leaderboard;
        }
    } catch (error) {
        console.error('Error loading visibility preference:', error);
    }
}

function setupVisibilityToggle() {
    const toggle = document.getElementById('visibility-toggle');
    
    toggle.addEventListener('change', async () => {
        const token = localStorage.getItem('token');
        // Checkbox is "Hide from others", so inverse of show_on_leaderboard
        const showOnLeaderboard = !toggle.checked;
        
        try {
            const response = await fetch(`${LEADERBOARD_API_URL}/visibility`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    show_on_leaderboard: showOnLeaderboard
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Reload rankings to reflect the change
                await loadRankings();
                showNotification('Privacy settings updated successfully');
            } else {
                showError('Failed to update privacy settings: ' + (data.error || 'Unknown error'));
                // Revert the toggle
                toggle.checked = !toggle.checked;
            }
        } catch (error) {
            console.error('Error updating visibility:', error);
            showError('Failed to update privacy settings');
            // Revert the toggle
            toggle.checked = !toggle.checked;
        }
    });
}

async function loadRankings() {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${LEADERBOARD_API_URL}/rankings`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayRankings(data.rankings);
        } else {
            showError('Failed to load rankings: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error loading rankings:', error);
        showError('Failed to load rankings');
    }
}

function displayRankings(rankings) {
    const tbody = document.getElementById('rankings-body');
    const noDataMessage = document.getElementById('no-data-message');
    
    if (!rankings || rankings.length === 0) {
        tbody.innerHTML = '';
        noDataMessage.style.display = 'block';
        return;
    }
    
    noDataMessage.style.display = 'none';
    tbody.innerHTML = '';
    
    const currentUser = JSON.parse(localStorage.getItem('user'));
    const currentUsername = currentUser?.username;
    
    rankings.forEach(ranking => {
        const row = document.createElement('tr');
        
        // Highlight current user's row
        if (ranking.username === currentUsername) {
            row.classList.add('current-user-row');
        }
        
        // Rank cell with medal
        const rankCell = document.createElement('td');
        const rankContent = getMedalForRank(ranking.rank);
        rankCell.innerHTML = rankContent;
        row.appendChild(rankCell);
        
        // Username cell
        const usernameCell = document.createElement('td');
        usernameCell.textContent = ranking.username;
        if (ranking.username === currentUsername) {
            usernameCell.innerHTML += ' <span class="you-label">(You)</span>';
        }
        row.appendChild(usernameCell);
        
        // Wins cell
        const winsCell = document.createElement('td');
        winsCell.textContent = ranking.wins;
        row.appendChild(winsCell);
        
        // Total score cell
        const scoreCell = document.createElement('td');
        scoreCell.textContent = ranking.total_score;
        row.appendChild(scoreCell);
        
        // Games played cell
        const gamesCell = document.createElement('td');
        gamesCell.textContent = ranking.games_played;
        row.appendChild(gamesCell);
        
        tbody.appendChild(row);
    });
}

function getMedalForRank(rank) {
    switch(rank) {
        case 1:
            return '<span class="medal gold-medal">🥇</span>';
        case 2:
            return '<span class="medal silver-medal">🥈</span>';
        case 3:
            return '<span class="medal bronze-medal">🥉</span>';
        default:
            return rank;
    }
}

function showError(message) {
    const tbody = document.getElementById('rankings-body');
    tbody.innerHTML = `
        <tr>
            <td colspan="5" class="error-message" style="text-align: center; color: #e74c3c; padding: 20px;">
                ${message}
            </td>
        </tr>
    `;
}

function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #27ae60;
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}
