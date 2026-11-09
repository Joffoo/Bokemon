#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""双臂发散实验执行器：P（三轨三个独立上下文） vs S（单 Agent 一次发散）。

除"上下文边界"外，其余变量一律对齐：同一 Stage 0、同一模型、同一温度、
同一候选预算、同一 Stage 2 裁判、同一重试策略。

用法：
    python run_eval.py --mock --limit 6 --repeats 1     # 干跑，不联网
    python run_eval.py --limit 6 --repeats 1            # 真实试跑
    python run_eval.py --workers 4                      # 全量
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

import prompts as promptlib

HERE = Path(__file__).resolve().parent
LABEL = {"A": "[A轨体面破绽]", "B": "[B轨异业动作]", "C": "[C轨物理死磕]"}

_print_lock = threading.Lock()


# --------------------------------------------------------------------------- #
# 模型调用
# --------------------------------------------------------------------------- #
def load_config(path: Path) -> tuple[dict, str]:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    key = cfg.get("api_key") or os.environ.get(cfg.get("api_key_env", ""), "")
    if not key:
        raise SystemExit(
            f"[config] 没有可用的 API Key：请在 {path} 填 api_key，"
            f"或设置环境变量 {cfg.get('api_key_env')}。"
        )
    return cfg, key


def endpoint_of(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions" if base.endswith("/v1") else f"{base}/v1/chat/completions"


def chat(
    cfg: dict,
    key: str,
    system: str,
    user: str,
    image_url: str | None = None,
    mock_tag: tuple | None = None,
) -> dict:
    """一次 chat completion。mock_tag 非空时走本地假数据。"""
    t0 = time.time()

    if mock_tag is not None:
        time.sleep(0.01)
        content = _mock_reply(*mock_tag)
        return {
            "content": content,
            "usage": {"prompt_tokens": len(system) + len(user), "completion_tokens": len(content)},
            "latency_ms": int((time.time() - t0) * 1000),
        }

    messages = [{"role": "system", "content": system}]
    if image_url:
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        )
    else:
        messages.append({"role": "user", "content": user})

    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": cfg.get("temperature", 0.7),
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    url = endpoint_of(cfg["base_url"])
    retries = int(cfg.get("max_retries", 3))
    timeout = float(cfg.get("timeout", 45))

    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:160]}")
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            if not content:
                raise RuntimeError("空 content")
            return {
                "content": content,
                "usage": data.get("usage", {}) or {},
                "latency_ms": int((time.time() - t0) * 1000),
            }
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if attempt >= retries:
                break
            time.sleep(2 ** attempt)
    raise RuntimeError(f"调用失败（{retries + 1} 次）：{last_err}")


# --------------------------------------------------------------------------- #
# 解析与清洗
# --------------------------------------------------------------------------- #
def parse_jsonish(text: str):
    """容错解析：直接解析 → 去围栏 → 截取首尾括号 → 逐行数组拼接。

    最后一档处理模型偶发的多行输出：每行各自是一个合法 JSON 数组
    （["a"]\\n["b"]\\n["c"]），逐行解析后拼成一个大数组。
    """
    if not text:
        raise ValueError("空回复")
    candidates = [text.strip()]
    fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.S)
    candidates.append(fenced)
    for c in candidates:
        try:
            return json.loads(c)
        except Exception:  # noqa: BLE001
            pass
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        i, j = fenced.find(open_ch), fenced.rfind(close_ch)
        if i != -1 and j > i:
            try:
                return json.loads(fenced[i : j + 1])
            except Exception:  # noqa: BLE001
                continue
    lines = []
    for ln in fenced.splitlines():
        ln = ln.strip().rstrip(",")
        if ln.startswith("[") and ln.endswith("]"):
            try:
                lines.extend(json.loads(ln))
                continue
            except Exception:  # noqa: BLE001
                pass
        if ln.startswith("{") and ln.endswith("}"):
            try:
                lines.append(json.loads(ln))
                continue
            except Exception:  # noqa: BLE001
                pass
    if lines:
        return lines
    raise ValueError(f"JSON 解析失败：{text[:120]}")


