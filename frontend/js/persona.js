// Persona Tuner, Model Config, and System Stats

class PersonaSettingsManager {
  constructor() {
    this.settings = {};
    this.stats = {};
    this.initEvents();
  }

  initEvents() {
    // Form Submit
    const form = document.getElementById('settings-form');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.saveFromUI();
      });
    }

    // Sliders Live Update
    const concisenessSlider = document.getElementById('setting-conciseness');
    const formalitySlider = document.getElementById('setting-formality');

    if (concisenessSlider) {
      concisenessSlider.addEventListener('input', (e) => {
        const val = e.target.value;
        document.getElementById('conciseness-val').innerText = val < 35 ? 'Thorough & Deep' : (val > 65 ? 'Very Concise & Bulleted' : 'Balanced Detail');
      });
    }

    if (formalitySlider) {
      formalitySlider.addEventListener('input', (e) => {
        const val = e.target.value;
        document.getElementById('formality-val').innerText = val < 35 ? 'Casual & Energetic' : (val > 65 ? 'Academic & Formal' : 'Polished & Friendly');
      });
    }

    // Provider Selector Toggle
    const providerSelect = document.getElementById('setting-provider');
    if (providerSelect) {
      providerSelect.addEventListener('change', (e) => {
        this.updateProviderVisibility(e.target.value);
      });
    }
  }

  async loadSettings() {
    try {
      this.settings = await api.getSettings();
      this.populateUI(this.settings);
      await this.loadStats();
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  }

  async loadStats() {
    try {
      this.stats = await api.getStats();
      this.populateStats(this.stats);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  }

  populateUI(s) {
    const providerElem = document.getElementById('setting-provider');
    if (providerElem) providerElem.value = s.provider || 'builtin';

    const geminiKeyElem = document.getElementById('setting-gemini-key');
    if (geminiKeyElem) geminiKeyElem.value = s.gemini_api_key || '';

    const geminiModelElem = document.getElementById('setting-gemini-model');
    if (geminiModelElem) geminiModelElem.value = s.gemini_model || 'gemini-2.0-flash';

    const openaiKeyElem = document.getElementById('setting-openai-key');
    if (openaiKeyElem) openaiKeyElem.value = s.openai_api_key || '';

    const openaiModelElem = document.getElementById('setting-openai-model');
    if (openaiModelElem) openaiModelElem.value = s.openai_model || 'gpt-4o-mini';

    const concisenessElem = document.getElementById('setting-conciseness');
    if (concisenessElem) {
      concisenessElem.value = s.tone_conciseness ?? 50;
      concisenessElem.dispatchEvent(new Event('input'));
    }

    const formalityElem = document.getElementById('setting-formality');
    if (formalityElem) {
      formalityElem.value = s.tone_formality ?? 40;
      formalityElem.dispatchEvent(new Event('input'));
    }

    const styleElem = document.getElementById('setting-style');
    if (styleElem) styleElem.value = s.tone_style || 'balanced';

    this.updateProviderVisibility(s.provider || 'builtin');
  }

  populateStats(st) {
    const elMem = document.getElementById('stat-total-memories');
    if (elMem) elMem.innerText = st.total_memories;

    const elPinned = document.getElementById('stat-pinned-memories');
    if (elPinned) elPinned.innerText = st.pinned_memories;

    const elSkills = document.getElementById('stat-total-skills');
    if (elSkills) elSkills.innerText = st.total_skills;

    const elMastery = document.getElementById('stat-avg-mastery');
    if (elMastery) elMastery.innerText = `${st.average_mastery}%`;

    const elNotes = document.getElementById('stat-total-notes');
    if (elNotes) elNotes.innerText = st.total_notes;

    const elTurns = document.getElementById('stat-total-turns');
    if (elTurns) elTurns.innerText = st.total_chat_turns;
  }

  updateProviderVisibility(provider) {
    const geminiBox = document.getElementById('gemini-config-box');
    const openaiBox = document.getElementById('openai-config-box');

    if (geminiBox) geminiBox.classList.toggle('hidden', provider !== 'gemini');
    if (openaiBox) openaiBox.classList.toggle('hidden', provider !== 'openai');
  }

  async saveFromUI() {
    const payload = {
      provider: document.getElementById('setting-provider').value,
      gemini_api_key: document.getElementById('setting-gemini-key')?.value || '',
      gemini_model: document.getElementById('setting-gemini-model')?.value || 'gemini-2.0-flash',
      openai_api_key: document.getElementById('setting-openai-key')?.value || '',
      openai_model: document.getElementById('setting-openai-model')?.value || 'gpt-4o-mini',
      tone_conciseness: parseInt(document.getElementById('setting-conciseness').value, 10),
      tone_formality: parseInt(document.getElementById('setting-formality').value, 10),
      tone_style: document.getElementById('setting-style').value,
      auto_learning_enabled: true,
      memory_recall_limit: 6
    };

    try {
      await api.saveSettings(payload);
      window.app.showToast('⚙️ Persona & Engine settings saved!', 'success');
      await this.loadStats();
    } catch (err) {
      window.app.showToast('Failed to save settings: ' + err.message, 'error');
    }
  }
}
