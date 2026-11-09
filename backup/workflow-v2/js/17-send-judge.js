// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
async function _sendJudge(playerMsg, text, img, allCandidates) {
            playerMsg.pipelineState.currentStage = 2;
            playerMsg.pipelineState.currentStageName = '独立裁判与终审中...';
            scrollToBottom();

            const stage2SystemPrompt = `你是一名冷酷严苛的日式大喜利独立裁判兼终审监督。
【核心大喜利原题】: ${text || '看图大喜利'}
【常识核心】: ${playerMsg.pipelineState.stage0.raw_telemetry}
【平庸三阱】: ${(playerMsg.pipelineState.stage0.forbidden_baseline || []).join('\n')}

目标不是把每句答案压成同一种短句，而是找到**题目与笑点之间最短、最意外、最自然的连接**。核心原则是：先保护笑点，再修理表达；先判断方向是否适配，再决定是否启用该方向。

## Stage 2 独立裁判工作流（候选已匿名隐藏来源和轨道）

### 第一步：硬伤证伪（逐条检查并给出单一死因）
逐条审查匿名候选，任一不过即淘汰并给出单一死因：
1. 是否真正回答原题，而不是只借用了题目中的一个词。
2. 读者是否能在一次阅读内补齐关键场景；若必须听作者解释，淘汰。
3. 是否只是现实观察、普通吐槽、谐音或现成网梗。
4. 是否有两个以上互不咬合的概念硬拼。
5. 是否依赖错误事实或不属于题目的外来背景。
6. 是否只有“奇怪”而没有具体意外、目的反咬或人物暴露。
7. 句子本身是否自然通顺。
8. 是否像微型故事或讲故事（出现多句叙事、起承转合交代前因后果、不够利落，非单格画面大喜利，淘汰）。
若全灭，照实报告全灭，严禁为了保留名额而复活答案。

### 第二步：相对排序与胜出判定
幸存者按四项分别给 1～5 分，不合并成含糊的总印象：
- 题目贴合（1-5）
- 一秒可见性（1-5）
- 意外与落差（1-5）
- 语言自然与利落度（1-5）
另标记：[讲故事太长]、[需要解释]、[像模板]、[笑点机制重复]。
裁判必须说明最强候选胜出的具体原因，不写“很有趣”“很高级”这类空泛赞美。决出最佳原句（initial_champion）。

## Stage 3 主 Agent 终审与可选润色（先保护笑点，再剪除故事赘述）

主 Agent读取裁判报告：
- **剪除故事赘述，提炼单镜头**：若候选包含成立的笑点，但混入了前情交代、起承转合或后续交代的叙事长句，终审必须剪除所有外围叙事铺垫，直接提炼为**最短连接的单镜头动作白描或当事人单句台词**。
- **保留原句 vs 润色比较**：润色最多尝试两版，严格锁死原句的核心器物与错位动作。若原句本身已是一步到位的利落单句，坚决保留原句；若改写后显著去除了拖沓叙事、使画面一秒秒懂，加冕为最终全场总冠军（final_champion）。

【JSON 输出契约】请输出合法 JSON（除 JSON 外无任何额外说明字符）：
{
  "eliminations": ["候选句子 -> 单一淘汰死因"],
  "scoring_and_ranking": "幸存候选四维打分、标记与排序过程",
  "initial_champion": "最佳原句",
  "crowning_reason": "最强候选胜出的具体原因（客观剖析笑点机制与意外落差）",
  "recast_needed": false,
  "recast_variants": {
    "variant_1": "润色尝试版1（若无需润色可填原句）",
    "variant_2": "润色尝试版2（若无需润色可填原句）"
  },
  "final_champion": "全场总冠军金句"
}`;

            const stage2UserPrompt = `【大喜利原题】: ${text || '看图大喜利'}\n所有候选短句池：\n${allCandidates.join('\n')}\n请对照原题进行硬伤证伪、四维打分与终审选拔！`;
            const stage2Reply = await callLlmWithBackoff({
              systemPrompt: stage2SystemPrompt,
              userPrompt: stage2UserPrompt,
              imageBase64: img
            });

            const parsedS2 = parseJsonSafely(stage2Reply);

            // Extract initial champion & track candidates for fallback
            let initialCleaned = cleanPunchline(parsedS2.initial_champion) || '';
            if (!initialCleaned || initialCleaned === '无合格初稿' || initialCleaned.includes('无合格') || initialCleaned.includes('全灭')) {
              initialCleaned = cleanPunchline(parsedS2.final_champion)
                || (allCandidates.length ? cleanPunchline(allCandidates[0].replace(/^候选\s*\d+[:：]\s*/, '')) : '')
                || '大喜利金句生成完毕';
            }

            let finalRecastVariants = null;
            if (parsedS2.recast_variants && (parsedS2.recast_variants.variant_1 || parsedS2.recast_variants.variant_2 || parsedS2.recast_variants.monologue)) {
              finalRecastVariants = {
                variant_1: cleanPunchline(parsedS2.recast_variants.variant_1 || parsedS2.recast_variants.monologue || ''),
                variant_2: cleanPunchline(parsedS2.recast_variants.variant_2 || parsedS2.recast_variants.cold_sketch || '')
              };
            }

            const eliminationsList = Array.isArray(parsedS2.eliminations)
              ? parsedS2.eliminations
              : (Array.isArray(parsedS2.four_gate_eliminations) ? parsedS2.four_gate_eliminations : [String(parsedS2.eliminations || parsedS2.four_gate_eliminations || '')].filter(Boolean));

            playerMsg.pipelineState.stage2 = {
              four_gate_eliminations: eliminationsList,
              duel_records: parsedS2.scoring_and_ranking || parsedS2.duel_records || parsedS2.pk_interrogation || '',
              pk_interrogation: parsedS2.scoring_and_ranking || parsedS2.duel_records || '',
              track_champions: {},
              initial_champion: initialCleaned,
              recast_variants: finalRecastVariants,
              crowning_reason: parsedS2.crowning_reason || ''
            };

            // Final champion selection: preserve best punchline
            let cleanedChampion = cleanPunchline(parsedS2.final_champion)
              || initialCleaned
              || '大喜利金句生成完毕';

            playerMsg.champion = cleanedChampion;

            // ==========================================
            // STAGE 3: Canvas 压字 (看图大喜利)
            // ==========================================
            if (img) {
              try {
                playerMsg.pipelineState.currentStageName = '压制日式综艺字幕中...';
                const memeUrl = await renderCanvasMeme(img, cleanedChampion);
                playerMsg.memeDataUrl = memeUrl;
              } catch (memeErr) {
                console.error("Canvas meme rendering error:", memeErr);
              }
            }

            playerMsg.pipelineState.currentStage = 3;
            playerMsg.pipelineState.currentStageName = '✓ 金句生成完毕';
            playChampionSound();
            showToast('已加冕全场总冠军！点击绿色气泡即可复制');

        }
