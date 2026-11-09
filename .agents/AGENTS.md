# Bokeman 项目工作流与验收规范

- **术语与决策记录**：项目术语见根目录 [GLOSSARY.md](../GLOSSARY.md)；架构决策（发散架构、文件拆分）见 [docs/adr/](../docs/adr/)；发散架构实验全量数据与报告见 `bench/ab-divergence/report.md`。

- **大喜利唯一真源（Single Source of Truth）**：[`.agents/skills/oogiri-flow/SKILL.md`](skills/oogiri-flow/SKILL.md) 与前端 `js/` 模块（Stage 0 在 `js/15-send-stage.js`，轨道 A/B/C 在 `js/16-send-diverge.js` 与 `js/12-reroll-diverge.js`，Stage 2 在 `js/17-send-judge.js` 与 `js/13-reroll-judge.js`；拼装函数 `buildDivergenceSystemPrompt` 在 `js/00-helpers.js`）中的 Stage 0、Stage 1（Subagent A / B / C）及 Stage 2 提示词必须保持 100% 中文原文一致，严禁擅自删减承重机制或造成双端不一致。`index.html` 只保留页面模板与装配壳（`setup()` → `BK.buildSetupTail()`）。
- **修改工作流必跑子 Agent A/B 盲测验收**：每次修改 `js/` 中的任何提示词或工作流逻辑时，必须先读取并严格执行 [`.agents/skills/workflow-ab-eval/SKILL.md`](skills/workflow-ab-eval/SKILL.md)，调用 `invoke_subagent`（三轨分别作为 3 个独立子 Agent 并行派发，全中文原样提示词）完成修改前后（Baseline vs. Candidate）的实测对比，验收通过后方可交付给用户。
- **生成型子 Agent 纪律**：经 workflow/subagent 派发的纯文本生成任务（三轨发散、盲评裁判、Stage 2 裁决、Stage 0 切片等），提示词必须显式声明「纯文本生成任务，禁止读写仓库文件」——2026-11-09 曾有实验子 Agent 在运行中途向仓库写入 `.githooks/`。需要读写仓库的子任务改用主会话或 `/handoff` 流程。
- **单文件体积规矩**：源码文件超过 20KB 会被 pre-commit 钩子拦截；`index.html` 在 `.githooks/size-baseline.txt` 有棘轮基线（2026-11-09 拆分后已从 325350 降到 63818），**只许变小不许变大**，新功能一律进 `js/` 模块。
- **提示词漂移机器拦截**：pre-commit 会运行 `bench/ab-divergence/prompts.py --check`（副本一致 + 指纹对账，登记值在 `bench/ab-divergence/PROMPTS_FINGERPRINT`）。有意修改提示词后须执行 `--update-fingerprint` 一并提交；校验失败一律当事故排查，不许直接改登记值放过。
