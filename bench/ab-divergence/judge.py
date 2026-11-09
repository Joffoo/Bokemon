#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盲评裁判：把两臂冠军去标签、乱序，交给与"选择裁判"不同的模型打分。

为什么必须换模型：Stage 2 已经替自己选过一次冠军，同一个模型再给自己的选择打分，
分数里一半是它自己的选择偏好。评估裁判只回答"哪句更好笑"，不知道有实验这回事。

用法：
    python judge.py --mock
    python judge.py
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from run_eval import chat, endpoint_of, load_config, parse_jsonish  # noqa: E402

JUDGE_SYSTEM = """你是日式大喜利的盲评裁判。下面有两句同一道题的候选金句，分别标为「甲」和「乙」。
你不知道它们由谁生成，也不需要比较谁更努力。请各自独立打分，不要因为一句差就给另一句加分。

标尺（5 分制）：
5 = 读完 0.5 秒「哈？」，再 0.5 秒逻辑接通爆笑；一读就懂；错位只有一处
4 = 好笑，但要多绕半秒才接通
3 = 看懂了，不笑
2 = 勉强成立，但语义暧昧、需要猜
1 = 不成立 / 看不懂 / 只是客观描述没做错位

只输出 JSON：
{"甲": {"score": 1-5, "why": "20字以内"}, "乙": {"score": 1-5, "why": "20字以内"}}"""


def judge_prompt(prompt_text: str, x: str, y: str) -> str:
    return f"【题面】{prompt_text or '（看图大喜利）'}\n【甲】{x}\n【乙】{y}"


def _score_from_hash(text: str, judge_name: str) -> int:
    h = int(hashlib.sha256(f"{judge_name}|{text}".encode()).hexdigest(), 16)
    return 1 + h % 5


def mock_judge(judge_name: str, cmp_id: str, p: str, s: str, qtype: str) -> dict:
    base_p, base_s = _score_from_hash(p, judge_name), _score_from_hash(s, judge_name)
    # 给 P 一点点优势，让干跑的报告不是完全五五开，方便检查统计分支
    if qtype == "image":
        base_p = min(5, base_p + 1)
    return {"P": base_p, "S": base_s, "why": "mock"}


