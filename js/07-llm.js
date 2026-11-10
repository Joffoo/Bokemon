// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
        async function callLlmWithBackoff({ systemPrompt, userPrompt, imageBase64, onRetry }) {
          let attempt = 0;
          const maxRetries = config.maxRetries || 3;
          let delayMs = 1000;

          let base = (config.baseUrl || 'https://api.openai.com/v1').trim().replace(/\/+$/, '');
          let endpoint = base;
          if (!base.endsWith('/chat/completions')) {
            endpoint = base.endsWith('/v1') ? `${base}/chat/completions` : `${base}/v1/chat/completions`;
          }
          const timeoutSec = config.timeoutSeconds || 120;

          while (attempt <= maxRetries) {
            const controller = new AbortController();
            // 超时覆盖「连接 + 读取响应体」全程，finally 中统一清理
            const timerId = setTimeout(() => controller.abort(), timeoutSec * 1000);
            try {
              if (!config.apiKey || !config.apiKey.trim()) throw Object.assign(new Error('未配置 API Key'), { fatal: true });
              if (!config.model || !config.model.trim()) throw Object.assign(new Error('未配置模型名称'), { fatal: true });

              const messagesPayload = [
                { role: 'system', content: systemPrompt }
              ];

              if (imageBase64) {
                messagesPayload.push({
                  role: 'user',
                  content: [
                    { type: 'text', text: userPrompt },
                    { type: 'image_url', image_url: { url: imageBase64 } }
                  ]
                });
              } else {
                messagesPayload.push({ role: 'user', content: userPrompt });
              }

              const res = await bkFetch(endpoint, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${config.apiKey.trim()}`
                },
                body: JSON.stringify({
                  model: config.model.trim(),
                  messages: messagesPayload,
                  temperature: config.temperature !== undefined ? config.temperature : 0.7
                }),
                signal: controller.signal
              });

              if (!res.ok) {
                const errTxt = await res.text();
                // 4xx（除 408/429）重试无意义（Key 错误、参数错误、模型不存在等），直接失败
                const retryable = res.status === 408 || res.status === 429 || res.status >= 500;
                throw Object.assign(new Error(`HTTP ${res.status}: ${errTxt.slice(0, 120)}`), { fatal: !retryable });
              }

              const data = await res.json();
              const content = data.choices?.[0]?.message?.content;
              if (!content) throw new Error("Empty choices in response");
              return content;

            } catch (err) {
              // 超时属于等待超时，直接抛出，严禁在思考超时后让用户从头被动重试 3 遍
              if (err && err.name === 'AbortError') {
                throw Object.assign(new Error(`服务端响应超时（超过 ${timeoutSec} 秒未完成），请检查网络或更换更敏捷的模型`), { fatal: true });
              }
              attempt++;
              if ((err && err.fatal) || attempt > maxRetries) {
                // TypeError: Failed to fetch = 网络层/跨域层失败，附上端点与可能原因，避免裸报错无法定位
                throw (err && err.message === 'Failed to fetch')
                  ? new Error(`浏览器无法连接 ${endpoint}（网络不通、被代理/防火墙拦截，或该服务端未开放跨域 CORS。请确认 API 中转支持跨域）`)
                  : err;
              }
              if (onRetry) onRetry(attempt, delayMs, err.message);
              await new Promise(r => setTimeout(r, delayMs));
              delayMs *= 2; // Exponential backoff (1s -> 2s -> 4s)
            } finally {
              clearTimeout(timerId);
            }
          }
        }

        // Client-side HTML5 Canvas Meme Rendering (Strictly replicating render_meme.py)
