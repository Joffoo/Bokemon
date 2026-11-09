#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 index.html 里逐字提取三轨 + Stage 2 提示词，保证实验与线上提示词零漂移。

为什么要抽取而不是复制：复制一份就等于多一个真源，改一处漏一处时实验结论立刻失真。
index.html 里这些提示词是 JS 模板字符串，`${...}` 位置用运行时变量填充；这里按表达式特征
识别后替换，遇到未知表达式直接报错，绝不静默留空。
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sysif hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# 提示词真源：拆分后位于 js/ 模块（03/11/12 含轨道与 Stage 0，14/15/16/17 含 handleSend 侧，18 含尾段）
SOURCES = [ROOT / "index.html"] + sorted((ROOT / "js").glob("*.js"))

_VARS = {
    "stage0": "stage0SystemPrompt",
    "A": "sysA",
    "B": "sysB",
    "C": "sysC",
    "stage2": "stage2SystemPrompt",
}

# 表达式特征 -> 渲染值。顺序有意义：先匹配 text ||，避免误判。
_EXPR_RULES = (
    ("text ||", "prompt"),
    ("promptText ||", "prompt"),
    ("raw_telemetry", "telemetry"),
    ("forbidden_baseline", "baselines"),
    ("secular_domains", "domains"),
)


def _extract(src: str, var: str) -> str:
    """取最后一处定义。

    index.html 里 rerollPunchline 与 handleSend 各有一份同名模板；handleSend 是主生产路径，
    位置更靠后，所以取 last。两份是否一致另由 check_duplicates() 报告。
    """
    pattern = re.compile(r"const " + re.escape(var) + r" = `([\s\S]*?)`;")
    matches = list(pattern.finditer(src))
    if not matches:
        raise SystemExit(
            f"[prompts] 无法从 index.html 提取 `const {var}`。\n"
            f"  index.html 结构变了？请先修好抽取规则，不要手工复制提示词。"
        )
    return matches[-1].group(1).replace("\\`", "`")


def _render(tpl: str, values: dict[str, str]) -> str:
    def sub(m: re.Match) -> str:
        expr = m.group(1)
        for key, name in _EXPR_RULES:
            if key in expr:
                return values[name]
        raise SystemExit(
            f"[prompts] 遇到未知模板表达式 ${{{expr}}}。\n"
            f"  新增了运行时变量？请在 _EXPR_RULES 里登记，否则实验用的提示词会和线上不一致。"
        )

    return re.sub(r"\$\{([^}]*)\}", sub, tpl)


def build(stage0: dict, prompt_text: str) -> dict[str, str]:
    """返回渲染好的 A / B / C / stage2 提示词。"""
    src = chr(10).join(f.read_text(encoding="utf-8") for f in SOURCES)
    values = {
        "prompt": prompt_text,
        "telemetry": stage0.get("raw_telemetry", ""),
        "baselines": "\n".join(stage0.get("forbidden_baseline", [])),
        "domains": "\n".join(stage0.get("secular_domains", [])),
    }
    return {key: _render(_extract(src, var), values) for key, var in _VARS.items()}


def build_arm_s(rendered: dict[str, str], track_order: str = "ABC") -> str:
    """把三轨提示词原样拼成单 Agent 的一次系统提示词。

    track_order 用于跨重复轮换段落顺序，抵消"后段被前段带跑"的锚定效应。
    """
    head = (
        "【本次任务：三轨并行发散，一次完成】\n"
        "你将依次完成三条轨道的发散。每条轨道只产出该轨道的候选，三条轨道互不参照、"
        "互不借用对方的词，不得合并成一种口吻。全部完成后再输出，顺序如下。\n\n"
    )
    sections = {
        "A": ("轨道 A / 体面破绽", rendered["A"]),
        "B": ("轨道 B / 异业动作", rendered["B"]),
        "C": ("轨道 C / 物理死磕", rendered["C"]),
    }
    body = ""
    for key in track_order:
        title, text = sections[key]
        body += f"=== {title} ===\n{text}\n\n"
    tail = (
        "【输出契约】只输出合法 JSON，除 JSON 外无任何字符：\n"
        '{"A": ["短句1", "短句2", "短句3"],\n'
        ' "B": [{"category": "[序号] 类别名", "punchline": "台词"}],\n'
        ' "C": ["短句1", "短句2", "短句3"]}\n'
    )
    return head + body + tail


