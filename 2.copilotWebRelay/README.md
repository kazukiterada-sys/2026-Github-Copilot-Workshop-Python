# Copilot Web Relay

ローカルで動作する GitHub Copilot CLI をブラウザからアクセス可能にする Web アプリケーションです。

## アーキテクチャ

```
Browser (React/TS)  ◄── WebSocket ──►  Backend (FastAPI)  ◄── PTY ──►  Copilot CLI
```

## ディレクトリ構成

```
2.copilotWebRelay/
├── backend/
│   ├── main.py              # FastAPI エントリポイント
│   ├── cli_bridge.py        # Copilot CLI PTY 制御
│   ├── websocket_handler.py # WebSocket メッセージルーティング
│   ├── config.py            # 設定
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # メインアプリ
│   │   ├── App.css
│   │   ├── main.tsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── e2e/
│   ├── tests/
│   │   └── start-session.spec.ts
│   ├── playwright.config.ts
│   └── package.json
├── docs/
│   └── planning.md
└── README.md
```

## セットアップ & 起動方法

### 前提条件

- Python 3.10+
- Node.js 18+
- `copilot` CLI がインストール済み・認証済みであること

### Backend

```bash
cd 2.copilotWebRelay/backend
pip install -r requirements.txt
python main.py
# → http://localhost:8000 で起動
```

### Frontend

```bash
cd 2.copilotWebRelay/frontend
npm install
npm run dev
# → http://localhost:5173 で起動
```

### E2E テスト

```bash
# バックエンドとフロントエンドを起動した状態で
cd 2.copilotWebRelay/e2e
npm install
npx playwright install chromium
npm test
```

## WebSocket プロトコル

### クライアント → サーバー

```json
{ "type": "input",  "payload": "string" }
{ "type": "resize", "cols": 80, "rows": 24 }
{ "type": "session", "action": "start", "cols": 120, "rows": 40 }
{ "type": "session", "action": "stop" }
```

### サーバー → クライアント

```json
{ "type": "output", "payload": "string" }
{ "type": "status", "payload": "メッセージ", "state": "running | stopped | error" }
```

## 実装フェーズ

- **Phase 1 (MVP)**: ターミナルエミュレータ + WebSocket ブリッジ ✅
- **Phase 2**: チャット UI + Markdown レンダリング + セッション管理
- **Phase 3**: 認証・セキュリティ + ファイル連携 + UI/UX 改善

詳細は [`docs/planning.md`](docs/planning.md) を参照してください。
