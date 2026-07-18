import React, { useState, useRef, useEffect } from 'react';
import ChatBubble from './ChatBubble';
import { api } from '../api';

const SUGGESTIONS = [
  'Where is Gate A?',
  'Where can I find food near Section 101?',
  'Is there step-free access to my seat?',
  'Where is the nearest medical station?',
  'Where are the restrooms?',
];

/**
 * FanPortal component representing the visitor-facing platform dashboard.
 * Supports trilingual Q&A and accessible zone monitoring.
 *
 * @param {Object} props
 * @param {Array.<Object>} props.zones - List of all zones.
 * @returns {React.ReactElement} The rendered FanPortal component.
 */
export default function FanPortal({ zones }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      answer_en: "Hi! I'm your ArenaIQ assistant for FIFA World Cup 2026. Ask me about directions, food, medical stations, or facilities — in English, Spanish, or Arabic!",
      answer_es: '¡Hola! Soy tu asistente ArenaIQ para el Mundial FIFA 2026. Pregúntame sobre direcciones, comida, estaciones médicas o instalaciones.',
      answer_ar: 'مرحباً! أنا مساعد ArenaIQ الخاص بك لكأس العالم FIFA 2026. اسألني عن الاتجاهات والطعام والمحطات الطبية والمرافق.',
      lang: 'en',
      used_ai: false,
      confidence: 1,
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lang, setLang] = useState('en');
  const [err, setErr] = useState('');
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /**
   * Sends user query to the Fan Assistant backend endpoint.
   *
   * @param {string} [text] - Optional quick suggestion query text.
   */
  const send = async (text) => {
    const q = (text || input).trim();
    if (!q) return;
    setErr('');
    setInput('');
    setLoading(true);
    setMessages(m => [...m, { role: 'user', text: q }]);
    try {
      const res = await api.askFan(q);
      setMessages(m => [...m, { role: 'assistant', ...res, lang }]);
    } catch (e) {
      if (e.status === 422) {
        setErr('Your message was rejected: ' + (e.data?.detail || 'invalid input'));
        setMessages(m => m.slice(0, -1));
      } else {
        setErr(e.message || 'Failed to get response');
      }
    } finally {
      setLoading(false);
    }
  };

  const accessibleZones = (zones || []).filter(z => z.is_step_free || z.is_low_noise);

  return (
    <div className="fan-shell">
      {/* Chat */}
      <div className="fan-chat" aria-label="Fan assistant chat">
        <div style={{ padding: '.65rem .75rem', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ fontWeight: 700, fontSize: '.9rem' }}>🏟 Fan Assistant</div>
          <div className="lang-tabs" style={{ padding: 0 }}>
            {['en', 'es', 'ar'].map(l => (
              <button
                key={l}
                className={`lang-tab${lang === l ? ' active' : ''}`}
                onClick={() => setLang(l)}
                aria-pressed={lang === l}
                aria-label={`Switch to ${l === 'en' ? 'English' : l === 'es' ? 'Spanish' : 'Arabic'}`}
                id={`lang-tab-${l}`}
              >
                {l === 'en' ? '🇬🇧 EN' : l === 'es' ? '🇪🇸 ES' : '🇸🇦 AR'}
              </button>
            ))}
          </div>
        </div>

        <div className="chat-messages" role="log" aria-live="polite" aria-label="Chat conversation">
          {messages.map((m, i) => <ChatBubble key={i} msg={{ ...m, lang }} />)}
          {loading && (
            <div className="chat-bubble assistant">
              <span className="spinner" aria-label="Thinking…" />
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {err && <p className="form-error" role="alert" style={{ padding: '0 .75rem .5rem' }}>⚠ {err}</p>}

        {/* Quick suggestions */}
        {messages.length < 3 && (
          <div style={{ padding: '.5rem .75rem', display: 'flex', flexWrap: 'wrap', gap: '.35rem' }}>
            {SUGGESTIONS.map((s, i) => (
              <button
                key={i}
                className="btn btn-secondary btn-sm"
                onClick={() => send(s)}
                aria-label={`Quick question: ${s}`}
                id={`suggestion-${i}`}
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <div className="chat-input-row">
          <input
            id="fan-chat-input"
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            placeholder={lang === 'ar' ? 'اكتب سؤالك هنا…' : lang === 'es' ? 'Escribe tu pregunta…' : 'Ask anything about the stadium…'}
            dir={lang === 'ar' ? 'rtl' : 'ltr'}
            aria-label="Type your question"
            disabled={loading}
          />
          <button
            id="fan-send-btn"
            className="btn btn-primary"
            onClick={() => send()}
            disabled={loading || !input.trim()}
            aria-label="Send message"
          >
            Send
          </button>
        </div>
      </div>

      {/* Accessibility info panel */}
      <div>
        <div className="card" style={{ marginBottom: '1rem' }}>
          <div className="card-header">
            <h3 className="card-title">♿ Accessible Zones</h3>
            <span className="badge badge-open">{accessibleZones.length}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '.5rem' }}>
            {accessibleZones.map(z => (
              <div key={z.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '.45rem .6rem', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '.84rem' }}>{z.name}</div>
                  <div style={{ fontSize: '.73rem', color: 'var(--text-secondary)' }}>
                    {z.is_step_free && '♿ Step-free  '}
                    {z.is_low_noise && '🔇 Low noise'}
                  </div>
                </div>
                <span className={`badge badge-${z.color_state === 'green' ? 'green' : z.color_state === 'yellow' ? 'medium' : z.color_state === 'red' ? 'high' : 'critical'}`}>
                  {Math.round((z.density_pct || 0) * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">ℹ️ Stadium Info</h3>
          </div>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '.55rem' }}>
            {[
              ['🚪 Gates A & B', 'North side — step-free access'],
              ['🚪 Gates C & D', 'South side'],
              ['🍔 Food kiosks', 'North & South Concourses'],
              ['🏥 Medical', 'Near Sections 101 & 110'],
              ['🅿️ Parking', 'P1 (east), P2 (west)'],
              ['🟠 Volunteers', '5 posts throughout stadium'],
            ].map(([label, desc]) => (
              <li key={label} style={{ display: 'flex', gap: '.5rem', fontSize: '.82rem' }}>
                <span style={{ fontWeight: 600, minWidth: 120 }}>{label}</span>
                <span style={{ color: 'var(--text-secondary)' }}>{desc}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
