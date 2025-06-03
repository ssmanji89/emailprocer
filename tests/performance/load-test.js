import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time');
const apiCalls = new Counter('api_calls');
const wsConnections = new Counter('ws_connections');

// Test configuration
export const options = {
  stages: [
    // Ramp up
    { duration: '2m', target: 10 },   // Ramp up to 10 users over 2 minutes
    { duration: '5m', target: 10 },   // Stay at 10 users for 5 minutes
    { duration: '2m', target: 20 },   // Ramp up to 20 users over 2 minutes
    { duration: '5m', target: 20 },   // Stay at 20 users for 5 minutes
    { duration: '2m', target: 50 },   // Ramp up to 50 users over 2 minutes
    { duration: '5m', target: 50 },   // Stay at 50 users for 5 minutes
    { duration: '2m', target: 0 },    // Ramp down to 0 users over 2 minutes
  ],
  thresholds: {
    // Performance thresholds
    http_req_duration: ['p(95)<2000'], // 95% of requests should be below 2s
    http_req_failed: ['rate<0.05'],    // Error rate should be below 5%
    error_rate: ['rate<0.05'],         // Custom error rate should be below 5%
    response_time: ['p(95)<2000'],     // 95% of response times should be below 2s
    
    // API-specific thresholds
    'http_req_duration{endpoint:health}': ['p(95)<500'],     // Health checks should be fast
    'http_req_duration{endpoint:auth}': ['p(95)<1000'],      // Auth should be under 1s
    'http_req_duration{endpoint:emails}': ['p(95)<3000'],    // Email processing can be slower
    'http_req_duration{endpoint:analytics}': ['p(95)<2000'], // Analytics should be reasonable
  },
};

// Environment configuration
const BASE_URL = __ENV.K6_STAGING_URL || 'https://staging-api.emailbot.your-domain.com';
const WS_URL = __ENV.K6_WS_URL || 'wss://staging-api.emailbot.your-domain.com';
const API_KEY = __ENV.K6_API_KEY || 'test_api_key';

// Test data
const testUsers = [
  { email: 'test1@example.com', role: 'admin' },
  { email: 'test2@example.com', role: 'user' },
  { email: 'test3@example.com', role: 'manager' },
];

const testEmails = [
  {
    subject: 'Urgent: System Alert',
    body: 'This is a test email for performance testing',
    sender: 'alert@system.com',
    priority: 'high'
  },
  {
    subject: 'Weekly Report',
    body: 'This is a weekly report email for testing',
    sender: 'reports@company.com',
    priority: 'normal'
  },
  {
    subject: 'Customer Inquiry',
    body: 'Customer has a question about our service',
    sender: 'customer@example.com',
    priority: 'normal'
  }
];

// Setup function - runs once per VU
export function setup() {
  console.log('Starting EmailBot performance test');
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`WebSocket URL: ${WS_URL}`);
  
  // Test basic connectivity
  const healthCheck = http.get(`${BASE_URL}/health`);
  check(healthCheck, {
    'setup: health check successful': (r) => r.status === 200,
  });
  
  return { baseUrl: BASE_URL, wsUrl: WS_URL };
}

