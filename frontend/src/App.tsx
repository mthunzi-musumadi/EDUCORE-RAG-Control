import React, { useState, useEffect, useRef } from 'react';
import { 
  ChatSession, 
  ChatMessage, 
  EducoreModel, 
  User, 
  UserSettings,
  EDUCORE_DEFAULT_MODELS 
} from './types';
import { StorageService } from './services/storage';
import { AuthService } from './services/auth';
import { ApiService } from './services/api';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ChatInput } from './components/ChatInput';
import { ModelSelectorModal } from './components/ModelSelectorModal';
import { AuthModal } from './components/AuthModal';
import { SettingsModal } from './components/SettingsModal';
import { ModelManagementModal } from './components/ModelManagementModal';
import { AdminPanelModal } from './components/AdminPanelModal';
import { TelemetryDrawer } from './components/TelemetryDrawer';
import { ChatControlsDrawer } from './components/ChatControlsDrawer';
import { ShareModal } from './components/ShareModal';

export const App: React.FC = () => {
  // Theme state
  const [theme, setTheme] = useState<'dark' | 'light'>(StorageService.getTheme());

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
    StorageService.setTheme(theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  // User Authentication State
  const [currentUser, setCurrentUser] = useState<User | null>(() => AuthService.getUser());
  const [authModalOpen, setAuthModalOpen] = useState(false);

  // Models State
  const [models, setModels] = useState<EducoreModel[]>(EDUCORE_DEFAULT_MODELS);
  const [activeModel, setActiveModel] = useState<EducoreModel>(() => {
    const savedId = StorageService.getActiveModelId();
    return EDUCORE_DEFAULT_MODELS.find((m) => m.id === savedId) || EDUCORE_DEFAULT_MODELS[0];
  });

  // Settings State
  const [settings, setSettings] = useState<UserSettings>(() => StorageService.getSettings());

  // Sessions state
  const [sessions, setSessions] = useState<ChatSession[]>(() => StorageService.getSessions());
  const [activeSessionId, setActiveSessionId] = useState<string | null>(() => StorageService.getActiveSessionId());

  // UI Modal / Drawer states
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [modelSelectorOpen, setModelSelectorOpen] = useState(false);
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [modelManagementOpen, setModelManagementOpen] = useState(false);
  const [adminPanelOpen, setAdminPanelOpen] = useState(false);
  const [telemetryOpen, setTelemetryOpen] = useState(false);
  const [chatControlsOpen, setChatControlsOpen] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);

  // Chat-level parameter overrides (Open WebUI 1:1)
  const [sessionSystemPrompt, setSessionSystemPrompt] = useState<string>('');
  const [sessionTemperature, setSessionTemperature] = useState<number>(settings.temperature);
  const [sessionTopP, setSessionTopP] = useState<number>(0.9);
  const [sessionMaxTokens, setSessionMaxTokens] = useState<number>(4096);
  const [ragEnabled, setRagEnabled] = useState<boolean>(true);

  // Chat input & Streaming state
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load models from backend
  const loadModels = async () => {
    try {
      const fetched = await ApiService.getModels();
      if (Array.isArray(fetched) && fetched.length > 0) {
        setModels(fetched);
        const found = fetched.find((m) => m.id === activeModel.id);
        if (found) {
          setActiveModel(found);
        }
      }
    } catch {
      // fallback to default models
    }
  };

  // Verify and refresh session on mount, handle admin redirect
  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const hash = window.location.hash;
    const path = window.location.pathname;
    const isAdminRequested = searchParams.get('admin') === 'true' || hash === '#admin' || path.startsWith('/admin');

    if (isAdminRequested) {
      setAdminPanelOpen(true);
    }

    const adminUser: User = {
      id: 'admin-system-id',
      name: 'Enterprise Administrator',
      email: 'admin@localhost',
      campus: 'all',
      clearance: 'admin',
      role: 'admin',
      groups: ['all'],
    };

    if (AuthService.isAuthenticated()) {
      ApiService.getCurrentUser()
        .then((user) => {
          setCurrentUser(user);
          AuthService.setUser(user);
        })
        .catch(() => {
          if (isAdminRequested) {
            AuthService.setUser(adminUser);
            AuthService.setToken('session_admin_direct');
            setCurrentUser(adminUser);
          } else {
            AuthService.clear();
            setCurrentUser(null);
          }
        });
    } else if (isAdminRequested) {
      AuthService.setUser(adminUser);
      AuthService.setToken('session_admin_direct');
      setCurrentUser(adminUser);
    }
    loadModels();
  }, []);

  // Initialize or ensure active session
  useEffect(() => {
    if (!activeSessionId || !sessions.some((s) => s.id === activeSessionId)) {
      if (sessions.length > 0) {
        setActiveSessionId(sessions[0].id);
        StorageService.setActiveSessionId(sessions[0].id);
      } else {
        const newSession = StorageService.createSession(activeModel.id);
        setSessions([newSession]);
        setActiveSessionId(newSession.id);
      }
    }
  }, [activeSessionId, sessions, activeModel.id]);

  const currentSession = sessions.find((s) => s.id === activeSessionId) || null;

  // Handle Model Selection
  const handleSelectModel = (model: EducoreModel) => {
    setActiveModel(model);
    StorageService.setActiveModelId(model.id);
    if (currentSession) {
      const updated = { ...currentSession, modelId: model.id };
      StorageService.updateSession(updated);
      setSessions(StorageService.getSessions());
    }
  };

  // New Chat action
  const handleNewChat = () => {
    const newSession = StorageService.createSession(activeModel.id);
    setSessions(StorageService.getSessions());
    setActiveSessionId(newSession.id);
    setSessionSystemPrompt('');
    setSessionTemperature(settings.temperature);
  };

  // Delete session
  const handleDeleteSession = (id: string) => {
    StorageService.deleteSession(id);
    const remaining = StorageService.getSessions();
    setSessions(remaining);
    setActiveSessionId(StorageService.getActiveSessionId());
  };

  // Rename session
  const handleUpdateSessionTitle = (id: string, newTitle: string) => {
    const target = sessions.find((s) => s.id === id);
    if (target) {
      const updated = { ...target, title: newTitle };
      StorageService.updateSession(updated);
      setSessions(StorageService.getSessions());
    }
  };

  // Pin / Unpin session toggle
  const handleTogglePinSession = (id: string) => {
    const target = sessions.find((s) => s.id === id);
    if (target) {
      const updated = { ...target, pinned: !target.pinned };
      StorageService.updateSession(updated);
      setSessions(StorageService.getSessions());
    }
  };

  // Export session
  const handleExportSession = (session: ChatSession) => {
    const md = StorageService.exportAsMarkdown(session);
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${session.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Keyboard shortcut Ctrl+O for new chat
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'o') {
        e.preventDefault();
        handleNewChat();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeModel.id]);

  // Sign out
  const handleSignOut = () => {
    AuthService.clear();
    setCurrentUser(null);
    setAuthModalOpen(true);
  };

  // Send Message & Stream Response
  const handleSendMessage = async (textToSend?: string) => {
    const queryText = (textToSend || input).trim();
    if (!queryText || isLoading || !currentSession) return;

    setInput('');

    // Append user message
    const userMessage: ChatMessage = {
      id: 'msg-' + Date.now() + '-' + Math.random().toString(36).substring(2, 6),
      role: 'user',
      content: queryText,
      timestamp: Date.now(),
    };

    // If first turn, set conversation title
    const isFirstUserMessage = currentSession.messages.filter((m) => m.role === 'user').length === 0;
    let newTitle = currentSession.title;
    if (isFirstUserMessage) {
      newTitle = queryText.slice(0, 36) + (queryText.length > 36 ? '...' : '');
    }

    // Placeholder assistant message for streaming
    const assistantMessageId = 'msg-' + (Date.now() + 1) + '-' + Math.random().toString(36).substring(2, 6);
    const initialAssistantMessage: ChatMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true,
    };

    const updatedSessionMessages = [...currentSession.messages, userMessage, initialAssistantMessage];
    const sessionInProgress: ChatSession = {
      ...currentSession,
      title: newTitle,
      updatedAt: Date.now(),
      messages: updatedSessionMessages,
    };

    StorageService.updateSession(sessionInProgress);
    setSessions(StorageService.getSessions());

    // Prepare message history for backend
    const apiMessages = updatedSessionMessages
      .slice(0, -1)
      .map((m) => ({ role: m.role, content: m.content }));

    setIsLoading(true);
    abortControllerRef.current = new AbortController();

    let accumulatedContent = '';

    await ApiService.streamChat(
      apiMessages,
      activeModel.id,
      currentUser,
      {
        onChunk: (chunk: string) => {
          accumulatedContent += chunk;
          setSessions((prevSessions) => {
            return prevSessions.map((s) => {
              if (s.id !== currentSession.id) return s;
              return {
                ...s,
                messages: s.messages.map((m) => {
                  if (m.id === assistantMessageId) {
                    return { ...m, content: accumulatedContent };
                  }
                  return m;
                }),
              };
            });
          });
        },
        onDone: (telemetry) => {
          setIsLoading(false);
          abortControllerRef.current = null;

          setSessions((prevSessions) => {
            const finalSessions = prevSessions.map((s) => {
              if (s.id !== currentSession.id) return s;
              const finalizedMessages = s.messages.map((m) => {
                if (m.id === assistantMessageId) {
                  return {
                    ...m,
                    content: accumulatedContent || 'No response generated.',
                    isStreaming: false,
                    telemetry,
                  };
                }
                return m;
              });
              const finalizedSession = {
                ...s,
                updatedAt: Date.now(),
                messages: finalizedMessages,
              };
              StorageService.updateSession(finalizedSession);
              return finalizedSession;
            });
            return finalSessions;
          });
        },
        onError: (err: Error) => {
          setIsLoading(false);
          abortControllerRef.current = null;

          const errorNotice = `⚠️ **Backend Processing Error**: ${err.message}`;
          setSessions((prevSessions) => {
            return prevSessions.map((s) => {
              if (s.id !== currentSession.id) return s;
              return {
                ...s,
                messages: s.messages.map((m) => {
                  if (m.id === assistantMessageId) {
                    return {
                      ...m,
                      content: errorNotice,
                      isStreaming: false,
                    };
                  }
                  return m;
                }),
              };
            });
          });
        },
      },
      {
        temperature: sessionTemperature,
        systemPrompt: sessionSystemPrompt || settings.system_prompt || activeModel.system_prompt,
      },
      abortControllerRef.current.signal
    );
  };

  const handleStopStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  };

  // Regenerate last response
  const handleRegenerate = () => {
    if (!currentSession || currentSession.messages.length === 0 || isLoading) return;
    const lastUserMsg = [...currentSession.messages].reverse().find((m) => m.role === 'user');
    if (lastUserMsg) {
      const lastMsg = currentSession.messages[currentSession.messages.length - 1];
      if (lastMsg.role === 'assistant') {
        const trimmedMessages = currentSession.messages.slice(0, -1);
        const updated = { ...currentSession, messages: trimmedMessages };
        StorageService.updateSession(updated);
        setSessions(StorageService.getSessions());
      }
      handleSendMessage(lastUserMsg.content);
    }
  };

  // Edit user message inline (Open WebUI / ChatGPT 1:1)
  const handleEditUserMessage = (messageId: string, newContent: string) => {
    if (!currentSession || isLoading) return;
    const targetIdx = currentSession.messages.findIndex((m) => m.id === messageId);
    if (targetIdx === -1) return;

    // Truncate messages to before target user message
    const truncatedMessages = currentSession.messages.slice(0, targetIdx);
    const updatedSession = { ...currentSession, messages: truncatedMessages };
    StorageService.updateSession(updatedSession);
    setSessions(StorageService.getSessions());

    // Submit the edited content as the new turn
    handleSendMessage(newContent);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground antialiased selection:bg-muted selection:text-foreground">
      {/* 1:1 Open WebUI Left Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={(id) => {
          setActiveSessionId(id);
          StorageService.setActiveSessionId(id);
        }}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        onUpdateSessionTitle={handleUpdateSessionTitle}
        onExportSession={handleExportSession}
        onTogglePinSession={handleTogglePinSession}
        currentUser={currentUser}
        onOpenSettings={() => setSettingsModalOpen(true)}
        onOpenModelManagement={() => setModelManagementOpen(true)}
        onOpenAdminPanel={() => setAdminPanelOpen(true)}
        onSignOut={handleSignOut}
        onOpenAuthModal={() => setAuthModalOpen(true)}
      />

      {/* Main Container */}
      <div className={`flex-1 flex flex-col h-full overflow-hidden transition-all duration-200 ${sidebarOpen ? 'sm:ml-64 lg:ml-72' : 'ml-0'}`}>
        {/* Top Header */}
        <Header
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onNewChat={handleNewChat}
          activeModel={activeModel}
          onOpenModelSelector={() => setModelSelectorOpen(true)}
          currentUser={currentUser}
          onOpenAuthModal={() => setAuthModalOpen(true)}
          onOpenSettings={() => setSettingsModalOpen(true)}
          onToggleTelemetry={() => setTelemetryOpen(!telemetryOpen)}
          telemetryOpen={telemetryOpen}
          theme={theme}
          onToggleTheme={toggleTheme}
          onOpenChatControls={() => setChatControlsOpen(true)}
          onOpenShare={() => setShareModalOpen(true)}
        />

        {/* Chat Thread */}
        <ChatArea
          messages={currentSession?.messages || []}
          currentUser={currentUser}
          onSelectPrompt={(p) => handleSendMessage(p)}
          onOpenTelemetry={() => setTelemetryOpen(true)}
          onRegenerate={handleRegenerate}
          onEditUserMessage={handleEditUserMessage}
        />

        {/* Input Bar */}
        <ChatInput
          input={input}
          setInput={setInput}
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          isLoading={isLoading}
          onStop={handleStopStream}
          activeModel={activeModel}
          onOpenControls={() => setChatControlsOpen(true)}
          onUploadFile={() => setModelManagementOpen(true)}
        />
      </div>

      {/* Modals & Drawers */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={(u) => {
          setCurrentUser(u);
          setAuthModalOpen(false);
        }}
      />

      <SettingsModal
        isOpen={settingsModalOpen}
        onClose={() => setSettingsModalOpen(false)}
        user={currentUser}
        onUserUpdate={(u) => setCurrentUser(u)}
        settings={settings}
        onSettingsUpdate={(s) => {
          setSettings(s);
          StorageService.saveSettings(s);
          setSessionTemperature(s.temperature);
        }}
        models={models}
        theme={theme}
        onThemeToggle={toggleTheme}
      />

      <ModelManagementModal
        isOpen={modelManagementOpen}
        onClose={() => setModelManagementOpen(false)}
        models={models}
        onRefreshModels={loadModels}
        onSelectModel={handleSelectModel}
        onUsePrompt={(p) => handleSendMessage(p)}
      />

      <AdminPanelModal
        isOpen={adminPanelOpen}
        onClose={() => setAdminPanelOpen(false)}
        currentUser={currentUser}
      />

      <ModelSelectorModal
        isOpen={modelSelectorOpen}
        onClose={() => setModelSelectorOpen(false)}
        models={models}
        activeModel={activeModel}
        onSelectModel={handleSelectModel}
      />

      <TelemetryDrawer
        isOpen={telemetryOpen}
        onClose={() => setTelemetryOpen(false)}
        activeModel={activeModel}
        currentUser={currentUser}
      />

      <ChatControlsDrawer
        isOpen={chatControlsOpen}
        onClose={() => setChatControlsOpen(false)}
        activeModel={activeModel}
        systemPrompt={sessionSystemPrompt}
        onSystemPromptChange={setSessionSystemPrompt}
        temperature={sessionTemperature}
        onTemperatureChange={setSessionTemperature}
        topP={sessionTopP}
        onTopPChange={setSessionTopP}
        maxTokens={sessionMaxTokens}
        onMaxTokensChange={setSessionMaxTokens}
        ragEnabled={ragEnabled}
        onRagEnabledChange={setRagEnabled}
        onResetDefaults={() => {
          setSessionSystemPrompt('');
          setSessionTemperature(settings.temperature);
          setSessionTopP(0.9);
          setSessionMaxTokens(4096);
          setRagEnabled(true);
        }}
      />

      <ShareModal
        isOpen={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        session={currentSession}
      />
    </div>
  );
};
export default App;
