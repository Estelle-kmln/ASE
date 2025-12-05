/**
 * Token Management Utility
 * Handles automatic token refresh and provides a fetch wrapper
 * that automatically handles token expiration and refresh
 */

const TOKEN_REFRESH_API = 'http://localhost:8080/api/auth/refresh';
const LOGOUT_API = 'http://localhost:8080/api/auth/logout';

// Token refresh state
let isRefreshing = false;
let refreshPromise = null;

/**
 * Token Storage Interface
 */
const TokenStorage = {
    getAccessToken: () => localStorage.getItem('token'),
    getRefreshToken: () => localStorage.getItem('refresh_token'),
    getTokenExpiry: () => localStorage.getItem('token_expiry'),
    
    setAccessToken: (token) => localStorage.setItem('token', token),
    setRefreshToken: (token) => localStorage.setItem('refresh_token', token),
    setTokenExpiry: (expiresIn) => {
        // Store expiry timestamp (current time + expires_in seconds - 60s buffer)
        const expiryTime = Date.now() + ((expiresIn - 60) * 1000);
        localStorage.setItem('token_expiry', expiryTime.toString());
    },
    
    clearTokens: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('token_expiry');
        localStorage.removeItem('user');
    },
    
    isTokenExpiringSoon: () => {
        const expiry = TokenStorage.getTokenExpiry();
        if (!expiry) return true;
        
        // Check if token expires in less than 5 minutes
        const timeUntilExpiry = parseInt(expiry) - Date.now();
        return timeUntilExpiry < (5 * 60 * 1000); // 5 minutes
    },
    
    isTokenExpired: () => {
        const expiry = TokenStorage.getTokenExpiry();
        if (!expiry) return true;
        return parseInt(expiry) <= Date.now();
    }
};

/**
 * Refresh the access token using the refresh token
 * @returns {Promise<boolean>} True if refresh successful, false otherwise
 */
async function refreshAccessToken() {
    // If already refreshing, wait for that request to complete
    if (isRefreshing && refreshPromise) {
        return refreshPromise;
    }
    
    isRefreshing = true;
    
    refreshPromise = (async () => {
        try {
            const refreshToken = TokenStorage.getRefreshToken();
            
            if (!refreshToken) {
                console.error('No refresh token available');
                return false;
            }
            
            console.log('Refreshing access token...');
            
            const response = await fetch(TOKEN_REFRESH_API, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh_token: refreshToken
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Update access token and expiry
                TokenStorage.setAccessToken(data.access_token);
                TokenStorage.setTokenExpiry(data.expires_in);
                
                console.log('Access token refreshed successfully');
                return true;
            } else {
                console.error('Token refresh failed:', response.status);
                
                // If refresh token is invalid/expired, clear everything and redirect to login
                if (response.status === 401) {
                    TokenStorage.clearTokens();
                    window.location.href = 'login.html';
                }
                
                return false;
            }
        } catch (error) {
            console.error('Error refreshing token:', error);
            return false;
        } finally {
            isRefreshing = false;
            refreshPromise = null;
        }
    })();
    
    return refreshPromise;
}

/**
 * Logout and revoke tokens
 */
async function logout() {
    try {
        const token = TokenStorage.getAccessToken();
        const refreshToken = TokenStorage.getRefreshToken();
        
        if (token && refreshToken) {
            // Try to revoke the refresh token on the server
            await fetch(LOGOUT_API, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh_token: refreshToken
                })
            }).catch(() => {
                // Ignore errors - we'll clear tokens locally anyway
            });
        }
    } finally {
        // Always clear local tokens
        TokenStorage.clearTokens();
        window.location.href = 'login.html';
    }
}

/**
 * Enhanced fetch that automatically handles token refresh
 * @param {string} url - The URL to fetch
 * @param {Object} options - Fetch options
 * @returns {Promise<Response>}
 */
async function authenticatedFetch(url, options = {}) {
    // Check if token needs refresh before making the request
    if (TokenStorage.isTokenExpiringSoon()) {
        console.log('Token expiring soon, refreshing...');
        const refreshed = await refreshAccessToken();
        
        if (!refreshed) {
            console.error('Failed to refresh token');
            // Let the request proceed anyway - might fail with 401
        }
    }
    
    // Add Authorization header with current token
    const token = TokenStorage.getAccessToken();
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };
    
    // Make the request
    const response = await fetch(url, {
        ...options,
        headers
    });
    
    // If we get 401, try to refresh and retry once
    if (response.status === 401 && !options._isRetry) {
        console.log('Got 401, attempting token refresh and retry...');
        
        const refreshed = await refreshAccessToken();
        
        if (refreshed) {
            // Retry the request with new token
            return authenticatedFetch(url, {
                ...options,
                _isRetry: true // Prevent infinite retry loop
            });
        } else {
            // Refresh failed, redirect to login
            console.error('Token refresh failed, redirecting to login');
            TokenStorage.clearTokens();
            window.location.href = 'login.html';
            throw new Error('Authentication failed');
        }
    }
    
    return response;
}

/**
 * Store tokens after login/register
 * @param {Object} authResponse - Response from login/register endpoint
 */
function storeAuthTokens(authResponse) {
    if (authResponse.access_token) {
        TokenStorage.setAccessToken(authResponse.access_token);
    }
    
    if (authResponse.refresh_token) {
        TokenStorage.setRefreshToken(authResponse.refresh_token);
    }
    
    if (authResponse.expires_in) {
        TokenStorage.setTokenExpiry(authResponse.expires_in);
    }
    
    if (authResponse.user) {
        localStorage.setItem('user', JSON.stringify(authResponse.user));
    }
}

/**
 * Check if user is authenticated
 * @returns {boolean}
 */
function isAuthenticated() {
    const token = TokenStorage.getAccessToken();
    const refreshToken = TokenStorage.getRefreshToken();
    
    // Must have both tokens
    if (!token || !refreshToken) {
        return false;
    }
    
    // If access token is expired but we have a refresh token, we can refresh
    if (TokenStorage.isTokenExpired()) {
        // Trigger async refresh (non-blocking)
        refreshAccessToken().catch(() => {
            // If refresh fails, user will be redirected to login on next API call
        });
    }
    
    return true;
}

/**
 * Initialize token refresh on page load
 * Should be called when the page loads
 */
function initializeTokenManagement() {
    // Check if tokens need refresh
    if (isAuthenticated() && TokenStorage.isTokenExpiringSoon()) {
        refreshAccessToken().catch(() => {
            console.error('Initial token refresh failed');
        });
    }
    
    // Set up periodic check (every 5 minutes)
    setInterval(() => {
        if (isAuthenticated() && TokenStorage.isTokenExpiringSoon()) {
            refreshAccessToken().catch(() => {
                console.error('Periodic token refresh failed');
            });
        }
    }, 5 * 60 * 1000); // 5 minutes
}

// Export functions for use in other scripts
window.TokenManagement = {
    authenticatedFetch,
    refreshAccessToken,
    logout,
    storeAuthTokens,
    isAuthenticated,
    initializeTokenManagement,
    TokenStorage
};