def clean_line(value) -> str:
    """两臂共用的清洗函数——必须完全一致，否则等于给某一臂额外加工。"""
    if value is None:
        return ""
    s = str(value).strip().strip('`"“”「」『』')
    s = re.sub(r"^(?:\[[ABC]轨[^\]]*\]|Subagent\s*[ABC]|轨道\s*[ABC]|[ABC]轨)[：:\s\-—]*", "", s)
    s = s.strip().strip("。，、；：！？.,;:!?")
    return s.replace(" ", "")


def norm_string_list(raw) -> list[str]:
    if isinstance(raw, dict):
        raw = list(raw.values())
    if not isinstance(raw, list):
        return []
    return [x for x in (clean_line(v) for v in raw) if x]


def norm_track_b(raw) -> list[dict]:
    if isinstance(raw, dict):
        raw = [{"category": str(k), "punchline": v} for k, v in raw.items()]
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        if isinstance(item, dict):
            out.append(
                {
                    "category": str(item.get("category", "")).strip(),
                    "punchline": clean_line(item.get("punchline") or item.get("line") or ""),
                }
            )
        else:
            out.append({"category": "", "punchline": clean_line(item)})
    return out


def build_pool(tracks: dict) -> list[str]:
    """与 index.html 完全一致的合并规则。"""
    lines = [f"{LABEL['A']} {x}" for x in tracks.get("A", [])]
    lines += [f"{LABEL['B']} {x['punchline']}" for x in tracks.get("B", [])]
    lines += [f"{LABEL['C']} {x}" for x in tracks.get("C", [])]
    return [ln for ln in lines if ln and "无" not in ln and len(ln) > 5]


def pick_champion(parsed, pool: list[str]) -> str:
    if not isinstance(parsed, dict):
        return clean_line(pool[0]) if pool else ""
    fc = clean_line(parsed.get("final_champion"))
    if fc and "无合格" not in fc and "全灭" not in fc:
        return fc
    recast = parsed.get("recast_variants") or {}
    if isinstance(recast, dict):
        for key in ("cold_sketch", "monologue", "quantified"):
            c = clean_line(recast.get(key))
            if c and "无合格" not in c:
                return c
    ic = clean_line(parsed.get("initial_champion"))
    if ic and "无合格" not in ic and "全灭" not in ic:
        return ic
    return clean_line(pool[0]) if pool else ""


# --------------------------------------------------------------------------- #
# 单次运行
# --------------------------------------------------------------------------- #
def run_arm(
    arm: str,
    rendered: dict[str, str],
    stage0: dict,
    cfg: dict,
    key: str,
    image_url: str | None,
    item: dict,
    repeat: int,
    track_order: str,
    mock: bool,
) -> dict:
    tracks = {"A": [], "B": [], "C": []}
    errors: list[str] = []
    usage = {"prompt": 0, "completion": 0}
    latency = 0

    def note(res: dict) -> None:
        nonlocal latency
        usage["prompt"] += int(res["usage"].get("prompt_tokens", 0))
        usage["completion"] += int(res["usage"].get("completion_tokens", 0))
        latency = max(latency, res["latency_ms"])

    if arm == "P":
        def worker(track: str) -> None:
            tag = ("track", item["id"], arm, repeat, track) if mock else None
            res = chat(cfg, key, rendered[track], f"命题：{item.get('prompt') or '根据图片'}", image_url, tag)
            note(res)
            parsed = parse_jsonish(res["content"])
            tracks[track] = norm_track_b(parsed) if track == "B" else norm_string_list(parsed)

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(worker, t): t for t in ("A", "B", "C")}
            for fut in as_completed(futures):
                t = futures[fut]
                try:
                    fut.result()
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{t}: {exc}")
                    tracks[t] = []
    else:
        sys_s = promptlib.build_arm_s(rendered, track_order)
        tag = ("single", item["id"], arm, repeat, track_order) if mock else None
        res = chat(cfg, key, sys_s, f"命题：{item.get('prompt') or '根据图片'}", image_url, tag)
        note(res)
        try:
            parsed = parse_jsonish(res["content"])
            tracks["A"] = norm_string_list(parsed.get("A"))
            tracks["B"] = norm_track_b(parsed.get("B"))
            tracks["C"] = norm_string_list(parsed.get("C"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"single: {exc}")

    pool = build_pool(tracks)

    champion = ""
    if pool:
        s2_user = (
            f"【大喜利原题】: {item.get('prompt') or '看图大喜利'}\n"
            f"所有候选短句池：\n" + "\n".join(pool) + "\n"
            "请对照原题严苛审判、公诉人两两死斗与三向句法重铸！"
        )
        tag = ("stage2", item["id"], arm, repeat, "") if mock else None
        res = chat(cfg, key, rendered["stage2"], s2_user, image_url, tag)
        note(res)
        try:
            champion = pick_champion(parse_jsonish(res["content"]), pool)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"stage2: {exc}")
            champion = clean_line(pool[0]) if pool else ""

    return {
        "tracks": tracks,
        "pool": pool,
        "champion": champion,
        "tokens": usage,
        "latency_ms": latency,
        "errors": errors,
    }


