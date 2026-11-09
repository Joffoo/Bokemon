#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""机械关卡 + 聚类 bootstrap + 预注册判定，输出 report.md / summary.json。

判定规则写在 DESIGN.md 第 7 节；这里只负责执行，不负责解释。
规则若与 DESIGN.md 不一致，以 DESIGN.md 为准，并改这里的代码——不是反过来。

用法：
    python analyze.py --mock
    python analyze.py
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent

PUNCT = set("，。、；：？！…—·～「」『』《》（）【】,.;:?!\"'“”‘’()[]{}<>~@#$%^&*_+=`|/\\")
# 结构助词：按词性判定，不做子串匹配——否则「地砖」「地毯」「过路票」会被误杀
PARTICLES = ("的", "地", "得", "了", "着", "过")
BANNED_PHRASES = ("其实", "原来", "因为", "所以")

try:  # 可选依赖：没有 jieba 时动词关卡标为 skipped，不静默放行
    import jieba.posseg as pseg

    _HAS_JIEBA = True
except Exception:  # noqa: BLE001
    _HAS_JIEBA = False


def strip_label(line: str) -> str:
    return re.sub(r"^\[[ABC]轨[^\]]*\]\s*", "", line).strip()


def has_verb(text: str) -> bool | None:
    if not _HAS_JIEBA:
        return None
    try:
        return any(flag.startswith("v") for _, flag in pseg.cut(text))
    except Exception:  # noqa: BLE001
        return None


def banned_hits(text: str) -> list[str]:
    """虚词黑名单。有 jieba 时只看"助词词性"的单字，避免把「地砖/过路票」当违规。"""
    hits = [p for p in BANNED_PHRASES if p in text]
    if not _HAS_JIEBA:
        return hits + [p for p in PARTICLES if p in text]
    try:
        for word, flag in pseg.cut(text):
            if word in PARTICLES and flag.startswith("u"):
                hits.append(word)
    except Exception:  # noqa: BLE001
        return hits + [p for p in PARTICLES if p in text]
    return hits


def gate(line: str) -> dict[str, list[str]]:
    """硬关卡（确定性规则）与软关卡（启发式判定）分开。

    硬关卡是提示词里白纸黑字的规则，脚本能百分百判定，用来当门槛。
    软关卡「含动词」依赖分词，jieba 在 8~14 字的短句上会误判（例如把「塞进」标成人名 nr），
    所以只做诊断，不当门槛——否则会拿一个噪声尺子去否掉两臂。
    """
    body = strip_label(line)
    if not body:
        return {"hard": ["空句"], "soft": []}
    hard: list[str] = []
    soft: list[str] = []
    if len(body) > 14:
        hard.append("超14字")
    if any(ch in PUNCT for ch in body):
        hard.append("含标点或空格")
    if banned_hits(body):
        hard.append("含虚词")
    if has_verb(body) is False:
        soft.append("动词可疑")
    return {"hard": hard, "soft": soft}


def bigrams(line: str) -> set[str]:
    s = strip_label(line)
    return {s[i : i + 2] for i in range(len(s) - 1)}


def diversity(pool: list[str]) -> float:
    if len(pool) < 2:
        return 0.0
    ds = []
    for i in range(len(pool)):
        for j in range(i + 1, len(pool)):
            a, b = bigrams(pool[i]), bigrams(pool[j])
            union = len(a | b)
            ds.append(1 - len(a & b) / union if union else 0.0)
    return statistics.fmean(ds)


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, int(math.ceil(0.95 * len(s))) - 1)
    return s[max(0, idx)]


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def bootstrap_ci(deltas_by_item: dict[str, list[float]], iters: int = 10000, seed: int = 7) -> tuple[float, float]:
    items = list(deltas_by_item)
    if not items:
        return (0.0, 0.0)
    rng = random.Random(seed)
    means = []
    for _ in range(iters):
        pick = [rng.choice(items) for _ in items]
        vals = [v for it in pick for v in deltas_by_item[it]]
        if vals:
            means.append(statistics.fmean(vals))
    if not means:
        return (0.0, 0.0)
    means.sort()
    lo = means[int(0.025 * len(means))]
    hi = means[int(0.975 * len(means)) - 1]
    return (lo, hi)


