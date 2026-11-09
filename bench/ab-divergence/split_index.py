#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""index.html 拆分器（方案 B 最终版 v2：全局连续分区，无空隙无重叠）。

架构：JS 全量外置为经典脚本（file:// 双击可用）。
- setup 顶层按「连续分区」切分：每个 8 缩进顶层声明拥有 [自身, 下一声明) 区间，
  区间按首函数名映射到目标文件——任意行必有所属，不可能丢也不可能重；
- 状态区(1290–1485) / onMounted 块 / loadSavedConfig() 调用 / exportedBundle 单独指派；
- handleSend / rerollPunchline 在 try 包络内按语句缝切成编排壳 + 分段函数；
- 3 张 base64 预设图分块进 01-assets-*.js（运行时字符串逐字节相同）。

安全性：ADDED/REMOVED 双向多重集校验，任何未登记差异拒绝落盘。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "index.html"
JS = ROOT / "js"
THRESHOLD = 20480
HEADER = "// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）"

src = SRC.read_text(encoding="utf-8")
L = src.split("\n")
ADDED: list[str] = []
REMOVED: list[str] = []


def find_one(pat: str, lo: int = 1, hi: int | None = None, last: bool = False) -> int:
    hits = [i for i, ln in enumerate(L, 1) if lo <= i <= (hi or len(L)) and re.search(pat, ln)]
    if not hits:
        raise SystemExit(f"[anchor] /{pat}/ 零命中")
    if len(hits) > 1 and not last:
        raise SystemExit(f"[anchor] /{pat}/ 命中 {len(hits)} 处 {hits[:6]}，需要恰好 1 处")
    return hits[-1] if last else hits[0]


A = {}
A["script_open"] = find_one(r"^\s*<script>\s*$", 1000, 1200)
A["createApp"] = find_one(r"^\s*createApp\(\{\s*$")
A["mount"] = find_one(r"\}\)\.mount\('#app'\);")
A["setup_head"] = find_one(r"^\s*setup\(\)\s*\{\s*$")
A["decl_showToast"] = find_one(r"^\s{8}function showToast\(msg, duration = 2000\) \{$")
A["onmounted_comment"] = find_one(r"^\s{8}// Load configuration from localStorage on mount\s*$")
A["decl_reroll"] = find_one(r"^\s{8}async function rerollPunchline\(playerMsg\) \{$")
A["decl_handleSend"] = find_one(r"^\s{8}async function handleSend\(\) \{$")
A["decl_exported"] = find_one(r"^\s{8}const exportedBundle = \{$")
A["decl_parseJson"] = find_one(r"^\s{8}function parseJsonSafely\(text\) \{$")
A["call_loadSaved"] = find_one(r"^\s{8}loadSavedConfig\(\);\s*$")
A["seam1_send"] = find_one(r"^\s*// STAGE 1: 三轨一次发散", A["decl_handleSend"])
A["seam2_send"] = find_one(r"^\s*playerMsg\.pipelineState\.currentStage = 2;\s*$", A["seam1_send"], A["decl_exported"], last=True)
A["catch_send"] = find_one(r"^\s*\} catch \(err\) \{$", A["seam2_send"])
A["seam_reroll"] = find_one(r"^\s*playerMsg\.pipelineState\.currentStage = 2;\s*$", A["decl_reroll"], A["call_loadSaved"], last=True)
A["catch_reroll"] = find_one(r"^\s*\} catch \(err\) \{$", A["seam_reroll"], A["call_loadSaved"])
A["comment_llm"] = find_one(r"^\s*// Real LLM Re-roll pipeline", A["decl_reroll"])
A["try_send"] = find_one(r"^\s*try \{\s*$", A["decl_handleSend"], A["seam1_send"], last=True)
A["try_reroll"] = find_one(r"^\s*try \{\s*$", A["comment_llm"], A["comment_llm"] + 6)
A["comment_stage0"] = find_one(r"^\s*// STAGE 0: 地基遥测", A["decl_handleSend"])
A["tail_return"] = find_one(r"^\s*return exportedBundle;\s*$")

