// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
        function loadSavedConfig() {
          try {
            const snd = localStorage.getItem('oogiri_sound_enabled');
            if (snd !== null) {
              soundEnabled.value = snd !== 'false';
            }

            let raw = sessionStorage.getItem('oogiri_flow_config');
            if (raw) {
              const parsed = JSON.parse(raw);
              Object.assign(config, parsed);
              config.rememberKey = false;
            } else {
              raw = localStorage.getItem('oogiri_flow_config');
              if (raw) {
                const parsed = JSON.parse(raw);
                Object.assign(config, parsed);
                config.rememberKey = true;
              }
            }

            const cachedModels = localStorage.getItem('oogiri_cached_models');
            if (cachedModels) {
              try {
                fetchedModels.value = JSON.parse(cachedModels);
              } catch (e) {}
            }
          } catch (e) {
            console.error('Failed to load saved config:', e);
          }
          Object.assign(tempConfig, config);
        }

        // Open/Close settings modal with clean temp state
        function openSettingsModal() {
          Object.assign(tempConfig, config);
          testStatus.value = null;
          testMessage.value = '';
          showSettingsModal.value = true;
        }

        function closeSettingsModal() {
          Object.assign(tempConfig, config);
          testStatus.value = null;
          testMessage.value = '';
          showSettingsModal.value = false;
        }

        // Save BYOK settings
        function saveSettings() {
          Object.assign(config, tempConfig);
          try {
            if (config.rememberKey) {
              localStorage.setItem('oogiri_flow_config', JSON.stringify(config));
              sessionStorage.removeItem('oogiri_flow_config');
            } else {
              sessionStorage.setItem('oogiri_flow_config', JSON.stringify(config));
              localStorage.removeItem('oogiri_flow_config');
            }
          } catch (e) {
            console.error('Failed to save to storage', e);
          }
          showSettingsModal.value = false;
          showToast('设置已保存');
        }

        // Purge credentials & local model cache
        function purgeCredentials() {
          try {
            localStorage.removeItem('oogiri_flow_config');
            sessionStorage.removeItem('oogiri_flow_config');
            localStorage.removeItem('oogiri_cached_models');
          } catch (e) {}
          config.apiKey = '';
          config.baseUrl = 'https://api.openai.com/v1';
          config.model = 'gpt-4o';
          config.rememberKey = true;
          Object.assign(tempConfig, config);
          fetchedModels.value = [];
          showModelDropdown.value = false;
          testStatus.value = null;
          testMessage.value = '';
          showToast('已清空本地凭据与模型缓存');
        }

        // Select Provider Preset
        function selectProvider(provider) {
          tempConfig.baseUrl = provider.url;
          if (provider.defaultModel && (!tempConfig.model || tempConfig.model === 'gpt-4o')) {
            tempConfig.model = provider.defaultModel;
          }
          showToast(`已选用 ${provider.name} 预设`);
        }

        // ==========================================
        // WEB AUDIO SYNTHESIS ENGINE (Zero external dependencies)
        // ==========================================
        let audioCtx = null;
        // Initialize saved config on startup
        loadSavedConfig();
        // Dynamic Available Models Fetcher (/v1/models)
        async function fetchAvailableModels() {
          if (!tempConfig.apiKey || !tempConfig.apiKey.trim()) {
            testStatus.value = 'error';
            testMessage.value = '请先输入 API Key 再拉取模型列表！';
            return;
          }

          fetchingModels.value = true;
          testStatus.value = 'testing';
          testMessage.value = '正在连通服务端拉取可用模型列表 (/models)...';

          try {
            let base = (tempConfig.baseUrl || 'https://api.openai.com/v1').trim().replace(/\/+$/, '');
            base = base.replace(/\/chat\/completions\/?$/, '');

            let endpointsToTry = [];
            if (base.endsWith('/v1')) {
              endpointsToTry = [`${base}/models`, `${base.replace(/\/v1$/, '')}/models`];
            } else if (base.includes('/v1/')) {
              endpointsToTry = [base.replace(/\/v1\/.*$/, '/v1/models')];
            } else {
              endpointsToTry = [`${base}/v1/models`, `${base}/models`];
            }

            let res = null;
            let lastErr = null;

            for (const ep of endpointsToTry) {
              try {
                const r = await bkFetch(ep, {
                  method: 'GET',
                  headers: {
                    'Authorization': `Bearer ${tempConfig.apiKey.trim()}`
                  }
                });
                if (r.ok) {
                  res = r;
                  break;
                } else {
                  lastErr = lastErr || new Error(`HTTP ${r.status}（${ep}）`);
                }
              } catch (e) {
                // TypeError: Failed to fetch = 网络层/跨域层失败（拿不到状态码），补上端点与可能原因
                lastErr = lastErr || ((e && e.message === 'Failed to fetch')
                  ? new Error(`浏览器无法连接 ${ep}（网络不通、被代理/防火墙拦截，或该服务端未开放跨域 CORS。可手动输入模型名称直接使用，或确认 API 中转支持跨域）`)
                  : e);
              }
            }

            if (!res) {
              throw lastErr || new Error('拉取失败，请检查 Base URL 与 API Key 是否支持 /models 接口');
            }

            const data = await res.json();
            let ids = [];
            if (Array.isArray(data)) {
              ids = data.map(item => typeof item === 'string' ? item : (item.id || item.name || ''));
            } else if (data && Array.isArray(data.data)) {
              ids = data.data.map(item => item.id || item.name || '');
            } else if (data && Array.isArray(data.models)) {
              ids = data.models.map(item => item.name || item.id || '');
            }

            ids = [...new Set(ids.filter(Boolean))].sort((a, b) => a.localeCompare(b));

            if (ids.length === 0) {
              throw new Error('接口未返回任何有效的模型 ID');
            }

            fetchedModels.value = ids;
            showModelDropdown.value = true;
            try {
              localStorage.setItem('oogiri_cached_models', JSON.stringify(ids));
            } catch (e) {}

            testStatus.value = 'success';
            testMessage.value = `✓ 成功拉取到 ${ids.length} 个可用模型！点击下拉列表或搜索框即可快速选用。`;
          } catch (err) {
            testStatus.value = 'error';
            const offlineHint = (typeof navigator !== 'undefined' && !navigator.onLine) ? '（当前浏览器处于离线状态，请检查网络后重试）' : '';
            testMessage.value = `拉取模型失败：${err.message}${offlineHint}`;
          } finally {
            fetchingModels.value = false;
          }
        }

        // Test API Connection
        async function testApiConnection() {
          if (!tempConfig.apiKey) {
            testStatus.value = 'error';
            testMessage.value = '请先输入 API Key！';
            return;
          }

          testingApi.value = true;
          testStatus.value = 'testing';
          testMessage.value = '正在连通中转接口...';

          const testController = new AbortController();
          const testTimerId = setTimeout(() => testController.abort(), (tempConfig.timeoutSeconds || 60) * 1000);
          try {
            let base = (tempConfig.baseUrl || 'https://api.openai.com/v1').trim().replace(/\/+$/, '');
            let endpoint = base;
            if (!base.endsWith('/chat/completions')) {
              endpoint = base.endsWith('/v1') ? `${base}/chat/completions` : `${base}/v1/chat/completions`;
            }

            const res = await bkFetch(endpoint, {
              signal: testController.signal,
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${tempConfig.apiKey.trim()}`
              },
              body: JSON.stringify({
                model: tempConfig.model.trim(),
                messages: [{ role: 'user', content: 'Say OK' }],
                max_tokens: 5
              })
            });

            if (!res.ok) {
              const txt = await res.text();
              throw new Error(`HTTP ${res.status}: ${txt.slice(0, 100)}`);
            }

            testStatus.value = 'success';
            testMessage.value = '✓ 连通成功！模型响应正常。';
          } catch (err) {
            testStatus.value = 'error';
            testMessage.value = err.name === 'AbortError' ? '连通失败：请求超时，服务端长时间无响应' : (err.message === 'Failed to fetch' ? '连通失败：浏览器无法连接该地址（网络不通，或服务端未开放跨域 CORS。可确认 API 地址或中转站是否支持跨域）' : `连通失败：${err.message}`);
          } finally {
            clearTimeout(testTimerId);
            testingApi.value = false;
          }
        }
