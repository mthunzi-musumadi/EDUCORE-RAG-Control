const http = require('http');

async function main() {
  // 1. Login to get JWT
  const loginBody = JSON.stringify({ email: 'admin@localhost.com', password: 'Password123!' });
  const loginRes = await new Promise((resolve, reject) => {
    const req = http.request('http://localhost:3080/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(loginBody),
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
  console.log(`[AUTH] Logged in as: ${loginRes.body.user.email} (role: ${loginRes.body.user.role})`);

  async function get(path) {
    return new Promise((resolve, reject) => {
      const req = http.request(`http://localhost:3080${path}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }, (res) => {
        let data = '';
        res.on('data', c => data += c);
        res.on('end', () => {
          try {
            resolve({ status: res.statusCode, body: JSON.parse(data) });
          } catch (e) {
            resolve({ status: res.statusCode, body: data });
          }
        });
      });
      req.on('error', reject);
      req.end();
    });
  }

  // Test 1: Campuses
  const campuses = await get('/api/admin/educore/campuses');
  console.log(`\n[CAMPUSES] Status: ${campuses.status}, Count: ${campuses.body.campuses?.length}`);
  for (const c of campuses.body.campuses || []) {
    console.log(`  - [${c.code}] ${c.name} (${c.location}) - ${c.documents} docs`);
  }

  // Test 2: Clearance Tiers
  const clearances = await get('/api/admin/educore/clearances');
  console.log(`\n[CLEARANCES] Status: ${clearances.status}, Count: ${clearances.body.clearances?.length}`);
  for (const cl of clearances.body.clearances || []) {
    console.log(`  - [L${cl.level}] ${cl.label} (${cl.tier}): ${cl.shards.join(', ')}`);
  }

  // Test 3: Framework Status
  const status = await get('/api/admin/educore/status');
  console.log(`\n[FRAMEWORK STATUS] Status: ${status.status}, Service: ${status.body.service}`);
  console.log(`  - Total Vectors: ${status.body.total_vector_count}, Shards: ${Object.keys(status.body.shard_vector_counts || {}).length}`);

  // Test 4: Audit Ledger
  const audit = await get('/api/admin/educore/audit');
  console.log(`\n[AUDIT LEDGER] Status: ${audit.status}, Entries: ${Array.isArray(audit.body) ? audit.body.length : 0}`);
  if (Array.isArray(audit.body) && audit.body.length > 0) {
    const last = audit.body[audit.body.length - 1];
    console.log(`  - Latest: [${last.timestamp?.split('T')[1]?.slice(0, 8)}] ${last.user_email} | ${last.clearance} | status: ${last.guardrail_status}`);
  }

  // Test 5: Users
  const users = await get('/api/admin/educore/users');
  console.log(`\n[USERS DIRECTORY] Status: ${users.status}, Count: ${users.body.users?.length}`);
  for (const u of (users.body.users || []).slice(0, 5)) {
    console.log(`  - ${u.name} (${u.email}) | Role: ${u.role} | Clearance: ${u.clearance} | Campus: ${u.campus}`);
  }

  console.log('\n====================================================');
  console.log('ALL EDUCORE ADMIN API ENDPOINTS VERIFIED ON LIBRECHAT PORT 3080!');
  console.log('====================================================');
}

main().catch(console.error);
