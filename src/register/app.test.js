import { test, describe } from 'node:test';
import assert from 'node:assert';
import { register } from './app.js';

// Mock del cliente de Cognito
function createMockCognitoClient(shouldFail = false, error = null) {
  return {
    send: (command) => {
      if (shouldFail) {
        throw error;
      }
      return Promise.resolve({});
    }
  };
}

describe('register function', () => {
  test('should register user successfully', async () => {
    // Configurar environment
    process.env.CLIENT_ID = 'test-client-id';
    
    const mockCognitoClient = createMockCognitoClient();
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
    // Configurar environment
    process.env.CLIENT_ID = 'test-client-id';
    
    const mockCognitoClient = createMockCognitoClient();
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
    // Configurar environment
    process.env.CLIENT_ID = 'test-client-id';
    
    const mockCognitoClient = createMockCognitoClient();
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
    // Configurar environment
    process.env.CLIENT_ID = 'test-client-id';
    
    const error = new Error('UsernameExistsException');
    error.name = 'UsernameExistsException';
    const mockCognitoClient = createMockCognitoClient(true, error);

    const event = {
      body: JSON.stringify({
        email: 'existing@example.com',
        password: 'TestPass123!'
      })
    };

    const result = await register(event, null, mockCognitoClient);

    assert.strictEqual(result.statusCode, 409);
    assert.deepStrictEqual(JSON.parse(result.body), { message: 'user already exists, try to login' });
  });

  test('should return 500 for other errors', async () => {
    // Configurar environment
    process.env.CLIENT_ID = 'test-client-id';
    
    const error = new Error('Some other error');
    const mockCognitoClient = createMockCognitoClient(true, error);

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