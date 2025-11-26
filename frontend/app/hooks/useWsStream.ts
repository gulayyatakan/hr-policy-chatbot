'use client';

import { useEffect, useRef, useState } from 'react';

export function useWsStream(url?: string) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!url) return; // no backend yet
    const ws = new WebSocket(url);
    wsRef.current = ws;

    const onOpen = () => setConnected(true);
    const onClose = () => setConnected(false);

    ws.addEventListener('open', onOpen);
    ws.addEventListener('close', onClose);

    // Example: log messages (you can wire to state here if needed)
    ws.addEventListener('message', evt => {
      // console.log('WS message:', evt.data);
    });

    return () => {
      ws.removeEventListener('open', onOpen);
      ws.removeEventListener('close', onClose);
      try { ws.close(); } catch {}
      wsRef.current = null;
    };
  }, [url]);

  const send = (payload: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return false;
    wsRef.current.send(payload);
    return true;
    // you can extend to support binary etc.
  };

  return { connected, send };
}
