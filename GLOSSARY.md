# Bokeman（大喜利金句工作台）

单页应用（BYOK、无后端）：用户出题（文字/图片），按 oogiri-flow 三轨发散产出大喜利金句并压字成图。

## Language

### 工作流阶段

**Stage 0（地基切片）**:
从命题提取纯物理事实（原生器物、力学微姿态）、平庸三阱与预筛世俗域，供三轨共用。
_Avoid_: 分析题面、题面解析

**发散段（Stage 1）**:
单实例一次完成三轨候选的生成段，输出统一 JSON（A/C 各 3 句、B 按世俗域清单逐类）。
_Avoid_: 三轨并行（旧架构，已废止，见 docs/adr/0001）

**公诉人段（Stage 2）**:
对候选池执行四道检视关、两两死斗与三向句法重铸，产出全场总冠军。

**编排壳 / 分段函数**:
`handleSend`/`rerollPunchline` 拆分后的形态：编排壳只保留 try 包络与分段调用，分段函数（`_sendStage0`/`_sendDiverge`/`_sendJudge` 等）各自独占一个语句缝之间的原文。

### 提示词治理

**提示词真源（SSOT）**:
Stage 0/1/2 提示词的权威文本，位于 `js/15|16|17`（发送侧）与 `js/12|13`（reroll 侧），必须与 `.agents/skills/oogiri-flow/SKILL.md` 逐字一致。
_Avoid_: 在 index.html 里找提示词（拆分后已不在）

**提示词指纹**:
五个提示词模板的 SHA-256 前 12 位（`bench/ab-divergence/prompts.py`），用于跨拆分/跨提交验证提示词零漂移，当前 d2a0c8cdc780。

**双端一致**:
SKILL.md 与 js/ 模块的同名提示词逐字相同的铁律；由 `prompts.py` 的 `check_duplicates()` 机器核对。

### 体积治理

**20KB 棘轮**:
pre-commit 拦截超 20KB 源码文件的规矩；已登记的老大文件只要不超过基线字节即可提交，基线只降不升（`.githooks/size-baseline.txt`）。

**装配壳**:
index.html 中仅存的脚本：`setup()` 调用 `BK.buildSetupTail()` 返回模板绑定；页面模板本身留在 index.html。
