const { MongoMemoryServer } = require('mongodb-memory-server');
const fs = require('fs');
const path = require('path');

async function main() {
  const dataDir = path.join(__dirname, 'data');
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }

  console.log("Initializing MongoDB runner...");
  const mongod = await MongoMemoryServer.create({
    instance: {
      port: 27017,
      dbPath: dataDir,
    }
  });
  console.log("MongoDB is LIVE at:", mongod.getUri());
  console.log("Port:", mongod.instanceInfo.port);
  await mongod.stop();
  console.log("MongoDB stopped cleanly.");
}

main().catch(err => {
  console.error("MongoDB start error:", err);
  process.exit(1);
});