# ---------------------------------------------------------------- 连续分区
# setup 内全部顶层声明（8 缩进 const/let/function），每个声明拥有到下一声明的区间
decls = sorted(i for i, ln in enumerate(L, 1)
               if A["setup_head"] < i < A["mount"] and re.match(r"^\s{8}(?:async function |function |const [A-Za-z_$]|let [A-Za-z_$])", ln))

# 区间 → 文件的映射（按区间首声明名；未映射 = 报错）
NAME2FILE = {
    "showToast": "03-ui-audio.js", "copyPunchline": "03-ui-audio.js",
    "getAudioContext": "03-ui-audio.js", "toggleSound": "03-ui-audio.js",
    "playStartSound": "03-ui-audio.js", "playChampionSound": "03-ui-audio.js",
    "scrollToBottom": "03-ui-audio.js", "resetNewGame": "03-ui-audio.js",
    "loadSavedConfig": "04-settings.js", "openSettingsModal": "04-settings.js",
    "closeSettingsModal": "04-settings.js", "saveSettings": "04-settings.js",
    "purgeCredentials": "04-settings.js", "selectProvider": "04-settings.js",
    "fetchAvailableModels": "04-settings.js", "testApiConnection": "04-settings.js",
    "audioCtx": "04-settings.js",
    "handleImageUpload": "05-cards.js", "clearSelectedImage": "05-cards.js",
    "selectPresetPrompt": "05-cards.js", "selectImagePreset": "05-cards.js",
    "openImagePreview": "05-cards.js", "closeImagePreview": "05-cards.js",
    "downloadMeme": "05-cards.js", "findHostMessage": "05-cards.js",
    "crownManualVariant": "05-cards.js",
    "exportMarkdownHistory": "06-export.js",
    "parseJsonSafely": "00-helpers.js",
    "callLlmWithBackoff": "07-llm.js",
    "renderCanvasMeme": "08-meme.js", "drawRoundRect": "08-meme.js",
    "measureWrappedLines": "08-meme.js", "drawWrappedText": "08-meme.js",
    "renderSharePoster": "09-poster.js", "openSharePosterModal": "09-poster.js",
    "downloadSharePoster": "09-poster.js", "getStatusBadgeClass": "09-poster.js",
    "getStatusText": "09-poster.js",
    "runMockPreset": "10-demo.js",
    "exportedBundle": "18-app.js",
}

state_lo, state_hi = A["setup_head"] + 1, A["onmounted_comment"] - 1

def body(a: int, b: int) -> str:
    """[a, b] 闭区间行 → 文本（1 基，含端点）。"""
    return "\n".join(L[a - 1 : b])


FILES: dict[str, list[str]] = {}


def emit_part(fname: str, content: str) -> None:
    FILES.setdefault(fname, []).append(content)


def name_of(decl: int) -> str:
    m = re.match(r"^\s{8}(?:async function |function |const |let )([A-Za-z_$][\w$]*)", L[decl - 1])
    return m.group(1) if m else f"?{decl}"


# 特殊区间：state（显式范围）+ onMounted 块（裸语句区）
special = {A["setup_head"] + 1: ("state", state_lo, state_hi)}

regions = []  # (start, end, first_decl_line)
i = A["decl_showToast"]
while i <= A["mount"] - 2:
    if L[i - 1].strip() == "":
        i += 1
        continue
    if i == A["call_loadSaved"] - 1:  # 尾部裸调用（注释 + loadSavedConfig()）→ 18-app
        regions.append((i, i + 1, "bare"))
        i += 2
        continue
    nxt = [d for d in decls if d > i]
    end = (nxt[0] - 1) if nxt else A["mount"] - 2
    if i == A["decl_reroll"]:
        end = min(end, A["call_loadSaved"] - 2)  # reroll 区间在尾部裸调用前收口
    regions.append((i, end, i))
    i = end + 1

# 切掉 reroll/handleSend 的区间，换成编排壳 + 分段函数
BODIES: dict[str, str] = {}


