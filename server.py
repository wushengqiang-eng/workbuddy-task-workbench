# -*- coding: utf-8 -*-
"""WorkBuddy 任务工作台 · 本地实时服务

双击「启动工作台.bat」运行。启动后自动打开浏览器。
点页面「刷新数据」或每 30 秒自动查询一次数据库，任务实时更新。
关闭本窗口即停止服务。
"""
import os
import json
import webbrowser
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from refresh import get_payload, search_tasks

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8765


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # 静默，避免刷屏

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path
        qs = parse_qs(u.query)
        if path in ("/api/tasks", "/data.js"):
            try:
                pins = qs.get("pin", [""])[0]
                pin_ids = [x for x in pins.split(",") if x] if pins else None
                payload = get_payload(pin_ids)
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self._send(200, body, "application/json; charset=utf-8")
            except Exception as e:
                self._send(500, json.dumps({"error": str(e)}).encode(), "application/json; charset=utf-8")
        elif path == "/api/search":
            try:
                q = qs.get("q", [""])[0]
                body = json.dumps({"results": search_tasks(q)}, ensure_ascii=False).encode("utf-8")
                self._send(200, body, "application/json; charset=utf-8")
            except Exception as e:
                self._send(500, json.dumps({"error": str(e)}).encode(), "application/json; charset=utf-8")
        elif path in ("/", "/workbench.html"):
            with open(os.path.join(HERE, "workbench.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain; charset=utf-8")


def main():
    url = "http://127.0.0.1:%d/" % PORT
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("工作台已启动: " + url)
    print("关闭此窗口即停止服务。")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
