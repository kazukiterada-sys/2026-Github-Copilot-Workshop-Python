"""pytest の conftest — sys.path にルートを追加して timer モジュールをインポート可能にする。"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
