// Configuration
const API_BASE_URL = 'http://localhost:8080/api/auth';

// State
let isLoginMode = true;
let lockoutTimer = null;
let lockedUsername = null;
let lockoutEndTime = null;

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
    
    // Clear any existing lockout timer when switching modes
    clearLockoutTimer();
    
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
        
        // Validate password strength for registration
        const passwordError = validatePassword(password);
        if (passwordError) {
            showAlert(passwordError, 'error');
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
            // Clear any existing lockout timer
            clearLockoutTimer();
            
            // Store tokens using token management utility
            if (window.TokenManagement) {
                window.TokenManagement.storeAuthTokens(data);
            } else {
                // Fallback to old method if token management not loaded
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                if (data.refresh_token) {
                    localStorage.setItem('refresh_token', data.refresh_token);
                }
                if (data.expires_in) {
                    const expiryTime = Date.now() + ((data.expires_in - 60) * 1000);
                    localStorage.setItem('token_expiry', expiryTime.toString());
                }
            }
            
            showAlert('Login successful!', 'success');
            
            // Redirect to homepage
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);
        } else if (response.status === 423) {
            // Account locked - start countdown timer
            handleAccountLockout(username, data);
        } else if (response.status === 401 && data.remaining_attempts !== undefined) {
            // Failed login with remaining attempts warning
            const attemptsMessage = data.remaining_attempts > 0
                ? `Invalid username or password. You have ${data.remaining_attempts} attempt${data.remaining_attempts !== 1 ? 's' : ''} remaining before your account is locked.`
                : 'Invalid username or password.';
            showAlert(attemptsMessage, 'error');
        } else {
            showAlert(data.error || 'Login failed. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showAlert('Network error. Please try again.', 'error');
    }
}

function handleAccountLockout(username, data) {
    lockedUsername = username;
    
    // Debug logging
    console.log('Lockout data received:', data);
    console.log('locked_until:', data.locked_until);
    console.log('retry_after:', data.retry_after);
    
    if (data.locked_until) {
        // The server returns UTC time without 'Z' suffix, so we need to add it
        // to ensure JavaScript parses it correctly as UTC
        let isoTimestamp = data.locked_until;
        if (!isoTimestamp.endsWith('Z') && !isoTimestamp.includes('+')) {
            isoTimestamp = isoTimestamp + 'Z';
        }
        lockoutEndTime = new Date(isoTimestamp);
        console.log('Parsed lockout end time:', lockoutEndTime);
        console.log('Current time:', new Date());
        console.log('Time difference (ms):', lockoutEndTime - new Date());
    } else if (data.retry_after) {
        // Fallback: calculate end time from retry_after
        lockoutEndTime = new Date(Date.now() + (data.retry_after * 1000));
        console.log('Calculated lockout end time from retry_after:', lockoutEndTime);
    } else {
        console.error('No lockout time information available!');
        return;
    }
    
    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.style.opacity = '0.5';
    submitBtn.style.cursor = 'not-allowed';
    
    // Show initial lockout message
    updateLockoutDisplay();
    
    // Update display every 60 seconds
    lockoutTimer = setInterval(() => {
        updateLockoutDisplay();
    }, 60000); // 60 seconds
}

function updateLockoutDisplay() {
    const now = new Date();
    const remainingMs = lockoutEndTime - now;
    
    console.log('Update display - Remaining ms:', remainingMs);
    console.log('Current time:', now);
    console.log('Lockout end time:', lockoutEndTime);
    
    if (remainingMs <= 0) {
        // Lockout period has ended
        console.log('Lockout period ended');
        clearLockoutTimer();
        showAlert('Account lockout period has ended. You may try logging in again.', 'success');
        return;
    }
    
    const remainingMinutes = Math.ceil(remainingMs / 60000);
    const remainingSeconds = Math.ceil(remainingMs / 1000);
    
    console.log('Remaining minutes:', remainingMinutes);
    console.log('Remaining seconds:', remainingSeconds);
    
    let timeMessage;
    if (remainingMinutes > 1) {
        timeMessage = `${remainingMinutes} minutes`;
    } else if (remainingMinutes === 1) {
        timeMessage = '1 minute';
    } else {
        timeMessage = `${remainingSeconds} seconds`;
    }
    
    showAlert(
        `🔒 Account temporarily locked due to multiple failed login attempts.<br>` +
        `Please try again in <strong>${timeMessage}</strong>.<br>`,
        'error'
    );
}

function clearLockoutTimer() {
    if (lockoutTimer) {
        clearInterval(lockoutTimer);
        lockoutTimer = null;
    }
    lockedUsername = null;
    lockoutEndTime = null;
    
    // Re-enable submit button
    submitBtn.disabled = false;
    submitBtn.style.opacity = '1';
    submitBtn.style.cursor = 'pointer';
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
            // Store tokens using token management utility
            if (window.TokenManagement) {
                window.TokenManagement.storeAuthTokens(data);
            } else {
                // Fallback to old method if token management not loaded
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                if (data.refresh_token) {
                    localStorage.setItem('refresh_token', data.refresh_token);
                }
                if (data.expires_in) {
                    const expiryTime = Date.now() + ((data.expires_in - 60) * 1000);
                    localStorage.setItem('token_expiry', expiryTime.toString());
                }
            }
            
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
