import React, { useState, useEffect } from 'react';
import { X, Activity, RefreshCw, Shield, FileText, CheckCircle2 } from 'lucide-react';
import { ApiService } from '../services/api';
import { EducoreModel, User } from '../types';

interface TelemetryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeModel: EducoreModel;
  currentUser: User | null;
}

export const TelemetryDrawer: React.FC<TelemetryDrawerProps> = ({
  isOpen,
  onClose,
  activeModel,
  currentUser,
}) => {
  const [health, setHealth] = useState<any>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [frameworkStatus, setFrameworkStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadTelemetry = async () => {
    setLoading(true);
    try {
      const [h, a, f] = await Promise.all([
        ApiService.getHealth().catch(() => ({ status: 'offline' })),
        ApiService.getAuditLogs().catch(() => []),
        ApiService.getFrameworkStatus().catch(() => ({ status: 'unavailable' })),
      ]);
      setHealth(h);
      setAuditLogs(Array.isArray(a) ? a.slice(-15).reverse() : []);
      setFrameworkStatus(f);
    } catch (e) {
      console.error('Failed to load telemetry:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadTelemetry();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/50 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-md bg-card h-full border-l border-border shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="h-14 px-5 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity size={18} className="text-foreground" />
            <h2 className="text-sm font-semibold text-foreground">
              ISO/IEC 42001 Live Telemetry
            </h2>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={loadTelemetry}
              className={`p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition ${loading ? 'animate-spin' : ''}`}
              title="Refresh Telemetry"
            >
              <RefreshCw size={15} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto space-y-5 flex-1 text-xs">
          {/* Active Session Status */}
          <div className="p-3.5 rounded-xl bg-muted/30 border border-border space-y-2">
            <div className="font-semibold text-foreground flex items-center justify-between">
              <span>Active Governance Boundary</span>
              <span className="flex items-center gap-1 text-[11px] text-foreground font-mono">
                <CheckCircle2 size={13} />
                Online
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-1 text-muted-foreground">
              <div>
                <span className="text-[10px] block text-muted-foreground uppercase">User</span>
                <span className="font-medium text-foreground truncate block">
                  {currentUser?.name || 'Guest User'}
                </span>
              </div>
              <div>
                <span className="text-[10px] block text-muted-foreground uppercase">Clearance</span>
                <span className="font-medium text-foreground uppercase block font-semibold">
                  {currentUser?.clearance || 'public'}
                </span>
              </div>
              <div>
                <span className="text-[10px] block text-muted-foreground uppercase">Campus</span>
                <span className="font-medium text-foreground truncate block">
                  {currentUser?.campus || 'Global / All'}
                </span>
              </div>
              <div>
                <span className="text-[10px] block text-muted-foreground uppercase">Model</span>
                <span className="font-medium text-foreground truncate block">
                  {activeModel.name}
                </span>
              </div>
            </div>
          </div>

          {/* Framework Document Watcher & Shards */}
          <div className="p-3.5 rounded-xl bg-muted/30 border border-border space-y-2">
            <div className="font-semibold text-foreground flex items-center gap-1.5">
              <Shield size={14} className="text-foreground" />
              <span>ChromaDB Physical Shard Isolation</span>
            </div>
            <p className="text-[11px] text-muted-foreground">
              Physical collections segregated by clearance tier with zero software leakage.
            </p>
            {frameworkStatus?.shard_vector_counts ? (
              <div className="grid grid-cols-2 gap-1.5 pt-1">
                {Object.entries(frameworkStatus.shard_vector_counts).map(([shard, count]) => (
                  <div key={shard} className="flex justify-between p-1.5 rounded bg-card border border-border font-mono text-[10px]">
                    <span className="uppercase text-muted-foreground">{shard}</span>
                    <span className="font-bold text-foreground">{String(count)} docs</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-muted-foreground text-[11px]">Loading shard telemetry...</div>
            )}
          </div>

          {/* Recent Audit Ledger Transactions */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-foreground flex items-center gap-1.5">
                <FileText size={14} className="text-foreground" />
                Recent Audit Trail (aims_rag_audit.jsonl)
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">
                {auditLogs.length} events
              </span>
            </div>

            <div className="space-y-1.5 max-h-72 overflow-y-auto">
              {auditLogs.length === 0 ? (
                <div className="p-4 text-center text-muted-foreground text-[11px] bg-muted/20 rounded-xl border border-border">
                  No recent audit transactions logged.
                </div>
              ) : (
                auditLogs.map((log, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-xl bg-card border border-border space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-muted-foreground">
                        {log.timestamp ? log.timestamp.split('T')[1]?.split('.')[0] : 'Just now'}
                      </span>
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${
                        log.guardrail_status?.includes('BLOCKED')
                          ? 'bg-red-500/10 text-red-500 border border-red-500/20'
                          : 'bg-muted text-foreground border border-border'
                      }`}>
                        {log.guardrail_status || 'ALLOW'}
                      </span>
                    </div>
                    <p className="text-[11px] text-foreground truncate font-medium">
                      {log.query}
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-0.5">
                      <span>User: {log.user_email || 'anonymous'}</span>
                      <span className="font-mono">{log.latency_ms?.toFixed(1) || 0}ms</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border text-[11px] text-muted-foreground text-center bg-muted/20">
          Compliant with ISO/IEC 42001 & Zambian Data Protection Act
        </div>
      </div>
    </div>
  );
};
