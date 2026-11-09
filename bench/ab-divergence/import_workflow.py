#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 DSH workflow（子 Agent 路径）的返回结果转成 analyze.py 认识的日志格式。

支持两种输入：
1. workflow 原始返回：{"items": [{id, poolP, poolS, champP, champS, scoreP, scoreS, tracksP, tracksS, ...}]}
2. 精简记录：同上去掉 tracks，另给 b_count / b_expected

用法：
    python import_workflow.py pilot.json
产物：runs.workflow.jsonl / judgements.workflow.jsonl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    src = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    items = src["items"]
    runs, jdgs = [], []
    skipped = []

    for r in items:
        if r.get("error") or not r.get("champP") or not r.get("champS"):
            skipped.append(r.get("id"))
            continue
        b_expected = int(r.get("b_expected") or 8)
        b_count = int(r.get("b_count") or b_expected)
        common = {
            "item_id": r["id"],
            "type": r.get("type", "text"),
            "repeat": 1,
            "model": src.get("model", "dsh-workflow"),
            "temperature": None,
            "prompt_hash": "dsh-workflow-pilot",
            "stage0": {"secular_domains": ["?"] * b_expected},
            "tokens": {"prompt": 0, "completion": 0},
            "latency_ms": 0,
            "errors": [],
            "b_count": b_count,
            "b_expected": b_expected,
        }
        for arm, tracks, pool, champ in (
            ("P", r.get("tracksP"), r["poolP"], r["champP"]),
            ("S", r.get("tracksS"), r["poolS"], r["champS"]),
        ):
            runs.append({
                **common,
                "run_id": f"{r['id']}|{arm}|r1",
                "arm": arm,
                "order": "P-first",
                "tracks": tracks or {"A": [], "B": [], "C": []},
                "pool": pool,
                "champion": champ,
            })

        sp, ss = r["scoreP"], r["scoreS"]
        winner = "P" if sp > ss else ("S" if ss > sp else "tie")
        jdgs.append({
            "cmp_id": f"{r['id']}|r1", "item_id": r["id"], "type": r.get("type", "text"), "repeat": 1,
            "champion": {"P": r["champP"], "S": r["champS"]},
            "judges": [{
                "judge": "J1", "model": src.get("model", "dsh-workflow"), "order": "see-record",
                "score": {"P": sp, "S": ss}, "winner": winner,
                "why": json.dumps({"P": r.get("judgeWhyP", ""), "S": r.get("judgeWhyS", "")}, ensure_ascii=False),
            }],
        })

    (HERE / "runs.workflow.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in runs), encoding="utf-8")
    (HERE / "judgements.workflow.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in jdgs), encoding="utf-8")
    print(f"导入 {len(runs) // 2} 题 / {len(runs)} 条运行；跳过 {skipped or '无'}")


if __name__ == "__main__":
    main()
