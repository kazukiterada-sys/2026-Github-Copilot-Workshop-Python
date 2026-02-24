"""WebSocket ハンドラ — ブラウザと CLI Bridge のメッセージルーティング"""
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from cli_bridge import CLIBridge

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """単一 WebSocket セッションを管理するハンドラ"""

    def __init__(self, websocket: WebSocket) -> None:
        self._ws = websocket
        self._bridge = CLIBridge()

    async def run(self) -> None:
        """WebSocket セッションのメインループ"""
        await self._ws.accept()
        logger.info("WebSocket: 接続確立")
        try:
            while True:
                raw = await self._ws.receive_text()
                await self._handle_message(raw)
        except WebSocketDisconnect:
            logger.info("WebSocket: クライアント切断")
        except Exception as exc:
            logger.error("WebSocket エラー: %s", exc)
        finally:
            if self._bridge.is_running:
                await self._bridge.stop()

    # ───────────────────────────────────────────────────────────
    # プライベートメソッド
    # ───────────────────────────────────────────────────────────

    async def _handle_message(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("不正な JSON: %s", raw)
            return

        msg_type = msg.get("type")

        if msg_type == "input":
            await self._on_input(msg.get("payload", ""))

        elif msg_type == "resize":
            cols = int(msg.get("cols", 80))
            rows = int(msg.get("rows", 24))
            self._bridge.resize(cols, rows)

        elif msg_type == "session":
            action = msg.get("action")
            if action == "start":
                cols = int(msg.get("cols", 120))
                rows = int(msg.get("rows", 40))
                await self._on_session_start(cols, rows)
            elif action == "stop":
                await self._on_session_stop()

        else:
            logger.warning("未知のメッセージタイプ: %s", msg_type)

    async def _on_input(self, payload: str) -> None:
        if self._bridge.is_running:
            try:
                self._bridge.send_input(payload)
            except RuntimeError as exc:
                logger.error("入力送信エラー: %s", exc)

    async def _on_session_start(self, cols: int, rows: int) -> None:
        if self._bridge.is_running:
            await self._send_status("すでにセッションが実行中です", "running")
            return
        try:
            await self._bridge.start(
                output_callback=self._on_cli_output,
                cols=cols,
                rows=rows,
            )
            await self._send_status("セッションを開始しました", "running")
        except RuntimeError as exc:
            logger.error("セッション起動エラー: %s", exc)
            await self._send_status(str(exc), "error")

    async def _on_session_stop(self) -> None:
        await self._bridge.stop()
        await self._send_status("セッションを停止しました", "stopped")

    async def _on_cli_output(self, data: str) -> None:
        """CLI からの出力をブラウザへ転送する。"""
        try:
            await self._ws.send_text(
                json.dumps({"type": "output", "payload": data})
            )
        except Exception as exc:
            logger.error("出力送信エラー: %s", exc)

    async def _send_status(self, message: str, state: str) -> None:
        try:
            await self._ws.send_text(
                json.dumps({"type": "status", "payload": message, "state": state})
            )
        except Exception as exc:
            logger.error("ステータス送信エラー: %s", exc)
