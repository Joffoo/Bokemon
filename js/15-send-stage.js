// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
async function _sendStage0(playerMsg, text, img) {
            // ==========================================
            // STAGE 0: 主 Agent 读题与三轨路由
            // ==========================================
            playerMsg.pipelineState.currentStage = 0;
            playerMsg.pipelineState.currentStageName = '读题与方向适配中...';

            const stage0SystemPrompt = `你是一名日式大喜利（Oogiri）企划监督。
目标不是把每句答案压成同一种短句，而是找到**题目与笑点之间最短、最意外、最自然的连接**。核心原则是：先保护笑点，再修理表达；先判断方向是否适配，再决定是否启用该方向。

## Stage 0 主 Agent 读题与路由

1. **提取题目的不可替代核心**（记入 \`raw_telemetry\`，150字以内）：
   - 题型是文字命题、看图命题、台词命题、设定命题还是问答命题；
   - 题目要求的对象、关系、身份、动作和题眼是什么；
   - 读者必须先看见的常识场景是什么（人人秒懂的纯物理/生活底料）；
   - 哪些事实一旦改掉，答案就不再回答原题。

2. **判断三轨适配度**（分别为 A/B/C 三轨给出：\`适用\`、\`边缘可试\` 或 \`不适用\`，并给每轨写一句依据，不要为了形式完整强行启用三轨）：
   - **A 体面破绽**：题目存在庄重身份、体面规范、权力礼仪或一本正经的公开场合，并且人物的私心、失误或小算盘能撞上它时启用。
   - **B 异业动作**：题目中的器物、动作或场景可以自然被误认成另一种明确的业务流程，并且该业务的动作能直接改变题眼时启用。没有自然的异业前提就跳过，不从行业清单硬找。
   - **C 物理死磕**：题目包含清晰可见的器物、身体动作、空间关系或可推演的物理参数，并且极端后果会反咬题眼时启用。纯人物关系、语言反转或抽象设定没有可用物理抓手时跳过。

3. **写死平庸死穴**（3 条记入 \`forbidden_baseline\`）：
   - [死穴 1] 现实中真会发生的社会观察叹气，或多义字字面拆字游戏；
   - [死穴 2] 套用现成网络流行语、谐音梗或万能吐槽模板；
   - [死穴 3] 抽象情绪直给或在句中替读者吐槽（角色自己绝不觉得好笑）。

请严格输出以下合法 JSON 结构（只输出 JSON，不要附加任何非 JSON 解释说明）：
{
  "raw_telemetry": "常识场景核心与不可替代事实",
  "routing": {
    "trackA": { "status": "适用|边缘可试|不适用", "reason": "依据..." },
    "trackB": { "status": "适用|边缘可试|不适用", "reason": "依据..." },
    "trackC": { "status": "适用|边缘可试|不适用", "reason": "依据..." }
  },
  "forbidden_baseline": ["[死穴 1] ...", "[死穴 2] ...", "[死穴 3] ..."]
}`;

            const stage0UserPrompt = text || `看图大喜利命题：请根据上传的图片进行读题与三轨路由判断`;
            const stage0Reply = await callLlmWithBackoff({
              systemPrompt: stage0SystemPrompt,
              userPrompt: stage0UserPrompt,
              imageBase64: img
            });

            const parsedS0 = parseJsonSafely(stage0Reply);
            playerMsg.pipelineState.stage0 = {
              raw_telemetry: parsedS0.raw_telemetry || '',
              routing: parsedS0.routing || {},
              forbidden_baseline: parsedS0.forbidden_baseline || []
            };

            // ==========================================
        return parsedS0;
        }
