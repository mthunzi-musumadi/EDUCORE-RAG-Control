const http = require('http');

async function run() {
  console.log('=== TESTING POST /api/agents/chat ===');

  // 1. Login
  const loginBody = JSON.stringify({ email: 'admin@localhost.com', password: 'Password123!' });
  const token = await new Promise((resolve, reject) => {
    const req = http.request('http://localhost:3080/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(loginBody)
      }
    }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve(JSON.parse(data).token));
    });
    req.on('error', reject);
    req.write(loginBody);
    req.end();
  });

  console.log('Logged in successfully.');

  const chatBody = JSON.stringify({
    endpoint: 'Educore Enterprise AI',
    endpointType: 'custom',
    spec: 'educore-governed-core',
    model: 'educore-rag-control',
    text: 'Hello Educore, please explain your role.',
    conversationId: '00000000-0000-0000-0000-000000000001',
    parentMessageId: '00000000-0000-0000-0000-000000000000',
  });

  const chatRes = await new Promise((resolve, reject) => {
    const req = http.request('http://localhost:3080/api/agents/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Length': Buffer.byteLength(chatBody)
      }
    }, res => {
      let data = '';
      res.on('data', c => {
        data += c;
        // Print first chunk
        if (data.length < 500) {
          console.log('[STREAM CHUNK]:', c.toString());
        }
      });
      res.on('end', () => resolve({ status: res.statusCode, body: data }));
    });
    req.on('error', reject);
    req.write(chatBody);
    req.end();
  });

  console.log(`[STATUS]: ${chatRes.status}`);
  console.log(`[BODY PREVIEW]: ${chatRes.body.slice(0, 300)}`);
}

run().catch(console.error);
