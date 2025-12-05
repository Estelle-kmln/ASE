/**
 * Admin Panel JavaScript
 * Handles user management, pagination, search, and logs viewing
 */

// State management
let currentPage = 1;
let pageSize = 10;
let totalPages = 1;
let searchQuery = "";
let searchTimeout = null;

// Check admin access on page load
document.addEventListener("DOMContentLoaded", async () => {
    await checkAuth();
    await checkAdminAccess();
    await loadUsers();
    setupEventListeners();
});

/**
 * Check if user has admin privileges
 */
async function checkAdminAccess() {
    try {
        const token = localStorage.getItem("token");
        if (!token) {
            window.location.href = "login.html";
            return;
        }

        const response = await fetch("http://localhost:8080/api/auth/profile", {
            method: "GET",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (response.ok) {
            const data = await response.json();
            if (!data.user.is_admin) {
                alert("Access denied. Admin privileges required.");
                window.location.href = "index.html";
            }
        } else {
            window.location.href = "login.html";
        }
    } catch (error) {
        console.error("Admin access check error:", error);
        window.location.href = "login.html";
    }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById("user-search");
    searchInput.addEventListener("input", (e) => {
        searchQuery = e.target.value.trim();
        
        // Show/hide clear button
        const clearBtn = document.getElementById("clear-search-btn");
        clearBtn.style.display = searchQuery ? "block" : "none";
        
        // Debounce search
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentPage = 1;
            loadUsers();
        }, 300);
    });

    // Page size selector
    const pageSizeSelect = document.getElementById("page-size-select");
    pageSizeSelect.addEventListener("change", (e) => {
        pageSize = parseInt(e.target.value);
        currentPage = 1;
        loadUsers();
    });

    // Current page selector
    const currentPageSelect = document.getElementById("current-page-select");
    currentPageSelect.addEventListener("change", (e) => {
        currentPage = parseInt(e.target.value);
        loadUsers();
    });

    // Edit user form
    const editUserForm = document.getElementById("edit-user-form");
    editUserForm.addEventListener("submit", handleEditUserSubmit);
}

/**
 * Load users with pagination
 */
async function loadUsers() {
    try {
        showLoading(true);
        const token = localStorage.getItem("token");
        
        let url = searchQuery
            ? `http://localhost:8080/api/admin/users/search?query=${encodeURIComponent(searchQuery)}&page=${currentPage - 1}&size=${pageSize}`
            : `http://localhost:8080/api/admin/users?page=${currentPage - 1}&size=${pageSize}`;

        const response = await fetch(url, {
            method: "GET",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (response.ok) {
            const data = await response.json();
            displayUsers(data.content);
            updatePagination(data.totalPages, data.number + 1);
        } else {
            throw new Error("Failed to load users");
        }
    } catch (error) {
        console.error("Error loading users:", error);
        showMessage("Failed to load users. Please try again.", "error");
    } finally {
        showLoading(false);
    }
}

/**
 * Display users in table
 */
function displayUsers(users) {
    const tbody = document.getElementById("users-table-body");
    const emptyState = document.getElementById("users-empty-state");
    
    tbody.innerHTML = "";
    
    if (users.length === 0) {
        emptyState.style.display = "block";
        tbody.parentElement.parentElement.style.display = "none";
        return;
    }
    
    emptyState.style.display = "none";
    tbody.parentElement.parentElement.style.display = "table";
    
    users.forEach(user => {
        const row = document.createElement("tr");
        row.className = user.enabled ? "" : "user-disabled";
        
        // Username with status badge
        const statusBadge = user.enabled 
            ? '<span class="badge badge-success">Active</span>'
            : '<span class="badge badge-inactive">Inactive</span>';
        
        // Role badge
        const isAdmin = user.roles && user.roles.includes("ROLE_ADMIN");
        const roleBadge = isAdmin
            ? '<span class="badge badge-admin">Admin</span>'
            : '<span class="badge badge-user">User</span>';
        
        // Format date
        const createdDate = user.created_at 
            ? new Date(user.created_at).toLocaleDateString()
            : "N/A";
        
        row.innerHTML = `
            <td>${escapeHtml(user.username)} ${statusBadge}</td>
            <td>${roleBadge}</td>
            <td>
                <button 
                    class="admin-action-btn ${user.enabled ? 'btn-disable' : 'btn-enable'}"
                    onclick="toggleUserStatus(${user.id}, ${user.enabled})"
                >
                    ${user.enabled ? '🚫 Disable' : '✓ Enable'}
                </button>
            </td>
            <td>${createdDate}</td>
            <td>
                <button 
                    class="admin-action-btn btn-edit"
                    onclick="openEditUserModal(${user.id}, '${escapeHtml(user.username)}', ${isAdmin}, ${user.enabled})"
                >
                    ✏️ Edit
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * Update pagination controls
 */
function updatePagination(total, current) {
    totalPages = total;
    currentPage = current;
    
    // Update total pages display
    document.getElementById("total-pages").textContent = totalPages;
    
    // Update page selector
    const pageSelect = document.getElementById("current-page-select");
    pageSelect.innerHTML = "";
    for (let i = 1; i <= totalPages; i++) {
        const option = document.createElement("option");
        option.value = i;
        option.textContent = i;
        if (i === currentPage) {
            option.selected = true;
        }
        pageSelect.appendChild(option);
    }
    
    // Update prev/next buttons
    document.getElementById("prev-page-btn").disabled = currentPage === 1;
    document.getElementById("next-page-btn").disabled = currentPage === totalPages;
}

/**
 * Navigate to previous page
 */
function previousPage() {
    if (currentPage > 1) {
        currentPage--;
        loadUsers();
    }
}

/**
 * Navigate to next page
 */
function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        loadUsers();
    }
}

/**
 * Clear search
 */
function clearUserSearch() {
    document.getElementById("user-search").value = "";
    searchQuery = "";
    document.getElementById("clear-search-btn").style.display = "none";
    currentPage = 1;
    loadUsers();
}

/**
 * Toggle user enabled/disabled status
 */
async function toggleUserStatus(userId, currentStatus) {
    const action = currentStatus ? "disable" : "enable";
    if (!confirm(`Are you sure you want to ${action} this user?`)) {
        return;
    }
    
    try {
        const token = localStorage.getItem("token");
        const response = await fetch(`http://localhost:8080/api/admin/users/${userId}`, {
            method: "PUT",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ enabled: !currentStatus })
        });

        if (response.ok) {
            showMessage(`User ${action}d successfully`, "success");
            await loadUsers();
        } else {
            throw new Error(`Failed to ${action} user`);
        }
    } catch (error) {
        console.error(`Error ${action}ing user:`, error);
        showMessage(`Failed to ${action} user. Please try again.`, "error");
    }
}

