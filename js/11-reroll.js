// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
        async function rerollPunchline(playerMsg) {
          if (isGeneratingAny.value || playerMsg.isGenerating) return;

          const hostMsg = findHostMessage(playerMsg);
          const promptText = hostMsg ? hostMsg.text : '大喜利命题';
          const imgUrl = hostMsg ? hostMsg.imageDataUrl : null;

          isGeneratingAny.value = true;
          playerMsg.isGenerating = true;
          playStartSound();

          // Handle Direct Mode reroll (no pipelineState)
          if (!playerMsg.pipelineState) {
            try {
              if (!config.apiKey) {
                await new Promise(r => setTimeout(r, 600));
                const mockDirects = [
                  "领唱翻开校歌本找今天的菜单",
                  "起调直接飙到帕瓦罗蒂的高音G",
                  "台下突然全体起立开始鼓掌",
                  "张嘴唱出了隔壁学校的校歌"
                ];
                playerMsg.champion = mockDirects[Math.floor(Math.random() * mockDirects.length)];
              } else {
                const directSystemPrompt = `请对下面的大喜利题目给出一句幽默搞笑的回答，只输出这一句话本身。`;
                const reply = await callLlmWithBackoff({
                  systemPrompt: directSystemPrompt,
                  userPrompt: (promptText || `请给出一句幽默大喜利回答`) + ` (请换一个完全不同、更具意外感的全新脑洞角度)`,
                  imageBase64: imgUrl
                });
                playerMsg.champion = cleanDirectReply(reply) || cleanPunchline(reply) || '大喜利金句生成完毕';
              }
              if (imgUrl) {
                try {
                  const memeUrl = await renderCanvasMeme(imgUrl, playerMsg.champion);
                  playerMsg.memeDataUrl = memeUrl;
                } catch (e) {}
              }
              playChampionSound();
              showToast('🎲 已换角度重新构思出金句！');
            } catch (err) {
              console.error('Direct reroll error:', err);
              showToast('重新构思异常：' + err.message);
            } finally {
              playerMsg.isGenerating = false;
              isGeneratingAny.value = false;
              scrollToBottom();
            }
            return;
          }

          // Reuse existing stage 0 telemetry
          const s0 = playerMsg.pipelineState?.stage0 || {
            raw_telemetry: `围绕命题「${promptText}」的常识地基器物与日常场景。`,
            forbidden_baseline: ['[阱1 现实观察] 现实叹气吐槽', '[阱2 廉价网梗] 常见烂梗', '[阱3 情绪直给] 情绪宣泄']
          };

          playerMsg.pipelineState.currentStage = 1;
          playerMsg.pipelineState.currentStageName = '多角度重新构思中...';
          playerMsg.pipelineState.trackA.status = 'running';
          playerMsg.pipelineState.trackB.status = 'running';
          playerMsg.pipelineState.trackC.status = 'running';
          scrollToBottom();

          // If no API key, run fast randomized re-roll demo
          if (!config.apiKey) {
            await new Promise(r => setTimeout(r, 600));
            // Alternative fresh mock options
            const mockTrackAOptions = [
              ["体检单必须盖火葬场公章", "工卡挂脖先通高压电", "入职体检按出厂合格证填"],
              ["晨会必须带洗脸盆点名", "工位隔板焊两米铁丝网", "迟到一秒扣除半年寿命"],
              ["体检单要求三代绝育证明", "考勤机只录入下跪姿态", "午休平躺按私自旷工处分"]
            ];
            const randA = mockTrackAOptions[Math.floor(Math.random() * mockTrackAOptions.length)];
            playerMsg.pipelineState.trackA.candidates = randA;
            playerMsg.pipelineState.trackA.status = 'done';

            await new Promise(r => setTimeout(r, 400));
            const mockTrackBOptions = [
              [
                { category: "[15] 长途货运治超", punchline: "午休进门先上地磅称过载" },
                { category: "[24] 高速收费站", punchline: "起身去厕所先刷ETC抬杆" },
                { category: "[7] 海关安检清关", punchline: "晨会脱鞋检查鞋垫含税率" },
                { category: "[3] 驾校科目考场", punchline: "回工位先挂倒挡鸣笛三声" }
              ],
              [
                { category: "[8] 殡葬法事公墓", punchline: "签合同时向工位三鞠躬" },
                { category: "[17] 澡堂足疗技师", punchline: "主管巡视逐个捏脚问吃劲" },
                { category: "[1] 市政危房维保", punchline: "敲击工位隔板检测回弹空鼓" },
                { category: "[24] 高速收费站", punchline: "打卡下班自动吐通行卡纸" }
              ],
              [
                { category: "[2] 临期商超早市", punchline: "实习生身上贴绿标打三折" },
                { category: "[16] 废品回收拆解", punchline: "离职前上磁选机过一遍铁" },
                { category: "[24] 高速收费站", punchline: "起身去洗手间必须刷ETC" },
                { category: "[7] 海关安检清关", punchline: "电脑开机先出示报关单" }
              ]
            ];
            const randB = mockTrackBOptions[Math.floor(Math.random() * mockTrackBOptions.length)];
            playerMsg.pipelineState.trackB.candidates = randB;
            playerMsg.pipelineState.trackB.status = 'done';

            await new Promise(r => setTimeout(r, 400));
            const mockTrackCOptions = [
              ["打卡机表面摩擦系数调零", "办公椅后倾两度触发自爆", "键盘空格键弹力调成八十斤"],
              ["空调常年维持零下十六度", "鼠标滑轮每转三圈自检十分钟", "饮水机出水需双人双锁核验"],
              ["考勤机指纹采集器通三万伏", "工位隔音板回音延迟八秒", "显示器亮度固定为强光手电"]
            ];
            const randC = mockTrackCOptions[Math.floor(Math.random() * mockTrackCOptions.length)];
            playerMsg.pipelineState.trackC.candidates = randC;
            playerMsg.pipelineState.trackC.status = 'done';

            playerMsg.pipelineState.currentStage = 2;
            playerMsg.pipelineState.currentStageName = '重新比对与精修...';
            scrollToBottom();

            await new Promise(r => setTimeout(r, 700));

            const recastPool = [
              {
                mono: "调完第一百三十把吉他第一把又跑调了",
                quant: "排练室门禁刷完最后一人正好该下班了",
                cold: "主唱跳水台下全是队友",
                champ: "主唱跳水台下全是队友",
                initial: "主唱跳水台下全都是队友",
                champions: {
                  trackA: "主唱跳水台下全是队友",
                  trackB: "全员上台前必须先上地磅测轴重",
                  trackC: "一百三十支麦克风啸叫当场融化调音台"
                },
                eliminations: [
                  "淘汰「居委会大妈直接把总闸拉了」：[关卡2 现实观察] 现实里扰民真会被拉闸，属于现实叹气观察缺乏荒谬错位",
                  "淘汰「合练三分钟排练室氧气含量降为零」：[关卡3 分镜实词密度] 抽象理科参数缺乏第一反应生理画面",
                  "淘汰「吉他拨片摩擦生热点燃了第一排观众」：[关卡1 抹除还原失败] 夸张失真无法还原正常日常操作"
                ],
                duel: "【死斗裁决】\n• A轨冠军：主唱跳水台下全是队友（落差极大，大白话画面感顶级）\n• B轨冠军：全员上台前必须先上地磅测轴重（前提级误解彻底）\n• C轨冠军：一百三十支麦克风啸叫当场融化调音台\n【终极两两PK】「主唱跳水台下全是队友」毫无AI公文痕迹，纯粹自然白话，一击即中！",
                reason: "「主唱跳水台下全是队友」用最地道的白话说清现场，拒绝AI文言文公文拼装词，底词右置反转绝妙，十个字画面跃然纸上！"
              },
              {
                mono: "拍拍莲花座示意佛祖往里挪",
                quant: "投完香火钱站在莲花台前等找零",
                cold: "投完香火钱站在莲花台前等找零",
                champ: "投完香火钱站在莲花台前等找零",
                initial: "投完香火钱站在莲花台前等找零",
                champions: {
                  trackA: "拍拍莲花座示意佛祖往里挪",
                  trackB: "投完香火钱站在莲花台前等找零",
                  trackC: "敲木鱼速度超每秒八十下触发超速抓拍"
                },
                eliminations: [
                  "淘汰「跪拜时嫌蒲团太硬给差评」：[关卡2 现实观察] 现实真有人会抱怨蒲团硬，缺乏形而上的神圣荒诞",
                  "淘汰「用功德箱余额刷脸支付买奶茶」：[关卡1 单点错位] 外来现代道具生硬硬塞",
                  "淘汰「给佛像刷金漆顺便贴防窥膜」：[关卡3 分镜实词密度] 概念堆砌多转半秒"
                ],
                duel: "【死斗裁决】\n• A轨冠军：拍拍莲花座示意佛祖往里挪\n• B轨冠军：投完香火钱站在莲花台前等找零\n• C轨冠军：敲木鱼速度超每秒八十下触发超速抓拍\n【终极两两PK】「投完香火钱站在莲花台前等找零」以极度市井的找零动作冒犯至高庄严道场，大白话利索，包袱脆响！",
                reason: "「投完香火钱站在莲花台前等找零」用极度市井的找零动作冒犯至高庄严道场，大白话利索，包袱脆响！"
              },
              {
                mono: "进门先把工服脱给海关",
                quant: "起身去洗手间每两米扣五毛钱",
                cold: "起身去厕所先刷ETC抬杆",
                champ: "起身去厕所先刷ETC抬杆",
                initial: "起身去厕所先刷ETC抬杆",
                champions: {
                  trackA: "考勤机必须录入下跪姿态",
                  trackB: "起身去厕所先刷ETC抬杆",
                  trackC: "办公椅后倾两度触发自爆"
                },
                eliminations: [
                  "淘汰「打卡机表面摩擦系数调零」：[关卡3 分镜实词密度] 纯物理参数抽象，缺乏生活生理直接笑点",
                  "淘汰「入职体检单盖火葬场公章」：[关卡2 反现实观察] 落差稍显刻意硬拗，擦边负面情绪",
                  "淘汰「打印前必须先打左转向灯」：[关卡1 单点错位抹除] 属于浅层工具用错而非前提级颠覆"
                ],
                duel: "【死斗裁决】\n• A轨冠军：考勤机必须录入下跪姿态\n• B轨冠军：起身去厕所先刷ETC抬杆\n• C轨冠军：办公椅后倾两度触发自爆\n【终极两两PK】「起身去厕所先刷ETC抬杆」大白话说清前提，底词右置一击毙命！",
                reason: "「起身去厕所先刷ETC抬杆」抹掉末词还原为极度日常的『起身去厕所』，底词右置一击毙命，白话利索，画面感顶级。"
              }
            ];
            const pick = recastPool.find(p => cleanPunchline(p.champ) !== playerMsg.champion) || recastPool[0];

            playerMsg.pipelineState.stage2 = {
              four_gate_eliminations: pick.eliminations,
              duel_records: pick.duel,
              pk_interrogation: pick.duel,
              track_champions: pick.champions,
              initial_champion: pick.initial,
              recast_variants: {
                monologue: pick.mono,
                quantified: pick.quant,
                cold_sketch: pick.cold
              },
              crowning_reason: pick.reason
            };
            playerMsg.champion = cleanPunchline(pick.champ);

            if (imgUrl) {
              try {
                const memeUrl = await renderCanvasMeme(imgUrl, playerMsg.champion);
                playerMsg.memeDataUrl = memeUrl;
              } catch (e) {}
            }

            playerMsg.pipelineState.currentStage = 3;
            playerMsg.isGenerating = false;
            isGeneratingAny.value = false;
            playChampionSound();
            scrollToBottom();
            showToast('🎲 已换角度决出全新冠军金句！');
            return;
          }

          // Real LLM Re-roll pipeline
          try {
          const allCandidates = await _rerollDiverge(playerMsg, promptText, imgUrl, s0);
          await _rerollJudge(playerMsg, promptText, imgUrl, s0, allCandidates);
          } catch (err) {
            console.error('Reroll failed:', err);
            showToast('换角度失败：' + err.message);
          } finally {
            playerMsg.isGenerating = false;
            isGeneratingAny.value = false;
            scrollToBottom();
          }
        }

