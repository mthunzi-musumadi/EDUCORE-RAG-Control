import { ChatSession, UserSettings } from '../types';

const STORAGE_KEYS = {
  SESSIONS: 'educore_chat_sessions_v1',
  ACTIVE_SESSION: 'educore_active_session_id',
  ACTIVE_MODEL: 'educore_active_model_id',
  SETTINGS: 'educore_user_settings_v1',
  THEME: 'educore_theme_pref',
};

const DEFAULT_SETTINGS: UserSettings = {
  default_model: 'educore-enterprise-all',
  temperature: 0.7,
  system_prompt: '',
  streaming: true,
  theme: 'dark',
  auto_scroll: true,
};

export const StorageService = {
  getSessions(): ChatSession[] {
    try {
      const data = localStorage.getItem(STORAGE_KEYS.SESSIONS);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.error('Failed to load chat sessions:', e);
      return [];
    }
  },

  saveSessions(sessions: ChatSession[]): void {
    try {
      localStorage.setItem(STORAGE_KEYS.SESSIONS, JSON.stringify(sessions));
    } catch (e) {
      console.error('Failed to save chat sessions:', e);
    }
  },

  getActiveSessionId(): string | null {
    return localStorage.getItem(STORAGE_KEYS.ACTIVE_SESSION);
  },

  setActiveSessionId(id: string): void {
    localStorage.setItem(STORAGE_KEYS.ACTIVE_SESSION, id);
  },

  getActiveModelId(): string {
    return localStorage.getItem(STORAGE_KEYS.ACTIVE_MODEL) || 'educore-enterprise-all';
  },

  setActiveModelId(modelId: string): void {
    localStorage.setItem(STORAGE_KEYS.ACTIVE_MODEL, modelId);
  },

  getSettings(): UserSettings {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.SETTINGS);
      return raw ? { ...DEFAULT_SETTINGS, ...JSON.parse(raw) } : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  },

  saveSettings(settings: UserSettings): void {
    try {
      localStorage.setItem(STORAGE_KEYS.SETTINGS, JSON.stringify(settings));
    } catch (e) {
      console.error('Failed to save settings:', e);
    }
  },

  getTheme(): 'dark' | 'light' {
    const saved = localStorage.getItem(STORAGE_KEYS.THEME);
    if (saved === 'light' || saved === 'dark') return saved;
    return 'dark'; // Monochromatic dark theme default
  },

  setTheme(theme: 'dark' | 'light'): void {
    localStorage.setItem(STORAGE_KEYS.THEME, theme);
  },

  createSession(modelId: string): ChatSession {
    const newSession: ChatSession = {
      id: 'session-' + Date.now() + '-' + Math.random().toString(36).substring(2, 7),
      title: 'New Chat',
      createdAt: Date.now(),
      updatedAt: Date.now(),
      modelId,
      messages: [],
    };
    const sessions = this.getSessions();
    sessions.unshift(newSession);
    this.saveSessions(sessions);
    this.setActiveSessionId(newSession.id);
    return newSession;
  },

  updateSession(updated: ChatSession): void {
    const sessions = this.getSessions();
    const index = sessions.findIndex((s) => s.id === updated.id);
    if (index !== -1) {
      sessions[index] = { ...updated, updatedAt: Date.now() };
      this.saveSessions(sessions);
    }
  },

  deleteSession(id: string): void {
    const sessions = this.getSessions().filter((s) => s.id !== id);
    this.saveSessions(sessions);
    if (this.getActiveSessionId() === id) {
      if (sessions.length > 0) {
        this.setActiveSessionId(sessions[0].id);
      } else {
        localStorage.removeItem(STORAGE_KEYS.ACTIVE_SESSION);
      }
    }
  },

  exportAsMarkdown(session: ChatSession): string {
    let md = `# ${session.title}\n\n`;
    md += `*Date: ${new Date(session.createdAt).toLocaleString()}*\n`;
    md += `*Model: ${session.modelId}*\n\n---\n\n`;
    for (const msg of session.messages) {
      const speaker = msg.role === 'user' ? '👤 User' : '🤖 Educore AI';
      md += `### ${speaker} (${new Date(msg.timestamp).toLocaleTimeString()})\n\n${msg.content}\n\n---\n\n`;
    }
    return md;
  }
};