def slice_region(start: int, end: int) -> None:
    global ADDED
    if start == A["decl_reroll"]:
        closer = L[region_end_of(end) - 1]
        print(f"[dbg reroll] start={start} end={end} try={A['try_reroll']} seam={A['seam_reroll']} closer={closer!r}")
        emit_part("11-reroll.js", body(start, A["try_reroll"]))
        emit_part("11-reroll.js", "\n".join([
            "          const allCandidates = await BK._rerollDiverge(playerMsg, promptText, imgUrl, s0);",
            "          await BK._rerollJudge(playerMsg, promptText, imgUrl, s0, allCandidates);",
            body(A["catch_reroll"], end),
        ]))
        ADDED += [
            "const allCandidates = await BK._rerollDiverge(playerMsg, promptText, imgUrl, s0);",
            "await BK._rerollJudge(playerMsg, promptText, imgUrl, s0, allCandidates);",
        ]
        emit_part("12-reroll-diverge.js", "\n".join([
            "async function _rerollDiverge(playerMsg, promptText, imgUrl, s0) {",
            body(A["try_reroll"] + 1, A["seam_reroll"] - 1),
            "        return allCandidates;",
            closer,
        ]))
        ADDED += ["async function _rerollDiverge(playerMsg, promptText, imgUrl, s0) {", "return allCandidates;", closer.strip()]
        emit_part("13-reroll-judge.js", "\n".join([
            "async function _rerollJudge(playerMsg, promptText, imgUrl, s0, allCandidates) {",
            body(A["seam_reroll"], A["catch_reroll"] - 1),
            closer,
        ]))
        ADDED += ["async function _rerollJudge(playerMsg, promptText, imgUrl, s0, allCandidates) {", closer.strip()]
        return
    if start == A["decl_handleSend"]:
        closer = L[region_end_of(end) - 1]
        emit_part("14-send.js", "\n".join([
            body(start, A["try_send"]),
            "          const parsedS0 = await BK._sendStage0(playerMsg, text, img);",
            "          const allCandidates = await BK._sendDiverge(playerMsg, text, img);",
            "          await BK._sendJudge(playerMsg, text, img, allCandidates);",
            body(A["catch_send"], end),
        ]))
        ADDED += [
            "const parsedS0 = await BK._sendStage0(playerMsg, text, img);",
            "const allCandidates = await BK._sendDiverge(playerMsg, text, img);",
            "await BK._sendJudge(playerMsg, text, img, allCandidates);",
        ]
        emit_part("15-send-stage.js", "\n".join([
            "async function _sendStage0(playerMsg, text, img) {",
            body(A["comment_stage0"] - 1, A["seam1_send"] - 1),
            "        return parsedS0;",
            closer,
        ]))
        ADDED += ["async function _sendStage0(playerMsg, text, img) {", "return parsedS0;", closer.strip()]
        emit_part("16-send-diverge.js", "\n".join([
            "async function _sendDiverge(playerMsg, text, img) {",
            body(A["seam1_send"], A["seam2_send"] - 1),
            "        return allCandidates;",
            closer,
        ]))
        ADDED += ["async function _sendDiverge(playerMsg, text, img) {", "return allCandidates;", closer.strip()]
        emit_part("17-send-judge.js", "\n".join([
            "async function _sendJudge(playerMsg, text, img, allCandidates) {",
            body(A["seam2_send"], A["catch_send"] - 1),
            closer,
        ]))
        ADDED += ["async function _sendJudge(playerMsg, text, img, allCandidates) {", closer.strip()]
        return
    nm = name_of(start)
    if nm.startswith("?"):
        # 纯注释/空行区：跟随下一个已声明函数的归属文件
        nxt_decl = [d for d in decls if d > end]
        if not nxt_decl:
            raise SystemExit(f"[map] 区间 L{start} 之后没有声明可归属")
        target = NAME2FILE.get(name_of(nxt_decl[0]))
    else:
        target = NAME2FILE.get(nm)
    if target is None:
        raise SystemExit(f"[map] 区间 L{start}（{nm}）未指派目标文件")
    emit_part(target, body(start, end))


def region_end_of(end: int) -> int:
    """end 是区间终点（含），函数真正的闭合行 = 向前跳过空行。"""
    e = end
    while L[e - 1].strip() == "":
        e -= 1
    return e


for (s, e, d) in regions:
    if (s, e, d) == (state_lo, state_hi, state_lo):
        continue
    slice_region(s, e)

# ---------------------------------------------------------------- 组装文件
FILES_OUT: dict[str, str] = {}


def finalize(name: str, content: str) -> None:
    FILES_OUT[name] = f"{HEADER}\n{content}\n"


