import React from 'react';

/**
 * @typedef {Object} ChatMessage
 * @property {string} role - Message sender role ('user' or 'assistant').
 * @property {string} [text] - Direct text content.
 * @property {string} [answer_en] - English answer.
 * @property {string} [answer_es] - Spanish answer.
 * @property {string} [answer_ar] - Arabic answer.
 * @property {string} [lang] - Display language.
 * @property {boolean} [used_ai] - Flag indicating whether GenAI responded.
 * @property {number} [confidence] - Agent confidence score.
 */

/**
 * ChatBubble component representing a message exchange in the portal.
 * Handles right-to-left layout for Arabic text.
 *
 * @param {Object} props
 * @param {ChatMessage} props.msg - Message details.
 * @returns {React.ReactElement} The chat bubble.
 */
export default function ChatBubble({ msg }) {
  if (msg.role === 'user') {
    return <div className="chat-bubble user">{msg.text}</div>;
  }

  const lang = msg.lang || 'en';
  const text = msg[`answer_${lang}`] || msg.answer_en || msg.text;
  const isAr = lang === 'ar';

  return (
    <div
      className={`chat-bubble assistant${isAr ? ' ar' : ''}`}
      dir={isAr ? 'rtl' : 'ltr'}
      lang={lang}
    >
      {text}
      {msg.used_ai !== undefined && (
        <div style={{ marginTop: '.35rem', fontSize: '.7rem', opacity: 0.6 }}>
          {msg.used_ai ? '✨ Gemini AI' : '📋 Fallback'}
          {msg.confidence !== undefined && ` · ${Math.round(msg.confidence * 100)}% confidence`}
        </div>
      )}
    </div>
  );
}
