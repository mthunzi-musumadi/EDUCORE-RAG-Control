const http = require('http');

async function run() {
  // Login
  const loginData = JSON.stringify({ email: 'admin@localhost.com', password: 'Password123!' });
  const token = await new Promise((resolve, reject) => {
    const req = http.request('http://localhost:3080/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(loginData) }
    }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve(JSON.parse(data).token));
    });
    req.write(loginData);
    req.end();
  });

  // Query /api/endpoints
  const endpointsRes = await new Promise((resolve, reject) => {
    const req = http.request('http://localhost:3080/api/endpoints', {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` }
    }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve(JSON.parse(data)));
    });
    req.end();
  });

  console.log('GET /api/endpoints response:');
  console.log(JSON.stringify(endpointsRes, null, 2));
}

run().catch(console.error);
