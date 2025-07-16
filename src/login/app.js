import {
    CognitoIdentityProviderClient,
    InitiateAuthCommand
} from "@aws-sdk/client-cognito-identity-provider";

import {
    CloudWatchClient,
    PutMetricDataCommand
  } from "@aws-sdk/client-cloudwatch";

const client = new CognitoIdentityProviderClient({});
const cloudwatchClient = new CloudWatchClient({});

async function sendMetric({ name, value = 1, unit = "Count", namespace = "Custom/Login" }) {    
    const command = new PutMetricDataCommand({
      Namespace: namespace,
      MetricData: [
        {
          MetricName: name,
          Timestamp: new Date(),
          Value: value,
          Unit: unit
        }
      ]
    });
  
    try {
      await cloudwatchClient.send(command);
      console.log(`Metric sent: ${name} = ${value}`);
    } catch (err) {
      console.error("Error sending CloudWatch metric:", err);
    }
  }

  export default async function login(event, context, cognitoClient = null) {
    const cognito =
        cognitoClient && typeof cognitoClient.send === "function"
            ? cognitoClient
            : client;

    const body = JSON.parse(event.body || "{}");
    const { email, password } = body;

    if (!email || !password) {
        console.warn("Missing email or password");
        await sendMetric({ name: "LoginFailure_MissingFields" });
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
        console.log("Login success for user:", email);
        await sendMetric({ name: "LoginSuccess" });
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
        console.error("Login failed:", err);

        if (err.name === 'NotAuthorizedException') {
            return { statusCode: 401, body: JSON.stringify({ message: "invalid credentials" }) };
        } else if (err.name === 'UserNotConfirmedException') {
            return { statusCode: 403, body: JSON.stringify({ message: "user not confirmed" }) };
        } else if (err.name === 'UserNotFoundException') {
            return { statusCode: 404, body: JSON.stringify({ message: "user not found" }) };
        }
        await sendMetric({ name: "LoginFailure_UnknownError" });
        return { statusCode: 500, body: JSON.stringify({ error: err.message }) };
    }
}
