// Billing & Subscription Manager for Stumpy AI SaaS
// Supports real Stripe Checkout + fallback demo mode

class BillingManager {
  constructor() {
    this.plans = [];
    this.initEvents();
    this.checkUpgradeStatus();
  }

  initEvents() {
    // Pro Upgrade Trigger Buttons
    document.querySelectorAll('.trigger-upgrade-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.openUpgradeModal();
      });
    });
  }

  checkUpgradeStatus() {
    // Check if user just came back from Stripe Checkout
    const params = new URLSearchParams(window.location.search);
    if (params.get('upgrade') === 'success') {
      // Clean the URL
      window.history.replaceState({}, '', '/');
      // Refresh user data then show success toast
      setTimeout(async () => {
        if (window.authManager) {
          await window.authManager.initSession();
          window.app?.showToast('🌟 Welcome to Stumpy Pro! All limits unlocked!', 'success');
        }
      }, 500);
    } else if (params.get('upgrade') === 'cancelled') {
      window.history.replaceState({}, '', '/');
      setTimeout(() => {
        window.app?.showToast('Upgrade cancelled. You can upgrade anytime.', 'info');
      }, 500);
    }
  }

  async loadPlans() {
    try {
      this.plans = await api.getTiers();
      this.renderUpgradeModal();
    } catch (err) {
      console.error('Failed to load plans:', err);
    }
  }

  openUpgradeModal(reason = null) {
    const reasonBox = document.getElementById('upgrade-reason-alert');
    if (reasonBox) {
      if (reason) {
        reasonBox.classList.remove('hidden');
        reasonBox.innerHTML = `
          <div class="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold flex items-center gap-2">
            <i data-lucide="alert-circle" class="w-4 h-4 shrink-0 text-amber-400"></i>
            <span>${reason}</span>
          </div>
        `;
        lucide.createIcons();
      } else {
        reasonBox.classList.add('hidden');
      }
    }

    this.renderUpgradeModal();
    window.app.openModal('pricing-modal');
  }

  renderUpgradeModal() {
    const container = document.getElementById('pricing-plans-container');
    if (!container) return;

    const user = window.authManager?.currentUser;
    const currentTier = user?.tier || 'free';

    container.innerHTML = `
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
        <!-- Free Starter Plan -->
        <div class="glass-panel p-6 rounded-2xl border ${currentTier === 'free' ? 'border-slate-700 bg-slate-900/60' : 'border-slate-800'} flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-2">
              <h4 class="font-extrabold text-slate-100 text-base">Free Starter</h4>
              <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700">CURRENT PLAN</span>
            </div>
            <p class="text-xs text-slate-400 mb-4">Lightweight daily companion and learning playground.</p>

            <div class="mb-4">
              <span class="text-3xl font-black text-slate-100">$0</span>
              <span class="text-xs text-slate-500"> / forever</span>
            </div>

            <ul class="space-y-2 text-xs text-slate-300 mb-6">
              <li class="flex items-center gap-2">
                <i data-lucide="check" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
                <span>Up to <strong>50 memories</strong> stored</span>
              </li>
              <li class="flex items-center gap-2">
                <i data-lucide="check" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
                <span>5 Adaptive Skill Quizzes / day</span>
              </li>
              <li class="flex items-center gap-2">
                <i data-lucide="check" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
                <span>10 Second Brain notes</span>
              </li>
              <li class="flex items-center gap-2">
                <i data-lucide="check" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
                <span>Built-in Smart Adaptive Engine</span>
              </li>
              <li class="flex items-center gap-2">
                <i data-lucide="check" class="w-3.5 h-3.5 text-slate-400 shrink-0"></i>
                <span>Interactive 2D Knowledge Graph</span>
              </li>
            </ul>
          </div>

          <button disabled class="w-full py-2.5 px-4 rounded-xl bg-slate-800 text-slate-400 text-xs font-semibold cursor-default">
            Your Active Plan
          </button>
        </div>

        <!-- Stumpy Pro Plan -->
        <div class="glass-panel p-6 rounded-2xl border-2 border-indigo-500/80 bg-indigo-950/20 flex flex-col justify-between relative shadow-2xl shadow-indigo-500/10">
          <div class="absolute -top-3 right-4 px-3 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-md">
            POPULAR
          </div>

          <div>
            <div class="flex items-center justify-between mb-2">
              <h4 class="font-extrabold text-indigo-200 text-base flex items-center gap-1.5">
                <i data-lucide="sparkles" class="w-4 h-4 text-amber-400"></i>
                <span>Stumpy Pro</span>
              </h4>
            </div>
            <p class="text-xs text-indigo-300/80 mb-4">Unlimited persistent memory, deep reasoning models, and infinite mastery.</p>

            <div class="mb-4">
              <span class="text-3xl font-black text-white">$12</span>
              <span class="text-xs text-indigo-300"> / month</span>
            </div>

            <ul class="space-y-2 text-xs text-indigo-100 mb-6">
              <li class="flex items-center gap-2">
                <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-emerald-400 shrink-0"></i>
                <span><strong>Unlimited</strong> memories & facts</span>
              </li>
              <li class="flex items-center gap-2">
                <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-emerald-400 shrink-0"></i>
                <span><strong>Unlimited</strong> daily skill quizzes</span>
              </li>
              <li class="flex items-center gap-2">
                <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-emerald-400 shrink-0"></i>
                <span><strong>Unlimited</strong> Second Brain vault</span>
              </li>
              <li class="flex items-center gap-2">
                <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-emerald-400 shrink-0"></i>
                <span>Google Gemini 2.0 & GPT-4o access</span>
              </li>
              <li class="flex items-center gap-2">
                <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-emerald-400 shrink-0"></i>
                <span>Priority high-throughput responses</span>
              </li>
              <li class="flex items-center gap-2">
                <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-emerald-400 shrink-0"></i>
                <span>Full custom persona & tone synthesis</span>
              </li>
            </ul>
          </div>

          ${currentTier === 'pro' ? `
            <button onclick="window.billingManager.managePro()" class="w-full py-2.5 px-4 rounded-xl bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 text-xs font-bold">
              ✓ Pro Active — Manage Subscription
            </button>
          ` : `
            <button onclick="window.billingManager.startUpgrade()" id="upgrade-btn" class="w-full py-3 px-4 rounded-xl gradient-btn text-white text-xs font-black shadow-xl shadow-indigo-500/30 hover:scale-105 transition flex items-center justify-center gap-2">
              <i data-lucide="zap" class="w-4 h-4 text-amber-300"></i>
              <span>Upgrade to Stumpy Pro ($12/mo)</span>
            </button>
          `}
        </div>
      </div>
    `;

    lucide.createIcons();
  }

  async startUpgrade() {
    const btn = document.getElementById('upgrade-btn');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `
        <svg class="animate-spin w-4 h-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
        </svg>
        <span>Redirecting to checkout...</span>
      `;
    }

    try {
      const result = await api.upgradePlan('pro_monthly');

      if (result.checkout_url) {
        // Stripe is configured — redirect to Stripe's hosted checkout page
        window.location.href = result.checkout_url;
      } else {
        // Demo mode — instant upgrade (Stripe not configured)
        window.authManager.currentUser = result;
        window.authManager.updateUserUI();
        window.app.closeModal('pricing-modal');
        window.app.showToast('🌟 Congratulations! Upgraded to Stumpy Pro! All limits unlocked!', 'success');
        await window.authManager.refreshAllData();
      }
    } catch (err) {
      window.app.showToast('Upgrade failed: ' + err.message, 'error');
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `
          <i data-lucide="zap" class="w-4 h-4 text-amber-300"></i>
          <span>Upgrade to Stumpy Pro ($12/mo)</span>
        `;
        lucide.createIcons();
      }
    }
  }

  async managePro() {
    try {
      const result = await api.cancelPlan();

      if (result.portal_url) {
        // Redirect to Stripe Customer Portal (manage/cancel subscription)
        window.location.href = result.portal_url;
      } else {
        // Demo mode — instant cancel
        window.authManager.currentUser = result;
        window.authManager.updateUserUI();
        window.app.closeModal('pricing-modal');
        window.app.showToast('Reverted to Free tier.', 'info');
        await window.authManager.refreshAllData();
      }
    } catch (err) {
      window.app.showToast('Failed: ' + err.message, 'error');
    }
  }

  // Legacy method name for backwards compatibility
  async cancelPro() {
    return this.managePro();
  }
}
