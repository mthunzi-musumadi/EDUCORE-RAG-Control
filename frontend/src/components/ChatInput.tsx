import React, { useRef, useEffect, useState } from 'react';
import { ArrowUp, Square, Paperclip, Zap, Mic, MicOff, Globe } from 'lucide-react';
import { EducoreModel } from '../types';

interface ChatInputProps {
  input: string;
  setInput: React.Dispatch<React.SetStateAction<string>> | ((value: string | ((prev: string) => string)) => void);
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  onStop: () => void;
  activeModel: EducoreModel;
  onOpenControls?: () => void;
  onUploadFile?: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  input,
  setInput,
  onSubmit,
  isLoading,
  onStop,
  activeModel,
  onOpenControls,
  onUploadFile,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef<any>(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 220)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isLoading) {
        onSubmit(e as any);
      }
    }
  };

  // Web Speech API Voice Recognition (Open WebUI 1:1)
  const toggleRecording = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    if (isRecording) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsRecording(false);
    } else {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        let currentTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          currentTranscript += event.results[i][0].transcript;
        }
        setInput((prev: string) => (prev ? prev + ' ' + currentTranscript : currentTranscript));
      };

      recognition.onerror = () => {
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognition.start();
      recognitionRef.current = recognition;
      setIsRecording(true);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-3 sm:px-4 pb-3 sm:pb-4 pt-1">
      {/* Floating Rounded Input Container (Open WebUI / ChatGPT Style) */}
      <form
        onSubmit={onSubmit}
        className="relative flex flex-col bg-card rounded-2xl sm:rounded-3xl border border-border shadow-lg focus-within:border-foreground/40 transition-all p-2 sm:p-2.5"
      >
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={`Message ${activeModel.name}...`}
          rows={1}
          className="w-full bg-transparent resize-none border-0 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-0 px-3 py-1.5 min-h-[44px] max-h-[220px]"
        />

        <div className="flex items-center justify-between pt-1 px-1.5 sm:px-2">
          {/* Left: Attachment & RAG Status indicators */}
          <div className="flex items-center gap-1.5 text-muted-foreground">
            {onUploadFile && (
              <button
                type="button"
                onClick={onUploadFile}
                className="p-1.5 rounded-full hover:text-foreground hover:bg-muted transition"
                title="Attach documents to RAG knowledge base"
              >
                <Paperclip size={16} />
              </button>
            )}

            <button
              type="button"
              onClick={onOpenControls}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-muted border border-border text-foreground hover:bg-muted/80 transition"
              title="Click to adjust chat parameters"
            >
              <Zap size={11} className="text-foreground" />
              <span>RAG Governed</span>
            </button>

            <span className="hidden sm:inline-block text-[11px] font-mono text-muted-foreground">
              Shift+Enter for newline
            </span>
          </div>

          {/* Right: Dictation & Submit/Stop Button */}
          <div className="flex items-center gap-1.5">
            {/* Voice Dictation (Microphone) */}
            <button
              type="button"
              onClick={toggleRecording}
              className={`p-1.5 rounded-full transition ${
                isRecording 
                  ? 'bg-red-500/20 text-red-500 animate-pulse' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
              }`}
              title={isRecording ? "Stop dictation" : "Voice input (Dictate)"}
            >
              {isRecording ? <MicOff size={16} /> : <Mic size={16} />}
            </button>

            {/* Send / Stop Toggle */}
            {isLoading ? (
              <button
                type="button"
                onClick={onStop}
                className="w-8 h-8 rounded-full bg-foreground text-background flex items-center justify-center hover:opacity-90 transition-opacity"
                title="Stop generation"
              >
                <Square size={13} fill="currentColor" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                  input.trim()
                    ? 'bg-foreground text-background hover:opacity-90'
                    : 'bg-muted text-muted-foreground cursor-not-allowed'
                }`}
                title="Send message"
              >
                <ArrowUp size={16} strokeWidth={2.5} />
              </button>
            )}
          </div>
        </div>
      </form>

      {/* Institutional Disclaimer Footer */}
      <div className="text-[11px] text-muted-foreground text-center mt-2">
        Educore Enterprise RAG can make mistakes. Verify critical institutional decisions and Cambridge syllabus information.
      </div>
    </div>
  );
};
