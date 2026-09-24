import React from 'react';
import { X, Sliders, RotateCcw, Zap, Sparkles, BookOpen, Shield } from 'lucide-react';
import { EducoreModel } from '../types';

interface ChatControlsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeModel: EducoreModel;
  systemPrompt: string;
  onSystemPromptChange: (val: string) => void;
  temperature: number;
  onTemperatureChange: (val: number) => void;
  topP: number;
  onTopPChange: (val: number) => void;
  maxTokens: number;
  onMaxTokensChange: (val: number) => void;
  ragEnabled: boolean;
  onRagEnabledChange: (val: boolean) => void;
  onResetDefaults: () => void;
}

export const ChatControlsDrawer: React.FC<ChatControlsDrawerProps> = ({
  isOpen,
  onClose,
  activeModel,
  systemPrompt,
  onSystemPromptChange,
  temperature,
  onTemperatureChange,
  topP,
  onTopPChange,
  maxTokens,
  onMaxTokensChange,
  ragEnabled,
  onRagEnabledChange,
  onResetDefaults,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50 backdrop-blur-xs transition-opacity animate-in fade-in duration-200">
      <div 
        className="w-full max-w-sm sm:max-w-md h-full bg-card border-l border-border flex flex-col shadow-2xl animate-in slide-in-from-right duration-200"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-foreground" />
            <h3 className="text-sm font-semibold text-foreground">Chat Controls</h3>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={onResetDefaults}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
              title="Reset to default parameters"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6 text-xs text-foreground">
          {/* Active Model Pill */}
          <div className="p-3 rounded-xl bg-muted/60 border border-border flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-[10px] uppercase font-mono text-muted-foreground font-semibold">Active Model</span>
              <span className="font-semibold text-xs text-foreground">{activeModel.name}</span>
            </div>
            <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-background border border-border">
              {activeModel.requiredTier || 'public'}
            </span>
          </div>

          {/* RAG Retrieval Toggle */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-foreground" />
                <label className="font-semibold text-xs text-foreground">RAG Vector Retrieval</label>
              </div>
              <input
                type="checkbox"
                checked={ragEnabled}
                onChange={(e) => onRagEnabledChange(e.target.checked)}
                className="w-4 h-4 accent-foreground cursor-pointer rounded"
              />
            </div>
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              When enabled, queries are enriched with ChromaDB institutional embeddings under ISO/IEC 42001 purview boundaries.
            </p>
          </div>

          <hr className="border-border" />

          {/* System Prompt Override */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="font-semibold text-xs text-foreground">System Prompt Override</label>
              <span className="text-[10px] text-muted-foreground font-mono">Chat-Specific</span>
            </div>
            <textarea
              value={systemPrompt}
              onChange={(e) => onSystemPromptChange(e.target.value)}
              placeholder={activeModel.system_prompt || "Custom instructions for this conversation..."}
              rows={4}
              className="w-full p-2.5 rounded-xl bg-background border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-foreground transition text-xs font-mono resize-y"
            />
            <p className="text-[11px] text-muted-foreground">
              Overrides the baseline system instruction for this chat session.
            </p>
          </div>

          <hr className="border-border" />

          {/* Temperature Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="font-semibold text-xs text-foreground">Temperature</label>
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-muted border border-border">
                {temperature.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1.5"
              step="0.05"
              value={temperature}
              onChange={(e) => onTemperatureChange(parseFloat(e.target.value))}
              className="w-full accent-foreground cursor-pointer h-1.5 bg-muted rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
              <span>0.0 (Precise / Factual)</span>
              <span>1.5 (Creative)</span>
            </div>
          </div>

          {/* Top-P Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="font-semibold text-xs text-foreground">Top-P (Nucleus Sampling)</label>
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-muted border border-border">
                {topP.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1"
              step="0.05"
              value={topP}
              onChange={(e) => onTopPChange(parseFloat(e.target.value))}
              className="w-full accent-foreground cursor-pointer h-1.5 bg-muted rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
              <span>0.1 (Focused)</span>
              <span>1.0 (Diverse)</span>
            </div>
          </div>

          {/* Max Tokens */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="font-semibold text-xs text-foreground">Max Output Tokens</label>
              <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-muted border border-border">
                {maxTokens}
              </span>
            </div>
            <input
              type="range"
              min="256"
              max="8192"
              step="256"
              value={maxTokens}
              onChange={(e) => onMaxTokensChange(parseInt(e.target.value, 10))}
              className="w-full accent-foreground cursor-pointer h-1.5 bg-muted rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-muted-foreground font-mono">
              <span>256</span>
              <span>8192</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border bg-muted/20 flex items-center justify-between">
          <span className="text-[11px] text-muted-foreground">Changes apply immediately</span>
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
