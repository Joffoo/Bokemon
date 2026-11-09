// Bokeman —— 自 index.html 字节级搬移（split_index.py 生成；提示词 SSOT 见 .agents/skills/oogiri-flow/SKILL.md）
    const { createApp, ref, reactive, computed, watch, onMounted, nextTick } = Vue;

    // 浏览器直连 API；若被 CORS 拦截（中转站不开放跨域，表现为 TypeError），自动改走同源 /api/proxy 中转
    // （线上由 Vercel 函数 api/proxy.js 提供，本地由 server.py 提供）。目标地址完全取自用户填写的 Base URL。
    // 直连失败时请求根本没发出（预检被拒），所以回退重发不会造成重复调用。
    const BK_NEEDS_PROXY = new Set();
    async function bkFetch(url, init) {
      let origin;
      try { origin = new URL(url).origin; } catch (e) { return fetch(url, init); }
      // file:// 或同源地址：没有中转可用，直接请求
      if (!/^https?:$/.test(location.protocol) || origin === location.origin) return fetch(url, init);
      const viaProxy = async (firstErr) => {
        const r = await fetch('api/proxy?u=' + encodeURIComponent(url), init);
        // 没有中转接口（纯静态托管）时拿到的是普通 404，此时仍报原始的直连错误
        if (!r.headers.get('X-Bokeman-Proxy')) throw firstErr || new TypeError('Failed to fetch');
        return r;
      };
      if (BK_NEEDS_PROXY.has(origin)) return viaProxy();
      try {
        return await fetch(url, init);
      } catch (e) {
        if (!e || e.name !== 'TypeError') throw e; // 超时(AbortError)等不回退
        BK_NEEDS_PROXY.add(origin);
        try { return await viaProxy(e); } catch (e2) { BK_NEEDS_PROXY.delete(origin); throw e; }
      }
    }
    // 24 Macro Ecological Secular Domains from SKILL.md
    const SECULAR_DOMAINS_24 = [
      "[1] 市政危房维保",   "[2] 临期商超早市",   "[3] 驾校科目考场",   "[4] 急诊老年康养",
      "[5] 城中村租房中介", "[6] 民政婚姻登记",   "[7] 海关安检清关",   "[8] 殡葬法事公墓",
      "[9] 县城草台剧组",   "[10] 典当行拍卖",    "[11] 餐饮后厨卫生",  "[12] 业委会物业纠纷",
      "[13] 古董文玩鉴定",  "[14] 宠物绝育检疫",  "[15] 长途货运治超",  "[16] 废品回收拆解",
      "[17] 澡堂足疗技师",  "[18] 公园象棋摊",    "[19] 农贸水产批发",  "[20] 裁缝铺改衣",
      "[21] 修锁配钥匙",    "[22] 广场舞音响",    "[23] 老式国营食堂",  "[24] 高速收费站"
    ];

    // Helper: Build a minimal standalone SVG Data URL for presets
    // Helper: Build a minimal standalone SVG Data URL for presets
    function createPresetImageSvg(title, bgGradient, mainIcon) {
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="600" height="450" viewBox="0 0 600 450">
        <defs>
          <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="${bgGradient[0]}"/>
            <stop offset="100%" stop-color="${bgGradient[1]}"/>
          </linearGradient>
        </defs>
        <rect width="600" height="450" fill="url(#g)"/>
        <circle cx="300" cy="190" r="110" fill="#ffffff" opacity="0.9"/>
        <text x="300" y="215" font-size="80" text-anchor="middle" font-family="sans-serif">${mainIcon}</text>
        <rect x="50" y="330" width="500" height="60" rx="8" fill="#000000" opacity="0.25"/>
        <text x="300" y="368" font-size="22" font-weight="bold" fill="#ffffff" text-anchor="middle" font-family="sans-serif">${title}</text>
      </svg>`;
      return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
    }

    // Helper: Build authentic PNG Data URL using offscreen Canvas (100% compatible with OpenAI/Claude vision APIs)
    function createPresetImagePng(title, bgGradient, mainIcon) {
      try {
        const canvas = document.createElement('canvas');
        canvas.width = 600;
        canvas.height = 450;
        const ctx = canvas.getContext('2d');
        if (!ctx) return createPresetImageSvg(title, bgGradient, mainIcon);

        const grad = ctx.createLinearGradient(0, 0, 600, 450);
        grad.addColorStop(0, bgGradient[0]);
        grad.addColorStop(1, bgGradient[1]);
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 600, 450);

        ctx.beginPath();
        ctx.arc(300, 190, 110, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.fill();

        ctx.font = '80px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(mainIcon, 300, 190);

        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.fillRect(50, 330, 500, 60);

        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 22px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(title, 300, 360);

        return canvas.toDataURL('image/png');
      } catch (e) {
        return createPresetImageSvg(title, bgGradient, mainIcon);
      }
    }

    // Dedicated Direct-Mode Reply Sanitizer (preserves complete natural punctuation and sentence without truncation)
    function cleanDirectReply(raw) {
      if (!raw || typeof raw !== 'string') return '';
      let s = raw.trim();
      s = s.replace(/^```[\s\S]*?\n/, '').replace(/\n```$/, '');
      const lines = s.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      if (lines.length > 0) s = lines[0];
      s = s.replace(/^[\s\*\-•—–]+\s*/, '');
      s = s.replace(/^(?:\d+|[a-zA-Z])[\.、\)）]\s*/, '');
      s = s.replace(/^(?:回答|大喜利|金句|台词|吐槽)[：:\s\-—]*/i, '');
      s = s.replace(/^[「“"『《\s]+|[」”"』》\s]+$/g, '');
      s = s.replace(/[。\.]$/, '');
      return s.length > 80 ? s.slice(0, 80) : s;
    }
    window.cleanDirectReply = cleanDirectReply;

    // Universal Punchline Sanitizer (preserves natural punctuation and clean punchlines up to 120 chars)
    function cleanPunchline(raw, stripAllPunctuation = false) {
      if (!raw || typeof raw !== 'string') return '';
      let s = raw.trim();
      s = s.replace(/^```[\s\S]*?\n/, '').replace(/\n```$/, '');

      // Strip leading bullets, numbers, dashes, or markers
      s = s.replace(/^[\s\*\-•—–]+\s*/, '');
      s = s.replace(/^(?:\[\d+\]\s*|\d+[\.、\)）\-—\s]*)/, '');

      // Strip any bracketed prefix at the start, e.g. [6], [15], 【民政婚姻登记】, [B轨异业动作], (异业动作), etc.
      while (/^[\[【（\(][^\]】）\)]+[\]】）\)]\s*/.test(s)) {
        s = s.replace(/^[\[【（\(][^\]】）\)]+[\]】）\)]\s*/, '');
      }

      // Strip secular domains or track category labels if left at front (with or without numbers)
      s = s.replace(/^(?:\d+[\.、\s]*)?(?:市政危房维保|临期商超早市|驾校科目考场|急诊老年康养|城中村租房中介|民政婚姻登记|海关安检清关|殡葬法事公墓|县城草台剧组|典当行拍卖|餐饮后厨卫生|业委会物业纠纷|古董文玩鉴定|宠物绝育检疫|长途货运治超|废品回收拆解|澡堂足疗技师|公园象棋摊|农贸水产批发|裁缝铺改衣|修锁配钥匙|广场舞音响|老式国营食堂|高速收费站|异业动作|体面破绽|物理死磕|生活破绽|职业动作|物理极限)[：:\s\-—]*/i, '');

      // Strip track / role / prompt labels
      s = s.replace(/^(?:[A-Ca-c]轨(?:\([^\)]+\)|（[^）]+）)?|Subagent\s*[A-Ca-c]|Track\s*[A-Ca-c]|第[一二三123]轨|最终全场总冠军|全场总冠军|总冠军|最终加冕|加冕|最终金句|加冕金句|金句|最佳原句|冠军初稿|初稿|重铸体|润色版|喝止体|折算体|白描体|冷面体|现场体|独白体|台词|回答|解答)[：:\s\-—]*/i, '');

      // Strip quotes
      s = s.replace(/^[「“"『《\s]+|[」”"』》\s]+$/g, '');

      // Strip trailing punctuation
      s = s.replace(/[。！？\.\!]+$/, '');

      if (stripAllPunctuation) {
        // Strip internal punctuation and symbols only when explicitly requested
        s = s.replace(/[，。！？、：；“”‘’\"\'\`\s\(\)（）\[\]【】《》「」『』—\-_\*•\+\/\\]/g, '');
      }
      return s.length > 120 ? s.slice(0, 120) : s;
    }
    window.cleanPunchline = cleanPunchline;

    // Normalizer for Track candidates (supports object {tag, candidate} or raw string)
    function normalizeStringCandidates(raw) {
      let list = [];
      if (Array.isArray(raw)) {
        list = raw;
      } else if (raw && typeof raw === 'object') {
        list = raw.candidates || raw.items || raw.bokes || raw.lines || raw.results || Object.values(raw).find(v => Array.isArray(v)) || [];
      }
      return list.map(item => {
        if (typeof item === 'string') return cleanPunchline(item) || item.trim();
        if (item && typeof item === 'object') {
          const tag = item.tag || item.category || item.name || '';
          const val = item.candidate || item.punchline || item.line || item.text || item.boke || item.content || Object.values(item)[0] || '';
          const cleaned = cleanPunchline(String(val)) || String(val).trim();
          return tag ? `[${tag}] ${cleaned}` : cleaned;
        }
        return String(item);
      }).filter(s => s && s !== '无');
    }

    // Normalizer for Track B candidates
    function normalizeTrackBCandidates(raw) {
      let list = [];
      if (Array.isArray(raw)) {
        list = raw;
      } else if (raw && typeof raw === 'object') {
        list = raw.candidates || raw.items || raw.actions || raw.list || Object.values(raw).find(v => Array.isArray(v)) || [];
      }
      return list.map(item => {
        if (typeof item === 'string') {
          const match = item.match(/^(\[[^\]]+\]|\d+[\.、]\s*[^：:\s]+)[:：\s\-—]*(.*)$/);
          if (match) {
            return { category: match[1].replace(/[\[\]]/g, '').trim(), punchline: cleanPunchline(match[2]) || match[2].trim() };
          }
          return { category: '异业动作', punchline: cleanPunchline(item) || item.trim() };
        }
        if (item && typeof item === 'object') {
          const cat = item.tag || item.category || item.domain || item.name || item.industry || item.类别 || item.世俗域 || Object.keys(item)[0] || '异业动作';
          const punch = item.candidate || item.punchline || item.line || item.action || item.boke || item.text || item.content || item.台词 || Object.values(item)[1] || Object.values(item)[0] || '';
          return { category: String(cat).trim(), punchline: cleanPunchline(String(punch)) || String(punch).trim() };
        }
        return { category: '异业动作', punchline: cleanPunchline(String(item)) || String(item) };
      }).filter(c => c.punchline && c.punchline !== '无');
    }

    // 多轨独立候选生成拼装
    function buildDivergenceSystemPrompt(trackAPrompt, trackBPrompt, trackCPrompt) {
      return `【本次任务：多轨独立候选生成】
目标不是把每句答案压成同一种短句，而是找到题目与笑点之间最短、最意外、最自然的连接。
各方向互不参照、互不借用对方的词。请依次完成已启用方向的候选生成。全部完成后再输出，顺序如下。

=== 轨道 A / 体面破绽 ===
${trackAPrompt}

=== 轨道 B / 异业动作 ===
${trackBPrompt}

=== 轨道 C / 物理死磕 ===
${trackCPrompt}

【输出契约】只输出合法 JSON，除 JSON 外无任何字符：
{"A": [{"tag": "机制标签", "candidate": "候选句子"}],
 "B": [{"tag": "机制标签", "candidate": "候选句子"}],
 "C": [{"tag": "机制标签", "candidate": "候选句子"}]}`;
    }


        function parseJsonSafely(text) {
          if (!text) throw new Error("Empty LLM reply");
          let s = text.trim();
          const sanitizeCommas = str => str.replace(/,\s*([\]}])/g, '$1');

          // 1. Try markdown fenced block
          const codeMatch = s.match(/```(?:json)?\s*([\s\S]*?)\s*```/i);
          if (codeMatch) {
            try { return JSON.parse(sanitizeCommas(codeMatch[1].trim())); } catch (e) {}
          }
          // 2. Direct JSON.parse
          try { return JSON.parse(sanitizeCommas(s)); } catch (e) {}
          // 3. Find outermost braces { ... }
          const firstBrace = s.indexOf('{');
          const lastBrace = s.lastIndexOf('}');
          if (firstBrace !== -1 && lastBrace > firstBrace) {
            try { return JSON.parse(sanitizeCommas(s.substring(firstBrace, lastBrace + 1))); } catch (e) {}
          }
          // 4. Find outermost brackets [ ... ]
          const firstBracket = s.indexOf('[');
          const lastBracket = s.lastIndexOf(']');
          if (firstBracket !== -1 && lastBracket > firstBracket) {
            try { return JSON.parse(sanitizeCommas(s.substring(firstBracket, lastBracket + 1))); } catch (e) {}
          }
          throw new Error("Unable to parse structured JSON from model response.");
        }
        window.parseJsonSafely = parseJsonSafely;

        // Exponential Backoff API Caller
