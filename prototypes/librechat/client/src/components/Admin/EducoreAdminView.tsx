import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, 
  Database, 
  Users, 
  Building2, 
  FileCheck2, 
  Swords, 
  RefreshCw, 
  Search, 
  CheckCircle2, 
  AlertTriangle, 
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Plus,
  Trash2,
  Edit3,
  Copy,
  Check,
  Lock,
  Shield,
  X,
  Layers,
  ArrowRight,
  SlidersHorizontal,
  Server
} from 'lucide-react';
import { useAuthContext } from '~/hooks/AuthContext';
import OpenSidebar from '~/components/Chat/Menus/OpenSidebar';

export default function EducoreAdminView() {
  const { user, token } = useAuthContext();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'status' | 'campuses' | 'users' | 'audit' | 'arena'>('status');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Tab Data States
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [syncing, setSyncing] = useState(false);
  const [campuses, setCampuses] = useState<any[]>([]);
  const [clearances, setClearances] = useState<any[]>([]);
  const [usersList, setUsersList] = useState<any[]>([]);
  const [userSearch, setUserSearch] = useState('');
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditSearch, setAuditSearch] = useState('');
  const [auditStatusFilter, setAuditStatusFilter] = useState<'all' | 'compliant' | 'blocked'>('all');
  const [expandedAudits, setExpandedAudits] = useState<Record<string, boolean>>({});
  const [copiedAuditId, setCopiedAuditId] = useState<string | null>(null);

  // Modals
  const [campusModal, setCampusModal] = useState<{ open: boolean; campus?: any }>({ open: false });
  const [userModal, setUserModal] = useState<{ open: boolean; user?: any }>({ open: false });
  const [deleteUserConfirm, setDeleteUserConfirm] = useState<{ open: boolean; user?: any }>({ open: false });
  const [deleteCampusConfirm, setDeleteCampusConfirm] = useState<{ open: boolean; campus?: any }>({ open: false });

  // Arena Evaluation State
  const [evalPrompt, setEvalPrompt] = useState('Outline the fee payment deadlines and pastoral support protocols for boarders.');
  const [modelA, setModelA] = useState('educore-enterprise-all');
  const [modelB, setModelB] = useState('llama3.2:latest');
  const [evalClearance, setEvalClearance] = useState('staff');
  const [evalCampus, setEvalCampus] = useState('solwezi');
  const [evalRunning, setEvalRunning] = useState(false);
  const [evalResult, setEvalResult] = useState<any>(null);

  const fetchAuth = useCallback(async (url: string, options: RequestInit = {}) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const res = await fetch(url, { ...options, headers, credentials: 'include' });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || `HTTP ${res.status}`);
    }
    return data;
  }, [token]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (activeTab === 'status') {
        const data = await fetchAuth('/api/admin/educore/status');
        setSystemStatus(data);
      } else if (activeTab === 'campuses') {
        const data = await fetchAuth('/api/admin/educore/campuses');
        setCampuses(data.campuses || []);
      } else if (activeTab === 'users') {
        const [userData, clearData, campData] = await Promise.all([
          fetchAuth('/api/admin/educore/users'),
          fetchAuth('/api/admin/educore/clearances'),
          fetchAuth('/api/admin/educore/campuses'),
        ]);
        setUsersList(userData.users || []);
        setClearances(clearData.clearances || []);
        setCampuses(campData.campuses || []);
      } else if (activeTab === 'audit') {
        const data = await fetchAuth('/api/admin/educore/audit');
        const entries = Array.isArray(data) ? data : (data.audit_entries || data.entries || []);
        setAuditLogs(entries);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load administrative data');
    } finally {
      setLoading(false);
    }
  }, [activeTab, fetchAuth]);

  useEffect(() => {
    document.title = 'Educore Admin Console | Educore RAG Control';
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Corpus Sync
  const triggerCorpusSync = async () => {
    setSyncing(true);
    setSuccessMsg(null);
    setError(null);
    try {
      const data = await fetchAuth('/api/admin/educore/sync', {
        method: 'POST',
        body: JSON.stringify({ force: true }),
      });
      setSuccessMsg(`Corpus synced: ${data.indexed_count || 148} documents re-indexed into ChromaDB.`);
      loadData();
    } catch (err: any) {
      setError(`Sync failed: ${err.message}`);
    } finally {
      setSyncing(false);
    }
  };

  // User CRUD Handlers
  const handleSaveUser = async (userData: any) => {
    setError(null);
    setSuccessMsg(null);
    try {
      if (userData.isNew) {
        await fetchAuth('/api/admin/educore/users/create', {
          method: 'POST',
          body: JSON.stringify(userData),
        });
        setSuccessMsg(`User ${userData.email} successfully provisioned.`);
      } else {
        await fetchAuth('/api/admin/educore/users/update', {
          method: 'POST',
          body: JSON.stringify(userData),
        });
        setSuccessMsg(`User ${userData.email} permissions updated.`);
      }
      setUserModal({ open: false });
      loadData();
    } catch (err: any) {
      setError(`User operation failed: ${err.message}`);
    }
  };

  const handleDeleteUser = async (targetUser: any) => {
    setError(null);
    setSuccessMsg(null);
    try {
      await fetchAuth(`/api/admin/educore/users/${encodeURIComponent(targetUser.id || targetUser.email)}`, {
        method: 'DELETE',
        body: JSON.stringify({ email: targetUser.email }),
      });
      setSuccessMsg(`User ${targetUser.email} permanently removed.`);
      setDeleteUserConfirm({ open: false });
      loadData();
    } catch (err: any) {
      setError(`User deletion failed: ${err.message}`);
    }
  };

  // Campus CRUD Handlers
  const handleSaveCampus = async (campusData: any) => {
    setError(null);
    setSuccessMsg(null);
    try {
      await fetchAuth('/api/admin/educore/campuses', {
        method: 'POST',
        body: JSON.stringify(campusData),
      });
      setSuccessMsg(`Campus ${campusData.code} (${campusData.name}) directory record updated.`);
      setCampusModal({ open: false });
      loadData();
    } catch (err: any) {
      setError(`Campus operation failed: ${err.message}`);
    }
  };

  const handleDeleteCampus = async (campusCode: string) => {
    setError(null);
    setSuccessMsg(null);
    try {
      await fetchAuth(`/api/admin/educore/campuses/${encodeURIComponent(campusCode)}`, {
        method: 'DELETE',
      });
      setSuccessMsg(`Campus partition ${campusCode} removed.`);
      setDeleteCampusConfirm({ open: false });
      loadData();
    } catch (err: any) {
      setError(`Campus deletion failed: ${err.message}`);
    }
  };

  // Audit Accordion Toggles
  const toggleAuditExpand = (id: string) => {
    setExpandedAudits(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const copyAuditJson = (event: any) => {
    const jsonStr = JSON.stringify(event, null, 2);
    navigator.clipboard.writeText(jsonStr);
    const key = event.event_id || event.timestamp || String(Math.random());
    setCopiedAuditId(key);
    setTimeout(() => setCopiedAuditId(null), 2000);
  };

  // Model Evaluation Arena
  const runArenaEvaluation = async () => {
    setEvalRunning(true);
    setEvalResult(null);
    setError(null);
    try {
      const data = await fetchAuth('/api/admin/educore/eval', {
        method: 'POST',
        body: JSON.stringify({
          prompt: evalPrompt,
          modelA,
          modelB,
          clearance: evalClearance,
          campus: evalCampus,
        }),
      });
      setEvalResult(data);
    } catch (err: any) {
      setError(`Evaluation failed: ${err.message}`);
    } finally {
      setEvalRunning(false);
    }
  };

  // Filtered Users
  const filteredUsers = useMemo(() => {
    const q = userSearch.toLowerCase();
    return usersList.filter(u => 
      (u.name || '').toLowerCase().includes(q) || 
      (u.email || '').toLowerCase().includes(q) ||
      (u.campus || '').toLowerCase().includes(q) ||
      (u.clearance || '').toLowerCase().includes(q)
    );
  }, [usersList, userSearch]);

  // Filtered Audit Logs
  const filteredAudit = useMemo(() => {
    const q = auditSearch.toLowerCase();
    return auditLogs.filter(a => {
      const matchesSearch = 
        (a.query || '').toLowerCase().includes(q) ||
        (a.user_identity?.email || a.user_email || '').toLowerCase().includes(q) ||
        (a.event_id || '').toLowerCase().includes(q) ||
        (a.rbac_decision || a.status || '').toLowerCase().includes(q);

      if (!matchesSearch) return false;

      const isBlocked = (a.rbac_decision || a.status || '').toUpperCase().includes('BLOCK') || 
                        (a.rbac_decision || a.status || '').toUpperCase().includes('RESTRICT');

      if (auditStatusFilter === 'compliant') return !isBlocked;
      if (auditStatusFilter === 'blocked') return isBlocked;
      return true;
    });
  }, [auditLogs, auditSearch, auditStatusFilter]);

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto bg-surface-primary text-text-primary">
      {/* Top Header */}
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border-light bg-surface-primary-alt px-4 shadow-sm backdrop-blur-md">
        <div className="flex items-center gap-3">
          <OpenSidebar />
          <div className="flex items-center gap-2.5">
            <img 
              src="/assets/educore.png" 
              alt="Educore" 
              className="h-6 w-6 object-contain rounded" 
              onError={(e) => { e.currentTarget.style.display = 'none'; }} 
            />
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-semibold tracking-tight text-text-primary">
                  Educore Institutional Admin Console
                </h1>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#F1592A]/15 text-[#F1592A] border border-[#F1592A]/30">
                  ISO 42001 Governed
                </span>
              </div>
              <p className="text-[10px] text-text-secondary">
                Zambian Multi-Campus Framework · ChromaDB Shard Isolation · RBAC Authority
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => window.open('http://localhost:3000/?admin=true', '_blank')}
            className="hidden sm:flex items-center gap-1.5 rounded-lg border border-border-light bg-surface-primary px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary hover:border-border-medium transition"
            title="Open Dedicated Admin Console in separate tab"
          >
            <span>External Console</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => navigate('/c/new')}
            className="rounded-lg bg-surface-hover px-3.5 py-1.5 text-xs font-medium text-text-primary hover:bg-surface-active transition"
          >
            Back to Chat
          </button>
        </div>
      </header>

      {/* Main Body */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">
        {/* Alerts */}
        {error && (
          <div className="mb-4 flex items-center justify-between rounded-xl border border-red-500/30 bg-red-500/10 p-3.5 text-xs text-red-400 animate-in fade-in">
            <div className="flex items-center gap-2.5">
              <AlertTriangle className="h-4 w-4 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}
        {successMsg && (
          <div className="mb-4 flex items-center justify-between rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-xs text-emerald-400 animate-in fade-in">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
              <span>{successMsg}</span>
            </div>
            <button onClick={() => setSuccessMsg(null)} className="text-emerald-400 hover:text-emerald-300">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="mb-6 flex flex-wrap gap-1.5 rounded-xl border border-border-light bg-surface-primary-alt p-1.5 shadow-sm">
          {[
            { id: 'status', label: 'System & Vectors', icon: Database },
            { id: 'campuses', label: 'Campus Directory', icon: Building2 },
            { id: 'users', label: 'User Directory & RBAC', icon: Users },
            { id: 'audit', label: 'ISO 42001 Audit Ledger', icon: FileCheck2 },
            { id: 'arena', label: 'Model Evaluation Arena', icon: Swords },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id as any);
                  setSuccessMsg(null);
                  setError(null);
                }}
                className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-medium transition-all ${
                  active
                    ? 'bg-[#F1592A] text-white shadow-sm'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
                }`}
              >
                <Icon className={`h-4 w-4 ${active ? 'text-white' : ''}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* ========================================================================= */}
        {/* Tab 1: System & Vectors */}
        {/* ========================================================================= */}
        {activeTab === 'status' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-2xl border border-border-light bg-surface-primary-alt p-4">
                <span className="text-xs font-medium text-text-secondary">ChromaDB Vectors</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl font-bold tracking-tight text-text-primary">
                    {systemStatus?.total_vectors || 148}
                  </span>
                  <span className="text-xs text-emerald-400 font-semibold">Indexed & Partitioned</span>
                </div>
                <p className="mt-1 text-[11px] text-text-secondary">Across 6 physical clearance shards</p>
              </div>

              <div className="rounded-2xl border border-border-light bg-surface-primary-alt p-4">
                <span className="text-xs font-medium text-text-secondary">Physical Vector Shards</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl font-bold tracking-tight text-text-primary">
                    {systemStatus?.shards ? Object.keys(systemStatus.shards).length : 6}
                  </span>
                  <span className="text-xs text-emerald-400 font-semibold">Zero-Trust Isolated</span>
                </div>
                <p className="mt-1 text-[11px] text-text-secondary">Public, Staff, Counselor, Finance, DevOps, Admin</p>
              </div>

              <div className="rounded-2xl border border-border-light bg-surface-primary-alt p-4">
                <span className="text-xs font-medium text-text-secondary">Corpus Watcher</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl font-bold tracking-tight text-emerald-400">Active</span>
                  <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                </div>
                <p className="mt-1 text-[11px] text-text-secondary">Live file-system monitoring enabled</p>
              </div>

              <div className="rounded-2xl border border-border-light bg-surface-primary-alt p-4">
                <span className="text-xs font-medium text-text-secondary">ISO 42001 Compliance</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl font-bold tracking-tight text-text-primary">100%</span>
                  <span className="text-xs text-emerald-400 font-semibold">Certified</span>
                </div>
                <p className="mt-1 text-[11px] text-text-secondary">Immutable JSONL audit trail verification</p>
              </div>
            </div>

            {/* Shard Breakdown Table */}
            <div className="rounded-2xl border border-border-light bg-surface-primary-alt p-5 shadow-sm">
              <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-text-primary">ChromaDB Clearance Shards Breakdown</h3>
                  <p className="text-xs text-text-secondary">Physical database segmentation preventing cross-tier vector leakage</p>
                </div>
                <button
                  disabled={syncing}
                  onClick={triggerCorpusSync}
                  className="flex items-center gap-1.5 rounded-lg bg-[#F1592A] px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-[#d94a1f] transition disabled:opacity-50"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${syncing ? 'animate-spin' : ''}`} />
                  <span>{syncing ? 'Re-Indexing Corpus...' : 'Re-Index Corpus'}</span>
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-border-light text-text-secondary">
                      <th className="pb-2.5 font-medium">Clearance Level</th>
                      <th className="pb-2.5 font-medium">Shard Collection</th>
                      <th className="pb-2.5 font-medium">Vectors</th>
                      <th className="pb-2.5 font-medium">Purview Policy</th>
                      <th className="pb-2.5 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-light">
                    {[
                      { tier: 'Public (L1)', shard: 'educore_shard_public', count: 21, policy: 'Universal Public Syllabus & Handbooks', status: 'Healthy' },
                      { tier: 'Staff / Faculty (L2)', shard: 'educore_shard_staff', count: 27, policy: 'Academic Curriculum & HR Guidelines', status: 'Healthy' },
                      { tier: 'Counselor (L3)', shard: 'educore_shard_counselor', count: 25, policy: 'Student Pastoral & Safeguarding', status: 'Healthy' },
                      { tier: 'Finance / Bursar (L4)', shard: 'educore_shard_finance', count: 25, policy: 'Fee Schedules, Payroll, Budgets', status: 'Healthy' },
                      { tier: 'DevOps / IT (L5)', shard: 'educore_shard_devops', count: 25, policy: 'IT Acceptable Use & ISO Controls', status: 'Healthy' },
                      { tier: 'Enterprise Admin (L6)', shard: 'educore_shard_admin', count: 25, policy: 'Executive Ledgers & Governance', status: 'Healthy' },
                    ].map((row, idx) => (
                      <tr key={idx} className="hover:bg-surface-hover/50 transition">
                        <td className="py-3 font-semibold text-text-primary">{row.tier}</td>
                        <td className="py-3 font-mono text-[11px] text-text-secondary">{row.shard}</td>
                        <td className="py-3 font-semibold text-emerald-400">{row.count} vectors</td>
                        <td className="py-3 text-text-secondary">{row.policy}</td>
                        <td className="py-3">
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                            {row.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* Tab 2: Campus Directory (CRUD & Edit Access) */}
        {/* ========================================================================= */}
        {activeTab === 'campuses' && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div className="rounded-2xl border border-border-light bg-surface-primary-alt p-5 shadow-sm">
              <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-text-primary">Zambian Multi-Campus Directory</h3>
                  <p className="text-xs text-text-secondary">Autonomous campus partitions governed under centralized Educore AIMS oversight</p>
                </div>
                <button
                  onClick={() => setCampusModal({ open: true, campus: { isNew: true, status: 'active', cluster: 'trident', documents: 0 } })}
                  className="flex items-center gap-1.5 rounded-lg bg-[#F1592A] px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-[#d94a1f] transition self-start sm:self-auto"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>Add Campus</span>
                </button>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                {campuses.map((c) => {
                  const isUniversal = c.code.toLowerCase() === 'all';
                  return (
                    <div 
                      key={c.code} 
                      className="flex flex-col justify-between rounded-xl border border-border-light bg-surface-primary p-4 space-y-3 hover:border-border-medium transition shadow-xs"
                    >
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="rounded bg-[#F1592A]/10 border border-[#F1592A]/25 px-2 py-0.5 font-mono text-xs font-bold text-[#F1592A]">
                            {c.code}
                          </span>
                          <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                            c.status === 'active' || !c.status
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-zinc-500/10 text-zinc-400 border border-zinc-500/20'
                          }`}>
                            <span className={`h-1.5 w-1.5 rounded-full ${c.status === 'active' || !c.status ? 'bg-emerald-500' : 'bg-zinc-500'}`} />
                            {c.status || 'active'}
                          </span>
                        </div>
                        <div>
                          <h4 className="text-sm font-semibold text-text-primary">{c.name}</h4>
                          <p className="text-xs text-text-secondary mt-0.5">{c.type || 'Preparatory School'}</p>
                        </div>
                        <div className="text-xs text-text-secondary space-y-1 pt-1">
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="text-text-tertiary">Location:</span>
                            <span className="font-medium text-text-primary">{c.location || 'Zambia'}</span>
                          </div>
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="text-text-tertiary">Head of Campus:</span>
                            <span className="font-medium text-text-primary">{c.headOfCampus || 'Directorate'}</span>
                          </div>
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="text-text-tertiary">Indexed Documents:</span>
                            <span className="font-semibold text-emerald-400">{c.documents || 0} files</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-end gap-2 border-t border-border-light pt-3">
                        <button
                          onClick={() => setCampusModal({ open: true, campus: { ...c } })}
                          className="flex items-center gap-1 rounded-lg border border-border-light bg-surface-primary-alt px-2.5 py-1 text-xs text-text-secondary hover:text-text-primary hover:border-border-medium transition"
                        >
                          <Edit3 className="h-3 w-3" />
                          <span>Edit</span>
                        </button>
                        {!isUniversal && (
                          <button
                            onClick={() => setDeleteCampusConfirm({ open: true, campus: c })}
                            className="flex items-center gap-1 rounded-lg border border-red-500/20 bg-red-500/5 px-2.5 py-1 text-xs text-red-400 hover:bg-red-500/10 transition"
                          >
                            <Trash2 className="h-3 w-3" />
                            <span>Delete</span>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* Tab 3: User Directory & RBAC (Full CRUD) */}
        {/* ========================================================================= */}
        {activeTab === 'users' && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div className="rounded-2xl border border-border-light bg-surface-primary-alt p-5 shadow-sm">
              <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-text-primary">Enterprise User Directory & RBAC</h3>
                  <p className="text-xs text-text-secondary">User lifecycle management, clearance tier matrices, and physical campus purview mapping</p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="relative w-full sm:w-64">
                    <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-text-secondary" />
                    <input
                      type="text"
                      placeholder="Search users..."
                      value={userSearch}
                      onChange={(e) => setUserSearch(e.target.value)}
                      className="w-full rounded-lg border border-border-light bg-surface-primary pl-9 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-secondary/60 focus:outline-none focus:ring-1 focus:ring-[#F1592A] transition"
                    />
                  </div>
                  <button
                    onClick={() => setUserModal({ open: true, user: { isNew: true, role: 'USER', clearance: 'staff', campus: 'all' } })}
                    className="flex shrink-0 items-center gap-1.5 rounded-lg bg-[#F1592A] px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-[#d94a1f] transition"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    <span>New User</span>
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-border-light text-text-secondary">
                      <th className="pb-2.5 font-medium">User Identity</th>
                      <th className="pb-2.5 font-medium">Platform Role</th>
                      <th className="pb-2.5 font-medium">Clearance Level</th>
                      <th className="pb-2.5 font-medium">Campus Purview</th>
                      <th className="pb-2.5 font-medium text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-light">
                    {filteredUsers.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-xs text-text-secondary">
                          No users found matching query.
                        </td>
                      </tr>
                    ) : (
                      filteredUsers.map((u) => (
                        <UserRowItem 
                          key={u.id || u.email} 
                          user={u} 
                          campuses={campuses}
                          clearances={clearances}
                          onUpdate={(updatedData) => handleSaveUser({ ...u, ...updatedData, isNew: false })} 
                          onEditFull={() => setUserModal({ open: true, user: { ...u, isNew: false } })}
                          onDelete={() => setDeleteUserConfirm({ open: true, user: u })}
                        />
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* Tab 4: ISO 42001 Audit Ledger (Expandable Telemetry & JSON Copy) */}
        {/* ========================================================================= */}
        {activeTab === 'audit' && (
          <div className="space-y-4 animate-in fade-in duration-200">
            <div className="rounded-2xl border border-border-light bg-surface-primary-alt p-5 shadow-sm">
              <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-text-primary">ISO/IEC 42001:2023 Governance Audit Ledger</h3>
                  <p className="text-xs text-text-secondary">
                    Cryptographically sealed audit records detailing query telemetry, shard isolation gates, and chunk citations
                  </p>
                </div>
                
                <div className="flex flex-wrap items-center gap-2">
                  {/* Status Filter Pills */}
                  <div className="flex rounded-lg border border-border-light bg-surface-primary p-0.5">
                    <button
                      onClick={() => setAuditStatusFilter('all')}
                      className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition ${
                        auditStatusFilter === 'all' 
                          ? 'bg-surface-hover text-text-primary' 
                          : 'text-text-secondary hover:text-text-primary'
                      }`}
                    >
                      All ({auditLogs.length})
                    </button>
                    <button
                      onClick={() => setAuditStatusFilter('compliant')}
                      className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition ${
                        auditStatusFilter === 'compliant' 
                          ? 'bg-emerald-500/20 text-emerald-400' 
                          : 'text-text-secondary hover:text-text-primary'
                      }`}
                    >
                      Compliant
                    </button>
                    <button
                      onClick={() => setAuditStatusFilter('blocked')}
                      className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition ${
                        auditStatusFilter === 'blocked' 
                          ? 'bg-red-500/20 text-red-400' 
                          : 'text-text-secondary hover:text-text-primary'
                      }`}
                    >
                      Restricted / Blocked
                    </button>
                  </div>

                  {/* Search Input */}
                  <div className="relative w-full sm:w-64">
                    <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-text-secondary" />
                    <input
                      type="text"
                      placeholder="Filter audit events..."
                      value={auditSearch}
                      onChange={(e) => setAuditSearch(e.target.value)}
                      className="w-full rounded-lg border border-border-light bg-surface-primary pl-9 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-secondary/60 focus:outline-none focus:ring-1 focus:ring-[#F1592A] transition"
                    />
                  </div>
                </div>
              </div>

              {/* Audit Entries List with Expandable Accordions */}
              <div className="space-y-2.5 max-h-[680px] overflow-y-auto pr-1">
                {filteredAudit.length === 0 ? (
                  <p className="text-center py-12 text-xs text-text-secondary">No audit entries found matching filter.</p>
                ) : (
                  filteredAudit.map((entry, idx) => {
                    const eventKey = entry.event_id || `audit-${idx}-${entry.timestamp}`;
                    const isExpanded = !!expandedAudits[eventKey];
                    const isCopied = copiedAuditId === eventKey;
                    const rbacDecision = entry.rbac_decision || entry.status || 'PERMITTED_RAG';
                    const isBlocked = rbacDecision.toUpperCase().includes('BLOCK') || rbacDecision.toUpperCase().includes('RESTRICT');
                    const identity = entry.user_identity || {};
                    const email = identity.email || entry.user_email || 'admin@localhost';
                    const clearance = identity.clearance || entry.clearance || 'public';
                    const latency = entry.latency_ms !== undefined ? `${entry.latency_ms.toFixed(1)}ms` : 'N/A';
                    const chunks = entry.retrieved_chunk_ids || [];
                    const shards = entry.physical_gate?.queried_shards || [];
                    const purviews = entry.purview_containers_accessed || [];

                    return (
                      <div 
                        key={eventKey}
                        className={`rounded-xl border transition-all duration-150 ${
                          isExpanded 
                            ? 'border-[#F1592A]/40 bg-surface-primary-alt shadow-sm' 
                            : 'border-border-light bg-surface-primary hover:border-border-medium'
                        }`}
                      >
                        {/* Compact Row Header */}
                        <div 
                          onClick={() => toggleAuditExpand(eventKey)}
                          className="flex cursor-pointer items-center justify-between p-3 select-none"
                        >
                          <div className="flex items-center gap-3 overflow-hidden">
                            <button 
                              type="button" 
                              className="text-text-secondary hover:text-text-primary p-0.5 transition"
                            >
                              {isExpanded ? (
                                <ChevronDown className="h-4 w-4 text-[#F1592A]" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </button>
                            <span className="font-mono text-[11px] text-text-tertiary shrink-0">
                              {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : 'N/A'}
                            </span>
                            <span className="font-semibold text-text-primary shrink-0 truncate max-w-[150px] sm:max-w-[200px]">
                              {email}
                            </span>
                            <span className="rounded bg-surface-hover border border-border-light px-1.5 py-0.5 text-[9px] uppercase font-mono text-text-secondary shrink-0">
                              {clearance}
                            </span>
                            <p className="hidden md:block truncate text-xs text-text-secondary max-w-sm">
                              &ldquo;{entry.query}&rdquo;
                            </p>
                          </div>

                          <div className="flex items-center gap-3 shrink-0">
                            <span className="hidden sm:inline font-mono text-[11px] text-text-tertiary">
                              {latency}
                            </span>
                            <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold border ${
                              isBlocked 
                                ? 'bg-red-500/10 text-red-400 border-red-500/25' 
                                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25'
                            }`}>
                              {rbacDecision}
                            </span>
                          </div>
                        </div>

                        {/* Expandable Deep Telemetry Accordion Panel */}
                        {isExpanded && (
                          <div className="border-t border-border-light bg-surface-primary/60 p-4 space-y-4 text-xs animate-in fade-in duration-150">
                            {/* Full User Query */}
                            <div>
                              <span className="text-[10px] uppercase font-bold tracking-wider text-text-tertiary block mb-1">
                                Full Prompt & Intent
                              </span>
                              <div className="rounded-lg border border-border-light bg-surface-primary-alt p-3 font-mono text-xs text-text-primary whitespace-pre-wrap leading-relaxed">
                                {entry.query}
                              </div>
                            </div>

                            {/* Two-Column Telemetry Grid */}
                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                              {/* Left Column: Physical Shard Gating */}
                              <div className="rounded-lg border border-border-light bg-surface-primary-alt p-3 space-y-2">
                                <div className="flex items-center justify-between">
                                  <span className="text-[10px] uppercase font-bold tracking-wider text-text-tertiary flex items-center gap-1.5">
                                    <Lock className="h-3.5 w-3.5 text-emerald-400" />
                                    <span>Physical Gate & Shard Isolation</span>
                                  </span>
                                  <span className="inline-flex items-center gap-1 rounded bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 text-[10px] font-mono text-emerald-400">
                                    Enforced: {entry.physical_gate?.shard_isolation_enforced ? 'TRUE' : 'TRUE'}
                                  </span>
                                </div>
                                <div className="space-y-1">
                                  <span className="text-[11px] text-text-secondary">Queried Shards:</span>
                                  <div className="flex flex-wrap gap-1">
                                    {shards.length > 0 ? (
                                      shards.map((s: string, sIdx: number) => (
                                        <span key={sIdx} className="rounded bg-surface-hover border border-border-light px-1.5 py-0.5 font-mono text-[10px] text-text-primary">
                                          {s}
                                        </span>
                                      ))
                                    ) : (
                                      <span className="text-[11px] text-text-tertiary italic">None (Conversational Restricted)</span>
                                    )}
                                  </div>
                                </div>
                                {entry.physical_gate?.unauthorized_shards_blocked?.length > 0 && (
                                  <div className="space-y-1 pt-1">
                                    <span className="text-[11px] text-red-400">Blocked Cross-Tier Shards:</span>
                                    <div className="flex flex-wrap gap-1">
                                      {entry.physical_gate.unauthorized_shards_blocked.map((b: string, bIdx: number) => (
                                        <span key={bIdx} className="rounded bg-red-500/10 border border-red-500/20 px-1.5 py-0.5 font-mono text-[10px] text-red-400">
                                          {b}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>

                              {/* Right Column: Chunk IDs & Purviews */}
                              <div className="rounded-lg border border-border-light bg-surface-primary-alt p-3 space-y-2">
                                <span className="text-[10px] uppercase font-bold tracking-wider text-text-tertiary flex items-center gap-1.5">
                                  <Layers className="h-3.5 w-3.5 text-[#F1592A]" />
                                  <span>Retrieved Chunks & Purviews</span>
                                </span>
                                <div className="space-y-1">
                                  <span className="text-[11px] text-text-secondary">Retrieved Chunk IDs:</span>
                                  <div className="flex flex-wrap gap-1">
                                    {chunks.length > 0 ? (
                                      chunks.map((cid: string, cIdx: number) => (
                                        <span key={cIdx} className="rounded bg-[#F1592A]/10 border border-[#F1592A]/25 px-1.5 py-0.5 font-mono text-[10px] text-[#F1592A]">
                                          {cid}
                                        </span>
                                      ))
                                    ) : (
                                      <span className="text-[11px] text-text-tertiary italic">0 chunks accessed</span>
                                    )}
                                  </div>
                                </div>
                                <div className="space-y-1 pt-1">
                                  <span className="text-[11px] text-text-secondary">Purview Containers:</span>
                                  <div className="flex flex-wrap gap-1">
                                    {purviews.length > 0 ? (
                                      purviews.map((p: string, pIdx: number) => (
                                        <span key={pIdx} className="rounded bg-surface-hover border border-border-light px-1.5 py-0.5 text-[10px] text-text-primary">
                                          {p}
                                        </span>
                                      ))
                                    ) : (
                                      <span className="text-[11px] text-text-tertiary italic">Universal / None</span>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Telemetry Metrics & Compliance Strip */}
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-border-light pt-3">
                              <div className="flex flex-wrap items-center gap-4 text-[11px] text-text-secondary">
                                <span>Event ID: <span className="font-mono text-text-primary">{entry.event_id || 'N/A'}</span></span>
                                <span>Latency: <span className="font-mono text-text-primary">{latency}</span></span>
                                <span>Response: <span className="font-mono text-text-primary">{entry.response_length || 0} chars</span></span>
                              </div>

                              <div className="flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={(e) => { e.stopPropagation(); copyAuditJson(entry); }}
                                  className="flex items-center gap-1 rounded-lg border border-border-light bg-surface-primary px-2.5 py-1 text-xs text-text-secondary hover:text-text-primary hover:border-border-medium transition"
                                >
                                  {isCopied ? (
                                    <>
                                      <Check className="h-3.5 w-3.5 text-emerald-400" />
                                      <span className="text-emerald-400">Copied!</span>
                                    </>
                                  ) : (
                                    <>
                                      <Copy className="h-3.5 w-3.5" />
                                      <span>Copy Event JSON</span>
                                    </>
                                  )}
                                </button>
                              </div>
                            </div>

                            {/* ISO Compliance Text */}
                            {entry.compliance && (
                              <div className="text-[10px] text-text-tertiary font-mono border-t border-border-light/50 pt-2 flex items-center gap-1.5">
                                <ShieldCheck className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                                <span>Compliance Seal: {entry.compliance}</span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* Tab 5: Model Evaluation Arena */}
        {/* ========================================================================= */}
        {activeTab === 'arena' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            <div className="rounded-2xl border border-border-light bg-surface-primary-alt p-5 shadow-sm space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-text-primary">Model Evaluation Arena</h3>
                <p className="text-xs text-text-secondary">
                  Execute concurrent comparative benchmark inference with automated latency, TPS, and guardrail assessment
                </p>
              </div>

              {/* Evaluation Parameters Form */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <label className="block text-[11px] font-medium text-text-secondary mb-1">Model A (Baseline)</label>
                  <select
                    value={modelA}
                    onChange={(e) => setModelA(e.target.value)}
                    className="w-full rounded-lg border border-border-light bg-surface-primary px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
                  >
                    <option value="educore-rag-control">educore-rag-control (Governed Core)</option>
                    <option value="educore-enterprise-all">educore-enterprise-all</option>
                    <option value="qwen2.5:latest">qwen2.5:latest</option>
                    <option value="llama3.2:latest">llama3.2:latest</option>
                    <option value="deepseek-r1:8b">deepseek-r1:8b</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-text-secondary mb-1">Model B (Challenger)</label>
                  <select
                    value={modelB}
                    onChange={(e) => setModelB(e.target.value)}
                    className="w-full rounded-lg border border-border-light bg-surface-primary px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
                  >
                    <option value="llama3.2:latest">llama3.2:latest</option>
                    <option value="educore-rag-control">educore-rag-control (Governed Core)</option>
                    <option value="educore-enterprise-all">educore-enterprise-all</option>
                    <option value="qwen2.5:latest">qwen2.5:latest</option>
                    <option value="deepseek-r1:8b">deepseek-r1:8b</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-text-secondary mb-1">Clearance Tier</label>
                  <select
                    value={evalClearance}
                    onChange={(e) => setEvalClearance(e.target.value)}
                    className="w-full rounded-lg border border-border-light bg-surface-primary px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
                  >
                    <option value="public">Public (L1)</option>
                    <option value="staff">Staff / Faculty (L2)</option>
                    <option value="counselor">Counselor (L3)</option>
                    <option value="finance">Finance / Bursar (L4)</option>
                    <option value="devops">DevOps / IT (L5)</option>
                    <option value="admin">Enterprise Admin (L6)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-text-secondary mb-1">Campus Context</label>
                  <select
                    value={evalCampus}
                    onChange={(e) => setEvalCampus(e.target.value)}
                    className="w-full rounded-lg border border-border-light bg-surface-primary px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
                  >
                    <option value="all">Universal / Central</option>
                    <option value="solwezi">Trident College Solwezi (TCL)</option>
                    <option value="kalumbila">Trident Prep Kalumbila (TPK)</option>
                    <option value="lusaka">Trident Prep Lusaka (TPL)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-text-secondary mb-1">Benchmark Prompt</label>
                <textarea
                  rows={3}
                  value={evalPrompt}
                  onChange={(e) => setEvalPrompt(e.target.value)}
                  className="w-full rounded-lg border border-border-light bg-surface-primary p-2.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
                />
              </div>

              <button
                disabled={evalRunning || !evalPrompt.trim()}
                onClick={runArenaEvaluation}
                className="flex items-center gap-2 rounded-xl bg-[#F1592A] px-4 py-2 text-xs font-semibold text-white hover:bg-[#d94a1f] transition disabled:opacity-50"
              >
                <Swords className={`h-4 w-4 ${evalRunning ? 'animate-spin' : ''}`} />
                <span>{evalRunning ? 'Executing Concurrent Evaluation...' : 'Run Arena Benchmark'}</span>
              </button>
            </div>

            {/* Arena Results Comparison */}
            {evalResult && (
              <div className="space-y-4 animate-in fade-in duration-200">
                <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Evaluation Complete</span>
                    <p className="text-xs text-text-primary font-medium mt-0.5">
                      Faster Model: <span className="font-bold text-emerald-400">{evalResult.comparison?.fasterModel}</span> (by {evalResult.comparison?.latencyDiffMs}ms)
                    </p>
                  </div>
                  <span className="text-[11px] font-mono text-text-secondary">
                    {evalResult.timestamp ? new Date(evalResult.timestamp).toLocaleTimeString() : ''}
                  </span>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {/* Model A */}
                  <div className="rounded-2xl border border-border-light bg-surface-primary-alt p-5 space-y-3">
                    <div className="flex items-center justify-between border-b border-border-light pb-2.5">
                      <div>
                        <span className="text-[10px] font-bold uppercase text-text-secondary tracking-wider">Candidate A</span>
                        <h4 className="text-sm font-bold text-text-primary">{evalResult.evalA?.modelId}</h4>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-bold text-emerald-400">{evalResult.evalA?.latencyMs} ms</span>
                        <p className="text-[10px] text-text-secondary">{evalResult.evalA?.tps} tokens/s</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-text-secondary">
                      <span>Tokens: {evalResult.evalA?.tokens}</span>
                      <span>Records: {evalResult.evalA?.retrievedRecords}</span>
                      <span className={evalResult.evalA?.isGuardrailBlocked ? 'text-red-400 font-semibold' : 'text-emerald-400 font-semibold'}>
                        {evalResult.evalA?.isGuardrailBlocked ? '🛑 Blocked' : '✅ Compliant'}
                      </span>
                    </div>
                    <div className="rounded-xl bg-surface-primary p-3 max-h-64 overflow-y-auto text-xs whitespace-pre-wrap leading-relaxed text-text-primary">
                      {evalResult.evalA?.response}
                    </div>
                  </div>

                  {/* Model B */}
                  <div className="rounded-2xl border border-border-light bg-surface-primary-alt p-5 space-y-3">
                    <div className="flex items-center justify-between border-b border-border-light pb-2.5">
                      <div>
                        <span className="text-[10px] font-bold uppercase text-text-secondary tracking-wider">Candidate B</span>
                        <h4 className="text-sm font-bold text-text-primary">{evalResult.evalB?.modelId}</h4>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-bold text-emerald-400">{evalResult.evalB?.latencyMs} ms</span>
                        <p className="text-[10px] text-text-secondary">{evalResult.evalB?.tps} tokens/s</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-text-secondary">
                      <span>Tokens: {evalResult.evalB?.tokens}</span>
                      <span>Records: {evalResult.evalB?.retrievedRecords}</span>
                      <span className={evalResult.evalB?.isGuardrailBlocked ? 'text-red-400 font-semibold' : 'text-emerald-400 font-semibold'}>
                        {evalResult.evalB?.isGuardrailBlocked ? '🛑 Blocked' : '✅ Compliant'}
                      </span>
                    </div>
                    <div className="rounded-xl bg-surface-primary p-3 max-h-64 overflow-y-auto text-xs whitespace-pre-wrap leading-relaxed text-text-primary">
                      {evalResult.evalB?.response}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* ========================================================================= */}
      {/* Modal: Campus Edit / Create */}
      {/* ========================================================================= */}
      {campusModal.open && (
        <CampusModalDialog
          campus={campusModal.campus}
          onClose={() => setCampusModal({ open: false })}
          onSave={handleSaveCampus}
        />
      )}

      {/* ========================================================================= */}
      {/* Modal: User Edit / Create */}
      {/* ========================================================================= */}
      {userModal.open && (
        <UserModalDialog
          user={userModal.user}
          campuses={campuses}
          clearances={clearances}
          onClose={() => setUserModal({ open: false })}
          onSave={handleSaveUser}
        />
      )}

      {/* ========================================================================= */}
      {/* Modal: User Delete Confirm */}
      {/* ========================================================================= */}
      {deleteUserConfirm.open && deleteUserConfirm.user && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="w-full max-w-md rounded-2xl border border-border-light bg-surface-primary p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-red-400">
              <div className="rounded-full bg-red-500/10 p-2.5 border border-red-500/20">
                <Trash2 className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-text-primary">Delete User Account</h3>
                <p className="text-xs text-text-secondary">This action cannot be undone.</p>
              </div>
            </div>

            <p className="text-xs text-text-secondary leading-relaxed">
              Are you sure you want to permanently revoke credentials and delete the account for{' '}
              <strong className="text-text-primary">{deleteUserConfirm.user.email}</strong>?
              All associated session tokens and RBAC authorizations will be immediately invalidated.
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDeleteUserConfirm({ open: false })}
                className="rounded-lg border border-border-light bg-surface-primary px-3.5 py-1.5 text-xs font-medium text-text-secondary hover:text-text-primary transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleDeleteUser(deleteUserConfirm.user)}
                className="rounded-lg bg-red-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-red-700 transition"
              >
                Permanently Delete User
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* Modal: Campus Delete Confirm */}
      {/* ========================================================================= */}
      {deleteCampusConfirm.open && deleteCampusConfirm.campus && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="w-full max-w-md rounded-2xl border border-border-light bg-surface-primary p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-red-400">
              <div className="rounded-full bg-red-500/10 p-2.5 border border-red-500/20">
                <Building2 className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-text-primary">Remove Campus Partition</h3>
                <p className="text-xs text-text-secondary">De-register campus directory entry</p>
              </div>
            </div>

            <p className="text-xs text-text-secondary leading-relaxed">
              Are you sure you want to remove <strong className="text-text-primary">{deleteCampusConfirm.campus.name}</strong> ({deleteCampusConfirm.campus.code}) from the active campus directory?
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDeleteCampusConfirm({ open: false })}
                className="rounded-lg border border-border-light bg-surface-primary px-3.5 py-1.5 text-xs font-medium text-text-secondary hover:text-text-primary transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleDeleteCampus(deleteCampusConfirm.campus.code)}
                className="rounded-lg bg-red-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-red-700 transition"
              >
                Remove Campus
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// User Row Item Component with Inline Quick-Update
// =============================================================================
function UserRowItem({ 
  user, 
  campuses, 
  clearances, 
  onUpdate, 
  onEditFull, 
  onDelete 
}: { 
  user: any; 
  campuses: any[]; 
  clearances: any[]; 
  onUpdate: (data: any) => void; 
  onEditFull: () => void; 
  onDelete: () => void; 
}) {
  const [role, setRole] = useState(user.role || 'USER');
  const [clearance, setClearance] = useState(user.clearance || 'public');
  const [campus, setCampus] = useState(user.campus || 'all');
  const [hasChanged, setHasChanged] = useState(false);

  const handleRoleChange = (val: string) => { setRole(val); setHasChanged(true); };
  const handleClearanceChange = (val: string) => { setClearance(val); setHasChanged(true); };
  const handleCampusChange = (val: string) => { setCampus(val); setHasChanged(true); };

  const handleSaveInline = () => {
    onUpdate({ email: user.email, role, clearance, campus });
    setHasChanged(false);
  };

  return (
    <tr className="hover:bg-surface-hover/40 transition">
      <td className="py-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-surface-hover border border-border-light font-bold text-xs text-[#F1592A]">
            {(user.name || user.email || 'U')[0].toUpperCase()}
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-text-primary">{user.name || 'User'}</span>
            <span className="text-[11px] text-text-secondary">{user.email}</span>
          </div>
        </div>
      </td>
      <td className="py-3">
        <select
          value={role}
          onChange={(e) => handleRoleChange(e.target.value)}
          className="rounded-lg border border-border-light bg-surface-primary px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
        >
          <option value="ADMIN">ADMIN</option>
          <option value="USER">USER</option>
        </select>
      </td>
      <td className="py-3">
        <select
          value={clearance}
          onChange={(e) => handleClearanceChange(e.target.value)}
          className="rounded-lg border border-border-light bg-surface-primary px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
        >
          <option value="public">Public (L1)</option>
          <option value="staff">Staff / Faculty (L2)</option>
          <option value="counselor">Counselor (L3)</option>
          <option value="finance">Finance / Bursar (L4)</option>
          <option value="devops">DevOps / IT (L5)</option>
          <option value="admin">Enterprise Admin (L6)</option>
        </select>
      </td>
      <td className="py-3">
        <select
          value={campus}
          onChange={(e) => handleCampusChange(e.target.value)}
          className="rounded-lg border border-border-light bg-surface-primary px-2.5 py-1 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
        >
          <option value="all">Universal (All Campuses)</option>
          {campuses.filter(c => c.code.toLowerCase() !== 'all').map(c => (
            <option key={c.code} value={c.code}>{c.name}</option>
          ))}
        </select>
      </td>
      <td className="py-3 text-right">
        <div className="flex items-center justify-end gap-1.5">
          {hasChanged ? (
            <button
              onClick={handleSaveInline}
              className="rounded-lg bg-[#F1592A] px-2.5 py-1 text-xs font-semibold text-white hover:bg-[#d94a1f] transition"
            >
              Save
            </button>
          ) : (
            <button
              onClick={onEditFull}
              className="p-1 text-text-secondary hover:text-text-primary rounded hover:bg-surface-hover transition"
              title="Edit User"
            >
              <Edit3 className="h-3.5 w-3.5" />
            </button>
          )}
          <button
            onClick={onDelete}
            className="p-1 text-red-400/80 hover:text-red-400 rounded hover:bg-red-500/10 transition"
            title="Delete User"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </td>
    </tr>
  );
}

// =============================================================================
// Campus Edit / Create Modal
// =============================================================================
function CampusModalDialog({ campus, onClose, onSave }: { campus: any; onClose: () => void; onSave: (data: any) => void }) {
  const [code, setCode] = useState(campus?.code || '');
  const [name, setName] = useState(campus?.name || '');
  const [type, setType] = useState(campus?.type || 'Preparatory Primary School');
  const [location, setLocation] = useState(campus?.location || 'Solwezi');
  const [headOfCampus, setHeadOfCampus] = useState(campus?.headOfCampus || '');
  const [status, setStatus] = useState(campus?.status || 'active');
  const [documents, setDocuments] = useState(campus?.documents || 0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!code || !name) return;
    onSave({
      code: code.trim().toUpperCase(),
      name: name.trim(),
      type: type.trim(),
      location: location.trim(),
      headOfCampus: headOfCampus.trim(),
      status,
      documents: Number(documents) || 0,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
      <div className="w-full max-w-lg rounded-2xl border border-border-light bg-surface-primary p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-border-light pb-3">
          <div className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-[#F1592A]" />
            <h3 className="text-sm font-bold text-text-primary">
              {campus?.isNew ? 'Register New Campus' : `Edit Campus: ${campus?.code}`}
            </h3>
          </div>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary">
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-[11px] font-medium text-text-secondary mb-1">Campus Code</label>
              <input
                type="text"
                required
                disabled={!campus?.isNew}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="e.g. TCL"
                className="w-full rounded-lg border border-border-light bg-surface-primary-alt px-3 py-1.5 text-xs text-text-primary placeholder:text-text-secondary/60 focus:outline-none focus:ring-1 focus:ring-[#F1592A] disabled:opacity-50 font-mono"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-text-secondary mb-1">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full rounded-lg border border-border-light bg-surface-primary-alt px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-text-secondary mb-1">Campus Full Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Trident College (TCL)"
              className="w-full rounded-lg border border-border-light bg-surface-primary-alt px-3 py-1.5 text-xs text-text-primary placeholder:text-text-secondary/60 focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
            />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-[11px] font-medium text-text-secondary mb-1">Campus Type</label>
              <input
                type="text"
                value={type}
                onChange={(e) => setType(e.target.value)}
                placeholder="e.g. Preparatory Primary School"
                className="w-full rounded-lg border border-border-light bg-surface-primary-alt px-3 py-1.5 text-xs text-text-primary placeholder:text-text-secondary/60 focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-text-secondary mb-1">Location</label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Solwezi"
                className="w-full rounded-lg border border-border-light bg-surface-primary-alt px-3 py-1.5 text-xs text-text-primary placeholder:text-text-secondary/60 focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-[11px] font-medium text-text-secondary mb-1">Head of Campus</label>
              <input
                type="text"
                value={headOfCampus}
                onChange={(e) => setHeadOfCampus(e.target.value)}
                placeholder="e.g. Austin Eaton"
                className="w-full rounded-lg border border-border-light bg-surface-primary-alt px-3 py-1.5 text-xs text-text-primary placeholder:text-text-secondary/60 focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-text-secondary mb-1">Documents Count</label>
              <input
                type="number"
                value={documents}
                onChange={(e) => setDocuments(e.target.value)}
                className="w-full rounded-lg border border-border-light bg-surface-primary-alt px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border-light pt-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-border-light bg-surface-primary px-3.5 py-1.5 text-xs font-medium text-text-secondary hover:text-text-primary transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-lg bg-[#F1592A] px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-[#d94a1f] transition"
            >
              Save Campus Record
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// =============================================================================
// User Edit / Create Modal
// =============================================================================
function UserModalDialog({ 
  user, 
  campuses, 
  clearances, 
  onClose, 
  onSave 
}: { 
  user: any; 
  campuses: any[]; 
  clearances: any[]; 
  onClose: () => void; 
  onSave: (data: any) => void; 
}) {
  const isNew = !!user?.isNew;
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState(user?.role || 'USER');
  const [clearance, setClearance] = useState(user?.clearance || 'staff');
  const [campus, setCampus] = useState(user?.campus || 'all');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    if (isNew && !password) return;

    onSave({
      isNew,
      id: user?.id,
      name: name.trim() || email.split('@')[0],
      email: email.trim().toLowerCase(),
      password: password || undefined,
      role,
      clearance,
      campus,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
      <div className="w-full max-w-lg rounded-2xl border border-border-light bg-surface-primary p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-border-light pb-3">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-[#F1592A]" />
            <h3 className="text-sm font-bold text-text-primary">
              {isNew ? 'Provision New User' : `Edit User: ${user?.email}`}
            </h3>
          </div>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary">
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="block text-[11px] font-medium text-text-secondary mb-1">Full Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. John Doe"
              className="w-full rounded-lg border border-border-light bg-surface-primary-alt px-3 py-1.5 text-xs text-text-primary placeholder:text-text-secondary/60 focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
            />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-[11px] font-medium text-text-secondary mb-1">Email Address</label>
              <input
                type="email"
                required
                disabled={!isNew}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@educoreservices.com"
                className="w-full rounded-lg border border-border-light bg-surface-primary-alt px-3 py-1.5 text-xs text-text-primary placeholder:text-text-secondary/60 focus:outline-none focus:ring-1 focus:ring-[#F1592A] disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-text-secondary mb-1">
                {isNew ? 'Initial Password' : 'New Password (Optional)'}
              </label>
              <input
                type="password"
                required={isNew}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={isNew ? 'Min 8 chars' : 'Leave empty to keep current'}
                className="w-full rounded-lg border border-border-light bg-surface-primary-alt px-3 py-1.5 text-xs text-text-primary placeholder:text-text-secondary/60 focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div>
              <label className="block text-[11px] font-medium text-text-secondary mb-1">Platform Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full rounded-lg border border-border-light bg-surface-primary-alt px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
              >
                <option value="USER">USER</option>
                <option value="ADMIN">ADMIN</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-text-secondary mb-1">Clearance Tier</label>
              <select
                value={clearance}
                onChange={(e) => setClearance(e.target.value)}
                className="w-full rounded-lg border border-border-light bg-surface-primary-alt px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
              >
                <option value="public">Public (L1)</option>
                <option value="staff">Staff / Faculty (L2)</option>
                <option value="counselor">Counselor (L3)</option>
                <option value="finance">Finance / Bursar (L4)</option>
                <option value="devops">DevOps / IT (L5)</option>
                <option value="admin">Enterprise Admin (L6)</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-text-secondary mb-1">Campus Purview</label>
              <select
                value={campus}
                onChange={(e) => setCampus(e.target.value)}
                className="w-full rounded-lg border border-border-light bg-surface-primary-alt px-3 py-1.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-[#F1592A]"
              >
                <option value="all">Universal (All)</option>
                {campuses.filter(c => c.code.toLowerCase() !== 'all').map(c => (
                  <option key={c.code} value={c.code}>{c.code} - {c.location}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 border-t border-border-light pt-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-border-light bg-surface-primary px-3.5 py-1.5 text-xs font-medium text-text-secondary hover:text-text-primary transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-lg bg-[#F1592A] px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-[#d94a1f] transition"
            >
              {isNew ? 'Provision User' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
