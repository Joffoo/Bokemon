// Bokeman 跨域中转（Vercel Serverless Function）。
// 页面调用 /api/proxy?u=<用户填写的完整 API 地址>，本函数把请求原样转发过去。
// 仅在浏览器直连失败（中转站不开放 CORS）时由前端自动回退使用；页面与本函数同源，无需任何跨域头。
//
// 安全：
// - Authorization 只透传，不保存、不打印；
// - 拒绝非 http(s)、以及指向本机/内网的目标，避免被当作内网探测跳板；
// - 拒绝跨站来源（Origin 与 Host 不一致）；
// - 可选环境变量 PROXY_ALLOW_HOSTS（逗号分隔）：设置后只允许转发到这些主机。

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

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

module.exports = async (req, res) => {
  const fail = (code, msg) => { res.statusCode = code; res.setHeader('X-Bokeman-Proxy', '1'); res.setHeader('Content-Type', 'text/plain; charset=utf-8'); res.end(msg); };

  if (req.method !== 'GET' && req.method !== 'POST') return fail(405, 'method not allowed');

  const origin = req.headers.origin;
  if (origin) {
    try { if (new URL(origin).host !== req.headers.host) return fail(403, 'forbidden origin'); }
    catch (e) { return fail(403, 'forbidden origin'); }
  }

  let target;
  try {
    const u = new URL(req.url, 'http://x').searchParams.get('u');
    target = new URL(u);
  } catch (e) { return fail(400, 'bad target url'); }
  if (target.protocol !== 'http:' && target.protocol !== 'https:') return fail(400, 'bad target url');
  if (isPrivateHost(target.hostname)) return fail(403, 'private target not allowed');
  const allow = (process.env.PROXY_ALLOW_HOSTS || '').split(',').map((s) => s.trim().toLowerCase()).filter(Boolean);
  if (allow.length && !allow.includes(target.hostname.toLowerCase())) return fail(403, 'host not allowed');

  const headers = { 'User-Agent': 'Mozilla/5.0 (Bokeman proxy)' };
  for (const k of FORWARD) if (req.headers[k]) headers[k] = req.headers[k];

  try {
    const body = req.method === 'POST' ? await readBody(req) : undefined;
    // 58s 主动超时：略低于 vercel.json 的 maxDuration=60s，确保函数先返回 502 而不是被平台强杀
    const up = await fetch(target.toString(), { method: req.method, headers, body, redirect: 'manual', signal: AbortSignal.timeout(58000) });
    res.statusCode = up.status;
    res.setHeader('X-Bokeman-Proxy', '1');
    up.headers.forEach((v, k) => { if (!SKIP_RESP.has(k) && !k.startsWith('access-control-')) res.setHeader(k, v); });
    res.end(Buffer.from(await up.arrayBuffer()));
  } catch (e) {
    fail(502, '中转无法连接上游 ' + target.hostname + '：' + (e && e.message));
  }
};
