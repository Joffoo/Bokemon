// Bokeman _worker.js
// 兼容 Cloudflare Workers (Static Assets) 与 Cloudflare Pages Advanced 模式
// 自动拦截 /api/proxy 请求，实现浏览器跨域（CORS）中转；其他请求原样委托给静态资源资产服务。

const FORWARD = ['authorization', 'content-type', 'accept'];
const SKIP_RESP = new Set(['transfer-encoding', 'connection', 'content-length', 'content-encoding', 'keep-alive', 'server', 'date']);

function isPrivateHost(h) {
  h = h.toLowerCase().replace(/^\[|\]$/g, '');
  if (h === 'localhost' || h.endsWith('.localhost') || h.endsWith('.local') || h.endsWith('.internal')) return true;
  if (h === '::1' || h === '::' || h.startsWith('fc') || h.startsWith('fd') || h.startsWith('fe80')) return true;
  const m = h.match(/^(\d+)\.(\d+)\.(\d+)\.(\d+)$/);
  if (m) {
    const [a, b] = [Number(m[1]), Number(m[2])];
    return a === 0 || a === 10 || a === 127 || (a === 169 && b === 254) || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168);
  }
  return false;
}

function handleProxy(request, env) {
  const fail = (code, msg) => {
    return new Response(msg, {
      status: code,
      headers: {
        'X-Bokeman-Proxy': '1',
        'Content-Type': 'text/plain; charset=utf-8',
        'Access-Control-Allow-Origin': '*'
      }
    });
  };

  if (request.method !== 'GET' && request.method !== 'POST') {
    return fail(405, 'method not allowed');
  }

  const reqUrl = new URL(request.url);
  const targetStr = reqUrl.searchParams.get('u');
  if (!targetStr) return fail(400, 'missing target url');

  let target;
  try {
    target = new URL(targetStr);
  } catch (e) {
    return fail(400, 'bad target url');
  }

  if (target.protocol !== 'http:' && target.protocol !== 'https:') {
    return fail(400, 'bad target url');
  }

  if (isPrivateHost(target.hostname)) {
    return fail(403, 'private target not allowed');
  }

  const allowStr = (env && env.PROXY_ALLOW_HOSTS) || '';
  const allow = allowStr.split(',').map((s) => s.trim().toLowerCase()).filter(Boolean);
  if (allow.length && !allow.includes(target.hostname.toLowerCase())) {
    return fail(403, 'host not allowed');
  }

  const headers = new Headers();
  headers.set('User-Agent', 'Mozilla/5.0 (Bokeman proxy)');
  for (const k of FORWARD) {
    const val = request.headers.get(k);
    if (val) headers.set(k, val);
  }

  return (async () => {
    try {
      const body = request.method === 'POST' ? request.body : undefined;
      const up = await fetch(target.toString(), {
        method: request.method,
        headers,
        body,
        redirect: 'manual'
      });

      const resHeaders = new Headers();
      resHeaders.set('X-Bokeman-Proxy', '1');
      resHeaders.set('Access-Control-Allow-Origin', '*');
      up.headers.forEach((v, k) => {
        const lower = k.toLowerCase();
        if (!SKIP_RESP.has(lower) && !lower.startsWith('access-control-')) {
          resHeaders.set(k, v);
        }
      });

      return new Response(up.body, {
        status: up.status,
        headers: resHeaders
      });
    } catch (e) {
      return fail(502, '中转无法连接上游 ' + target.hostname + '：' + (e && e.message));
    }
  })();
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === '/api/proxy') {
      return handleProxy(request, env);
    }
    // 静态资源回源 (Cloudflare Workers Static Assets 或 Pages)
    if (env.ASSETS && typeof env.ASSETS.fetch === 'function') {
      return env.ASSETS.fetch(request);
    }
    return new Response('Not found', { status: 404 });
  }
};
