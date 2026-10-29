import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Undo2,
  Play
} from 'lucide-react';

export default function AIChatbotPanel({
  chatMessages,
  onSendCommand,
  isProcessing,
  onSelectSuggestion,
  onApplyProposal,
  onCancelProposal
}) {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef(null);

  const quickPrompts = [
    'Select the clip from 00:10 to 00:25.',
    'Split at 00:18.',
    'Delete the selected segment.',
    'Split the selected clip at its midpoint.',
    'Delete the second half of the selected clip.',
    'Trim the video from 00:10 to 01:20.',
    'Play the video.',
    'Export the edited video.'
  ];

  const handleSend = (e) => {
    e?.preventDefault();
    if (!inputText.trim() || isProcessing) return;
    onSendCommand(inputText.trim());
    setInputText('');
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  return (
    <div className="h-full flex flex-col bg-[#141518] text-[#a0a4ae] select-none text-[11px]">
      {/* 1. Header */}
      <div className="h-7 px-3 border-b border-[#212328] flex items-center justify-between bg-[#18191d] text-[10px]">
        <div className="flex items-center gap-1.5 text-[#d0d3dc] font-medium">
          <Sparkles className="w-3 h-3 text-[#d48b3b]" />
          <span>EditMind Assistant</span>
        </div>
        <span className="text-[9px] text-[#696e7d] font-mono">Local NLE Engine</span>
      </div>

      {/* 2. Chat Log Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        {chatMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[90%] rounded p-2 text-[11px] leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-[#272932] text-[#e0e3eb] border border-[#373a46]'
                  : msg.isError
                  ? 'bg-[#251b1d] border border-[#442327] text-[#e28b8b]'
                  : 'bg-[#1a1b20] border border-[#262830] text-[#b5b9c4]'
              }`}
            >
              {/* Header */}
              <div className="flex items-center gap-1.5 mb-1 text-[9px] text-[#6b707e]">
                <span className="font-semibold text-[#8b90a0]">
                  {msg.sender === 'assistant' ? 'Assistant' : 'Editor'}
                </span>
                <span>• {msg.timestamp}</span>
              </div>

              {/* Message text */}
              <p className="whitespace-pre-wrap">{msg.text}</p>

              {/* Proposed Action Card (if action proposal present) */}
              {msg.actionProposal && (
                <div className="mt-2 pt-1.5 border-t border-[#2d303a] bg-[#141519] p-2 rounded border border-[#242630] space-y-1.5">
                  <div className="flex items-center justify-between text-[10px] text-[#d0d3dc] font-medium">
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-[#3b9a55]" />
                      <span>{msg.actionProposal.title || 'Proposed Timeline Edit'}</span>
                    </span>
                  </div>

                  {msg.actionProposal.time && (
                    <p className="text-[10px] font-mono text-[#8a8f9e]">
                      Target Time: <span className="text-[#c4c7d2]">{msg.actionProposal.time}</span>
                    </p>
                  )}
                  {msg.actionProposal.range && (
                    <p className="text-[10px] font-mono text-[#8a8f9e]">
                      Target Range: <span className="text-[#c4c7d2]">{msg.actionProposal.range}</span>
                    </p>
                  )}
                </div>
              )}

              {/* Action Description notification */}
              {msg.actionDescription && !msg.actionProposal && (
                <div className="mt-1.5 pt-1 border-t border-[#262832] flex items-center gap-1 text-[10px] text-[#5bb676] font-mono">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>{msg.actionDescription}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {isProcessing && (
          <div className="text-[10px] text-[#717582] italic bg-[#1a1b20] px-2 py-1.5 rounded border border-[#24262f] w-fit flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#d48b3b] animate-ping" />
            <span>Processing editing instruction...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 3. Suggested Prompt Chips */}
      <div className="px-2.5 py-1.5 border-t border-[#1f2025] bg-[#121316]">
        <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-thin">
          {quickPrompts.map((cmd, idx) => (
            <button
              key={idx}
              onClick={() => onSelectSuggestion(cmd)}
              className="text-[10px] whitespace-nowrap bg-[#1a1b20] hover:bg-[#252730] text-[#868a96] hover:text-[#d0d3dc] border border-[#272932] px-2 py-0.5 rounded transition shrink-0"
            >
              {cmd}
            </button>
          ))}
        </div>
      </div>

      {/* 4. Natural-Language Input Box */}
      <form onSubmit={handleSend} className="p-2 border-t border-[#212328] bg-[#16171b] flex items-center gap-1.5">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder='e.g. "Split at 00:18", "Delete selected segment"...'
          disabled={isProcessing}
          className="flex-1 bg-[#1a1c22] text-[11px] text-[#d8dbe4] placeholder-[#555a66] rounded px-2.5 py-1.5 border border-[#282b34] focus:outline-none focus:border-[#424653] transition"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || isProcessing}
          className="px-2.5 py-1.5 bg-[#252830] hover:bg-[#323642] disabled:opacity-30 text-[#e0e3eb] rounded border border-[#343844] transition flex items-center justify-center"
          title="Send command"
        >
          <Send className="w-3 h-3" />
        </button>
      </form>
    </div>
  );
}
