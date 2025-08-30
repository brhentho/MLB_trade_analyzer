/**
 * Simple test script to verify frontend-backend integration
 * Run this with: node test_integration.js
 */

const axios = require('axios');

const API_BASE_URL = 'http://localhost:8000';

// Test API endpoints
const tests = [
  {
    name: 'Health Check',
    method: 'GET',
    url: '/',
    expectStatus: 200
  },
  {
    name: 'Get Teams',
    method: 'GET',
    url: '/api/teams',
    expectStatus: 200
  },
  {
    name: 'Trade Analysis (Sample)',
    method: 'POST',
    url: '/api/analyze-trade',
    data: {
      team: 'yankees',
      request: 'I need a power hitter with 30+ home runs',
      urgency: 'medium'
    },
    expectStatus: 200
  }
];

async function runTest(test) {
  try {
    console.log(`\n🧪 Testing: ${test.name}`);
    
    const config = {
      method: test.method.toLowerCase(),
      url: `${API_BASE_URL}${test.url}`,
      timeout: 10000,
      validateStatus: function (status) {
        return status < 500; // Resolve for any status less than 500
      }
    };
    
    if (test.data) {
      config.data = test.data;
      config.headers = { 'Content-Type': 'application/json' };
    }
    
    const response = await axios(config);
    
    if (response.status === test.expectStatus) {
      console.log(`✅ PASS: ${test.name} (${response.status})`);
      if (response.data) {
        console.log(`   📊 Response preview:`, JSON.stringify(response.data, null, 2).substring(0, 200) + '...');
      }
    } else {
      console.log(`❌ FAIL: ${test.name} - Expected ${test.expectStatus}, got ${response.status}`);
      if (response.data) {
        console.log(`   📊 Error response:`, response.data);
      }
    }
    
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.log(`❌ FAIL: ${test.name} - Backend server not running (ECONNREFUSED)`);
    } else if (error.code === 'ECONNABORTED') {
      console.log(`❌ FAIL: ${test.name} - Request timeout`);
    } else {
      console.log(`❌ FAIL: ${test.name} - ${error.message}`);
    }
  }
}

async function runIntegrationTests() {
  console.log('🚀 Baseball Trade AI - Frontend-Backend Integration Test\n');
  console.log(`🔗 Testing API at: ${API_BASE_URL}\n`);
  
  for (const test of tests) {
    await runTest(test);
    // Wait between requests
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  console.log('\n✨ Integration tests completed!');
  console.log('\n📝 Next steps:');
  console.log('   1. Start backend: cd backend && python simple_main.py');
  console.log('   2. Start frontend: cd frontend && npm run dev');
  console.log('   3. Test in browser: http://localhost:3000');
}

// Check if axios is available
try {
  require('axios');
  runIntegrationTests();
} catch (e) {
  console.log('❌ axios not found. Install it with: npm install axios');
  console.log('\nAlternatively, test manually:');
  console.log('1. Start backend: cd backend && python simple_main.py');
  console.log('2. Test health: curl http://localhost:8000/');
  console.log('3. Test teams: curl http://localhost:8000/api/teams');
}