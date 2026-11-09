#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拆分后版本的浏览器验收：bootstrap → 演示管线 → 真实 API 全链路。

用法：
    python browser_verify.py bootstrap                 # 无成本：加载 + 27 模块 + 演示管线
    python browser_verify.py real --key SK --model deepseek-chat   # 真实出题一次 + reroll 一次
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

import mock_server

ROOT = Path(__file__).resolve().parents[2]
PAGE_URL = (ROOT / "index.html").as_uri()
SHOTS = Path(__file__).resolve().parent / "shots"
sys.stdout.reconfigure(encoding="utf-8")


def new_page(pw, shots: bool = True):
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 960})
    page = ctx.new_page()
    log: list[str] = []
    page.on("console", lambda m: log.append(f"[{m.type}] {m.text[:200]}") if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: log.append(f"[pageerror] {str(e)[:200]}"))
    page.on("requestfailed", lambda r: log.append(f"[reqfail] {r.url[:120]} {r.failure}") if "js/" in r.url else None)
    return browser, ctx, page, log


def bootstrap(pw) -> bool:
    browser, ctx, page, log = new_page(pw)
    page.goto(PAGE_URL, wait_until="networkidle", timeout=60000)
    page.screenshot(path=str(SHOTS / "01-bootstrap.png"))
    checks = page.evaluate("""() => ({
        scriptsLoaded: document.querySelectorAll('script[src^="js/"]').length,
        stateGlobals: ['messages','config','toast','pipelineMode','isGeneratingAny'].filter(k => { try { return typeof eval(k) !== 'undefined'; } catch (e) { return false; } }),
        studio: typeof window.oogiriStudio === 'object' && !!window.oogiriStudio,
        studioKeys: window.oogiriStudio ? ['handleSend','rerollPunchline','runMockPreset','exportMarkdownHistory'].filter(k => typeof window.oogiriStudio[k] === 'function') : [],
        handleSendGlobal: typeof window.handleSend === 'function',
        promptBuilder: typeof window.buildDivergenceSystemPrompt === 'function',
        appMounted: !!document.querySelector('#app .chat-container, #app [class*=chat]'),
    })""")
    print("bootstrap:", json.dumps(checks, ensure_ascii=False))
    ok = (checks["scriptsLoaded"] >= 27 and len(checks["stateGlobals"]) == 5
          and checks["studio"] and len(checks["studioKeys"]) == 4
          and checks["handleSendGlobal"] and checks["promptBuilder"] and checks["appMounted"])

    # 演示管线（无 API 成本）：验证状态卡 + 加冕链路
    demo = page.evaluate("""async () => {
        const before = window.oogiriStudio.messages.value.length;
        await window.oogiriStudio.runMockPreset(0);
        const msgs = window.oogiriStudio.messages.value;
        const player = [...msgs].reverse().find(m => m.role === 'player');
        return {
            before, after: msgs.length,
            champion: player && player.champion || '',
            stage: player && player.pipelineState ? player.pipelineState.currentStageName : '',
            tracks: player && player.pipelineState ? {
                a: player.pipelineState.trackA.candidates.length,
                b: player.pipelineState.trackB.candidates.length,
                c: player.pipelineState.trackC.candidates.length,
            } : null,
        };
    }""")
    print("demo:", json.dumps(demo, ensure_ascii=False))
    page.screenshot(path=str(SHOTS / "02-demo.png"))
    ok = ok and bool(demo["champion"]) and demo["tracks"] and demo["tracks"]["a"] > 0

    errs = [x for x in log if "[pageerror]" in x or "[reqfail]" in x or "[error]" in x]
    print(f"console/pageerror/reqfail：{len(errs)} 条")
    for x in errs[:10]:
        print("  ", x)
    ok = ok and not errs
    browser.close()
    print("BOOTSTRAP:", "PASS ✓" if ok else "FAIL ✗")
    return ok


def real(pw, key: str, model: str, do_reroll: bool, base_url: str = "https://api.deepseek.com",
         page_origin: str | None = None) -> bool:
    browser, ctx, page, log = new_page(pw)
    page.goto((page_origin or PAGE_URL) + ("/index.html" if page_origin else ""), wait_until="domcontentloaded", timeout=60000)
    page.evaluate("""cfg => {
        localStorage.setItem('oogiri_flow_config', JSON.stringify({
            baseUrl: cfg.baseUrl, apiKey: cfg.key, model: cfg.model,
            timeoutSeconds: 90, maxRetries: 2, temperature: 0.7, rememberKey: true,
        }));
    }""", {"key": key, "model": model, "baseUrl": base_url})
    page.reload(wait_until="networkidle")
    prompt = "站在天台上的西装男子，手里牵着一只气球"
    # 用绑定直接驱动（等价于点发送按钮）
    sent = page.evaluate("""async p => {
        window.oogiriStudio.inputText.value = p;
        window.oogiriStudio.selectedImage.value = null;
        await window.oogiriStudio.handleSend();
        const msgs = window.oogiriStudio.messages.value;
        const player = [...msgs].reverse().find(m => m.role === 'player');
        return { champion: player && player.champion || '', stage: player && player.pipelineState.currentStageName };
    }""", prompt)
    print("real send:", json.dumps(sent, ensure_ascii=False))
    page.screenshot(path=str(SHOTS / "03-real-send.png"))
    ok = bool(sent["champion"]) and "金句生成完毕" in (sent["stage"] or "")

    if do_reroll and ok:
        rr = page.evaluate("""async () => {
            const msgs = window.oogiriStudio.messages.value;
            const player = [...msgs].reverse().find(m => m.role === 'player');
            const before = player.champion;
            await window.rerollPunchline(player);
            return { before, after: player.champion,
                     stage: player.pipelineState.currentStageName,
                     divergeFile: 'js/11-13' };
        }""")
        print("reroll:", json.dumps(rr, ensure_ascii=False))
        page.screenshot(path=str(SHOTS / "04-real-reroll.png"))
        ok = ok and bool(rr["after"])
    errs = [x for x in log if "[pageerror]" in x or "[reqfail]" in x]
    print(f"pageerror/reqfail：{len(errs)} 条")
    for x in errs[:10]:
        print("  ", x)
    browser.close()
    print("REAL:", "PASS ✓" if ok and not errs else "FAIL ✗")
    return ok


if __name__ == "__main__":
    SHOTS.mkdir(exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["bootstrap", "real"])
    ap.add_argument("--key", default="")
    ap.add_argument("--model", default="deepseek-chat")
    ap.add_argument("--base-url", default="https://api.deepseek.com")
    ap.add_argument("--reroll", action="store_true")
    a = ap.parse_args()
    with sync_playwright() as pw:
        if a.mode == "bootstrap":
            sys.exit(0 if bootstrap(pw) else 1)
        if not a.key:
            raise SystemExit("real 模式需要 --key")
        origin = None
        if a.base_url.startswith("http://127.0.0.1"):
            origin = mock_server.serve(int(a.base_url.rsplit(":", 1)[1]))  # 同源 mock：静态页 + API
            print("mock 服务器：", origin)
        sys.exit(0 if real(pw, a.key, a.model, a.reroll, a.base_url, origin) else 1)
