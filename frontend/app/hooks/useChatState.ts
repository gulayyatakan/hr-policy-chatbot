'use client';

import { useCallback, useMemo, useState } from 'react';
import type { Message } from '../../lib/types';
import { uid } from '../../lib/uid';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export function useChatState() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: uid(),
      role: 'bot',
      text: 'Hi, I can answer questions about HR policies.',
      timestamp: Date.now()
    }
  ]);
  const [pending, setPending] = useState(false);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;

      const userMsg: Message = {
        id: uid(),
        role: 'user',
        text: trimmed,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, userMsg]);
      setPending(true);

      try {
        const res = await fetch(`${API_BASE}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: trimmed })
        });

        if (!res.ok) {
          throw new Error(`Backend returned ${res.status}`);
        }

        const data = await res.json() as {
          answer: string;
          // matches what the backend sends: "source"
          sources?: { source: string; chunk_index: number }[];
        };

        // Build a readable answer with sources
        const sourceLines =
          data.sources && data.sources.length
            ? '\n\nSources:\n' +
              data.sources
                .map(
                  s =>
                    `- ${s.source} (chunk ${s.chunk_index})`
                )
                .join('\n')
            : '';

        const botMsg: Message = {
          id: uid(),
          role: 'bot',
          text: data.answer + sourceLines,
          timestamp: Date.now()
        };

        setMessages(prev => [...prev, botMsg]);
      } catch (err) {
        console.error('Chat error', err);
        const botMsg: Message = {
          id: uid(),
          role: 'bot',
          text:
            'Sorry, something went wrong talking to the backend.',
          timestamp: Date.now()
        };
        setMessages(prev => [...prev, botMsg]);
      } finally {
        setPending(false);
      }
    },
    []
  );

  return useMemo(
    () => ({ messages, sendMessage, pending }),
    [messages, sendMessage, pending]
  );
}