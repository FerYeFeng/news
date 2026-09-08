#!/usr/bin/env python3
"""Serve generated pages on port 9092 and refresh all sources every 3 minutes."""

from __future__ import annotations

import os
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import fetch_news


ROOT = Path(__file__).resolve().parent
HTML_DIR = ROOT / "html"
HOST = "0.0.0.0"
PORT = 9092
INTERVAL_SECONDS = 180


def update_loop() -> None:
    while True:
        started = time.monotonic()
        print("\n开始更新全部平台……", flush=True)
        try:
            status = fetch_news.main()
        except Exception as error:
            print(f"更新异常：{error}", flush=True)
        else:
            print("全部平台更新完成。" if status == 0 else "部分平台更新失败。", flush=True)
        elapsed = time.monotonic() - started
        delay = max(0, INTERVAL_SECONDS - elapsed)
        print(f"本轮用时 {elapsed:.1f} 秒，{delay:.1f} 秒后开始下一轮。", flush=True)
        time.sleep(delay)


def main() -> None:
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(HTML_DIR)
    server = ThreadingHTTPServer((HOST, PORT), SimpleHTTPRequestHandler)
    threading.Thread(target=update_loop, name="news-updater", daemon=True).start()
    url = f"http://127.0.0.1:{PORT}/"
    print(f"监听地址：http://{HOST}:{PORT}/", flush=True)
    print(f"本机页面：{url}", flush=True)
    print("每 3 分钟更新全部平台。关闭此窗口即可停止。", flush=True)
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
