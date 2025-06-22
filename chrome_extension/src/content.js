/* src/content.js */

// Utility: generate a simple UUID for highlight IDs
function generateUUID() {
  return 'xxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

let bookmarkBtn = null;

// Create the "Save Highlight" button
function createBookmarkButton(x, y) {
  removeBookmarkButton();
  bookmarkBtn = document.createElement('button');
  bookmarkBtn.innerText = '🔖 Save Highlight';
  bookmarkBtn.style.position = 'absolute';
  bookmarkBtn.style.top = `${y + 5}px`;
  bookmarkBtn.style.left = `${x}px`;
  bookmarkBtn.style.zIndex = 10000;
  bookmarkBtn.style.padding = '4px 8px';
  bookmarkBtn.style.fontSize = '12px';
  bookmarkBtn.style.cursor = 'pointer';
  document.body.appendChild(bookmarkBtn);

  bookmarkBtn.addEventListener('click', onSaveHighlight);
}

// Remove the bookmark button if it exists
function removeBookmarkButton() {
  if (bookmarkBtn) {
    bookmarkBtn.removeEventListener('click', onSaveHighlight);
    document.body.removeChild(bookmarkBtn);
    bookmarkBtn = null;
  }
}

// Handler for saving a highlight
function onSaveHighlight() {
  const selection = window.getSelection();
  const text = selection.toString().trim();
  if (!text) return removeBookmarkButton();

  // Find nearest message container (assumes class 'message')
  let node = selection.anchorNode;
  while (node && !node.classList?.contains('message')) {
    node = node.parentElement;
  }

  const messageEl = node || document.body;
  const timestampEl = messageEl.querySelector('time') || messageEl.querySelector('.message-timestamp');
  const timestamp = timestampEl ? timestampEl.innerText : new Date().toISOString();
  const speaker = messageEl.classList.contains('user') ? 'user' : 'ai';

  const highlight = {
    id: generateUUID(),
    text,
    timestamp,
    speaker,
    url: window.location.href
  };

  // Send to background for storage
  chrome.runtime.sendMessage({ type: 'BOOKMARK', payload: highlight });
  removeBookmarkButton();
}

// Listen for text selection to show the bookmark button
document.addEventListener('mouseup', (e) => {
  const selection = window.getSelection().toString().trim();
  if (selection.length > 0) {
    createBookmarkButton(e.pageX, e.pageY);
  } else {
    removeBookmarkButton();
  }
});

document.addEventListener('mousedown', removeBookmarkButton);

// Inject "Copy Full Chat" button into page header
function injectCopyChatBtn() {
  const header = document.querySelector('header') || document.body;
  if (header && !document.getElementById('copy-full-chat-btn')) {
    const copyBtn = document.createElement('button');
    copyBtn.id = 'copy-full-chat-btn';
    copyBtn.innerText = '📋 Copy Full Chat';
    copyBtn.style.marginLeft = '8px';
    copyBtn.style.padding = '4px 8px';
    copyBtn.style.fontSize = '12px';
    copyBtn.style.cursor = 'pointer';
    header.appendChild(copyBtn);
    copyBtn.addEventListener('click', onCopyFullChat);
  }
}

// Handler for copying full chat
function onCopyFullChat() {
  const messages = Array.from(document.querySelectorAll('.message'));
  const chatContent = messages.map(msg => {
    const speaker = msg.classList.contains('user') ? 'User' : 'AI';
    const text = msg.innerText || '';
    return `${speaker}: ${text}`;
  }).join('\n');

  const chatData = {
    id: generateUUID(),
    platform: 'chat',
    url: window.location.href,
    full_content: chatContent,
    created_at: new Date().toISOString()
  };

  chrome.runtime.sendMessage({ type: 'COPY_CHAT', payload: chatData });
}

// Listen for scroll-to messages from popup
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'SCROLL_TO' && msg.payload?.id) {
    const highlightEl = document.querySelector(`[data-highlight-id="${msg.payload.id}"]`);
    if (highlightEl) {
      highlightEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      highlightEl.style.transition = 'background-color 0.5s';
      highlightEl.style.backgroundColor = 'yellow';
      setTimeout(() => { highlightEl.style.backgroundColor = ''; }, 2000);
    }
  }
});

// Init
injectCopyChatBtn();
