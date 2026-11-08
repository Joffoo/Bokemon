# Bokeman 项目工作流与验收规范

- **大喜利唯一真源（Single Source of Truth）**：[`.agents/skills/oogiri-flow/SKILL.md`](skills/oogiri-flow/SKILL.md) 与 [`index.html`](../index.html)（含 `handleSend` 与 `rerollPunchline`）中的 Stage 0、Stage 1（Subagent A / B / C）及 Stage 2 提示词必须保持 100% 中文原文一致，严禁擅自删减承重机制或造成双端不一致。
- **修改工作流必跑子 Agent A/B 盲测验收**：每次修改 [`index.html`](../index.html) 或 [`.agents/skills/oogiri-flow/SKILL.md`](skills/oogiri-flow/SKILL.md) 中的任何提示词或工作流逻辑时，必须先读取并严格执行 [`.agents/skills/workflow-ab-eval/SKILL.md`](skills/workflow-ab-eval/SKILL.md)，调用 `invoke_subagent`（三轨分别作为 3 个独立子 Agent 并行派发，全中文原样提示词）完成修改前后（Baseline vs. Candidate）的实测对比，验收通过后方可交付给用户。
