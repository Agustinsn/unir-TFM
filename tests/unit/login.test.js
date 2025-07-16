import { test, describe } from 'node:test';
import assert from 'node:assert';
import login  from '../../src/login/app.js';

// Mock del cliente de Cognito
function createMockCognitoClient(shouldFail = false, error = null, response = null) {
  return {
    send: (command) => {
      if (shouldFail) {
        throw error;
      }
      return Promise.resolve(response || {
        AuthenticationResult: {
          IdToken: 'mock-id-token',
          AccessToken: 'mock-access-token',
          RefreshToken: 'mock-refresh-token'
        }
      });
    }
  };
}

describe('login function', () => {
  test('should login user successfully', async () => {
    process.env.CLIENT_ID = 'test-client-id';
    const mockCognitoClient = createMockCognitoClient();

    const event = {
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'TestPass123!'
      })
    };

    const result = await login(event, null, mockCognitoClient);

    assert.strictEqual(result.statusCode, 200);
    assert.deepStrictEqual(JSON.parse(result.body), {
      message: 'login successful',
      idToken: 'mock-id-token',
      accessToken: 'mock-access-token',
      refreshToken: 'mock-refresh-token'
    });
  });

  test('should return 400 for missing email', async () => {
    process.env.CLIENT_ID = 'test-client-id';
    const mockCognitoClient = createMockCognitoClient();

    const event = {
      body: JSON.stringify({
        password: 'TestPass123!'
      })
    };

    const result = await login(event, null, mockCognitoClient);

    assert.strictEqual(result.statusCode, 400);
    assert.deepStrictEqual(JSON.parse(result.body), { message: 'email & password required' });
  });

  test('should return 400 for missing password', async () => {
    process.env.CLIENT_ID = 'test-client-id';
    const mockCognitoClient = createMockCognitoClient();

    const event = {
      body: JSON.stringify({
        email: 'test@example.com'
      })
    };

    const result = await login(event, null, mockCognitoClient);

    assert.strictEqual(result.statusCode, 400);
    assert.deepStrictEqual(JSON.parse(result.body), { message: 'email & password required' });
  });

  test('should return 401 for invalid credentials', async () => {
    process.env.CLIENT_ID = 'test-client-id';

    const error = new Error('invalid credentials');
    error.name = 'NotAuthorizedException';

    const mockCognitoClient = createMockCognitoClient(true, error);

    const event = {
      body: JSON.stringify({
        email: 'wrong@example.com',
        password: 'WrongPass123!'
      })
    };

    const result = await login(event, null, mockCognitoClient);

    assert.strictEqual(result.statusCode, 401);
    assert.deepStrictEqual(JSON.parse(result.body), { message: 'invalid credentials' });
  });

  test('should return 403 if user not confirmed', async () => {
    process.env.CLIENT_ID = 'test-client-id';

    const error = new Error('user not confirmed');
    error.name = 'UserNotConfirmedException';

    const mockCognitoClient = createMockCognitoClient(true, error);

    const event = {
      body: JSON.stringify({
        email: 'notconfirmed@example.com',
        password: 'TestPass123!'
      })
    };

    const result = await login(event, null, mockCognitoClient);

    assert.strictEqual(result.statusCode, 403);
    assert.deepStrictEqual(JSON.parse(result.body), { message: 'user not confirmed' });
  });

  test('should return 404 if user not found', async () => {
    process.env.CLIENT_ID = 'test-client-id';

    const error = new Error('user not found');
    error.name = 'UserNotFoundException';

    const mockCognitoClient = createMockCognitoClient(true, error);

    const event = {
      body: JSON.stringify({
        email: 'missing@example.com',
        password: 'TestPass123!'
      })
    };

    const result = await login(event, null, mockCognitoClient);

    assert.strictEqual(result.statusCode, 404);
    assert.deepStrictEqual(JSON.parse(result.body), { message: 'user not found' });
  });

  test('should return 500 for other errors', async () => {
    process.env.CLIENT_ID = 'test-client-id';

    const error = new Error('Unexpected error');

    const mockCognitoClient = createMockCognitoClient(true, error);

    const event = {
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'TestPass123!'
      })
    };

    const result = await login(event, null, mockCognitoClient);

    assert.strictEqual(result.statusCode, 500);
    assert.deepStrictEqual(JSON.parse(result.body), { error: 'Unexpected error' });
  });
});
