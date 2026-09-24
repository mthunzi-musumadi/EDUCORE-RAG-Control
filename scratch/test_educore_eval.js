const http = require('http');

async function main() {
  const loginBody = JSON.stringify({ email: 'admin@localhost.com', password: 'Password123!' });
  const loginRes = await new Promise((resolve, reject) => {
    const req = http.request('http://localhost:3080/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(loginBody) }
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve(JSON.parse(data)));
    });
    req.on('error', reject);
    req.write(loginBody);
    req.end();
  });

  const token = loginRes.token;
  console.log('[AUTH] Running Model Evaluation Arena test...');

  const evalBody = JSON.stringify({
    prompt: 'What are the staff leave guidelines?',
    modelA: 'educore-enterprise-all',
    modelB: 'educore-enterprise-all',
    clearance: 'staff',
    campus: 'solwezi'
  });

  const evalRes = await new Promise((resolve, reject) => {
    const req = http.request('http://localhost:3080/api/admin/educore/eval', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(evalBody)
      }
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve({ status: res.statusCode, body: JSON.parse(data) }));
    });
    req.on('error', reject);
    req.write(evalBody);
    req.end();
  });

  console.log(`[EVAL STATUS]: ${evalRes.status}`);
  console.log('Model A:', evalRes.body.evalA?.modelId, 'Latency:', evalRes.body.evalA?.latencyMs, 'ms, Tokens:', evalRes.body.evalA?.tokens);
  console.log('Comparison:', evalRes.body.comparison);
}

main().catch(console.error);
