import { MessageSquare, Send, Sparkles, Loader2 } from 'lucide-react';
import { useState } from 'react';
import clsx from 'clsx';

interface AssistantPanelProps {
  onQuery: (query: string) => Promise<{ reply: string; data?: any }>;
}

const SUGGESTIONS = [
  "How many vehicles are inside?",
  "Vehicle count today",
  "Recent vehicles in",
  "Recent vehicles out"
];

export function AssistantPanel({ onQuery }: AssistantPanelProps) {
  const [input, setInput] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [messages, setMessages] = useState<{role: 'user' | 'assistant', content: string}[]>([
    { role: 'assistant', content: 'Hello! I can help query campus vehicle data.' }
  ]);

  const handleSubmit = async (text: string) => {
    if (!text.trim() || isSearching) return;
    
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setIsSearching(true);
    
    try {
      const response = await onQuery(text);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.reply + (response.data && response.data.records ? `\nFound ${response.data.records.length} records.` : '') 
      }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error executing that query.' }]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#101624] rounded-xl shadow-lg border border-slate-800/80 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800/80 bg-[#161e31]">
        <Sparkles className="w-5 h-5 text-indigo-400" />
        <h2 className="font-semibold text-slate-200">Data Assistant</h2>
      </div>
      
      <div className="p-3 border-b border-slate-800/80 flex flex-wrap gap-2 bg-[#101624]">
        {SUGGESTIONS.map((suggestion, idx) => (
          <button
            key={idx}
            onClick={() => handleSubmit(suggestion)}
            disabled={isSearching}
            className="text-xs font-semibold px-3 py-1.5 bg-[#161e31] border border-slate-700/60 rounded-full text-slate-300 hover:border-indigo-500 hover:text-indigo-400 hover:shadow-sm transition-all disabled:opacity-50 cursor-pointer"
          >
            {suggestion}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={clsx(
            "flex gap-3 max-w-[85%]",
            msg.role === 'user' ? "ml-auto flex-row-reverse" : ""
          )}>
            <div className={clsx(
              "w-8 h-8 rounded-full flex items-center justify-center shrink-0 border",
              msg.role === 'user' ? "bg-indigo-950/40 text-indigo-450 border-indigo-900/40" : "bg-slate-800 text-slate-300 border-slate-700/50"
            )}>
              {msg.role === 'user' ? <MessageSquare className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
            </div>
            <div className={clsx(
              "px-4 py-2 rounded-2xl text-sm whitespace-pre-wrap border",
              msg.role === 'user' 
                ? "bg-indigo-600 text-slate-100 border-indigo-500 rounded-tr-sm" 
                : "bg-slate-800/70 text-slate-200 border-slate-700/55 rounded-tl-sm"
            )}>
              {msg.content}
            </div>
          </div>
        ))}
        {isSearching && (
          <div className="flex gap-3 max-w-[85%]">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-750 text-slate-350 flex items-center justify-center shrink-0">
              <Loader2 className="w-4 h-4 animate-spin" />
            </div>
            <div className="px-4 py-2 rounded-2xl text-sm bg-slate-800/70 border border-slate-750 text-slate-350 rounded-tl-sm flex items-center">
              Processing...
            </div>
          </div>
        )}
      </div>

      <div className="p-3 border-t border-slate-800 bg-[#101624]">
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSubmit(input); }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            disabled={isSearching}
            className="flex-1 px-4 py-2 bg-[#161e31] rounded-lg border border-slate-700/80 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all placeholder:text-slate-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isSearching}
            className="p-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:hover:bg-indigo-600 cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
