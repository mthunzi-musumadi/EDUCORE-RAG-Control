const mongoose = require('mongoose');

async function run() {
  await mongoose.connect('mongodb://127.0.0.1:27017/LibreChat');
  const res = await mongoose.connection.db.collection('users').updateOne(
    { email: 'student@sentinel-kabitaka.com' },
    { $set: { role: 'ADMIN' } }
  );
  console.log('Update result:', res);
  const updated = await mongoose.connection.db.collection('users').find({}).toArray();
  console.log('Updated users:', updated.map(u => ({ email: u.email, name: u.name, role: u.role })));
  await mongoose.disconnect();
}

run().catch(console.error);
