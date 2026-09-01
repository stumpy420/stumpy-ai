// Central API Client with JWT Bearer Token Authentication
const API_BASE = window.location.origin + '/api';

const api = {
  getToken() {
    return localStorage.getItem('stumpy_token');
  },

  setToken(token) {
    if (token) {
      localStorage.setItem('stumpy_token', token);
    } else {
      localStorage.removeItem('stumpy_token');
    }
  },

  async request(endpoint, options = {}) {
    const token = this.getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    if (res.status === 403) {
      const errData = await res.json().catch(() => ({ detail: 'Quota limit reached' }));
      // Trigger Pro Upgrade Modal if it was a quota error
      if (window.billingManager) {
        window.billingManager.openUpgradeModal(errData.detail || 'Free Tier Limit Reached');
      }
      throw new Error(errData.detail || 'Quota limit reached');
    }

    if (!res.ok) {
      const errText = await res.text();
      let detail = errText;
      try {
        const parsed = JSON.parse(errText);
        detail = parsed.detail || errText;
      } catch (e) {}
      throw new Error(detail);
    }

    return await res.json();
  },

  // Auth Endpoints
  async register(email, password, name = 'Adventurer') {
    const data = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name })
    });
    if (data.access_token) this.setToken(data.access_token);
    return data;
  },

  async login(email, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    if (data.access_token) this.setToken(data.access_token);
    return data;
  },

  async getGuestSession() {
    const data = await this.request('/auth/guest');
    if (data.access_token) this.setToken(data.access_token);
    return data;
  },

  async getMe() {
    return await this.request('/auth/me');
  },

  logout() {
    this.setToken(null);
  },

  // Billing Endpoints
  async getTiers() {
    return await this.request('/billing/tiers');
  },

  async upgradePlan(planId = 'pro_monthly') {
    return await this.request('/billing/upgrade', {
      method: 'POST',
      body: JSON.stringify({ plan_id: planId })
    });
  },

  async cancelPlan() {
    return await this.request('/billing/cancel', { method: 'POST' });
  },

  // Chat Endpoints
  async chat(message, sessionId = null, toneOverride = null) {
    return await this.request('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId, tone_override: toneOverride })
    });
  },

  async getSessions() {
    return await this.request('/chat/sessions');
  },

  async createSession(title = 'New Conversation') {
    return await this.request(`/chat/sessions?title=${encodeURIComponent(title)}`, {
      method: 'POST'
    });
  },

  async getHistory(sessionId) {
    return await this.request(`/chat/history/${sessionId}`);
  },

  async deleteSession(sessionId) {
    return await this.request(`/chat/history/${sessionId}`, { method: 'DELETE' });
  },

  async sendFeedback(messageId, score, correctionText = null) {
    return await this.request('/chat/feedback', {
      method: 'POST',
      body: JSON.stringify({ message_id: messageId, score, correction_text: correctionText })
    });
  },

  // Memory & Knowledge Graph Endpoints
  async getMemories(category = null, search = null) {
    let url = '/memory?';
    if (category) url += `category=${encodeURIComponent(category)}&`;
    if (search) url += `search=${encodeURIComponent(search)}&`;
    return await this.request(url);
  },

  async teachMemory(category, topic, content, isPinned = true) {
    return await this.request('/memory', {
      method: 'POST',
      body: JSON.stringify({ category, topic, content, is_pinned: isPinned })
    });
  },

  async updateMemory(id, category, topic, content, isPinned = false) {
    return await this.request(`/memory/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ category, topic, content, is_pinned: isPinned })
    });
  },

  async deleteMemory(id) {
    return await this.request(`/memory/${id}`, { method: 'DELETE' });
  },

  async togglePin(id) {
    return await this.request(`/memory/pin/${id}`, { method: 'POST' });
  },

  async getKnowledgeGraph() {
    return await this.request('/memory/graph');
  },

  async getProfile() {
    return await this.request('/memory/profile');
  },

  // Skills & Quiz Endpoints
  async getSkills() {
    return await this.request('/skills');
  },

  async createSkill(name, category = 'Programming', notes = '') {
    return await this.request('/skills', {
      method: 'POST',
      body: JSON.stringify({ name, category, notes })
    });
  },

  async getQuiz(skillId) {
    return await this.request(`/skills/${skillId}/quiz`);
  },

  async submitQuiz(quizId, selectedOptionIndex) {
    return await this.request('/skills/quiz/submit', {
      method: 'POST',
      body: JSON.stringify({ quiz_id: quizId, selected_option_index: selectedOptionIndex })
    });
  },

  async deleteSkill(skillId) {
    return await this.request(`/skills/${skillId}`, { method: 'DELETE' });
  },

  // Notes Endpoints
  async getNotes(search = null, tag = null) {
    let url = '/notes?';
    if (search) url += `search=${encodeURIComponent(search)}&`;
    if (tag) url += `tag=${encodeURIComponent(tag)}&`;
    return await this.request(url);
  },

  async createNote(title, content, tags = '', category = 'general') {
    return await this.request('/notes', {
      method: 'POST',
      body: JSON.stringify({ title, content, tags, category })
    });
  },

  async updateNote(id, title, content, tags = '', category = 'general') {
    return await this.request(`/notes/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ title, content, tags, category })
    });
  },

  async deleteNote(id) {
    return await this.request(`/notes/${id}`, { method: 'DELETE' });
  },

  // Settings & Stats
  async getSettings() {
    return await this.request('/settings');
  },

  async saveSettings(settingsObj) {
    return await this.request('/settings', {
      method: 'POST',
      body: JSON.stringify(settingsObj)
    });
  },

  async getStats() {
    return await this.request('/settings/stats');
  }
};
