/**
 * Educore Enterprise RAG — Automated MongoDB User Seeder
 * Ensures default Admin and institutional users exist in MongoDB.
 * Critical for fresh clones and cross-machine deployments where data/mongo is empty.
 */

const fs = require('fs');
const path = require('path');

let mongoose;
try {
  mongoose = require('mongoose');
} catch (e1) {
  try {
    mongoose = require(path.join(__dirname, 'api', 'node_modules', 'mongoose'));
  } catch (e2) {
    try {
      mongoose = require(path.join(__dirname, 'node_modules', 'mongoose'));
    } catch (e3) {
      console.warn('⚠️ Could not resolve mongoose module. Run npm install in prototypes/librechat.');
      process.exit(0);
    }
  }
}

const MONGO_URI = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/LibreChat';

async function seed() {
  console.log('----------------------------------------------------');
  console.log(' Educore User Seeder: Initializing MongoDB users...');
  console.log(' Database URI:', MONGO_URI);
  console.log('----------------------------------------------------');

  try {
    await mongoose.connect(MONGO_URI, { serverSelectionTimeoutMS: 5000 });
  } catch (err) {
    console.warn('⚠️ Could not connect to MongoDB:', err.message);
    console.warn('  Ensure MongoDB is running on port 27017 before seeding.');
    process.exit(0);
  }

  const db = mongoose.connection.db;
  const usersColl = db.collection('users');

  const defaultAdminHash = '$2a$10$ASi1b8nmPPxW4taN0YEVn.R3tFw1bTpdYDANs9WnQQNpzN/VHlbAe'; // Password123!

  // 1. Seed or update primary Admin user
  const adminEmails = ['admin@localhost.com', 'admin@localhost'];
  for (const email of adminEmails) {
    const existing = await usersColl.findOne({ email });
    if (!existing) {
      await usersColl.insertOne({
        name: 'Educore Administrator',
        username: email.split('@')[0],
        email: email,
        emailVerified: true,
        password: defaultAdminHash,
        avatar: null,
        provider: 'local',
        role: 'ADMIN',
        plugins: [],
        twoFactorEnabled: false,
        termsAccepted: true,
        termsAcceptedAt: new Date(),
        personalization: { memories: true },
        pinnedOrder: [],
        backupCodes: [],
        refreshToken: [],
        favorites: [],
        createdAt: new Date(),
        updatedAt: new Date()
      });
      console.log(`✓ Created default ADMIN user: ${email} (Password: Password123!)`);
    } else {
      // Ensure existing admin has ADMIN role
      if (existing.role !== 'ADMIN') {
        await usersColl.updateOne({ email }, { $set: { role: 'ADMIN', updatedAt: new Date() } });
        console.log(`✓ Promoted ${email} to ADMIN role.`);
      } else {
        console.log(`✓ Verified ADMIN user exists: ${email}`);
      }
    }
  }

  // 2. Import institutional users from exported_users.json if available
  const exportedPath = path.join(__dirname, 'data', 'exported_users.json');
  if (fs.existsSync(exportedPath)) {
    try {
      const exportedUsers = JSON.parse(fs.readFileSync(exportedPath, 'utf8'));
      let importedCount = 0;
      for (const u of exportedUsers) {
        if (!u.email) continue;
        const exists = await usersColl.findOne({ email: u.email });
        if (!exists) {
          await usersColl.insertOne({
            name: u.name || u.email.split('@')[0],
            username: u.username || u.email,
            email: u.email,
            emailVerified: true,
            password: u.password || defaultAdminHash,
            avatar: null,
            provider: 'local',
            role: u.role || 'USER',
            plugins: [],
            twoFactorEnabled: false,
            termsAccepted: true,
            termsAcceptedAt: new Date(),
            personalization: { memories: true },
            pinnedOrder: [],
            backupCodes: [],
            refreshToken: [],
            favorites: [],
            createdAt: new Date(),
            updatedAt: new Date()
          });
          importedCount++;
        }
      }
      if (importedCount > 0) {
        console.log(`✓ Imported ${importedCount} institutional user(s) from exported_users.json.`);
      }
    } catch (e) {
      console.warn('⚠️ Could not parse exported_users.json:', e.message);
    }
  }

  const totalUsers = await usersColl.countDocuments();
  console.log(`====================================================`);
  console.log(`✓ Seeding complete. Total registered users: ${totalUsers}`);
  console.log(`  Login with: admin@localhost.com / Password123!`);
  console.log(`====================================================`);

  await mongoose.disconnect();
  process.exit(0);
}

seed().catch((err) => {
  console.error('Failed to seed users:', err);
  process.exit(0);
});
