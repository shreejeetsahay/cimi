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
        const highlight = message.payload;
        const highlights = await getFromStorage('highlights');
        highlights.push(highlight);
        await setToStorage('highlights', highlights);
        sendResponse({ success: true, type: 'BOOKMARKED', highlight });
        break;
      }

      case 'COPY_CHAT': {
        const chat = message.payload;
        const chats = await getFromStorage('chats');
        chats.push(chat);
        await setToStorage('chats', chats);
        sendResponse({ success: true, type: 'CHAT_COPIED', chatId: chat.id });
        break;
      }

      case 'GET_BOOKMARKS': {
        const highlights = await getFromStorage('highlights');
        sendResponse({ success: true, highlights });
        break;
      }

      case 'GET_CHATS': {
        const chats = await getFromStorage('chats');
        sendResponse({ success: true, chats });
        break;
      }

      case 'DELETE_HIGHLIGHT': {
        const { id } = message.payload;
        let highlights = await getFromStorage('highlights');
        highlights = highlights.filter(h => h.id !== id);
        await setToStorage('highlights', highlights);
        sendResponse({ success: true, id });
        break;
      }

      case 'OPEN_POPUP': {
        if (chrome.action && chrome.action.openPopup) {
          chrome.action.openPopup();
        }
        sendResponse({ success: true });
        break;
      }

      default:
        sendResponse({ success: false, error: 'Unknown message type' });
    }
  })();

  return true; // async response
});

// Remove alarms if not needed, or keep placeholder
chrome.alarms.create('processEmbeddings', { periodInMinutes: 60 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'processEmbeddings') {
    console.log('Alarm: processEmbeddings triggered');
  }
});