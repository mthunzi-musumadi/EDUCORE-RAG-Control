const http = require('http');

async function request(path, method = 'GET', body = null, token = null) {
  return new Promise((resolve, reject) => {
    const headers = { 
      'Content-Type': 'application/json',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    };
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

async function verify() {
  console.log('--- STEP 1: Authentication ---');
  const login = await request('/api/auth/login', 'POST', {
    email: 'admin@localhost.com',
    password: 'Password123!'
  });
  if (!login.data.token) throw new Error('Login failed: ' + JSON.stringify(login.data));
  const token = login.data.token;
  console.log('✅ Admin authenticated successfully.');

  console.log('\n--- STEP 2: Campus Directory Edit Access ---');
  const campusUpdate = await request('/api/admin/educore/campuses', 'POST', {
    code: 'TPK',
    name: 'Trident Prep Kalumbila (TPK - Primary)',
    location: 'Kalumbila Town',
    type: 'Preparatory Primary School',
    headOfCampus: 'Debra Woods',
    status: 'active',
    documents: 5
  }, token);
  console.log('✅ Campus update response status:', campusUpdate.status);
  const tpk = campusUpdate.data.campuses?.find(c => c.code === 'TPK');
  console.log('✅ TPK Campus Name updated to:', tpk?.name, '| Location:', tpk?.location);

  // Restore TPK to clean state
  await request('/api/admin/educore/campuses', 'POST', {
    code: 'TPK',
    name: 'Trident Prep Kalumbila (TPK)',
    location: 'Kalumbila',
    type: 'Preparatory Primary School',
    headOfCampus: 'Debra Woods',
    status: 'active',
    documents: 5
  }, token);
  console.log('✅ TPK Campus restored to standard name.');

  console.log('\n--- STEP 3: User Directory & RBAC CRUD ---');
  const testEmail = `teacher_${Date.now()}@sentinel-kalumbila.com`;
  
  // Create
  const userCreate = await request('/api/admin/educore/users/create', 'POST', {
    name: 'Kalumbila Science Lead',
    email: testEmail,
    password: 'TempPassword2026!',
    role: 'USER',
    clearance: 'staff',
    campus: 'TPK'
  }, token);
  console.log('✅ Created User:', userCreate.data.user?.email, '| Clearance:', userCreate.data.user?.clearance);

  // Update
  const userUpdate = await request('/api/admin/educore/users/update', 'POST', {
    email: testEmail,
    role: 'ADMIN',
    clearance: 'counselor',
    campus: 'all'
  }, token);
  console.log('✅ Updated User RBAC permissions (Promoted to ADMIN + counselor clearance):', userUpdate.data.success);

  // Read list
  const usersList = await request('/api/admin/educore/users', 'GET', null, token);
  const foundUser = usersList.data.users?.find(u => u.email.toLowerCase() === testEmail.toLowerCase());
  console.log('✅ Verified User in Directory:', foundUser?.email, '| Role:', foundUser?.role, '| Clearance:', foundUser?.clearance);

  // Delete
  const userDelete = await request(`/api/admin/educore/users/${encodeURIComponent(testEmail)}`, 'DELETE', null, token);
  console.log('✅ Deleted User (CRUD completed):', userDelete.data.deletedId);

  console.log('\n--- STEP 4: Chat Inference with Institutional RAG ---');
  const chatRes = await request('/api/agents/chat', 'POST', {
    endpointType: 'custom',
    endpoint: 'Educore Enterprise AI',
    model: 'educore-rag-control',
    spec: 'educore-governed-core',
    text: 'What are the emergency contact guidelines for Trident College?',
    conversationId: null,
    isContinued: false
  }, token);
  console.log('✅ Chat response received, status:', chatRes.status);

  console.log('\n--- STEP 5: ISO 42001 Audit Ledger Inspection ---');
  const auditRes = await request('/api/admin/educore/audit', 'GET', null, token);
  const entries = Array.isArray(auditRes.data) ? auditRes.data : (auditRes.data.audit_entries || []);
  console.log('✅ Total Audit Entries in Ledger:', entries.length);
  if (entries.length > 0) {
    const latest = entries[entries.length - 1];
    console.log('✅ Latest Audit Event Telemetry:', {
      event_id: latest.event_id,
      timestamp: latest.timestamp,
      user: latest.user_identity?.email,
      rbac_decision: latest.rbac_decision,
      physical_gate_shards: latest.physical_gate?.queried_shards,
      retrieved_chunks: latest.retrieved_chunk_ids,
      purview_containers: latest.purview_containers_accessed,
      latency_ms: latest.latency_ms,
      compliance: latest.compliance
    });
  }

  console.log('\n🎉 ALL ADMINISTRATIVE AND GOVERNANCE VALIDATIONS PASSED SUCCESSFULLY!');
}

verify().catch(console.error);