# 00-helpers：pre-setup + parseJsonSafely 区间
finalize("00-helpers.js", body(A["script_open"] + 1, A["createApp"] - 1) + "\n\n" + "\n".join(FILES.get("00-helpers.js", [])))

# 01-assets：3 张 base64 分块
asset_stmts: list[str] = []
pa_of_line: dict[int, str] = {}
n_img = 0
for i in range(state_lo, state_hi + 1):
    if "base64," not in L[i - 1]:
        continue
    m = re.search(r'"dataUrl": "(data:image/[a-z]+;base64,([A-Za-z0-9+/=]+))"', L[i - 1])
    if not m:
        raise SystemExit(f"[base64] L{i} 结构不符合预期")
    n_img += 1
    key = f"img{n_img}"
    head, b64 = m.group(1).split("base64,", 1)
    pa_of_line[i] = key
    for j, c in enumerate([b64[p : p + 17000] for p in range(0, len(b64), 17000)]):
        stmt = f'BK.PA.{key} = "{head}base64,{c}";' if j == 0 else f'BK.PA.{key} += "{c}";'
        asset_stmts.append(stmt)
        ADDED.append(stmt.strip())
    REMOVED.append(L[i - 1].strip())
print(f"base64：{n_img} 张 → {len(asset_stmts)} 个分块语句")
vols: list[list[str]] = [[]]
for s in asset_stmts:
    if sum(len(x.encode()) + 1 for x in vols[-1]) + len(s.encode()) > 19000:
        vols.append([])
    vols[-1].append(s)
for vi, stmts in enumerate(vols, 1):
    head = "window.BK = window.BK || {};\nBK.PA = {};\n" if vi == 1 else ""
    finalize(f"01-assets-{vi}.js", head + "\n".join(stmts))
    if vi == 1:
        ADDED += ["window.BK = window.BK || {};", "BK.PA = {};"]
print(f"资产分卷：{len(vols)} 卷")

# 02-state：状态区 verbatim（dataUrl 改引用）
state_lines = []
for i in range(state_lo, state_hi + 1):
    ln = L[i - 1]
    if i in pa_of_line:
        new = re.sub(r'"data:image/[a-z]+;base64,[A-Za-z0-9+/=]+"', f"BK.PA.{pa_of_line[i]}", ln)
        ADDED.append(new.strip())
        ln = new
    state_lines.append(ln)
finalize("02-state.js", "\n".join(state_lines))

# 03–18：各分区
FILES["18-app.js"].insert(0, body(A["onmounted_comment"], A["decl_showToast"] - 1))  # onMounted 块（须在 setup 期间注册）
for fname, parts in FILES.items():
    if fname == "00-helpers.js":
        continue  # 上面已合并（pre-setup + parseJsonSafely 区间）
    content = "\n".join(parts)
    if fname == "18-app.js":
        # 区间原文以 `return exportedBundle;` 结尾，必须包进 buildSetupTail 供 setup 调用
        content = "BK.buildSetupTail = function () {\n" + content + "\n        };"
        ADDED += ["BK.buildSetupTail = function () {"]
    finalize(fname, content)

# ---------------------------------------------------------------- 新 index.html
ORDER = sorted(FILES_OUT, key=lambda n: (int(n.split("-")[0]), n))
tags = "\n".join(f'    <script src="js/{n}"></script>' for n in ORDER)
inline = "\n".join([
    "    <script>",
    "      // 应用装配：状态与函数在各 js 模块（全局词法绑定），这里只保留 setup 壳。",
    "      createApp({",
    "        setup() {",
    "          return BK.buildSetupTail();",
    "        }",
    "      }).mount('#app');",
    "    </script>",
])
inline_lines = [ln.strip() for ln in inline.split("\n") if ln.strip()]
tag_lines = [ln.strip() for ln in tags.split("\n") if ln.strip()]
new_index = "\n".join(L[: A["script_open"] - 1]) + "\n" + tags + "\n" + inline + "\n" + "\n".join(L[A["mount"] :])

# ---------------------------------------------------------------- 等价校验
def counter_of(text: str) -> Counter:
    return Counter(ln.strip() for ln in text.split("\n") if ln.strip())


orig_counter = counter_of(body(A["script_open"] + 1, A["mount"] - 1))
new_counter = Counter()
for name, content in FILES_OUT.items():
    new_counter += counter_of(content.split("\n", 1)[1])
