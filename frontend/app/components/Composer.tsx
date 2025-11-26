'use client';

import { useState } from 'react';

export default function Composer({
  onSend,
  disabled
}: {
  onSend: (text: string) => void;
  disabled?: boolean;
}) {
  const [text, setText] = useState('');

  const submit = () => {
    const t = text.trim();
    if (!t) return;
    onSend(t);
    setText('');
  };

  return (
    <div className="composer">
      <input
        className="input"
        placeholder="Type a message…"
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={e => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        disabled={disabled}
      />
      <button className="send" onClick={submit} disabled={disabled || !text.trim()}>
        Send
      </button>
    </div>
  );
}
