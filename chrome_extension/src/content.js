// src/content.js
(() => {
  let saveBtn = null;
  let menu = null;

  // --- Floating "Save snippet" button on text selection (unchanged) ---
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
    saveBtn.addEventListener('click', () => {
      chrome.runtime.sendMessage({
        type: 'BOOKMARK',
        payload: { text, url: window.location.href, timestamp: new Date().toISOString() }
      }, () => {
        saveBtn.innerText = '✔️';
        setTimeout(() => saveBtn && (saveBtn.innerText = 'Save snippet'), 1000);
      });
    });
    document.body.appendChild(saveBtn);
  }

  document.addEventListener('mouseup', () => {
    const sel = window.getSelection();
    const text = sel.toString().trim();
    if (!text) { removeSaveBtn(); return; }
    const rect = sel.getRangeAt(0).getBoundingClientRect();
    showSaveBtn(text, rect);
  });
  document.addEventListener('mousedown', e => {
    if (saveBtn && !e.target.closest('#save-snippet-btn')) removeSaveBtn();
  });

  // --- Static top-right div + horizontal icon popup menu ---

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

    // position menu right below anchor
    const rect = anchor.getBoundingClientRect();
    Object.assign(menu.style, {
      position: 'fixed',
      top:    `${rect.bottom + 6}px`,
      left:   `${rect.left}px`,
      zIndex: 10001
    });

    // handlers
    // Inside createMenu(anchor) after you append the menu…
    menu.querySelector('#save-chat-btn').addEventListener('click', async () => {
        // 1. Gather the full chat text
        const items = Array.from(document.querySelectorAll('main div[role="listitem"]'));
        const fullContent = items.map(node => node.innerText).join('\n\n');

        // 2. Build your request payload
        const payload = {
            chat_content: fullContent,
            source_url: window.location.href,
            platform: 'chatgpt'
            // you can add project, tags, conversation_id if you have them
        };

        try {
            // 3. Call your FastAPI backend
            const resp = await fetch('http://localhost:8000/api/process-chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
            });

            if (!resp.ok) {
            const err = await resp.text();
            throw new Error(`API error: ${resp.status} ${err}`);
            }

            const result = await resp.json();
            console.log('Processed chat:', result);

            // 4. Feedback to the user
            alert('Chat successfully processed!');
        } catch (e) {
            console.error('Error processing chat:', e);
            alert('Failed to process chat. See console for details.');
        } finally {
            // 5. Close the menu
            removeMenu();
        }
    });


    menu.querySelector('#search-snippet-btn').addEventListener('click', () => {
      if (chrome.action?.openPopup) chrome.action.openPopup();
      removeMenu();
    });
  }

  function removeMenu() {
    if (menu) { menu.remove(); menu = null; }
  }

  document.addEventListener('mousedown', e => {
    if (menu && !e.target.closest('#chatcards-popup-menu')) removeMenu();
  });

  window.addEventListener('load', injectDedicatedDiv);
  new MutationObserver(injectDedicatedDiv)
    .observe(document.body, { childList: true, subtree: true });
})();