// Main test function
export default function(data) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${API_KEY}`,
  };

  // Test 1: Health Check (lightweight)
  testHealthEndpoints(data.baseUrl, headers);
  
  // Test 2: Authentication Flow
  testAuthenticationFlow(data.baseUrl, headers);
  
  // Test 3: Email Processing
  testEmailProcessing(data.baseUrl, headers);
  
  // Test 4: Analytics Endpoints
  testAnalyticsEndpoints(data.baseUrl, headers);
  
  // Test 5: Real-time WebSocket (25% of users)
  if (Math.random() < 0.25) {
    testWebSocketConnection(data.wsUrl);
  }
  
  // Test 6: Escalation Management
  testEscalationEndpoints(data.baseUrl, headers);
  
  // Random sleep between 1-3 seconds
  sleep(Math.random() * 2 + 1);
}

function testHealthEndpoints(baseUrl, headers) {
  const responses = http.batch([
    ['GET', `${baseUrl}/health`, null, { headers, tags: { endpoint: 'health' } }],
    ['GET', `${baseUrl}/health/detailed`, null, { headers, tags: { endpoint: 'health' } }],
  ]);
  
  responses.forEach((response) => {
    const success = check(response, {
      'health check status is 200': (r) => r.status === 200,
      'health check response time < 500ms': (r) => r.timings.duration < 500,
    });
    
    errorRate.add(!success);
    responseTime.add(response.timings.duration);
    apiCalls.add(1);
  });
}

function testAuthenticationFlow(baseUrl, headers) {
  // Test API key validation
  const authResponse = http.get(`${baseUrl}/security/validate`, {
    headers,
    tags: { endpoint: 'auth' }
  });
  
  const success = check(authResponse, {
    'auth validation successful': (r) => r.status === 200 || r.status === 401,
    'auth response time < 1s': (r) => r.timings.duration < 1000,
  });
  
  errorRate.add(!success);
  responseTime.add(authResponse.timings.duration);
  apiCalls.add(1);
}

function testEmailProcessing(baseUrl, headers) {
  // Get processing status
  const statusResponse = http.get(`${baseUrl}/process/status`, {
    headers,
    tags: { endpoint: 'emails' }
  });
  
  // Get email statistics
  const statsResponse = http.get(`${baseUrl}/process/statistics`, {
    headers,
    tags: { endpoint: 'emails' }
  });
  
  // Simulate email processing trigger (POST)
  const triggerResponse = http.post(`${baseUrl}/process/trigger`, JSON.stringify({}), {
    headers,
    tags: { endpoint: 'emails' }
  });
  
  const responses = [statusResponse, statsResponse, triggerResponse];
  
  responses.forEach((response, index) => {
    const expectedStatus = index === 2 ? [200, 202] : [200]; // POST might return 202
    const success = check(response, {
      [`email processing ${index + 1} status correct`]: (r) => expectedStatus.includes(r.status),
      [`email processing ${index + 1} response time < 3s`]: (r) => r.timings.duration < 3000,
    });
    
    errorRate.add(!success);
    responseTime.add(response.timings.duration);
    apiCalls.add(1);
  });
}

function testAnalyticsEndpoints(baseUrl, headers) {
  const analyticsEndpoints = [
    '/analytics/dashboard',
    '/analytics/processing?days=7',
    '/analytics/classification',
    '/analytics/patterns'
  ];
  
  const requests = analyticsEndpoints.map(endpoint => [
    'GET',
    `${baseUrl}${endpoint}`,
    null,
    { headers, tags: { endpoint: 'analytics' } }
  ]);
  
  const responses = http.batch(requests);
  
  responses.forEach((response, index) => {
    const success = check(response, {
      [`analytics ${index + 1} status is 200`]: (r) => r.status === 200,
      [`analytics ${index + 1} response time < 2s`]: (r) => r.timings.duration < 2000,
      [`analytics ${index + 1} has data`]: (r) => r.body && r.body.length > 0,
    });
    
    errorRate.add(!success);
    responseTime.add(response.timings.duration);
    apiCalls.add(1);
  });
}

function testWebSocketConnection(wsUrl) {
  const url = `${wsUrl}/ws`;
  
  const response = ws.connect(url, {}, function (socket) {
    wsConnections.add(1);
    
    socket.on('open', function open() {
      console.log('WebSocket connection opened');
      
      // Send a test message
      socket.send(JSON.stringify({
        type: 'subscribe',
        channel: 'escalations'
      }));
    });
    
    socket.on('message', function message(data) {
      const success = check(data, {
        'websocket message received': (d) => d && d.length > 0,
      });
      errorRate.add(!success);
    });
    
    socket.on('error', function error(e) {
      console.log('WebSocket error:', e);
      errorRate.add(true);
    });
    
    // Keep connection open for 10-30 seconds
    sleep(Math.random() * 20 + 10);
    
    socket.close();
  });
  
  check(response, {
    'websocket connection successful': (r) => r && r.status === 101,
  });
}

function testEscalationEndpoints(baseUrl, headers) {
  // Get active escalations
  const escalationsResponse = http.get(`${baseUrl}/escalations/active`, {
    headers,
    tags: { endpoint: 'escalations' }
  });
  
  const success = check(escalationsResponse, {
    'escalations status is 200': (r) => r.status === 200,
    'escalations response time < 2s': (r) => r.timings.duration < 2000,
  });
  
  errorRate.add(!success);
  responseTime.add(escalationsResponse.timings.duration);
  apiCalls.add(1);
}

// Teardown function - runs once after all VUs finish
export function teardown(data) {
  console.log('EmailBot performance test completed');
  
  // Final health check
  const finalHealthCheck = http.get(`${data.baseUrl}/health`);
  check(finalHealthCheck, {
    'teardown: final health check successful': (r) => r.status === 200,
  });
} 