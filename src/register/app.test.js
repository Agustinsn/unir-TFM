import { register } from './app.js';

// Mock del cliente de Cognito
const mockCognitoClient = {
  send: jest.fn()
};

// Mock de process.env
const originalEnv = process.env;

beforeEach(() => {
  process.env = { ...originalEnv, CLIENT_ID: 'test-client-id' };
  mockCognitoClient.send.mockClear();
});

afterEach(() => {
  process.env = originalEnv;
});

describe('register function', () => {
  test('should register user successfully', async () => {
    mockCognitoClient.send.mockResolvedValue({});

    const event = {
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'TestPass123!'
      })
    };

    const result = await register(event, null, mockCognitoClient);

    expect(result.statusCode).toBe(201);
    expect(JSON.parse(result.body)).toEqual({ message: 'user registered' });
    expect(mockCognitoClient.send).toHaveBeenCalledWith(
      expect.objectContaining({
        input: {
          ClientId: 'test-client-id',
          Username: 'test@example.com',
          Password: 'TestPass123!',
          UserAttributes: [{ Name: 'email', Value: 'test@example.com' }]
        }
      })
    );
  });

  test('should return 400 for missing email', async () => {
    const event = {
      body: JSON.stringify({
        password: 'TestPass123!'
      })
    };

    const result = await register(event, null, mockCognitoClient);

    expect(result.statusCode).toBe(400);
    expect(JSON.parse(result.body)).toEqual({ message: 'email & password required' });
  });

  test('should return 400 for missing password', async () => {
    const event = {
      body: JSON.stringify({
        email: 'test@example.com'
      })
    };

    const result = await register(event, null, mockCognitoClient);

    expect(result.statusCode).toBe(400);
    expect(JSON.parse(result.body)).toEqual({ message: 'email & password required' });
  });

  test('should return 409 for existing user', async () => {
    const error = new Error('UsernameExistsException');
    error.name = 'UsernameExistsException';
    mockCognitoClient.send.mockRejectedValue(error);

    const event = {
      body: JSON.stringify({
        email: 'existing@example.com',
        password: 'TestPass123!'
      })
    };

    const result = await register(event, null, mockCognitoClient);

    expect(result.statusCode).toBe(409);
    expect(JSON.parse(result.body)).toEqual({ message: 'user already exists' });
  });

  test('should return 500 for other errors', async () => {
    const error = new Error('Some other error');
    mockCognitoClient.send.mockRejectedValue(error);

    const event = {
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'TestPass123!'
      })
    };

    const result = await register(event, null, mockCognitoClient);

    expect(result.statusCode).toBe(500);
    expect(JSON.parse(result.body)).toEqual({ error: 'Some other error' });
  });
}); 