new_counter += counter_of(inline)
new_counter += counter_of(tags)
for s in inline_lines:  # 与原文对冲的行（createApp/setup/闭合）不算新增
    if s not in orig_counter:
        ADDED.append(s)
ADDED.extend(tag_lines)

add_cnt = new_counter - orig_counter
rem_cnt = orig_counter - new_counter
ADDED_cnt = Counter(x for x in (s.strip() for s in ADDED) if x)
REMOVED_cnt = Counter(x for x in (s.strip() for s in REMOVED) if x)
unaccounted_add = add_cnt - ADDED_cnt
unaccounted_rem = rem_cnt - REMOVED_cnt
over_add = ADDED_cnt - add_cnt
over_rem = REMOVED_cnt - rem_cnt
ok = not unaccounted_add and not unaccounted_rem and not over_add and not over_rem

print()
print("文件体积：")
sizes = {n: len(c.encode("utf-8")) for n, c in FILES_OUT.items()}
sizes["index.html(新)"] = len(new_index.encode("utf-8"))
for n, s in sorted(sizes.items()):
    limit_ok = s <= THRESHOLD or n.startswith("index.html")
    print(f"  {'✓' if limit_ok else '✗超限'} {s:>7} B  {n}")
print(f"\n等价校验：新增未登记 {sum(unaccounted_add.values())}，删除未登记 {sum(unaccounted_rem.values())}，"
      f"登记未发生 +{sum(over_add.values())}/-{sum(over_rem.values())}")

# ---------------------------------------------------------------- 落盘参数
ap = argparse.ArgumentParser()
ap.add_argument("--write", action="store_true")
args, _ = ap.parse_known_args()

# ---------------------------------------------------------------- node --check
def node_check(name: str, code: str) -> bool:
    import tempfile
    tmp = Path(tempfile.gettempdir()) / f"bk_check_{name}"
    tmp.write_text(code, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    try:
        tmp.unlink()
    except FileNotFoundError:
        pass
    if r.returncode != 0:
        print(f"  ✗ {name}: {r.stderr.strip()[:200]}")
        for ln in code.split(chr(92)+chr(110))[-8:]:
            print("    " + ln)
        return False
    return True



if "--check" in sys.argv or args.write:
    print("node --check：")
    all_ok = all(node_check(n, c) for n, c in FILES_OUT.items())
    print("  全部通过 ✓" if all_ok else "  存在语法错误 ✗")
    ok = ok and all_ok

if args.write:
    if not ok:
        raise SystemExit("等价校验未通过，拒绝落盘")
    JS.mkdir(exist_ok=True)
    for n, c in FILES_OUT.items():
        (JS / n).write_text(c, encoding="utf-8", newline="")
    SRC.write_text(new_index, encoding="utf-8", newline="")
    print(f"已写出 {len(FILES_OUT)} 个 js 文件 + 新 index.html")
else:
    print("（--dry：未落盘；加 --write 输出）")
if unaccounted_add or unaccounted_rem or over_add or over_rem:
    dbg = FILES_OUT.get("00-helpers.js", "")
    print(f"[debug] 00-helpers 含 buildDivergence: {'buildDivergenceSystemPrompt' in dbg}；"
          f"pre-setup 范围 L{A['script_open'] + 1}–L{A['createApp'] - 1}")
    print(f"[debug] 18-app 行数: {len(FILES_OUT.get('18-app.js', '').splitlines())}")
    Path("_dump12.js").write_text(FILES_OUT.get("12-reroll-diverge.js", ""), encoding="utf-8")
    print("[debug] 12 已转储 _dump12.js")
if unaccounted_add:
    print("新增未登记：")
    for ln, c in unaccounted_add.items():
        print(f"  +×{c} {ln[:110]}")
if unaccounted_rem:
    print("删除未登记：")
    for ln, c in unaccounted_rem.items():
        print(f"  -×{c} {ln[:110]}")
if over_add:
    print("登记未发生(+)：")
    for ln, c in over_add.items():
        print(f"  +×{c} {ln[:110]}")
if over_rem:
    print("登记未发生(-)：")
    for ln, c in over_rem.items():
        print(f"  -×{c} {ln[:110]}")
