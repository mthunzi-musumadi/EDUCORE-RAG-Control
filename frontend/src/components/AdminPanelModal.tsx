import React, { useState, useEffect } from 'react';
import { User, SystemStatus, AuditEntry, ClearanceTier } from '../types';
import { ApiService } from '../services/api';
import { 
  X, 
  ShieldCheck, 
  Users, 
  BookOpen, 
  Activity, 
  FileText, 
  Search, 
  Trash2, 
  RefreshCw, 
  Check, 
  AlertCircle,
  Database,
  Layers
} from 'lucide-react';

interface AdminPanelModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: User | null;
}

export const AdminPanelModal: React.FC<AdminPanelModalProps> = ({
  isOpen,
  onClose,
  currentUser,
}) => {
  const [activeTab, setActiveTab] = useState<'users' | 'knowledge' | 'audit' | 'status'>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [userSearch, setUserSearch] = useState('');
  const [auditLogs, setAuditLogs] = useState<AuditEntry[]>([]);
  const [auditSearch, setAuditSearch] = useState('');
  const [frameworkStatus, setFrameworkStatus] = useState<SystemStatus | null>(null);

  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Load data when opening modal
  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen, activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'users') {
        const u = await ApiService.getUsers();
        setUsers(u);
      } else if (activeTab === 'knowledge' || activeTab === 'status') {
        const s = await ApiService.getFrameworkStatus();
        setFrameworkStatus(s);
      } else if (activeTab === 'audit') {
        const a = await ApiService.getAuditLogs();
        setAuditLogs(a);
      }
    } catch (err: any) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const handleUpdateUserRole = async (userId: string, newRole: string, clearance: string, campus: string) => {
    try {
      await ApiService.updateUser({ id: userId, role: newRole, clearance, campus });
      setStatusMsg({ text: 'User updated successfully.', type: 'success' });
      loadData();
    } catch (err: any) {
      setStatusMsg({ text: err.message || 'Failed to update user.', type: 'error' });
    }
  };

  const handleDeleteUser = async (userId: string, userName: string) => {
    if (!window.confirm(`Are you sure you want to delete user "${userName}"?`)) return;
    try {
      await ApiService.deleteUser(userId);
      setStatusMsg({ text: `User "${userName}" deleted.`, type: 'success' });
      loadData();
    } catch (err: any) {
      setStatusMsg({ text: err.message || 'Failed to delete user.', type: 'error' });
    }
  };

  const handleTriggerSync = async () => {
    setSyncing(true);
    setStatusMsg(null);
    try {
      const res = await ApiService.syncFramework(true);
      setStatusMsg({ 
        text: `Sync completed: ${res.indexed_files || 0} files indexed (${res.total_chunks || 0} chunks).`, 
        type: 'success' 
      });
      loadData();
    } catch (err: any) {
      setStatusMsg({ text: err.message || 'Knowledge sync failed.', type: 'error' });
    } finally {
      setSyncing(false);
    }
  };

  const filteredUsers = users.filter((u) =>
    u.name?.toLowerCase().includes(userSearch.toLowerCase()) ||
    u.email?.toLowerCase().includes(userSearch.toLowerCase()) ||
    u.role?.toLowerCase().includes(userSearch.toLowerCase()) ||
    u.clearance?.toLowerCase().includes(userSearch.toLowerCase())
  );

  const filteredAudit = auditLogs.filter((a) =>
    a.user_email?.toLowerCase().includes(auditSearch.toLowerCase()) ||
    a.query?.toLowerCase().includes(auditSearch.toLowerCase()) ||
    a.guardrail_status?.toLowerCase().includes(auditSearch.toLowerCase()) ||
    a.clearance?.toLowerCase().includes(auditSearch.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-4xl bg-card border border-border rounded-2xl shadow-2xl flex flex-col max-h-[88vh] overflow-hidden animate-in fade-in duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="h-5 w-5 text-foreground" />
            <div>
              <h3 className="font-semibold text-base text-foreground">Admin Management Panel</h3>
              <p className="text-[11px] text-muted-foreground">ISO/IEC 42001 Institutional Governance & RBAC Controls</p>
            </div>
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

        {/* Layout */}
        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar Tabs */}
          <div className="w-48 border-r border-border p-3 space-y-1 bg-muted/20 shrink-0">
            <button
              onClick={() => setActiveTab('users')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded-lg transition ${
                activeTab === 'users' ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              <Users className="h-4 w-4" />
              Users Directory
            </button>
            <button
              onClick={() => setActiveTab('knowledge')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded-lg transition ${
                activeTab === 'knowledge' ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              <BookOpen className="h-4 w-4" />
              Knowledge Base
            </button>
            <button
              onClick={() => setActiveTab('audit')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded-lg transition ${
                activeTab === 'audit' ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              <FileText className="h-4 w-4" />
              Audit Ledger
            </button>
            <button
              onClick={() => setActiveTab('status')}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium rounded-lg transition ${
                activeTab === 'status' ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              <Activity className="h-4 w-4" />
              System Status
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {/* USERS DIRECTORY TAB */}
            {activeTab === 'users' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between gap-4">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                    <input
                      type="text"
                      value={userSearch}
                      onChange={(e) => setUserSearch(e.target.value)}
                      placeholder="Search users by name, email, role, or clearance..."
                      className="w-full pl-9 pr-3 py-2 text-xs bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-foreground transition"
                    />
                  </div>
                  <button
                    onClick={loadData}
                    className="p-2 border border-border rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
                    title="Refresh user list"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </button>
                </div>

                <div className="border border-border rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-muted/60 text-muted-foreground border-b border-border">
                      <tr>
                        <th className="px-4 py-3 font-medium">User</th>
                        <th className="px-3 py-3 font-medium">Role</th>
                        <th className="px-3 py-3 font-medium">Clearance Tier</th>
                        <th className="px-3 py-3 font-medium">Campus</th>
                        <th className="px-3 py-3 font-medium text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {filteredUsers.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                            {loading ? 'Loading users...' : 'No users found.'}
                          </td>
                        </tr>
                      ) : (
                        filteredUsers.map((u) => (
                          <tr key={u.id} className="hover:bg-muted/20 transition">
                            <td className="px-4 py-3">
                              <div className="font-semibold text-foreground">{u.name}</div>
                              <div className="text-[11px] text-muted-foreground font-mono">{u.email}</div>
                            </td>
                            <td className="px-3 py-3">
                              <select
                                value={u.role}
                                onChange={(e) => handleUpdateUserRole(u.id, e.target.value, u.clearance, u.campus)}
                                className="px-2 py-1 bg-background border border-border rounded text-xs uppercase font-medium focus:outline-none"
                              >
                                <option value="user">User</option>
                                <option value="admin">Admin</option>
                              </select>
                            </td>
                            <td className="px-3 py-3">
                              <select
                                value={u.clearance}
                                onChange={(e) => handleUpdateUserRole(u.id, u.role, e.target.value, u.campus)}
                                className="px-2 py-1 bg-background border border-border rounded text-xs uppercase font-semibold focus:outline-none"
                              >
                                <option value="public">Public</option>
                                <option value="staff">Staff</option>
                                <option value="counselor">Counselor</option>
                                <option value="finance">Finance</option>
                                <option value="devops">DevOps</option>
                                <option value="admin">Admin</option>
                              </select>
                            </td>
                            <td className="px-3 py-3">
                              <span className="text-[11px] text-muted-foreground">{u.campus || 'all'}</span>
                            </td>
                            <td className="px-3 py-3 text-right">
                              {u.email !== 'admin@localhost' && (
                                <button
                                  onClick={() => handleDeleteUser(u.id, u.name)}
                                  className="p-1 text-red-500/70 hover:text-red-500 hover:bg-red-500/10 rounded transition"
                                  title="Delete user"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* KNOWLEDGE BASE TAB */}
            {activeTab === 'knowledge' && (
              <div className="space-y-5">
                <div className="flex items-center justify-between pb-3 border-b border-border">
                  <div>
                    <h4 className="text-sm font-semibold text-foreground">Governed Institutional Corpus</h4>
                    <p className="text-xs text-muted-foreground">
                      21+ policy documents, syllabi, handbooks, and financial schedules indexed in ChromaDB
                    </p>
                  </div>
                  <button
                    onClick={handleTriggerSync}
                    disabled={syncing}
                    className="flex items-center gap-1.5 px-3 py-2 bg-foreground text-background text-xs font-medium rounded-lg hover:opacity-90 transition disabled:opacity-50"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${syncing ? 'animate-spin' : ''}`} />
                    {syncing ? 'Indexing Corpus...' : 'Sync Corpus Now'}
                  </button>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-muted/30 border border-border rounded-xl">
                    <p className="text-[11px] text-muted-foreground uppercase font-medium">Total Vectors</p>
                    <p className="text-xl font-bold text-foreground mt-1">
                      {frameworkStatus?.total_vector_count ?? 120}
                    </p>
                  </div>
                  <div className="p-3 bg-muted/30 border border-border rounded-xl">
                    <p className="text-[11px] text-muted-foreground uppercase font-medium">Clearance Shards</p>
                    <p className="text-xl font-bold text-foreground mt-1">6 Physical Shards</p>
                  </div>
                  <div className="p-3 bg-muted/30 border border-border rounded-xl">
                    <p className="text-[11px] text-muted-foreground uppercase font-medium">Supported Formats</p>
                    <p className="text-xs font-mono text-foreground mt-2">.docx, .pdf, .xlsx, .json</p>
                  </div>
                </div>

                <div>
                  <h5 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                    Physical Shard Vector Breakdown
                  </h5>
                  <div className="border border-border rounded-xl p-3 bg-muted/20 grid grid-cols-3 gap-2 text-xs">
                    {frameworkStatus?.shard_vector_counts ? (
                      Object.entries(frameworkStatus.shard_vector_counts).map(([shard, cnt]) => (
                        <div key={shard} className="flex justify-between py-1 px-2 bg-background rounded border border-border">
                          <span className="font-semibold uppercase text-[11px]">{shard}</span>
                          <span className="font-mono text-muted-foreground">{cnt} vectors</span>
                        </div>
                      ))
                    ) : (
                      <div className="text-muted-foreground text-xs col-span-3">Loading shard counts...</div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* AUDIT LEDGER TAB */}
            {activeTab === 'audit' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between gap-4">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                    <input
                      type="text"
                      value={auditSearch}
                      onChange={(e) => setAuditSearch(e.target.value)}
                      placeholder="Filter audit records by user, query, clearance, or guardrail status..."
                      className="w-full pl-9 pr-3 py-2 text-xs bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-foreground transition"
                    />
                  </div>
                  <button
                    onClick={loadData}
                    className="p-2 border border-border rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
                    title="Refresh audit ledger"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </button>
                </div>

                <div className="border border-border rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-muted/60 text-muted-foreground border-b border-border">
                      <tr>
                        <th className="px-3 py-2.5 font-medium">Timestamp</th>
                        <th className="px-3 py-2.5 font-medium">User Email</th>
                        <th className="px-3 py-2.5 font-medium">Clearance</th>
                        <th className="px-3 py-2.5 font-medium">Prompt</th>
                        <th className="px-3 py-2.5 font-medium">Status</th>
                        <th className="px-3 py-2.5 font-medium text-right">Latency / TPS</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {filteredAudit.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                            {loading ? 'Loading audit records...' : 'No audit entries recorded yet.'}
                          </td>
                        </tr>
                      ) : (
                        filteredAudit.map((a, i) => (
                          <tr key={i} className="hover:bg-muted/20 transition">
                            <td className="px-3 py-2 text-[10px] text-muted-foreground font-mono whitespace-nowrap">
                              {a.timestamp ? a.timestamp.split('T')[1]?.split('.')[0] || a.timestamp : '-'}
                            </td>
                            <td className="px-3 py-2 font-mono text-[11px] text-foreground">
                              {a.user_email || 'anonymous'}
                            </td>
                            <td className="px-3 py-2">
                              <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-semibold bg-muted border border-border">
                                {a.clearance || 'public'}
                              </span>
                            </td>
                            <td className="px-3 py-2 max-w-xs truncate text-[11px]">
                              {a.query}
                            </td>
                            <td className="px-3 py-2">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                a.guardrail_status?.includes('BLOCKED') 
                                  ? 'bg-red-500/10 text-red-500 border border-red-500/20' 
                                  : 'bg-foreground/10 text-foreground border border-foreground/20'
                              }`}>
                                {a.guardrail_status || 'ALLOW'}
                              </span>
                            </td>
                            <td className="px-3 py-2 text-right font-mono text-[11px] text-muted-foreground">
                              {a.latency_ms?.toFixed(1) || 0}ms {a.tps ? `• ${a.tps.toFixed(1)}tps` : ''}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* SYSTEM STATUS TAB */}
            {activeTab === 'status' && (
              <div className="space-y-4 text-xs">
                <div className="p-4 bg-muted/20 border border-border rounded-xl space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full bg-foreground animate-pulse" />
                    <span className="font-semibold text-sm text-foreground">
                      {frameworkStatus?.service || 'Educore Enterprise RAG Governance Server'}
                    </span>
                  </div>
                  <p className="text-muted-foreground text-xs">
                    {frameworkStatus?.compliance || 'ISO/IEC 42001:2023 | Zambian Data Protection Act No. 3 of 2021'}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 border border-border rounded-lg bg-card">
                    <p className="text-[11px] text-muted-foreground uppercase font-medium">Status</p>
                    <p className="text-sm font-semibold text-foreground mt-0.5">Online & Compliant</p>
                  </div>
                  <div className="p-3 border border-border rounded-lg bg-card">
                    <p className="text-[11px] text-muted-foreground uppercase font-medium">Available Models</p>
                    <p className="text-sm font-semibold text-foreground mt-0.5">
                      {frameworkStatus?.available_models ?? 7} Models
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
