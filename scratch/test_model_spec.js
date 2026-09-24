const { loadCustomEndpointsConfig } = require('../prototypes/librechat/packages/api/dist/index.cjs');
const endpoints = loadCustomEndpointsConfig([{ 
  name: 'Educore Enterprise AI', 
  apiKey: 'test', 
  baseURL: 'http://127.0.0.1:8000/v1', 
  models: { default: ['test'] } 
}]);
console.log('Custom endpoints keys:', Object.keys(endpoints || {}));
