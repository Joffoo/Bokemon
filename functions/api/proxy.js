// Bokeman 跨域中转（Cloudflare Pages Functions 原生标准）。
// 页面调用 /api/proxy?u=<用户填写的完整 API 地址>，本函数把请求原样转发过去。
// 仅在浏览器直连失败（中转站不开放 CORS）时由前端自动回退使用；页面与本函数同源。

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

export async function onRequest(context) {
  const { request, env } = context;

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
}
