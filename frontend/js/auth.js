// Authentication & User State Manager for Stumpy AI SaaS

class AuthManager {
  constructor() {
    this.currentUser = null;
    this.initEvents();
  }

  initEvents() {
    // Auth Form Toggle (Sign In vs Register)
    const toggleBtns = document.querySelectorAll('.auth-tab-toggle');
    toggleBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const mode = btn.dataset.mode;
        this.setAuthMode(mode);
      });
    });

    // Login Form Submit
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        if (!email || !password) return;

        try {
          const res = await api.login(email, password);
          this.currentUser = res.user;
          window.app.showToast(`👋 Welcome back, ${this.currentUser.name}!`, 'success');
          window.app.closeModal('auth-modal');
          this.updateUserUI();
          await this.refreshAllData();
        } catch (err) {
          window.app.showToast('Login failed: ' + err.message, 'error');
        }
      });
    }

    // Register Form Submit
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
      registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('reg-name').value.trim() || 'Explorer';
        const email = document.getElementById('reg-email').value.trim();
        const password = document.getElementById('reg-password').value;
        if (!email || !password) return;

        try {
          const res = await api.register(email, password, name);
          this.currentUser = res.user;
          window.app.showToast(`🎉 Account created! Welcome, ${name}!`, 'success');
          window.app.closeModal('auth-modal');
          this.updateUserUI();
          await this.refreshAllData();
        } catch (err) {
          window.app.showToast('Registration failed: ' + err.message, 'error');
        }
      });
    }
  }

  async initSession() {
    try {
      const token = api.getToken();
      if (token) {
        this.currentUser = await api.getMe();
      } else {
        const guestRes = await api.getGuestSession();
        this.currentUser = guestRes.user;
      }
      this.updateUserUI();
    } catch (err) {
      console.warn('Session init fallback to guest:', err);
      try {
        const guestRes = await api.getGuestSession();
        this.currentUser = guestRes.user;
        this.updateUserUI();
      } catch (e) {
        console.error('Failed to init guest:', e);
      }
    }
  }

  setAuthMode(mode) {
    const loginBox = document.getElementById('login-box');
    const registerBox = document.getElementById('register-box');
    const loginToggle = document.getElementById('auth-tab-login');
    const regToggle = document.getElementById('auth-tab-register');

    if (mode === 'register') {
      if (loginBox) loginBox.classList.add('hidden');
      if (registerBox) registerBox.classList.remove('hidden');
      if (loginToggle) {
        loginToggle.classList.remove('bg-indigo-600', 'text-white');
        loginToggle.classList.add('text-slate-400');
      }
      if (regToggle) {
        regToggle.classList.add('bg-indigo-600', 'text-white');
        regToggle.classList.remove('text-slate-400');
      }
    } else {
      if (loginBox) loginBox.classList.remove('hidden');
      if (registerBox) registerBox.classList.add('hidden');
      if (loginToggle) {
        loginToggle.classList.add('bg-indigo-600', 'text-white');
        loginToggle.classList.remove('text-slate-400');
      }
      if (regToggle) {
        regToggle.classList.remove('bg-indigo-600', 'text-white');
        regToggle.classList.add('text-slate-400');
      }
    }
  }

  updateUserUI() {
    if (!this.currentUser) return;
    const u = this.currentUser;

    // Header User Profile Pill
    const userContainer = document.getElementById('header-user-profile');
    if (userContainer) {
      const isPro = u.tier === 'pro';
      const badgeClass = isPro 
        ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white font-black shadow-lg shadow-amber-500/20' 
        : 'bg-slate-800 text-slate-400 border border-slate-700';

      const memUsageText = isPro 
        ? `${u.memories_count} memories (Unlimited)`
        : `${u.memories_count}/${u.memory_limit} memories`;

      const memUsagePercent = isPro ? 100 : Math.min(100, Math.round((u.memories_count / u.memory_limit) * 100));

      userContainer.innerHTML = `
        <div class="flex items-center gap-2.5">
          <!-- Memory Quota Mini Progress (Desktop) -->
          <div class="hidden lg:flex flex-col items-end pr-2 border-r border-slate-800">
            <div class="text-[10px] text-slate-400 font-semibold flex items-center gap-1">
              <i data-lucide="brain" class="w-3 h-3 text-purple-400"></i>
              <span>${memUsageText}</span>
            </div>
            ${!isPro ? `
              <div class="w-24 h-1.5 bg-slate-800 rounded-full overflow-hidden mt-1">
                <div class="h-full rounded-full ${memUsagePercent > 80 ? 'bg-rose-500' : 'bg-indigo-500'}" style="width: ${memUsagePercent}%;"></div>
              </div>
            ` : ''}
          </div>

          <!-- User Badge / Menu Trigger -->
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider ${badgeClass}">
              ${isPro ? '🌟 PRO' : '🆓 FREE'}
            </span>

            ${u.is_guest ? `
              <button onclick="window.app.openModal('auth-modal')" class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition">
                <i data-lucide="log-in" class="w-3.5 h-3.5 text-indigo-400"></i>
                <span>Sign In / Save</span>
              </button>
            ` : `
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-slate-200">${u.name}</span>
                <button onclick="window.authManager.logout()" class="p-1.5 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-rose-400 transition" title="Sign Out">
                  <i data-lucide="log-out" class="w-3.5 h-3.5"></i>
                </button>
              </div>
            `}

            <!-- Pro Upgrade Button (if on free tier) -->
            ${!isPro ? `
              <button onclick="window.billingManager.openUpgradeModal()" class="hidden sm:flex items-center gap-1 px-3 py-1.5 rounded-xl gradient-btn text-white text-xs font-bold shadow-lg shadow-indigo-500/20 hover:scale-105 transition animate-pulse">
                <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
                <span>Upgrade</span>
              </button>
            ` : ''}
          </div>
        </div>
      `;
      lucide.createIcons();
    }
  }

  logout() {
    api.logout();
    window.app.showToast('Logged out of Stumpy AI', 'info');
    setTimeout(() => {
      window.location.reload();
    }, 400);
  }

  async refreshAllData() {
    await Promise.all([
      window.chatManager.loadSessions(),
      window.memoryBank.refresh(),
      window.skillMastery.refresh(),
      window.knowledgeVault.refresh(),
      window.personaSettings.loadSettings()
    ]);
  }
}
