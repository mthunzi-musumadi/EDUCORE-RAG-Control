import React from 'react';
import { 
  PanelLeftClose, 
  PanelLeftOpen, 
  SquarePen, 
  ChevronDown, 
  Activity, 
  Sun, 
  Moon, 
  ShieldCheck, 
  Sliders,
  Share2
} from 'lucide-react';
import { EducoreModel, User } from '../types';

interface HeaderProps {
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  onNewChat: () => void;
  activeModel: EducoreModel;
  onOpenModelSelector: () => void;
  currentUser: User | null;
  onOpenAuthModal: () => void;
  onOpenSettings: () => void;
  onToggleTelemetry: () => void;
  telemetryOpen: boolean;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
  onOpenChatControls: () => void;
  onOpenShare: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  sidebarOpen,
  onToggleSidebar,
  onNewChat,
  activeModel,
  onOpenModelSelector,
  currentUser,
  onOpenAuthModal,
  onOpenSettings,
  onToggleTelemetry,
  telemetryOpen,
  theme,
  onToggleTheme,
  onOpenChatControls,
  onOpenShare,
}) => {
  return (
    <header className="h-14 border-b border-border px-3 sm:px-4 flex items-center justify-between bg-card z-20 transition-colors">
      {/* Left: Sidebar Toggle, New Chat & Model Selector */}
      <div className="flex items-center gap-2">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
          title={sidebarOpen ? "Close sidebar" : "Open sidebar"}
          aria-label="Toggle sidebar"
        >
          {sidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
        </button>

        {!sidebarOpen && (
          <button
            onClick={onNewChat}
            className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
            title="New Chat (Ctrl+O)"
            aria-label="New chat"
          >
            <SquarePen size={18} />
          </button>
        )}

        {/* Model Selector Button (Open WebUI / ChatGPT style) */}
        <button
          onClick={onOpenModelSelector}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl hover:bg-muted border border-border/80 transition text-sm font-medium text-foreground group"
        >
          <span className="font-semibold tracking-tight truncate max-w-[130px] sm:max-w-[220px]">
            {activeModel.name}
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-muted text-foreground border border-border uppercase font-semibold">
            {activeModel.requiredTier || activeModel.clearanceLevel || 'public'}
          </span>
          <ChevronDown size={14} className="text-muted-foreground group-hover:text-foreground transition-colors" />
        </button>
      </div>

      {/* Right: Chat Controls, Share, User Badge, Telemetry & Theme */}
      <div className="flex items-center gap-1 sm:gap-1.5">
        {/* Chat Controls (Parameters) Button (Open WebUI 1:1) */}
        <button
          onClick={onOpenChatControls}
          className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
          title="Chat Controls (System Prompt, Temperature, RAG)"
          aria-label="Chat controls"
        >
          <Sliders size={17} />
        </button>

        {/* Share Button (Open WebUI 1:1) */}
        <button
          onClick={onOpenShare}
          className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
          title="Share or Export Conversation"
          aria-label="Share conversation"
        >
          <Share2 size={17} />
        </button>

        {/* User Session Badge */}
        {currentUser ? (
          <button
            onClick={onOpenSettings}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-foreground hover:bg-muted border border-border transition"
            title="Account Settings & Clearance"
          >
            <ShieldCheck size={14} className="text-foreground" />
            <span className="hidden sm:inline font-semibold uppercase">{currentUser.clearance}</span>
            <span className="hidden md:inline text-muted-foreground">({currentUser.campus})</span>
          </button>
        ) : (
          <button
            onClick={onOpenAuthModal}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-foreground text-background hover:opacity-90 transition"
          >
            Sign In
          </button>
        )}

        {/* Telemetry Inspector Button */}
        <button
          onClick={onToggleTelemetry}
          className={`p-2 rounded-lg transition ${
            telemetryOpen 
              ? 'text-foreground bg-muted border border-border' 
              : 'text-muted-foreground hover:text-foreground hover:bg-muted'
          }`}
          title="ISO 42001 Live Telemetry & Audit Inspector"
          aria-label="Toggle telemetry"
        >
          <Activity size={17} />
        </button>

        {/* Theme Toggle Button */}
        <button
          onClick={onToggleTheme}
          className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
          title={theme === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
        </button>
      </div>
    </header>
  );
};
