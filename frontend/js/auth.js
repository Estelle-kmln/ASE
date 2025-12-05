// Configuration
const API_BASE_URL = 'https://localhost:8443/api/auth';

// State
let isLoginMode = true;

// DOM Elements
const form = document.getElementById('auth-form');
const formTitle = document.getElementById('form-title');
const submitBtn = document.getElementById('submit-btn');
const toggleLink = document.getElementById('toggle-link');
const toggleText = document.getElementById('toggle-text');
const confirmPasswordGroup = document.getElementById('confirm-password-group');
const alertContainer = document.getElementById('alert-container');

// Event Listeners
toggleLink.addEventListener('click', toggleAuthMode);
form.addEventListener('submit', handleSubmit);

// Functions
function toggleAuthMode() {
    isLoginMode = !isLoginMode;
    
    if (isLoginMode) {
        formTitle.textContent = 'Login to Battlecards!';
        submitBtn.textContent = 'Login';
        toggleText.innerHTML = "Don't have an account? <a id='toggle-link'>Register here</a>";
        confirmPasswordGroup.style.display = 'none';
    } else {
        formTitle.textContent = 'Register for Battlecards!';
        submitBtn.textContent = 'Register';
        toggleText.innerHTML = "Already have an account? <a id='toggle-link'>Login here</a>";
        confirmPasswordGroup.style.display = 'block';
    }
    
    // Reattach event listener to new toggle link
    document.getElementById('toggle-link').addEventListener('click', toggleAuthMode);
    clearAlert();
}

async function handleSubmit(e) {
    e.preventDefault();
    clearAlert();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (isLoginMode) {
        await login(username, password);
    } else {
        const confirmPassword = document.getElementById('confirm-password').value;
        
        if (password !== confirmPassword) {
            showAlert('Passwords do not match!', 'error');
            return;
        }
        
        await register(username, password);
    }
}

async function login(username, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store token and user info
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            showAlert('Login successful!', 'success');
            
            // Redirect to homepage
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);
        } else {
            showAlert(data.error || 'Login failed. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showAlert('Network error. Please try again.', 'error');
    }
}

async function register(username, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store token and user info (registration now returns access token)
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            showAlert('Registration successful!', 'success');
            
            // Redirect to homepage
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);
        } else {
            showAlert(data.error || 'Registration failed. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showAlert('Network error. Please try again.', 'error');
    }
}

function showAlert(message, type) {
    alertContainer.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
}

function clearAlert() {
    alertContainer.innerHTML = '';
}

// Check if user is already logged in
if (localStorage.getItem('token')) {
    window.location.href = 'index.html';
}
