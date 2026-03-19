(function(){
  const root = document.getElementById('chatbot-root');
  if (!root) return;
  const toggle = document.getElementById('chatbot-toggle');
  const closeBtn = document.getElementById('chatbot-close');
  const windowEl = document.getElementById('chatbot-window');
  const input = document.getElementById('chatbot-input');
  const messagesEl = document.getElementById('chatbot-messages');
  const suggestionsEl = document.getElementById('chatbot-suggestions');
  const form = document.getElementById('chatbot-form');
  const apiUrl = root.dataset.apiUrl || '/faq-search/';

  function openWindow() { windowEl.classList.add('open'); windowEl.setAttribute('aria-hidden', 'false'); input.focus(); }
  function closeWindow() { windowEl.classList.remove('open'); windowEl.setAttribute('aria-hidden', 'true'); }

  toggle.addEventListener('click', function(){
    if (windowEl.classList.contains('open')) { closeWindow(); } else { openWindow(); fetchSuggestions(''); }
  });

  closeBtn.addEventListener('click', closeWindow);
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') closeWindow(); });

  let timeout = null;
  input.addEventListener('input', function(e){
    clearTimeout(timeout);
    timeout = setTimeout(function(){ fetchSuggestions(input.value.trim()); }, 250);
  });

  form.addEventListener('submit', function(e){ e.preventDefault(); const q = input.value.trim(); if (!q) return; appendUserMessage(q); sendQuestion(q); input.value = ''; suggestionsEl.innerHTML = ''; });

  // Fetch suggestions from the server
  async function fetchSuggestions(q){
    try {
      const url = apiUrl + (q ? ('?q=' + encodeURIComponent(q)) : '');
      const res = await fetch(url, { method: 'GET' });
      if (!res.ok) throw new Error('Network response not ok');
      const data = await res.json();
      renderSuggestions(data.results || []);
    } catch (err) {
      console.error('Chatbot fetch error:', err);
    }
  }

  async function sendQuestion(q){
    try {
      showTyping();
      const url = '/faq-reply/?q=' + encodeURIComponent(q);
      const res = await fetch(url, { method: 'GET' });
      hideTyping();
      if (!res.ok) throw new Error('Network response not ok');
      const data = await res.json();
      if (data.found) {
        appendBotMessage(data.answer);
      } else {
        appendBotMessage(data.message || "Sorry, I don't know the answer. You can contact support.");
        if (data.suggestions && data.suggestions.length) {
          renderSuggestions(data.suggestions);
        }
      }
    } catch (err) {
      hideTyping();
      console.error('Chatbot reply error:', err);
      appendBotMessage('Sorry, something went wrong. Please try again later.');
    }
  }

  function updateSuggestArrows(){
    const prev = document.querySelector('.chatbot-suggest-prev');
    const next = document.querySelector('.chatbot-suggest-next');
    if (!prev || !next) return;
    const el = suggestionsEl;
    // determine if we need arrows
    const canScrollLeft = el.scrollLeft > 0;
    const canScrollRight = el.scrollWidth - el.clientWidth - el.scrollLeft > 1;
    prev.disabled = !canScrollLeft;
    next.disabled = !canScrollRight;
  }

  let suggestionScrollTimeout = null;
  function renderSuggestions(items){
    suggestionsEl.innerHTML = '';
    if (!items.length) { updateSuggestArrows(); return; }
    items.slice(0,12).forEach(it => {
      const btn = document.createElement('button');
      btn.className = 'chatbot-suggestion';
      btn.type = 'button';
      btn.textContent = it.question;
      btn.title = it.question;
      btn.setAttribute('role','option');
      btn.addEventListener('click', function(){
        const q = it.question;
        appendUserMessage(q);
        sendQuestion(q);
      });
      suggestionsEl.appendChild(btn);
    });

    // wire up scrolling arrows
    const prev = document.querySelector('.chatbot-suggest-prev');
    const next = document.querySelector('.chatbot-suggest-next');
    if (prev && next) {
      prev.onclick = () => { suggestionsEl.scrollBy({ left: -Math.max(120, suggestionsEl.clientWidth * 0.6), behavior: 'smooth' }); };
      next.onclick = () => { suggestionsEl.scrollBy({ left: Math.max(120, suggestionsEl.clientWidth * 0.6), behavior: 'smooth' }); };

      // update arrow states on scroll
      suggestionsEl.addEventListener('scroll', function(){
        clearTimeout(suggestionScrollTimeout);
        suggestionScrollTimeout = setTimeout(updateSuggestArrows, 80);
      });

      // Keyboard support: left/right arrow when suggestions focused
      suggestionsEl.addEventListener('keydown', function(e){
        if (e.key === 'ArrowRight') { suggestionsEl.scrollBy({ left: 160, behavior: 'smooth' }); e.preventDefault(); }
        if (e.key === 'ArrowLeft') { suggestionsEl.scrollBy({ left: -160, behavior: 'smooth' }); e.preventDefault(); }
      });
    }

    // initial arrow state
    setTimeout(updateSuggestArrows, 50);
  }

  function showTyping(){
    const tip = document.createElement('div'); tip.className = 'chatbot-bot chatbot-typing'; tip.id = 'chatbot-typing'; tip.textContent = '...';
    messagesEl.appendChild(tip); messagesEl.scrollTop = messagesEl.scrollHeight;
  }
  function hideTyping(){ const t = document.getElementById('chatbot-typing'); if (t) t.remove(); }

  function appendUserMessage(text){
    const m = document.createElement('div'); m.className = 'chatbot-user'; m.textContent = text;
    messagesEl.appendChild(m); messagesEl.scrollTop = messagesEl.scrollHeight; 
  }

  function appendBotMessage(text){
    const m = document.createElement('div'); m.className = 'chatbot-bot'; m.textContent = text;
    messagesEl.appendChild(m); messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function escapeHtml(s){ return String(s).replace(/&/g, '&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

})();