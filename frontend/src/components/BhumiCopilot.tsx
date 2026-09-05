import { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';

interface Message {
  sender: 'user' | 'bot';
  text: string;
  provider?: string;
  grounded?: boolean;
  sources?: string[];
  suggestedAction?: {
    action_type: string;
    title: string;
    button_text?: string;
  };
  actionExecuted?: boolean;
  actionResult?: string;
  timestamp: string;
}

interface Props {
  projectId?: string;
  parcelId?: string;
}

export default function BhumiCopilot({ projectId, parcelId }: Props) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [executingAction, setExecutingAction] = useState<number | null>(null);
  const [conversationId, setConversationId] = useState<string>(() => 'conv_' + Math.random().toString(36).substring(2, 9));
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'bot',
      text: "👋 **Welcome to BHUMI Copilot.**\n\nI am your decision-support AI assistant. Ask me anything about project delay risks, critical land parcels, dispute litigation, compensation backlogs, or policy procedures.",
      provider: 'local_fallback',
      grounded: true,
      sources: ['BHUMI-AI Knowledge Core'],
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (open) scrollToBottom();
  }, [messages, open]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const newMsg: Message = {
      sender: 'user',
      text: query,
      timestamp: timeStr,
    };

    setMessages(prev => [...prev, newMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.copilot(query, projectId, 'en', conversationId, parcelId);
      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          text: res.answer || res.response || "No response received.",
          provider: res.provider,
          grounded: res.grounded,
          sources: res.sources || [],
          suggestedAction: res.suggested_action,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } catch (err: any) {
      setMessages(prev => [
        ...prev,
        {
          sender: 'bot',
          text: "⚠️ **Service Notice**: I encountered a temporary connection issue reaching the AI orchestration service. Your local database records remain completely intact. Please try again or rephrase your question.",
          provider: 'local_fallback',
          grounded: false,
          sources: [],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteAction = async (msgIndex: number, action: any) => {
    setExecutingAction(msgIndex);
    try {
      const res = await api.executeRecommendation({
        project_id: projectId || '12345678-1234-5678-1234-567812345678',
        recommendation_title: action.title,
        action_type: action.action_type || 'verify_field',
      });
      setMessages(prev =>
        prev.map((m, idx) =>
          idx === msgIndex
            ? {
                ...m,
                actionExecuted: true,
                actionResult: `✅ Workflow Task Created: "${res.title}" (Task ID: ${res.task_id.substring(0, 8)}...). Dispatched to Field Officer queue & logged in Audit Trail.`,
              }
            : m
        )
      );
    } catch (err: any) {
      setMessages(prev =>
        prev.map((m, idx) =>
          idx === msgIndex
            ? { ...m, actionResult: '❌ Could not create task: Insufficient permissions or server error.' }
            : m
        )
      );
    } finally {
      setExecutingAction(null);
    }
  };

  const handleClearChat = () => {
    setConversationId('conv_' + Math.random().toString(36).substring(2, 9));
    setMessages([
      {
        sender: 'bot',
        text: "✨ **Conversation reset.**\n\nHow can I assist your land acquisition monitoring or decision-making right now?",
        provider: 'local_fallback',
        grounded: true,
        sources: ['BHUMI-AI Knowledge Core'],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  const starterChips = [
    "🚨 Why is this project delayed?",
    "⚖️ Which disputes are blocking possession?",
    "🔬 What if we resolve 4 disputes?",
    "📋 Give me today's executive briefing",
  ];

  return (
    <>
      {/* FLOATING TRIGGER BUTTON */}
      <button
        onClick={() => setOpen(!open)}
        className="copilot-floating-btn"
        style={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          zIndex: 999,
          background: 'linear-gradient(135deg, #1B6CA8 0%, #14527E 100%)',
          color: '#FFFFFF',
          border: 'none',
          borderRadius: 50,
          padding: '12px 22px',
          boxShadow: '0 8px 24px rgba(27, 108, 168, 0.45)',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          fontWeight: 700,
          fontSize: 14,
          cursor: 'pointer',
          transition: 'all 0.2s ease',
        }}
        title="Open BHUMI Intelligent Decision Copilot"
      >
        <span style={{ fontSize: 18 }}>🤖</span>
        <span>BHUMI Copilot</span>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#2ECC71', display: 'inline-block' }} />
      </button>

      {/* CHAT DRAWER PANEL */}
      {open && (
        <div
          style={{
            position: 'fixed',
            bottom: 84,
            right: 24,
            width: 440,
            maxWidth: 'calc(100vw - 32px)',
            height: 600,
            maxHeight: 'calc(100vh - 120px)',
            background: '#FFFFFF',
            borderRadius: 18,
            boxShadow: '0 16px 48px rgba(0, 0, 0, 0.22), 0 0 1px rgba(0, 0, 0, 0.1)',
            border: '1px solid #E2E8F0',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
          }}
        >
          {/* HEADER */}
          <div
            style={{
              background: 'linear-gradient(135deg, #1B3A4B 0%, #152F3D 100%)',
              color: '#FFFFFF',
              padding: '14px 18px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <div>
              <div style={{ fontWeight: 700, fontSize: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>🌱</span>
                <span>BHUMI AI Copilot</span>
                <span
                  style={{
                    fontSize: 10,
                    background: 'rgba(46, 204, 113, 0.2)',
                    color: '#2ECC71',
                    border: '1px solid #2ECC71',
                    borderRadius: 12,
                    padding: '1px 7px',
                    fontWeight: 600,
                  }}
                >
                  ONLINE
                </span>
              </div>
              <div style={{ fontSize: 11, color: '#C8DDE6', marginTop: 2 }}>
                Intelligent Decision Support & Database Grounding
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <button
                onClick={handleClearChat}
                title="Start new conversation"
                style={{
                  background: 'rgba(255, 255, 255, 0.12)',
                  border: 'none',
                  color: '#FFFFFF',
                  borderRadius: 6,
                  padding: '4px 8px',
                  fontSize: 11,
                  cursor: 'pointer',
                  fontWeight: 600,
                }}
              >
                🔄 New Chat
              </button>
              <button
                onClick={() => setOpen(false)}
                title="Close chat"
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#FFFFFF',
                  cursor: 'pointer',
                  fontSize: 18,
                  lineHeight: 1,
                  padding: 4,
                }}
              >
                ✕
              </button>
            </div>
          </div>

          {/* MESSAGES FEED */}
          <div
            style={{
              flex: 1,
              padding: 16,
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
              background: '#F8FAFC',
            }}
          >
            {messages.map((m, i) => (
              <div
                key={i}
                style={{
                  alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '90%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}
              >
                {/* Bubble */}
                <div
                  style={{
                    background: m.sender === 'user' ? '#1B6CA8' : '#FFFFFF',
                    color: m.sender === 'user' ? '#FFFFFF' : '#1E293B',
                    padding: '12px 16px',
                    borderRadius: m.sender === 'user' ? '16px 16px 2px 16px' : '16px 16px 16px 2px',
                    fontSize: 13,
                    lineHeight: 1.6,
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
                    border: m.sender === 'user' ? 'none' : '1px solid #E2E8F0',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {m.text}
                </div>

                {/* Metadata & Sources */}
                {m.sender === 'bot' && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 6, paddingLeft: 4 }}>
                    {/* Provider Tag */}
                    <span
                      style={{
                        fontSize: 10,
                        padding: '1px 6px',
                        borderRadius: 4,
                        fontWeight: 600,
                        background: m.provider === 'gemini' ? '#EBF5FC' : '#FEF3E2',
                        color: m.provider === 'gemini' ? '#1B6CA8' : '#D35400',
                        border: m.provider === 'gemini' ? '1px solid #BEE3F8' : '1px solid #FBD38D',
                      }}
                    >
                      {m.provider === 'gemini' ? '✨ Gemini AI' : '🏛️ BHUMI Local Intelligence'}
                    </span>

                    {/* Grounded Indicator */}
                    {m.grounded && (
                      <span style={{ fontSize: 10, color: '#27AE60', fontWeight: 600 }}>
                        ✓ Grounded in DB
                      </span>
                    )}

                    {/* Timestamp */}
                    <span style={{ fontSize: 10, color: '#94A3B8', marginLeft: 'auto' }}>
                      {m.timestamp}
                    </span>
                  </div>
                )}

                {/* Sources Pill Row */}
                {m.sender === 'bot' && m.sources && m.sources.length > 0 && (
                  <div style={{ fontSize: 10, color: '#64748B', display: 'flex', flexWrap: 'wrap', gap: 4, paddingLeft: 4 }}>
                    <span style={{ fontWeight: 600 }}>Sources:</span>
                    {m.sources.map((s, sIdx) => (
                      <span
                        key={sIdx}
                        style={{
                          background: '#EDF2F7',
                          borderRadius: 4,
                          padding: '1px 5px',
                        }}
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                )}

                {/* Action Recommendation Button */}
                {m.sender === 'bot' && m.suggestedAction && !m.actionExecuted && (
                  <div style={{ marginTop: 6, paddingLeft: 4 }}>
                    <button
                      onClick={() => handleExecuteAction(i, m.suggestedAction)}
                      disabled={executingAction === i}
                      style={{
                        background: 'linear-gradient(135deg, #E67E22, #D35400)',
                        color: '#FFFFFF',
                        border: 'none',
                        borderRadius: 8,
                        padding: '8px 14px',
                        fontSize: 12,
                        fontWeight: 700,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        boxShadow: '0 2px 8px rgba(230, 126, 34, 0.3)',
                      }}
                    >
                      <span>⚡</span>
                      <span>{executingAction === i ? 'Creating Task...' : m.suggestedAction.button_text || 'Create Action Task'}</span>
                    </button>
                  </div>
                )}

                {/* Action Result Message */}
                {m.actionResult && (
                  <div
                    style={{
                      fontSize: 11,
                      color: m.actionResult.startsWith('✅') ? '#27AE60' : '#E74C3C',
                      background: m.actionResult.startsWith('✅') ? '#E8F8EF' : '#FDECEA',
                      padding: '6px 10px',
                      borderRadius: 6,
                      fontWeight: 600,
                      marginTop: 4,
                    }}
                  >
                    {m.actionResult}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#64748B', fontSize: 12, paddingLeft: 8 }}>
                <div className="spinner" style={{ width: 14, height: 14 }} />
                <span>BHUMI Copilot is analyzing database context...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* STARTER CHIPS (Visible only on initial turn) */}
          {messages.length === 1 && (
            <div style={{ padding: '8px 14px', background: '#F1F5F9', borderTop: '1px solid #E2E8F0', display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ fontSize: 11, color: '#64748B', fontWeight: 600 }}>Suggested prompts:</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {starterChips.map((chip, cIdx) => (
                  <button
                    key={cIdx}
                    onClick={() => handleSend(chip)}
                    style={{
                      background: '#FFFFFF',
                      border: '1px solid #CBD5E1',
                      borderRadius: 14,
                      padding: '4px 10px',
                      fontSize: 11,
                      color: '#1E293B',
                      cursor: 'pointer',
                      textAlign: 'left',
                      fontWeight: 500,
                      transition: 'background 0.15s',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = '#E2E8F0')}
                    onMouseLeave={e => (e.currentTarget.style.background = '#FFFFFF')}
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* INPUT BAR */}
          <div
            style={{
              padding: '12px 14px',
              borderTop: '1px solid #E2E8F0',
              background: '#FFFFFF',
              display: 'flex',
              gap: 8,
              alignItems: 'flex-end',
            }}
          >
            <textarea
              style={{
                flex: 1,
                fontSize: 13,
                borderRadius: 10,
                border: '1px solid #CBD5E1',
                padding: '8px 12px',
                resize: 'none',
                minHeight: 38,
                maxHeight: 100,
                outline: 'none',
                fontFamily: 'inherit',
                lineHeight: 1.4,
              }}
              placeholder="Ask anything about land, disputes, risk or R&R... (Enter to send)"
              value={input}
              rows={1}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <button
              className="btn btn-primary"
              style={{ padding: '8px 16px', height: 38, borderRadius: 10, fontWeight: 700 }}
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
            >
              Send ↵
            </button>
          </div>
        </div>
      )}
    </>
  );
}
