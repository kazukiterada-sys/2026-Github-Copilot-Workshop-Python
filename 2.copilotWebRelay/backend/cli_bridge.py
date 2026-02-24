"""Copilot CLI Bridge — PTY を使った CLI プロセス管理"""
import asyncio
import logging
from typing import Callable, Awaitable

import pexpect

from config import config

logger = logging.getLogger(__name__)


class CLIBridge:
    """Copilot CLI プロセスを PTY 経由で管理するクラス"""

    def __init__(self) -> None:
        self._proc: pexpect.spawn | None = None
        self._read_task: asyncio.Task | None = None
        self._output_callback: Callable[[str], Awaitable[None]] | None = None

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.isalive()

    async def start(
        self,
        output_callback: Callable[[str], Awaitable[None]],
        cols: int = config.default_cols,
        rows: int = config.default_rows,
    ) -> None:
        """CLI プロセスを起動する。失敗時は例外を投げる。"""
        if self.is_running:
            raise RuntimeError("CLIBridge is already running")

        self._output_callback = output_callback
        try:
            self._proc = pexpect.spawn(
                config.cli_command,
                dimensions=(rows, cols),
                encoding=config.output_encoding,
                codec_errors="replace",
                timeout=None,
            )
        except Exception as exc:
            self._proc = None
            raise RuntimeError(f"CLI の起動に失敗しました: {exc}") from exc

        loop = asyncio.get_event_loop()
        self._read_task = loop.create_task(self._read_loop())
        logger.info("CLIBridge: プロセス起動完了 (cols=%d, rows=%d)", cols, rows)

    async def stop(self) -> None:
        """CLI プロセスを停止する。"""
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
            self._read_task = None

        if self._proc and self._proc.isalive():
            self._proc.close(force=True)
        self._proc = None
        logger.info("CLIBridge: プロセス停止完了")

    def send_input(self, text: str) -> None:
        """CLI の stdin にテキストを送信する。"""
        if not self.is_running:
            raise RuntimeError("CLI is not running")
        self._proc.send(text)

    def resize(self, cols: int, rows: int) -> None:
        """ターミナルサイズを変更する。"""
        if self.is_running:
            self._proc.setwinsize(rows, cols)

    async def _read_loop(self) -> None:
        """PTY の stdout を非同期に読み続け、コールバックへ渡す。"""
        loop = asyncio.get_event_loop()
        while self.is_running:
            try:
                data = await loop.run_in_executor(
                    None, self._read_chunk
                )
                if data and self._output_callback:
                    await self._output_callback(data)
            except (pexpect.EOF, pexpect.TIMEOUT):
                break
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("CLIBridge 読み取りエラー: %s", exc)
                break

        logger.info("CLIBridge: 読み取りループ終了")

    def _read_chunk(self) -> str:
        """同期的に PTY から最大 4096 バイト読み取る。"""
        try:
            return self._proc.read_nonblocking(size=4096, timeout=config.read_timeout)
        except pexpect.TIMEOUT:
            return ""
        except pexpect.EOF:
            raise
