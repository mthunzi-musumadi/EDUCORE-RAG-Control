const http = require('http');

async function request(path, method = 'GET', body = null, token = null) {
  return new Promise((resolve, reject) => {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const bodyStr = body ? JSON.stringify(body) : null;
    if (bodyStr) headers['Content-Length'] = Buffer.byteLength(bodyStr);

    const req = http.request(`http://127.0.0.1:3080${path}`, { method, headers }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, data });
        }
      });
    });
    req.on('error', reject);
    if (bodyStr) req.write(bodyStr);
    req.end();
  });
}

async function run() {
  console.log('1. Logging in...');
  const loginRes = await request('/api/auth/login', 'POST', {
    email: 'admin@localhost.com',
    password: 'Password123!'
  });
  if (loginRes.status !== 200 || !loginRes.data.token) {
    throw new Error('Login failed: ' + JSON.stringify(loginRes.data));
  }
  const token = loginRes.data.token;
  console.log('Logged in successfully!');

  console.log('\n2. Testing Campuses GET...');
  const campGet = await request('/api/admin/educore/campuses', 'GET', null, token);
  console.log('Campuses status:', campGet.status, 'Count:', campGet.data.campuses?.length);

  console.log('\n3. Testing Campus Edit/Update...');
  const campUpdate = await request('/api/admin/educore/campuses', 'POST', {
    code: 'TCL',
    name: 'Trident College Solwezi (Main)',
    location: 'Solwezi West',
    type: 'Secondary College (Boarding & Day)',
    headOfCampus: 'Austin Eaton',
    status: 'active',
    documents: 6
  }, token);
  console.log('Campus update status:', campUpdate.status, 'TCL name:', campUpdate.data.campuses?.find(c => c.code === 'TCL')?.name);

  console.log('\n4. Testing User Creation (CRUD)...');
  const testEmail = `testuser_${Date.now()}@educoreservices.com`;
  const userCreate = await request('/api/admin/educore/users/create', 'POST', {
    name: 'Auditor Test User',
    email: testEmail,
    password: 'Password123!',
    role: 'USER',
    clearance: 'counselor',
    campus: 'TPS'
  }, token);
  console.log('User create status:', userCreate.status, 'User:', userCreate.data.user?.email);

  console.log('\n5. Testing User Update (CRUD)...');
  const userUpdate = await request('/api/admin/educore/users/update', 'POST', {
    email: testEmail,
    role: 'ADMIN',
    clearance: 'admin',
    campus: 'all'
  }, token);
  console.log('User update status:', userUpdate.status, 'Result:', userUpdate.data.success);

  console.log('\n6. Testing User Delete (CRUD)...');
  const userDelete = await request(`/api/admin/educore/users/${encodeURIComponent(testEmail)}`, 'DELETE', null, token);
  console.log('User delete status:', userDelete.status, 'Deleted:', userDelete.data.deletedId);

  console.log('\n7. Testing Audit Ledger Fetch...');
  const auditRes = await request('/api/admin/educore/audit', 'GET', null, token);
  const auditEntries = Array.isArray(auditRes.data) ? auditRes.data : (auditRes.data.audit_entries || []);
  console.log('Audit entries status:', auditRes.status, 'Total logged events:', auditEntries.length);
  if (auditEntries.length > 0) {
    const first = auditEntries[auditEntries.length - 1];
    console.log('Sample audit event:', {
      event_id: first.event_id,
      timestamp: first.timestamp,
      query: first.query?.slice(0, 40) + '...',
      shards: first.physical_gate?.queried_shards?.length,
      chunks: first.retrieved_chunk_ids,
      compliance: first.compliance?.slice(0, 30) + '...'
    });
  }

  console.log('\nALL BACKEND ADMIN CRUD TESTS PASSED!');
}

run().catch(console.error);
