const express = require('express');
const http = require('http');
const fs = require('fs');
const path = require('path');
const bcrypt = require('bcryptjs');
const { requireJwtAuth } = require('~/server/middleware');
const db = require('~/models');

const router = express.Router();
const EDUCORE_BASE = 'http://127.0.0.1:8000';

function educoreRequest(method, reqPath, body = null, headers = {}) {
  return new Promise((resolve) => {
    const url = new URL(reqPath, EDUCORE_BASE);
    const reqHeaders = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer educore-enterprise-token',
      ...headers,
    };
    const bodyStr = body ? JSON.stringify(body) : null;
    if (bodyStr) {
      reqHeaders['Content-Length'] = Buffer.byteLength(bodyStr);
    }
    const req = http.request(url, { method, headers: reqHeaders }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch (e) {
          resolve({ status: res.statusCode, data });
        }
      });
    });
    req.on('error', (err) => {
      resolve({ status: 503, data: { error: `Educore Backend unreachable: ${err.message}` } });
    });
    if (bodyStr) req.write(bodyStr);
    req.end();
  });
}

// -----------------------------------------------------------------------------
// Campus Directory Persistence
// -----------------------------------------------------------------------------
function getCampusFilePath() {
  const possiblePaths = [
    path.resolve(__dirname, '../../../../../../data/campus_directory.json'),
    path.resolve(__dirname, '../../../../../data/campus_directory.json'),
    path.resolve(process.cwd(), '../../data/campus_directory.json'),
    path.resolve(process.cwd(), 'data/campus_directory.json'),
  ];
  for (const p of possiblePaths) {
    if (fs.existsSync(p)) return p;
  }
  return path.resolve(__dirname, '../../../../../../data/campus_directory.json');
}

function readCampuses() {
  try {
    const p = getCampusFilePath();
    if (fs.existsSync(p)) {
      const data = fs.readFileSync(p, 'utf-8');
      return JSON.parse(data);
    }
  } catch (err) {
    console.error('[Educore Admin] Error reading campus directory:', err);
  }
  return [
    { code: 'TCL', name: 'Trident College (TCL)', cluster: 'trident', location: 'Solwezi', type: 'Secondary College (Boarding & Day)', documents: 6, headOfCampus: 'Austin Eaton', status: 'active' },
    { code: 'TPS', name: 'Trident Prep Solwezi (TPS)', cluster: 'trident', location: 'Solwezi', type: 'Preparatory Primary School', documents: 5, headOfCampus: 'Kirsten Eaton', status: 'active' },
    { code: 'TPK', name: 'Trident Prep Kalumbila (TPK)', cluster: 'trident', location: 'Kalumbila', type: 'Preparatory Primary School', documents: 5, headOfCampus: 'Debra Woods', status: 'active' },
    { code: 'TPL', name: 'Trident Prep Lusaka (TPL)', cluster: 'trident', location: 'Lusaka', type: 'Preparatory Primary School', documents: 5, headOfCampus: 'Gemma Thomson', status: 'active' },
    { code: 'all', name: 'All Campuses (Universal Purview)', cluster: 'institutional', location: 'Zambia Multi-Site', type: 'Institutional Gateway', documents: 21, headOfCampus: 'Executive Directorate', status: 'active' }
  ];
}

function saveCampuses(campuses) {
  const p = getCampusFilePath();
  const dir = path.dirname(p);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  fs.writeFileSync(p, JSON.stringify(campuses, null, 2), 'utf-8');
}

// 1. Framework & Knowledge Status
router.get('/status', requireJwtAuth, async (req, res) => {
  const result = await educoreRequest('GET', '/api/framework/status');
  res.status(result.status).json(result.data);
});

// 2. Trigger Corpus Sync
router.post('/sync', requireJwtAuth, async (req, res) => {
  const result = await educoreRequest('POST', '/api/framework/sync', req.body);
  res.status(result.status).json(result.data);
});

// 3. ISO 42001 Audit Ledger
router.get('/audit', requireJwtAuth, async (req, res) => {
  const result = await educoreRequest('GET', '/api/audit');
  res.status(result.status).json(result.data);
});

// 4. Official Campus Registry (CRUD)
router.get('/campuses', requireJwtAuth, async (req, res) => {
  const campuses = readCampuses();
  res.json({ success: true, campuses });
});

