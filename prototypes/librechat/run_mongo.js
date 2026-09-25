const net = require('net');
const path = require('path');
const fs = require('fs');

// 1. Resolve mongodb-memory-server across monorepo package structures
let MongoMemoryServer;
const searchPaths = [
  'mongodb-memory-server',
  path.join(__dirname, 'node_modules', 'mongodb-memory-server'),
  path.join(__dirname, 'api', 'node_modules', 'mongodb-memory-server'),
  path.join(__dirname, '..', '..', 'node_modules', 'mongodb-memory-server')
];

for (const p of searchPaths) {
  try {
    const mod = require(p);
    MongoMemoryServer = mod.MongoMemoryServer;
    if (MongoMemoryServer) break;
  } catch (e) {
    // continue searching
  }
}

if (!MongoMemoryServer) {
  console.error('====================================================');
  console.error(' Error: "mongodb-memory-server" package not found.');
  console.error(' Please run "npm install" inside prototypes/librechat');
  console.error('====================================================');
  process.exit(1);
}

// 2. Check if a MongoDB instance is already listening on port 27017
function isPortActive(port, host = '127.0.0.1') {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(1000);
    socket.once('connect', () => {
      socket.destroy();
      resolve(true);
    });
    socket.once('timeout', () => {
      socket.destroy();
      resolve(false);
    });
    socket.once('error', () => {
      socket.destroy();
      resolve(false);
    });
    socket.connect(port, host);
  });
}

async function startMongo() {
  const isRunning = await isPortActive(27017);
  if (isRunning) {
    console.log('====================================================');
    console.log('✓ MongoDB is ALREADY ACTIVE on port 27017.');
    console.log('  Using existing MongoDB instance.');
    console.log('====================================================');
    return;
  }

  const dbDir = path.join(__dirname, 'data', 'mongo');
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }

  // Clear stale lock file if mongod is not actually running
  const lockFile = path.join(dbDir, 'mongod.lock');
  if (fs.existsSync(lockFile)) {
    try {
      fs.unlinkSync(lockFile);
    } catch (e) {
      // ignore if locked
    }
  }

  console.log('====================================================');
  console.log(' Starting Standalone MongoDB on Port 27017...');
  console.log(' Data Directory:', dbDir);
  console.log('====================================================');

  const mongod = await MongoMemoryServer.create({
    instance: {
      port: 27017,
      dbPath: dbDir,
    }
  });

  console.log('✓ MongoDB is RUNNING at:', mongod.getUri());
  console.log('Press Ctrl+C to stop.');

  process.on('SIGINT', async () => {
    console.log('\nStopping MongoDB server...');
    await mongod.stop();
    console.log('MongoDB server stopped.');
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    await mongod.stop();
    process.exit(0);
  });

  // Keep process running
  await new Promise(() => {});
}

startMongo().catch((err) => {
  console.error('Failed to start MongoDB:', err);
  process.exit(1);
});
