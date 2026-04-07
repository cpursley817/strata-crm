// ===== API COMMUNICATION =====
// Every request from the browser to the server goes through this function.
// If the server says you're not logged in (401), it shows the login screen.

/**
 * Makes an API request to the server.
 * All browser-to-server communication flows through this function.
 * Automatically handles 401 (unauthorized) responses by showing the login screen.
 * Returns parsed JSON response on success, or null on failure.
 *
 * @param {string} endpoint - The API endpoint path (e.g., '/dashboard', '/sections')
 * @param {string} method - HTTP method: 'GET', 'POST', 'PUT', 'DELETE' (default: 'GET')
 * @param {object|null} body - Request body for POST/PUT requests, automatically JSON stringified
 * @returns {Promise<object|null>} Parsed JSON response, or null if request failed
 */
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
    };
    if (body) options.body = JSON.stringify(body);
    try {
        const response = await fetch(`/api${endpoint}`, options);
        if (!response.ok) {
            if (response.status === 401) showLogin();
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}
