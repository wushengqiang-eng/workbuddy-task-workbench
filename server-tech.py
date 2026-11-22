# -*- coding: utf-8 -*-
"""WorkBuddy 任务工作台 · 科技版本地服务（端口 8766）

与现有工作台（8765）完全独立，可同时运行。
双击「启动科技版.bat」运行。
"""
import os
import json
import webbrowser
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from refresh import get_payload

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8766
PAGE = "workbench-tech.html"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/api/tasks", "/data.js"):
            try:
                body = json.dumps(get_payload(), ensure_ascii=False).encode("utf-8")
                self._send(200, body, "application/json; charset=utf-8")
            except Exception as e:
                self._send(500, json.dumps({"error": str(e)}).encode(), "application/json; charset=utf-8")
        elif path in ("/", "/" + PAGE, "/index.html"):
            with open(os.path.join(HERE, PAGE), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain; charset=utf-8")


def main():
    url = "http://127.0.0.1:%d/" % PORT
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("科技版工作台已启动: " + url)
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
