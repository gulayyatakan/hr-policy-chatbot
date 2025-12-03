const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Our backend doesn't need chat IDs, but the React code expects createChat()
// to return an object with an `id`, so we just return a dummy one.
async function createChat() {
  return { id: 'local' };
}

// Sends a user message to the streaming endpoint of your FastAPI backend.
// `chatId` is ignored, but we keep it in the signature so the rest of the
// frontend code doesn't have to change.
async function sendChatMessage(chatId, message) {
  const res = await fetch(`${BASE_URL}/chat-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: message })
  });

  if (!res.ok || !res.body) {
    // Try to read error body as text for debugging
    const errorText = await res.text().catch(() => null);
    return Promise.reject({ status: res.status, data: errorText });
  }

  // Frontend's parseSSEStream expects a ReadableStream
  return res.body;
}

export default {
  createChat,
  sendChatMessage
};