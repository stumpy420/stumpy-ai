// Main Application Orchestrator & State Manager for Stumpy AI SaaS

class StumpyApp {
  constructor() {
    this.currentTab = 'chat';
    this.init();
  }

  async init() {
    this.initNavigation();
    this.initModals();

    // 1. Initialize Auth & Billing Managers
    window.authManager = new AuthManager();
    window.billingManager = new BillingManager();

    // 2. Initialize Core Submodules
    window.chatManager = new ChatManager('chat-messages-container', 'chat-sessions-list');
    window.memoryGraph = new MemoryGraphVisualizer('knowledge-graph-canvas', 'node-detail-panel');
    window.memoryBank = new MemoryBankManager('memory-cards-grid', 'memory-count-badge');
    window.skillMastery = new SkillMasteryManager('skills-grid-container', 'skills-count-badge');
    window.knowledgeVault = new KnowledgeVaultManager('notes-grid-container', 'notes-count-badge');
    window.personaSettings = new PersonaSettingsManager();

    // 3. Initialize Session & Load User Context
    await window.authManager.initSession();
    await window.billingManager.loadPlans();

    // 4. Initial Data Load
    await Promise.all([
      window.chatManager.loadSessions(),
      window.memoryBank.refresh(),
      window.skillMastery.refresh(),
      window.knowledgeVault.refresh(),
      window.personaSettings.loadSettings()
    ]);

    lucide.createIcons();
  }

  initNavigation() {
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        this.switchTab(tab);
      });
    });
  }

  switchTab(tabName) {
    this.currentTab = tabName;

    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
      const isTarget = btn.dataset.tab === tabName;
      if (isTarget) {
        btn.classList.add('bg-indigo-600/20', 'text-indigo-300', 'border', 'border-indigo-500/30');
        btn.classList.remove('text-slate-400', 'hover:bg-slate-800/60');
      } else {
        btn.classList.remove('bg-indigo-600/20', 'text-indigo-300', 'border', 'border-indigo-500/30');
        btn.classList.add('text-slate-400', 'hover:bg-slate-800/60');
      }
    });

    document.querySelectorAll('.tab-content').forEach(section => {
      section.classList.toggle('hidden', section.id !== `tab-${tabName}`);
    });

    if (tabName === 'brain') {
      setTimeout(() => {
        if (window.memoryGraph) {
          window.memoryGraph.resize();
          window.memoryGraph.loadData();
        }
        if (window.memoryBank) window.memoryBank.refresh();
      }, 50);
    } else if (tabName === 'skills') {
      if (window.skillMastery) window.skillMastery.refresh();
    } else if (tabName === 'notes') {
      if (window.knowledgeVault) window.knowledgeVault.refresh();
    } else if (tabName === 'persona') {
      if (window.personaSettings) window.personaSettings.loadSettings();
    }

    lucide.createIcons();
  }

  initModals() {
    document.querySelectorAll('.modal-backdrop').forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          modal.classList.add('hidden');
        }
      });
    });

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-backdrop').forEach(m => m.classList.add('hidden'));
      }
    });
  }

  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('hidden');
  }

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('hidden');
  }

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const borderClass = type === 'success' ? 'border-emerald-500/60 text-emerald-300' :
                        (type === 'error' ? 'border-rose-500/60 text-rose-300' : 'border-indigo-500/60 text-indigo-300');

    toast.className = `glass-panel px-4 py-3 rounded-2xl border ${borderClass} shadow-2xl text-xs font-semibold flex items-center gap-2 animate-fadeIn transition-all`;
    toast.innerHTML = `
      <i data-lucide="${type === 'success' ? 'check-circle-2' : (type === 'error' ? 'alert-triangle' : 'sparkles')}" class="w-4 h-4 shrink-0"></i>
      <span>${message}</span>
    `;

    container.appendChild(toast);
    lucide.createIcons();

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-8px)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.app = new StumpyApp();
});
