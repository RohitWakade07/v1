const BASE_URL = 'http://localhost:8000/api/v1';

const results = [];

function logResult(name, status, detail) {
  results.push({ name, status, detail });
  console.log(`[${status}] ${name}${detail ? ': ' + detail : ''}`);
}

async function request(method, path, body = null, token = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  
  const options = { method, headers };
  if (body) options.body = JSON.stringify(body);
  
  const url = path.startsWith('http') ? path : `${BASE_URL}${path}`;
  const res = await fetch(url, options);
  const data = await res.json().catch(() => null);
  
  if (!res.ok) {
    throw { status: res.status, data };
  }
  return data;
}

async function runTests() {
  console.log('Starting E2E API Tests...');
  
  let studentToken = '';
  let mentorToken = '';
  let assignmentId = '';

  // 1. Health Check
  try {
    const data = await request('GET', 'http://localhost:8000/health');
    if (data.status === 'ok') {
      logResult('Health Check', 'PASS');
    } else {
      logResult('Health Check', 'FAIL', 'Unexpected payload: ' + JSON.stringify(data));
    }
  } catch (err) {
    logResult('Health Check', 'FAIL', err.data?.detail || 'Fetch failed');
  }

  // 2. Mentor Login
  try {
    const data = await request('POST', '/auth/mentor/login', {
      username: 'test_mentor',
      password: 'password123'
    });
    if (data.access_token) {
      mentorToken = data.access_token;
      logResult('Mentor Login', 'PASS');
    } else {
      logResult('Mentor Login', 'FAIL', 'No access token');
    }
  } catch (err) {
    logResult('Mentor Login', 'FAIL', err.data?.detail || 'Request failed');
  }

  // 3. Create Assignment (Mentor)
  if (mentorToken) {
    try {
      const data = await request('POST', '/assignments', {
        title: 'Test Assignment ' + Date.now(),
        slug: 'test-assignment-' + Date.now(),
        description: 'Test description',
        category: 'artifact_validation',
        max_score: 100,
        publish_immediately: false
      }, mentorToken);
      assignmentId = data.id;
      logResult('Create Assignment (Draft)', 'PASS');
    } catch (err) {
      logResult('Create Assignment (Draft)', 'FAIL', err.data?.detail || 'Request failed');
    }
  }

  // 4. Publish Assignment (Mentor)
  if (mentorToken && assignmentId) {
    try {
      const data = await request('POST', `/assignments/${assignmentId}/publish`, {}, mentorToken);
      if (data.is_published === true) {
        logResult('Publish Assignment', 'PASS');
      } else {
        logResult('Publish Assignment', 'FAIL', 'Not published');
      }
    } catch (err) {
      logResult('Publish Assignment', 'FAIL', err.data?.detail || 'Request failed');
    }
  }

  // 5. Student Register/Login
  try {
    const regData = await request('POST', '/auth/student/register', {
      roll_number: '2024CS001',
      full_name: 'Test Student',
      email: 'student@test.com',
      password: 'password123'
    }).catch(err => {
      // Ignore conflict if already registered
      if (err.status !== 409) throw err;
    });

    const data = await request('POST', '/auth/student/login', {
      roll_number: '2024CS001',
      password: 'password123'
    });
    if (data.access_token) {
      studentToken = data.access_token;
      logResult('Student Login', 'PASS');
    } else {
      logResult('Student Login', 'FAIL', 'No access token');
    }
  } catch (err) {
    logResult('Student Login', 'FAIL', err.data?.detail || 'Request failed');
  }

  // 6. Get Assignments (Student)
  if (studentToken) {
    try {
      const data = await request('GET', '/assignments', null, studentToken);
      if (Array.isArray(data)) {
        logResult('Get Published Assignments', 'PASS', `Found ${data.length} assignments`);
      } else {
        logResult('Get Published Assignments', 'FAIL', 'Payload not an array');
      }
    } catch (err) {
      logResult('Get Published Assignments', 'FAIL', err.data?.detail || 'Request failed');
    }
  }

  // 7. Submit Proof (Student)
  if (studentToken && assignmentId) {
    try {
      const data = await request('POST', `/proof/submit`, {
        assignment_id: assignmentId,
        student_id: 'test_student',
        session_id: '123e4567-e89b-12d3-a456-426614174000',
        timestamp: new Date().toISOString(),
        nonce: 'random-nonce',
        grader_binary_hash: 'hash',
        results: {},
        artifact_hashes: {},
        hmac_signature: 'signature'
      }, studentToken);
      if (data.id) {
        logResult('Submit Proof', 'PASS');
      } else {
        logResult('Submit Proof', 'FAIL', 'No submission ID returned');
      }
    } catch (err) {
      logResult('Submit Proof', 'FAIL', err.data?.detail || 'Request failed');
    }
  }

  console.log('\n--- JSON RESULT PAYLOAD ---');
  console.log(JSON.stringify(results));
}

runTests();
