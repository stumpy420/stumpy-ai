// Chat Companion Component with Active Memory Recall & Inline Learning Highlights

class ChatManager {
  constructor(messagesContainerId, sessionsContainerId) {
    this.container = document.getElementById(messagesContainerId);
    this.sessionsList = document.getElementById(sessionsContainerId);
    this.currentSessionId = null;
    this.sessions = [];
    this.isSending = false;
    this.initEvents();
  }

  initEvents() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');

    if (chatForm) {
      chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.sendMessage();
      });
    }

    if (chatInput) {
      chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
    }

    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
      newChatBtn.addEventListener('click', () => this.startNewChat());
    }
  }

  async loadSessions() {
    try {
      this.sessions = await api.getSessions();
      this.renderSessionsList();
      if (this.sessions.length > 0 && !this.currentSessionId) {
        await this.selectSession(this.sessions[0].id);
      } else if (this.sessions.length === 0) {
        this.showWelcomeScreen();
      }
    } catch (err) {
      console.error('Failed to load sessions:', err);
    }
  }

  renderSessionsList() {
    if (!this.sessionsList) return;

    if (this.sessions.length === 0) {
      this.sessionsList.innerHTML = `<div class="text-xs text-slate-500 px-3 py-2">No past conversations</div>`;
      return;
    }

    this.sessionsList.innerHTML = this.sessions.map(s => {
      const isActive = s.id === this.currentSessionId;
      return `
        <div onclick="window.chatManager.selectSession('${s.id}')" class="group flex items-center justify-between px-3 py-2 rounded-xl text-xs cursor-pointer transition ${isActive ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30' : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'}">
          <div class="flex items-center gap-2 truncate">
            <i data-lucide="message-square" class="w-3.5 h-3.5 shrink-0 ${isActive ? 'text-indigo-400' : 'text-slate-500'}"></i>
            <span class="truncate">${s.title}</span>
          </div>
          <button onclick="event.stopPropagation(); window.chatManager.deleteSession('${s.id}')" class="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-400 rounded transition" title="Delete chat">
            <i data-lucide="trash-2" class="w-3 h-3"></i>
          </button>
        </div>
      `;
    }).join('');

    lucide.createIcons();
  }

  async selectSession(sessionId) {
    this.currentSessionId = sessionId;
    this.renderSessionsList();
    try {
      const messages = await api.getHistory(sessionId);
      this.renderMessages(messages);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  }

  async startNewChat() {
    this.currentSessionId = null;
    this.renderSessionsList();
    this.showWelcomeScreen();
    const chatInput = document.getElementById('chat-input');
    if (chatInput) chatInput.focus();
  }

  async deleteSession(sessionId) {
    if (!confirm('Delete this conversation?')) return;
    try {
      await api.deleteSession(sessionId);
      if (this.currentSessionId === sessionId) {
        this.currentSessionId = null;
      }
      await this.loadSessions();
    } catch (err) {
      window.app.showToast('Failed to delete: ' + err.message, 'error');
    }
  }

  showWelcomeScreen() {
    if (!this.container) return;
    this.container.innerHTML = `
      <div class="max-w-2xl mx-auto py-12 px-4 text-center space-y-6">
        <div class="inline-flex p-4 rounded-3xl glass-panel border border-indigo-500/20 shadow-2xl relative">
          <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 flex items-center justify-center text-white shadow-lg animate-learn-pulse">
            <i data-lucide="bot" class="w-8 h-8"></i>
          </div>
        </div>

        <div class="space-y-2">
          <h2 class="text-2xl font-extrabold text-slate-100 tracking-tight">Meet <span class="gradient-text">Stumpy AI</span></h2>
          <p class="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
            The adaptive AI companion that learns your style, tracks your skills, remembers your projects, and gets smarter the more you talk.
          </p>
        </div>

        <!-- Quick Starter Prompts -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-4 text-left">
          <button onclick="window.chatManager.fillPrompt('Hi! My name is Alex, I am building a high-throughput event streaming engine in Rust, and I prefer concise code snippets.')" class="p-3.5 rounded-2xl glass-panel glass-panel-hover border border-slate-800 text-xs text-slate-300 transition">
            <div class="font-bold text-slate-200 mb-1 flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
              Teach Stumpy About You
            </div>
            <p class="text-slate-400 text-[11px]">"Hi! My name is Alex, I'm building a streaming engine in Rust..."</p>
          </button>

          <button onclick="window.chatManager.fillPrompt('What have you learned about me so far and what is in your memory graph?')" class="p-3.5 rounded-2xl glass-panel glass-panel-hover border border-slate-800 text-xs text-slate-300 transition">
            <div class="font-bold text-slate-200 mb-1 flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-indigo-400"></span>
              Inspect Learned Context
            </div>
            <p class="text-slate-400 text-[11px]">"What have you learned about me so far?"</p>
          </button>

          <button onclick="window.chatManager.fillPrompt('Can you generate a quiz for me to practice Modern Python and System Design?')" class="p-3.5 rounded-2xl glass-panel glass-panel-hover border border-slate-800 text-xs text-slate-300 transition">
            <div class="font-bold text-slate-200 mb-1 flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-amber-400"></span>
              Skill Practice & Quizzes
            </div>
            <p class="text-slate-400 text-[11px]">"Can you generate a quiz for me on Python?"</p>
          </button>

          <button onclick="window.chatManager.fillPrompt('Remember that I always prefer dark-mode CSS and Tailwind utility classes for UI components.')" class="p-3.5 rounded-2xl glass-panel glass-panel-hover border border-slate-800 text-xs text-slate-300 transition">
            <div class="font-bold text-slate-200 mb-1 flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-purple-400"></span>
              Set Custom Preference
            </div>
            <p class="text-slate-400 text-[11px]">"Remember that I always prefer dark-mode CSS..."</p>
          </button>
        </div>
      </div>
    `;
    lucide.createIcons();
  }

  fillPrompt(text) {
    const input = document.getElementById('chat-input');
    if (input) {
      input.value = text;
      input.focus();
    }
  }

  renderMessages(messages) {
    if (!this.container) return;
    if (messages.length === 0) {
      this.showWelcomeScreen();
      return;
    }

    this.container.innerHTML = messages.map(m => this.createMessageHTML(m)).join('');
    this.scrollToBottom();
    lucide.createIcons();
  }

  createMessageHTML(msg) {
    const isUser = msg.role === 'user';
    const parsedContent = this.formatMarkdown(msg.content);

    if (isUser) {
      return `
        <div class="flex justify-end mb-4 animate-fadeIn">
          <div class="max-w-2xl bg-indigo-600/90 text-white px-4 py-3 rounded-2xl rounded-tr-sm shadow-md text-xs leading-relaxed">
            ${this.escapeHTML(msg.content)}
          </div>
        </div>
      `;
    } else {
      const recalledMemories = msg.recalled_memories || [];
      const hasMemories = recalledMemories.length > 0;

      const memoriesHTML = hasMemories ? `
        <div class="mt-3 pt-2 border-t border-slate-800/80">
          <details class="group text-[11px]">
            <summary class="cursor-pointer font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5 select-none">
              <i data-lucide="brain" class="w-3.5 h-3.5"></i>
              <span>Recalled ${recalledMemories.length} relevant memories</span>
              <i data-lucide="chevron-down" class="w-3 h-3 ml-auto transition-transform group-open:rotate-180"></i>
            </summary>
            <div class="mt-2 space-y-1.5 pl-2 border-l-2 border-indigo-500/40">
              ${recalledMemories.map(rm => `
                <div class="text-slate-300 text-[10px] flex items-start gap-1.5">
                  <span class="px-1.5 py-0.2 rounded font-bold uppercase tracking-wider text-[9px] badge-${rm.category}">${rm.category}</span>
                  <span class="text-slate-400 font-semibold">${rm.topic}:</span>
                  <span class="text-slate-300">${rm.content}</span>
                </div>
              `).join('')}
            </div>
          </details>
        </div>
      ` : '';

      return `
        <div class="flex gap-3 mb-6 animate-fadeIn group" id="msg-${msg.id || Date.now()}">
          <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shrink-0 shadow-md mt-0.5">
            <i data-lucide="sparkles" class="w-4 h-4"></i>
          </div>

          <div class="flex-1 max-w-3xl">
            <div class="glass-panel rounded-2xl rounded-tl-sm p-4 border border-slate-800/90 shadow-lg">
              <div class="prose-dark text-xs leading-relaxed">
                ${parsedContent}
              </div>
              ${memoriesHTML}
            </div>

            <!-- Feedback & Actions -->
            <div class="flex items-center gap-2 mt-1.5 px-1 text-[11px] text-slate-500">
              <button onclick="window.chatManager.sendFeedback(${msg.id}, 1)" class="hover:text-emerald-400 p-1 rounded transition" title="Helpful response">
                <i data-lucide="thumbs-up" class="w-3.5 h-3.5 ${msg.feedback_score === 1 ? 'text-emerald-400 fill-emerald-400' : ''}"></i>
              </button>
              <button onclick="window.chatManager.sendFeedback(${msg.id}, -1)" class="hover:text-rose-400 p-1 rounded transition" title="Not quite right">
                <i data-lucide="thumbs-down" class="w-3.5 h-3.5 ${msg.feedback_score === -1 ? 'text-rose-400 fill-rose-400' : ''}"></i>
              </button>
              <button onclick="window.chatManager.teachCorrection(${msg.id})" class="hover:text-indigo-400 p-1 rounded flex items-center gap-1 transition">
                <i data-lucide="book-plus" class="w-3.5 h-3.5"></i>
                <span>Teach Correction</span>
              </button>
            </div>
          </div>
        </div>
      `;
    }
  }

  async sendMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text || this.isSending) return;

    this.isSending = true;
    input.value = '';

    // If on welcome screen, clear it
    if (!this.currentSessionId) {
      this.container.innerHTML = '';
    }

    // Optimistically render user message
    this.container.insertAdjacentHTML('beforeend', this.createMessageHTML({
      role: 'user',
      content: text
    }));
    this.scrollToBottom();

    // Render typing indicator
    const typingId = 'typing-indicator-' + Date.now();
    this.container.insertAdjacentHTML('beforeend', `
      <div id="${typingId}" class="flex gap-3 mb-6 animate-fadeIn">
        <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shrink-0 shadow-md">
          <i data-lucide="sparkles" class="w-4 h-4"></i>
        </div>
        <div class="glass-panel rounded-2xl rounded-tl-sm px-4 py-3 border border-slate-800 flex items-center gap-2">
          <span class="text-xs text-indigo-400 font-medium">Stumpy is thinking & synthesizing memories...</span>
          <div class="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></div>
        </div>
      </div>
    `);
    this.scrollToBottom();
    lucide.createIcons();

    try {
      const resp = await api.chat(text, this.currentSessionId);
      this.currentSessionId = resp.session_id;

      // Remove typing indicator
      const typingElem = document.getElementById(typingId);
      if (typingElem) typingElem.remove();

      // Show Learning Insight Toast / Box if Stumpy learned a new fact
      if (resp.learned_insights && resp.learned_insights.length > 0) {
        resp.learned_insights.forEach(ins => {
          window.app.showToast(`✨ Learned new fact: ${ins.fact}`, 'success');
        });
      }

      // Render Assistant Response
      this.container.insertAdjacentHTML('beforeend', this.createMessageHTML({
        role: 'assistant',
        content: resp.message,
        recalled_memories: resp.recalled_memories
      }));

      // Render Follow-up Chips if present
      if (resp.suggested_followups && resp.suggested_followups.length > 0) {
        const followupsHTML = `
          <div class="flex flex-wrap gap-2 mb-6 ml-11 animate-fadeIn">
            ${resp.suggested_followups.map(f => `
              <button onclick="window.chatManager.fillPrompt('${this.escapeQuotes(f)}')" class="px-3 py-1 rounded-full text-[11px] bg-slate-800/80 hover:bg-indigo-600/30 hover:border-indigo-500/50 border border-slate-700 text-slate-300 transition flex items-center gap-1.5">
                <i data-lucide="corner-down-right" class="w-3 h-3 text-indigo-400"></i>
                <span>${f}</span>
              </button>
            `).join('')}
          </div>
        `;
        this.container.insertAdjacentHTML('beforeend', followupsHTML);
      }

      this.scrollToBottom();
      lucide.createIcons();

      // Refresh background datasets
      await this.loadSessions();
      if (window.memoryBank) window.memoryBank.refresh();
      if (window.memoryGraph) window.memoryGraph.loadData();
      if (window.personaSettings) window.personaSettings.loadStats();
      if (window.authManager) await window.authManager.initSession();

    } catch (err) {
      const typingElem = document.getElementById(typingId);
      if (typingElem) typingElem.remove();
      window.app.showToast('Error generating response: ' + err.message, 'error');
    } finally {
      this.isSending = false;
      input.focus();
    }
  }

  async sendFeedback(msgId, score) {
    if (!msgId) return;
    try {
      await api.sendFeedback(msgId, score);
      window.app.showToast(score === 1 ? '👍 Thanks for the positive reinforcement!' : '👎 Feedback noted to adapt future responses.', 'info');
    } catch (err) {
      console.error(err);
    }
  }

  teachCorrection(msgId) {
    const correction = prompt('What is the correct fact or preference Stumpy should remember?');
    if (correction && correction.trim()) {
      api.sendFeedback(msgId, -1, correction.trim())
        .then(() => {
          window.app.showToast('🧠 Correction recorded in Stumpy Brain!', 'success');
          if (window.memoryBank) window.memoryBank.refresh();
          if (window.memoryGraph) window.memoryGraph.loadData();
        })
        .catch(err => window.app.showToast('Failed to save correction: ' + err.message, 'error'));
    }
  }

  scrollToBottom() {
    if (this.container) {
      this.container.scrollTop = this.container.scrollHeight;
    }
  }

  escapeHTML(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  escapeQuotes(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
  }

  formatMarkdown(text) {
    if (!text) return '';
    let html = text;

    // Code blocks ```lang\ncode\n```
    html = html.replace(/```([a-zA-Z0-9_\-\.]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      return `<pre><code class="language-${lang}">${this.escapeHTML(code.trim())}</code></pre>`;
    });

    // Inline code `code`
    html = html.replace(/`([^`]+)`/g, (match, code) => {
      return `<code>${this.escapeHTML(code)}</code>`;
    });

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Bold & Italic
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Blockquotes
    html = html.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');

    // Bullet points
    html = html.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Line breaks
    html = html.replace(/\n\n/g, '<p></p>');
    html = html.replace(/\n/g, '<br/>');

    return html;
  }
}
