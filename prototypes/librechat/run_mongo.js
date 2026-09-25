const { MongoMemoryServer } = require('../../scratch/mongo-test/node_modules/mongodb-memory-server');
const path = require('path');
const fs = require('fs');

async function startMongo() {
  const dbDir = path.join(__dirname, 'data', 'mongo');
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }

  console.log('----------------------------------------------------');
  console.log(' Starting Standalone MongoDB on Port 27017...');
  console.log(' Data Directory:', dbDir);
  console.log('----------------------------------------------------');

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
}

startMongo().catch((err) => {
  console.error('Failed to start MongoDB:', err);
  process.exit(1);
});
