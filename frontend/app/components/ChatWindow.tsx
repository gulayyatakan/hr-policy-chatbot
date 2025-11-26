'use client';

import MessageBubble from './MessageBubble';
import type { Message } from '../../lib/types';
import { useEffect, useRef } from 'react';

export default function ChatWindow({ messages }: { messages: Message[] }) {
  const endRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => endRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages]);

  return (
    <div className="window">
      {messages.map(m => (
        <MessageBubble key={m.id} message={m} />
      ))}
      <div ref={endRef} />
    </div>
  );
}
