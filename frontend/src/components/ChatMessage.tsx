import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { 
  Copy, 
  Check, 
  ShieldAlert, 
  Activity, 
  User as UserIcon, 
  ChevronDown, 
  ChevronRight, 
  FileText,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  Edit2,
  Volume2,
  VolumeX,
  Code,
  Eye,
  CheckCircle2
} from 'lucide-react';
import { ChatMessage as ChatMessageType, User } from '../types';

interface ChatMessageProps {
  message: ChatMessageType;
  currentUser: User | null;
  onOpenTelemetry?: () => void;
  onRegenerate?: () => void;
  onEditUserMessage?: (messageId: string, newContent: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  currentUser,
  onOpenTelemetry,
  onRegenerate,
  onEditUserMessage,
}) => {
  const [copied, setCopied] = useState(false);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(message.content);
  const [viewRawMarkdown, setViewRawMarkdown] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const isUser = message.role === 'user';

  // Cleanup speech synthesis on unmount
  useEffect(() => {
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleToggleSpeech = () => {
    if (!('speechSynthesis' in window)) {
      alert('Speech synthesis is not supported in this browser.');
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    } else {
      window.speechSynthesis.cancel();
      const cleanText = message.content.replace(/[`*#_\[\]()]/g, '');
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 1.0;
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
      setIsSpeaking(true);
    }
  };

  const handleSaveEdit = () => {
    if (editContent.trim() && onEditUserMessage) {
      onEditUserMessage(message.id, editContent.trim());
      setIsEditing(false);
    }
  };

  const isGuardrailBlocked = message.content.includes('🛑 **Educore Framework Stop-Condition Triggered**');
  const retrievedDocs = message.telemetry?.retrieved_records || [];
  const tps = message.telemetry?.tps;
  const latency = message.telemetry?.latency_ms;

  return (
    <div
      className={`w-full py-5 px-3 sm:px-6 transition-colors group ${
        isUser
          ? 'bg-transparent'
          : 'bg-muted/20 border-y border-border/40'
      }`}
    >
      <div className="max-w-3xl mx-auto flex gap-3 sm:gap-4 items-start">
        {/* Avatar */}
        <div className="flex-shrink-0 mt-0.5">
          {isUser ? (
            <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-muted border border-border flex items-center justify-center text-xs font-semibold text-foreground">
              {currentUser?.name ? currentUser.name[0].toUpperCase() : <UserIcon size={14} />}
            </div>
          ) : (
            <img
              src="/educore-rag-e.png"
              alt="Educore AI Platform"
              className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg object-contain bg-background p-0.5 border border-border shadow-xs"
            />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-2">
          {/* Header row: Speaker Name & Timestamp */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-foreground">
                {isUser ? (currentUser?.name || 'You') : 'Educore AI'}
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">
                {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
              {!isUser && !isGuardrailBlocked && (
                <span className="inline-flex items-center gap-1 text-[10px] font-mono text-muted-foreground bg-muted px-1.5 py-0.5 rounded border border-border">
                  ISO 42001 Audited
                </span>
              )}
              {!isUser && isGuardrailBlocked && (
                <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-red-500 bg-red-500/10 border border-red-500/30 px-2 py-0.5 rounded-full">
                  <ShieldAlert size={11} />
                  Guardrail Intercept
                </span>
              )}
            </div>

            {/* User message hover edit button */}
            {isUser && !isEditing && (
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => setIsEditing(true)}
                  className="p-1 rounded text-muted-foreground hover:text-foreground hover:bg-muted transition"
                  title="Edit prompt"
                >
                  <Edit2 size={12} />
                </button>
                <button
                  onClick={handleCopy}
                  className="p-1 rounded text-muted-foreground hover:text-foreground hover:bg-muted transition"
                  title="Copy text"
                >
                  {copied ? <Check size={12} className="text-foreground" /> : <Copy size={12} />}
                </button>
              </div>
            )}
          </div>

          {/* Render Body or Inline Editor for User */}
          {isUser && isEditing ? (
            <div className="space-y-2 pt-1 animate-in fade-in duration-100">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={3}
                className="w-full p-2.5 rounded-xl bg-card border border-border text-foreground text-xs font-sans focus:outline-none focus:ring-1 focus:ring-foreground transition"
              />
              <div className="flex items-center gap-2 justify-end">
                <button
                  onClick={() => {
                    setIsEditing(false);
                    setEditContent(message.content);
                  }}
                  className="px-2.5 py-1 rounded-lg text-xs text-muted-foreground hover:bg-muted transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  className="px-3 py-1 rounded-lg text-xs bg-foreground text-background font-medium hover:opacity-90 transition"
                >
                  Save & Submit
                </button>
              </div>
            </div>
          ) : isGuardrailBlocked ? (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-sm text-foreground">
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          ) : viewRawMarkdown ? (
            /* Raw Markdown source view */
            <div className="p-3 rounded-xl bg-card border border-border font-mono text-xs text-foreground whitespace-pre-wrap leading-relaxed">
              {message.content}
            </div>
          ) : (
            <div className="prose dark:prose-invert max-w-none text-sm text-foreground leading-relaxed break-words font-sans">
              <ReactMarkdown
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
                components={{
                  code({ node, inline, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline ? (
                      <div className="my-3 rounded-lg overflow-hidden border border-border bg-card text-foreground">
                        <div className="flex items-center justify-between px-3.5 py-1.5 bg-muted text-[11px] font-mono text-muted-foreground border-b border-border">
                          <span>{match ? match[1] : 'code'}</span>
                          <button
                            onClick={() => navigator.clipboard.writeText(String(children).replace(/\n$/, ''))}
                            className="flex items-center gap-1 hover:text-foreground transition-colors"
                          >
                            <Copy size={12} />
                            <span>Copy code</span>
                          </button>
                        </div>
                        <div className="p-3 overflow-x-auto text-xs font-mono">
                          <code className={className} {...props}>
                            {children}
                          </code>
                        </div>
                      </div>
                    ) : (
                      <code className="px-1.5 py-0.5 rounded bg-muted text-foreground font-mono text-xs" {...props}>
                        {children}
                      </code>
                    );
                  }
                }}
              >
                {message.content}
              </ReactMarkdown>

              {message.isStreaming && <span className="inline-block w-1.5 h-4 ml-0.5 bg-foreground animate-pulse" />}
            </div>
          )}

          {/* Sources / Citations Accordion (Open WebUI Style) */}
          {!isUser && retrievedDocs.length > 0 && !message.isStreaming && (
            <div className="pt-2">
              <button
                onClick={() => setSourcesOpen(!sourcesOpen)}
                className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground font-medium py-1 transition"
              >
                {sourcesOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                <FileText size={13} />
                <span>Sources ({retrievedDocs.length} documents)</span>
              </button>

              {sourcesOpen && (
                <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2 animate-in fade-in duration-150">
                  {retrievedDocs.map((doc, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-lg bg-card border border-border text-xs space-y-1 hover:border-foreground/30 transition"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-foreground truncate">{doc.title}</span>
                        <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-muted font-mono font-medium">
                          {doc.clearance}
                        </span>
                      </div>
                      <p className="text-[10px] text-muted-foreground truncate">
                        {doc.source_file || doc.purview_label}
                      </p>
                      {doc.content && (
                        <p className="text-[11px] text-muted-foreground line-clamp-2 pt-1 border-t border-border/50">
                          {doc.content}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Action Bar for Assistant Message (Open WebUI Style) */}
          {!isUser && !message.isStreaming && (
            <div className="flex items-center justify-between pt-2 text-muted-foreground text-xs">
              <div className="flex items-center gap-1">
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 px-2 py-1 rounded hover:bg-muted hover:text-foreground transition"
                  title="Copy response"
                >
                  {copied ? <Check size={13} className="text-foreground" /> : <Copy size={13} />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>

                {onRegenerate && (
                  <button
                    onClick={onRegenerate}
                    className="flex items-center gap-1 px-2 py-1 rounded hover:bg-muted hover:text-foreground transition"
                    title="Regenerate response"
                  >
                    <RotateCcw size={13} />
                    <span>Retry</span>
                  </button>
                )}

                {/* Read Aloud / TTS button */}
                <button
                  onClick={handleToggleSpeech}
                  className={`p-1.5 rounded hover:bg-muted transition ${isSpeaking ? 'text-foreground bg-muted' : ''}`}
                  title={isSpeaking ? "Stop speech" : "Read aloud"}
                >
                  {isSpeaking ? <VolumeX size={13} /> : <Volume2 size={13} />}
                </button>

                {/* Raw Markdown view toggle */}
                <button
                  onClick={() => setViewRawMarkdown(!viewRawMarkdown)}
                  className={`p-1.5 rounded hover:bg-muted transition ${viewRawMarkdown ? 'text-foreground bg-muted' : ''}`}
                  title={viewRawMarkdown ? "Show rendered" : "View raw markdown"}
                >
                  {viewRawMarkdown ? <Eye size={13} /> : <Code size={13} />}
                </button>

                <button
                  onClick={() => setFeedback(feedback === 'up' ? null : 'up')}
                  className={`p-1.5 rounded hover:bg-muted transition ${feedback === 'up' ? 'text-foreground bg-muted' : ''}`}
                  title="Good response"
                >
                  <ThumbsUp size={13} />
                </button>

                <button
                  onClick={() => setFeedback(feedback === 'down' ? null : 'down')}
                  className={`p-1.5 rounded hover:bg-muted transition ${feedback === 'down' ? 'text-foreground bg-muted' : ''}`}
                  title="Bad response"
                >
                  <ThumbsDown size={13} />
                </button>
              </div>

              {/* Latency & TPS telemetry pill */}
              <div className="flex items-center gap-2">
                {(tps || latency) && (
                  <button
                    onClick={onOpenTelemetry}
                    className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono text-muted-foreground hover:text-foreground hover:bg-muted transition"
                    title="View ISO 42001 Telemetry & Audit Logs"
                  >
                    <Activity size={12} />
                    <span>
                      {tps ? `${tps.toFixed(1)} tps` : ''}
                      {tps && latency ? ' • ' : ''}
                      {latency ? `${latency.toFixed(0)}ms` : ''}
                    </span>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
