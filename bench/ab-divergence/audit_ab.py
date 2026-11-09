#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""正式 A/B 盲测结果审计：四关机械检查 + 棘轮判定。

输入：workflow 返回值存成的 JSON（{"rows": [...], "s0": {...}}）
用法：
    python audit_ab.py ab_result.json
按 workflow-ab-eval Step 4 输出判定：
  - 关 2（机械部分）：≤14 字、零标点零空格、冠军无标签残留
  - 棘轮：候选臂在触发题（T06）不劣于基线，且回归题（T03）零退化
  - 裁判同向率
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze import gate, strip_label  # noqa: E402

TRIGGER = "T06"
REGRESSION = "T03"


def main() -> None:
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    rows = [r for r in data["rows"] for r in ([r] if "scoreA" in r else r.get("reps", []))]
    rows = [r for r in rows if "scoreA" in r]

    # ---- 机械关（关 2 的可判定部分）：两臂冠军 + 全部候选 ----
    def gate_stats(rows, champ_key, tracks_key):
        champs, all_c = [], []
        for r in rows:
            if r.get(champ_key):
                champs.append((r["id"], r[champ_key], gate(strip_label(r[champ_key]))["hard"]))
            for t in (r.get(tracks_key) or {}).get("A", []) + (r.get(tracks_key) or {}).get("C", []):
                all_c.append(gate(t)["hard"])
            for b in (r.get(tracks_key) or {}).get("B", []):
                if b.get("punchline") and b["punchline"] != "无":
                    all_c.append(gate(b["punchline"])["hard"])
        champ_ok = sum(1 for _, _, f in champs if not f)
        all_ok = sum(1 for f in all_c if not f)
        return {
            "champion_compliance": champ_ok / len(champs) if champs else 0,
            "pool_compliance": all_ok / len(all_c) if all_c else 0,
            "champion_fails": [f"{i}: {c} {f}" for i, c, f in champs if f],
        }

    st_a = gate_stats(rows, "champA", "tracksA")
    st_c = gate_stats(rows, "champS", "tracksS")
    print(f"基线臂（三轨并行）  冠军合规 {st_a['champion_compliance']:.0%}  池合规 {st_a['pool_compliance']:.0%}")
    print(f"候选臂（单实例）    冠军合规 {st_c['champion_compliance']:.0%}  池合规 {st_c['pool_compliance']:.0%}")
    for name, st in (("基线", st_a), ("候选", st_c)):
        for f in st["champion_fails"]:
            print(f"  [{name} 冠军违规] {f}")

    # ---- 盲评分与棘轮 ----
    per_item = {}
    for r in rows:
        per_item.setdefault(r["id"], []).append((r["scoreA"], r["scoreS"]))

    verdicts = {}
    for iid, pairs in sorted(per_item.items()):
        d = statistics.fmean(s - a for a, s in pairs)
        wins = sum(1 for a, s in pairs if s > a)
        ties = sum(1 for a, s in pairs if s == a)
        losses = sum(1 for a, s in pairs if s < a)
        verdicts[iid] = {"delta_S_minus_A": round(d, 2), "S_win": wins, "tie": ties, "A_win": losses}
        kind = "触发题" if iid == TRIGGER else ("回归题" if iid == REGRESSION else iid)
        print(f"{kind} {iid}: Δ(S−A)={d:+.2f}  候选胜 {wins} / 平 {ties} / 基线胜 {losses}")

    # ---- 裁判同向率（单裁判，按重复内正负号） ----
    signs = [(1 if s > a else (-1 if s < a else 0)) for a, s in [p for ps in per_item.values() for p in ps]]
    non_tie = [x for x in signs if x]
    print(f"有效同向样本: {len(non_tie)}/{len(signs)}")

    tri = verdicts.get(TRIGGER, {})
    reg = verdicts.get(REGRESSION, {})
    trigger_ok = tri.get("delta_S_minus_A", -9) >= 0
    no_regression = reg.get("delta_S_minus_A", -9) >= 0
    print()
    if trigger_ok and no_regression:
        print("棘轮判定：✓ 通过——候选在触发题不劣于基线，回归题零退化，可交付")
    else:
        print(f"棘轮判定：✗ 不通过——触发 {'过' if trigger_ok else '不过'}，回归 {'零退化' if no_regression else '有退化'}；退回修正并重跑")

    Path("ab_audit.json").write_text(
        json.dumps({"baseline": st_a, "candidate": st_c, "verdicts": verdicts,
                    "ratchet_pass": bool(trigger_ok and no_regression)},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("→ ab_audit.json")


if __name__ == "__main__":
    main()
