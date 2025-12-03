/**
 * MoAI Tab Suspender - Background Service Worker
 *
 * Connects to Native Messaging host and suspends inactive tabs on command.
 * Part of macOS Resource Optimizer integration.
 *
 * @version 1.0.0
 * @author MoAI-ADK
 */

// Native Messaging host name
const HOST_NAME = 'com.moai.tab_suspender';

// Active port connection
let port = null;

// Connection state
let isConnected = false;

/**
 * Initialize Native Messaging connection
 */
function connectToHost() {
  try {
    port = chrome.runtime.connectNative(HOST_NAME);

    port.onMessage.addListener((message) => {
      console.log('[MoAI] Received message from host:', message);
      handleHostMessage(message);
    });

    port.onDisconnect.addListener(() => {
      console.log('[MoAI] Disconnected from host');
      isConnected = false;
      port = null;

      if (chrome.runtime.lastError) {
        console.error('[MoAI] Disconnect error:', chrome.runtime.lastError.message);
      }
    });

    isConnected = true;
    console.log('[MoAI] Connected to Native Messaging host');

  } catch (error) {
    console.error('[MoAI] Failed to connect to host:', error);
    isConnected = false;
  }
}

/**
 * Handle messages from Native Messaging host
 * @param {Object} message - Message from host
 */
function handleHostMessage(message) {
  const { action } = message;

  switch (action) {
    case 'suspend_tabs':
      suspendInactiveTabs(message);
      break;

    case 'get_tab_count':
      getTabCount();
      break;

    case 'ping':
      sendResponse({ action: 'pong', timestamp: Date.now() });
      break;

    default:
      console.warn('[MoAI] Unknown action:', action);
      sendResponse({ success: false, error: 'Unknown action' });
  }
}

/**
 * Suspend inactive tabs
 * @param {Object} params - Suspension parameters
 */
async function suspendInactiveTabs(params) {
  try {
    const tabs = await chrome.tabs.query({});
    let suspended = 0;
    const suspendedTabs = [];

    for (const tab of tabs) {
      // Skip tabs that should not be suspended
      if (shouldSkipTab(tab)) {
        continue;
      }

      try {
        await chrome.tabs.discard(tab.id);
        suspended++;
        suspendedTabs.push({
          id: tab.id,
          title: tab.title,
          url: tab.url
        });
      } catch (error) {
        console.warn(`[MoAI] Failed to suspend tab ${tab.id}:`, error);
      }
    }

    sendResponse({
      success: true,
      tabs_suspended: suspended,
      tabs_total: tabs.length,
      suspended_tabs: suspendedTabs
    });

  } catch (error) {
    console.error('[MoAI] Error suspending tabs:', error);
    sendResponse({
      success: false,
      error: error.message
    });
  }
}

/**
 * Determine if a tab should be skipped from suspension
 * @param {chrome.tabs.Tab} tab - Tab to check
 * @returns {boolean} - True if tab should be skipped
 */
function shouldSkipTab(tab) {
  // Skip pinned tabs
  if (tab.pinned) {
    return true;
  }

  // Skip active tab
  if (tab.active) {
    return true;
  }

  // Skip tabs playing audio
  if (tab.audible) {
    return true;
  }

  // Skip chrome:// and chrome-extension:// pages
  if (tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://')) {
    return true;
  }

  // Skip already discarded tabs
  if (tab.discarded) {
    return true;
  }

  return false;
}

/**
 * Get current tab count
 */
async function getTabCount() {
  try {
    const tabs = await chrome.tabs.query({});
    const activeTabs = tabs.filter(t => !t.discarded);
    const inactiveTabs = tabs.filter(t => t.discarded);

    sendResponse({
      success: true,
      total_tabs: tabs.length,
      active_tabs: activeTabs.length,
      suspended_tabs: inactiveTabs.length
    });
  } catch (error) {
    console.error('[MoAI] Error getting tab count:', error);
    sendResponse({
      success: false,
      error: error.message
    });
  }
}

/**
 * Send response to Native Messaging host
 * @param {Object} response - Response object
 */
function sendResponse(response) {
  if (port && isConnected) {
    try {
      port.postMessage(response);
      console.log('[MoAI] Sent response to host:', response);
    } catch (error) {
      console.error('[MoAI] Failed to send response:', error);
    }
  } else {
    console.warn('[MoAI] Cannot send response: not connected');
  }
}

// Initialize connection on startup
connectToHost();

// Log extension loaded
console.log('[MoAI] Tab Suspender extension loaded');
