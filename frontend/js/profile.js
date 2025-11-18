// Configuration
const AUTH_API_URL = 'http://localhost:8080/api/auth';

// State
let isEditMode = false;
let currentUser = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadProfile();
});

function checkAuth() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (!token || !user) {
        window.location.href = 'login.html';
        return;
    }
    
    currentUser = JSON.parse(user);
}

async function loadProfile() {
    const token = localStorage.getItem('token');
    
    try {
        const response = await fetch(`${AUTH_API_URL}/profile`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('username').value = data.username;
            document.getElementById('email').value = data.email;
            
            // Update localStorage with latest data
            currentUser = data;
            localStorage.setItem('user', JSON.stringify(data));
        } else {
            showAlert('Failed to load profile', 'error');
        }
    } catch (error) {
        console.error('Error loading profile:', error);
        showAlert('Network error. Please try again.', 'error');
    }
}

function toggleEdit() {
    isEditMode = !isEditMode;
    
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const editBtn = document.getElementById('edit-btn');
    const saveBtn = document.getElementById('save-btn');
    
    if (isEditMode) {
        usernameInput.disabled = false;
        emailInput.disabled = false;
        passwordInput.disabled = false;
        confirmPasswordInput.disabled = false;
        editBtn.textContent = '❌ Cancel';
        saveBtn.style.display = 'block';
    } else {
        usernameInput.disabled = true;
        emailInput.disabled = true;
        passwordInput.disabled = true;
        confirmPasswordInput.disabled = true;
        passwordInput.value = '';
        confirmPasswordInput.value = '';
        editBtn.textContent = '✏️ Edit';
        saveBtn.style.display = 'none';
        clearAlert();
        
        // Reload original values
        loadProfile();
    }
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
        if (password.length < 6) {
            showAlert('Password must be at least 6 characters long', 'error');
            return;
        }
    }
    
    const token = localStorage.getItem('token');
    const updateData = {
        username,
        email
    };
    
    if (password) {
        updateData.password = password;
    }
    
    try {
        const response = await fetch(`${AUTH_API_URL}/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
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