def arm_stats(runs: list[dict]) -> dict:
    by_arm: dict[str, dict] = {}
    for arm in ("P", "S"):
        rs = [r for r in runs if r["arm"] == arm]
        total = len(rs)
        usable = [r for r in rs if r["pool"] and r["champion"]]
        cands = [c for r in rs for c in r["pool"]]
        gates = {c: gate(c) for c in cands}
        hard_fail = [c for c, g in gates.items() if g["hard"]]
        soft_flag = [c for c, g in gates.items() if g["soft"]]
        b_ok, b_expect = 0, 0
        for r in rs:
            domains = (r.get("stage0") or {}).get("secular_domains") or []
            b_expect += int(r.get("b_expected") or max(1, len(domains)))
            if r.get("b_count") is not None:
                b_ok += int(r["b_count"])
            else:
                b_ok += len([x for x in r["tracks"].get("B", []) if x.get("punchline") and "无" not in x["punchline"]])
        by_arm[arm] = {
            "runs": total,
            "usable_rate": len(usable) / total if total else 0.0,
            "compliance": 1 - len(hard_fail) / len(cands) if cands else 0.0,
            "champion_compliance": (
                1 - sum(1 for r in usable if gate(r["champion"])["hard"]) / len(usable) if usable else 0.0
            ),
            "verb_flag_rate": len(soft_flag) / len(cands) if cands else 0.0,
            "fail_reasons": {
                f: sum(1 for g in gates.values() if f in g["hard"])
                for f in ("超14字", "含标点或空格", "含虚词", "空句")
            },
            "error_rate": sum(1 for r in rs if r["errors"]) / total if total else 0.0,
            "p95_latency_ms": p95([r["latency_ms"] for r in rs]),
            "tokens": sum(r["tokens"].get("prompt", 0) + r["tokens"].get("completion", 0) for r in rs),
            "diversity": statistics.fmean([diversity(r["pool"]) for r in rs if len(r["pool"]) > 1]) if rs else 0.0,
            "b_budget_ratio": b_ok / b_expect if b_expect else 0.0,
        }
    return by_arm


