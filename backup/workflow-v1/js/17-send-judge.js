// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
async function _sendJudge(playerMsg, text, img, allCandidates) {
            playerMsg.pipelineState.currentStage = 2;
            playerMsg.pipelineState.currentStageName = '推敲精选最佳金句...';
            scrollToBottom();

            const stage2SystemPrompt = `你是一名冷酷严苛的日式大喜利公诉人（裁判长）。
【核心大喜利原题】: ${text || '看图大喜利'}
【常识地基】: ${playerMsg.pipelineState.stage0.raw_telemetry}
【平庸三阱】: ${(playerMsg.pipelineState.stage0.forbidden_baseline || []).join('\n')}

## Stage 2 公诉人证伪裁决与句法骨架重铸

### 第一步：四道客观检视关（任一关不过即出局）

对全部候选逐条过四关：
1. **单点错位与抹除还原关（首要铁律）**：
   - 检查是否符合**“地基 7：错位 3”**：**如果把句末的错位词抹掉、换成普通词，前半句必须能还原成一句 100% 正常、通顺的日常话！**
   - **【严禁科普与医学说明文】**：凡是毫无错位、仅仅客观描述自然界/生理现象的科普说明文（如“微晃一个呼吸周期”、“心跳搏动”、“光线直线传播”等），属于“0% 错位”，第一顺位当场判死！
   - 凡是前半句就已经奇形怪状、把 3 个及以上概念硬捏在一起（“A词+B词+C词”连连看）、往原场景硬塞外来假道具、或删掉动词变成需要猜谜的电报哑谜，第一顺位直接枪毙！
2. **反现实观察与双核替换关**：
   - **淘汰“弱错位（现实观察）”**：现实中真有可能会发生的事（让人读完叹气觉得“确实很惨/很穷/很累”而非荒谬发笑的），一律判死；
   - **破坏性替换测试**：触碰 \`forbidden_baseline\` 即死；将原题的【题眼属性】替换成其他无关形容词后句子依然成立的，说明与题眼零耦合，当场判死。
3. **分镜与实词密度关**：画不出包含原题单一道具与清晰人体姿态的单格漫画即死；含 2 个及以上虚词（的/了/着/过/呢/吧）或句中含空格断句的即死。
4. **末词遮蔽关（Ochi 语序验证）**：在前半句为 100% 正常通顺地基的前提下，遮住句末最后 2~4 个字，若前半句已把包袱泄光，当场腰斩或倒装；严禁在底词之后还留有解释性词尾。

**三轨均不设保底**。全灭也照实报，严禁为了让排名好看而复活任何一条。

### 第二步：公诉人式两两死斗（只准证伪，不准吹捧）

通过四关的幸存者进入两两对照：
- **裁决铁律**：比较候选 X 与 Y 时，**严禁写空洞赞美词**。裁判必须扮演公诉人，按 **「落差高度 × 回收利落度」** 质询：哪一条的犯蠢层级更浅（只是工具错而非前提错）？哪一条的画面需要多绕半秒弯子？将较弱者淘汰，最直观、落差最狠的那一条晋级。
- 先在轨内两两PK，挑出 A、B、C 各 1 条**轨道冠军**；三条轨道冠军再两两PK，决出 1 条**总冠军初稿**。

### 第三步：总冠军「句法骨架三向重铸」（修理赘述，拒绝改出哑谜）

拿到**总冠军初稿**后，**严格锁死该初稿的具体原题器物与核心错位事件（严禁偷换道具，且严禁删掉核心动词变成名词堆砌哑谜！）**，按以下 **3 种正交的代数句法槽位公式**尝试重铸（均须 ≤14 字、零标点、零句中空格、底词右置）：

1. **\`[现场喝止/当事人独白体]\`**
   - **句法公式**：\`[70% 正常操作原题器物的前置指令] + [30% 暴露前提误解的突发末词]\`
   - **声学特征**：以无比认真的当事人或画外人的口吻直接发话（若原题本身要求“说一句话/台词”，优先取此体）。
2. **\`[量化规矩/折算体]\`**
   - **句法公式**：\`[70% 原题正常器物与动作] + 超/每 [具体刻度] + [30% 荒谬计价或离谱后果]\`
   - **声学特征**：将荒诞的前提错位写成场所内一本正经的明文规矩。
3. **\`[冷面白描/单动作体]\`**
   - **句法公式**：\`[70% 场内角色 + 操作原题单一器物] + [30% 错位核心动词与底词]\`
   - **声学特征**：极简白描，不加任何修饰词，靠单一动作的反差一击致命。

【**重铸铁律**（ひねりは修理に使う）】：直接说最清楚的梗，就直接说！将【总冠军初稿】与【3 个句法重铸体】同台对决——若某个重铸体为了压字数而损失了“一读秒懂”的通顺度，立即废弃该重铸体；选出最自然、最秒懂、0.5 秒“哈？”之后瞬间爆笑的那 1 句，加冕为最终**全场总冠军**。

【JSON 输出铁律】
严禁在 \`track_champions\`、\`initial_champion\`、\`recast_variants\`、\`final_champion\` 中携带任何轨道标签（如 [A轨]）、行业分类名或序号！请输出合法 JSON（只输出 JSON）：
{
  "four_gate_eliminations": ["淘汰理由清单"],
  "duel_records": "公诉人质询过程与决选理由",
  "track_champions": {
    "trackA": "A轨冠军短句",
    "trackB": "B轨冠军短句",
    "trackC": "C轨冠军短句"
  },
  "initial_champion": "总冠军初稿短句",
  "recast_variants": {
    "monologue": "现场喝止/当事人独白体",
    "quantified": "量化规矩/折算体",
    "cold_sketch": "冷面白描/单动作体"
  },
  "final_champion": "全场总冠军金句（≤14字零标点零空格）",
  "crowning_reason": "加冕判词"
}`;

            const stage2UserPrompt = `【大喜利原题】: ${text || '看图大喜利'}\n所有候选短句池：\n${allCandidates.join('\n')}\n请对照原题严苛审判、公诉人两两死斗与三向句法重铸！`;
            const stage2Reply = await callLlmWithBackoff({
              systemPrompt: stage2SystemPrompt,
              userPrompt: stage2UserPrompt,
              imageBase64: img
            });

            const parsedS2 = parseJsonSafely(stage2Reply);

            // Extract initial champion & track candidates for fallback
            let initialCleaned = cleanPunchline(parsedS2.initial_champion) || '';
            if (!initialCleaned || initialCleaned === '无合格初稿' || initialCleaned.includes('无合格') || initialCleaned.includes('全灭')) {
              initialCleaned = cleanPunchline(parsedS2.track_champions?.trackA) 
                || cleanPunchline(parsedS2.track_champions?.trackB) 
                || cleanPunchline(parsedS2.track_champions?.trackC) 
                || (allCandidates.length ? cleanPunchline(allCandidates[0]) : '') 
                || '大喜利金句生成完毕';
            }

            let finalRecastVariants = null;
            if (parsedS2.recast_variants && (parsedS2.recast_variants.monologue || parsedS2.recast_variants.quantified || parsedS2.recast_variants.cold_sketch)) {
              finalRecastVariants = {
                monologue: cleanPunchline(parsedS2.recast_variants.monologue) || parsedS2.recast_variants.monologue || '',
                quantified: cleanPunchline(parsedS2.recast_variants.quantified) || parsedS2.recast_variants.quantified || '',
                cold_sketch: cleanPunchline(parsedS2.recast_variants.cold_sketch) || parsedS2.recast_variants.cold_sketch || ''
              };
            }

            playerMsg.pipelineState.stage2 = {
              four_gate_eliminations: Array.isArray(parsedS2.four_gate_eliminations) 
                ? parsedS2.four_gate_eliminations 
                : (parsedS2.four_gate_eliminations ? [String(parsedS2.four_gate_eliminations)] : []),
              duel_records: parsedS2.duel_records || parsedS2.pk_interrogation || '',
              pk_interrogation: parsedS2.pk_interrogation || parsedS2.duel_records || '',
              track_champions: parsedS2.track_champions || {},
              initial_champion: initialCleaned,
              recast_variants: finalRecastVariants,
              crowning_reason: parsedS2.crowning_reason || ''
            };

            // Clean champion: strictly strip accidental labels/quotes/punctuation, ensuring 100% preservation of punchline words
            let cleanedChampion = cleanPunchline(parsedS2.final_champion)
              || cleanPunchline(finalRecastVariants?.cold_sketch)
              || cleanPunchline(finalRecastVariants?.monologue)
              || cleanPunchline(finalRecastVariants?.quantified)
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
