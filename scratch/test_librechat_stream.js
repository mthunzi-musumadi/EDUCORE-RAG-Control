const http = require('http');

async function main() {
  // 1. Login
  const loginBody = JSON.stringify({ email: 'admin@localhost.com', password: 'Password123!' });
  const loginRes = await new Promise((resolve, reject) => {
    const req = http.request('http://localhost:3080/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(loginBody),
        'Origin': 'http://localhost:3080',
        'Referer': 'http://localhost:3080/login'
      }
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve({ status: res.statusCode, body: JSON.parse(data) }));
    });
    req.on('error', reject);
    req.write(loginBody);
    req.end();
  });

  const token = loginRes.body.token;
  console.log('Logged in as:', loginRes.body.user.email);

  // 2. Send Chat Request (Step 1 of Generation Protocol)
  const chatPayload = {
    text: 'What are the admission rules for Solwezi campus?',
    sender: 'User',
    isTemporary: false,
    endpoint: 'Educore Enterprise RAG',
    endpointType: 'custom',
    model: 'educore-enterprise-all',
    conversationId: 'new',
    parentMessageId: '00000000-0000-0000-0000-000000000000',
    messageId: '11111111-1111-1111-1111-111111111111',
  };

  const chatBody = JSON.stringify(chatPayload);

  const step1 = await new Promise((resolve, reject) => {
    const req = http.request('http://localhost:3080/api/agents/chat/Educore%20Enterprise%20RAG', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(chatBody),
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json, text/event-stream',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      }
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve({ raw: data });
        }
      });
    });
    req.on('error', reject);
    req.write(chatBody);
    req.end();
  });

  const streamId = step1.streamId;
  console.log('Got streamId:', streamId);

  // 3. Connect to Stream (Step 2 of Generation Protocol)
  const streamStartTime = Date.now();
  let firstTokenTime = null;
  let tokenCount = 0;

  console.log('Streaming response tokens:');
  console.log('----------------------------------------------------');

  await new Promise((resolve, reject) => {
    const req = http.request(`http://localhost:3080/api/agents/chat/stream/${streamId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'text/event-stream',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      }
    }, (res) => {
      let buffer = '';
      res.on('data', (chunk) => {
        buffer += chunk.toString();
        const lines = buffer.split('\n\n');
        buffer = lines.pop(); // keep last incomplete block

        for (const block of lines) {
          if (!block.trim()) continue;
          const match = block.match(/data: (.*)/s);
          if (!match) continue;
          try {
            const data = JSON.parse(match[1]);
            if (data.event === 'on_message_delta') {
              const delta = data.data.delta;
              if (delta && delta.content && delta.content[0] && delta.content[0].text) {
                if (!firstTokenTime) {
                  firstTokenTime = Date.now();
                  process.stderr.write(`\n[First token received at +${firstTokenTime - streamStartTime}ms]\n`);
                }
                process.stdout.write(delta.content[0].text);
                tokenCount++;
              }
            } else if (data.event === 'title') {
              process.stderr.write(`\n[Title generated at +${Date.now() - streamStartTime}ms: "${data.data?.title?.slice(0, 40)}..."]\n`);
            } else if (data.final) {
              process.stderr.write(`\n[Stream final event received at +${Date.now() - streamStartTime}ms]\n`);
            }
          } catch (e) {}
        }
      });
      res.on('end', () => {
        const totalTime = Date.now() - streamStartTime;
        console.log('\n----------------------------------------------------');
        console.log(`Stream complete. Tokens: ${tokenCount}, Total time: ${totalTime}ms`);
        resolve();
      });
    });
    req.on('error', reject);
    req.end();
  });
}

main().catch(console.error);
