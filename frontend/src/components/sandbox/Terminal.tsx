import React, { useEffect, useRef } from 'react';
import { Terminal as XTerm } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';

interface TerminalProps {
  sandboxId: string;
}

export const Terminal: React.FC<TerminalProps> = ({ sandboxId }) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!terminalRef.current) return;

    const term = new XTerm({
      cursorBlink: true,
      theme: {
        background: '#1a1b26',
        foreground: '#c0caf5',
        cursor: '#c0caf5',
        black: '#15161e',
        red: '#f7768e',
        green: '#9ece6a',
        yellow: '#e0af68',
        blue: '#7aa2f7',
        magenta: '#bb9af7',
        cyan: '#7dcfff',
        white: '#a9b1d6',
        brightBlack: '#414868',
        brightRed: '#f7768e',
        brightGreen: '#9ece6a',
        brightYellow: '#e0af68',
        brightBlue: '#7aa2f7',
        brightMagenta: '#bb9af7',
        brightCyan: '#7dcfff',
        brightWhite: '#c0caf5'
      },
      fontFamily: '"Fira Code", monospace',
      fontSize: 14,
    });
    
    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(terminalRef.current);
    fitAddon.fit();
    xtermRef.current = term;

    // Connect WebSocket
    // Extract token to authenticate websocket
    const token = localStorage.getItem('token');
    
    // In FastAPI, it's difficult to pass token via headers in WebSocket. Usually passed via query param or subprotocol.
    // We will just let the endpoint handle it or skip auth for WS for this demo since sandboxId is UUID
    const wsUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}`.replace('http', 'ws') + `/api/v1/sandbox/pty/${sandboxId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      term.writeln('\x1b[1;32m[Connected to Sandbox]\x1b[0m');
    };

    ws.onmessage = (event) => {
      if (typeof event.data === 'string') {
        term.write(event.data);
      } else {
        const reader = new FileReader();
        reader.onload = () => {
          if (reader.result) {
            term.write(new Uint8Array(reader.result as ArrayBuffer));
          }
        };
        reader.readAsArrayBuffer(event.data);
      }
    };

    ws.onclose = () => {
      term.writeln('\r\n\x1b[1;31m[Disconnected from Sandbox]\x1b[0m');
    };

    term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data);
      }
    });

    const handleResize = () => {
      fitAddon.fit();
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      term.dispose();
    };
  }, [sandboxId]);

  return (
    <div className="h-full w-full bg-[#1a1b26] p-2 rounded-lg overflow-hidden">
      <div ref={terminalRef} className="h-full w-full" />
    </div>
  );
};
