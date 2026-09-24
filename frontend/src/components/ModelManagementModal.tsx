import React, { useState, useEffect } from 'react';
import { EducoreModel, ClearanceTier, SystemStatus } from '../types';
import { ApiService } from '../services/api';
import { 
  X, 
  Cpu, 
  Plus, 
  Trash2, 
  Edit3, 
  Search, 
  Shield, 
  Check, 
  AlertCircle,
  Sliders,
  Sparkles,
  BookOpen,
  FileText,
  RefreshCw,
  MessageSquare,
  Play
} from 'lucide-react';

interface ModelManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
  models: EducoreModel[];
  onRefreshModels: () => void;
  onSelectModel: (model: EducoreModel) => void;
  onUsePrompt?: (promptText: string) => void;
}

export const ModelManagementModal: React.FC<ModelManagementModalProps> = ({
  isOpen,
  onClose,
  models,
  onRefreshModels,
  onSelectModel,
  onUsePrompt,
}) => {
  const [activeTab, setActiveTab] = useState<'models' | 'knowledge' | 'prompts'>('models');
  const [search, setSearch] = useState('');
  const [editingModel, setEditingModel] = useState<Partial<EducoreModel> | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [frameworkStatus, setFrameworkStatus] = useState<SystemStatus | null>(null);

  // Form states for Create/Edit
  const [formId, setFormId] = useState('');
  const [formName, setFormName] = useState('');
  const [formBase, setFormBase] = useState('educore-enterprise-all');
  const [formDesc, setFormDesc] = useState('');
  const [formPrompt, setFormPrompt] = useState('');
  const [formTemp, setFormTemp] = useState(0.7);
  const [formTier, setFormTier] = useState<ClearanceTier>('public');

  // Load framework status when switching to knowledge tab
  useEffect(() => {
    if (isOpen && activeTab === 'knowledge') {
      ApiService.getFrameworkStatus()
        .then(setFrameworkStatus)
        .catch(console.error);
    }
  }, [isOpen, activeTab]);

  if (!isOpen) return null;

  const startCreate = () => {
    setIsCreating(true);
    setEditingModel(null);
    setFormId(`custom-model-${Date.now().toString().slice(-4)}`);
    setFormName('');
    setFormBase('educore-enterprise-all');
    setFormDesc('');
    setFormPrompt('');
    setFormTemp(0.7);
    setFormTier('public');
  };

  const startEdit = (m: EducoreModel) => {
    setIsCreating(false);
    setEditingModel(m);
    setFormId(m.id);
    setFormName(m.name);
    setFormBase(m.base_model_id || 'educore-enterprise-all');
    setFormDesc(m.description || '');
    setFormPrompt(m.system_prompt || '');
    setFormTemp(m.temperature || 0.7);
    setFormTier(m.requiredTier || 'public');
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatusMsg(null);
    try {
      const payload: Partial<EducoreModel> = {
        id: formId.trim().toLowerCase().replace(/\s+/g, '-'),
        name: formName.trim(),
        base_model_id: formBase,
        description: formDesc.trim(),
        system_prompt: formPrompt.trim(),
        temperature: formTemp,
        requiredTier: formTier,
      };

      if (isCreating) {
        await ApiService.createModel(payload);
        setStatusMsg({ text: `Model "${payload.name}" created successfully.`, type: 'success' });
      } else {
        await ApiService.updateModel(payload);
        setStatusMsg({ text: `Model "${payload.name}" updated successfully.`, type: 'success' });
      }

      onRefreshModels();
      setIsCreating(false);
      setEditingModel(null);
    } catch (err: any) {
      setStatusMsg({ text: err.message || 'Failed to save model.', type: 'error' });
    } finally {
      setLoading(false);
      setTimeout(() => setStatusMsg(null), 3000);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete the model "${name}"?`)) return;
    setLoading(true);
    try {
      await ApiService.deleteModel(id);
      setStatusMsg({ text: `Model "${name}" deleted.`, type: 'success' });
      onRefreshModels();
    } catch (err: any) {
      setStatusMsg({ text: err.message || 'Failed to delete model.', type: 'error' });
    } finally {
      setLoading(false);
      setTimeout(() => setStatusMsg(null), 3000);
    }
  };

  const handleTriggerSync = async () => {
    setSyncing(true);
    setStatusMsg(null);
    try {
      const res = await ApiService.syncFramework(true);
      setStatusMsg({ 
        text: `Knowledge sync completed: ${res.indexed_files || 0} files indexed (${res.total_chunks || 0} chunks).`, 
        type: 'success' 
      });
      const s = await ApiService.getFrameworkStatus();
      setFrameworkStatus(s);
    } catch (err: any) {
      setStatusMsg({ text: err.message || 'Sync failed.', type: 'error' });
    } finally {
      setSyncing(false);
      setTimeout(() => setStatusMsg(null), 4000);
    }
  };

  const institutionalPrompts = [
    {
      title: 'Cambridge IGCSE Math Guide',
      category: 'Academic',
      prompt: 'Can you guide me step-by-step through solving quadratic equations by completing the square under Cambridge IGCSE Mathematics 0580?',
      desc: 'Syllabus-aligned pedagogy for algebraic factorization and graph sketches.'
    },
    {
      title: 'Diagnostic Stoichiometry Hint',
      category: 'Science',
      prompt: 'I am solving a chemistry stoichiometry problem with limiting reagents and gas volume at RTP. Please provide a Socratic diagnostic hint rather than the final answer.',
      desc: 'Guided diagnostic feedback encouraging student problem-solving.'
    },
    {
      title: 'ISO 42001 AIIA Assessment',
      category: 'Governance',
      prompt: 'What are the mandatory statutory compliance requirements for the 6-Step Algorithmic Impact Assessment under the Educore AI Framework (EDU-AIMS-HBK-v1.0)?',
      desc: 'Governance audit check for high-risk educational AI systems.'
    },
    {
      title: 'Dual-Key Financial Variance Audit',
      category: 'Finance',
      prompt: 'Summarize the bursary variance expenditure and dual-key manual verification notice rules under Guardrail Fin-01.',
      desc: 'Clearance verification rules for bursary disbursement discrepancies.'
    }
  ];

  const filteredModels = models.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    m.id.toLowerCase().includes(search.toLowerCase()) ||
    (m.description && m.description.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-150">
      <div className="w-full max-w-3xl bg-card border border-border rounded-2xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-2.5">
            <Cpu className="h-5 w-5 text-foreground" />
            <div>
              <h3 className="font-semibold text-base text-foreground">Workspace</h3>
              <p className="text-[11px] text-muted-foreground">Manage Models, Knowledge Bases, and Prompt Presets</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {activeTab === 'models' && !isCreating && !editingModel && (
              <button
                onClick={startCreate}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-foreground text-background text-xs font-medium rounded-lg hover:opacity-90 transition"
              >
                <Plus className="h-3.5 w-3.5" />
                Create Model
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Workspace Navigation Tabs (Open WebUI 1:1) */}
        <div className="flex border-b border-border px-6 bg-muted/20">
          <button
            onClick={() => setActiveTab('models')}
            className={`flex items-center gap-2 py-3 px-3 border-b-2 text-xs font-medium transition ${
              activeTab === 'models'
                ? 'border-foreground text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Cpu className="w-4 h-4" />
            <span>Models ({models.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('knowledge')}
            className={`flex items-center gap-2 py-3 px-3 border-b-2 text-xs font-medium transition ${
              activeTab === 'knowledge'
                ? 'border-foreground text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Knowledge Base</span>
          </button>

          <button
            onClick={() => setActiveTab('prompts')}
            className={`flex items-center gap-2 py-3 px-3 border-b-2 text-xs font-medium transition ${
              activeTab === 'prompts'
                ? 'border-foreground text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Prompts</span>
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

        {/* Tab 1: Models */}
        {activeTab === 'models' && (
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {isCreating || editingModel ? (
              /* Model Create / Edit Form */
              <form onSubmit={handleSave} className="space-y-4 text-xs">
                <div className="flex items-center justify-between pb-2 border-b border-border">
                  <h4 className="font-semibold text-foreground text-sm">
                    {isCreating ? 'Create Custom Model Preset' : `Edit Model: ${editingModel?.name}`}
                  </h4>
                  <button
                    type="button"
                    onClick={() => {
                      setIsCreating(false);
                      setEditingModel(null);
                    }}
                    className="text-muted-foreground hover:text-foreground text-xs"
                  >
                    Cancel
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Model Identifier (ID)</label>
                    <input
                      type="text"
                      value={formId}
                      onChange={(e) => setFormId(e.target.value)}
                      disabled={!isCreating}
                      required
                      placeholder="e.g. cambridge-tutor"
                      className="w-full p-2 bg-background border border-border rounded-lg text-foreground font-mono disabled:opacity-50"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Display Name</label>
                    <input
                      type="text"
                      value={formName}
                      onChange={(e) => setFormName(e.target.value)}
                      required
                      placeholder="e.g. Cambridge IGCSE Math Specialist"
                      className="w-full p-2 bg-background border border-border rounded-lg text-foreground"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Base Model Engine</label>
                    <select
                      value={formBase}
                      onChange={(e) => setFormBase(e.target.value)}
                      className="w-full p-2 bg-background border border-border rounded-lg text-foreground font-mono"
                    >
                      <option value="educore-enterprise-all">educore-enterprise-all (Unified)</option>
                      <option value="qwen2.5:latest">qwen2.5:latest (Fast)</option>
                      <option value="llama3.2:latest">llama3.2:latest</option>
                      <option value="deepseek-r1:8b">deepseek-r1:8b (Reasoning)</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="font-medium text-foreground">Required Clearance Tier</label>
                    <select
                      value={formTier}
                      onChange={(e) => setFormTier(e.target.value as ClearanceTier)}
                      className="w-full p-2 bg-background border border-border rounded-lg text-foreground font-mono uppercase"
                    >
                      <option value="public">public (All Users)</option>
                      <option value="staff">staff (Educators)</option>
                      <option value="counselor">counselor</option>
                      <option value="finance">finance</option>
                      <option value="devops">devops</option>
                      <option value="admin">admin (Full Governance)</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground">Description</label>
                  <input
                    type="text"
                    value={formDesc}
                    onChange={(e) => setFormDesc(e.target.value)}
                    placeholder="Short description of model capabilities and purview..."
                    className="w-full p-2 bg-background border border-border rounded-lg text-foreground"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-foreground">System Prompt (Governed Instructions)</label>
                  <textarea
                    value={formPrompt}
                    onChange={(e) => setFormPrompt(e.target.value)}
                    rows={4}
                    placeholder="You are an Educore AI tutor strictly adhering to Cambridge standards..."
                    className="w-full p-2 bg-background border border-border rounded-lg text-foreground font-mono resize-y"
                  />
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between">
                    <label className="font-medium text-foreground">Temperature</label>
                    <span className="font-mono text-muted-foreground">{formTemp.toFixed(2)}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1.5"
                    step="0.05"
                    value={formTemp}
                    onChange={(e) => setFormTemp(parseFloat(e.target.value))}
                    className="w-full accent-foreground"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setIsCreating(false);
                      setEditingModel(null);
                    }}
                    className="px-3 py-1.5 border border-border rounded-lg text-foreground hover:bg-muted transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-4 py-1.5 bg-foreground text-background font-medium rounded-lg hover:opacity-90 transition disabled:opacity-50"
                  >
                    {loading ? 'Saving...' : 'Save Model'}
                  </button>
                </div>
              </form>
            ) : (
              /* Models List */
              <>
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search model presets..."
                    className="w-full pl-9 pr-3 py-2 text-xs bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-1 focus:ring-foreground"
                  />
                </div>

                <div className="grid grid-cols-1 gap-2.5">
                  {filteredModels.map((m) => (
                    <div
                      key={m.id}
                      className="p-3.5 rounded-xl border border-border bg-card hover:border-foreground/30 transition flex items-start justify-between group"
                    >
                      <div className="flex-1 pr-4">
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <span className="font-semibold text-xs text-foreground">{m.name}</span>
                          <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-muted border border-border">
                            {m.requiredTier || m.clearanceLevel || 'public'}
                          </span>
                          {m.is_custom && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-foreground text-background font-medium">
                              Custom
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                          {m.description || 'Governed institutional intelligence model.'}
                        </p>
                        <div className="flex items-center gap-3 mt-2 text-[10px] text-muted-foreground font-mono">
                          <span>Base: {m.base_model_id || 'educore-enterprise-all'}</span>
                          <span>Temp: {m.temperature ?? 0.7}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5 shrink-0">
                        <button
                          onClick={() => {
                            onSelectModel(m);
                            onClose();
                          }}
                          className="px-2.5 py-1 rounded-lg text-xs bg-muted hover:bg-foreground hover:text-background transition font-medium"
                          title="Select this model for chat"
                        >
                          Use
                        </button>
                        <button
                          onClick={() => startEdit(m)}
                          className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
                          title="Edit model"
                        >
                          <Edit3 size={13} />
                        </button>
                        {m.is_custom && (
                          <button
                            onClick={() => handleDelete(m.id, m.name)}
                            className="p-1.5 rounded-lg text-muted-foreground hover:text-red-500 hover:bg-muted transition"
                            title="Delete custom model"
                          >
                            <Trash2 size={13} />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Tab 2: Knowledge Base */}
        {activeTab === 'knowledge' && (
          <div className="flex-1 overflow-y-auto p-6 space-y-4 text-xs">
            <div className="flex items-center justify-between p-4 rounded-xl bg-muted/40 border border-border">
              <div>
                <h4 className="font-semibold text-foreground text-xs">ChromaDB Multi-Campus Corpus</h4>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  Synchronizes ISO/IEC 42001 governance policies, Cambridge IGCSE syllabi, and administrative handbooks.
                </p>
              </div>
              <button
                onClick={handleTriggerSync}
                disabled={syncing}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-foreground text-background font-medium rounded-lg hover:opacity-90 transition disabled:opacity-50"
              >
                <RefreshCw size={13} className={syncing ? 'animate-spin' : ''} />
                <span>{syncing ? 'Indexing...' : 'Sync Corpus'}</span>
              </button>
            </div>

            {/* ChromaDB Shard Breakdown */}
            <div className="space-y-2">
              <label className="font-semibold text-foreground text-xs">Physical Shard Status</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {frameworkStatus?.shard_vector_counts ? (
                  Object.entries(frameworkStatus.shard_vector_counts).map(([shardName, count]) => (
                    <div key={shardName} className="p-3 rounded-xl border border-border bg-card flex justify-between items-center">
                      <div>
                        <span className="font-medium text-foreground capitalize">{shardName}</span>
                        <p className="text-[10px] text-muted-foreground">Governed Purview Vector Shard</p>
                      </div>
                      <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-muted">
                        {String(count)} records
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="col-span-2 text-center py-6 text-muted-foreground">
                    Corpus initialized with 21+ framework documents.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Prompts Presets */}
        {activeTab === 'prompts' && (
          <div className="flex-1 overflow-y-auto p-6 space-y-3 text-xs">
            <p className="text-[11px] text-muted-foreground">
              Select or copy institutional prompt templates grounded in Educore standards:
            </p>
            <div className="grid grid-cols-1 gap-2.5">
              {institutionalPrompts.map((p, idx) => (
                <div key={idx} className="p-3.5 rounded-xl border border-border bg-card space-y-2 hover:border-foreground/30 transition">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-foreground text-xs">{p.title}</span>
                      <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-muted font-mono font-medium">
                        {p.category}
                      </span>
                    </div>
                    {onUsePrompt && (
                      <button
                        onClick={() => {
                          onUsePrompt(p.prompt);
                          onClose();
                        }}
                        className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs bg-muted hover:bg-foreground hover:text-background transition font-medium"
                      >
                        <Play size={11} fill="currentColor" />
                        <span>Use</span>
                      </button>
                    )}
                  </div>
                  <p className="text-[11px] text-muted-foreground">{p.desc}</p>
                  <div className="p-2 rounded-lg bg-background border border-border font-mono text-[10px] text-foreground">
                    {p.prompt}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="px-6 py-3 border-t border-border bg-muted/20 flex justify-between items-center text-[11px] text-muted-foreground">
          <span>Educore Enterprise Model & Knowledge Management</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-foreground text-background font-medium text-xs hover:opacity-90 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
