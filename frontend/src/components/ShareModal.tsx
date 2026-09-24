import React, { useState } from 'react';
import { X, Share2, Copy, Check, Download, FileText, Code2 } from 'lucide-react';
import { ChatSession } from '../types';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  session: ChatSession | null;
}

export const ShareModal: React.FC<ShareModalProps> = ({
  isOpen,
  onClose,
  session,
}) => {
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedText, setCopiedText] = useState(false);

  if (!isOpen || !session) return null;

  const conversationMarkdown = `# ${session.title}\n\n*Generated on ${new Date(session.createdAt).toLocaleString()}*\n\n---\n\n` +
    session.messages.map((m) => `### ${m.role === 'user' ? 'User' : 'Educore AI'} (${new Date(m.timestamp).toLocaleTimeString()}):\n\n${m.content}\n\n`).join('---\n\n');

  const handleCopyText = () => {
    navigator.clipboard.writeText(conversationMarkdown);
    setCopiedText(true);
    setTimeout(() => setCopiedText(false), 2000);
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const downloadFile = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadMarkdown = () => {
    const filename = `${session.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.md`;
    downloadFile(conversationMarkdown, filename, 'text/markdown');
  };

  const handleDownloadJSON = () => {
    const filename = `${session.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.json`;
    downloadFile(JSON.stringify(session, null, 2), filename, 'application/json');
  };

  const handleDownloadTXT = () => {
    const plainText = session.messages.map((m) => `[${m.role.toUpperCase()}] ${m.content}`).join('\n\n');
    const filename = `${session.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.txt`;
    downloadFile(plainText, filename, 'text/plain');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="w-full max-w-md bg-card border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-5 py-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Share2 className="w-4 h-4 text-foreground" />
            <h3 className="text-sm font-semibold text-foreground">Share Conversation</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 text-xs">
          <div className="p-3 rounded-xl bg-muted/40 border border-border">
            <p className="font-semibold text-xs text-foreground truncate">{session.title}</p>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              {session.messages.length} message{session.messages.length === 1 ? '' : 's'} • Last active {new Date(session.updatedAt).toLocaleTimeString()}
            </p>
          </div>

          {/* Quick Copy Options */}
          <div className="space-y-2">
            <label className="font-semibold text-muted-foreground text-[11px]">Copy to Clipboard</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={handleCopyText}
                className="flex items-center justify-center gap-1.5 p-2.5 rounded-xl border border-border hover:bg-muted text-foreground transition font-medium"
              >
                {copiedText ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedText ? 'Copied Transcript' : 'Copy Transcript'}</span>
              </button>
              <button
                onClick={handleCopyLink}
                className="flex items-center justify-center gap-1.5 p-2.5 rounded-xl border border-border hover:bg-muted text-foreground transition font-medium"
              >
                {copiedLink ? <Check className="w-3.5 h-3.5" /> : <Share2 className="w-3.5 h-3.5" />}
                <span>{copiedLink ? 'Copied Link' : 'Copy Link'}</span>
              </button>
            </div>
          </div>

          {/* Export File Formats */}
          <div className="space-y-2 pt-2">
            <label className="font-semibold text-muted-foreground text-[11px]">Export Format</label>
            <div className="space-y-1.5">
              <button
                onClick={handleDownloadMarkdown}
                className="w-full flex items-center justify-between p-2.5 rounded-xl border border-border hover:bg-muted text-foreground transition text-left"
              >
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-muted-foreground" />
                  <div>
                    <span className="font-medium text-xs">Markdown (.md)</span>
                    <p className="text-[10px] text-muted-foreground">Formatted conversation with code blocks and headers</p>
                  </div>
                </div>
                <Download className="w-3.5 h-3.5 text-muted-foreground" />
              </button>

              <button
                onClick={handleDownloadJSON}
                className="w-full flex items-center justify-between p-2.5 rounded-xl border border-border hover:bg-muted text-foreground transition text-left"
              >
                <div className="flex items-center gap-2">
                  <Code2 className="w-4 h-4 text-muted-foreground" />
                  <div>
                    <span className="font-medium text-xs">JSON (.json)</span>
                    <p className="text-[10px] text-muted-foreground">Full structured payload with telemetry metadata</p>
                  </div>
                </div>
                <Download className="w-3.5 h-3.5 text-muted-foreground" />
              </button>

              <button
                onClick={handleDownloadTXT}
                className="w-full flex items-center justify-between p-2.5 rounded-xl border border-border hover:bg-muted text-foreground transition text-left"
              >
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-muted-foreground" />
                  <div>
                    <span className="font-medium text-xs">Plain Text (.txt)</span>
                    <p className="text-[10px] text-muted-foreground">Lightweight text transcript</p>
                  </div>
                </div>
                <Download className="w-3.5 h-3.5 text-muted-foreground" />
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-border bg-muted/20 flex justify-end">
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
