/* src/popup.js */

// State
let highlights = [];
let fuse;

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  const searchInput = document.getElementById('search');
  const resultsDiv = document.getElementById('results');

  // Fetch existing highlights from background
  const res = await window.Utils.sendMessage('GET_BOOKMARKS');
  highlights = res.highlights || [];

  // Initialize Fuse.js for fuzzy search on 'text' field
  fuse = new Fuse(highlights, {
    keys: ['text'],
    threshold: 0.3,
    minMatchCharLength: 2,
  });

  // Initial render (all highlights)
  renderResults(highlights);

  // Wire up search input
  searchInput.addEventListener('input', window.Utils.debounce((e) => {
    const query = e.target.value.trim();
    if (query.length > 0) {
      const searchResults = fuse.search(query).map(r => r.item);
      renderResults(searchResults);
    } else {
      renderResults(highlights);
    }
  }, 200));
});

// Render result list
function renderResults(items) {
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '';

  if (items.length === 0) {
    resultsDiv.innerHTML = '<p class="no-results">No highlights found.</p>';
    return;
  }

  items.forEach(item => {
    const card = document.createElement('div');
    card.className = 'result-card';

    // Snippet
    const textEl = document.createElement('p');
    textEl.className = 'result-text';
    textEl.innerText = item.text;
    card.appendChild(textEl);

    // Metadata
    const metaEl = document.createElement('div');
    metaEl.className = 'result-meta';
    metaEl.innerText = `${item.speaker.toUpperCase()} • ${window.Utils.formatTimestamp(item.timestamp)}`;
    card.appendChild(metaEl);

    // Actions container
    const actionsEl = document.createElement('div');
    actionsEl.className = 'result-actions';

    // Copy button
    const copyBtn = document.createElement('button');
    copyBtn.innerText = 'Copy';
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(item.text);
    });
    actionsEl.appendChild(copyBtn);

    // Go to Chat button
    const gotoBtn = document.createElement('button');
    gotoBtn.innerText = 'Go to chat';
    gotoBtn.addEventListener('click', () => {
      // Send a message to content script to scroll to the highlight
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]?.id) {
          chrome.tabs.sendMessage(tabs[0].id, { type: 'SCROLL_TO', payload: { id: item.id } });
        }
      });
    });
    actionsEl.appendChild(gotoBtn);

    card.appendChild(actionsEl);
    resultsDiv.appendChild(card);
  });
}
