import {
    CognitoIdentityProviderClient,
    InitiateAuthCommand
} from "@aws-sdk/client-cognito-identity-provider";

const client = new CognitoIdentityProviderClient({});

export async function login(event, context, cognitoClient = null) {
    const cognito = cognitoClient || client;

    const body = JSON.parse(event.body || "{}");
    const { email, password } = body;

    if (!email || !password) {
        return {
            statusCode: 400,
            body: JSON.stringify({ message: "email & password required" })
        };
    }

    const command = new InitiateAuthCommand({
        AuthFlow: "USER_PASSWORD_AUTH",
        ClientId: process.env.CLIENT_ID,
        AuthParameters: {
            USERNAME: email,
            PASSWORD: password
        }
    });

    try {
        const response = await cognito.send(command);
        return {
            statusCode: 200,
            body: JSON.stringify({
                message: "login successful",
                idToken: response.AuthenticationResult?.IdToken,
                accessToken: response.AuthenticationResult?.AccessToken,
                refreshToken: response.AuthenticationResult?.RefreshToken
            })
        };
    } catch (err) {
        if (err.name === 'NotAuthorizedException') {
            return { statusCode: 401, body: JSON.stringify({ message: "invalid credentials" }) };
        } else if (err.name === 'UserNotConfirmedException') {
            return { statusCode: 403, body: JSON.stringify({ message: "user not confirmed" }) };
        } else if (err.name === 'UserNotFoundException') {
            return { statusCode: 404, body: JSON.stringify({ message: "user not found" }) };
        }
        return { statusCode: 500, body: JSON.stringify({ error: err.message }) };
    }
}
