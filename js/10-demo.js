// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
        async function runMockPreset(presetIndex = 0) {
          showPresetsModal.value = false;
          isGeneratingAny.value = true;
          playStartSound();

          const now = new Date();
          const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

          const mockQuestion = "史上首个 130 人组成的摇滚乐队解散，理由是什么？";
          const mockImg = createPresetImageSvg(mockQuestion, ['#1A1A1D', '#C3073F'], '🎸');

          // Host Message
          messages.value.push({
            id: Date.now(),
            time: timeStr,
            showTime: true,
            role: 'host',
            text: mockQuestion,
            imageDataUrl: mockImg
          });

          // Player placeholder
          const playerMsgId = Date.now() + 1;
          const playerMsg = reactive({
            id: playerMsgId,
            time: timeStr,
            showTime: false,
            role: 'player',
            isGenerating: true,
            champion: '',
            memeDataUrl: null,
            expandedDetails: false,
            pipelineState: {
              currentStage: 0,
              currentStageName: '分析题面常识中...',
              stage0: { raw_telemetry: '', forbidden_baseline: [] },
              trackA: { status: 'idle', retries: 0, candidates: [] },
              trackB: { status: 'idle', retries: 0, candidates: [] },
              trackC: { status: 'idle', retries: 0, candidates: [] },
              stage2: {
                pk_interrogation: '',
                track_champions: {},
                initial_champion: '',
                recast_variants: {},
                crowning_reason: ''
              }
            }
          });

          messages.value.push(playerMsg);
          scrollToBottom();

          // Stage 0 Demo
          await new Promise(r => setTimeout(r, 800));
          playerMsg.pipelineState.stage0 = {
            raw_telemetry: "主体为130人超大规模摇滚乐队现场。常识地基器物包括：吉他调音器、排练室门卡、主唱麦克风、舞台监听音箱、台下跳水区。错位方向：用极度琐碎具体的组织微动作和考勤规矩，去冲撞摇滚乐本应狂放不羁的形式感。",
            forbidden_baseline: [
              "[阱1 现实观察] 人太多了分钱不均吵架解散（现实叹气观察）",
              "[阱2 廉价网梗] 只要人够多排练室都装不下（网梗套路）",
              "[阱3 情绪直给] 根本听不清主唱在唱什么太吵了（情绪直给吐槽）"
            ]
          };

          // Stage 1 Demo (Concurrency)
          playerMsg.pipelineState.currentStage = 1;
          playerMsg.pipelineState.currentStageName = '多角度脑洞构思中...';
          playerMsg.pipelineState.trackA.status = 'running';
          playerMsg.pipelineState.trackB.status = 'running';
          playerMsg.pipelineState.trackC.status = 'running';
          scrollToBottom();

          await new Promise(r => setTimeout(r, 1000));
          playerMsg.pipelineState.trackA.candidates = [
            "调完第一百三十把吉他第一把又跑调了",
            "主唱跳水台下全都是队友",
            "排练室门禁刷完最后一人正好该下班了"
          ];
          playerMsg.pipelineState.trackA.status = 'done';

          await new Promise(r => setTimeout(r, 600));
          playerMsg.pipelineState.trackB.candidates = [
            { category: "[15] 长途货运治超", punchline: "全员上台前必须先上地磅测轴重" },
            { category: "[24] 高速收费站", punchline: "主唱进排练室先领卡出排练室扫码缴费" },
            { category: "[1] 市政危房维保", punchline: "鼓手敲第一下现场直接触发危房警报" },
            { category: "[12] 业委会物业纠纷", punchline: "居委会大妈直接把总闸拉了" }
          ];
          playerMsg.pipelineState.trackB.status = 'done';

          await new Promise(r => setTimeout(r, 500));
          playerMsg.pipelineState.trackC.candidates = [
            "一百三十支麦克风啸叫当场融化调音台",
            "合练三分钟排练室氧气含量降为零",
            "吉他拨片摩擦生热点燃了第一排观众"
          ];
          playerMsg.pipelineState.trackC.status = 'done';

          // Stage 2 Demo
          playerMsg.pipelineState.currentStage = 2;
          playerMsg.pipelineState.currentStageName = '推敲精选最佳金句...';
          scrollToBottom();

          await new Promise(r => setTimeout(r, 1200));
          playerMsg.pipelineState.stage2 = {
            four_gate_eliminations: [
              "淘汰「居委会大妈直接把总闸拉了」：[关卡2 现实观察] 现实里扰民真会被拉闸，属于现实叹气观察缺乏荒谬错位",
              "淘汰「合练三分钟排练室氧气含量降为零」：[关卡3 分镜实词密度] 抽象理科参数缺乏第一反应生理画面",
              "淘汰「吉他拨片摩擦生热点燃了第一排观众」：[关卡1 抹除还原失败] 夸张失真无法还原正常日常操作"
            ],
            duel_records: "【死斗裁决】\n• A轨冠军：主唱跳水台下全是队友（落差极大，大白话画面感顶级）\n• B轨冠军：全员上台前必须先上地磅测轴重（前提级误解彻底）\n• C轨冠军：一百三十支麦克风啸叫当场融化调音台\n【终极对决】「主唱跳水台下全是队友」毫无AI公文痕迹，纯粹自然白话，一击即中！",
            pk_interrogation: "【四关检视淘汰】\n• 淘汰「居委会拉闸」：现实观察缺乏荒谬错位。\n• 淘汰「氧气为零」：抽象参数缺乏生理笑点。\n• 淘汰「拨片生热」：缺乏生活还原度。\n【终极两两PK】「主唱跳水台下全是队友」以纯粹自然白话全票加冕！",
            track_champions: {
              trackA: "主唱跳水台下全是队友",
              trackB: "全员上台前必须先上地磅测轴重",
              trackC: "一百三十支麦克风啸叫当场融化调音台"
            },
            initial_champion: "主唱跳水台下全都是队友",
            recast_variants: {
              monologue: "调完第一百三十把吉他第一把又跑调了",
              quantified: "排练室门禁刷完最后一人正好该下班了",
              cold_sketch: "主唱跳水台下全是队友"
            },
            crowning_reason: "「主唱跳水台下全是队友」用最地道的白话说清现场，拒绝AI文言文公文拼装词，底词右置反转绝妙，十个字画面跃然纸上！"
          };

          const finalChampion = "主唱跳水台下全是队友";
          playerMsg.champion = finalChampion;

          // Render Canvas Meme
          try {
            const memeUrl = await renderCanvasMeme(mockImg, finalChampion);
            playerMsg.memeDataUrl = memeUrl;
          } catch (e) {
            console.error("Meme render error", e);
          }

          playerMsg.pipelineState.currentStage = 3;
          playerMsg.isGenerating = false;
          isGeneratingAny.value = false;
          playChampionSound();
          scrollToBottom();
          showToast('已加冕全场总冠军！点击绿色气泡即可复制');
        }

        // MAIN WORKFLOW EXECUTION (Code-Driven State Machine)