def run_one(
    cfg: dict,
    key: str,
    judge: dict,
    cmp_row: dict,
    image_url: str | None,
    mock: bool,
) -> dict:
    p, s = cmp_row["champion"]["P"], cmp_row["champion"]["S"]
    rng = random.Random(f"{cmp_row['cmp_id']}|{judge['name']}")
    p_is_jia = rng.random() < 0.5
    jia, yi = (p, s) if p_is_jia else (s, p)

    if mock:
        sc = mock_judge(judge["name"], cmp_row["cmp_id"], p, s, cmp_row["type"])
        score_p, score_s, why = sc["P"], sc["S"], sc["why"]
    else:
        res = chat(
            {**cfg, **judge},
            key,
            JUDGE_SYSTEM,
            judge_prompt(cmp_row.get("prompt", ""), jia, yi),
            image_url,
            None,
        )
        parsed = parse_jsonish(res["content"])
        jia_score = int(parsed["甲"]["score"])
        yi_score = int(parsed["乙"]["score"])
        score_p, score_s = (jia_score, yi_score) if p_is_jia else (yi_score, jia_score)
        why = json.dumps({"甲": parsed["甲"].get("why", ""), "乙": parsed["乙"].get("why", "")}, ensure_ascii=False)

    winner = "P" if score_p > score_s else ("S" if score_s > score_p else "tie")
    return {
        "judge": judge["name"],
        "model": judge.get("model", "mock"),
        "order": "P-first" if p_is_jia else "S-first",
        "score": {"P": score_p, "S": score_s},
        "winner": winner,
        "why": why,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(HERE / "config.json"))
    ap.add_argument("--runs", default="")
    ap.add_argument("--items", default=str(HERE / "items.jsonl"))
    ap.add_argument("--out", default="")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    runs_path = Path(args.runs) if args.runs else HERE / ("runs.mock.jsonl" if args.mock else "runs.jsonl")
    out_path = Path(args.out) if args.out else HERE / ("judgements.mock.jsonl" if args.mock else "judgements.jsonl")
    if not runs_path.exists():
        raise SystemExit(f"[judge] 找不到 {runs_path}，先跑 run_eval.py")

    items = {}
    if Path(args.items).exists():
        for ln in Path(args.items).read_text(encoding="utf-8").splitlines():
            if ln.strip():
                it = json.loads(ln)
                items[it["id"]] = it

    cfg: dict = {"base_url": "", "model": "mock", "max_retries": 0, "timeout": 60}
    judges: list[dict] = [{"name": "J1", "model": "mock"}, {"name": "J2", "model": "mock"}]
    if not args.mock:
        raw = json.loads(Path(args.config).read_text(encoding="utf-8"))
        cfg = {k: raw[k] for k in ("base_url", "model", "temperature", "max_retries", "timeout") if k in raw}
        judges = raw.get("judges") or []
        if not judges:
            raise SystemExit("[judge] config.json 里需要 judges 数组（至少 1 个，建议 2 个不同家族模型）")
        for j in judges:
            ref = j.get("api_key_env") or raw.get("api_key_env") or ""
            j["_key"] = j.get("api_key") or os.environ.get(ref, "")
            if not j["_key"]:
                raise SystemExit(f"[judge] 裁判 {j.get('name')} 缺少 API Key（环境变量 {ref or '未指定'}）")

    rows: dict[str, dict] = {}
    for ln in runs_path.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        r = json.loads(ln)
        if r["errors"] or not r.get("champion"):
            continue
        cmp_id = f"{r['item_id']}|r{r['repeat']}"
        row = rows.setdefault(
            cmp_id,
            {
                "cmp_id": cmp_id,
                "item_id": r["item_id"],
                "type": r["type"],
                "repeat": r["repeat"],
                "prompt": items.get(r["item_id"], {}).get("prompt", ""),
                "champion": {},
            },
        )
        row["champion"][r["arm"]] = r["champion"]

    pairs = [r for r in rows.values() if len(r["champion"]) == 2]

    done: set[str] = set()
    if out_path.exists():
        for ln in out_path.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                done.add(json.loads(ln)["cmp_id"])

    print(f"判定 {len(pairs)} 组 × {len(judges)} 位裁判 | 已有 {len(done)} 组")

    todo = [row for row in pairs if row["cmp_id"] not in done]

    def judge_pair(row: dict) -> dict | None:
        item = items.get(row["item_id"], {})
        image_url = None
        if item.get("image_path"):
            p = Path(item["image_path"])
            if not p.is_absolute():
                p = HERE / p
            if p.exists():
                image_url = "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()
        verdicts = []
        for j in judges:
            try:
                verdicts.append(run_one(cfg, j.get("_key", ""), j, row, image_url, args.mock))
            except Exception as exc:  # noqa: BLE001
                print(f"  ✗ {row['cmp_id']} / {j['name']}: {exc}")
        if not verdicts:
            return None
        return {
            **{k: row[k] for k in ("cmp_id", "item_id", "type", "repeat")},
            "prompt": row["prompt"],
            "champion": row["champion"],
            "judges": verdicts,
        }

    done_count = 0
    # 追加前确保文件以换行结尾——上次回填脚本用 join 重写时没带尾换行，
    # 结果两条记录拼到了一行。防御：读末字节，不完整就补一个。
    if out_path.exists() and out_path.stat().st_size > 0:
        with open(out_path, "rb") as fh:
            fh.seek(-1, 2)
            if fh.read(1) != b"\n":
                with open(out_path, "a", encoding="utf-8") as fh2:
                    fh2.write("\n")
                print("（补了缺失的行尾换行）")
    with open(out_path, "a", encoding="utf-8") as fh:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for rec in pool.map(judge_pair, todo):
                if rec is None:
                    continue
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()
                done_count += 1
                line = " ".join(f"{v['judge']}:{v['score']['P']}/{v['score']['S']}" for v in rec["judges"])
                print(f"  ✓ {rec['cmp_id']}  {line}")

    print(f"完成：新判 {done_count} 组 → {out_path}")


if __name__ == "__main__":
    main()
