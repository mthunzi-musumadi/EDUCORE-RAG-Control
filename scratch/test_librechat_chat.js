const http = require('http');

async function request(urlStr, options = {}, body = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlStr);
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    const bodyStr = body ? (typeof body === 'string' ? body : JSON.stringify(body)) : null;
    if (bodyStr) headers['Content-Length'] = Buffer.byteLength(bodyStr);

    const req = http.request(url, { ...options, headers }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, headers: res.headers, data: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, headers: res.headers, data });
        }
      });
    });
    req.on('error', reject);
    if (bodyStr) req.write(bodyStr);
    req.end();
  });
}

async function run() {
  console.log('=== TESTING LIBRECHAT CHAT WITH MODEL SPEC ===');

  // 1. Login
  const loginRes = await request('http://localhost:3080/api/auth/login', { method: 'POST' }, {
    email: 'admin@localhost.com',
    password: 'Password123!'
  });
  const token = loginRes.data.token;
  console.log(`[AUTH] Logged in: ${loginRes.data.user.email}`);

  // 2. Query Startup Config to check modelSpecs
  const cfg = await request('http://localhost:3080/api/config', {
    headers: { Authorization: `Bearer ${token}` }
  });
  console.log('[CONFIG MODEL SPECS]:', JSON.stringify(cfg.data.modelSpecs, null, 2));
  console.log('[CONFIG ENDPOINTS]:', JSON.stringify(cfg.data.endpoints, null, 2));

  // 3. Send chat message through LibreChat Ask / Chat Endpoint
  const askRes = await new Promise((resolve, reject) => {
    const askBody = JSON.stringify({
      endpoint: 'Educore Enterprise AI',
      model: 'educore-rag-control',
      spec: 'educore-governed-core',
      text: 'What are the main principles of the Educore AI framework?',
      conversationId: null,
      parentMessageId: '00000000-0000-0000-0000-000000000000',
    });
    const req = http.request('http://localhost:3080/api/ask/custom', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'Content-Length': Buffer.byteLength(askBody)
      }
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve({ status: res.statusCode, body: data }));
    });
    req.on('error', reject);
    req.write(askBody);
    req.end();
  });

  console.log(`[CHAT ASK STATUS]: ${askRes.status}`);
  console.log(`[CHAT ASK RESPONSE PREVIEW]: ${askRes.body.slice(0, 300)}`);
}

run().catch(console.error);
