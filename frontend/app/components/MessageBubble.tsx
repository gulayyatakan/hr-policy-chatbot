'use client';

import type { Message } from '../../lib/types';
import { format } from '../../lib/time';

export default function MessageBubble({ message }: { message: Message }) {
  const mine = message.role === 'user';
  return (
    <div className={`row ${mine ? 'right' : 'left'}`}>
      <div className={`bubble ${mine ? 'mine' : 'theirs'}`}>
        <div className="text">{message.text}</div>
        <div className="meta">{format(message.timestamp)}</div>
      </div>
    </div>
  );
}
