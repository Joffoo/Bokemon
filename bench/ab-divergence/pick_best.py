#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中性选优：从每臂的候选池里选出最好笑的一句，不做淘汰。

为什么不用生产 Stage 2：实跑发现它在真实题面上有 46% 的运行直接报「全灭」，
两臂一起全灭，比较就没法做了。Stage 2 的四道关 + 三向重铸是产品逻辑，
不是发散质量的度量；这里换成同一把中性尺子，两臂完全对称。

用法：
    python select.py --runs runs.jsonl --out runs.selected.jsonl
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from run_eval import chat, parse_jsonish  # noqa: E402

SELECT_SYSTEM = """你是日式大喜利的盲评裁判。下面是一批同一道题的候选金句，请选出其中最好笑、最秒懂的一句。

标尺：读完 0.5 秒「哈？」，再 0.5 秒逻辑接通爆笑；一读就懂；错位只有一处。
不要选需要绕弯才懂的，不要选只是描述画面而没有错位的。

只输出 JSON：{"best": "你选中的那句原文", "why": "20字以内"}"""


def strip_label(line: str) -> str:
    return re.sub(r"^\[[ABC]轨[^\]]*\]\s*", "", line).strip()


def pick(cfg: dict, key: str, prompt: str, pool: list[str], image_url: str | None) -> dict:
    body = "\n".join(f"{i + 1}. {strip_label(c)}" for i, c in enumerate(pool))
    user = f"【题面】{prompt}\n\n候选：\n{body}\n\n只输出 JSON。"
    res = chat({**cfg, "temperature": 0.2}, key, SELECT_SYSTEM, user, image_url)
    parsed = parse_jsonish(res["content"])
    best = str(parsed.get("best", "")).strip()
    # 模型可能把序号带出来，按原文反查
    for c in pool:
        if strip_label(c) and (strip_label(c) in best or best in strip_label(c)):
            return {"champion": strip_label(c), "why": str(parsed.get("why", ""))[:40], "raw": best}
    return {"champion": strip_label(pool[0]), "why": "fallback: 未匹配到原文", "raw": best}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(HERE / "config.json"))
    ap.add_argument("--runs", default=str(HERE / "runs.jsonl"))
    ap.add_argument("--items", default=str(HERE / "items.jsonl"))
    ap.add_argument("--out", default=str(HERE / "runs.selected.jsonl"))
    ap.add_argument("--only", default="", help="逗号分隔的题目 id，只重选这些题（留空=全部）")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    key = os.environ.get(cfg.get("api_key_env", ""), "")
    if not key:
        raise SystemExit(f"[select] 缺少环境变量 {cfg.get('api_key_env')}")

    prompts: dict[str, str] = {}
    images: dict[str, str | None] = {}
    for ln in Path(args.items).read_text(encoding="utf-8").splitlines():
        if ln.strip():
            it = json.loads(ln)
            prompts[it["id"]] = it.get("prompt", "")
            img = None
            if it.get("image_path"):
                p = Path(it["image_path"])
                if not p.is_absolute():
                    p = HERE / p
                if p.exists():
                    img = "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()
            images[it["id"]] = img

    rows = [json.loads(l) for l in Path(args.runs).read_text(encoding="utf-8").splitlines() if l.strip()]
    todo = [r for r in rows if r["pool"]]
    if args.only:
        only = {x.strip() for x in args.only.split(",") if x.strip()}
        todo = [r for r in todo if r["item_id"] in only]
        print(f"只重选 {sorted(only)}：{len(todo)} 条")

    def work(r: dict) -> dict:
        out = pick(cfg, key, prompts.get(r["item_id"], ""), r["pool"], images.get(r["item_id"]))
        return {**r, "stage2_champion": r["champion"], "champion": out["champion"], "select_why": out["why"]}

    done = []
    n_todo = len(todo)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, res in enumerate(pool.map(work, todo), 1):
            done.append(res)
            if i % 10 == 0 or i == n_todo:
                print(f"  {i}/{n_todo}")

    # --only 模式：保留原文件里其他题的记录，只替换被重选的
    out_path = Path(args.out)
    if args.only and out_path.exists():
        old = [json.loads(l) for l in out_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        redone_ids = {(r["item_id"], r["run_id"]) for r in done}
        old = [o for o in old if (o["item_id"], o["run_id"]) not in redone_ids]
        done = done + old
    done.sort(key=lambda r: (r["item_id"], r["arm"], r["repeat"]))

    out_path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in done), encoding="utf-8")
    print(f"完成 → {out_path}（{len(done)} 条）")


if __name__ == "__main__":
    main()
