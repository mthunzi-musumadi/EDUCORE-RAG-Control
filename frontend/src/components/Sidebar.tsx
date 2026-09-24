import React, { useState, useMemo, useRef, useEffect } from 'react';
import { 
  SquarePen, 
  Search, 
  MessageSquare, 
  Pin, 
  PinOff,
  Trash2, 
  Download, 
  PanelLeftClose, 
  Settings, 
  Cpu, 
  ShieldCheck, 
  LogOut, 
  LogIn, 
  ChevronUp,
  Layers,
  Sparkles,
  BookOpen
} from 'lucide-react';
import { ChatSession, User } from '../types';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  onUpdateSessionTitle: (id: string, newTitle: string) => void;
  onExportSession: (session: ChatSession) => void;
  onTogglePinSession?: (id: string) => void;
  currentUser: User | null;
  onOpenSettings: () => void;
  onOpenModelManagement: () => void;
  onOpenAdminPanel: () => void;
  onSignOut: () => void;
  onOpenAuthModal: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  onUpdateSessionTitle,
  onExportSession,
  onTogglePinSession,
  currentUser,
  onOpenSettings,
  onOpenModelManagement,
  onOpenAdminPanel,
  onSignOut,
  onOpenAuthModal,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  // Close profile popup when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(e.target as Node)) {
        setProfileMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter sessions by search
  const filteredSessions = useMemo(() => {
    if (!searchQuery.trim()) return sessions;
    const q = searchQuery.toLowerCase();
    return sessions.filter((s) => s.title.toLowerCase().includes(q));
  }, [sessions, searchQuery]);

  // Group sessions by date
  const groupedSessions = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

    const groups: { [key: string]: ChatSession[] } = {
      'Pinned': [],
      'Today': [],
      'Yesterday': [],
      'Previous 7 Days': [],
      'Previous 30 Days': [],
      'Older': [],
    };

    for (const session of filteredSessions) {
      if (session.pinned) {
        groups['Pinned'].push(session);
        continue;
      }
      const sDate = new Date(session.updatedAt);
      if (sDate >= today) {
        groups['Today'].push(session);
      } else if (sDate >= yesterday) {
        groups['Yesterday'].push(session);
      } else if (sDate >= sevenDaysAgo) {
        groups['Previous 7 Days'].push(session);
      } else if (sDate >= thirtyDaysAgo) {
        groups['Previous 30 Days'].push(session);
      } else {
        groups['Older'].push(session);
      }
    }

    return Object.entries(groups).filter(([_, list]) => list.length > 0);
  }, [filteredSessions]);

  const handleStartRename = (session: ChatSession) => {
    setEditingId(session.id);
    setEditTitle(session.title);
  };

  const handleSaveRename = (id: string) => {
    if (editTitle.trim()) {
      onUpdateSessionTitle(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const initials = currentUser?.name
    ? currentUser.name
        .split(' ')
        .map((n) => n[0])
        .slice(0, 2)
        .join('')
        .toUpperCase()
    : 'G';

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-30 w-64 sm:w-72 bg-sidebar border-r border-sidebar-border flex flex-col transition-transform duration-200 ease-in-out ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      {/* Top Header: Institutional Logo & Title */}
      <div className="h-14 px-4 flex items-center justify-between border-b border-sidebar-border">
        <div className="flex items-center gap-2.5">
          <img 
            src="/educore.png" 
            alt="Educore Logo" 
            className="w-7 h-7 object-contain rounded"
          />
          <div className="flex flex-col">
            <span className="text-sm font-semibold tracking-tight text-foreground leading-tight">
              Educore AI
            </span>
            <span className="text-[10px] text-muted-foreground font-medium">Enterprise Platform</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
          title="Close sidebar"
        >
          <PanelLeftClose size={18} />
        </button>
      </div>

      {/* Navigation: New Chat & Workspace Quick Link */}
      <div className="p-3 space-y-1.5">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-card hover:bg-muted border border-border text-foreground transition font-medium text-sm group"
        >
          <div className="flex items-center gap-2.5">
            <SquarePen size={16} className="text-muted-foreground group-hover:text-foreground transition-colors" />
            <span>New Chat</span>
          </div>
          <kbd className="hidden sm:inline-block text-[10px] px-1.5 py-0.5 rounded font-mono text-muted-foreground bg-background border border-border">
            Ctrl+O
          </kbd>
        </button>

        {/* Open WebUI 1:1 Workspace Navigation Item */}
        <button
          onClick={onOpenModelManagement}
          className="w-full flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/60 transition text-xs font-medium"
        >
          <Cpu size={15} />
          <span>Workspace (Models & Data)</span>
        </button>

        {/* Enterprise Admin Console Navigation Item */}
        <button
          onClick={onOpenAdminPanel}
          className="w-full flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 transition text-xs font-semibold"
        >
          <ShieldCheck size={15} className="shrink-0" />
          <span>Admin Console</span>
        </button>
      </div>

      {/* Search Input */}
      <div className="px-3 pb-2">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-2.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-background text-foreground text-xs placeholder:text-muted-foreground border border-border focus:outline-none focus:ring-1 focus:ring-foreground transition"
          />
        </div>
      </div>

      {/* Chat History List */}
      <div className="flex-1 overflow-y-auto px-2 space-y-4 py-2">
        {groupedSessions.length === 0 ? (
          <div className="text-center py-8 text-xs text-muted-foreground">
            {searchQuery ? 'No conversations found' : 'No chat history'}
          </div>
        ) : (
          groupedSessions.map(([groupName, groupList]) => (
            <div key={groupName} className="space-y-0.5">
              <div className="px-3 py-1 text-[11px] font-medium text-muted-foreground">
                {groupName}
              </div>
              {groupList.map((session) => {
                const isActive = session.id === activeSessionId;
                const isEditing = editingId === session.id;

                return (
                  <div
                    key={session.id}
                    onClick={() => onSelectSession(session.id)}
                    className={`group relative flex items-center justify-between px-3 py-2 rounded-xl text-xs cursor-pointer transition-colors ${
                      isActive
                        ? 'bg-muted text-foreground font-medium'
                        : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                    }`}
                  >
                    <div className="flex items-center gap-2 overflow-hidden flex-1 mr-1">
                      {session.pinned ? (
                        <Pin size={13} className="text-foreground shrink-0 fill-current" />
                      ) : (
                        <MessageSquare size={13} className="text-muted-foreground shrink-0" />
                      )}
                      
                      {isEditing ? (
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveRename(session.id);
                            if (e.key === 'Escape') setEditingId(null);
                          }}
                          onBlur={() => handleSaveRename(session.id)}
                          autoFocus
                          className="w-full bg-background text-foreground px-1.5 py-0.5 rounded border border-border focus:outline-none"
                          onClick={(e) => e.stopPropagation()}
                        />
                      ) : (
                        <span className="truncate">{session.title}</span>
                      )}
                    </div>

                    {!isEditing && (
                      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                        {/* Pin / Unpin button */}
                        {onTogglePinSession && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onTogglePinSession(session.id);
                            }}
                            className="p-1 hover:text-foreground hover:bg-background rounded"
                            title={session.pinned ? "Unpin chat" : "Pin chat"}
                          >
                            {session.pinned ? <PinOff size={12} /> : <Pin size={12} />}
                          </button>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartRename(session);
                          }}
                          className="p-1 hover:text-foreground hover:bg-background rounded"
                          title="Rename"
                        >
                          <SquarePen size={12} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onExportSession(session);
                          }}
                          className="p-1 hover:text-foreground hover:bg-background rounded"
                          title="Export as Markdown"
                        >
                          <Download size={12} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteSession(session.id);
                          }}
                          className="p-1 hover:text-red-500 hover:bg-background rounded"
                          title="Delete"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))
        )}
      </div>

      {/* Bottom User Profile Section with Open WebUI Dropdown */}
      <div className="p-3 border-t border-sidebar-border bg-sidebar relative" ref={profileMenuRef}>
        {/* Profile Dropdown Popup */}
        {profileMenuOpen && (
          <div className="absolute bottom-full left-3 right-3 mb-2 bg-card border border-border rounded-xl shadow-xl p-1.5 space-y-1 animate-in fade-in slide-in-from-bottom-2 duration-150 z-40">
            {currentUser && (
              <div className="px-3 py-2 border-b border-border mb-1">
                <p className="text-xs font-semibold text-foreground truncate">{currentUser.name}</p>
                <p className="text-[10px] text-muted-foreground truncate">{currentUser.email}</p>
                <div className="flex items-center gap-1.5 mt-1.5">
                  <span className="text-[9px] px-1.5 py-0.5 rounded uppercase font-semibold bg-muted border border-border">
                    {currentUser.clearance}
                  </span>
                  <span className="text-[9px] text-muted-foreground truncate">
                    {currentUser.campus}
                  </span>
                </div>
              </div>
            )}

            <button
              onClick={() => {
                setProfileMenuOpen(false);
                onOpenModelManagement();
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-foreground hover:bg-muted transition text-left"
            >
              <Cpu size={14} className="text-muted-foreground" />
              <span>Workspace / Models</span>
            </button>

            <button
              onClick={() => {
                setProfileMenuOpen(false);
                onOpenAdminPanel();
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-foreground hover:bg-muted transition text-left"
            >
              <ShieldCheck size={14} className="text-emerald-500" />
              <span className="font-medium">Admin Console</span>
            </button>

            <button
              onClick={() => {
                setProfileMenuOpen(false);
                onOpenSettings();
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-foreground hover:bg-muted transition text-left"
            >
              <Settings size={14} className="text-muted-foreground" />
              <span>Settings</span>
            </button>

            <hr className="border-border my-1" />

            {currentUser ? (
              <button
                onClick={() => {
                  setProfileMenuOpen(false);
                  onSignOut();
                }}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-red-500 hover:bg-red-500/10 transition text-left"
              >
                <LogOut size={14} />
                <span>Sign Out</span>
              </button>
            ) : (
              <button
                onClick={() => {
                  setProfileMenuOpen(false);
                  onOpenAuthModal();
                }}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs text-foreground hover:bg-muted transition text-left"
              >
                <LogIn size={14} />
                <span>Sign In / Register</span>
              </button>
            )}
          </div>
        )}

        {/* Profile Card Button */}
        <button
          onClick={() => setProfileMenuOpen(!profileMenuOpen)}
          className="w-full flex items-center justify-between p-2 rounded-xl hover:bg-muted transition text-left group"
        >
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-full bg-muted border border-border flex items-center justify-center font-bold text-xs text-foreground shrink-0">
              {initials}
            </div>
            <div className="flex flex-col overflow-hidden">
              <span className="text-xs font-semibold text-foreground truncate">
                {currentUser?.name || 'Guest User'}
              </span>
              <span className="text-[10px] text-muted-foreground truncate">
                {currentUser?.email || 'Public Clearance'}
              </span>
            </div>
          </div>
          <ChevronUp size={14} className={`text-muted-foreground group-hover:text-foreground transition-transform ${profileMenuOpen ? 'rotate-180' : ''}`} />
        </button>
      </div>
    </aside>
  );
};