router.post(['/campuses', '/campuses/update'], requireJwtAuth, async (req, res) => {
  try {
    const campus = req.body;
    if (!campus.code || !campus.name) {
      return res.status(400).json({ error: 'Campus code and name are required' });
    }
    const campuses = readCampuses();
    const idx = campuses.findIndex(c => c.code.toLowerCase() === campus.code.toLowerCase());
    if (idx >= 0) {
      campuses[idx] = {
        ...campuses[idx],
        name: campus.name,
        location: campus.location ?? campuses[idx].location,
        type: campus.type ?? campuses[idx].type,
        headOfCampus: campus.headOfCampus ?? campuses[idx].headOfCampus,
        status: campus.status ?? campuses[idx].status ?? 'active',
        documents: campus.documents !== undefined ? Number(campus.documents) : campuses[idx].documents,
      };
    } else {
      campuses.push({
        code: campus.code.toUpperCase(),
        name: campus.name,
        cluster: campus.cluster || 'trident',
        location: campus.location || 'Zambia',
        type: campus.type || 'Campus',
        documents: Number(campus.documents) || 0,
        headOfCampus: campus.headOfCampus || '',
        status: campus.status || 'active',
      });
    }
    saveCampuses(campuses);
    res.json({ success: true, campuses });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.delete('/campuses/:code', requireJwtAuth, async (req, res) => {
  try {
    const { code } = req.params;
    let campuses = readCampuses();
    campuses = campuses.filter(c => c.code.toLowerCase() !== code.toLowerCase());
    saveCampuses(campuses);
    res.json({ success: true, campuses });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 5. Clearance Tiers Matrix (ISO 42001 RBAC)
router.get('/clearances', requireJwtAuth, async (req, res) => {
  const clearances = [
    { tier: 'public', label: 'Public', level: 1, shards: ['public'], description: 'General prospective students, public handbook, open policies' },
    { tier: 'staff', label: 'Staff / Faculty', level: 2, shards: ['public', 'staff'], description: 'Academic staff, curriculum guidelines, HR leave policies' },
    { tier: 'counselor', label: 'Counselor', level: 3, shards: ['public', 'staff', 'counselor'], description: 'Student welfare, pastoral care, medical and counseling procedures' },
    { tier: 'finance', label: 'Finance / Bursar', level: 4, shards: ['public', 'staff', 'finance'], description: 'Tuition structures, fee schedules, payroll, scholarship allocations' },
    { tier: 'devops', label: 'DevOps / IT', level: 5, shards: ['public', 'staff', 'devops'], description: 'IT acceptable use, cybersecurity, network architecture, ISO controls' },
    { tier: 'admin', label: 'Enterprise Admin', level: 6, shards: ['public', 'staff', 'counselor', 'finance', 'devops', 'admin'], description: 'Board governance, legal agreements, executive audit ledger' },
  ];
  res.json({ success: true, clearances });
});

// 6. User Directory (Merged MongoDB + Educore)
router.get('/users', requireJwtAuth, async (req, res) => {
  try {
    const mongoUsers = await db.findUsers({}, 'name email role createdAt');
    const eduResult = await educoreRequest('GET', '/api/v1/users');
    const eduUsers = Array.isArray(eduResult.data) ? eduResult.data : (eduResult.data?.users || []);

    const eduMap = new Map();
    for (const u of eduUsers) {
      if (u.email) eduMap.set(u.email.toLowerCase(), u);
    }

    const merged = mongoUsers.map((mu) => {
      const email = (mu.email || '').toLowerCase();
      const eu = eduMap.get(email) || {};
      return {
        id: mu._id?.toString() || eu.id,
        name: mu.name || eu.name || 'User',
        email: mu.email || eu.email,
        role: mu.role || eu.role || 'USER',
        clearance: eu.clearance || (mu.role === 'ADMIN' ? 'admin' : 'staff'),
        campus: eu.campus || 'all',
        groups: eu.groups || [],
        createdAt: mu.createdAt,
      };
    });

    // Also include any Educore users not in Mongo
    for (const eu of eduUsers) {
      if (eu.email && !merged.some(m => m.email?.toLowerCase() === eu.email.toLowerCase())) {
        merged.push({
          id: eu.id,
          name: eu.name || 'User',
          email: eu.email,
          role: (eu.role || 'USER').toUpperCase(),
          clearance: eu.clearance || 'staff',
          campus: eu.campus || 'all',
          groups: eu.groups || [],
          createdAt: eu.created_at ? new Date(eu.created_at * 1000).toISOString() : new Date().toISOString(),
        });
      }
    }

    res.json({ success: true, users: merged });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 7. Create User (CRUD)
router.post('/users/create', requireJwtAuth, async (req, res) => {
  try {
    const { name, email, password, role = 'USER', clearance = 'staff', campus = 'all' } = req.body;
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    const salt = bcrypt.genSaltSync(10);
    const hashedPassword = bcrypt.hashSync(password, salt);
    const username = email.split('@')[0];

    // 1. Create or update in Mongo
    let mongoUser = null;
    try {
      mongoUser = await db.findUser({ email });
      if (!mongoUser && db.createUser) {
        mongoUser = await db.createUser({
          provider: 'local',
          email,
          username,
          name: name || username,
          avatar: null,
          role: role.toUpperCase(),
          password: hashedPassword,
          emailVerified: true,
        }, undefined, true, true);
      } else if (mongoUser && db.updateUser) {
        await db.updateUser({ email }, {
          name: name || mongoUser.name,
          role: role.toUpperCase(),
          emailVerified: true,
        });
      }
    } catch (e) {
      console.warn('[Educore Admin] Mongo user creation error:', e.message);
    }

    // 2. Create in Educore Backend
    const eduRes = await educoreRequest('POST', '/api/v1/users/user/create', {
      id: mongoUser?._id?.toString() || email,
      name: name || username,
      email,
      role: role.toLowerCase(),
      clearance,
      campus,
    });

    res.json({
      success: true,
      user: {
        id: mongoUser?._id?.toString() || email,
        name: name || username,
        email,
        role: role.toUpperCase(),
        clearance,
        campus,
      },
      educore: eduRes.data,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 8. Update User Clearance / Role / Campus / Name (CRUD)
router.post(['/user/update', '/users/update'], requireJwtAuth, async (req, res) => {
  try {
    const { id, email, name, role, clearance, campus } = req.body;
    if (!email && !id) return res.status(400).json({ error: 'Email or ID is required' });

    // Update MongoDB user
    if (db.updateUser) {
      try {
        const query = id ? { _id: id } : { email };
        const updates = {};
        if (role) updates.role = role.toUpperCase();
        if (name) updates.name = name;
        await db.updateUser(query, updates);
      } catch (e) {
        console.warn('[Educore Admin] Mongo user update error:', e.message);
      }
    }

    // Update Educore Backend user
    const eduRes = await educoreRequest('POST', '/api/v1/users/user/update', {
      id: id || email,
      role: (role || 'user').toLowerCase(),
      clearance: clearance || 'public',
      campus: campus || 'all',
    });

    res.json({ success: true, educore: eduRes.data });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 9. Delete User (CRUD)
router.delete(['/users/:id', '/user/delete'], requireJwtAuth, async (req, res) => {
  try {
    const id = req.params.id || req.query.id || req.body?.id;
    const email = req.query.email || req.body?.email;

    if (!id && !email) {
      return res.status(400).json({ error: 'User ID or Email is required for deletion' });
    }

    // 1. Delete from MongoDB
    if (id && db.deleteUserById) {
      try {
        await db.deleteUserById(id);
      } catch (e) {
        console.warn('[Educore Admin] Mongo deleteUserById error:', e.message);
      }
    }
    if (email && db.deleteUser) {
      try {
        await db.deleteUser({ email });
      } catch (e) {
        console.warn('[Educore Admin] Mongo deleteUser error:', e.message);
      }
    }

    // 2. Delete from Educore Backend
    const targetId = email || id;
    const eduRes = await educoreRequest('POST', '/api/v1/users/user/delete', {
      id: targetId,
    });

    res.json({ success: true, deletedId: id || email, educore: eduRes.data });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 10. Models List
router.get('/models', requireJwtAuth, async (req, res) => {
  const result = await educoreRequest('GET', '/api/v1/models');
  res.status(result.status).json(result.data);
});

// 11. Model Evaluations Arena
router.post('/eval', requireJwtAuth, async (req, res) => {
  const { prompt, modelA = 'educore-enterprise-all', modelB = 'llama3.2:latest', clearance = 'staff', campus = 'solwezi' } = req.body;
  if (!prompt) return res.status(400).json({ error: 'Prompt is required for model evaluation' });

  const runModel = async (modelId) => {
    const t0 = Date.now();
    const payload = {
      model: modelId,
      messages: [{ role: 'user', content: prompt }],
      stream: false,
    };
    const headers = {
      'X-Clearance': clearance,
      'X-Campus': campus,
    };
    const res = await educoreRequest('POST', '/v1/chat/completions', payload, headers);
    const latency = Date.now() - t0;
    const choice = res.data?.choices?.[0]?.message?.content || '';
    const usage = res.data?.usage || {};
    const telemetry = res.data?.educore_telemetry || {};

    const isGuardrailBlocked = choice.includes('🛑 **Educore Framework Stop-Condition Triggered**');

    return {
      modelId,
      latencyMs: latency,
      tokens: usage.completion_tokens || 0,
      tps: telemetry.tps || (usage.completion_tokens ? Number(((usage.completion_tokens / (latency / 1000))).toFixed(1)) : 0),
      response: choice,
      isGuardrailBlocked,
      retrievedRecords: telemetry.retrieved_records?.length || 0,
    };
  };

  try {
    const [evalA, evalB] = await Promise.all([runModel(modelA), runModel(modelB)]);
    res.json({
      success: true,
      timestamp: new Date().toISOString(),
      prompt,
      evalA,
      evalB,
      comparison: {
        fasterModel: evalA.latencyMs < evalB.latencyMs ? modelA : modelB,
        latencyDiffMs: Math.abs(evalA.latencyMs - evalB.latencyMs),
        higherTpsModel: evalA.tps > evalB.tps ? modelA : modelB,
      }
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
