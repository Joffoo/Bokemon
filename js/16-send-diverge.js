// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
async function _sendDiverge(playerMsg, text, img) {
            // STAGE 1: 三轨一次发散（单实例单次调用，拼装提示词见 buildDivergenceSystemPrompt）
            // ==========================================
            playerMsg.pipelineState.currentStage = 1;
            playerMsg.pipelineState.currentStageName = '多角度脑洞构思中...';
            playerMsg.pipelineState.trackA.status = 'running';
            playerMsg.pipelineState.trackB.status = 'running';
            playerMsg.pipelineState.trackC.status = 'running';
            scrollToBottom();

            // Task A: 体面破绽
            const sysA = `【命题输入】
${text || '（见上传图片）'}

【常识地基切片】
${playerMsg.pipelineState.stage0.raw_telemetry}

【先导词】体面破绽
【认知机制】
1. 地基 7 错位 3（1回答1ひねり）：每句只准选用【常识地基切片】中的 **1 个** 原生器物或固有仪式作为 70% 的稳固地基，只在该器物的操作目的或私下规矩上做 **1 处** 错位。严禁同时错位两处以上（错位两处地基即崩塌为怪异病句）。
2. 落差方向与极端反推：地基越庄重/正经，错位越要琐碎世俗；**现实中真会发生的事只是“观察”不是大喜利**，必须往绝对不会发生、但顺着题眼逻辑一秒能接通的极端方向推两步，再往回撤半步。
3. 当事人绝对认真：句中角色绝不是在故意搞笑，他自己无比严肃、真心实意觉得这个荒唐操作是绝妙规矩。

【语言与声学规范】
1. 直接说清铁律（严禁电报哑谜）：每句必须包含 **1 个清晰的具体动词**，一读即懂。省略只用于砍掉解释性废话，绝不为了炫技把句子缩成需要猜谜的名词堆砌。
2. 长度与连贯：不超过 14 字，严禁使用标点符号，严禁在句中使用空格断句。
3. 底词右置（Ochi）：把那唯一的 30% 错位词死死钉在全句最后 2~4 个字，包袱落地立刻闭嘴，严禁在底词后追加半个字的解释。
4. 虚词断头台：严禁出现“的、地、得、了、着、过、其实、原来”等虚词，零情绪形容词。

【负向排除集】以下平庸三阱已被封禁，触碰即作废：
${(playerMsg.pipelineState.stage0.forbidden_baseline || []).join('\n')}

【交付】输出 3 句一读即懂、地基稳固、末词一击致命的短句。为方便程序解析，请直接输出合法 JSON 字符串数组：["短句1", "短句2", "短句3"]，只输出 JSON。`;

            // Task B: 异业动作
            const sysB = `【命题输入】
${text || '（见上传图片）'}

【常识地基切片】
${playerMsg.pipelineState.stage0.raw_telemetry}

【预筛世俗域清单】
${(playerMsg.pipelineState.stage0.secular_domains || []).join('\n')}

【先导词】异业动作
【认知机制】
1. 前提级误解（バカの深さ）：错位分三层——浅层是工具用错，中层是没看懂气氛，**最深层（最爆笑）是“连根本前提都搞错了”（角色带着十二分的敬业与认真，把当前场合的根本性质当成了另一个世俗行业）**。
2. 地基 7 错位 3：对照【预筛世俗域清单】逐类发散。每句只锁定原题中的 **1 个** 原生器物作为 70% 常识地基，让角色用该世俗域老手“最标志性的 1 个肌肉记忆动作”去操作它，做 **1 处** 前提级错位并自然引爆题眼。严禁往原场景硬塞外行假道具，严禁叠加三个概念。

【语言与声学规范】
1. 直接说清铁律：必须有 **1 个三岁小孩都能认出的清晰动词**，严禁写成多词硬拼的病句或哑谜，确保 0.5 秒看清单格画面。
2. 长度与连贯：每句不超过 14 字，严禁使用标点符号，严禁在句中使用空格断句。
3. 底词右置（Ochi）：将暴露异业前提误解的关键动作或口吻钉在句末最后 2~4 个字。
4. 数量：严格按给定清单的序号与类别名逐类输出，每类 1 句。某类无法用单一动作自然咬合时，直接输出该类别名加「无」，严禁硬拼凑数。

【负向排除集】以下平庸三阱已被封禁，触碰即作废：
${(playerMsg.pipelineState.stage0.forbidden_baseline || []).join('\n')}

【交付】按 \`[序号 类别名] 台词\` 逻辑逐类生成（台词内部无空格无标点，严禁把序号或类别名写进台词里），为方便程序解析，请直接输出合法 JSON 数组：[{"category": "[序号] 类别名", "punchline": "无标点台词或无"}]，只输出 JSON。`;

            // Task C: 物理死磕
            const sysC = `【命题输入】
${text || '（见上传图片）'}

【常识地基切片】
${playerMsg.pipelineState.stage0.raw_telemetry}

【先导词】物理死磕
【认知机制】
1. 单参数极端外推：每句只锁定【常识地基切片】中的 **1 个** 原生器物作为 70% 常识地基，顺着一个能直接体现题眼的天然物理参数（摩擦力、温度传导、湿度、光学折射、声学分贝、几何尺寸、结构承重），往极端因果死推两步（T+1 物理后果），再拉回半步引爆荒谬错位。**【铁律】严禁写成毫无错位的纯客观生理/科普说明文（例如“呼吸一次”、“心跳微弱”、“眨眼一次”等纯科普事实直接判死，无错位即非大喜利）！**
2. 零人为借口铁律：只靠纯客观的器物状态或物理机制异常直接成立，不添加多余的人情解释，且严禁违背基本物理常识。

【语言与声学规范】
1. 直接说清铁律：主谓宾或因果动作清晰，一秒读通，严禁名词堆砌哑谜。
2. 长度与连贯：不超过 14 字，严禁使用标点符号，严禁在句中使用空格断句。
3. 底词右置（Ochi）：把最终推演出的极端物理结果压在全句最后 2~4 个字。
4. 虚词断头台：清零“的、了、着、因为、所以”等连接词与助词，零情绪词。

【负向排除集】以下平庸三阱已被封禁，触碰即作废：
${(playerMsg.pipelineState.stage0.forbidden_baseline || []).join('\n')}

【交付】输出 3 句冷面、一秒读懂、无空格无标点的短句。为方便程序解析，请直接输出合法 JSON 字符串数组：["短句1", "短句2", "短句3"]，只输出 JSON。`;

            // 单实例一次发散：一次调用完成三轨（弃用 Promise.allSettled 三路并发）
            try {
              const res = await callLlmWithBackoff({
                systemPrompt: buildDivergenceSystemPrompt(sysA, sysB, sysC),
                userPrompt: `命题：${text || '根据图片'}`,
                imageBase64: img,
                onRetry: (attempt) => {
                  playerMsg.pipelineState.trackA.retries = attempt;
                  playerMsg.pipelineState.trackB.retries = attempt;
                  playerMsg.pipelineState.trackC.retries = attempt;
                }
              });
              const parsed = parseJsonSafely(res) || {};
              playerMsg.pipelineState.trackA.candidates = normalizeStringCandidates(parsed.A);
              playerMsg.pipelineState.trackB.candidates = normalizeTrackBCandidates(parsed.B);
              playerMsg.pipelineState.trackC.candidates = normalizeStringCandidates(parsed.C);
              playerMsg.pipelineState.trackA.status = playerMsg.pipelineState.trackA.candidates.length ? 'done' : 'failed';
              playerMsg.pipelineState.trackB.status = playerMsg.pipelineState.trackB.candidates.length ? 'done' : 'failed';
              playerMsg.pipelineState.trackC.status = playerMsg.pipelineState.trackC.candidates.length ? 'done' : 'failed';
            } catch (e) {
              console.error('Divergence call failed', e);
              playerMsg.pipelineState.trackA.status = 'failed';
              playerMsg.pipelineState.trackB.status = 'failed';
              playerMsg.pipelineState.trackC.status = 'failed';
              throw e;
            }

            // Consolidate Candidates
            const allCandidates = [
              ...playerMsg.pipelineState.trackA.candidates.map(c => `[A轨体面破绽] ${c}`),
              ...playerMsg.pipelineState.trackB.candidates.map(c => `[B轨异业动作] ${cleanPunchline(c.punchline || c.line || '')}`),
              ...playerMsg.pipelineState.trackC.candidates.map(c => `[C轨物理死磕] ${c}`)
            ].filter(line => line && !line.includes('无') && line.length > 5);

            if (allCandidates.length === 0) {
              throw new Error("三轨候选均为空或请求全部遭遇异常，请检查网络后重试。");
            }

            // ==========================================
            // STAGE 2: 公诉人证伪裁决与句法骨架重铸
            // ==========================================
        return allCandidates;
        }