def fingerprint() -> str:
    """提示词指纹，写进 manifest 与每条日志。"""
    src = chr(10).join(f.read_text(encoding="utf-8") for f in SOURCES)
    raw = "".join(_extract(src, v) for v in _VARS.values())
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def _normalize(tpl: str) -> str:
    def sub(m: re.Match) -> str:
        for key, name in _EXPR_RULES:
            if key in m.group(1):
                return "{{" + name + "}}"
        return "{{unknown}}"

    # 去掉全部空白后再比：两份副本的 JSON 换行/缩进不同，不算内容漂移
    return re.sub(r"\s+", "", re.sub(r"\$\{([^}]*)\}", sub, tpl))


def check_duplicates() -> dict[str, bool]:
    """检查 index.html 内同名模板的多处副本是否一致（rerollPunchline vs handleSend）。

    AGENTS.md 要求 handleSend 与 rerollPunchline 提示词双端一致；这里做一次机器核对，
    返回 {var: 是否所有副本一致}。不一致不影响本实验（只取 handleSend），但值得报警。
    """
    src = chr(10).join(f.read_text(encoding="utf-8") for f in SOURCES)
    out = {}
    for var in _VARS.values():
        pattern = re.compile(r"const " + re.escape(var) + r" = `([\s\S]*?)`;")
        copies = {_normalize(m.group(1)) for m in pattern.finditer(src)}
        out[var] = len(copies) <= 1
    return out


FP_FILE = Path(__file__).resolve().parent / "PROMPTS_FINGERPRINT"


def check() -> bool:
    """SSOT 校验：副本一致 + 指纹与登记值相符。退出码即结果。"""
    ok = True
    for var, same in check_duplicates().items():
        if not same:
            ok = False
            print(f"✗ {var} 存在多份不一致的副本（rerollPunchline / handleSend 改了一处漏一处）")
    fp = fingerprint()
    if not FP_FILE.exists():
        FP_FILE.write_text(fp, encoding="utf-8")
        print(f"✓ 首次运行，已登记提示词指纹 {fp} → PROMPTS_FINGERPRINT")
        return ok
    recorded = FP_FILE.read_text(encoding="utf-8").strip()
    if fp != recorded:
        ok = False
        print(f"✗ 提示词指纹漂移：当前 {fp}，登记 {recorded}")
        print("  若为有意修改提示词，请同步更新登记值：python bench/ab-divergence/prompts.py --update-fingerprint")
        print("  若为无意改动，请检查 js/ 模块与 SKILL.md 的双端一致。")
    else:
        print(f"✓ 提示词指纹一致（{fp}），副本一致")
    return ok


if __name__ == "__main__":
    fp = fingerprint()
    if "--check" in sys.argv:
        sys.exit(0 if check() else 1)
    if "--update-fingerprint" in sys.argv:
        FP_FILE.write_text(fp, encoding="utf-8")
        print(f"已登记提示词指纹 {fp} → PROMPTS_FINGERPRINT")
        sys.exit(0)
    print(f"提示词指纹: {fp}")
    for var, same in check_duplicates().items():
        if not same:
            print(f"  ⚠ {var} 在 index.html 里有多份不一致的副本（rerollPunchline / handleSend）")
    demo = build(
        {
            "raw_telemetry": "演示地基",
            "forbidden_baseline": ["阱1", "阱2", "阱3"],
            "secular_domains": ["[1] 市政危房维保", "[2] 临期商超早市"],
        },
        "演示命题",
    )
    for k, v in demo.items():
        print(f"\n--- {k} ({len(v)} 字) ---\n{v[:120]}...")

