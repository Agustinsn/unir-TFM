import {
    CognitoIdentityProviderClient,
    SignUpCommand
} from "@aws-sdk/client-cognito-identity-provider";

const client = new CognitoIdentityProviderClient({});

export async function register(event, context, cognitoClient = null) {
    const cognito = cognitoClient || client;
    
    const body = JSON.parse(event.body || "{}");
    const { email, password } = body;
    if (!email || !password) {
        return { statusCode: 400, body: JSON.stringify({ message: "email & password required" }) };
    }
    try {
        await cognito.send(new SignUpCommand({
            ClientId: process.env.CLIENT_ID,
            Username: email,
            Password: password,
            UserAttributes: [{ Name: "email", Value: email }]
        }));
        return { statusCode: 201, body: JSON.stringify({ message: "user registered" }) };
    } catch (err) {
        if (err.name === 'UsernameExistsException') {
            return { statusCode: 409, body: JSON.stringify({ message: "user already exists" }) };
        }
        return { statusCode: 500, body: JSON.stringify({ error: err.message }) };
    }
}
