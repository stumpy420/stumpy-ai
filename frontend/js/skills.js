// Skill Mastery & Adaptive Quiz Component

class SkillMasteryManager {
  constructor(gridContainerId, countBadgeId) {
    this.container = document.getElementById(gridContainerId);
    this.countBadge = document.getElementById(countBadgeId);
    this.skills = [];
    this.currentQuiz = null;
    this.selectedOptionIndex = null;
    this.initEvents();
  }

  initEvents() {
    // Add Skill Form
    const skillForm = document.getElementById('add-skill-form');
    if (skillForm) {
      skillForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('skill-name').value.trim();
        const category = document.getElementById('skill-category').value;
        const notes = document.getElementById('skill-notes').value.trim();

        if (!name) return;

        try {
          await api.createSkill(name, category, notes);
          window.app.showToast(`🎯 Now tracking skill: ${name}!`, 'success');
          skillForm.reset();
          window.app.closeModal('add-skill-modal');
          await this.refresh();
          if (window.memoryGraph) window.memoryGraph.loadData();
        } catch (err) {
          window.app.showToast('Failed to add skill: ' + err.message, 'error');
        }
      });
    }
  }

  async refresh() {
    try {
      this.skills = await api.getSkills();
      if (this.countBadge) this.countBadge.innerText = this.skills.length;
      this.render();
    } catch (err) {
      console.error('Failed to fetch skills:', err);
    }
  }

  render() {
    if (!this.container) return;

    if (this.skills.length === 0) {
      this.container.innerHTML = `
        <div class="col-span-full py-12 text-center text-slate-500">
          <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-slate-800/80 flex items-center justify-center text-slate-400">
            <i data-lucide="target" class="w-6 h-6"></i>
          </div>
          <p class="text-sm font-medium text-slate-400">No skills currently tracked</p>
          <p class="text-xs text-slate-500 mt-1">Add a skill or mention what you're learning in chat!</p>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    this.container.innerHTML = this.skills.map(sk => {
      const accuracy = sk.total_quizzes_taken > 0 
        ? Math.round((sk.correct_answers / sk.total_quizzes_taken) * 100) 
        : 0;

      const mastery = Math.round(sk.mastery_level || 10);
      const progressBarColor = mastery >= 75 ? 'from-emerald-500 to-teal-400' : (mastery >= 40 ? 'from-indigo-500 to-cyan-400' : 'from-amber-500 to-orange-400');

      return `
        <div class="glass-panel glass-panel-hover rounded-2xl p-5 border border-slate-800/80 flex flex-col justify-between relative overflow-hidden group">
          <div class="absolute top-0 left-0 w-1.5 h-full bg-gradient-to-b ${progressBarColor}"></div>

          <div>
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide uppercase bg-slate-800 text-slate-300 border border-slate-700/50">${sk.category}</span>
              <button onclick="window.skillMastery.deleteSkill(${sk.id})" class="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-slate-800 text-slate-500 hover:text-rose-400 transition" title="Delete skill">
                <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
              </button>
            </div>

            <h3 class="font-bold text-base text-slate-100 mb-1">${sk.name}</h3>
            <p class="text-xs text-slate-400 line-clamp-2 mb-4">${sk.notes || 'Continuous adaptive mastery track'}</p>

            <!-- Mastery Meter -->
            <div class="space-y-1.5 mb-4">
              <div class="flex justify-between text-xs font-semibold">
                <span class="text-slate-300">Mastery Level</span>
                <span class="text-indigo-400">${mastery}%</span>
              </div>
              <div class="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
                <div class="h-full rounded-full bg-gradient-to-r ${progressBarColor} transition-all duration-700" style="width: ${mastery}%;"></div>
              </div>
            </div>

            <!-- Quiz Stats -->
            <div class="grid grid-cols-2 gap-2 p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60 text-center mb-4">
              <div>
                <div class="text-[11px] text-slate-500 font-medium">Quizzes Taken</div>
                <div class="text-sm font-bold text-slate-200">${sk.total_quizzes_taken}</div>
              </div>
              <div>
                <div class="text-[11px] text-slate-500 font-medium">Accuracy</div>
                <div class="text-sm font-bold text-emerald-400">${accuracy}%</div>
              </div>
            </div>
          </div>

          <button onclick="window.skillMastery.startQuiz(${sk.id})" class="w-full py-2.5 px-4 rounded-xl gradient-btn text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/10">
            <i data-lucide="play-circle" class="w-4 h-4"></i>
            Take Adaptive Quiz
          </button>
        </div>
      `;
    }).join('');

    lucide.createIcons();
  }

  async startQuiz(skillId) {
    try {
      window.app.openModal('quiz-modal');
      const quizContainer = document.getElementById('quiz-content');
      quizContainer.innerHTML = `
        <div class="py-16 text-center text-slate-400">
          <div class="w-8 h-8 mx-auto mb-3 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          <p class="text-sm font-medium">Stumpy AI is generating an adaptive question...</p>
        </div>
      `;

      this.currentQuiz = await api.getQuiz(skillId);
      this.selectedOptionIndex = null;
      this.renderQuizQuestion();
    } catch (err) {
      window.app.showToast('Failed to generate quiz: ' + err.message, 'error');
      window.app.closeModal('quiz-modal');
    }
  }

  renderQuizQuestion() {
    const q = this.currentQuiz;
    const quizContainer = document.getElementById('quiz-content');
    if (!quizContainer) return;

    quizContainer.innerHTML = `
      <div class="space-y-5">
        <div class="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <span class="text-xs uppercase font-bold tracking-wider text-indigo-400">${q.skill_name || 'Adaptive Quiz'}</span>
            <span class="ml-2 px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">${q.difficulty}</span>
          </div>
          <span class="text-xs text-slate-500">Targeted Learning</span>
        </div>

        <h3 class="text-base font-bold text-slate-100 leading-snug">${q.question}</h3>

        <div class="space-y-2.5" id="quiz-options-list">
          ${q.options.map((opt, idx) => `
            <button onclick="window.skillMastery.selectOption(${idx})" id="quiz-opt-${idx}" class="quiz-option-btn w-full p-3.5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 text-left text-xs text-slate-200 transition flex items-start gap-3">
              <span class="w-5 h-5 rounded-full border border-slate-700 bg-slate-800 flex items-center justify-center font-bold text-[10px] text-slate-400 shrink-0 mt-0.5">${String.fromCharCode(65 + idx)}</span>
              <span class="leading-relaxed">${opt}</span>
            </button>
          `).join('')}
        </div>

        <div id="quiz-feedback-box" class="hidden p-4 rounded-xl border"></div>

        <div class="pt-3 flex justify-end gap-3 border-t border-slate-800">
          <button onclick="window.app.closeModal('quiz-modal')" class="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition">Close</button>
          <button id="quiz-submit-btn" onclick="window.skillMastery.submitAnswer()" disabled class="px-5 py-2 rounded-xl gradient-btn text-white text-xs font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition">
            Submit Answer
          </button>
          <button id="quiz-next-btn" onclick="window.skillMastery.startQuiz(${q.skill_id})" class="hidden px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition flex items-center gap-1.5">
            <span>Next Question</span>
            <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `;

    lucide.createIcons();
  }

  selectOption(idx) {
    this.selectedOptionIndex = idx;
    document.querySelectorAll('.quiz-option-btn').forEach((btn, i) => {
      if (i === idx) {
        btn.classList.add('border-indigo-500', 'bg-indigo-950/40');
        btn.querySelector('span').classList.add('bg-indigo-600', 'text-white', 'border-indigo-500');
      } else {
        btn.classList.remove('border-indigo-500', 'bg-indigo-950/40');
        btn.querySelector('span').classList.remove('bg-indigo-600', 'text-white', 'border-indigo-500');
      }
    });

    const submitBtn = document.getElementById('quiz-submit-btn');
    if (submitBtn) submitBtn.disabled = false;
  }

  async submitAnswer() {
    if (this.selectedOptionIndex === null || !this.currentQuiz) return;

    const submitBtn = document.getElementById('quiz-submit-btn');
    const nextBtn = document.getElementById('quiz-next-btn');
    if (submitBtn) submitBtn.disabled = true;

    try {
      const res = await api.submitQuiz(this.currentQuiz.id, this.selectedOptionIndex);

      // Disable all option buttons
      document.querySelectorAll('.quiz-option-btn').forEach((btn, idx) => {
        btn.disabled = true;
        if (idx === res.correct_option_index) {
          btn.classList.add('border-emerald-500', 'bg-emerald-950/40');
          btn.querySelector('span').classList.add('bg-emerald-600', 'text-white');
        } else if (idx === this.selectedOptionIndex && !res.is_correct) {
          btn.classList.add('border-rose-500', 'bg-rose-950/40');
          btn.querySelector('span').classList.add('bg-rose-600', 'text-white');
        }
      });

      // Show Feedback Box
      const feedbackBox = document.getElementById('quiz-feedback-box');
      if (feedbackBox) {
        feedbackBox.classList.remove('hidden');
        feedbackBox.className = `p-4 rounded-xl border ${res.is_correct ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-200' : 'bg-rose-950/30 border-rose-800/60 text-rose-200'} text-xs space-y-2`;
        feedbackBox.innerHTML = `
          <div class="font-bold flex items-center gap-1.5 text-sm">
            <i data-lucide="${res.is_correct ? 'check-circle' : 'alert-circle'}" class="w-4 h-4"></i>
            <span>${res.is_correct ? 'Correct!' : 'Incorrect'}</span>
            <span class="text-xs font-normal opacity-80 ml-auto">Mastery: ${res.new_mastery_level}%</span>
          </div>
          <p class="leading-relaxed text-slate-300">${res.explanation}</p>
        `;
        lucide.createIcons();
      }

      if (submitBtn) submitBtn.classList.add('hidden');
      if (nextBtn) nextBtn.classList.remove('hidden');

      // Refresh skill mastery list & brain graph
      await this.refresh();
      if (window.memoryGraph) window.memoryGraph.loadData();
    } catch (err) {
      window.app.showToast('Failed to submit answer: ' + err.message, 'error');
    }
  }

  async deleteSkill(id) {
    if (!confirm('Remove this skill from tracking?')) return;
    try {
      await api.deleteSkill(id);
      window.app.showToast('Skill removed', 'info');
      await this.refresh();
      if (window.memoryGraph) window.memoryGraph.loadData();
    } catch (err) {
      window.app.showToast('Failed to delete skill: ' + err.message, 'error');
    }
  }
}
