import React, { useRef, useEffect } from 'react';
import { ChatMessage as ChatMessageType, User } from '../types';
import { ChatMessage } from './ChatMessage';
import { BookOpen, GraduationCap, ShieldCheck, Calculator } from 'lucide-react';

interface ChatAreaProps {
  messages: ChatMessageType[];
  currentUser: User | null;
  onSelectPrompt: (promptText: string) => void;
  onOpenTelemetry?: () => void;
  onRegenerate?: () => void;
  onEditUserMessage?: (messageId: string, newContent: string) => void;
}

export const ChatArea: React.FC<ChatAreaProps> = ({
  messages,
  currentUser,
  onSelectPrompt,
  onOpenTelemetry,
  onRegenerate,
  onEditUserMessage,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on message update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const quickPrompts = [
    {
      title: 'Cambridge IGCSE Math',
      desc: 'Quadratic equations & completing the square (Syllabus 0580)',
      icon: BookOpen,
      prompt: 'Can you guide me through solving a quadratic equation using completing the square in Cambridge IGCSE Mathematics 0580?',
    },
    {
      title: 'Socratic Diagnostic Hint',
      desc: 'Chemistry stoichiometry and mole calculation guidance',
      icon: GraduationCap,
      prompt: 'I am trying to solve a chemistry stoichiometry problem involving limiting reagents and moles. Can you give me a diagnostic hint?',
    },
    {
      title: 'Governance & Purview',
      desc: '6-Step AIIA requirements under EDU-AIMS-HBK-v1.0',
      icon: ShieldCheck,
      prompt: 'What are the statutory requirements for the 6-Step Algorithmic Impact Assessment under the Educore AI Framework?',
    },
    {
      title: 'Financial Variance & Audit',
      desc: 'Dual-key manual verification notice (Guardrail Fin-01)',
      icon: Calculator,
      prompt: 'Summarize the bursary variance expenditure and dual-key audit rules under Guardrail Fin-01.',
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto">
      {messages.length === 0 ? (
        /* Empty State Landing Screen (Open WebUI / ChatGPT Style) */
        <div className="min-h-full flex flex-col items-center justify-center px-4 py-8 max-w-3xl mx-auto">
          {/* Educore Stylised Logo */}
          <div className="mb-6 relative">
            <img
              src="/educore-rag-e.png"
              alt="Educore Services RAG Platform"
              className="w-16 h-16 sm:w-20 sm:h-20 object-contain drop-shadow-md rounded-2xl p-1 bg-card border border-border"
            />
          </div>

          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground text-center mb-2">
            Educore Enterprise RAG
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground text-center max-w-md mb-8">
            Governed institutional intelligence grounded in ISO/IEC 42001 and multi-campus Purview boundaries.
          </p>

          {/* Quick Starter Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
            {quickPrompts.map((p) => {
              const Icon = p.icon;
              return (
                <button
                  key={p.title}
                  onClick={() => onSelectPrompt(p.prompt)}
                  className="flex items-start gap-3 p-3.5 rounded-2xl bg-card hover:bg-muted/60 border border-border text-left transition-all group"
                >
                  <div className="p-2 rounded-xl bg-muted text-foreground flex-shrink-0 group-hover:scale-105 transition-transform">
                    <Icon size={16} />
                  </div>
                  <div className="flex flex-col overflow-hidden">
                    <span className="text-xs font-semibold text-foreground">
                      {p.title}
                    </span>
                    <span className="text-[11px] text-muted-foreground leading-snug line-clamp-2 mt-0.5">
                      {p.desc}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      ) : (
        /* Messages Stream */
        <div className="divide-y divide-border/40 pb-8">
          {messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              message={msg}
              currentUser={currentUser}
              onOpenTelemetry={onOpenTelemetry}
              onRegenerate={onRegenerate}
              onEditUserMessage={onEditUserMessage}
            />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
};
