/**
 * GitHub Webhook Monitor - JavaScript Application
 * Handles real-time polling, event display, and UI updates
 */

// ============================================
// Configuration
// ============================================

const CONFIG = {
    POLL_INTERVAL: 15000, // 15 seconds (as per requirements)
    API_ENDPOINT: '/api/events',
    MAX_EVENTS_DISPLAY: 100,
    DATE_FORMAT_OPTIONS: {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZoneName: 'short'
    }
};

// ============================================
// Application State
// ============================================

const state = {
    events: [],
    displayedEventIds: new Set(), // Track displayed events to prevent duplicates
    lastPollTime: null,
    isPolling: false,
    pollTimer: null,
    countdownTimer: null,
    nextPollSeconds: 15
};

// ============================================
// DOM Elements
// ============================================

const elements = {
    // Stats
    totalEvents: document.getElementById('totalEvents'),
    lastUpdate: document.getElementById('lastUpdate'),
    nextPoll: document.getElementById('nextPoll'),
    
    // Status
    connectionStatus: document.getElementById('connectionStatus'),
    
    // Buttons
    refreshBtn: document.getElementById('refreshBtn'),
    
    // Containers
    loadingState: document.getElementById('loadingState'),
    emptyState: document.getElementById('emptyState'),
    eventsList: document.getElementById('eventsList')
};

// ============================================
// Utility Functions
// ============================================

/**
 * Format timestamp to readable format
 * @param {string} isoTimestamp - ISO 8601 timestamp
 * @returns {string} Formatted date string
 */
function formatTimestamp(isoTimestamp) {
    try {
        const date = new Date(isoTimestamp);
        return date.toLocaleString('en-US', CONFIG.DATE_FORMAT_OPTIONS);
    } catch (error) {
        console.error('Error formatting timestamp:', error);
        return isoTimestamp;
    }
}

/**
 * Format relative time (e.g., "2 minutes ago")
 * @param {string} isoTimestamp - ISO 8601 timestamp
 * @returns {string} Relative time string
 */
function formatRelativeTime(isoTimestamp) {
    try {
        const date = new Date(isoTimestamp);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        
        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        return `${Math.floor(seconds / 86400)}d ago`;
    } catch (error) {
        return 'Unknown';
    }
}

/**
 * Update connection status badge
 * @param {boolean} connected - Connection status
 */
function updateConnectionStatus(connected) {
    if (connected) {
        elements.connectionStatus.classList.add('connected');
        elements.connectionStatus.querySelector('.status-text').textContent = 'Connected';
    } else {
        elements.connectionStatus.classList.remove('connected');
        elements.connectionStatus.querySelector('.status-text').textContent = 'Disconnected';
    }
}

/**
 * Update stats display
 */
function updateStats() {
    // Total events
    elements.totalEvents.textContent = state.events.length;
    
    // Last update time
    if (state.lastPollTime) {
        elements.lastUpdate.textContent = formatRelativeTime(state.lastPollTime);
    } else {
        elements.lastUpdate.textContent = 'Never';
    }
}

/**
 * Start countdown timer for next poll
 */
function startCountdown() {
    // Clear existing countdown
    if (state.countdownTimer) {
        clearInterval(state.countdownTimer);
    }
    
    state.nextPollSeconds = 15;
    elements.nextPoll.textContent = `${state.nextPollSeconds}s`;
    
    state.countdownTimer = setInterval(() => {
        state.nextPollSeconds--;
        elements.nextPoll.textContent = `${state.nextPollSeconds}s`;
        
        if (state.nextPollSeconds <= 0) {
            clearInterval(state.countdownTimer);
        }
    }, 1000);
}

// ============================================
// Event Display Functions
// ============================================

/**
 * Generate event message based on event type
 * @param {Object} event - Event object from database
 * @returns {string} Formatted event message
 */
function generateEventMessage(event) {
    const author = `<span class="event-author">${event.author}</span>`;
    
    switch (event.event_type) {
        case 'push':
            const branch = `<span class="event-branch">${event.branch || 'unknown'}</span>`;
            return `${author} pushed to ${branch}`;
            
        case 'pull_request':
            const fromBranch = `<span class="event-branch">${event.from_branch}</span>`;
            const toBranch = `<span class="event-branch">${event.to_branch}</span>`;
            return `${author} submitted a pull request from ${fromBranch} to ${toBranch}`;
            
        case 'merge':
            const mergeFr = `<span class="event-branch">${event.from_branch}</span>`;
            const mergeTo = `<span class="event-branch">${event.to_branch}</span>`;
            return `${author} merged branch ${mergeFr} to ${mergeTo}`;
            
        default:
            return `${author} performed ${event.event_type} action`;
    }
}

/**
 * Create event DOM element
 * @param {Object} event - Event object
 * @param {boolean} isNew - Whether this is a new event
 * @returns {HTMLElement} Event element
 */
