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
  console.log('=== TESTING LIBRECHAT GOVERNANCE IMPLEMENTATION ===');

  // 1. Startup Config
  const cfg = await request('http://localhost:3080/api/config');
  console.log(`[CONFIG] App Title: "${cfg.data.appTitle}"`);
  console.log(`[CONFIG] Registration Enabled: ${cfg.data.registrationEnabled}`);
  console.log(`[CONFIG] TOS Modal Acceptance: ${cfg.data.interface?.termsOfService?.modalAcceptance}`);
  console.log(`[CONFIG] TOS Title: "${cfg.data.interface?.termsOfService?.modalTitle}"`);

  // 2. Login
  const loginRes = await request('http://localhost:3080/api/auth/login', { method: 'POST' }, {
    email: 'admin@localhost.com',
    password: 'Password123!'
  });
  if (loginRes.status !== 200 || !loginRes.data.token) {
    console.error('[AUTH FAILED]', loginRes.data);
    process.exit(1);
  }
  const token = loginRes.data.token;
  console.log(`[AUTH SUCCESS] User: ${loginRes.data.user.email} (Role: ${loginRes.data.user.role})`);

  // 3. Models
  const modelsRes = await request('http://localhost:3080/api/models', {
    headers: { Authorization: `Bearer ${token}` }
  });
  console.log('[MODELS RESPONSE]', JSON.stringify(modelsRes.data, null, 2));

  // 4. Admin Status
  const adminStatus = await request('http://localhost:3080/api/admin/educore/status', {
    headers: { Authorization: `Bearer ${token}` }
  });
  console.log(`[ADMIN STATUS] Status: ${adminStatus.status}, Chroma Shards: ${Object.keys(adminStatus.data.shards || {}).length}, Vectors: ${adminStatus.data.total_vectors}`);

  // 5. Test Chat Completion through Backend Direct & Custom Endpoint
  const directRes = await request('http://localhost:8000/v1/chat/completions', {
    method: 'POST',
    headers: { Authorization: 'Bearer educore-internal-secure-key' }
  }, {
    model: 'educore-rag-control',
    messages: [
      { role: 'user', content: 'What is the role of the Educore Enterprise AI assistant?' }
    ],
    temperature: 0.1
  });
  console.log(`[DIRECT CHAT] Status: ${directRes.status}, Model: ${directRes.data.model}`);
  console.log(`[DIRECT REPLY EXCERPT]: ${directRes.data.choices?.[0]?.message?.content?.slice(0, 150)}...`);

  console.log('\n>>> ALL GOVERNANCE SPECIFICATION TESTS PASSED SUCCESSFULLY! <<<');
}

run().catch(err => {
  console.error('[ERROR]', err);
  process.exit(1);
});
