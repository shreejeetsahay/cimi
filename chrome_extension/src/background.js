/* src/background.js */

// Utility functions for chrome.storage.local (Promise-based)
function getFromStorage(key) {
  return new Promise((resolve) => {
    chrome.storage.local.get([key], (result) => {
      resolve(result[key] || []);
    });
  });
}

function setToStorage(key, data) {
  return new Promise((resolve) => {
    chrome.storage.local.set({ [key]: data }, () => {
      resolve();
    });
  });
}

// Handle incoming messages from content script or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  (async () => {
    switch (message.type) {
      case 'BOOKMARK': {
        // Save a single highlight
        const highlight = message.payload;
        const highlights = await getFromStorage('highlights');
        highlights.push(highlight);
        await setToStorage('highlights', highlights);
        sendResponse({ success: true, type: 'BOOKMARKED', highlight });
        break;
      }

      case 'COPY_CHAT': {
        // Save a full chat snapshot
        const chat = message.payload;
        const chats = await getFromStorage('chats');
        chats.push(chat);
        await setToStorage('chats', chats);
        sendResponse({ success: true, type: 'CHAT_COPIED', chatId: chat.id });
        break;
      }

      case 'GET_BOOKMARKS': {
        // Retrieve all highlights
        const highlights = await getFromStorage('highlights');
        sendResponse({ success: true, highlights });
        break;
      }

      case 'GET_CHATS': {
        // Retrieve all full chat snapshots
        const chats = await getFromStorage('chats');
        sendResponse({ success: true, chats });
        break;
      }

      case 'DELETE_HIGHLIGHT': {
        // Remove a highlight by id
        const { id } = message.payload;
        let highlights = await getFromStorage('highlights');
        highlights = highlights.filter(h => h.id !== id);
        await setToStorage('highlights', highlights);
        sendResponse({ success: true, id });
        break;
      }

      default:
        // Unknown message
        sendResponse({ success: false, error: 'Unknown message type' });
    }
  })();

  // Return true to indicate we're sending response asynchronously
  return true;
});

// Optional: setup alarms for future embedding batch processing
chrome.alarms.create('processEmbeddings', { periodInMinutes: 60 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'processEmbeddings') {
    // Placeholder: implement embedding generation batch job
    console.log('Alarm: processEmbeddings triggered');
  }
});
