const http = require('http');

function post(url, data) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const postData = JSON.stringify(data);
    const req = http.request({
      hostname: u.hostname,
      port: u.port,
      path: u.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    }, (res) => {
      console.log(`Status: ${res.statusCode}`);
      console.log('Headers:', res.headers);
      let body = '';
      res.on('data', chunk => {
        console.log(`Chunk received: ${chunk.length} bytes`);
        body += chunk;
      });
      res.on('end', () => {
        console.log('Response ended');
        try {
          resolve({ status: res.statusCode, data: JSON.parse(body) });
        } catch {
          resolve({ status: res.statusCode, body });
        }
      });
    });

    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

async function run() {
  console.log('--- Testing SignIn on port 3000 ---');
  const t0 = Date.now();
  const signin = await post('http://localhost:3000/api/v1/auths/signin', {
    email: 'admin@localhost',
    password: 'admin123'
  });
  console.log('SignIn result in', Date.now() - t0, 'ms:', signin);

  console.log('\n--- Testing SignUp on port 3000 ---');
  const t1 = Date.now();
  const signup = await post('http://localhost:3000/api/v1/auths/signup', {
    name: 'Test Student',
    email: `student_${Date.now()}@educore.ac.zm`,
    password: 'password123',
    campus: 'all'
  });
  console.log('SignUp result in', Date.now() - t1, 'ms:', signup);
}

run().catch(console.error);
