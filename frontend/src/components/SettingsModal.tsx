import React, { useState, useEffect } from 'react';
import { User, UserSettings, EducoreModel } from '../types';
import { ApiService } from '../services/api';
import { 
  X, 
  Settings as SettingsIcon, 
  User as UserIcon, 
  Palette, 
  Info, 
  Lock, 
  Check, 
  AlertCircle,
  Sliders,
  Shield,
  Volume2,
  VolumeX,
  Play
} from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: User | null;
  onUserUpdate: (updatedUser: User) => void;
  settings: UserSettings;
  onSettingsUpdate: (newSettings: UserSettings) => void;
  models: EducoreModel[];
  theme: 'dark' | 'light';
  onThemeToggle: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  user,
  onUserUpdate,
  settings,
  onSettingsUpdate,
  models,
  theme,
  onThemeToggle,
}) => {
  const [activeTab, setActiveTab] = useState<'general' | 'account' | 'interface' | 'audio' | 'about'>('general');

  // Form states
  const [defaultModel, setDefaultModel] = useState(settings.default_model);
  const [temperature, setTemperature] = useState(settings.temperature);
  const [systemPrompt, setSystemPrompt] = useState(settings.system_prompt);
  const [streaming, setStreaming] = useState(settings.streaming);
  const [autoScroll, setAutoScroll] = useState(settings.auto_scroll);

  // Profile states
  const [displayName, setDisplayName] = useState(user?.name || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Audio / TTS states
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<string>('');
  const [speechRate, setSpeechRate] = useState<number>(1.0);

  // Status message
  const [statusMsg, setStatusMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if ('speechSynthesis' in window) {
      const loadVoices = () => {
        const available = window.speechSynthesis.getVoices();
        setVoices(available);
        if (available.length > 0 && !selectedVoice) {
          const defaultV = available.find((v) => v.lang.startsWith('en')) || available[0];
          setSelectedVoice(defaultV.name);
        }
      };
      loadVoices();
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  if (!isOpen) return null;

  const handleSaveGeneral = () => {
    const updated: UserSettings = {
      ...settings,
      default_model: defaultModel,
      temperature,
      system_prompt: systemPrompt,
      streaming,
      auto_scroll: autoScroll,
    };
    onSettingsUpdate(updated);
    setStatusMsg({ text: 'General settings saved successfully.', type: 'success' });
    setTimeout(() => setStatusMsg(null), 3000);
  };

  const handleTestAudio = () => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance('This is Educore Enterprise RAG speech synthesis preview.');
    const v = voices.find((voice) => voice.name === selectedVoice);
    if (v) utterance.voice = v;
    utterance.rate = speechRate;
    window.speechSynthesis.speak(utterance);
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setLoading(true);
    setStatusMsg(null);
    try {
      const resp = await ApiService.updateProfile(displayName, user.email);
      onUserUpdate(resp.user);
      setStatusMsg({ text: 'Profile updated successfully.', type: 'success' });
    } catch (err: any) {
      setStatusMsg({ text: err.message || 'Failed to update profile.', type: 'error' });
    } finally {
      setLoading(false);
      setTimeout(() => setStatusMsg(null), 3000);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setStatusMsg({ text: 'New passwords do not match.', type: 'error' });
      return;
    }
    setLoading(true);
    setStatusMsg(null);
    try {
      await ApiService.updatePassword(currentPassword, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setStatusMsg({ text: 'Password changed successfully.', type: 'success' });
    } catch (err: any) {
      setStatusMsg({ text: err.message || 'Failed to update password.', type: 'error' });
    } finally {
      setLoading(false);
      setTimeout(() => setStatusMsg(null), 3000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-2xl bg-card border border-border rounded-2xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-2.5">
            <SettingsIcon className="h-5 w-5 text-foreground" />
            <h3 className="font-semibold text-base text-foreground">Settings</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Status Toast */}
        {statusMsg && (
          <div className={`mx-6 mt-4 p-3 rounded-lg text-xs flex items-center gap-2 ${
            statusMsg.type === 'success' 
              ? 'bg-foreground/10 text-foreground border border-foreground/20' 
              : 'bg-red-500/10 text-red-500 border border-red-500/20'
          }`}>
            {statusMsg.type === 'success' ? <Check className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
            <span>{statusMsg.text}</span>
          </div>
        )}

        {/* Content Layout */}
        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar Tabs (Open WebUI 1:1) */}
          <div className="w-48 border-r border-border p-3 space-y-1 bg-muted/20 shrink-0">
            <button
              onClick={() => setActiveTab('general')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded-lg transition ${
                activeTab === 'general' ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              <Sliders className="h-4 w-4" />
              General
            </button>
            <button
              onClick={() => setActiveTab('interface')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded-lg transition ${
                activeTab === 'interface' ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              <Palette className="h-4 w-4" />
              Interface
            </button>
            <button
              onClick={() => setActiveTab('audio')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded-lg transition ${
                activeTab === 'audio' ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              <Volume2 className="h-4 w-4" />
              Audio (TTS)
            </button>
            <button
              onClick={() => setActiveTab('account')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded-lg transition ${
                activeTab === 'account' ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              <UserIcon className="h-4 w-4" />
              Account
            </button>
            <button
              onClick={() => setActiveTab('about')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded-lg transition ${
                activeTab === 'about' ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              <Info className="h-4 w-4" />
              About
            </button>
          </div>

          {/* Main Tab Panel */}
          <div className="flex-1 overflow-y-auto p-6 text-xs text-foreground">
            {/* General Tab */}
            {activeTab === 'general' && (
              <div className="space-y-5">
                <div className="space-y-1.5">
                  <label className="font-semibold text-xs text-foreground">Default Model</label>
                  <select
                    value={defaultModel}
                    onChange={(e) => setDefaultModel(e.target.value)}
                    className="w-full p-2 bg-background border border-border rounded-lg text-foreground font-mono text-xs"
                  >
                    {models.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name} ({m.requiredTier || 'public'})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between items-center">
                    <label className="font-semibold text-xs text-foreground">Default Temperature</label>
                    <span className="font-mono text-xs text-muted-foreground">{temperature.toFixed(2)}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1.5"
                    step="0.05"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full accent-foreground"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="font-semibold text-xs text-foreground">Default System Prompt</label>
                  <textarea
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                    rows={4}
                    placeholder="Global baseline instructions across all new conversations..."
                    className="w-full p-2.5 bg-background border border-border rounded-lg text-foreground font-mono text-xs resize-y"
                  />
                </div>

                <div className="flex items-center justify-between pt-2">
                  <div>
                    <span className="font-semibold text-xs text-foreground">Stream Responses</span>
                    <p className="text-[11px] text-muted-foreground">Display assistant tokens in real-time as they generate</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={streaming}
                    onChange={(e) => setStreaming(e.target.checked)}
                    className="w-4 h-4 accent-foreground cursor-pointer rounded"
                  />
                </div>

                <div className="flex justify-end pt-4">
                  <button
                    onClick={handleSaveGeneral}
                    className="px-4 py-1.5 bg-foreground text-background font-medium rounded-lg hover:opacity-90 transition"
                  >
                    Save Changes
                  </button>
                </div>
              </div>
            )}

            {/* Interface Tab */}
            {activeTab === 'interface' && (
              <div className="space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-semibold text-xs text-foreground">Interface Theme</span>
                    <p className="text-[11px] text-muted-foreground">Toggle between ChatGPT / Open WebUI Dark and Light themes</p>
                  </div>
                  <button
                    onClick={onThemeToggle}
                    className="px-3 py-1.5 border border-border rounded-lg bg-muted text-foreground hover:bg-muted/80 font-medium transition"
                  >
                    Currently: {theme === 'dark' ? 'Dark Mode' : 'Light Mode'}
                  </button>
                </div>

                <hr className="border-border" />

                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-semibold text-xs text-foreground">Auto-Scroll to Bottom</span>
                    <p className="text-[11px] text-muted-foreground">Automatically keep viewport aligned to bottom on new tokens</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={autoScroll}
                    onChange={(e) => setAutoScroll(e.target.checked)}
                    className="w-4 h-4 accent-foreground cursor-pointer rounded"
                  />
                </div>
              </div>
            )}

            {/* Audio (TTS) Tab */}
            {activeTab === 'audio' && (
              <div className="space-y-5">
                <div className="space-y-1.5">
                  <label className="font-semibold text-xs text-foreground">Text-to-Speech Voice</label>
                  <select
                    value={selectedVoice}
                    onChange={(e) => setSelectedVoice(e.target.value)}
                    className="w-full p-2 bg-background border border-border rounded-lg text-foreground text-xs"
                  >
                    {voices.map((v) => (
                      <option key={v.name} value={v.name}>
                        {v.name} ({v.lang})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between items-center">
                    <label className="font-semibold text-xs text-foreground">Speech Rate (Speed)</label>
                    <span className="font-mono text-xs text-muted-foreground">{speechRate.toFixed(2)}x</span>
                  </div>
                  <input
                    type="range"
                    min="0.5"
                    max="2.0"
                    step="0.05"
                    value={speechRate}
                    onChange={(e) => setSpeechRate(parseFloat(e.target.value))}
                    className="w-full accent-foreground"
                  />
                </div>

                <div className="pt-2">
                  <button
                    onClick={handleTestAudio}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-muted hover:bg-muted/80 border border-border rounded-lg text-foreground font-medium transition"
                  >
                    <Play size={13} fill="currentColor" />
                    <span>Test Voice Preview</span>
                  </button>
                </div>
              </div>
            )}

            {/* Account Tab */}
            {activeTab === 'account' && (
              <div className="space-y-6">
                {user ? (
                  <>
                    <form onSubmit={handleUpdateProfile} className="space-y-3 pb-5 border-b border-border">
                      <h4 className="font-semibold text-foreground text-xs">Profile Information</h4>
                      <div className="space-y-1">
                        <label className="text-muted-foreground">Full Name</label>
                        <input
                          type="text"
                          value={displayName}
                          onChange={(e) => setDisplayName(e.target.value)}
                          className="w-full p-2 bg-background border border-border rounded-lg text-foreground"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-muted-foreground">Email Address</label>
                        <input
                          type="email"
                          value={user.email}
                          disabled
                          className="w-full p-2 bg-background border border-border rounded-lg text-muted-foreground opacity-70"
                        />
                      </div>
                      <div className="flex items-center gap-4 text-muted-foreground pt-1">
                        <span>Role: <strong className="text-foreground uppercase">{user.role}</strong></span>
                        <span>Clearance: <strong className="text-foreground uppercase">{user.clearance}</strong></span>
                        <span>Campus: <strong className="text-foreground">{user.campus}</strong></span>
                      </div>
                      <div className="pt-1">
                        <button
                          type="submit"
                          disabled={loading}
                          className="px-3 py-1.5 bg-foreground text-background font-medium rounded-lg hover:opacity-90 transition"
                        >
                          {loading ? 'Saving...' : 'Update Profile'}
                        </button>
                      </div>
                    </form>

                    <form onSubmit={handleUpdatePassword} className="space-y-3">
                      <h4 className="font-semibold text-foreground text-xs">Change Password</h4>
                      <div className="space-y-1">
                        <label className="text-muted-foreground">Current Password</label>
                        <input
                          type="password"
                          value={currentPassword}
                          onChange={(e) => setCurrentPassword(e.target.value)}
                          required
                          className="w-full p-2 bg-background border border-border rounded-lg text-foreground"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-muted-foreground">New Password</label>
                        <input
                          type="password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          required
                          className="w-full p-2 bg-background border border-border rounded-lg text-foreground"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-muted-foreground">Confirm New Password</label>
                        <input
                          type="password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          required
                          className="w-full p-2 bg-background border border-border rounded-lg text-foreground"
                        />
                      </div>
                      <div className="pt-1">
                        <button
                          type="submit"
                          disabled={loading}
                          className="px-3 py-1.5 bg-foreground text-background font-medium rounded-lg hover:opacity-90 transition"
                        >
                          {loading ? 'Updating...' : 'Change Password'}
                        </button>
                      </div>
                    </form>
                  </>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    Please sign in to manage account settings and clearance.
                  </div>
                )}
              </div>
            )}

            {/* About Tab */}
            {activeTab === 'about' && (
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-3 rounded-xl bg-muted/40 border border-border">
                  <img src="/educore.png" alt="Educore Logo" className="w-10 h-10 object-contain rounded" />
                  <div>
                    <h4 className="font-bold text-foreground text-sm">Educore Enterprise RAG</h4>
                    <p className="text-[11px] text-muted-foreground">Governed Institutional Intelligence Platform v1.0.0</p>
                  </div>
                </div>

                <div className="space-y-2 leading-relaxed text-muted-foreground">
                  <p>
                    Educore Enterprise RAG integrates multi-campus pedagogical guidance with strict ISO/IEC 42001 and ISO/IEC 27001 compliance standards.
                  </p>
                  <p>
                    All inference turns are monitored through the 6-Step Algorithmic Impact Assessment (AIIA) and logged to the statutory audit ledger (<code className="text-foreground">aims_rag_audit.jsonl</code>).
                  </p>
                </div>

                <div className="p-3 rounded-xl border border-border bg-card font-mono text-[10px] space-y-1 text-muted-foreground">
                  <div>Backend: Python 3.14 + Educore Pure-HTTP Engine</div>
                  <div>Store: SQLite <code>data/openwebui/webui.db</code> (Bcrypt Auth)</div>
                  <div>Vector Index: ChromaDB Multi-Shard Corpus</div>
                  <div>Purview: Multi-Campus Gating (Confidential, Internal, Public)</div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-border bg-muted/20 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-foreground text-background font-medium text-xs hover:opacity-90 transition"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
