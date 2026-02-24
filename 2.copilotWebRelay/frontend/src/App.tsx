/**
 * App.tsx — メインアプリ
 * ターミナル UI + WebSocket 接続 + セッション管理
 */
import { useEffect, useRef, useCallback } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';
import './App.css';

// ─── WebSocket メッセージ型 ────────────────────────────────────────────────

type ServerMessage =
  | { type: 'output'; payload: string }
  | { type: 'status'; payload: string; state: 'running' | 'stopped' | 'error' };

type ClientMessage =
  | { type: 'input'; payload: string }
  | { type: 'resize'; cols: number; rows: number }
  | { type: 'session'; action: 'start' | 'stop'; cols?: number; rows?: number };

// ─── 接続状態型 ───────────────────────────────────────────────────────────

type ConnectState = 'disconnected' | 'connected' | 'error';
type SessionState = 'running' | 'stopped' | 'error';

const WS_URL = '/ws';

function App() {
  const termRef       = useRef<HTMLDivElement>(null);
  const terminalRef   = useRef<Terminal | null>(null);
  const fitAddonRef   = useRef<FitAddon | null>(null);
  const wsRef         = useRef<WebSocket | null>(null);
  const connectRef    = useRef<ConnectState>('disconnected');
  const sessionRef    = useRef<SessionState>('stopped');

  // ─── UI 状態（DOM を直接更新して再レンダーを回避） ──────────────────────

  const setStatusDot = useCallback((state: ConnectState) => {
    connectRef.current = state;
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    if (!dot || !text) return;
    dot.className = `status-dot ${state}`;
    const labels: Record<ConnectState, string> = {
      connected: '接続済み',
      disconnected: '未接続',
      error: '接続エラー',
    };
    text.textContent = labels[state];
  }, []);

  const setSessionButtons = useCallback((session: SessionState) => {
    sessionRef.current = session;
    const startBtn = document.getElementById('btn-start') as HTMLButtonElement | null;
    const stopBtn  = document.getElementById('btn-stop')  as HTMLButtonElement | null;
    if (!startBtn || !stopBtn) return;
    startBtn.disabled = session === 'running';
    stopBtn.disabled  = session !== 'running';
  }, []);

  // ─── WebSocket 送信ヘルパー ──────────────────────────────────────────────

  const send = useCallback((msg: ClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  // ─── WebSocket 接続 ───────────────────────────────────────────────────────

  const connectWS = useCallback(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      if (wsRef.current !== ws) return;
      setStatusDot('connected');
      terminalRef.current?.writeln('\r\n\x1b[32m[Relay] サーバーに接続しました\x1b[0m\r\n');
    };

    ws.onmessage = (ev) => {
      try {
        const msg: ServerMessage = JSON.parse(ev.data as string);
        if (msg.type === 'output') {
          terminalRef.current?.write(msg.payload);
        } else if (msg.type === 'status') {
          const color = msg.state === 'running' ? '32' : msg.state === 'error' ? '31' : '33';
          terminalRef.current?.writeln(`\r\n\x1b[${color}m[Relay] ${msg.payload}\x1b[0m\r\n`);
          setSessionButtons(msg.state);
        }
      } catch {
        /* ignore malformed messages */
      }
    };

    ws.onerror = () => {
      if (wsRef.current !== ws) return;
      setStatusDot('error');
    };

    ws.onclose = () => {
      if (wsRef.current !== ws) return;
      setStatusDot('disconnected');
      setSessionButtons('stopped');
      wsRef.current = null;
      // 3 秒後に再接続
      setTimeout(connectWS, 3000);
    };
  }, [setStatusDot, setSessionButtons]);

  // ─── セッション操作 ───────────────────────────────────────────────────────

  const startSession = useCallback(() => {
    const term = terminalRef.current;
    if (!term) return;
    send({
      type: 'session',
      action: 'start',
      cols: term.cols,
      rows: term.rows,
    });
  }, [send]);

  const stopSession = useCallback(() => {
    send({ type: 'session', action: 'stop' });
  }, [send]);

  // ─── 初期化 ───────────────────────────────────────────────────────────────

  useEffect(() => {
    if (!termRef.current) return;

    // xterm.js 初期化
    const terminal = new Terminal({
      theme: {
        background: '#11111b',
        foreground: '#cdd6f4',
        cursor: '#f5c2e7',
        selectionBackground: '#585b70',
        black: '#45475a',
        red: '#f38ba8',
        green: '#a6e3a1',
        yellow: '#f9e2af',
        blue: '#89b4fa',
        magenta: '#cba6f7',
        cyan: '#89dceb',
        white: '#bac2de',
        brightBlack: '#585b70',
        brightRed: '#f38ba8',
        brightGreen: '#a6e3a1',
        brightYellow: '#f9e2af',
        brightBlue: '#89b4fa',
        brightMagenta: '#cba6f7',
        brightCyan: '#89dceb',
        brightWhite: '#a6adc8',
      },
      fontFamily: "'JetBrains Mono', 'Cascadia Code', 'Fira Code', monospace",
      fontSize: 14,
      lineHeight: 1.3,
      cursorBlink: true,
    });

    const fitAddon = new FitAddon();
    terminal.loadAddon(fitAddon);
    terminal.open(termRef.current);
    fitAddon.fit();
    terminalRef.current = terminal;
    fitAddonRef.current = fitAddon;

    terminal.writeln('\x1b[35m  Copilot Web Relay — ターミナル\x1b[0m');
    terminal.writeln('\x1b[90m  「Start Session」でセッションを開始してください\x1b[0m\r\n');

    // キー入力を WebSocket へ転送
    terminal.onData((data) => {
      send({ type: 'input', payload: data });
    });

    // リサイズ
    const observer = new ResizeObserver(() => {
      fitAddon.fit();
      send({ type: 'resize', cols: terminal.cols, rows: terminal.rows });
    });
    if (termRef.current.parentElement) {
      observer.observe(termRef.current.parentElement);
    }

    // WebSocket 接続
    connectWS();

    return () => {
      observer.disconnect();
      terminal.dispose();
      wsRef.current?.close();
    };
  }, [connectWS, send]);

  // ─── レンダー ─────────────────────────────────────────────────────────────

  return (
    <div className="app">
      <div className="toolbar">
        <h1>🤖 Copilot Web Relay</h1>

        <div className="status-indicator">
          <span id="status-dot" className="status-dot disconnected" />
          <span id="status-text" className="status-text">未接続</span>
        </div>

        <button
          id="btn-start"
          className="btn btn-start"
          onClick={startSession}
        >
          Start Session
        </button>
        <button
          id="btn-stop"
          className="btn btn-stop"
          disabled
          onClick={stopSession}
        >
          Stop Session
        </button>
      </div>

      <div className="terminal-container" ref={termRef} />
    </div>
  );
}

export default App;
