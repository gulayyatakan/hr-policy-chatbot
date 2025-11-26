'use client';

import ChatWindow from './components/ChatWindow';
import Composer from './components/Composer';
import { useChatState } from './hooks/useChatState';

export default function ChatPage() {
  const { messages, sendMessage, pending } = useChatState();

  return (
    <main className="page">
      <section className="chat-card">
        <header className="chat-header">
          <h1>Chat</h1>
        </header>

        <ChatWindow messages={messages} />

        <footer className="composer-wrap">
          <Composer onSend={sendMessage} disabled={pending} />
        </footer>
      </section>
    </main>
  );
}
