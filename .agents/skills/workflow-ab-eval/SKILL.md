---
name: workflow-ab-eval
description: 修改大喜利提示词、多Agent工作流或裁判规则时的前置A/B子Agent盲测验收技能。每次修改 js/ 模块或 oogiri-flow/SKILL.md 的提示词与工作流时自动触发，通过独立子Agent（invoke_subagent）对比修改前（Baseline A）与修改后（Candidate B）的真实生成结果，严禁未经实测直接交付给用户消耗外部API额度。
---

# Workflow A/B Eval（工作流修改前后子 Agent 盲测验收）

修改提示词或工作流时，必须先用内置子 Agent（`invoke_subagent`）跑完修改前后的对照实测（零外部 API 成本），绝不靠猜，也绝不让用户拿昂贵的外部模型当小白鼠。

## Step 1: 唯一真源同步与机制差异核对（Mechanism Diff）

1. **双端完全一致铁律**：项目中 `.agents/skills/oogiri-flow/SKILL.md` 与前端 `js/` 模块（Stage 0 在 `js/15-send-stage.js`，轨道 A/B/C 在 `js/16-send-diverge.js` 与 `js/12-reroll-diverge.js`，Stage 2 在 `js/17-send-judge.js` 与 `js/13-reroll-judge.js`；`rerollPunchline` 在 `js/11-reroll.js`、`handleSend` 在 `js/14-send.js`）中的 Stage 0、Stage 1（Subagent A / B / C）及 Stage 2 提示词**必须保持 100% 中文原文一致**。严禁改一处漏一处，严禁夹杂英文指令或擅自删减。
2. **提取基线与候选**：读取修改前的 **Baseline (A)**（如 `git show HEAD:js/16-send-diverge.js`）与拟修改的 **Candidate (B)**，列出每一处增删改对应的认知机制。
3. **承重墙保护检查**：原工作流是反复打磨出的精密闭环，检查是否误删了承重机制（如 Stage 0 图文分流提取与禁开外来假道具词表、Stage 1 锁定单一原生器物 + 三岁小孩能懂的具体动词 + 往极端推两步拉回半步 + 底词落地闭嘴、Stage 2 四道检视关 + 三向代数句法重铸公式）。

**完成判据**：`oogiri-flow/SKILL.md` 与 `js/` 模块提示词完全一致，且所有机制改动均已完成承重检查。

## Step 2: 锁定测试基准题（Benchmark Selection）

固定 2 道代表性测试题用于 A/B 同台盲测：
1. **触发题（Trigger Case）**：暴露当前问题的原题或原图（例如上传的看图大喜利图片，或特定台词/歌词类命题）。
2. **回归题（Regression Case）**：另一类典型大喜利命题（若触发题是图片，则回归题选文字题；若触发题是台词题，则回归题选事件/原因题），确保修改不会顾此失彼。

**完成判据**：2 道测试基准题（文字或图片绝对路径）已锁定。

## Step 3: 独立子 Agent 严格隔离派发（`invoke_subagent`）

使用当前环境的 `invoke_subagent`（`TypeName: "self"`, `Model: "inherit"`）在真实上下文隔离边界下执行测试，且下发给子 Agent 的提示词必须与项目内完全一致（全中文原样下发，不掺杂英文包装）：

1. **每臂按其自身架构派发（铁律）**：测试时两臂各自按**被测架构本身**的派发方式执行，严禁为了"派发方式对齐"而改测别的架构：
   - **Baseline A（三轨并行架构）**：并行发起 **3 次独立的 `invoke_subagent` 调用**（`Role` 分别设为 `"Subagent A 体面破绽"`、`"Subagent B 异业动作"`、`"Subagent C 物理死磕"`），每个子 Agent 只接收自己那一轨的中文提示词与 Stage 0 产出的 `{{raw_telemetry}}`、`{{forbidden_baseline}}`（及 B 轨的 `{{secular_domains}}）`。
   - **Candidate B（单实例一次发散架构，2026-11 起的 Stage 1 现行架构）**：发起 **1 次子 Agent 调用**，接收按 `oogiri-flow` Stage 1 拼装规范拼好的完整提示词（拼装头 + 三段轨道原文 + JSON 输出契约），产出 `{"A": [...], "B": [...], "C": [...]}`。
   - 给子 Agent 的轨道提示词正文必须与项目内逐字一致（全中文原样下发，不掺杂英文包装）；两臂共用同一份 Stage 0 产出，保证差异只来自派发架构。
2. **Stage 2 独立公诉人裁决**：汇总两臂各自的候选池后，分别派发给独立的 Stage 2 子 Agent（`Role: "Stage 2 公诉人裁判"`），严格按四道检视关、两两死斗与三向句法公式完成重铸与加冕。两臂用同一份 Stage 2 提示词。
3. **图像原图直读**：若测试题包含图片，在中文提示词中附上图片绝对路径，由各轨子 Agent 先调用 `read_file` 查看原图再作答。

**完成判据**：Baseline A 与 Candidate B 均按各自架构跑完「发散 → Stage 2 裁决」完整闭环，且两臂题面、Stage 0、裁判完全一致。

## Step 4: 四关盲审与棘轮留存（Blind Gate Audit & Ratchet）

向用户汇报前，按硬性门槛逐条对比 Baseline A 与 Candidate B 的产出：

1. **单点错位与抹除还原关（70/30 检验）**：抹掉句末最后 2~4 字的错位底词后，前半句是否能 100% 还原为锁定原题 **1 个原生器物** 的正常通顺日常白话？
2. **具体动词与零杂质关**：是否包含清晰的具体动词（零公文拼装词、零电报哑谜、零序号/行业分类前缀泄露、底词后零解释词尾、≤14 字、零标点零空格）？
3. **棘轮裁决（Ratchet）**：只有当 Candidate B 在触发题上显著优于 Baseline A、且在回归题上零退化时，才允许写入代码交付用户；若发现退化，立即退回修正并重跑 Step 3。

**完成判据**：Candidate B 全面通过四关检验且实测优于 Baseline A，向用户附上修改前后子 Agent 实测对比表。
