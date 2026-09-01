// Memory Bank & Fact Manager Component

class MemoryBankManager {
  constructor(containerId, countBadgeId) {
    this.container = document.getElementById(containerId);
    this.countBadge = document.getElementById(countBadgeId);
    this.currentCategory = 'all';
    this.searchQuery = '';
    this.memories = [];
    this.initEvents();
  }

  initEvents() {
    const searchInput = document.getElementById('memory-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value;
        this.render();
      });
    }

    // Category filter tabs
    document.querySelectorAll('.memory-filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.memory-filter-btn').forEach(b => {
          b.classList.remove('bg-indigo-600', 'text-white');
          b.classList.add('bg-slate-800/80', 'text-slate-400');
        });
        btn.classList.remove('bg-slate-800/80', 'text-slate-400');
        btn.classList.add('bg-indigo-600', 'text-white');

        this.currentCategory = btn.dataset.category;
        this.render();
      });
    });

    // Teach Form Submit
    const teachForm = document.getElementById('teach-memory-form');
    if (teachForm) {
      teachForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const category = document.getElementById('teach-category').value;
        const topic = document.getElementById('teach-topic').value.trim();
        const content = document.getElementById('teach-content').value.trim();
        const isPinned = document.getElementById('teach-pinned').checked;

        if (!topic || !content) return;

        try {
          await api.teachMemory(category, topic, content, isPinned);
          window.app.showToast('🧠 Memory saved and pinned to Stumpy Brain!', 'success');
          teachForm.reset();
          window.app.closeModal('teach-modal');
          await this.refresh();
          if (window.memoryGraph) window.memoryGraph.loadData();
        } catch (err) {
          window.app.showToast('Failed to save memory: ' + err.message, 'error');
        }
      });
    }
  }

  async refresh() {
    try {
      this.memories = await api.getMemories();
      if (this.countBadge) this.countBadge.innerText = this.memories.length;
      this.render();
    } catch (err) {
      console.error('Failed to fetch memories:', err);
    }
  }

  render() {
    if (!this.container) return;

    let filtered = this.memories;
    if (this.currentCategory !== 'all') {
      filtered = filtered.filter(m => m.category === this.currentCategory);
    }
    if (this.searchQuery.trim()) {
      const q = this.searchQuery.toLowerCase();
      filtered = filtered.filter(m => 
        m.topic.toLowerCase().includes(q) || 
        m.content.toLowerCase().includes(q) ||
        m.category.toLowerCase().includes(q)
      );
    }

    if (filtered.length === 0) {
      this.container.innerHTML = `
        <div class="col-span-full py-12 text-center text-slate-500">
          <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-slate-800/80 flex items-center justify-center text-slate-400">
            <i data-lucide="brain-circuit" class="w-6 h-6"></i>
          </div>
          <p class="text-sm font-medium text-slate-400">No memories match this filter</p>
          <p class="text-xs text-slate-500 mt-1">Chat with Stumpy AI or click "Teach Stumpy AI" to add facts.</p>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    this.container.innerHTML = filtered.map(m => {
      const badgeClass = `badge-${m.category}`;
      const timeAgo = this.formatDate(m.updated_at || m.created_at);

      return `
        <div class="glass-panel glass-panel-hover rounded-xl p-4 flex flex-col justify-between border border-slate-800/80 relative group">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="px-2 py-0.5 rounded-md text-[11px] font-semibold uppercase ${badgeClass}">${m.category}</span>
              <div class="flex items-center gap-1">
                <button onclick="window.memoryBank.togglePin(${m.id})" class="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-amber-400 transition" title="${m.is_pinned ? 'Unpin' : 'Pin to priority'}">
                  <i data-lucide="pin" class="w-3.5 h-3.5 ${m.is_pinned ? 'text-amber-400 fill-amber-400' : ''}"></i>
                </button>
                <button onclick="window.memoryBank.editMemory(${m.id})" class="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-indigo-400 transition" title="Edit fact">
                  <i data-lucide="edit-2" class="w-3.5 h-3.5"></i>
                </button>
                <button onclick="window.memoryBank.deleteMemory(${m.id})" class="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition" title="Delete fact">
                  <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                </button>
              </div>
            </div>

            <h4 class="font-bold text-slate-200 text-sm mb-1">${m.topic.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</h4>
            <p class="text-xs text-slate-300 leading-relaxed">${m.content}</p>
          </div>

          <div class="mt-4 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-400">
            <span class="flex items-center gap-1">
              <i data-lucide="sparkles" class="w-3 h-3 text-indigo-400"></i>
              ${m.source === 'direct_teaching' ? 'Manual' : (m.source === 'correction' ? 'Correction' : 'Auto-learned')}
            </span>
            <span>Recalled ${m.access_count || 0}x • ${timeAgo}</span>
          </div>
        </div>
      `;
    }).join('');

    lucide.createIcons();
  }

  async togglePin(id) {
    try {
      await api.togglePin(id);
      await this.refresh();
      if (window.memoryGraph) window.memoryGraph.loadData();
    } catch (err) {
      window.app.showToast('Failed to toggle pin: ' + err.message, 'error');
    }
  }

  async deleteMemory(id) {
    if (!confirm('Are you sure you want Stumpy AI to forget this memory?')) return;
    try {
      await api.deleteMemory(id);
      window.app.showToast('Memory removed from brain', 'info');
      await this.refresh();
      if (window.memoryGraph) window.memoryGraph.loadData();
    } catch (err) {
      window.app.showToast('Failed to delete memory: ' + err.message, 'error');
    }
  }

  editMemory(id) {
    const mem = this.memories.find(m => m.id === id);
    if (!mem) return;

    const newContent = prompt('Edit memory fact:', mem.content);
    if (newContent !== null && newContent.trim()) {
      api.updateMemory(id, mem.category, mem.topic, newContent.trim(), mem.is_pinned)
        .then(() => {
          window.app.showToast('Memory updated!', 'success');
          this.refresh();
          if (window.memoryGraph) window.memoryGraph.loadData();
        })
        .catch(err => window.app.showToast('Failed to update: ' + err.message, 'error'));
    }
  }

  formatDate(dateStr) {
    if (!dateStr) return 'recently';
    const date = new Date(dateStr);
    const now = new Date();
    const diffSecs = Math.floor((now - date) / 1000);
    if (diffSecs < 60) return 'just now';
    if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ago`;
    if (diffSecs < 86400) return `${Math.floor(diffSecs / 3600)}h ago`;
    return `${Math.floor(diffSecs / 86400)}d ago`;
  }
}