/**
 * Open edit user modal
 */
function openEditUserModal(userId, username, isAdmin, enabled) {
    document.getElementById("edit-user-id").value = userId;
    document.getElementById("edit-username").value = username;
    document.getElementById("edit-role").value = isAdmin ? "ROLE_ADMIN" : "ROLE_USER";
    document.getElementById("edit-enabled").checked = enabled;
    
    document.getElementById("edit-user-modal").style.display = "flex";
}

/**
 * Close edit user modal
 */
function closeEditUserModal() {
    document.getElementById("edit-user-modal").style.display = "none";
    document.getElementById("edit-user-form").reset();
}

/**
 * Handle edit user form submission
 */
async function handleEditUserSubmit(e) {
    e.preventDefault();
    
    const userId = document.getElementById("edit-user-id").value;
    const role = document.getElementById("edit-role").value;
    const enabled = document.getElementById("edit-enabled").checked;
    
    try {
        const token = localStorage.getItem("token");
        const response = await fetch(`http://localhost/api/admin/users/${userId}`, {
            method: "PUT",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                roles: [role],
                enabled: enabled
            })
        });

        if (response.ok) {
            showMessage("User updated successfully", "success");
            closeEditUserModal();
            await loadUsers();
        } else {
            throw new Error("Failed to update user");
        }
    } catch (error) {
        console.error("Error updating user:", error);
        showMessage("Failed to update user. Please try again.", "error");
    }
}

/**
 * Toggle logs view
 */
function toggleLogsView() {
    const logsContainer = document.getElementById("logs-container");
    const isVisible = logsContainer.style.display !== "none";
    
    if (isVisible) {
        logsContainer.style.display = "none";
        document.getElementById("view-logs-btn").textContent = "View Logs";
    } else {
        logsContainer.style.display = "block";
        document.getElementById("view-logs-btn").textContent = "Hide Logs";
        loadLogs();
    }
}

/**
 * Load system logs
 */
async function loadLogs() {
    try {
        const token = localStorage.getItem("token");
        const response = await fetch("http://localhost:8080/api/logs/list", {
            method: "GET",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (response.ok) {
            const logs = await response.json();
            displayLogs(logs);
        } else {
            throw new Error("Failed to load logs");
        }
    } catch (error) {
        console.error("Error loading logs:", error);
        document.getElementById("logs-list").innerHTML = 
            '<div class="admin-error">Failed to load logs. Please try again.</div>';
    }
}

/**
 * Display logs
 */
function displayLogs(logs) {
    const logsList = document.getElementById("logs-list");
    
    if (logs.length === 0) {
        logsList.innerHTML = '<div class="admin-empty-state">No logs available.</div>';
        return;
    }
    
    logsList.innerHTML = logs.map(log => {
        const timestamp = log.timestamp 
            ? new Date(log.timestamp).toLocaleString()
            : "N/A";
        
        return `
            <div class="admin-log-item">
                <div class="admin-log-header">
                    <span class="admin-log-action">${escapeHtml(log.action)}</span>
                    <span class="admin-log-timestamp">${timestamp}</span>
                </div>
                <div class="admin-log-body">
                    <strong>User:</strong> ${escapeHtml(log.username || "System")}
                    ${log.details ? `<br><strong>Details:</strong> ${escapeHtml(log.details)}` : ""}
                </div>
            </div>
        `;
    }).join("");
}

/**
 * Refresh logs
 */
function refreshLogs() {
    loadLogs();
}

/**
 * Show loading indicator
 */
function showLoading(show) {
    const loadingDiv = document.getElementById("users-loading");
    loadingDiv.style.display = show ? "block" : "none";
}

/**
 * Show message
 */
function showMessage(message, type = "info") {
    // Simple alert for now - can be enhanced with toast notifications
    alert(message);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return "";
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}

/**
 * Navigate to a page
 */
function navigateTo(page) {
    window.location.href = page;
}

/**
 * Logout
 */
function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    window.location.href = "login.html";
}
