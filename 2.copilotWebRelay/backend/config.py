"""アプリケーション設定"""
from dataclasses import dataclass, field


@dataclass
class Config:
    host: str = "0.0.0.0"
    port: int = 8000
    cli_command: str = "copilot"
    default_cols: int = 120
    default_rows: int = 40
    read_timeout: float = 0.05
    output_encoding: str = "utf-8"


config = Config()
