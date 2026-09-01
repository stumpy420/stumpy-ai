// Second Brain / Knowledge Vault Component

class KnowledgeVaultManager {
  constructor(gridContainerId, countBadgeId) {
    this.container = document.getElementById(gridContainerId);
    this.countBadge = document.getElementById(countBadgeId);
    this.notes = [];
    this.searchQuery = '';
    this.selectedTag = '';
    this.initEvents();
  }

  initEvents() {
    const searchInput = document.getElementById('note-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value;
        this.render();
      });
    }

    // Add Note Form Submit
    const noteForm = document.getElementById('add-note-form');
    if (noteForm) {
      noteForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = document.getElementById('note-title').value.trim();
        const category = document.getElementById('note-category').value;
        const tags = document.getElementById('note-tags').value.trim();
        const content = document.getElementById('note-content').value.trim();

        if (!title || !content) return;

        try {
          await api.createNote(title, content, tags, category);
          window.app.showToast('📚 Note indexed in your Second Brain!', 'success');
          noteForm.reset();
          window.app.closeModal('add-note-modal');
          await this.refresh();
          if (window.memoryGraph) window.memoryGraph.loadData();
        } catch (err) {
          window.app.showToast('Failed to save note: ' + err.message, 'error');
        }
      });
    }
  }

  async refresh() {
    try {
      this.notes = await api.getNotes();
      if (this.countBadge) this.countBadge.innerText = this.notes.length;
      this.render();
    } catch (err) {
      console.error('Failed to fetch notes:', err);
    }
  }

  render() {
    if (!this.container) return;

    let filtered = this.notes;
    if (this.searchQuery.trim()) {
      const q = this.searchQuery.toLowerCase();
      filtered = filtered.filter(n =>
        n.title.toLowerCase().includes(q) ||
        n.content.toLowerCase().includes(q) ||
        n.tags.toLowerCase().includes(q)
      );
    }

    if (filtered.length === 0) {
      this.container.innerHTML = `
        <div class="col-span-full py-12 text-center text-slate-500">
          <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-slate-800/80 flex items-center justify-center text-slate-400">
            <i data-lucide="book-open" class="w-6 h-6"></i>
          </div>
          <p class="text-sm font-medium text-slate-400">No notes in your Second Brain</p>
          <p class="text-xs text-slate-500 mt-1">Add cheat sheets, code snippets, or project notes to index them!</p>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    this.container.innerHTML = filtered.map(n => {
      const tagsList = n.tags ? n.tags.split(',').map(t => t.trim()).filter(Boolean) : [];

      return `
        <div class="glass-panel glass-panel-hover rounded-2xl p-5 border border-slate-800/80 flex flex-col justify-between group">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-cyan-950/50 text-cyan-400 border border-cyan-800/40">${n.category}</span>
              <button onclick="window.knowledgeVault.deleteNote(${n.id})" class="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-slate-800 text-slate-500 hover:text-rose-400 transition" title="Delete note">
                <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
              </button>
            </div>

            <h3 class="font-bold text-sm text-slate-100 mb-2">${n.title}</h3>
            <p class="text-xs text-slate-300 whitespace-pre-wrap line-clamp-4 leading-relaxed font-mono bg-slate-900/60 p-3 rounded-xl border border-slate-800/60 mb-3">${n.content}</p>
          </div>

          <div>
            <div class="flex flex-wrap gap-1.5 mb-3">
              ${tagsList.map(tag => `
                <span class="px-2 py-0.5 rounded-md text-[10px] bg-slate-800 text-slate-400 border border-slate-700/50">#${tag}</span>
              `).join('')}
            </div>

            <div class="flex items-center justify-between text-[11px] text-slate-500 border-t border-slate-800/60 pt-2">
              <span>Indexed in Memory Graph</span>
              <button onclick="window.knowledgeVault.askAboutNote(${n.id})" class="text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 transition">
                <span>Discuss in Chat</span>
                <i data-lucide="message-square" class="w-3 h-3"></i>
              </button>
            </div>
          </div>
        </div>
      `;
    }).join('');

    lucide.createIcons();
  }

  askAboutNote(noteId) {
    const note = this.notes.find(n => n.id === noteId);
    if (!note) return;

    window.app.switchTab('chat');
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
      chatInput.value = `Can you explain the key concepts from my note "${note.title}" and how I can apply them?`;
      chatInput.focus();
    }
  }

  async deleteNote(id) {
    if (!confirm('Remove this note from your Second Brain?')) return;
    try {
      await api.deleteNote(id);
      window.app.showToast('Note deleted', 'info');
      await this.refresh();
      if (window.memoryGraph) window.memoryGraph.loadData();
    } catch (err) {
      window.app.showToast('Failed to delete note: ' + err.message, 'error');
    }
  }
}
