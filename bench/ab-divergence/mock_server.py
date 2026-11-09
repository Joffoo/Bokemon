#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同源 mock 服务器 + 页面验证：静态文件 + /v1/chat/completions 确定性响应。

跑法：python browser_verify.py real --base-url http://127.0.0.1:8941 --model mock --reroll
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8", ".png": "image/png"}

S0 = {
    "raw_telemetry": "会议室白板没擦干净 投影仪遥控器不见了 搪瓷杯倒扣在桌角 椅子还维持着散会时的朝向",
    "forbidden_baseline": [
        "[阱 1 现实观察与字面拆解] 散会忘了关投影仪",
        "[阱 2 廉价网梗] 我不允许还有人没开过这种会",
        "[阱 3 情绪直给与自行吐槽] 会议真让人疲惫",
    ],
    "secular_domains": ["[1] 市政危房维保", "[3] 驾校科目考场", "[10] 典当行拍卖",
                        "[11] 餐饮后厨卫生", "[17] 澡堂足疗技师", "[21] 修锁配钥匙",
                        "[23] 老式国营食堂", "[24] 高速收费站"],
}
DIVERGE = {
    "A": ["白板留着没擦当遗产", "杯子倒扣先算封存", "椅子朝向按原样看管"],
    "B": [{"category": d, "punchline": p} for d, p in zip(S0["secular_domains"], [
        "白板裂缝挂上危房牌", "绕白板一圈喊报告", "敲白板听裂定真假",
        "白板擦挂消毒池浸泡", "给白板搓澡先搓背", "往白板槽里灌铅粉",
        "白板笔套上饭票套", "给白板裂贴通行票"])],
    "C": ["白板受潮鼓包开会弹开", "椅子腿锈死保持坐姿", "投影仪积灰厚到能种菜"],
}
JUDGE = {
    "track_champions": {"trackA": "白板留着没擦当遗产", "trackB": "绕白板一圈喊报告", "trackC": "白板受潮鼓包开会弹开"},
    "initial_champion": "白板留着没擦当遗产",
    "recast_variants": {"monologue": "白板别擦留着传家", "quantified": "白板遗产每天巡视三遍", "cold_sketch": "散会三天白板长出遗嘱"},
    "final_champion": "散会三天白板长出遗嘱",
    "crowning_reason": "mock 冠军",
}


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "*")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/v1/models":
            body = json.dumps({"data": [{"id": "mock"}]}).encode()
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
            return
        if path in ("/", "/index.html"):
            f = ROOT / "index.html"
        else:
            f = ROOT / path.lstrip("/")
        if f.is_file():
            body = f.read_bytes()
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", MIME.get(f.suffix, "application/octet-stream"))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(n) or b"{}")
        system = ""
        for m in payload.get("messages", []):
            if m.get("role") == "system":
                system = m.get("content", "")
        if "企划监督" in system:
            content = json.dumps(S0, ensure_ascii=False)
        elif "轨道 A" in system:
            content = json.dumps(DIVERGE, ensure_ascii=False)
        else:
            content = json.dumps(JUDGE, ensure_ascii=False)
        body = json.dumps({"choices": [{"message": {"role": "assistant", "content": content}}],
                           "usage": {"prompt_tokens": 1, "completion_tokens": 1}}).encode()
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def serve(port: int = 8941) -> str:
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}"