def run_item(
    item: dict,
    cfg: dict,
    key: str,
    repeats: int,
    prompt_fp: str,
    mock: bool,
) -> list[dict]:
    prompt_text = item.get("prompt", "")
    image_url = None
    if item.get("image_path"):
        p = Path(item["image_path"])
        if not p.is_absolute():
            p = HERE / p
        if p.exists():
            image_url = "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()
        elif not mock:
            raise SystemExit(f"[items] 图片不存在：{p}")

    # Stage 0：每题只跑一次，两臂共用
    s0_user = prompt_text or "看图大喜利命题：请根据上传的图片进行物理地基遥测"
    s0_tag = ("stage0", item["id"], "", 0, "") if mock else None
    s0_res = chat(cfg, key, promptlib.build({}, prompt_text)["stage0"], s0_user, image_url, s0_tag)
    try:
        stage0 = parse_jsonish(s0_res["content"])
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Stage 0 解析失败（{item['id']}）：{exc}") from exc

    rendered = promptlib.build(stage0, prompt_text)
    records = []

    for repeat in range(1, repeats + 1):
        rng = random.Random(f"{item['id']}|{repeat}")
        first = "P" if rng.random() < 0.5 else "S"
        track_order = ("ABC", "BCA", "CAB")[(repeat - 1) % 3]

        for arm in (first, "S" if first == "P" else "P"):
            res = run_arm(
                arm, rendered, stage0, cfg, key, image_url, item, repeat, track_order, mock
            )
            records.append(
                {
                    "run_id": f"{item['id']}|{arm}|r{repeat}",
                    "item_id": item["id"],
                    "type": item.get("type", "text"),
                    "repeat": repeat,
                    "arm": arm,
                    "order": f"{first}-first",
                    "track_order": track_order,
                    "model": "mock" if mock else cfg["model"],
                    "temperature": cfg.get("temperature", 0.7),
                    "prompt_hash": prompt_fp,
                    "stage0": stage0,
                    "tracks": res["tracks"],
                    "pool": res["pool"],
                    "champion": res["champion"],
                    "tokens": res["tokens"],
                    "latency_ms": res["latency_ms"],
                    "errors": res["errors"],
                }
            )
    return records


# --------------------------------------------------------------------------- #
# mock 数据
# --------------------------------------------------------------------------- #
_MOCK_LINES = [
    "梯子塞进电梯口",
    "拿量角器量老板脸色",
    "把公章栓上牵引绳",
    "用保鲜膜裹住发动机",
    "给门卫递一张取号纸",
    "把话筒吊在脚手架上",
    "对合同吹一口灵气",
    "拿体温计量水泥标号",
    "用订书机钉住请假条",
    "把红包塞进安检筐",
    "拿理发推子修草坪",
    "把欠条折成纸飞机",
]
_MOCK_DOMAINS = [
    "[1] 市政危房维保",
    "[2] 临期商超早市",
    "[3] 驾校科目考场",
    "[8] 殡葬法事公墓",
    "[9] 县城草台剧组",
    "[13] 古董文玩鉴定",
    "[21] 修锁配钥匙",
    "[24] 高速收费站",
]


def _pick(seed_text: str, n: int) -> list[str]:
    h = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16)
    return [_MOCK_LINES[(h >> (i * 5)) % len(_MOCK_LINES)] for i in range(n)]


