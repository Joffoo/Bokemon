# index.html 拆分为 js 模块，源码文件执行 20KB 棘轮

`index.html` 曾是 325KB 单文件（约 3,920 行），每次 AI 协作都要吞掉全部上下文，且触发团队新立的「源码文件超 20KB 拒绝提交」pre-commit 规矩。2026-11-09 用字节级搬移拆为 27 个 `js/` 模块（经典脚本、无构建、file:// 双击可用）：状态区放脚本顶层成为全局词法绑定，函数零包装逐字搬移；`handleSend`/`rerollPunchline` 按 try 包络语句缝切成编排壳 + 分段函数；3 张 base64 预设图分块进 `js/01-assets-*.js`（运行时字符串不变，规避 file:// 下 canvas 污染）。拆分器与行多重集等价校验在 `bench/ab-divergence/split_index.py`（差异 0/0/0 才允许落盘）。提示词真源随迁至 `js/` 模块，`bench/ab-divergence/prompts.py` 的指纹校验（d2a0c8cdc780）证明跨拆分逐字节一致。

## Consequences

- `index.html` 只剩页面模板 + 装配壳（`setup()` → `BK.buildSetupTail()`），棘轮基线从 325350 降到 63818（`.githooks/size-baseline.txt`）——**只许变小不许变大**；要删掉基线行需把模板也组件化（未做）。
- 新功能一律进 `js/` 模块；提示词 SSOT 位置见 `.agents/AGENTS.md`。
- 状态靠全局词法绑定共享，经典脚本加载顺序即依赖顺序（`js/` 文件名前缀即序）。

Status: accepted（2026-11-09）