function createEventElement(event, isNew = false) {
    const eventDiv = document.createElement('div');
    eventDiv.className = `event-item ${isNew ? 'new' : ''}`;
    eventDiv.dataset.eventId = event._id;
    
    const eventMessage = generateEventMessage(event);
    const timestamp = formatTimestamp(event.timestamp);
    
    eventDiv.innerHTML = `
        <div class="event-header">
            <span class="event-type ${event.event_type}">
                ${event.event_type === 'push' ? '📤' : event.event_type === 'pull_request' ? '🔀' : '🔗'}
                ${event.event_type.replace('_', ' ')}
            </span>
            <span class="event-timestamp" title="${timestamp}">
                ${formatRelativeTime(event.timestamp)}
            </span>
        </div>
        <div class="event-message">
            ${eventMessage}
        </div>
    `;
    
    return eventDiv;
}

/**
 * Display events in the UI
 * @param {Array} events - Array of event objects
 */
function displayEvents(events) {
    // Hide loading state
    elements.loadingState.style.display = 'none';
    
    if (events.length === 0) {
        // Show empty state
        elements.emptyState.style.display = 'block';
        elements.eventsList.style.display = 'none';
        return;
    }
    
    // Show events list
    elements.emptyState.style.display = 'none';
    elements.eventsList.style.display = 'flex';
    
    // Determine new events
    const newEvents = events.filter(event => !state.displayedEventIds.has(event._id));
    
    // Add new events to the top
    newEvents.forEach(event => {
        const eventElement = createEventElement(event, true);
        elements.eventsList.insertBefore(eventElement, elements.eventsList.firstChild);
        state.displayedEventIds.add(event._id);
    });
    
    // Limit displayed events
    while (elements.eventsList.children.length > CONFIG.MAX_EVENTS_DISPLAY) {
        const lastChild = elements.eventsList.lastChild;
        state.displayedEventIds.delete(lastChild.dataset.eventId);
        elements.eventsList.removeChild(lastChild);
    }
    
    // Update relative timestamps for existing events
    updateRelativeTimestamps();
}

/**
 * Update relative timestamps for all displayed events
 */
function updateRelativeTimestamps() {
    const timestampElements = elements.eventsList.querySelectorAll('.event-timestamp');
    
    state.events.forEach((event, index) => {
        if (timestampElements[index]) {
            const relativeTime = formatRelativeTime(event.timestamp);
            timestampElements[index].textContent = relativeTime;
        }
    });
}

// ============================================
// API Functions
// ============================================

/**
 * Fetch events from the server
 * @returns {Promise<Array>} Array of events
 */
async function fetchEvents() {
    try {
        const response = await fetch(CONFIG.API_ENDPOINT);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
            return data.events || [];
        } else {
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.error('Error fetching events:', error);
        updateConnectionStatus(false);
        throw error;
    }
}

/**
 * Poll for new events
 */
async function pollEvents() {
    if (state.isPolling) {
        console.log('Poll already in progress, skipping...');
        return;
    }
    
    state.isPolling = true;
    
    try {
        console.log('📡 Polling for events...');
        
        const events = await fetchEvents();
        
        // Update state
        state.events = events;
        state.lastPollTime = new Date().toISOString();
        
        // Update UI
        displayEvents(events);
        updateStats();
        updateConnectionStatus(true);
        
        console.log(`✓ Fetched ${events.length} events`);
        
    } catch (error) {
        console.error('✗ Poll failed:', error);
        updateConnectionStatus(false);
    } finally {
        state.isPolling = false;
        startCountdown();
    }
}

/**
 * Start automatic polling
 */
function startPolling() {
    console.log(`🚀 Starting automatic polling (every ${CONFIG.POLL_INTERVAL / 1000}s)`);
    
    // Poll immediately
    pollEvents();
    
    // Set up interval
    if (state.pollTimer) {
        clearInterval(state.pollTimer);
    }
    
    state.pollTimer = setInterval(pollEvents, CONFIG.POLL_INTERVAL);
}

/**
 * Stop automatic polling
 */
function stopPolling() {
    if (state.pollTimer) {
        clearInterval(state.pollTimer);
        state.pollTimer = null;
    }
    
    if (state.countdownTimer) {
        clearInterval(state.countdownTimer);
        state.countdownTimer = null;
    }
}

// ============================================
// Event Handlers
// ============================================

/**
 * Handle refresh button click
 */
function handleRefresh() {
    console.log('🔄 Manual refresh triggered');
    
    // Add rotating animation
    elements.refreshBtn.classList.add('rotating');
    
    // Poll events
    pollEvents();
    
    // Remove animation after 1 second
    setTimeout(() => {
        elements.refreshBtn.classList.remove('rotating');
    }, 1000);
    
    // Restart polling timer
    stopPolling();
    startPolling();
}

/**
 * Handle page visibility change (pause polling when tab is hidden)
 */
function handleVisibilityChange() {
    if (document.hidden) {
        console.log('⏸️  Page hidden, pausing polling');
        stopPolling();
    } else {
        console.log('▶️  Page visible, resuming polling');
        startPolling();
    }
}

// ============================================
// Initialization
// ============================================

/**
 * Initialize the application
 */
function init() {
    console.log('🎯 Initializing GitHub Webhook Monitor');
    
    // Set up event listeners
    elements.refreshBtn.addEventListener('click', handleRefresh);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Start polling
    startPolling();
    
    // Update stats every 30 seconds
    setInterval(() => {
        updateStats();
        updateRelativeTimestamps();
    }, 30000);
    
    console.log('✓ Application initialized');
}

// ============================================
// Start Application
// ============================================

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
