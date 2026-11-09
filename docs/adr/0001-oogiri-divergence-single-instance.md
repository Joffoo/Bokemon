# 大喜利发散架构：三轨并行改为单实例一次发散

`oogiri-flow` 的 Stage 1 原强制「三轨必须由三个独立上下文各自发散」，但 2026-11 的双路径实测（生产 API 路径 36 组盲评 + 子 Agent 路径 18 组，全量数据见 `bench/ab-divergence/report.md`）证明隔离收益不成立：池内多样性差异 +0.003≈零、盲评分不占优，而调用数翻倍、冠军格式合规率更差（72% vs 89%）。因此 Stage 1 改为单实例一次完成：三段轨道提示词（体面破绽 / 异业动作 / 物理死磕）逐字拼装为一次调用（`js/00-helpers.js` 的 `buildDivergenceSystemPrompt`），SKILL.md 与之同步。完整设计与验收标准见 `bench/ab-divergence/DESIGN.md`。

## Considered Options

- **保留三轨并行**：被实验证伪——隔离的理论收益（多极向）未兑现，成本与格式纪律均处劣势。
- **第三臂（同会话连跑三轮）**：可拆分「隔离」与「多次采样」两个变量，但成本 +50%，搁置。
- **API 路径 vs 子 Agent 路径**：实验以生产 API 路径为准（变量最干净）；子 Agent 路径因并发限流与仓库误写风险只作方向性旁证。

## Consequences

- 每题 Stage 1 从 4 次 API 调用降为 2 次（Stage 0 + 一次发散）。
- 单次调用失败不再有单轨降级，整体报错（实验中 46/46 解析成功支撑此取舍）。
- `.agents/skills/oogiri-flow/SKILL.md` 中「必须三个独立实例否则等于没做」的主张已废止，不得据旧文恢复。
- 严格的正式 A/B 盲测被用户终止（子 Agent 并发限流），改架构的判定依据是上述 54 组实测；如需正式补测，工具链在 `bench/ab-divergence/`。

Status: accepted（2026-11-09）
