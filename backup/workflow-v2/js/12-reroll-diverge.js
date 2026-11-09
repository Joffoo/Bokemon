// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
async function _rerollDiverge(playerMsg, promptText, imgUrl, s0) {
            const sysA = `【命题输入】
${promptText || '（见上传图片）'}

【常识核心】
${s0.raw_telemetry}

【方向说明】A 轨：体面破绽
从“公开身份/体面规范”与“角色真正想做的事”之间找冲突。错位应暴露人物的具体目的、习惯或私下规矩，而不只是把庄重场景换成一个琐碎物件。优先产生一格能画出的动作或一句当事人会认真说出的话。问自己：角色为什么觉得这件事完全合理？如果答案只有“因为反差”，继续寻找更具体的行为依据。

【生成要求】
1. 单格一击，严禁叙事交代与讲故事：大喜利是现场单格画面动作白描或角色脱口而出的单句台词，必须一口气读完（约10~25字自然句）。绝对禁止多句拼接、绝对禁止交代“先如何、又如何、结果如何”的起承转合微型小说。读者有充分的常识脑补能力，直接从最荒唐的核心动作或台词切入！
2. 生成 3～5 条单句候选，优先保证笑点成立、题目贴合、画面清晰。
3. 每条候选附一个不超过 6 字的内部机制标签（如“身份误认”“礼仪露馅”“私下规矩”等）。

【负面边界】以下平庸三阱已被封禁，触碰即作废：
${(s0.forbidden_baseline || []).join('\n')}

【交付】直接输出合法 JSON 数组：[{"tag": "机制标签", "candidate": "候选句子"}]，只输出 JSON。`;

            const sysB = `【命题输入】
${promptText || '（见上传图片）'}

【常识核心】
${s0.raw_telemetry}

【方向说明】B 轨：异业动作
先找题目中本来就存在的动作或器物，再判断它能否被另一行业的从业者按其业务逻辑操作。笑点来自根本性质被认错，不是简单把职业名词贴到原场景上。行业只是隐藏前提，候选必须脱离行业说明仍能看见清晰动作。若必须塞入外来道具、覆盖多个行业或依赖职业知识才能理解，放弃该候选。若题目无自然异业前提，可输出空数组。

【生成要求】
1. 单格一击，严禁叙事交代与讲故事：大喜利是现场单格画面动作白描或角色脱口而出的单句台词，必须一口气读完（约10~25字自然句）。绝对禁止交代前因后果的叙事小作文，直接展现那个前提搞错的荒唐肌肉记忆动作！若无自然异业前提则只保留自然成立者。
2. 生成 3～5 条单句候选，优先保证笑点成立、题目贴合、动作清晰。
3. 每条候选附一个不超过 6 字的内部机制标签（如“前提认错”“工种混淆”“行业惯性”等）。

【负面边界】以下平庸三阱已被封禁，触碰即作废：
${(s0.forbidden_baseline || []).join('\n')}

【交付】直接输出合法 JSON 数组：[{"tag": "机制标签", "candidate": "候选句子"}]，只输出 JSON。`;

            const sysC = `【命题输入】
${promptText || '（见上传图片）'}

【常识核心】
${s0.raw_telemetry}

【方向说明】C 轨：物理死磕
锁定一个读者立刻认出的物理关系，例如摩擦、承重、温度、声响、弹性、遮挡、速度或空间位置，向极端推演一至两步，再让结果回扣题目的人物或目的。物理合理不等于好笑；最终后果必须造成意外、暴露身份或破坏原目的。只写奇怪状态、不含清晰动作或后果的候选不算完成。严禁写成毫无错位的纯客观生理/科普说明文。

【生成要求】
1. 单格一击，严禁叙事交代与讲故事：大喜利是现场单格画面动作白描或角色脱口而出的单句台词，必须一口气读完（约10~25字自然句）。绝对禁止交代前因后果的叙事小作文，直接描写物理极端后果反咬题眼的那一瞬间！
2. 生成 3～5 条单句候选，优先保证笑点成立、物理推演意外、后果反咬题眼。
3. 每条候选附一个不超过 6 字的内部机制标签（如“承重反咬”“物理露馅”“声响穿帮”等）。

【负面边界】以下平庸三阱已被封禁，触碰即作废：
${(s0.forbidden_baseline || []).join('\n')}

【交付】直接输出合法 JSON 数组：[{"tag": "机制标签", "candidate": "候选句子"}]，只输出 JSON。`;

            // 多轨生成调用（换个角度重抽）
            const divergeRes = await callLlmWithBackoff({
              systemPrompt: buildDivergenceSystemPrompt(sysA, sysB, sysC),
              userPrompt: `命题：${promptText || '根据图片'}`,
              imageBase64: imgUrl
            });
            const diverged = parseJsonSafely(divergeRes) || {};
            const candsA = normalizeStringCandidates(diverged.A);
            const candsB = normalizeTrackBCandidates(diverged.B);
            const candsC = normalizeStringCandidates(diverged.C);

            playerMsg.pipelineState.trackA.candidates = candsA;
            playerMsg.pipelineState.trackA.status = candsA.length ? 'done' : 'failed';
            playerMsg.pipelineState.trackB.candidates = candsB;
            playerMsg.pipelineState.trackB.status = candsB.length ? 'done' : 'failed';
            playerMsg.pipelineState.trackC.candidates = candsC;
            playerMsg.pipelineState.trackC.status = candsC.length ? 'done' : 'failed';

            const rawPool = [
              ...candsA.map(c => cleanPunchline(c)),
              ...candsB.map(b => cleanPunchline(b.punchline || b.line || b)),
              ...candsC.map(c => cleanPunchline(c))
            ].filter(line => line && !line.includes('无') && line.length > 3);

            const uniquePool = Array.from(new Set(rawPool));
            const allCandidates = uniquePool.map((line, idx) => `候选 ${idx + 1}: ${line}`);

        return allCandidates;
        }
