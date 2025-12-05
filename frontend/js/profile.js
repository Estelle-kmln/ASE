// Configuration
const AUTH_API_URL = 'http://localhost:8080/api/auth';

// State
let isEditMode = false;
let currentUser = null;

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
    setupMenu();
    loadProfile();
});

function setupMenu() {
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

async function loadProfile() {
    try {
        const fetchFunc = window.TokenManagement ? window.TokenManagement.authenticatedFetch : fetch;
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Add auth header if not using authenticatedFetch
        if (!window.TokenManagement) {
            const token = localStorage.getItem('token');
            if (!token) {
                console.error('No token found');
                localStorage.clear();
                window.location.href = 'login.html';
                return;
            }
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetchFunc(`${AUTH_API_URL}/profile`, {
            headers: headers
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log('Profile data:', data);
            // Backend returns { user: { id, username, created_at } }
            const userData = data.user || data;
            document.getElementById('username').value = userData.username || '';
            
            // Password is always shown as dots for security
            document.getElementById('password').value = '••••••••';
            
            // Update localStorage with latest data
            currentUser = userData;
            localStorage.setItem('user', JSON.stringify(userData));
        } else if (response.status === 401) {
            // Token expired or invalid
            console.error('Unauthorized - token may be expired');
            showAlert('Session expired. Please login again.', 'error');
            setTimeout(() => {
                localStorage.clear();
                window.location.href = 'login.html';
            }, 2000);
        } else {
            console.error('Failed to load profile:', data);
            showAlert('Failed to load profile: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error loading profile:', error);
        showAlert('Network error. Please check your connection and try again.', 'error');
    }
}

function toggleEdit() {
    isEditMode = !isEditMode;
    
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const editBtn = document.getElementById('edit-btn');
    const saveBtn = document.getElementById('save-btn');
    
    if (isEditMode) {
        usernameInput.disabled = false;
        passwordInput.disabled = false;
        passwordInput.value = ''; // Clear to allow new password entry
        passwordInput.placeholder = 'Enter new password (leave blank to keep current)';
        editBtn.textContent = '❌ Cancel';
        saveBtn.style.display = 'block';
    } else {
        usernameInput.disabled = true;
        passwordInput.disabled = true;
        passwordInput.value = '••••••••';
        passwordInput.placeholder = '••••••••';
        editBtn.textContent = '✏️ Edit';
        saveBtn.style.display = 'none';
        clearAlert();
        
        // Reload original values
        loadProfile();
    }
}

function validatePassword(password) {
    // Check minimum length (8 characters)
    if (password.length < 8) {
        return 'Password must be at least 8 characters long';
    }
    
    // Check for at least one number
    if (!/\d/.test(password)) {
        return 'Password must contain at least one number';
    }
    
    // Check for at least one special character from allowed list
    if (!/[!@$%^&*()_+=\[\]{}:;,.?/<>-]/.test(password)) {
        return 'Password must contain at least one special character (!@$%^&*()_+={}[]:;,.?/<>-)';
    }
    
    // Check that password only contains allowed characters
    if (!/^[a-zA-Z0-9!@$%^&*()_+=\[\]{}:;,.?/<>-]+$/.test(password)) {
        return 'Password contains invalid characters. Only letters, numbers, and these special characters are allowed: !@$%^&*()_+={}[]:;,.?/<>-';
    }
    
    return null; // Password is valid
}

document.getElementById('profile-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAlert();
    
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    // Validate passwords if they're being changed
    if (password || confirmPassword) {
        if (password !== confirmPassword) {
            showAlert('Passwords do not match!', 'error');
            return;
        }
        
        // Validate password strength
        const passwordError = validatePassword(password);
        if (passwordError) {
            showAlert(passwordError, 'error');
            return;
        }
    }
    
    const updateData = {
        username,
        email
    };
    
    if (password) {
        updateData.password = password;
    }
    
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
        
        const response = await fetchFunc(`${AUTH_API_URL}/profile`, {
            method: 'PUT',
            headers: headers,
            body: JSON.stringify(updateData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('Profile updated successfully!', 'success');
            
            // Update localStorage
            localStorage.setItem('user', JSON.stringify(data.user));
            currentUser = data.user;
            
            // Exit edit mode
            setTimeout(() => {
                toggleEdit();
            }, 1500);
        } else {
            showAlert(data.error || 'Failed to update profile', 'error');
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        showAlert('Network error. Please try again.', 'error');
    }
});

function showAlert(message, type) {
    const alertContainer = document.getElementById('alert-container');
    alertContainer.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
}

function clearAlert() {
    document.getElementById('alert-container').innerHTML = '';
}

function goHome() {
    window.location.href = 'index.html';
}
