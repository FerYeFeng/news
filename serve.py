#!/usr/bin/env python3
"""Serve generated pages on port 9092 and refresh all sources every 10 minutes."""

from __future__ import annotations

import os
import threading
import time
import webbrowser
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import fetch_news


ROOT = Path(__file__).resolve().parent
HTML_DIR = ROOT / "html"
HOST = "0.0.0.0"
PORT = 9092
INTERVAL_SECONDS = 600
refresh_lock = threading.Lock()


def lower_process_priority() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        kernel32.SetPriorityClass.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
        kernel32.SetPriorityClass(kernel32.GetCurrentProcess(), 0x00004000)
    except Exception:
        pass


class NewsHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".json": "application/json; charset=utf-8",
    }

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/refresh":
            self.send_error(404)
            return
        if not refresh_lock.acquire(blocking=False):
            body = json.dumps({"ok": False, "message": "已有更新任务正在运行"}, ensure_ascii=False).encode()
            self.send_response(409)
        else:
            try:
                status = fetch_news.main()
                body = json.dumps({"ok": status == 0, "status": status}).encode()
                self.send_response(200)
            except Exception as error:
                body = json.dumps({"ok": False, "message": str(error)}, ensure_ascii=False).encode()
                self.send_response(500)
            finally:
                refresh_lock.release()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def update_loop() -> None:
    while True:
        started = time.monotonic()
        print("\n开始更新全部平台……", flush=True)
        with refresh_lock:
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
    lower_process_priority()
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    os.chdir(HTML_DIR)
    server = ThreadingHTTPServer((HOST, PORT), NewsHandler)
    threading.Thread(target=update_loop, name="news-updater", daemon=True).start()
    url = f"http://127.0.0.1:{PORT}/"
    print(f"监听地址：http://{HOST}:{PORT}/", flush=True)
    print(f"本机页面：{url}", flush=True)
    print("每 10 分钟更新全部平台。关闭此窗口即可停止。", flush=True)
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
