import {
    CognitoIdentityProviderClient,
    SignUpCommand
} from "@aws-sdk/client-cognito-identity-provider";

const client = new CognitoIdentityProviderClient({});

export default async function register(event, context, cognitoClient = null) {
    // const cognito = cognitoClient || client;
    const cognito =
        cognitoClient && typeof cognitoClient.send === "function"
            ? cognitoClient
            : client;

    console.log("Lambda invoked");
    console.log("typeof cognito:", typeof cognito);
    console.log("typeof cognito.send:", typeof cognito?.send);
    console.log("client instance class name:", client.constructor.name);
    
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
            return { statusCode: 409, body: JSON.stringify({ message: "user already exists, try to login" }) };
        }
        return { statusCode: 500, body: JSON.stringify({ error: err.message }) };
    }
}
