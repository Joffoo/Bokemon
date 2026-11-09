"""Bokeman 本地服务器：托管页面 + 为浏览器不能直连的 API（不开放 CORS）充当本机中转。

仅供本地开发/自用：双击「启动.bat」，或  python server.py [--port 8787] [--open]
线上部署（Vercel）不需要它，用的是同一接口的 api/proxy.js。

工作方式：页面直连失败（中转站不开放 CORS）时，自动回退为请求
    /api/proxy?u=<用户填写的完整地址>
本服务把它原样转发到该地址。转发目标完全由用户在页面里填的 Base URL 决定。

安全：
- 只监听 127.0.0.1；
- 只接受本机页面（同源或 file://）的请求，拒绝其他网站借道；
- Authorization 由浏览器随请求带来，只透传，不保存、不打印、不写盘。
"""
import argparse
import mimetypes
import os
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

ROOT = os.path.dirname(os.path.abspath(__file__))
FORWARD_REQ_HEADERS = ("authorization", "content-type", "accept")
SKIP_RESP_HEADERS = {"transfer-encoding", "connection", "content-length", "content-encoding",
                     "keep-alive", "server", "date"}
PROXY_PATH = "/api/proxy"  # 与 Vercel 函数 api/proxy.js 同一接口
STATIC_EXT = {".svg", ".png", ".ico", ".jpg", ".jpeg", ".gif", ".webp"}  # 根目录下的 logo 等图片


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    port = 8787

    def log_message(self, fmt, *args):  # 不记录请求头/正文，避免泄露 Key
        pass

    def _is_proxy(self):
        return urlsplit(self.path).path == PROXY_PATH

    def _origin_ok(self):
        o = self.headers.get("Origin")
        return o in (None, "null", "http://127.0.0.1:%d" % self.port, "http://localhost:%d" % self.port)

    def _cors(self):
        o = self.headers.get("Origin")
        return {
            "Access-Control-Allow-Origin": o if o else "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "authorization, content-type, accept",
            "Access-Control-Max-Age": "600",
            "Vary": "Origin",
        }

    def _send(self, status, body=b"", headers=None):
        self.send_response(status)
        for k, v in {**self._cors(), **(headers or {})}.items():
            self.send_header(k, v)
        if self._is_proxy():
            self.send_header("X-Bokeman-Proxy", "1")  # 前端据此确认回应来自中转而不是静态 404
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_OPTIONS(self):
        if not self._origin_ok():
            return self._send(403, b"forbidden origin")
        self._send(204)

    def do_GET(self):
        if self._is_proxy():
            return self._proxy()
        self._static()

    def do_POST(self):
        if self._is_proxy():
            return self._proxy()
        self._send(404, b"not found")

    def _static(self):
        rel = urlsplit(self.path).path.lstrip("/") or "index.html"
        full = os.path.normpath(os.path.join(ROOT, rel))
        # 只托管 index.html、js/ 与根目录图片（logo），且不能越出项目目录
        ok = rel == "index.html" or rel.startswith("js/") or \
            ("/" not in rel and os.path.splitext(rel)[1].lower() in STATIC_EXT)
        if not full.startswith(ROOT + os.sep) or not ok or not os.path.isfile(full):
            return self._send(404, b"not found")
        with open(full, "rb") as f:
            data = f.read()
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or "javascript" in ctype:
            ctype += "; charset=utf-8"
        self._send(200, data, {"Content-Type": ctype, "Cache-Control": "no-store"})

    def _proxy(self):
        if not self._origin_ok():
            return self._send(403, b"forbidden origin")
        target = (parse_qs(urlsplit(self.path).query).get("u") or [""])[0]
        parts = urlsplit(target)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            return self._send(400, b"bad target url")
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        headers = {k: self.headers[k] for k in FORWARD_REQ_HEADERS if self.headers.get(k)}
        headers["User-Agent"] = "Mozilla/5.0 (Bokeman local proxy)"
        req = urllib.request.Request(target, data=body, headers=headers, method=self.command)
        try:
            resp = urllib.request.urlopen(req, timeout=120)
        except urllib.error.HTTPError as e:
            resp = e  # 4xx/5xx 也原样回传给页面
        except Exception as e:
            return self._send(502, ("本地代理无法连接上游 %s：%s" % (parts.netloc, e)).encode("utf-8"),
                              {"Content-Type": "text/plain; charset=utf-8"})
        data = resp.read()
        out = {k: v for k, v in resp.headers.items()
               if k.lower() not in SKIP_RESP_HEADERS and not k.lower().startswith("access-control-")}
        self._send(resp.status if hasattr(resp, "status") else resp.code, data, out)


class Server(ThreadingHTTPServer):
    allow_reuse_address = False  # Windows 上为 True 时允许多进程同占一端口，新旧版本会混用


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--open", action="store_true", help="启动后自动打开浏览器")
    a = ap.parse_args()
    Handler.port = a.port
    url = "http://127.0.0.1:%d/" % a.port
    try:
        srv = Server(("127.0.0.1", a.port), Handler)
    except OSError:  # 端口已被占用：多半是已经启动过了，直接打开即可
        print("端口 %d 已被占用，可能已在运行：%s" % (a.port, url))
        if a.open:
            webbrowser.open(url)
        return
    print("Bokeman 已启动：%s   （关闭此窗口即停止）" % url)
    if a.open:
        webbrowser.open(url)
    srv.serve_forever()


if __name__ == "__main__":
    main()