def _mock_reply(kind: str, item_id: str, arm: str, repeat: int, track: str) -> str:
    if kind == "stage0":
        return json.dumps(
            {
                "raw_telemetry": "演示地基：一个人蹲在路边，脚边一只破了的口袋",
                "forbidden_baseline": [
                    "[阱 1 现实观察与字面拆解] 钱包丢了很心疼",
                    "[阱 2 廉价网梗] 我裂开了",
                    "[阱 3 情绪直给与自行吐槽] 他好惨啊",
                ],
                "secular_domains": _MOCK_DOMAINS,
            },
            ensure_ascii=False,
        )
    if kind == "track":
        lines = _pick(f"{item_id}|{arm}|{repeat}|{track}", 3)
        if track == "B":
            return json.dumps(
                [{"category": d, "punchline": _pick(f"{item_id}{d}{repeat}", 1)[0]} for d in _MOCK_DOMAINS],
                ensure_ascii=False,
            )
        return json.dumps(lines, ensure_ascii=False)
    if kind == "single":
        return json.dumps(
            {
                "A": _pick(f"{item_id}|S|{repeat}|A", 3),
                "B": [
                    {"category": d, "punchline": _pick(f"{item_id}{d}S{repeat}", 1)[0]}
                    for d in _MOCK_DOMAINS
                ],
                "C": _pick(f"{item_id}|S|{repeat}|C", 3),
            },
            ensure_ascii=False,
        )
    if kind == "stage2":
        champ = _pick(f"{item_id}|{arm}|{repeat}|champ", 1)[0]
        return json.dumps(
            {
                "track_champions": {"trackA": champ, "trackB": champ, "trackC": champ},
                "initial_champion": champ,
                "recast_variants": {"cold_sketch": champ, "monologue": champ, "quantified": champ},
                "final_champion": champ,
                "crowning_reason": "mock",
            },
            ensure_ascii=False,
        )
    raise ValueError(kind)


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(HERE / "config.json"))
    ap.add_argument("--items", default=str(HERE / "items.jsonl"))
    ap.add_argument("--out", default="")
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 题")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    out_path = Path(args.out) if args.out else HERE / ("runs.mock.jsonl" if args.mock else "runs.jsonl")
    items_path = Path(args.items)
    if not items_path.exists():
        fallback = HERE / "items.sample.jsonl"
        if fallback.exists():
            print(f"[items] 找不到 {items_path.name}，回退到 items.sample.jsonl（正式实验请先冻结 items.jsonl）")
            items_path = fallback
        else:
            raise SystemExit(f"[items] 找不到 {items_path}（先用 items.sample.jsonl 改名或自备）")

    items = [json.loads(ln) for ln in items_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if args.limit:
        items = items[: args.limit]

    cfg = {"base_url": "", "model": "mock", "temperature": 0.7, "max_retries": 0, "timeout": 5}
    key = ""
    if not args.mock:
        cfg, key = load_config(Path(args.config))

    fp = promptlib.fingerprint()
    done: set[str] = set()
    if out_path.exists():
        for ln in out_path.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                try:
                    done.add(json.loads(ln)["run_id"])
                except Exception:  # noqa: BLE001
                    pass

    print(f"提示词指纹 {fp} | 模型 {cfg['model']} | 题数 {len(items)} | 重复 {args.repeats}")
    print(f"输出 {out_path.name} | 已有 {len(done)} 条，断点续跑")

    manifest = {
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prompt_hash": fp,
        "model": cfg.get("model"),
        "temperature": cfg.get("temperature"),
        "items_file": str(items_path),
        "items_hash": hashlib.sha256(items_path.read_bytes()).hexdigest()[:12],
        "n_items": len(items),
        "repeats": args.repeats,
        "arms": ["P", "S"],
        "mock": args.mock,
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def work(item: dict) -> list[dict]:
        recs = run_item(item, cfg, key, args.repeats, fp, args.mock)
        return [r for r in recs if r["run_id"] not in done]

    written = 0
    with open(out_path, "a", encoding="utf-8") as fh, ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(work, it): it for it in items}
        for fut in as_completed(futures):
            item = futures[fut]
            try:
                recs = fut.result()
            except Exception as exc:  # noqa: BLE001
                with _print_lock:
                    print(f"  ✗ {item['id']}: {exc}")
                continue
            for r in recs:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                written += 1
            fh.flush()
            with _print_lock:
                champs = ", ".join(f"{r['arm']}={r['champion']}" for r in recs)
                print(f"  ✓ {item['id']} ({len(recs)} 条) {champs}")

    print(f"完成：新增 {written} 条 → {out_path}")


if __name__ == "__main__":
    main()
