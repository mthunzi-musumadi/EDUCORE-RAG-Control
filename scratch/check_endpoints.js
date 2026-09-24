const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../prototypes/librechat/.env') });
const { loadCustomEndpointsConfig } = require('../prototypes/librechat/packages/api/dist/endpoints/custom/config.js');
const yaml = require('yaml');
const fs = require('fs');

const yamlContent = fs.readFileSync(path.join(__dirname, '../prototypes/librechat/librechat.yaml'), 'utf8');
const parsed = yaml.parse(yamlContent);
console.log('YAML parsed endpoints:', JSON.stringify(parsed.endpoints, null, 2));

const loaded = loadCustomEndpointsConfig(parsed.endpoints.custom);
console.log('Resolved custom endpoints config:', JSON.stringify(loaded, null, 2));
