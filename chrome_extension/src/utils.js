/* src/utils.js */

/**
 * Debounce: ensure func is called only after wait ms have elapsed since last call
 * @param {Function} func
 * @param {number} wait
 */
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

/**
 * Throttle: ensure func is called at most once per limit ms
 * @param {Function} func
 * @param {number} limit
 */
function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Send a message to background or other parts of the extension
 * @param {string} type
 * @param {any} payload
 * @returns {Promise<any>}
 */
function sendMessage(type, payload) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ type, payload }, (response) => {
      resolve(response);
    });
  });
}

/**
 * Format ISO timestamp into a readable local string
 * @param {string} isoTs
 * @returns {string}
 */
function formatTimestamp(isoTs) {
  const date = new Date(isoTs);
  return date.toLocaleString();
}

// Expose utilities on the global window object
window.Utils = {
  debounce,
  throttle,
  sendMessage,
  formatTimestamp,
};