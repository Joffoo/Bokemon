#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 Stage 2 (Judge) 失败断网遇阻后，断点续传能够直接复用 Stage 1 候选词执行 Stage 2。"""
import json
import sys
import threading
import http.server
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
PAGE_URL = (ROOT / "index.html").as_uri()

S0 = {
    "raw_telemetry": "会议室白板没擦干净 投影仪遥控器不见了 搪瓷杯倒扣在桌角",
    "forbidden_baseline": ["[阱 1] 散会忘了关投影仪", "[阱 2] 廉价网梗", "[阱 3] 会议让人疲惫"],
    "secular_domains": ["[1] 市政危房维保", "[3] 驾校科目考场", "[10] 典当行拍卖"]
}

DIVERGE = {
    "A": ["白板留着没擦当遗产", "杯子倒扣先算封存", "椅子朝向按原样看管"],
    "B": [
        {"category": "[1] 市政危房维保", "punchline": "白板裂缝挂上危房牌"},
        {"category": "[3] 驾校科目考场", "punchline": "绕白板一圈喊报告"}
    ],
    "C": ["白板受潮鼓包开会弹开", "椅子腿锈死保持坐姿"]
}

JUDGE = {
    "eliminations": ["淘汰「椅子朝向按原样看管」：画面平淡"],
    "scoring_and_ranking": "白板裂缝挂上危房牌 胜出",
    "initial_champion": "白板裂缝挂上危房牌",
    "crowning_reason": "绝佳反差动作",
    "recast_variants": {"variant_1": "白板裂缝挂上危房牌", "variant_2": "白板裂缝挂上危房牌"},
    "final_champion": "白板裂缝挂上危房牌"
}

calls = []

class FaultyMockHandler(http.server.BaseHTTPRequestHandler):
    judge_should_fail = True

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "*")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(n) or b"{}")
        system = ""
        for m in payload.get("messages", []):
            if m.get("role") == "system":
                system = m.get("content", "")

        call_type = "unknown"
        if "企划监督" in system:
            call_type = "stage0"
            content = json.dumps(S0, ensure_ascii=False)
            status = 200
        elif "轨道 A" in system or "A 轨" in system:
            call_type = "diverge"
            content = json.dumps(DIVERGE, ensure_ascii=False)
            status = 200
        else:
            call_type = "judge"
            if FaultyMockHandler.judge_should_fail:
                self.send_response(520)
                self._cors()
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"error code: 520 (Web server is returning an unknown error)")
                calls.append("judge_520")
                return
            else:
                content = json.dumps(JUDGE, ensure_ascii=False)
                status = 200

        calls.append(call_type)
        body = json.dumps({"choices": [{"message": {"role": "assistant", "content": content}}]}).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

server = http.server.ThreadingHTTPServer(("127.0.0.1", 8955), FaultyMockHandler)
t = threading.Thread(target=server.serve_forever, daemon=True)
t.start()

print("Faulty mock server running on 8955...")

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(PAGE_URL)

    # 配置 Mock 地址
    page.evaluate('''() => {
        config.baseUrl = 'http://127.0.0.1:8955/v1';
        config.apiKey = 'test-mock-key';
        config.model = 'mock-model';
        config.maxRetries = 0;
        config.timeoutSeconds = 5;
    }''')

    # 发起发送
    print("触发 handleSend...")
    page.evaluate('''async () => {
        inputText.value = "测试命题：会议室白板";
        await handleSend();
    }''')

    # 检查第一次运行结果：应该停在异常中断
    state1 = page.evaluate('''() => {
        const msgs = window.oogiriStudio.messages.value;
        const player = [...msgs].reverse().find(m => m.role === 'player');
        return {
            champion: player.champion,
            stageName: player.pipelineState?.currentStageName,
            isGenerating: player.isGenerating,
            candsA: player.pipelineState?.trackA?.candidates?.length || 0,
            candsB: player.pipelineState?.trackB?.candidates?.length || 0,
            candsC: player.pipelineState?.trackC?.candidates?.length || 0
        };
    }''')

    print("中断状态检验:", json.dumps(state1, ensure_ascii=False))
    assert "520" in state1["champion"], f"Expected 520 in champion: {state1['champion']}"
    assert state1["stageName"] == "✕ 异常中断"
    assert state1["candsA"] > 0 and state1["candsB"] > 0
    print("已确认：Stage 0 与 Stage 1 成功完成，Stage 2 发生 520 异常，候选词已保存在状态中！")
    print(f"调用序列: {calls}")
    assert calls[:2] == ["stage0", "diverge"]
    assert all(c == "judge_520" for c in calls[2:])

    # 检查页面上是否存在恢复执行按钮
    resume_btn = page.locator("button:has-text('恢复执行')")
    assert resume_btn.is_visible(), "恢复执行按钮未显示！"
    print("已确认：'🔄 恢复执行' 按钮正常显示！")

    # 准备恢复执行：模拟网络恢复，judge 响应正常 200
    FaultyMockHandler.judge_should_fail = False

    # 点击恢复执行
    print("点击 '🔄 恢复执行'...")
    resume_btn.click()
    page.wait_for_function("() => window.oogiriStudio && !window.oogiriStudio.isGeneratingAny.value")

    # 检查第二次运行结果：应该直接调用 judge 并成功
    state2 = page.evaluate('''() => {
        const msgs = window.oogiriStudio.messages.value;
        const player = [...msgs].reverse().find(m => m.role === 'player');
        return {
            champion: player.champion,
            stageName: player.pipelineState?.currentStageName,
            isGenerating: player.isGenerating
        };
    }''')

    print("恢复后最终状态:", json.dumps(state2, ensure_ascii=False))
    assert state2["champion"] == "白板裂缝挂上危房牌"
    assert state2["stageName"] == "✓ 金句生成完毕"
    assert not state2["isGenerating"]

    print(f"恢复后完整调用序列: {calls}")
    # 核心断言：恢复时只追加了一次 judge 调用，没有重新发起 stage0 或 diverge！
    assert calls[-1] == "judge"
    assert calls.count("stage0") == 1, "stage0 不应被重复调用！"
    assert calls.count("diverge") == 1, "diverge 不应被重复调用！"

    print("✓ 断点续传验证大获成功！完全跳过了第2步发散，直接执行第3步！")
    browser.close()

server.shutdown()
