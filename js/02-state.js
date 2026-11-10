// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
        const chatContainer = ref(null);
        const inputText = ref('');
        const selectedImage = ref(null);
        const isGeneratingAny = ref(false);
        const pipelineMode = ref(localStorage.getItem('bokemon_pipeline_mode') || 'workflow');

        watch(pipelineMode, (val) => {
          try { localStorage.setItem('bokemon_pipeline_mode', val); } catch(e){}
        });

        // Modals & UI States
        const showSettingsModal = ref(false);
        const showPresetsModal = ref(false);
        const showApiKey = ref(false);
        const testingApi = ref(false);
        const testStatus = ref(null);
        const testMessage = ref('');

        const previewModal = reactive({
          visible: false,
          url: '',
          title: ''
        });

        const sharePosterModal = reactive({
          visible: false,
          url: '',
          title: '大喜利对决分享卡片'
        });

        const toast = reactive({
          visible: false,
          message: '',
          timer: null
        });

        // Dynamic models fetching state
        const fetchingModels = ref(false);
        const fetchedModels = ref([]);
        const showModelDropdown = ref(false);
        const modelSearchQuery = ref('');
        const recommendedModels = [
          'gpt-4o',
          'gpt-4o-mini',
          'deepseek-chat',
          'claude-3-7-sonnet'
        ];

        const filteredFetchedModels = computed(() => {
          if (!modelSearchQuery.value.trim()) return fetchedModels.value;
          const q = modelSearchQuery.value.toLowerCase().trim();
          return fetchedModels.value.filter(m => m.toLowerCase().includes(q));
        });

        const soundEnabled = ref(true);

        const providerPresets = [
          { name: 'OpenAI 官方', url: 'https://api.openai.com/v1', defaultModel: 'gpt-4o' },
          { name: 'OpenRouter', url: 'https://openrouter.ai/api/v1', defaultModel: 'deepseek/deepseek-chat' },
          { name: 'DeepSeek 官方', url: 'https://api.deepseek.com/v1', defaultModel: 'deepseek-chat' },
          { name: '硅基流动', url: 'https://api.siliconflow.cn/v1', defaultModel: 'deepseek-ai/DeepSeek-V3' }
        ];

        // Config model (BYOK)
        const config = reactive({
          baseUrl: 'https://api.openai.com/v1',
          apiKey: '',
          model: 'gpt-4o',
          timeoutSeconds: 120,
          maxRetries: 3,
          temperature: 0.7,
          rememberKey: true
        });

        const tempConfig = reactive({ ...config });

        const DEFAULT_WELCOME_MESSAGE = {
          id: 1,
          time: '刚刚',
          showTime: true,
          role: 'host',
          text: '欢迎来到 Bokemon！请在下方输入文字命题，或点击 📎 按钮上传图片命题。',
          imageDataUrl: null
        };

        function getInitialMessages() {
          try {
            const raw = localStorage.getItem('oogiri_chat_messages');
            if (raw) {
              const parsed = JSON.parse(raw);
              if (Array.isArray(parsed) && parsed.length > 0) {
                return parsed.map(m => {
                  if (m.isGenerating) {
                    return { ...m, isGenerating: false };
                  }
                  return m;
                });
              }
            }
          } catch (e) {
            console.warn('Failed to parse saved chat messages from localStorage:', e);
          }
          return [DEFAULT_WELCOME_MESSAGE];
        }

        // Messages list restored from localStorage
        const messages = ref(getInitialMessages());

        // Function to persist messages to localStorage
        function saveMessagesToStorage() {
          try {
            localStorage.setItem('oogiri_chat_messages', JSON.stringify(messages.value));
          } catch (e) {
            console.warn('Failed to save full messages to localStorage (quota exceeded?), pruning older images...', e);
            try {
              const pruned = messages.value.slice(-30).map((m, idx, arr) => {
                if (idx < arr.length - 4) {
                  return { ...m, imageDataUrl: null, memeDataUrl: null };
                }
                return m;
              });
              localStorage.setItem('oogiri_chat_messages', JSON.stringify(pruned));
            } catch (e2) {
              console.error('Failed to save pruned messages to localStorage', e2);
            }
          }
        }

        // Watch messages deeply to auto-persist any change
        watch(messages, () => {
          saveMessagesToStorage();
        }, { deep: true });

        // Preset prompts based on 大喜利十题四组实测汇总.md
        const textPresets = [
          {
                    "title": "T01 · 妈妈和魔术师出轨了，你是怎么发现的？",
                    "prompt": "妈妈和魔术师出轨了，你是怎么发现的？",
                    "description": "家庭伦理常识地基与舞台魔术道具的意外穿帮"
          },
          {
                    "title": "T02 · 史上首个 130 人组成的摇滚乐队解散，理由是什么？",
                    "prompt": "史上首个 130 人组成的摇滚乐队解散，理由是什么？",
                    "description": "超大规模乐队现场与极繁琐组织考勤纪律的剧烈冲突"
          },
          {
                    "title": "T03 · 每 8 秒发生一次的是什么行为？",
                    "prompt": "每 8 秒发生一次的是什么行为？",
                    "description": "极短物理时间刻度下的世俗职业肌肉记忆"
          },
          {
                    "title": "T04 · 拍马屁的忍者对前辈忍者说了什么？",
                    "prompt": "拍马屁的忍者对前辈忍者说了什么？",
                    "description": "传统忍术器物与现代职场谄媚的荒诞错位"
          },
          {
                    "title": "T05 · 俗话说佛也有三次好脾气，第一次见面就把佛惹火的行为是什么？",
                    "prompt": "俗话说佛也有三次好脾气，第一次见面就把佛惹火的行为是什么？",
                    "description": "庄严肃穆宗教道场与市井凡人算计习惯的碰撞"
          },
          {
                    "title": "T06 · 精通 SM 的传说女王大人最终领悟的终极辱骂台词是什么？",
                    "prompt": "精通 SM 的传说女王大人最终领悟的终极辱骂台词是什么？",
                    "description": "绝对权威人设与平庸生活现实的破防"
          }
];

        const imagePresets = [
          {
                    "title": "P01 · 会议圆桌听讲",
                    "prompt": "【看图大喜利】会议圆桌听讲",
                    "description": "国际会议圆桌严肃听讲（实测原图）",
                    "dataUrl": BK.PA.img1
          },
          {
                    "title": "P02 · 典礼长者按胸口",
                    "prompt": "【看图大喜利】典礼长者按胸口",
                    "description": "盛大典礼长者庄严按抚胸口（实测原图）",
                    "dataUrl": BK.PA.img2
          },
          {
                    "title": "P03 · 鼓手前倾双槌平刺",
                    "prompt": "【看图大喜利】鼓手前倾双槌平刺",
                    "description": "摇滚舞台鼓手前倾双槌平刺（实测原图）",
                    "dataUrl": BK.PA.img3
          }
];

