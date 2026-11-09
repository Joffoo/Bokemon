// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
        async function handleSend() {
          const text = inputText.value.trim();
          const img = selectedImage.value ? selectedImage.value.dataUrl : null;
          const imgName = selectedImage.value ? selectedImage.value.name : '';

          if (!text && !img) return;

          // Check if API key is provided
          if (!config.apiKey) {
            showSettingsModal.value = true;
            testStatus.value = 'error';
            testMessage.value = '请先填写 API Key 才能向大模型发起实时请求，或者使用“体验离线演示”！';
            return;
          }

          isGeneratingAny.value = true;
          playStartSound();
          inputText.value = '';
          selectedImage.value = null;

          const now = new Date();
          const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

          // Append Host Question Message
          messages.value.push({
            id: Date.now(),
            time: timeStr,
            showTime: true,
            role: 'host',
            text: text || `【看图大喜利命题】${imgName}`,
            imageDataUrl: img
          });

          // DIRECT MODE BRANCH (Single Prompt, No Workflow)
          if (pipelineMode.value === 'direct') {
            const playerMsg = reactive({
              id: Date.now() + 1,
              time: timeStr,
              showTime: false,
              role: 'player',
              isGenerating: true,
              champion: '',
              memeDataUrl: null,
              expandedDetails: false,
              pipelineState: null // No multi-stage pipeline state
            });

            messages.value.push(playerMsg);
            scrollToBottom();

            try {
              const directSystemPrompt = `请对下面的大喜利题目给出一句幽默搞笑的回答，只输出这一句话本身。`;

              const reply = await callLlmWithBackoff({
                systemPrompt: directSystemPrompt,
                userPrompt: text || `请根据图片做一句极品大喜利回答`,
                imageBase64: img
              });

              const cleaned = cleanDirectReply(reply) || cleanPunchline(reply) || '大喜利金句生成完毕';
              playerMsg.champion = cleaned;

              if (img) {
                try {
                  const memeUrl = await renderCanvasMeme(img, cleaned);
                  playerMsg.memeDataUrl = memeUrl;
                } catch (e) {}
              }

              playChampionSound();
              showToast('🚀 极简模式：已秒出金句！');
            } catch (err) {
              console.error('Direct generation error:', err);
              playerMsg.champion = '生成遇到异常：' + err.message;
              showToast('生成异常：' + err.message);
            } finally {
              playerMsg.isGenerating = false;
              isGeneratingAny.value = false;
              scrollToBottom();
            }
            return;
          }

          // WORKFLOW MODE BRANCH (4-Stage Multi-Agent)
          // Append Player Placeholder
          const playerMsg = reactive({
            id: Date.now() + 1,
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
              stage0: { raw_telemetry: '', forbidden_baseline: [], secular_domains: [] },
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

          try {
          const parsedS0 = await _sendStage0(playerMsg, text, img);
          const allCandidates = await _sendDiverge(playerMsg, text, img);
          await _sendJudge(playerMsg, text, img, allCandidates);
          } catch (err) {
            console.error('Pipeline error:', err);
            playerMsg.champion = '执行遇阻：' + err.message;
            playerMsg.pipelineState.currentStageName = '✕ 异常中断';
            showToast('生成中断：' + err.message, 3500);
          } finally {
            playerMsg.isGenerating = false;
            isGeneratingAny.value = false;
            scrollToBottom();
          }
        }

