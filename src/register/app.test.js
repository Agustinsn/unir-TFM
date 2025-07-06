import { test, describe } from 'node:test';
import assert from 'node:assert';
import { register } from './app.js';

// Mock del cliente de Cognito
const mockCognitoClient = {
  send: (command) => {
    // Simular el comportamiento del mock
    if (mockCognitoClient.shouldFail) {
      throw mockCognitoClient.error;
    }
    return Promise.resolve({});
  },
  shouldFail: false,
  error: null
};

// Mock de process.env
const originalEnv = process.env;

describe('register function', () => {
  beforeEach(() => {
    process.env = { ...originalEnv, CLIENT_ID: 'test-client-id' };
    mockCognitoClient.shouldFail = false;
    mockCognitoClient.error = null;
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  test('should register user successfully', async () => {
    const event = {
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'TestPass123!'
      })
    };

    const result = await register(event, null, mockCognitoClient);

    assert.strictEqual(result.statusCode, 201);
    assert.deepStrictEqual(JSON.parse(result.body), { message: 'user registered' });
  });

  test('should return 400 for missing email', async () => {
    const event = {
      body: JSON.stringify({
        password: 'TestPass123!'
      })
    };

    const result = await register(event, null, mockCognitoClient);

    assert.strictEqual(result.statusCode, 400);
    assert.deepStrictEqual(JSON.parse(result.body), { message: 'email & password required' });
  });

  test('should return 400 for missing password', async () => {
    const event = {
      body: JSON.stringify({
        email: 'test@example.com'
      })
    };

    const result = await register(event, null, mockCognitoClient);

    assert.strictEqual(result.statusCode, 400);
    assert.deepStrictEqual(JSON.parse(result.body), { message: 'email & password required' });
  });

  test('should return 409 for existing user', async () => {
    const error = new Error('UsernameExistsException');
    error.name = 'UsernameExistsException';
    mockCognitoClient.shouldFail = true;
    mockCognitoClient.error = error;

    const event = {
      body: JSON.stringify({
        email: 'existing@example.com',
        password: 'TestPass123!'
      })
    };

    const result = await register(event, null, mockCognitoClient);

    assert.strictEqual(result.statusCode, 409);
    assert.deepStrictEqual(JSON.parse(result.body), { message: 'user already exists' });
  });

  test('should return 500 for other errors', async () => {
    const error = new Error('Some other error');
    mockCognitoClient.shouldFail = true;
    mockCognitoClient.error = error;

    const event = {
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'TestPass123!'
      })
    };

    const result = await register(event, null, mockCognitoClient);

    assert.strictEqual(result.statusCode, 500);
    assert.deepStrictEqual(JSON.parse(result.body), { error: 'Some other error' });
  });
}); 