def decide(stats: dict, delta: float, ci: tuple[float, float]) -> tuple[str, str]:
    p, s = stats["P"], stats["S"]
    gate_fail = []
    for name, st in (("P", p), ("S", s)):
        if st["usable_rate"] < 0.95:
            gate_fail.append(f"{name} 可用率 {st['usable_rate']:.0%} < 95%")
        if st["champion_compliance"] < 0.95:
            gate_fail.append(f"{name} 冠军合规率 {st['champion_compliance']:.0%} < 95%")
        if st["error_rate"] > 0.03:
            gate_fail.append(f"{name} 失败率 {st['error_rate']:.1%} > 3%")
        if st["p95_latency_ms"] > 45000:
            gate_fail.append(f"{name} p95 {st['p95_latency_ms']:.0f}ms > 45s")
        if st["b_budget_ratio"] < 0.70:
            gate_fail.append(f"{name} B 轨预算仅 {st['b_budget_ratio']:.0%}")
    if gate_fail:
        return "实验无效", "；".join(gate_fail)

    if delta >= 0.30 and ci[0] > 0:
        return "三轨并行胜", f"Δ={delta:+.2f}，CI 下界 {ci[0]:+.2f} > 0"
    if delta <= -0.30 and ci[1] < 0:
        return "单 Agent 胜", f"Δ={delta:+.2f}，CI 上界 {ci[1]:+.2f} < 0"

    if s["error_rate"] > p["error_rate"] + 0.05 or s["p95_latency_ms"] > p["p95_latency_ms"] * 1.2:
        return "平局 → 保留三轨", "单 Agent 在失败率或延迟上更差（平局规则 1）"
    if s["tokens"] < p["tokens"]:
        return "平局 → 切单 Agent", f"无实际差异；单 Agent token 少 {1 - s['tokens'] / max(1, p['tokens']):.0%}（平局规则 2）"
    return "平局 → 切单 Agent", "无实际差异且单 Agent 无成本劣势（平局规则 3：维护面更小）"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="")
    ap.add_argument("--judgements", default="")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--iters", type=int, default=10000)
    ap.add_argument("--min-items", type=int, default=12, help="少于该题数只报数值，不下结论")
    args = ap.parse_args()

    runs_path = Path(args.runs) if args.runs else HERE / ("runs.mock.jsonl" if args.mock else "runs.jsonl")
    jdg_path = Path(args.judgements) if args.judgements else HERE / ("judgements.mock.jsonl" if args.mock else "judgements.jsonl")

    runs = load_jsonl(runs_path)
    judges = load_jsonl(jdg_path)
    if not runs:
        raise SystemExit(f"[analyze] 没有数据：{runs_path}")

    stats = arm_stats(runs)

    per_cmp: list[dict] = []
    for row in judges:
        scores = [j["score"] for j in row["judges"]]
        if not scores:
            continue
        sp = statistics.fmean(s["P"] for s in scores)
        ss = statistics.fmean(s["S"] for s in scores)
        per_cmp.append(
            {
                "item_id": row["item_id"],
                "type": row["type"],
                "delta": sp - ss,
                "winner": "P" if sp > ss else ("S" if ss > sp else "tie"),
            }
        )

    deltas_by_item: dict[str, list[float]] = {}
    for c in per_cmp:
        deltas_by_item.setdefault(c["item_id"], []).append(c["delta"])
    all_deltas = [c["delta"] for c in per_cmp]

    agree, multi = 0, 0
    for row in judges:
        if len(row["judges"]) < 2:
            continue
        multi += 1
        signs = {(j["score"]["P"] > j["score"]["S"]) - (j["score"]["P"] < j["score"]["S"]) for j in row["judges"]}
        if len(signs) == 1:
            agree += 1
    judge_agreement = agree / multi if multi else None
    delta = statistics.fmean(all_deltas) if all_deltas else 0.0
    ci = bootstrap_ci(deltas_by_item, args.iters)

    wins = {k: sum(1 for c in per_cmp if c["winner"] == k) for k in ("P", "tie", "S")}

    def split(rows: list[dict]) -> tuple[float, int]:
        v = [r["delta"] for r in rows]
        return (statistics.fmean(v) if v else 0.0, len(v))

    d_text, n_text = split([c for c in per_cmp if c["type"] != "image"])
    d_img, n_img = split([c for c in per_cmp if c["type"] == "image"])

    decision, reason = decide(stats, delta, ci)
    if len(deltas_by_item) < args.min_items:
        decision = "样本不足（pilot）"
        reason = f"{len(deltas_by_item)} 题 < 判定下限 {args.min_items} 题：只报数值，不做架构结论"
    div_gap = stats["P"]["diversity"] - stats["S"]["diversity"]

    summary = {
        "decision": decision,
        "reason": reason,
        "n_pairs": len(per_cmp),
        "n_items": len(deltas_by_item),
        "delta": round(delta, 3),
        "ci95": [round(ci[0], 3), round(ci[1], 3)],
        "wins": wins,
        "judge_agreement": None if judge_agreement is None else round(judge_agreement, 3),
        "by_type": {"text": {"delta": round(d_text, 3), "n": n_text}, "image": {"delta": round(d_img, 3), "n": n_img}},
        "diversity_gap": round(div_gap, 3),
        "arms": stats,
    }
    (HERE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    def pct(x: float) -> str:
        return f"{x * 100:.1f}%"

    lines = [
        "# 发散架构对照实验：三轨并行 vs 单 Agent",
        "",
        f"> 样本：{len(deltas_by_item)} 题 / {len(per_cmp)} 组比较　模型：{runs[0].get('model')}　"
        f"提示词指纹：{runs[0].get('prompt_hash')}",
        "",
    ]
    if runs[0].get("model") == "mock":
        lines += ["> ⚠️ **干跑数据（mock）**：只验证管道是否通，任何数值都不可用于决策。", ""]
    lines += [
        "## 判定",
        "",
        f"**{decision}** —— {reason}",
        "",
        f"- 主指标 Δ（P−S，5 分制）：**{delta:+.2f}**，95% CI [{ci[0]:+.2f}, {ci[1]:+.2f}]",
        f"- 胜/平/负：P {wins['P']} / 平 {wins['tie']} / S {wins['S']}",
        "",
        "## 硬门槛",
        "",
        "| 门槛 | P（三轨） | S（单 Agent） | 阈值 |",
        "|---|---|---|---|",
        f"| 可用率 | {pct(stats['P']['usable_rate'])} | {pct(stats['S']['usable_rate'])} | ≥95% |",
        f"| 池合规率（诊断） | {pct(stats['P']['compliance'])} | {pct(stats['S']['compliance'])} | 门槛 95% |",
        f"| 冠军合规率（交付层） | {pct(stats['P']['champion_compliance'])} | {pct(stats['S']['champion_compliance'])} | ≥95% |",
        f"| 动词可疑率（诊断） | {pct(stats['P']['verb_flag_rate'])} | {pct(stats['S']['verb_flag_rate'])} | 不进门槛 |",
        f"| 请求失败率 | {pct(stats['P']['error_rate'])} | {pct(stats['S']['error_rate'])} | ≤3% |",
        f"| p95 延迟 | {stats['P']['p95_latency_ms'] / 1000:.1f}s | {stats['S']['p95_latency_ms'] / 1000:.1f}s | ≤45s |",
        f"| B 轨预算 | {pct(stats['P']['b_budget_ratio'])} | {pct(stats['S']['b_budget_ratio'])} | ≥70% |",
        f"| 总 token | {stats['P']['tokens']} | {stats['S']['tokens']} | — |",
        "",
        "## 机制诊断",
        "",
        f"- 池内多样性（2-gram Jaccard 距离）：P {stats['P']['diversity']:.3f} / S {stats['S']['diversity']:.3f}"
        f"（差 {div_gap:+.3f}）",
        f"- 分层 Δ：文字 {d_text:+.2f}（n={n_text}） / 图像 {d_img:+.2f}（n={n_img}）",
        f"- 裁判一致率：{'不可用（单裁判）' if judge_agreement is None else pct(judge_agreement) + '（同向占比）'}",
        "",
    ]
    if _HAS_JIEBA:
        lines.append("> 合规率只算硬关卡（长度/标点/空格/虚词）。动词关卡靠分词，短句上误判率高，仅作诊断。")
    else:
        lines.append("> ⚠ 未安装 jieba，动词诊断已跳过；硬关卡不受影响。")

    lines += [
        "",
        "## 读法",
        "",
        "1. 先看判定行：`实验无效` 不代表结论，只代表这轮数据不算数。",
        "2. 再看 Δ 与 CI：CI 跨 0 就不要说谁更好，按平局规则走。",
        "3. 再看机制：若判三轨胜但多样性没差，赢的不是隔离，必须在报告里另找解释。",
        "4. 最后看分层：若只有图像题有差，考虑分路设计而不是一刀切换架构。",
        "",
    ]
    (HERE / "report.md").write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    print(f"\n→ report.md / summary.json")


if __name__ == "__main__":
    main()
