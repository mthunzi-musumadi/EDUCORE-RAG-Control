import React from 'react';
import { X, Check, Shield, Search } from 'lucide-react';
import { EducoreModel } from '../types';

interface ModelSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  models: EducoreModel[];
  activeModel: EducoreModel;
  onSelectModel: (model: EducoreModel) => void;
}

export const ModelSelectorModal: React.FC<ModelSelectorModalProps> = ({
  isOpen,
  onClose,
  models,
  activeModel,
  onSelectModel,
}) => {
  const [search, setSearch] = React.useState('');

  if (!isOpen) return null;

  const filtered = models.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    m.id.toLowerCase().includes(search.toLowerCase()) ||
    (m.description && m.description.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-card border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="px-5 py-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield size={18} className="text-foreground" />
            <h2 className="text-sm font-semibold text-foreground">
              Select Educore AI Model
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
          >
            <X size={16} />
          </button>
        </div>

        {/* Search Input */}
        <div className="p-3 border-b border-border">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search available models..."
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-foreground transition"
            />
          </div>
        </div>

        {/* Model List */}
        <div className="p-3 overflow-y-auto space-y-2 flex-1">
          {filtered.map((model) => {
            const isSelected = model.id === activeModel.id;

            return (
              <button
                key={model.id}
                onClick={() => {
                  onSelectModel(model);
                  onClose();
                }}
                className={`w-full flex items-start justify-between p-3.5 rounded-xl border text-left transition-all ${
                  isSelected
                    ? 'bg-muted border-foreground/30 text-foreground shadow-sm'
                    : 'bg-card hover:bg-muted/40 border-border text-foreground'
                }`}
              >
                <div className="flex-1 pr-3">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="font-semibold text-xs text-foreground">
                      {model.name}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-muted text-foreground border border-border uppercase font-semibold">
                      {model.requiredTier || model.clearanceLevel || 'public'}
                    </span>
                    {model.is_custom && (
                      <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-foreground text-background">
                        Custom
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-muted-foreground leading-snug">
                    {model.description || 'Institutional governed model preset.'}
                  </p>
                  {model.targetUser && (
                    <div className="text-[10px] text-muted-foreground mt-1.5">
                      Target: {model.targetUser}
                    </div>
                  )}
                </div>

                {isSelected && (
                  <div className="w-5 h-5 rounded-full bg-foreground text-background flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Check size={12} strokeWidth={3} />
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-border text-[11px] text-muted-foreground text-center bg-muted/20">
          Governed by Educore AI Framework (EDU-AIMS-HBK-v1.0 & ISO/IEC 42001)
        </div>
      </div>
    </div>
  );
};
