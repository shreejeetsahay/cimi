// src/content.js
(() => {
  let saveBtn = null;
  let menu = null;

  // Unified API caller for processing chat/snippet
  async function sendToApi(chatContent) {
    const payload = {
      chat_content: chatContent,
      source_url:   window.location.href,
      platform:     'chatgpt'
    };
    try {
      const resp = await fetch('http://localhost:8000/api/process-chat', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload)
      });
      if (!resp.ok) {
        const errText = await resp.text();
        throw new Error(`API ${resp.status}: ${errText}`);
      }
      return await resp.json();
    } catch (e) {
      console.error('sendToApi error:', e);
      throw e;
    }
  }

  // --- Floating "Save snippet" button on text selection ---

  function removeSaveBtn() {
    if (saveBtn) {
      saveBtn.remove();
      saveBtn = null;
    }
  }

  function showSaveBtn(text, rect) {
    removeSaveBtn();
    saveBtn = document.createElement('button');
    saveBtn.id = 'save-snippet-btn';
    saveBtn.innerText = 'Save snippet';
    Object.assign(saveBtn.style, {
      position: 'absolute',
      top:    `${rect.top + window.scrollY - 30}px`,
      left:   `${rect.left + window.scrollX}px`,
      zIndex: 9999,
    });

    saveBtn.addEventListener('click', async () => {
      saveBtn.disabled = true;
      try {
        await sendToApi(text);
        saveBtn.innerText = '✔️';
      } catch {
        saveBtn.innerText = '❌';
      } finally {
        setTimeout(() => {
          if (saveBtn) {
            saveBtn.innerText = 'Save snippet';
            saveBtn.disabled = false;
          }
        }, 1000);
      }
    });

    document.body.appendChild(saveBtn);
  }

  document.addEventListener('mouseup', () => {
    const sel = window.getSelection();
    const text = sel.toString().trim();
    if (!text) {
      removeSaveBtn();
      return;
    }
    const rect = sel.getRangeAt(0).getBoundingClientRect();
    showSaveBtn(text, rect);
  });

  document.addEventListener('mousedown', e => {
    if (saveBtn && !e.target.closest('#save-snippet-btn')) {
      removeSaveBtn();
    }
  });

  // --- Static top-right div & horizontal icon menu ---

  function injectDedicatedDiv() {
    if (document.getElementById('chatcards-dedicated-div')) return;
    const div = document.createElement('div');
    div.id = 'chatcards-dedicated-div';
    div.innerText = '🔖 ChatCards';
    document.body.appendChild(div);

    div.addEventListener('click', e => {
      e.stopPropagation();
      toggleMenu(div);
    });
  }

  function toggleMenu(anchor) {
    if (menu) removeMenu();
    else        createMenu(anchor);
  }

  function createMenu(anchor) {
    removeMenu();
    menu = document.createElement('div');
    menu.id = 'chatcards-popup-menu';
    menu.innerHTML = `
      <button id="save-chat-btn" title="Save Current Chat">📋</button>
      <button id="search-snippet-btn" title="Search Snippets">🔍</button>
    `;
    document.body.appendChild(menu);

    const rect = anchor.getBoundingClientRect();
    Object.assign(menu.style, {
      position: 'fixed',
      top:    `${rect.bottom + 6}px`,
      left:   `${rect.left}px`,
      zIndex: 10001
    });

    // Save Current Chat
    menu.querySelector('#save-chat-btn').addEventListener('click', async () => {
      // 1. Grab the full chat text (main.innerText fallback)
      let fullContent = '';
      const mainEl = document.querySelector('main');
      if (mainEl && mainEl.innerText.trim()) {
        fullContent = mainEl.innerText.trim();
      } else {
        const nodes = document.querySelectorAll('.whitespace-pre-wrap, p, .markdown');
        fullContent = Array.from(nodes)
          .map(el => el.innerText.trim())
          .filter(t => t.length)
          .join('\n\n');
      }

      // 2. Send to API
      try {
        await sendToApi(fullContent);
        alert('Chat processed successfully!');
      } catch {
        alert('Failed to process chat. Check console.');
      }
      removeMenu();
    });

    // Open Search Snippets popup
    menu.querySelector('#search-snippet-btn').addEventListener('click', () => {
      if (chrome.action?.openPopup) chrome.action.openPopup();
      removeMenu();
    });
  }

  function removeMenu() {
    if (menu) {
      menu.remove();
      menu = null;
    }
  }

  document.addEventListener('mousedown', e => {
    if (menu && !e.target.closest('#chatcards-popup-menu')) {
      removeMenu();
    }
  });

  // Initialize on load and re-inject on SPA navigations
  window.addEventListener('load', injectDedicatedDiv);
  new MutationObserver(injectDedicatedDiv)
    .observe(document.body, { childList: true, subtree: true });
})();
